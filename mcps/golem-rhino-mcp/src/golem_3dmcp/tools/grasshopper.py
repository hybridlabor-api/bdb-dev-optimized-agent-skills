"""
golem_3dmcp/tools/grasshopper.py
=================================
MCP tools for interacting with Grasshopper within Rhino.

Registered tools:
  - run_grasshopper_definition
  - get_grasshopper_outputs
  - set_grasshopper_input
  - open_grasshopper_definition
  - close_grasshopper_definition
  - list_grasshopper_components
  - bake_grasshopper_objects
"""

from __future__ import annotations

from typing import Any

from golem_3dmcp.connection import get_connection
from golem_3dmcp.server import mcp


def _send(method: str, params: dict[str, Any]) -> dict[str, Any]:
    return get_connection().send_command(method, params)


# ---------------------------------------------------------------------------
# Definition management
# ---------------------------------------------------------------------------

@mcp.tool()
def open_grasshopper_definition(file_path: str) -> dict[str, Any]:
    """
    Open a Grasshopper definition (.gh or .ghx) file.

    The definition is opened in the background (headless) — Grasshopper's
    canvas does not need to be visible.

    Args:
        file_path: Absolute path to the .gh or .ghx file.

    Returns:
        dict with 'definition_id' (a handle for subsequent calls),
        'input_names', and 'output_names'.
    """
    return _send("grasshopper.open_definition", {"file_path": file_path})


@mcp.tool()
def close_grasshopper_definition(definition_id: str | None = None) -> dict[str, Any]:
    """
    Close a Grasshopper definition that was previously opened.

    Args:
        definition_id: ID returned by open_grasshopper_definition.
                       If None, closes the currently active definition.
    """
    return _send("grasshopper.close_definition", {"definition_id": definition_id})


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------

@mcp.tool()
def run_grasshopper_definition(
    file_path: str | None = None,
    definition_id: str | None = None,
    inputs: dict[str, Any] | None = None,
    timeout_seconds: int = 60,
) -> dict[str, Any]:
    """
    Run a Grasshopper definition and return its outputs.

    Either file_path (to open and run) or definition_id (already open) must
    be provided.

    Args:
        file_path:        Absolute path to a .gh / .ghx file (opens it first).
        definition_id:    ID of an already-open definition.
        inputs:           Dict mapping component nickname -> value to set
                          before running.  Supports numbers, strings, and
                          point dicts {"x", "y", "z"}.
        timeout_seconds:  Maximum seconds to wait for the solution to complete.

    Returns:
        dict with 'outputs' mapping component nickname -> serialised value,
        'solution_time_ms', and 'warnings' list.
    """
    return _send("grasshopper.run_definition", {
        "file_path": file_path,
        "definition_id": definition_id,
        "inputs": inputs or {},
        "timeout_seconds": timeout_seconds,
    })


@mcp.tool()
def get_grasshopper_outputs(definition_id: str | None = None) -> dict[str, Any]:
    """
    Read the current output values from a Grasshopper definition without
    re-running it.

    Args:
        definition_id: ID of the definition.  Uses active definition if None.

    Returns:
        dict with 'outputs' mapping component nickname -> current value.
    """
    return _send("grasshopper.get_outputs", {"definition_id": definition_id})


# ---------------------------------------------------------------------------
# Input manipulation
# ---------------------------------------------------------------------------

@mcp.tool()
def set_grasshopper_input(
    component_name: str,
    value: Any,
    definition_id: str | None = None,
    run_after: bool = True,
) -> dict[str, Any]:
    """
    Set the value of a Grasshopper input component (number slider, panel,
    point parameter, etc.).

    Args:
        component_name: Nickname of the input component to set.
        value:          New value.  Supported types:
                        - float / int for sliders
                        - str for panel text
                        - {"x": float, "y": float, "z": float} for point params
                        - list of the above for list inputs
        definition_id:  ID of the target definition.  Active if None.
        run_after:      Trigger a new solution after setting the value if True.
    """
    return _send("grasshopper.set_input", {
        "component_name": component_name,
        "value": value,
        "definition_id": definition_id,
        "run_after": run_after,
    })


# ---------------------------------------------------------------------------
# Component inspection
# ---------------------------------------------------------------------------

@mcp.tool()
def list_grasshopper_components(
    definition_id: str | None = None,
    component_type: str | None = None,
) -> dict[str, Any]:
    """
    List components in the Grasshopper definition.

    Args:
        definition_id: ID of the definition.  Active if None.
        component_type: Filter by type: 'input', 'output', 'param', or None
                        for all components.

    Returns:
        dict with 'components' list.  Each entry has 'name', 'nickname',
        'type', 'category', and 'description'.
    """
    return _send("grasshopper.list_components", {
        "definition_id": definition_id,
        "component_type": component_type,
    })


# ---------------------------------------------------------------------------
# Baking
# ---------------------------------------------------------------------------

@mcp.tool()
def bake_grasshopper_objects(
    component_names: list[str] | None = None,
    definition_id: str | None = None,
    layer: str | None = None,
) -> dict[str, Any]:
    """
    Bake (commit) Grasshopper geometry into the Rhino document as persistent
    objects.

    Args:
        component_names: Names of output components to bake.  Bakes all
                         geometry outputs if None.
        definition_id:   ID of the definition.  Active if None.
        layer:           Layer to bake objects onto.  Uses the component's
                         default layer if None.

    Returns:
        dict with 'guids' list of the newly baked object GUIDs.
    """
    return _send("grasshopper.bake_objects", {
        "component_names": component_names,
        "definition_id": definition_id,
        "layer": layer,
    })
