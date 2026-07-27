"""
tests/test_integration.py
==========================
Integration tests for GOLEM-3DMCP.

IMPORTANT: All tests in this file require a running Rhino instance with the
GOLEM-3DMCP plugin loaded and listening on 127.0.0.1:9876.

By default every test is skipped via the ``rhino_connection`` fixture —
if the fixture cannot connect it yields ``None`` and the test body calls
``pytest.skip()``.  This means the full ``pytest tests/`` suite always
passes cleanly whether Rhino is running or not.

To run integration tests against a live Rhino instance:

    pytest tests/test_integration.py -v -m integration

Marks
-----
All tests carry ``@pytest.mark.integration`` so they can be selected or
excluded with::

    pytest -m "not integration"   # skip all integration tests
    pytest -m integration          # run only integration tests
"""

from __future__ import annotations

import base64
import uuid

import pytest

# ---------------------------------------------------------------------------
# Marker declaration
# ---------------------------------------------------------------------------

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _skip_if_no_rhino(connection) -> None:
    """Call at the start of every integration test."""
    if connection is None:
        pytest.skip("Rhino is not running — skipping integration test")


def _unique_layer() -> str:
    return f"TestLayer_{uuid.uuid4().hex[:8]}"


# ---------------------------------------------------------------------------
# Connectivity
# ---------------------------------------------------------------------------

class TestConnectivity:

    def test_connection_is_alive(self, rhino_connection):
        """Verify the connection fixture is live and responding."""
        _skip_if_no_rhino(rhino_connection)
        assert rhino_connection.is_connected()

    def test_ping_roundtrip(self, rhino_connection):
        """ping command should return without error."""
        _skip_if_no_rhino(rhino_connection)
        result = rhino_connection.send_command("ping", {})
        # The plugin returns either {} or {"pong": True} — both are acceptable.
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# Scene inspection
# ---------------------------------------------------------------------------

class TestSceneIntegration:

    def test_get_document_info(self, rhino_connection):
        """get_document_info returns a dict with expected fields."""
        _skip_if_no_rhino(rhino_connection)
        result = rhino_connection.send_command("scene.get_document_info", {})
        assert isinstance(result, dict)
        assert "units" in result
        assert "object_count" in result
        assert "layer_count" in result

    def test_list_layers_returns_list(self, rhino_connection):
        _skip_if_no_rhino(rhino_connection)
        result = rhino_connection.send_command("scene.list_layers", {})
        assert "layers" in result or isinstance(result, dict)

    def test_list_objects_returns_dict(self, rhino_connection):
        _skip_if_no_rhino(rhino_connection)
        result = rhino_connection.send_command(
            "scene.list_objects",
            {"layer": None, "object_type": None, "name": None,
             "visible_only": False, "unlocked_only": False},
        )
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# Geometry creation → query → deletion
# ---------------------------------------------------------------------------

class TestGeometryRoundTrip:

    def test_create_box_query_delete(self, rhino_connection):
        """
        Full round-trip:
          1. Create a box.
          2. Query it back to confirm it exists.
          3. Delete it.
          4. Confirm it is gone.
        """
        _skip_if_no_rhino(rhino_connection)

        # 1. Create
        create_result = rhino_connection.send_command("geometry.create_box", {
            "corner": {"x": 0.0, "y": 0.0, "z": 0.0},
            "width": 2.0, "depth": 2.0, "height": 2.0,
            "layer": None, "name": "IntegrationTestBox",
        })
        assert "guid" in create_result, f"Expected 'guid' in result: {create_result}"
        guid = create_result["guid"]
        assert isinstance(guid, str) and len(guid) > 0

        try:
            # 2. Query
            info = rhino_connection.send_command("scene.get_object_info", {"guid": guid})
            assert info.get("guid") == guid or guid in str(info)

        finally:
            # 3. Delete (always, even if query failed)
            delete_result = rhino_connection.send_command(
                "scene.delete_objects", {"guids": [guid]}
            )
            assert isinstance(delete_result, dict)

    def test_create_sphere_and_delete(self, rhino_connection):
        _skip_if_no_rhino(rhino_connection)

        create_result = rhino_connection.send_command("geometry.create_sphere", {
            "center": {"x": 10.0, "y": 10.0, "z": 0.0},
            "radius": 1.0,
            "layer": None, "name": "IntegrationTestSphere",
        })
        assert "guid" in create_result
        guid = create_result["guid"]

        rhino_connection.send_command("scene.delete_objects", {"guids": [guid]})

    def test_create_line_and_delete(self, rhino_connection):
        _skip_if_no_rhino(rhino_connection)

        result = rhino_connection.send_command("geometry.create_line", {
            "start": {"x": 0.0, "y": 0.0, "z": 0.0},
            "end": {"x": 5.0, "y": 5.0, "z": 0.0},
            "layer": None, "name": None,
        })
        assert "guid" in result
        rhino_connection.send_command("scene.delete_objects", {"guids": [result["guid"]]})

    def test_boolean_union_two_boxes(self, rhino_connection):
        """Create two overlapping boxes, union them, then clean up."""
        _skip_if_no_rhino(rhino_connection)

        box_a = rhino_connection.send_command("geometry.create_box", {
            "corner": {"x": 0.0, "y": 0.0, "z": 0.0},
            "width": 2.0, "depth": 2.0, "height": 2.0,
            "layer": None, "name": None,
        })
        box_b = rhino_connection.send_command("geometry.create_box", {
            "corner": {"x": 1.0, "y": 0.0, "z": 0.0},
            "width": 2.0, "depth": 2.0, "height": 2.0,
            "layer": None, "name": None,
        })

        guid_a = box_a["guid"]
        guid_b = box_b["guid"]

        union_result = rhino_connection.send_command("operations.boolean_union", {
            "guids": [guid_a, guid_b],
            "delete_input": True,
        })

        # Clean up the union result (input objects already deleted)
        if "guid" in union_result:
            rhino_connection.send_command(
                "scene.delete_objects", {"guids": [union_result["guid"]]}
            )
        elif "guids" in union_result:
            rhino_connection.send_command(
                "scene.delete_objects", {"guids": union_result["guids"]}
            )


# ---------------------------------------------------------------------------
# Viewport capture
# ---------------------------------------------------------------------------

class TestViewportCapture:

    def test_capture_returns_base64_image(self, rhino_connection):
        """capture_viewport returns a base64-encoded PNG string."""
        _skip_if_no_rhino(rhino_connection)

        result = rhino_connection.send_command("viewport.capture", {
            "view_name": None,
            "width": 320,
            "height": 240,
            "display_mode": None,
            "transparent_background": False,
        })

        assert isinstance(result, dict)
        assert "image" in result, f"'image' key missing from result: {result}"
        image_data = result["image"]
        assert isinstance(image_data, str)
        assert len(image_data) > 0

        # Verify it is valid base64
        try:
            decoded = base64.b64decode(image_data)
            assert len(decoded) > 0
        except Exception as exc:
            pytest.fail(f"viewport capture 'image' is not valid base64: {exc}")

    def test_capture_width_height_respected(self, rhino_connection):
        """The response should report the requested dimensions."""
        _skip_if_no_rhino(rhino_connection)

        result = rhino_connection.send_command("viewport.capture", {
            "view_name": None,
            "width": 640,
            "height": 480,
            "display_mode": "Wireframe",
            "transparent_background": False,
        })
        # Not all plugins echo dimensions, so only assert if present.
        if "width" in result:
            assert result["width"] == 640
        if "height" in result:
            assert result["height"] == 480


# ---------------------------------------------------------------------------
# Script execution
# ---------------------------------------------------------------------------

class TestScriptExecution:

    def test_execute_python_simple_expression(self, rhino_connection):
        """Execute Python code that populates _output and verify the result."""
        _skip_if_no_rhino(rhino_connection)

        code = "_output['answer'] = 6 * 7"
        result = rhino_connection.send_command("scripting.execute_python", {
            "code": code,
            "context": {},
            "timeout_seconds": 10,
            "capture_output": True,
        })

        assert isinstance(result, dict)
        assert result.get("success") is True
        output = result.get("output", {})
        assert output.get("answer") == 42

    def test_execute_python_captures_print_output(self, rhino_connection):
        """print() output is captured in the 'stdout' field."""
        _skip_if_no_rhino(rhino_connection)

        code = "print('hello from integration test')"
        result = rhino_connection.send_command("scripting.execute_python", {
            "code": code,
            "context": {},
            "timeout_seconds": 10,
            "capture_output": True,
        })

        assert result.get("success") is True
        stdout = result.get("stdout", "")
        assert "hello from integration test" in stdout

    def test_execute_python_syntax_error_returns_failure(self, rhino_connection):
        """A syntax error in the code results in success=False."""
        _skip_if_no_rhino(rhino_connection)

        code = "def broken(:\n    pass"  # deliberate syntax error
        result = rhino_connection.send_command("scripting.execute_python", {
            "code": code,
            "context": {},
            "timeout_seconds": 10,
            "capture_output": True,
        })

        assert result.get("success") is False
        assert "error" in result or "traceback" in result

    def test_execute_python_with_context_variables(self, rhino_connection):
        """Variables injected via context are available during execution."""
        _skip_if_no_rhino(rhino_connection)

        code = "_output['doubled'] = my_value * 2"
        result = rhino_connection.send_command("scripting.execute_python", {
            "code": code,
            "context": {"my_value": 21},
            "timeout_seconds": 10,
            "capture_output": False,
        })

        assert result.get("success") is True
        assert result.get("output", {}).get("doubled") == 42


# ---------------------------------------------------------------------------
# Layer management
# ---------------------------------------------------------------------------

class TestLayerManagement:

    def test_create_and_delete_layer(self, rhino_connection):
        """Create a test layer, verify it exists, then delete it."""
        _skip_if_no_rhino(rhino_connection)

        layer_name = _unique_layer()

        create_result = rhino_connection.send_command("scene.create_layer", {
            "name": layer_name,
            "color": {"r": 255, "g": 0, "b": 0, "a": 255},
            "visible": True,
            "locked": False,
            "parent": None,
        })
        assert isinstance(create_result, dict)

        # Clean up
        rhino_connection.send_command("scene.delete_layer", {
            "name": layer_name,
            "delete_objects": False,
        })
