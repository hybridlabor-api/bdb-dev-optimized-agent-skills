"""
mcp_server/tools/surfaces.py
==============================
MCP tools for creating surfaces and breps in Rhino.

Registered tools:
  - extrude_curve
  - loft_curves
  - revolve_curve
  - sweep_1_rail
  - sweep_2_rails
  - patch_surface
  - planar_surface
  - cap_planar_holes
  - offset_surface
  - mesh_from_surface
  - convert_to_nurbs
  - rebuild_surface
"""

from __future__ import annotations

from typing import Any, Optional

from mcp_server.server import mcp
from mcp_server.connection import get_connection


def _send(method: str, params: dict) -> dict:
    return get_connection().send_command(method, params)


# ---------------------------------------------------------------------------
# Surface creation
# ---------------------------------------------------------------------------

@mcp.tool()
def extrude_curve(
    profile_guid: str,
    direction_x: float = 0.0,
    direction_y: float = 0.0,
    direction_z: float = 1.0,
    distance: float = 1.0,
    cap: bool = True,
    layer: Optional[str] = None,
    name: Optional[str] = None,
) -> dict[str, Any]:
    """
    Extrude a curve profile along a direction vector to create a surface or solid.

    Args:
        profile_guid:        GUID of the curve to extrude.
        direction_x/y/z:     Extrusion direction vector.
        distance:            Extrusion distance (scales the direction vector).
        cap:                 Cap the ends if the profile is a closed curve.
        layer:               Layer for the result.
        name:                Optional result name.
    """
    return _send("surfaces.extrude_curve", {
        "profile_guid": profile_guid,
        "direction": {"x": direction_x, "y": direction_y, "z": direction_z},
        "distance": distance,
        "cap": cap,
        "layer": layer,
        "name": name,
    })


@mcp.tool()
def loft_curves(
    curve_guids: list[str],
    closed: bool = False,
    loft_type: str = "Normal",
    layer: Optional[str] = None,
    name: Optional[str] = None,
) -> dict[str, Any]:
    """
    Loft a surface through an ordered list of cross-section curves.

    Args:
        curve_guids: Ordered list of cross-section curve GUIDs (minimum 2).
        closed:      Close the loft back to the first section if True.
        loft_type:   Loft algorithm: 'Normal', 'Loose', 'Tight', 'Straight',
                     'Developable', 'Uniform'.
        layer:       Layer for the result.
        name:        Optional result name.
    """
    return _send("surfaces.loft_curves", {
        "curve_guids": curve_guids,
        "closed": closed,
        "loft_type": loft_type,
        "layer": layer,
        "name": name,
    })


@mcp.tool()
def revolve_curve(
    profile_guid: str,
    axis_start_x: float = 0.0,
    axis_start_y: float = 0.0,
    axis_start_z: float = 0.0,
    axis_end_x: float = 0.0,
    axis_end_y: float = 0.0,
    axis_end_z: float = 1.0,
    start_angle: float = 0.0,
    end_angle: float = 360.0,
    layer: Optional[str] = None,
    name: Optional[str] = None,
) -> dict[str, Any]:
    """
    Revolve a profile curve around an axis to create a surface of revolution.

    Args:
        profile_guid:          GUID of the profile curve.
        axis_start_x/y/z:      Start point of the revolution axis.
        axis_end_x/y/z:        End point of the revolution axis.
        start_angle:           Start angle in degrees (typically 0).
        end_angle:             End angle in degrees (360 = full revolution).
        layer:                 Layer for the result.
        name:                  Optional result name.
    """
    return _send("surfaces.revolve_curve", {
        "profile_guid": profile_guid,
        "axis_start": {"x": axis_start_x, "y": axis_start_y, "z": axis_start_z},
        "axis_end": {"x": axis_end_x, "y": axis_end_y, "z": axis_end_z},
        "start_angle": start_angle,
        "end_angle": end_angle,
        "layer": layer,
        "name": name,
    })


@mcp.tool()
def sweep_1_rail(
    rail_guid: str,
    cross_section_guids: list[str],
    closed: bool = False,
    layer: Optional[str] = None,
    name: Optional[str] = None,
) -> dict[str, Any]:
    """
    Create a surface by sweeping cross-section curves along a single rail curve.

    Args:
        rail_guid:             GUID of the rail (path) curve.
        cross_section_guids:   Ordered list of cross-section curve GUIDs.
        closed:                Close the sweep if True.
        layer:                 Layer for the result.
        name:                  Optional result name.
    """
    return _send("surfaces.sweep_1_rail", {
        "rail_guid": rail_guid,
        "cross_section_guids": cross_section_guids,
        "closed": closed,
        "layer": layer,
        "name": name,
    })


@mcp.tool()
def sweep_2_rails(
    rail1_guid: str,
    rail2_guid: str,
    cross_section_guids: list[str],
    closed: bool = False,
    layer: Optional[str] = None,
    name: Optional[str] = None,
) -> dict[str, Any]:
    """
    Create a surface by sweeping cross-sections along two rail curves.

    Args:
        rail1_guid:            GUID of the first rail curve.
        rail2_guid:            GUID of the second rail curve.
        cross_section_guids:   Ordered list of cross-section curve GUIDs.
        closed:                Close the sweep if True.
        layer:                 Layer for the result.
        name:                  Optional result name.
    """
    return _send("surfaces.sweep_2_rails", {
        "rail1_guid": rail1_guid,
        "rail2_guid": rail2_guid,
        "cross_section_guids": cross_section_guids,
        "closed": closed,
        "layer": layer,
        "name": name,
    })


@mcp.tool()
def patch_surface(
    input_guids: list[str],
    u_spans: int = 10,
    v_spans: int = 10,
    trim: bool = True,
    layer: Optional[str] = None,
    name: Optional[str] = None,
) -> dict[str, Any]:
    """
    Fit a patch surface to boundary curves and/or point objects.

    Args:
        input_guids: GUIDs of boundary curves, point objects, or a mix.
        u_spans:     Number of surface spans in U direction.
        v_spans:     Number of surface spans in V direction.
        trim:        Trim the surface to the boundary curves if True.
        layer:       Layer for the result.
        name:        Optional result name.
    """
    return _send("surfaces.patch_surface", {
        "input_guids": input_guids,
        "u_spans": u_spans,
        "v_spans": v_spans,
        "trim": trim,
        "layer": layer,
        "name": name,
    })


@mcp.tool()
def planar_surface(
    boundary_guid: str,
    layer: Optional[str] = None,
    name: Optional[str] = None,
) -> dict[str, Any]:
    """
    Create a planar surface from a closed planar curve boundary.

    Args:
        boundary_guid: GUID of a closed, planar curve.
        layer:         Layer for the result.
        name:          Optional result name.
    """
    return _send("surfaces.planar_surface", {
        "boundary_guid": boundary_guid,
        "layer": layer,
        "name": name,
    })


@mcp.tool()
def cap_planar_holes(guid: str) -> dict[str, Any]:
    """
    Cap all planar holes in a brep with flat surfaces.

    Args:
        guid: GUID of the brep to cap.

    Returns:
        dict with 'guid' of the modified brep and 'caps_added' count.
    """
    return _send("surfaces.cap_planar_holes", {"guid": guid})


@mcp.tool()
def offset_surface(
    guid: str,
    distance: float = 1.0,
    solid: bool = False,
    both_sides: bool = False,
) -> dict[str, Any]:
    """
    Offset a surface or brep by a specified distance.

    Args:
        guid:        GUID of the surface or brep to offset.
        distance:    Offset distance (positive = outward along normals).
        solid:       Create a solid by lofting between original and offset if True.
        both_sides:  Offset in both normal directions if True.
    """
    return _send("surfaces.offset_surface", {
        "guid": guid,
        "distance": distance,
        "solid": solid,
        "both_sides": both_sides,
    })


# ---------------------------------------------------------------------------
# Mesh operations
# ---------------------------------------------------------------------------

@mcp.tool()
def mesh_from_surface(
    source_guid: str,
    max_edge_length: Optional[float] = None,
    refine_mesh: bool = True,
    simple_planes: bool = False,
    layer: Optional[str] = None,
    name: Optional[str] = None,
) -> dict[str, Any]:
    """
    Create a mesh approximation of a brep or surface.

    Args:
        source_guid:      GUID of the brep or surface to mesh.
        max_edge_length:  Maximum mesh edge length.  Auto-calculated if None.
        refine_mesh:      Refine mesh for smoother result if True.
        simple_planes:    Use simple (coarser) meshing for planar faces if True.
        layer:            Layer for the resulting mesh.
        name:             Optional result name.
    """
    return _send("surfaces.mesh_from_surface", {
        "source_guid": source_guid,
        "max_edge_length": max_edge_length,
        "refine_mesh": refine_mesh,
        "simple_planes": simple_planes,
        "layer": layer,
        "name": name,
    })


@mcp.tool()
def convert_to_nurbs(guid: str, delete_input: bool = False) -> dict[str, Any]:
    """
    Convert an extrusion or SubD object to a NURBS brep.

    Args:
        guid:         GUID of the object to convert.
        delete_input: Delete the input object after conversion if True.
    """
    return _send("surfaces.convert_to_nurbs", {
        "guid": guid,
        "delete_input": delete_input,
    })


@mcp.tool()
def rebuild_surface(
    guid: str,
    point_count_u: int = 10,
    point_count_v: int = 10,
    degree_u: int = 3,
    degree_v: int = 3,
    delete_input: bool = False,
) -> dict[str, Any]:
    """
    Rebuild a surface with a new point count and degree.

    Args:
        guid:           GUID of the surface to rebuild.
        point_count_u:  Number of control points in U direction.
        point_count_v:  Number of control points in V direction.
        degree_u:       Polynomial degree in U direction (1-11).
        degree_v:       Polynomial degree in V direction (1-11).
        delete_input:   Delete the input surface if True.
    """
    return _send("surfaces.rebuild_surface", {
        "guid": guid,
        "point_count_u": point_count_u,
        "point_count_v": point_count_v,
        "degree_u": degree_u,
        "degree_v": degree_v,
        "delete_input": delete_input,
    })
