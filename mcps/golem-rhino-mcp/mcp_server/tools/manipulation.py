"""
mcp_server/tools/manipulation.py
==================================
MCP tools for transforming and manipulating existing Rhino objects.

Registered tools:
  - move_objects
  - rotate_objects
  - scale_objects
  - scale_objects_1d
  - scale_objects_2d
  - copy_objects
  - orient_objects
  - align_objects
  - distribute_objects
  - apply_transform
"""

from __future__ import annotations

from typing import Any, Optional

from mcp_server.server import mcp
from mcp_server.connection import get_connection


def _send(method: str, params: dict) -> dict:
    return get_connection().send_command(method, params)


# ---------------------------------------------------------------------------
# Move / Copy
# ---------------------------------------------------------------------------

@mcp.tool()
def move_objects(
    guids: list[str],
    translation_x: float = 0.0,
    translation_y: float = 0.0,
    translation_z: float = 0.0,
) -> dict[str, Any]:
    """
    Translate (move) objects by a displacement vector.

    Args:
        guids:           GUIDs of objects to move.
        translation_x/y/z: Translation vector components.
    """
    return _send("manipulation.move_objects", {
        "guids": guids,
        "translation": {"x": translation_x, "y": translation_y, "z": translation_z},
    })


@mcp.tool()
def copy_objects(
    guids: list[str],
    translation_x: float = 0.0,
    translation_y: float = 0.0,
    translation_z: float = 0.0,
) -> dict[str, Any]:
    """
    Copy objects and translate the copies by a displacement vector.

    Args:
        guids:             GUIDs of objects to copy.
        translation_x/y/z: Translation vector for the copies.

    Returns:
        dict with 'guids' list of the new (copied) object GUIDs.
    """
    return _send("manipulation.copy_objects", {
        "guids": guids,
        "translation": {"x": translation_x, "y": translation_y, "z": translation_z},
    })


# ---------------------------------------------------------------------------
# Rotate
# ---------------------------------------------------------------------------

@mcp.tool()
def rotate_objects(
    guids: list[str],
    angle_degrees: float = 90.0,
    center_x: float = 0.0,
    center_y: float = 0.0,
    center_z: float = 0.0,
    axis_x: float = 0.0,
    axis_y: float = 0.0,
    axis_z: float = 1.0,
    copy: bool = False,
) -> dict[str, Any]:
    """
    Rotate objects around an axis by a given angle.

    Args:
        guids:         GUIDs of objects to rotate.
        angle_degrees: Rotation angle in degrees (positive = counter-clockwise
                       when viewed along the axis from tip toward origin).
        center_x/y/z:  A point on the rotation axis.
        axis_x/y/z:    Rotation axis direction vector.
        copy:          Create rotated copies if True; rotate originals if False.
    """
    return _send("manipulation.rotate_objects", {
        "guids": guids,
        "angle_degrees": angle_degrees,
        "center": {"x": center_x, "y": center_y, "z": center_z},
        "axis": {"x": axis_x, "y": axis_y, "z": axis_z},
        "copy": copy,
    })


# ---------------------------------------------------------------------------
# Scale
# ---------------------------------------------------------------------------

@mcp.tool()
def scale_objects(
    guids: list[str],
    scale_x: float = 1.0,
    scale_y: float = 1.0,
    scale_z: float = 1.0,
    center_x: float = 0.0,
    center_y: float = 0.0,
    center_z: float = 0.0,
    copy: bool = False,
) -> dict[str, Any]:
    """
    Scale objects with independent X, Y, Z factors.

    For uniform scaling, set scale_x = scale_y = scale_z.

    Args:
        guids:         GUIDs of objects to scale.
        scale_x/y/z:   Scale factors for each axis (1.0 = no change).
        center_x/y/z:  Centre of scaling.
        copy:          Scale copies if True; scale originals if False.
    """
    return _send("manipulation.scale_objects", {
        "guids": guids,
        "scale": {"x": scale_x, "y": scale_y, "z": scale_z},
        "center": {"x": center_x, "y": center_y, "z": center_z},
        "copy": copy,
    })


@mcp.tool()
def scale_objects_1d(
    guids: list[str],
    scale_factor: float = 2.0,
    origin_x: float = 0.0,
    origin_y: float = 0.0,
    origin_z: float = 0.0,
    direction_x: float = 1.0,
    direction_y: float = 0.0,
    direction_z: float = 0.0,
    copy: bool = False,
) -> dict[str, Any]:
    """
    Scale objects along a single direction (1D scale).

    Args:
        guids:               GUIDs of objects to scale.
        scale_factor:        Scale factor along the direction.
        origin_x/y/z:        Scale origin point.
        direction_x/y/z:     Direction to scale along.
        copy:                Scale copies if True.
    """
    return _send("manipulation.scale_objects_1d", {
        "guids": guids,
        "scale_factor": scale_factor,
        "origin": {"x": origin_x, "y": origin_y, "z": origin_z},
        "direction": {"x": direction_x, "y": direction_y, "z": direction_z},
        "copy": copy,
    })


@mcp.tool()
def scale_objects_2d(
    guids: list[str],
    scale_x: float = 2.0,
    scale_y: float = 2.0,
    center_x: float = 0.0,
    center_y: float = 0.0,
    center_z: float = 0.0,
    copy: bool = False,
) -> dict[str, Any]:
    """
    Scale objects in two dimensions (planar scale preserving the third axis).

    Args:
        guids:         GUIDs of objects to scale.
        scale_x/y:     Scale factors in X and Y.
        center_x/y/z:  Centre of scaling.
        copy:          Scale copies if True.
    """
    return _send("manipulation.scale_objects_2d", {
        "guids": guids,
        "scale_x": scale_x,
        "scale_y": scale_y,
        "center": {"x": center_x, "y": center_y, "z": center_z},
        "copy": copy,
    })


# ---------------------------------------------------------------------------
# Orient / Align
# ---------------------------------------------------------------------------

@mcp.tool()
def orient_objects(
    guids: list[str],
    reference_points: list[dict[str, float]],
    target_points: list[dict[str, float]],
    copy: bool = False,
) -> dict[str, Any]:
    """
    Orient objects by mapping two or three reference points to target points.

    This is the Rhino Orient command: it defines a transformation by
    specifying where known reference points should end up.

    Args:
        guids:             GUIDs of objects to orient.
        reference_points:  List of 2 or 3 point dicts (from-locations).
        target_points:     List of 2 or 3 point dicts (to-locations).
        copy:              Orient copies if True; move originals if False.
    """
    return _send("manipulation.orient_objects", {
        "guids": guids,
        "reference_points": reference_points,
        "target_points": target_points,
        "copy": copy,
    })


@mcp.tool()
def align_objects(
    guids: list[str],
    alignment: str = "center",
    axis: str = "x",
) -> dict[str, Any]:
    """
    Align objects along a common axis.

    Args:
        guids:     GUIDs of objects to align.
        alignment: Alignment position: 'min', 'center', 'max'.
        axis:      Axis to align along: 'x', 'y', 'z'.
    """
    return _send("manipulation.align_objects", {
        "guids": guids,
        "alignment": alignment,
        "axis": axis,
    })


@mcp.tool()
def distribute_objects(
    guids: list[str],
    axis: str = "x",
    spacing: Optional[float] = None,
) -> dict[str, Any]:
    """
    Distribute objects evenly along an axis.

    Args:
        guids:   GUIDs of objects to distribute.
        axis:    Axis to distribute along: 'x', 'y', 'z'.
        spacing: Fixed spacing between objects.  If None, objects are evenly
                 spaced between the outermost two.
    """
    return _send("manipulation.distribute_objects", {
        "guids": guids,
        "axis": axis,
        "spacing": spacing,
    })


# ---------------------------------------------------------------------------
# Raw transform
# ---------------------------------------------------------------------------

@mcp.tool()
def apply_transform(
    guids: list[str],
    matrix: list[list[float]],
    copy: bool = False,
) -> dict[str, Any]:
    """
    Apply a 4x4 transformation matrix to objects.

    The matrix is provided as a nested list of 4 rows, each with 4 columns.
    This enables arbitrary affine transformations (translate, rotate, scale,
    shear) in a single call.

    Args:
        guids:  GUIDs of objects to transform.
        matrix: 4x4 transformation matrix as [[row0], [row1], [row2], [row3]].
                Example identity matrix:
                [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]
        copy:   Transform copies if True; transform originals if False.
    """
    return _send("manipulation.apply_transform", {
        "guids": guids,
        "matrix": matrix,
        "copy": copy,
    })
