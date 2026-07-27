"""
golem_3dmcp/tools/viewport.py
==============================
MCP tools for viewport capture and camera control in Rhino.

Registered tools:
  - capture_viewport
  - set_camera
  - zoom_extents
  - zoom_selected
  - set_display_mode
  - set_background_color
  - add_named_view
  - restore_named_view
"""

from __future__ import annotations

from typing import Any

from golem_3dmcp.connection import get_connection
from golem_3dmcp.server import mcp


def _send(method: str, params: dict[str, Any]) -> dict[str, Any]:
    return get_connection().send_command(method, params)


# ---------------------------------------------------------------------------
# Viewport capture
# ---------------------------------------------------------------------------

@mcp.tool()
def capture_viewport(
    view_name: str | None = None,
    width: int = 1920,
    height: int = 1080,
    display_mode: str | None = None,
    transparent_background: bool = False,
) -> dict[str, Any]:
    """
    Capture a Rhino viewport to a base64-encoded PNG image.

    Use this to visually inspect the current state of the model, verify
    geometry creation, or share a rendered view.

    Args:
        view_name:              Name of the viewport to capture (e.g. 'Perspective',
                                'Top', 'Front').  Captures the active viewport if None.
        width:                  Output image width in pixels (default 1920).
        height:                 Output image height in pixels (default 1080).
        display_mode:           Display mode for the capture: 'Wireframe', 'Shaded',
                                'Rendered', 'Arctic', 'Technical', 'Pen', 'Ghosted',
                                'X-Ray'.  Uses the viewport's current mode if None.
        transparent_background: Render with a transparent background if True
                                (useful for compositing).

    Returns:
        dict with:
          'image'       — base64-encoded PNG string
          'width'       — actual pixel width
          'height'      — actual pixel height
          'view_name'   — name of the view that was captured
          'display_mode'— display mode used for the capture
    """
    return _send("viewport.capture", {
        "view_name": view_name,
        "width": width,
        "height": height,
        "display_mode": display_mode,
        "transparent_background": transparent_background,
    })


# ---------------------------------------------------------------------------
# Camera control
# ---------------------------------------------------------------------------

@mcp.tool()
def set_camera(
    location_x: float = 0.0,
    location_y: float = -10.0,
    location_z: float = 5.0,
    target_x: float = 0.0,
    target_y: float = 0.0,
    target_z: float = 0.0,
    view_name: str | None = None,
    lens_length: float | None = None,
) -> dict[str, Any]:
    """
    Set the camera position and target for a Rhino viewport.

    Args:
        location_x/y/z: Camera position in world coordinates.
        target_x/y/z:   Camera target (look-at point) in world coordinates.
        view_name:       Name of the viewport to change.  Active viewport if None.
        lens_length:     Perspective lens length in mm.  35mm is typical.
                         Pass None to keep the current lens length.
    """
    return _send("viewport.set_camera", {
        "location": {"x": location_x, "y": location_y, "z": location_z},
        "target": {"x": target_x, "y": target_y, "z": target_z},
        "view_name": view_name,
        "lens_length": lens_length,
    })


@mcp.tool()
def zoom_extents(
    view_name: str | None = None,
    selected_only: bool = False,
) -> dict[str, Any]:
    """
    Zoom to the extents of all objects (or selected objects only).

    Args:
        view_name:     Name of the viewport.  Active viewport if None.
        selected_only: Zoom to the extents of selected objects only if True.
    """
    return _send("viewport.zoom_extents", {
        "view_name": view_name,
        "selected_only": selected_only,
    })


@mcp.tool()
def zoom_selected(guids: list[str], view_name: str | None = None) -> dict[str, Any]:
    """
    Zoom to show specific objects in a viewport.

    Args:
        guids:     GUIDs of objects to zoom to.
        view_name: Name of the viewport.  Active viewport if None.
    """
    return _send("viewport.zoom_selected", {
        "guids": guids,
        "view_name": view_name,
    })


# ---------------------------------------------------------------------------
# Display modes and appearance
# ---------------------------------------------------------------------------

@mcp.tool()
def set_display_mode(
    mode: str = "Shaded",
    view_name: str | None = None,
) -> dict[str, Any]:
    """
    Change the display mode of a Rhino viewport.

    Args:
        mode:      Display mode name: 'Wireframe', 'Shaded', 'Rendered',
                   'Arctic', 'Technical', 'Pen', 'Ghosted', 'X-Ray',
                   or any custom display mode name defined in Rhino.
        view_name: Name of the viewport.  Active viewport if None.
    """
    return _send("viewport.set_display_mode", {
        "mode": mode,
        "view_name": view_name,
    })


@mcp.tool()
def set_background_color(
    r: int = 255,
    g: int = 255,
    b: int = 255,
    view_name: str | None = None,
) -> dict[str, Any]:
    """
    Set the background colour of a Rhino viewport.

    Args:
        r/g/b:     Red, green, blue channels (0-255).
        view_name: Name of the viewport.  Active viewport if None.
    """
    return _send("viewport.set_background_color", {
        "color": {"r": r, "g": g, "b": b},
        "view_name": view_name,
    })


# ---------------------------------------------------------------------------
# Named views
# ---------------------------------------------------------------------------

@mcp.tool()
def add_named_view(
    view_name_to_save_as: str,
    source_view_name: str | None = None,
) -> dict[str, Any]:
    """
    Save the current camera position of a viewport as a named view.

    Args:
        view_name_to_save_as: Name under which to save the view.
        source_view_name:     Viewport whose camera to save.  Active viewport if None.
    """
    return _send("viewport.add_named_view", {
        "save_as": view_name_to_save_as,
        "source_view_name": source_view_name,
    })


@mcp.tool()
def restore_named_view(
    named_view: str,
    target_view_name: str | None = None,
    animate: bool = True,
) -> dict[str, Any]:
    """
    Restore a previously saved named view.

    Args:
        named_view:       Name of the saved view to restore.
        target_view_name: Viewport to restore the view in.  Active viewport if None.
        animate:          Animate the camera transition if True.
    """
    return _send("viewport.restore_named_view", {
        "named_view": named_view,
        "target_view_name": target_view_name,
        "animate": animate,
    })
