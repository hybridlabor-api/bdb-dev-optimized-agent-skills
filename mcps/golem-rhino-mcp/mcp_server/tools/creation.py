"""
mcp_server/tools/creation.py
=============================
MCP tools for creating primitive geometry in Rhino.

Registered tools:
  - create_box
  - create_sphere
  - create_cylinder
  - create_cone
  - create_torus
  - create_line
  - create_arc
  - create_circle
  - create_polyline
  - create_nurbs_curve
  - create_point
  - create_text
"""

from __future__ import annotations

from typing import Any, Optional

from mcp_server.server import mcp
from mcp_server.connection import get_connection


def _send(method: str, params: dict) -> dict:
    return get_connection().send_command(method, params)


# ---------------------------------------------------------------------------
# Primitive solids
# ---------------------------------------------------------------------------

@mcp.tool()
def create_box(
    corner_x: float = 0.0,
    corner_y: float = 0.0,
    corner_z: float = 0.0,
    width: float = 1.0,
    depth: float = 1.0,
    height: float = 1.0,
    layer: Optional[str] = None,
    name: Optional[str] = None,
) -> dict[str, Any]:
    """
    Create a rectangular box (cuboid) in the Rhino document.

    The box is axis-aligned.  The corner point is the minimum XYZ corner.

    Args:
        corner_x: X coordinate of the minimum corner.
        corner_y: Y coordinate of the minimum corner.
        corner_z: Z coordinate of the minimum corner.
        width:    Dimension along the X axis (must be > 0).
        depth:    Dimension along the Y axis (must be > 0).
        height:   Dimension along the Z axis (must be > 0).
        layer:    Layer to place the object on (full path).
        name:     Optional object name.

    Returns:
        dict with 'guid' of the created object.
    """
    return _send("geometry.create_box", {
        "corner": {"x": corner_x, "y": corner_y, "z": corner_z},
        "width": width,
        "depth": depth,
        "height": height,
        "layer": layer,
        "name": name,
    })


@mcp.tool()
def create_sphere(
    center_x: float = 0.0,
    center_y: float = 0.0,
    center_z: float = 0.0,
    radius: float = 1.0,
    layer: Optional[str] = None,
    name: Optional[str] = None,
) -> dict[str, Any]:
    """
    Create a sphere in the Rhino document.

    Args:
        center_x: X coordinate of the sphere centre.
        center_y: Y coordinate of the sphere centre.
        center_z: Z coordinate of the sphere centre.
        radius:   Sphere radius (must be > 0).
        layer:    Layer to place the object on.
        name:     Optional object name.
    """
    return _send("geometry.create_sphere", {
        "center": {"x": center_x, "y": center_y, "z": center_z},
        "radius": radius,
        "layer": layer,
        "name": name,
    })


@mcp.tool()
def create_cylinder(
    base_x: float = 0.0,
    base_y: float = 0.0,
    base_z: float = 0.0,
    height: float = 1.0,
    radius: float = 1.0,
    cap: bool = True,
    layer: Optional[str] = None,
    name: Optional[str] = None,
) -> dict[str, Any]:
    """
    Create a cylinder in the Rhino document.

    The cylinder is aligned with the world Z axis.

    Args:
        base_x:  X coordinate of the base circle centre.
        base_y:  Y coordinate of the base circle centre.
        base_z:  Z coordinate of the base circle centre.
        height:  Cylinder height along Z (must be > 0).
        radius:  Circle radius (must be > 0).
        cap:     Cap both ends if True (closed solid).
        layer:   Layer to place the object on.
        name:    Optional object name.
    """
    return _send("geometry.create_cylinder", {
        "base_center": {"x": base_x, "y": base_y, "z": base_z},
        "height": height,
        "radius": radius,
        "cap": cap,
        "layer": layer,
        "name": name,
    })


@mcp.tool()
def create_cone(
    base_x: float = 0.0,
    base_y: float = 0.0,
    base_z: float = 0.0,
    radius: float = 1.0,
    height: float = 1.0,
    cap: bool = True,
    layer: Optional[str] = None,
    name: Optional[str] = None,
) -> dict[str, Any]:
    """
    Create a cone aligned with the world Z axis.

    Args:
        base_x: X coordinate of the base circle centre.
        base_y: Y coordinate.
        base_z: Z coordinate.
        radius: Base circle radius (must be > 0).
        height: Cone height (must be > 0).
        cap:    Cap the base if True.
        layer:  Layer to place the object on.
        name:   Optional object name.
    """
    return _send("geometry.create_cone", {
        "base_center": {"x": base_x, "y": base_y, "z": base_z},
        "radius": radius,
        "height": height,
        "cap": cap,
        "layer": layer,
        "name": name,
    })


@mcp.tool()
def create_torus(
    center_x: float = 0.0,
    center_y: float = 0.0,
    center_z: float = 0.0,
    major_radius: float = 2.0,
    minor_radius: float = 0.5,
    layer: Optional[str] = None,
    name: Optional[str] = None,
) -> dict[str, Any]:
    """
    Create a torus in the world XY plane.

    Args:
        center_x:     X coordinate of the torus centre.
        center_y:     Y coordinate.
        center_z:     Z coordinate.
        major_radius: Distance from torus centre to tube centre (must be > 0).
        minor_radius: Radius of the tube cross-section (must be > 0 and
                      less than major_radius).
        layer:        Layer to place the object on.
        name:         Optional object name.
    """
    return _send("geometry.create_torus", {
        "center": {"x": center_x, "y": center_y, "z": center_z},
        "major_radius": major_radius,
        "minor_radius": minor_radius,
        "layer": layer,
        "name": name,
    })


# ---------------------------------------------------------------------------
# Curves
# ---------------------------------------------------------------------------

@mcp.tool()
def create_line(
    start_x: float = 0.0,
    start_y: float = 0.0,
    start_z: float = 0.0,
    end_x: float = 1.0,
    end_y: float = 0.0,
    end_z: float = 0.0,
    layer: Optional[str] = None,
    name: Optional[str] = None,
) -> dict[str, Any]:
    """
    Create a straight line curve.

    Args:
        start_x/y/z: Start point coordinates.
        end_x/y/z:   End point coordinates.
        layer:        Layer to place the object on.
        name:         Optional object name.
    """
    return _send("geometry.create_line", {
        "start": {"x": start_x, "y": start_y, "z": start_z},
        "end": {"x": end_x, "y": end_y, "z": end_z},
        "layer": layer,
        "name": name,
    })


@mcp.tool()
def create_arc(
    center_x: float = 0.0,
    center_y: float = 0.0,
    center_z: float = 0.0,
    radius: float = 1.0,
    start_angle: float = 0.0,
    end_angle: float = 90.0,
    layer: Optional[str] = None,
    name: Optional[str] = None,
) -> dict[str, Any]:
    """
    Create an arc in the world XY plane.

    Args:
        center_x/y/z: Centre point coordinates.
        radius:        Arc radius (must be > 0).
        start_angle:   Start angle in degrees.
        end_angle:     End angle in degrees.
        layer:         Layer to place the object on.
        name:          Optional object name.
    """
    return _send("geometry.create_arc", {
        "center": {"x": center_x, "y": center_y, "z": center_z},
        "radius": radius,
        "start_angle": start_angle,
        "end_angle": end_angle,
        "layer": layer,
        "name": name,
    })


@mcp.tool()
def create_circle(
    center_x: float = 0.0,
    center_y: float = 0.0,
    center_z: float = 0.0,
    radius: float = 1.0,
    layer: Optional[str] = None,
    name: Optional[str] = None,
) -> dict[str, Any]:
    """
    Create a full circle curve in the world XY plane.

    Args:
        center_x/y/z: Centre point coordinates.
        radius:        Circle radius (must be > 0).
        layer:         Layer to place the object on.
        name:          Optional object name.
    """
    return _send("geometry.create_circle", {
        "center": {"x": center_x, "y": center_y, "z": center_z},
        "radius": radius,
        "layer": layer,
        "name": name,
    })


@mcp.tool()
def create_polyline(
    points: list[dict[str, float]],
    closed: bool = False,
    layer: Optional[str] = None,
    name: Optional[str] = None,
) -> dict[str, Any]:
    """
    Create a polyline through an ordered list of points.

    Args:
        points: List of point dicts, each with 'x', 'y', 'z' keys.
                Minimum 2 points required.
                Example: [{"x": 0, "y": 0, "z": 0}, {"x": 1, "y": 1, "z": 0}]
        closed: Connect the last point back to the first if True.
        layer:  Layer to place the object on.
        name:   Optional object name.
    """
    return _send("geometry.create_polyline", {
        "points": points,
        "closed": closed,
        "layer": layer,
        "name": name,
    })


@mcp.tool()
def create_nurbs_curve(
    points: list[dict[str, float]],
    degree: int = 3,
    interpolate: bool = True,
    weights: Optional[list[float]] = None,
    layer: Optional[str] = None,
    name: Optional[str] = None,
) -> dict[str, Any]:
    """
    Create a NURBS curve through (or near) a list of points.

    Args:
        points:      Ordered list of point dicts with 'x', 'y', 'z' keys.
                     Minimum 2 points required.
        degree:      Polynomial degree (1-11, default 3 = cubic).
        interpolate: If True the curve passes exactly through each point
                     (interpolated).  If False the points are NURBS control
                     points.
        weights:     Per-point rational weights (same length as points).
                     Uniform (all 1.0) if omitted.
        layer:       Layer to place the object on.
        name:        Optional object name.
    """
    return _send("geometry.create_nurbs_curve", {
        "points": points,
        "degree": degree,
        "interpolate": interpolate,
        "weights": weights,
        "layer": layer,
        "name": name,
    })


# ---------------------------------------------------------------------------
# Points and annotations
# ---------------------------------------------------------------------------

@mcp.tool()
def create_point(
    x: float = 0.0,
    y: float = 0.0,
    z: float = 0.0,
    layer: Optional[str] = None,
    name: Optional[str] = None,
) -> dict[str, Any]:
    """
    Create a point object in the Rhino document.

    Args:
        x/y/z: Point coordinates.
        layer: Layer to place the object on.
        name:  Optional object name.
    """
    return _send("geometry.create_point", {
        "location": {"x": x, "y": y, "z": z},
        "layer": layer,
        "name": name,
    })


@mcp.tool()
def create_text(
    text: str,
    position_x: float = 0.0,
    position_y: float = 0.0,
    position_z: float = 0.0,
    height: float = 1.0,
    font: str = "Arial",
    layer: Optional[str] = None,
    name: Optional[str] = None,
) -> dict[str, Any]:
    """
    Create a text annotation object in the Rhino document.

    Args:
        text:              The text string to display.
        position_x/y/z:   Position of the text origin.
        height:            Text height in model units.
        font:              Font name (e.g. 'Arial', 'Times New Roman').
        layer:             Layer to place the object on.
        name:              Optional object name.
    """
    return _send("geometry.create_text", {
        "text": text,
        "position": {"x": position_x, "y": position_y, "z": position_z},
        "height": height,
        "font": font,
        "layer": layer,
        "name": name,
    })
