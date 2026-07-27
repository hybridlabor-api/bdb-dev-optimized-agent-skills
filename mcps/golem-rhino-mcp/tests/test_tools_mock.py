"""
tests/test_tools_mock.py
=========================
Unit tests for MCP tool functions with a mocked RhinoConnection.

Strategy
--------
Each tool module calls ``get_connection()`` at invocation time via its own
module-local reference ``golem_3dmcp.tools.{module}.get_connection``.  We
patch that attribute directly on the already-imported module so the tool
function sees our fake connection regardless of how many times the module
has been imported.

For each tool under test we verify:
  1. The correct ``method`` string is passed to ``send_command``.
  2. The correct ``params`` dict is passed (checking key values).
  3. The tool returns whatever ``send_command`` returns unchanged.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import golem_3dmcp.tools.creation as _creation_mod
import golem_3dmcp.tools.files as _files_mod
import golem_3dmcp.tools.manipulation as _manipulation_mod
import golem_3dmcp.tools.operations as _operations_mod

# ---------------------------------------------------------------------------
# Pre-import ALL tool modules here at collection time.
# Python caches modules in sys.modules; importing them once and then
# patching the 'get_connection' name inside each module's namespace is the
# correct way to intercept the call.
# ---------------------------------------------------------------------------
import golem_3dmcp.tools.scene as _scene_mod
import golem_3dmcp.tools.scripting as _scripting_mod
import golem_3dmcp.tools.viewport as _viewport_mod

# ---------------------------------------------------------------------------
# Fake connection
# ---------------------------------------------------------------------------

class _FakeConnection:
    """
    Lightweight stand-in for RhinoConnection.  Records every send_command
    call and returns ``response`` each time.
    """

    def __init__(self, response: dict | None = None) -> None:
        self.calls: list[dict[str, Any]] = []
        self.response = response or {}

    def send_command(self, method: str, params: dict, timeout: int = 30) -> dict:
        self.calls.append({"method": method, "params": params})
        return dict(self.response)

    def last_call(self) -> dict[str, Any]:
        assert self.calls, "send_command was never called"
        return self.calls[-1]


def _fc(response: dict | None = None) -> _FakeConnection:
    return _FakeConnection(response=response)


# ---------------------------------------------------------------------------
# Scene tools
# ---------------------------------------------------------------------------

class TestSceneTools:

    def test_get_document_info_sends_correct_method(self):
        fc = _fc({"file_path": "/tmp/model.3dm", "units": "Meters"})
        with patch.object(_scene_mod, "get_connection", return_value=fc):
            result = _scene_mod.get_document_info()

        assert fc.last_call()["method"] == "scene.get_document_info"
        assert fc.last_call()["params"] == {}
        assert result["units"] == "Meters"

    def test_list_layers_sends_correct_method(self):
        fc = _fc({"layers": []})
        with patch.object(_scene_mod, "get_connection", return_value=fc):
            result = _scene_mod.list_layers()

        assert fc.last_call()["method"] == "scene.list_layers"
        assert result == {"layers": []}

    def test_list_objects_passes_filter_params(self):
        fc = _fc({"objects": []})
        with patch.object(_scene_mod, "get_connection", return_value=fc):
            _scene_mod.list_objects(
                layer="Walls", object_type="brep", visible_only=True
            )

        params = fc.last_call()["params"]
        assert params["layer"] == "Walls"
        assert params["object_type"] == "brep"
        assert params["visible_only"] is True

    def test_get_object_info_sends_guid(self):
        guid = "abc-def-123"
        fc = _fc({"guid": guid, "type": "brep"})
        with patch.object(_scene_mod, "get_connection", return_value=fc):
            result = _scene_mod.get_object_info(guid=guid)

        assert fc.last_call()["method"] == "scene.get_object_info"
        assert fc.last_call()["params"]["guid"] == guid
        assert result["type"] == "brep"

    def test_delete_objects_sends_guids(self):
        guids = ["g1", "g2", "g3"]
        fc = _fc({"deleted": 3})
        with patch.object(_scene_mod, "get_connection", return_value=fc):
            _scene_mod.delete_objects(guids=guids)

        assert fc.last_call()["method"] == "scene.delete_objects"
        assert fc.last_call()["params"]["guids"] == guids

    def test_create_layer_sends_all_params(self):
        fc = _fc({"guid": "layer-guid"})
        with patch.object(_scene_mod, "get_connection", return_value=fc):
            _scene_mod.create_layer(
                name="NewLayer",
                color_r=255, color_g=0, color_b=128,
                visible=True, locked=False,
            )

        params = fc.last_call()["params"]
        assert params["name"] == "NewLayer"
        assert params["color"]["r"] == 255
        assert params["color"]["b"] == 128
        assert params["visible"] is True

    def test_get_selected_objects_sends_correct_method(self):
        fc = _fc({"objects": ["g1"]})
        with patch.object(_scene_mod, "get_connection", return_value=fc):
            _scene_mod.get_selected_objects()

        assert fc.last_call()["method"] == "scene.get_selected_objects"

    def test_tool_passes_through_connection_result_verbatim(self):
        """Whatever the connection returns is returned unchanged by the tool."""
        arbitrary = {"foo": [1, 2, 3], "bar": {"nested": True}}
        fc = _fc(arbitrary)
        with patch.object(_scene_mod, "get_connection", return_value=fc):
            result = _scene_mod.get_document_info()

        assert result == arbitrary

    def test_select_objects_sends_guids(self):
        guids = ["x1", "x2"]
        fc = _fc({"selected": 2})
        with patch.object(_scene_mod, "get_connection", return_value=fc):
            _scene_mod.select_objects(guids=guids)

        assert fc.last_call()["params"]["guids"] == guids

    def test_hide_objects_sends_guids_and_flag(self):
        fc = _fc({})
        with patch.object(_scene_mod, "get_connection", return_value=fc):
            _scene_mod.hide_objects(guids=["h1"], hide=True)

        params = fc.last_call()["params"]
        assert params["guids"] == ["h1"]
        assert params["hide"] is True

    def test_set_object_layer_sends_layer(self):
        fc = _fc({})
        with patch.object(_scene_mod, "get_connection", return_value=fc):
            _scene_mod.set_object_layer(guids=["obj1"], layer="NewLayer")

        params = fc.last_call()["params"]
        assert params["layer"] == "NewLayer"

    def test_list_views_sends_correct_method(self):
        fc = _fc({"views": []})
        with patch.object(_scene_mod, "get_connection", return_value=fc):
            _scene_mod.list_views()

        assert fc.last_call()["method"] == "scene.list_views"


# ---------------------------------------------------------------------------
# Creation tools
# ---------------------------------------------------------------------------

class TestCreationTools:

    def test_create_box_sends_correct_params(self):
        fc = _fc({"guid": "box-guid"})
        with patch.object(_creation_mod, "get_connection", return_value=fc):
            result = _creation_mod.create_box(
                corner_x=1.0, corner_y=2.0, corner_z=0.0,
                width=5.0, depth=3.0, height=2.0,
                layer="Structure", name="MyBox",
            )

        assert fc.last_call()["method"] == "geometry.create_box"
        params = fc.last_call()["params"]
        assert params["corner"] == {"x": 1.0, "y": 2.0, "z": 0.0}
        assert params["width"] == 5.0
        assert params["depth"] == 3.0
        assert params["height"] == 2.0
        assert params["layer"] == "Structure"
        assert params["name"] == "MyBox"
        assert result == {"guid": "box-guid"}

    def test_create_sphere_sends_correct_params(self):
        fc = _fc({"guid": "sphere-guid"})
        with patch.object(_creation_mod, "get_connection", return_value=fc):
            _creation_mod.create_sphere(
                center_x=0.0, center_y=0.0, center_z=5.0, radius=2.5
            )

        params = fc.last_call()["params"]
        assert params["center"] == {"x": 0.0, "y": 0.0, "z": 5.0}
        assert params["radius"] == 2.5

    def test_create_cylinder_sends_correct_params(self):
        fc = _fc({"guid": "cyl-guid"})
        with patch.object(_creation_mod, "get_connection", return_value=fc):
            _creation_mod.create_cylinder(
                base_x=0.0, base_y=0.0, base_z=0.0,
                height=10.0, radius=3.0, cap=False,
            )

        params = fc.last_call()["params"]
        assert params["height"] == 10.0
        assert params["radius"] == 3.0
        assert params["cap"] is False

    def test_create_line_sends_start_and_end(self):
        fc = _fc({"guid": "line-guid"})
        with patch.object(_creation_mod, "get_connection", return_value=fc):
            _creation_mod.create_line(
                start_x=0.0, start_y=0.0, start_z=0.0,
                end_x=10.0, end_y=0.0, end_z=0.0,
            )

        params = fc.last_call()["params"]
        assert params["start"] == {"x": 0.0, "y": 0.0, "z": 0.0}
        assert params["end"] == {"x": 10.0, "y": 0.0, "z": 0.0}

    def test_create_circle_sends_radius(self):
        fc = _fc({"guid": "circle-guid"})
        with patch.object(_creation_mod, "get_connection", return_value=fc):
            _creation_mod.create_circle(
                center_x=0.0, center_y=0.0, center_z=0.0, radius=5.0
            )

        assert fc.last_call()["params"]["radius"] == 5.0

    def test_create_arc_sends_angles(self):
        fc = _fc({"guid": "arc-guid"})
        with patch.object(_creation_mod, "get_connection", return_value=fc):
            _creation_mod.create_arc(
                center_x=0.0, center_y=0.0, center_z=0.0,
                radius=3.0, start_angle=0.0, end_angle=90.0,
            )

        params = fc.last_call()["params"]
        assert params["start_angle"] == 0.0
        assert params["end_angle"] == 90.0

    def test_create_box_defaults(self):
        """Default arguments produce the expected default params."""
        fc = _fc({})
        with patch.object(_creation_mod, "get_connection", return_value=fc):
            _creation_mod.create_box()

        params = fc.last_call()["params"]
        assert params["corner"] == {"x": 0.0, "y": 0.0, "z": 0.0}
        assert params["width"] == 1.0
        assert params["layer"] is None
        assert params["name"] is None

    def test_create_text_sends_text_and_position(self):
        fc = _fc({"guid": "text-guid"})
        with patch.object(_creation_mod, "get_connection", return_value=fc):
            _creation_mod.create_text(
                text="Hello World",
                position_x=5.0, position_y=0.0, position_z=0.0,
                height=2.0,
            )

        params = fc.last_call()["params"]
        assert params["text"] == "Hello World"
        assert params["position"]["x"] == 5.0
        assert params["height"] == 2.0


# ---------------------------------------------------------------------------
# Operations tools
# ---------------------------------------------------------------------------

class TestOperationsTools:

    def test_boolean_union_sends_correct_params(self):
        guids = ["g1", "g2"]
        fc = _fc({"guid": "union-result"})
        with patch.object(_operations_mod, "get_connection", return_value=fc):
            result = _operations_mod.boolean_union(guids=guids, delete_input=True)

        assert fc.last_call()["method"] == "operations.boolean_union"
        params = fc.last_call()["params"]
        assert params["guids"] == guids
        assert params["delete_input"] is True
        assert result == {"guid": "union-result"}

    def test_boolean_difference_sends_target_and_cutter(self):
        fc = _fc({"guid": "diff-result"})
        with patch.object(_operations_mod, "get_connection", return_value=fc):
            _operations_mod.boolean_difference(
                target_guids=["base"], cutter_guids=["tool"], delete_input=False
            )

        params = fc.last_call()["params"]
        assert params["target_guids"] == ["base"]
        assert params["cutter_guids"] == ["tool"]
        assert params["delete_input"] is False

    def test_boolean_intersection_sends_guids(self):
        fc = _fc({"guid": "int-result"})
        with patch.object(_operations_mod, "get_connection", return_value=fc):
            _operations_mod.boolean_intersection(guids=["a", "b"])

        assert fc.last_call()["method"] == "operations.boolean_intersection"
        assert fc.last_call()["params"]["guids"] == ["a", "b"]

    def test_join_curves_sends_correct_params(self):
        fc = _fc({"guids": ["joined"]})
        with patch.object(_operations_mod, "get_connection", return_value=fc):
            _operations_mod.join_curves(guids=["c1", "c2"], delete_input=True)

        params = fc.last_call()["params"]
        assert params["guids"] == ["c1", "c2"]
        assert params["delete_input"] is True

    def test_mirror_objects_sends_plane(self):
        fc = _fc({"guids": ["mirrored"]})
        with patch.object(_operations_mod, "get_connection", return_value=fc):
            _operations_mod.mirror_objects(
                guids=["obj"],
                plane_origin_x=0.0, plane_origin_y=0.0, plane_origin_z=0.0,
                plane_normal_x=1.0, plane_normal_y=0.0, plane_normal_z=0.0,
                copy=True,
            )

        params = fc.last_call()["params"]
        assert params["plane_origin"] == {"x": 0.0, "y": 0.0, "z": 0.0}
        assert params["plane_normal"] == {"x": 1.0, "y": 0.0, "z": 0.0}
        assert params["copy"] is True

    def test_offset_curve_sends_distance_and_style(self):
        fc = _fc({"guid": "offset-guid"})
        with patch.object(_operations_mod, "get_connection", return_value=fc):
            _operations_mod.offset_curve(
                guid="curve-guid", distance=2.0, corner_style="Round"
            )

        params = fc.last_call()["params"]
        assert params["distance"] == 2.0
        assert params["corner_style"] == "Round"

    def test_fillet_curves_sends_radius_and_flags(self):
        fc = _fc({"guid": "fillet-guid"})
        with patch.object(_operations_mod, "get_connection", return_value=fc):
            _operations_mod.fillet_curves(
                guid1="c1", guid2="c2", radius=0.5, extend=True, trim=True
            )

        params = fc.last_call()["params"]
        assert params["radius"] == 0.5
        assert params["extend"] is True
        assert params["trim"] is True


# ---------------------------------------------------------------------------
# Manipulation tools
# ---------------------------------------------------------------------------

class TestManipulationTools:

    def test_move_objects_sends_correct_params(self):
        guids = ["obj1", "obj2"]
        fc = _fc({"guids": guids})
        with patch.object(_manipulation_mod, "get_connection", return_value=fc):
            result = _manipulation_mod.move_objects(
                guids=guids,
                translation_x=5.0, translation_y=0.0, translation_z=2.0,
            )

        assert fc.last_call()["method"] == "manipulation.move_objects"
        params = fc.last_call()["params"]
        assert params["guids"] == guids
        assert params["translation"] == {"x": 5.0, "y": 0.0, "z": 2.0}
        assert result == {"guids": guids}

    def test_rotate_objects_sends_angle_and_axis(self):
        fc = _fc({"guids": ["r"]})
        with patch.object(_manipulation_mod, "get_connection", return_value=fc):
            _manipulation_mod.rotate_objects(
                guids=["obj"],
                angle_degrees=45.0,
                axis_z=1.0,
                copy=True,
            )

        params = fc.last_call()["params"]
        assert params["angle_degrees"] == 45.0
        assert params["copy"] is True

    def test_scale_objects_sends_scale_factors(self):
        fc = _fc({"guids": ["s"]})
        with patch.object(_manipulation_mod, "get_connection", return_value=fc):
            _manipulation_mod.scale_objects(
                guids=["obj"], scale_x=2.0, scale_y=2.0, scale_z=2.0
            )

        params = fc.last_call()["params"]
        assert params["scale"] == {"x": 2.0, "y": 2.0, "z": 2.0}

    def test_copy_objects_sends_translation(self):
        fc = _fc({"guids": ["copy1"]})
        with patch.object(_manipulation_mod, "get_connection", return_value=fc):
            _manipulation_mod.copy_objects(guids=["src"], translation_x=10.0)

        params = fc.last_call()["params"]
        assert params["translation"]["x"] == 10.0

    def test_align_objects_sends_alignment_and_axis(self):
        fc = _fc({})
        with patch.object(_manipulation_mod, "get_connection", return_value=fc):
            _manipulation_mod.align_objects(
                guids=["a", "b"], alignment="min", axis="z"
            )

        params = fc.last_call()["params"]
        assert params["alignment"] == "min"
        assert params["axis"] == "z"

    def test_apply_transform_sends_matrix(self):
        identity = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
        fc = _fc({"guids": ["t"]})
        with patch.object(_manipulation_mod, "get_connection", return_value=fc):
            _manipulation_mod.apply_transform(guids=["obj"], matrix=identity)

        params = fc.last_call()["params"]
        assert params["matrix"] == identity


# ---------------------------------------------------------------------------
# Viewport tools
# ---------------------------------------------------------------------------

class TestViewportTools:

    def test_capture_viewport_sends_correct_params(self):
        fc = _fc({
            "image": "base64datahere",
            "width": 1920, "height": 1080,
            "view_name": "Perspective",
            "display_mode": "Shaded",
        })
        with patch.object(_viewport_mod, "get_connection", return_value=fc):
            result = _viewport_mod.capture_viewport(
                view_name="Perspective",
                width=1920, height=1080,
                display_mode="Shaded",
                transparent_background=False,
            )

        assert fc.last_call()["method"] == "viewport.capture"
        params = fc.last_call()["params"]
        assert params["view_name"] == "Perspective"
        assert params["width"] == 1920
        assert params["height"] == 1080
        assert params["display_mode"] == "Shaded"
        assert params["transparent_background"] is False
        assert result["image"] == "base64datahere"

    def test_capture_viewport_default_params(self):
        """Omitting optional args uses sane defaults."""
        fc = _fc({"image": "data"})
        with patch.object(_viewport_mod, "get_connection", return_value=fc):
            _viewport_mod.capture_viewport()

        params = fc.last_call()["params"]
        assert params["view_name"] is None
        assert params["width"] == 1920
        assert params["height"] == 1080

    def test_set_display_mode_sends_mode(self):
        fc = _fc({})
        with patch.object(_viewport_mod, "get_connection", return_value=fc):
            _viewport_mod.set_display_mode(mode="Rendered")

        assert fc.last_call()["params"]["mode"] == "Rendered"

    def test_zoom_extents_sends_correct_params(self):
        fc = _fc({})
        with patch.object(_viewport_mod, "get_connection", return_value=fc):
            _viewport_mod.zoom_extents(selected_only=True)

        params = fc.last_call()["params"]
        assert params["selected_only"] is True

    def test_set_camera_sends_location_and_target(self):
        fc = _fc({})
        with patch.object(_viewport_mod, "get_connection", return_value=fc):
            _viewport_mod.set_camera(
                location_x=10.0, location_y=10.0, location_z=5.0,
                target_x=0.0, target_y=0.0, target_z=0.0,
            )

        params = fc.last_call()["params"]
        assert params["location"] == {"x": 10.0, "y": 10.0, "z": 5.0}
        assert params["target"] == {"x": 0.0, "y": 0.0, "z": 0.0}

    def test_zoom_selected_sends_guids(self):
        fc = _fc({})
        with patch.object(_viewport_mod, "get_connection", return_value=fc):
            _viewport_mod.zoom_selected(guids=["z1", "z2"])

        assert fc.last_call()["params"]["guids"] == ["z1", "z2"]


# ---------------------------------------------------------------------------
# Files tools
# ---------------------------------------------------------------------------

class TestFilesTools:

    def test_save_document_sends_correct_method(self):
        fc = _fc({"success": True})
        with patch.object(_files_mod, "get_connection", return_value=fc):
            result = _files_mod.save_document()

        assert fc.last_call()["method"] == "files.save_document"
        assert fc.last_call()["params"] == {}
        assert result == {"success": True}

    def test_save_document_as_sends_path_and_overwrite(self):
        fc = _fc({"success": True})
        with patch.object(_files_mod, "get_connection", return_value=fc):
            _files_mod.save_document_as(file_path="/tmp/model.3dm", overwrite=True)

        params = fc.last_call()["params"]
        assert params["file_path"] == "/tmp/model.3dm"
        assert params["overwrite"] is True

    def test_new_document_sends_units(self):
        fc = _fc({})
        with patch.object(_files_mod, "get_connection", return_value=fc):
            _files_mod.new_document(units="Meters")

        assert fc.last_call()["params"]["units"] == "Meters"

    def test_export_objects_sends_guids_and_path(self):
        guids = ["g1", "g2"]
        fc = _fc({"file_path": "/tmp/out.obj", "object_count": 2})
        with patch.object(_files_mod, "get_connection", return_value=fc):
            _files_mod.export_objects(
                guids=guids,
                file_path="/tmp/out.obj",
                overwrite=True,
            )

        params = fc.last_call()["params"]
        assert params["guids"] == guids
        assert params["file_path"] == "/tmp/out.obj"
        assert params["overwrite"] is True

    def test_import_file_sends_path(self):
        fc = _fc({"guids": [], "object_count": 0})
        with patch.object(_files_mod, "get_connection", return_value=fc):
            _files_mod.import_file(file_path="/tmp/model.obj")

        assert fc.last_call()["params"]["file_path"] == "/tmp/model.obj"

    def test_get_document_path_sends_correct_method(self):
        fc = _fc({"file_path": "/tmp/test.3dm", "is_modified": False})
        with patch.object(_files_mod, "get_connection", return_value=fc):
            result = _files_mod.get_document_path()

        assert fc.last_call()["method"] == "files.get_document_path"
        assert result["file_path"] == "/tmp/test.3dm"

    def test_export_document_sends_all_params(self):
        fc = _fc({"file_path": "/tmp/export.stl"})
        with patch.object(_files_mod, "get_connection", return_value=fc):
            _files_mod.export_document(
                file_path="/tmp/export.stl",
                file_format="STL",
                overwrite=False,
                selected_only=True,
            )

        params = fc.last_call()["params"]
        assert params["file_format"] == "STL"
        assert params["selected_only"] is True


# ---------------------------------------------------------------------------
# Scripting tools
# ---------------------------------------------------------------------------

class TestScriptingTools:

    def test_execute_python_sends_code(self):
        code = "print('hello')\n_output['x'] = 42"
        fc = _fc({"success": True, "output": {"x": 42}, "stdout": "hello\n"})
        with patch.object(_scripting_mod, "get_connection", return_value=fc):
            result = _scripting_mod.execute_python(code=code)

        assert fc.last_call()["method"] == "scripting.execute_python"
        params = fc.last_call()["params"]
        assert params["code"] == code
        assert params["capture_output"] is True
        assert result["output"] == {"x": 42}

    def test_execute_python_sends_context(self):
        fc = _fc({"success": True, "output": {}})
        ctx = {"my_var": 3.14}
        with patch.object(_scripting_mod, "get_connection", return_value=fc):
            _scripting_mod.execute_python(code="pass", context=ctx)

        assert fc.last_call()["params"]["context"] == ctx

    def test_execute_python_default_context_is_empty_dict(self):
        """When no context is given, an empty dict is sent (not None)."""
        fc = _fc({"success": True, "output": {}})
        with patch.object(_scripting_mod, "get_connection", return_value=fc):
            _scripting_mod.execute_python(code="x = 1")

        assert fc.last_call()["params"]["context"] == {}

    def test_execute_python_sends_timeout(self):
        fc = _fc({"success": True, "output": {}})
        with patch.object(_scripting_mod, "get_connection", return_value=fc):
            _scripting_mod.execute_python(code="pass", timeout_seconds=60)

        assert fc.last_call()["params"]["timeout_seconds"] == 60

    def test_run_rhino_command_sends_command_string(self):
        fc = _fc({"success": True, "command_result": 1})
        with patch.object(_scripting_mod, "get_connection", return_value=fc):
            result = _scripting_mod.run_rhino_command(
                command="_Move _Enter", echo=False
            )

        assert fc.last_call()["method"] == "scripting.run_rhino_command"
        assert fc.last_call()["params"]["command"] == "_Move _Enter"
        assert fc.last_call()["params"]["echo"] is False
        assert result["success"] is True

    def test_evaluate_expression_sends_expression_and_variables(self):
        fc = _fc({"value": 5.0, "type": "float"})
        with patch.object(_scripting_mod, "get_connection", return_value=fc):
            result = _scripting_mod.evaluate_expression(
                expression="x + y",
                variables={"x": 2.0, "y": 3.0},
            )

        params = fc.last_call()["params"]
        assert params["expression"] == "x + y"
        assert params["variables"] == {"x": 2.0, "y": 3.0}
        assert result["value"] == 5.0

    def test_evaluate_expression_default_variables_is_empty_dict(self):
        """When no variables are given, an empty dict is sent."""
        fc = _fc({"value": 42, "type": "int"})
        with patch.object(_scripting_mod, "get_connection", return_value=fc):
            _scripting_mod.evaluate_expression(expression="42")

        assert fc.last_call()["params"]["variables"] == {}

    def test_execute_rhinoscript_sends_code_and_timeout(self):
        fc = _fc({"success": True, "result": None})
        with patch.object(_scripting_mod, "get_connection", return_value=fc):
            _scripting_mod.execute_rhinoscript(
                code="MsgBox \"hello\"", timeout_seconds=15
            )

        params = fc.last_call()["params"]
        assert params["code"] == "MsgBox \"hello\""
        assert params["timeout_seconds"] == 15
