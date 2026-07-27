"""
golem_3dmcp/tools/scene.py
==========================
MCP tools for inspecting and querying the Rhino scene/document.

Registered tools:
  - get_document_info   — Document metadata (path, units, tolerance, counts)
  - list_layers         — All layers with colour/visibility/locked state
  - list_objects        — Objects with optional filters
  - get_object_info     — Full detail on a single object by GUID
  - get_selected_objects — Currently selected objects
  - list_views          — Named and active views
"""

from __future__ import annotations

from typing import Any

from golem_3dmcp.connection import get_connection
from golem_3dmcp.server import mcp


def _send(method: str, params: dict[str, Any]) -> dict[str, Any]:
    """Convenience wrapper: get connection and send a command."""
    conn = get_connection()
    return conn.send_command(method, params)


# ---------------------------------------------------------------------------
# Document info
# ---------------------------------------------------------------------------

@mcp.tool()
def get_document_info() -> dict[str, Any]:
    """
    Return high-level metadata about the currently open Rhino document:
    file path, unit system, tolerances, and object/layer counts.
    """
    return _send("scene.get_document_info", {})


# ---------------------------------------------------------------------------
# Layers
# ---------------------------------------------------------------------------

@mcp.tool()
def list_layers() -> dict[str, Any]:
    """
    List all layers in the Rhino document.

    Returns a list of layer objects, each containing:
    name, full_path, colour (r/g/b/a), visible, locked, parent, object_count.
    """
    return _send("scene.list_layers", {})


@mcp.tool()
def create_layer(
    name: str,
    color_r: int = 0,
    color_g: int = 0,
    color_b: int = 0,
    visible: bool = True,
    locked: bool = False,
    parent: str | None = None,
) -> dict[str, Any]:
    """
    Create a new layer in the Rhino document.

    Args:
        name:    Layer name.  Use '::' as a separator for nested layers,
                 e.g. 'Site::Buildings::Walls'.
        color_r: Red channel of the layer colour (0-255).
        color_g: Green channel (0-255).
        color_b: Blue channel (0-255).
        visible: Whether the layer is initially visible.
        locked:  Whether the layer is initially locked.
        parent:  Full path of the parent layer, or None for top-level.
    """
    return _send("scene.create_layer", {
        "name": name,
        "color": {"r": color_r, "g": color_g, "b": color_b, "a": 255},
        "visible": visible,
        "locked": locked,
        "parent": parent,
    })


@mcp.tool()
def delete_layer(name: str, delete_objects: bool = False) -> dict[str, Any]:
    """
    Delete a layer from the document.

    Args:
        name:           Full layer path to delete.
        delete_objects: If True, objects on this layer are deleted too.
                        If False, the operation fails when objects exist on
                        the layer.
    """
    return _send("scene.delete_layer", {
        "name": name,
        "delete_objects": delete_objects,
    })


# ---------------------------------------------------------------------------
# Objects
# ---------------------------------------------------------------------------

@mcp.tool()
def list_objects(
    layer: str | None = None,
    object_type: str | None = None,
    name: str | None = None,
    visible_only: bool = False,
    unlocked_only: bool = False,
) -> dict[str, Any]:
    """
    List objects in the Rhino document with optional filters.

    All filter arguments are optional; omitting them returns all objects.

    Args:
        layer:         Return only objects on this layer (full path).
        object_type:   Filter by geometry type: 'brep', 'curve', 'mesh',
                       'point', 'extrusion', 'subd', etc.
        name:          Return objects whose name contains this substring.
        visible_only:  Exclude hidden objects when True.
        unlocked_only: Exclude locked objects when True.
    """
    return _send("scene.list_objects", {
        "layer": layer,
        "object_type": object_type,
        "name": name,
        "visible_only": visible_only,
        "unlocked_only": unlocked_only,
    })


@mcp.tool()
def get_object_info(guid: str) -> dict[str, Any]:
    """
    Return full detail for a single Rhino object identified by its GUID.

    The response includes: guid, type, layer, name, colour, visible, locked,
    bounding_box, user_text key-value pairs, and a geometry summary.

    Args:
        guid: The object GUID as a string (braces optional).
    """
    return _send("scene.get_object_info", {"guid": guid})


@mcp.tool()
def get_selected_objects() -> dict[str, Any]:
    """
    Return all currently selected objects in the Rhino viewport.

    Returns the same per-object detail format as get_object_info.
    """
    return _send("scene.get_selected_objects", {})


@mcp.tool()
def select_objects(guids: list[str]) -> dict[str, Any]:
    """
    Select a list of objects in the Rhino viewport by GUID.

    Args:
        guids: List of object GUIDs to select.
    """
    return _send("scene.select_objects", {"guids": guids})


@mcp.tool()
def deselect_all() -> dict[str, Any]:
    """Deselect all objects in the Rhino viewport."""
    return _send("scene.deselect_all", {})


@mcp.tool()
def delete_objects(guids: list[str]) -> dict[str, Any]:
    """
    Delete one or more objects from the Rhino document.

    Args:
        guids: List of object GUIDs to delete.
    """
    return _send("scene.delete_objects", {"guids": guids})


@mcp.tool()
def hide_objects(guids: list[str], hide: bool = True) -> dict[str, Any]:
    """
    Hide or show objects in the Rhino document.

    Args:
        guids: List of object GUIDs.
        hide:  True to hide, False to show.
    """
    return _send("scene.hide_objects", {"guids": guids, "hide": hide})


@mcp.tool()
def lock_objects(guids: list[str], lock: bool = True) -> dict[str, Any]:
    """
    Lock or unlock objects in the Rhino document.

    Args:
        guids: List of object GUIDs.
        lock:  True to lock, False to unlock.
    """
    return _send("scene.lock_objects", {"guids": guids, "lock": lock})


@mcp.tool()
def set_object_layer(guids: list[str], layer: str) -> dict[str, Any]:
    """
    Move one or more objects to a different layer.

    Args:
        guids: List of object GUIDs.
        layer: Full layer path to move the objects to.
    """
    return _send("scene.set_object_layer", {"guids": guids, "layer": layer})


@mcp.tool()
def set_object_name(guid: str, name: str) -> dict[str, Any]:
    """
    Assign a name to a Rhino object.

    Args:
        guid: Object GUID.
        name: New name string.
    """
    return _send("scene.set_object_name", {"guid": guid, "name": name})


@mcp.tool()
def set_user_text(guid: str, key: str, value: str) -> dict[str, Any]:
    """
    Set a user-text key-value pair on an object.

    Args:
        guid:  Object GUID.
        key:   User-text key.
        value: User-text value.
    """
    return _send("scene.set_user_text", {"guid": guid, "key": key, "value": value})


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------

@mcp.tool()
def list_views() -> dict[str, Any]:
    """
    List all named views in the document plus the currently active view.

    Each view entry includes: name, is_perspective, camera_location,
    camera_target, display_mode.
    """
    return _send("scene.list_views", {})


@mcp.tool()
def set_active_view(view_name: str) -> dict[str, Any]:
    """
    Set the active Rhino viewport by name.

    Args:
        view_name: View name, e.g. 'Perspective', 'Top', 'Front', 'Right'.
    """
    return _send("scene.set_active_view", {"view_name": view_name})
