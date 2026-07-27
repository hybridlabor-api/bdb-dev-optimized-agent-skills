"""
mcp_server/tools/operations.py
================================
MCP tools for boolean and geometric operations on Rhino objects.

Registered tools:
  - boolean_union
  - boolean_difference
  - boolean_intersection
  - mirror_objects
  - array_objects_linear
  - array_objects_polar
  - group_objects
  - ungroup_objects
  - join_curves
  - explode_object
  - trim_curve
  - extend_curve
  - offset_curve
  - fillet_curves
  - chamfer_curves
"""

from __future__ import annotations

from typing import Any, Optional

from mcp_server.server import mcp
from mcp_server.connection import get_connection


def _send(method: str, params: dict) -> dict:
    return get_connection().send_command(method, params)


# ---------------------------------------------------------------------------
# Boolean operations
# ---------------------------------------------------------------------------

@mcp.tool()
def boolean_union(guids: list[str], delete_input: bool = True) -> dict[str, Any]:
    """
    Perform a Boolean union on two or more closed breps.

    All input objects must be closed (solid) breps.  The result is a single
    closed brep representing the union of all inputs.

    Args:
        guids:        List of two or more object GUIDs to union.
        delete_input: Delete the input objects after the operation if True.

    Returns:
        dict with 'guid' of the resulting object, or 'error' on failure.
    """
    return _send("operations.boolean_union", {
        "guids": guids,
        "delete_input": delete_input,
    })


@mcp.tool()
def boolean_difference(
    target_guids: list[str],
    cutter_guids: list[str],
    delete_input: bool = True,
) -> dict[str, Any]:
    """
    Subtract cutter breps from target breps (Boolean difference).

    Args:
        target_guids: GUIDs of the breps to cut from (the base solids).
        cutter_guids: GUIDs of the breps to cut with (the tools).
        delete_input: Delete input objects after the operation if True.
    """
    return _send("operations.boolean_difference", {
        "target_guids": target_guids,
        "cutter_guids": cutter_guids,
        "delete_input": delete_input,
    })


@mcp.tool()
def boolean_intersection(
    guids: list[str],
    delete_input: bool = True,
) -> dict[str, Any]:
    """
    Compute the Boolean intersection of two or more closed breps.

    The result is the solid volume common to all input breps.

    Args:
        guids:        List of two or more object GUIDs.
        delete_input: Delete input objects after the operation if True.
    """
    return _send("operations.boolean_intersection", {
        "guids": guids,
        "delete_input": delete_input,
    })


# ---------------------------------------------------------------------------
# Transforms
# ---------------------------------------------------------------------------

@mcp.tool()
def mirror_objects(
    guids: list[str],
    plane_origin_x: float = 0.0,
    plane_origin_y: float = 0.0,
    plane_origin_z: float = 0.0,
    plane_normal_x: float = 1.0,
    plane_normal_y: float = 0.0,
    plane_normal_z: float = 0.0,
    copy: bool = True,
) -> dict[str, Any]:
    """
    Mirror objects across a plane defined by origin and normal vector.

    Args:
        guids:               GUIDs of objects to mirror.
        plane_origin_x/y/z:  A point on the mirror plane.
        plane_normal_x/y/z:  Normal vector of the mirror plane.
        copy:                Create mirrored copies if True; move the originals if False.
    """
    return _send("operations.mirror_objects", {
        "guids": guids,
        "plane_origin": {"x": plane_origin_x, "y": plane_origin_y, "z": plane_origin_z},
        "plane_normal": {"x": plane_normal_x, "y": plane_normal_y, "z": plane_normal_z},
        "copy": copy,
    })


@mcp.tool()
def array_objects_linear(
    guids: list[str],
    count_x: int = 2,
    count_y: int = 1,
    count_z: int = 1,
    spacing_x: float = 1.0,
    spacing_y: float = 1.0,
    spacing_z: float = 0.0,
) -> dict[str, Any]:
    """
    Create a rectangular (linear) array of objects.

    Args:
        guids:     GUIDs of the objects to array.
        count_x:   Number of copies along X (including the original).
        count_y:   Number of copies along Y.
        count_z:   Number of copies along Z.
        spacing_x: Distance between copies along X.
        spacing_y: Distance between copies along Y.
        spacing_z: Distance between copies along Z.
    """
    return _send("operations.array_objects_linear", {
        "guids": guids,
        "count_x": count_x,
        "count_y": count_y,
        "count_z": count_z,
        "spacing_x": spacing_x,
        "spacing_y": spacing_y,
        "spacing_z": spacing_z,
    })


@mcp.tool()
def array_objects_polar(
    guids: list[str],
    count: int = 6,
    center_x: float = 0.0,
    center_y: float = 0.0,
    center_z: float = 0.0,
    angle_degrees: float = 360.0,
) -> dict[str, Any]:
    """
    Create a polar (rotational) array of objects around a centre point.

    Args:
        guids:         GUIDs of the objects to array.
        count:         Total number of copies (including the original).
        center_x/y/z:  Centre point of the polar array.
        angle_degrees: Total angle to distribute copies over (default 360 = full circle).
    """
    return _send("operations.array_objects_polar", {
        "guids": guids,
        "count": count,
        "center": {"x": center_x, "y": center_y, "z": center_z},
        "angle_degrees": angle_degrees,
    })


# ---------------------------------------------------------------------------
# Grouping
# ---------------------------------------------------------------------------

@mcp.tool()
def group_objects(guids: list[str], group_name: Optional[str] = None) -> dict[str, Any]:
    """
    Group objects together.

    Args:
        guids:       GUIDs of the objects to group.
        group_name:  Optional name for the group.

    Returns:
        dict with 'group_name' of the created group.
    """
    return _send("operations.group_objects", {
        "guids": guids,
        "group_name": group_name,
    })


@mcp.tool()
def ungroup_objects(guids: list[str]) -> dict[str, Any]:
    """
    Remove objects from their groups.

    Args:
        guids: GUIDs of the objects to ungroup.
    """
    return _send("operations.ungroup_objects", {"guids": guids})


# ---------------------------------------------------------------------------
# Curve operations
# ---------------------------------------------------------------------------

@mcp.tool()
def join_curves(guids: list[str], delete_input: bool = True) -> dict[str, Any]:
    """
    Join multiple open curves into one or more polycurves.

    Curves must be within the document tolerance of each other at their
    endpoints to be joinable.

    Args:
        guids:        GUIDs of the curves to join.
        delete_input: Delete the input curves after joining if True.
    """
    return _send("operations.join_curves", {
        "guids": guids,
        "delete_input": delete_input,
    })


@mcp.tool()
def explode_object(guid: str, delete_input: bool = True) -> dict[str, Any]:
    """
    Explode a polycurve, brep, or group into its component parts.

    Args:
        guid:         GUID of the object to explode.
        delete_input: Delete the input object after exploding if True.
    """
    return _send("operations.explode_object", {
        "guid": guid,
        "delete_input": delete_input,
    })


@mcp.tool()
def offset_curve(
    guid: str,
    distance: float = 1.0,
    direction_x: float = 0.0,
    direction_y: float = 0.0,
    direction_z: float = 1.0,
    corner_style: str = "Sharp",
) -> dict[str, Any]:
    """
    Offset a curve by a specified distance.

    Args:
        guid:            GUID of the curve to offset.
        distance:        Offset distance (positive = left of curve direction).
        direction_x/y/z: Normal direction of the offset plane.
        corner_style:    How sharp corners are handled: 'Sharp', 'Round', 'Smooth', 'Chamfer'.
    """
    return _send("operations.offset_curve", {
        "guid": guid,
        "distance": distance,
        "plane_normal": {"x": direction_x, "y": direction_y, "z": direction_z},
        "corner_style": corner_style,
    })


@mcp.tool()
def fillet_curves(
    guid1: str,
    guid2: str,
    radius: float = 1.0,
    extend: bool = True,
    trim: bool = True,
) -> dict[str, Any]:
    """
    Create a fillet arc between two curves.

    Args:
        guid1:   GUID of the first curve.
        guid2:   GUID of the second curve.
        radius:  Fillet radius.
        extend:  Extend curves to meet if True.
        trim:    Trim curves at the fillet tangent points if True.
    """
    return _send("operations.fillet_curves", {
        "guid1": guid1,
        "guid2": guid2,
        "radius": radius,
        "extend": extend,
        "trim": trim,
    })
