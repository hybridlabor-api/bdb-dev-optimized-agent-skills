# -*- coding: utf-8 -*-
"""
rhino_plugin/handlers/operations.py
=====================================
Geometry operations handler for GOLEM-3DMCP.

Covers:
  - Boolean operations    (union, difference, intersection, split)
  - Trim / Split          (trim, split)
  - Offset                (offset_curve, offset_surface)
  - Fillet / Chamfer      (fillet_edge, fillet_curves, chamfer_curves, chamfer_edge)
  - Intersection          (intersect -- auto-detects curve/surface combinations)
  - Meshing               (mesh_from_brep)
  - Curve operations      (project_curve, extend_curve, blend_curves, rebuild_curve,
                           rebuild_surface)

Design notes
------------
* Python 3.9 compatible -- no ``match``/``case``, no ``X | Y`` union syntax,
  no lower-case ``dict[str, ...]`` / ``list[str]`` generics in runtime annotations.
* Zero external dependencies -- only stdlib, Rhino, and rhinoscriptsyntax.
* All handlers are decorated with both ``@handler`` (dispatcher registration)
  and ``@wrap_handler`` (consistent exception-to-error-dict conversion).
* Booleans delete their input objects on success (as the Rhino UI does).
  Offset / project / blend / rebuild operations preserve originals.
* Every handler returns either a success payload dict or lets wrap_handler
  convert the exception into a GOLEM error dict.

Registers the following dispatcher methods::

    operations.boolean_union
    operations.boolean_difference
    operations.boolean_intersection
    operations.boolean_split
    operations.trim
    operations.split
    operations.offset_curve
    operations.offset_surface
    operations.fillet_edge
    operations.fillet_curves
    operations.chamfer_curves
    operations.chamfer_edge
    operations.intersect
    operations.mesh_from_brep
    operations.project_curve
    operations.extend_curve
    operations.blend_curves
    operations.rebuild_curve
    operations.rebuild_surface
"""

# ---------------------------------------------------------------------------
# Rhino imports -- wrapped in try/except so linters & test runners can import
# this module without exploding.  At runtime inside Rhino all will succeed.
# ---------------------------------------------------------------------------
try:
    import Rhino
    import Rhino.Geometry as RG
    import Rhino.Geometry.Intersect as RGI
    import scriptcontext as sc
    import rhinoscriptsyntax as rs
    import System
    _RHINO_AVAILABLE = True
except ImportError:
    _RHINO_AVAILABLE = False

try:
    from typing import Any, Dict, List, Optional
except ImportError:
    pass

from rhino_plugin.dispatcher import handler
from rhino_plugin.utils.error_handler import wrap_handler, GolemError, ErrorCode
from rhino_plugin.utils.guid_registry import registry
from rhino_plugin.utils.geometry_serializer import (
    serialize_brep,
    serialize_curve,
    serialize_mesh,
    serialize_surface,
    serialize_point3d,
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _require(params, key, expected_type=None):
    # type: (Dict[str, Any], str, Optional[type]) -> Any
    """
    Pull *key* from *params*, raising ``ValueError`` with a clear message if
    it is absent or the wrong type.
    """
    if key not in params:
        raise ValueError("Required parameter '{key}' is missing.".format(key=key))
    value = params[key]
    if expected_type is not None and not isinstance(value, expected_type):
        raise ValueError(
            "Parameter '{key}' must be a {tp} (got {actual}).".format(
                key=key,
                tp=expected_type.__name__,
                actual=type(value).__name__,
            )
        )
    return value


def _coerce_guid(guid_str):
    # type: (str) -> System.Guid
    """Parse a GUID string into a ``System.Guid``, raising ``ValueError`` on failure."""
    try:
        return System.Guid(str(guid_str))
    except Exception:
        raise ValueError("Invalid GUID string: '{g}'".format(g=guid_str))


def _coerce_brep(guid_str):
    # type: (str) -> RG.Brep
    """Validate GUID exists, then coerce to Brep.  Raises on failure."""
    registry.validate_guid(guid_str)
    sys_guid = _coerce_guid(guid_str)
    brep = rs.coercebrep(sys_guid)
    if brep is None:
        raise GolemError(
            ErrorCode.INVALID_PARAMS,
            "Object '{g}' is not a Brep.".format(g=guid_str),
        )
    return brep


def _coerce_curve(guid_str):
    # type: (str) -> RG.Curve
    """Validate GUID exists, then coerce to Curve.  Raises on failure."""
    registry.validate_guid(guid_str)
    sys_guid = _coerce_guid(guid_str)
    curve = rs.coercecurve(sys_guid)
    if curve is None:
        raise GolemError(
            ErrorCode.INVALID_PARAMS,
            "Object '{g}' is not a Curve.".format(g=guid_str),
        )
    return curve


def _coerce_surface(guid_str):
    # type: (str) -> RG.Surface
    """Validate GUID exists, then coerce to Surface.  Raises on failure."""
    registry.validate_guid(guid_str)
    sys_guid = _coerce_guid(guid_str)
    srf = rs.coercesurface(sys_guid)
    if srf is None:
        raise GolemError(
            ErrorCode.INVALID_PARAMS,
            "Object '{g}' is not a Surface.".format(g=guid_str),
        )
    return srf


def _add_brep_to_doc(brep):
    # type: (RG.Brep) -> str
    """Add *brep* to the Rhino document and return its GUID string."""
    new_guid = sc.doc.Objects.AddBrep(brep)
    if new_guid == System.Guid.Empty:
        raise GolemError(
            ErrorCode.OPERATION_FAILED,
            "Failed to add result Brep to the document.",
        )
    guid_str = str(new_guid)
    registry.register(guid_str, obj_type="brep")
    return guid_str


def _add_curve_to_doc(curve):
    # type: (RG.Curve) -> str
    """Add *curve* to the Rhino document and return its GUID string."""
    new_guid = sc.doc.Objects.AddCurve(curve)
    if new_guid == System.Guid.Empty:
        raise GolemError(
            ErrorCode.OPERATION_FAILED,
            "Failed to add result Curve to the document.",
        )
    guid_str = str(new_guid)
    registry.register(guid_str, obj_type="curve")
    return guid_str


def _add_mesh_to_doc(mesh):
    # type: (RG.Mesh) -> str
    """Add *mesh* to the Rhino document and return its GUID string."""
    new_guid = sc.doc.Objects.AddMesh(mesh)
    if new_guid == System.Guid.Empty:
        raise GolemError(
            ErrorCode.OPERATION_FAILED,
            "Failed to add result Mesh to the document.",
        )
    guid_str = str(new_guid)
    registry.register(guid_str, obj_type="mesh")
    return guid_str


def _add_point_to_doc(point3d):
    # type: (RG.Point3d) -> str
    """Add a point to the Rhino document and return its GUID string."""
    new_guid = sc.doc.Objects.AddPoint(point3d)
    if new_guid == System.Guid.Empty:
        raise GolemError(
            ErrorCode.OPERATION_FAILED,
            "Failed to add intersection point to the document.",
        )
    guid_str = str(new_guid)
    registry.register(guid_str, obj_type="point")
    return guid_str


def _delete_object(guid_str):
    # type: (str) -> None
    """Delete an object from the Rhino document and remove it from the registry."""
    sys_guid = _coerce_guid(guid_str)
    sc.doc.Objects.Delete(sys_guid, True)
    registry.unregister(guid_str)


def _list_param(params, key):
    # type: (Dict[str, Any], str) -> List
    """Return a list from *params[key]*, raising if absent or not iterable."""
    value = _require(params, key)
    if not isinstance(value, (list, tuple)):
        raise ValueError(
            "Parameter '{key}' must be a list (got {tp}).".format(
                key=key, tp=type(value).__name__
            )
        )
    return list(value)


def _optional_float(params, key, default):
    # type: (Dict[str, Any], str, float) -> float
    """Return float from params or default.  Raises ValueError on bad type."""
    if key not in params or params[key] is None:
        return default
    try:
        return float(params[key])
    except (TypeError, ValueError):
        raise ValueError(
            "Parameter '{key}' must be a number.".format(key=key)
        )


def _optional_bool(params, key, default):
    # type: (Dict[str, Any], str, bool) -> bool
    if key not in params or params[key] is None:
        return default
    return bool(params[key])


def _optional_int(params, key, default):
    # type: (Dict[str, Any], str, int) -> int
    if key not in params or params[key] is None:
        return default
    try:
        return int(params[key])
    except (TypeError, ValueError):
        raise ValueError(
            "Parameter '{key}' must be an integer.".format(key=key)
        )


# ---------------------------------------------------------------------------
# Boolean operations
# ---------------------------------------------------------------------------

@wrap_handler
@handler("operations.boolean_union")
def boolean_union(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Boolean union of two or more closed Breps.

    Parameters
    ----------
    guids : list[str]
        Two or more object GUIDs.  All must be closed (solid) Breps.

    Returns
    -------
    dict
        ``{"guids": [...], "count": int, "objects": [...]}``
    """
    guid_list = _list_param(params, "guids")
    if len(guid_list) < 2:
        raise ValueError("boolean_union requires at least 2 GUIDs.")

    breps = [_coerce_brep(g) for g in guid_list]

    tol = sc.doc.ModelAbsoluteTolerance
    results = RG.Brep.CreateBooleanUnion(breps, tol)

    if results is None or len(results) == 0:
        raise GolemError(
            ErrorCode.OPERATION_FAILED,
            "Boolean union failed -- check that all objects are valid, closed Breps "
            "and that they actually intersect.",
        )

    # Delete originals.
    for g in guid_list:
        _delete_object(g)

    result_guids = [_add_brep_to_doc(b) for b in results]
    sc.doc.Views.Redraw()

    return {
        "guids": result_guids,
        "count": len(result_guids),
        "objects": [serialize_brep(b) for b in results],
    }


@wrap_handler
@handler("operations.boolean_difference")
def boolean_difference(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Boolean difference: subtract cutter Breps from target Breps.

    Parameters
    ----------
    guid_a : str
        GUID of the Brep to cut from (primary solid).
    guids_b : list[str]
        GUIDs of the Breps to cut with (tool solids).

    Returns
    -------
    dict
        ``{"guids": [...], "count": int, "objects": [...]}``
    """
    guid_a = _require(params, "guid_a", str)
    guids_b = _list_param(params, "guids_b")
    if len(guids_b) == 0:
        raise ValueError("guids_b must contain at least one GUID.")

    brep_a = [_coerce_brep(guid_a)]
    breps_b = [_coerce_brep(g) for g in guids_b]

    tol = sc.doc.ModelAbsoluteTolerance
    results = RG.Brep.CreateBooleanDifference(brep_a, breps_b, tol)

    if results is None or len(results) == 0:
        raise GolemError(
            ErrorCode.OPERATION_FAILED,
            "Boolean difference failed -- ensure the cutter actually intersects "
            "the target and both are valid closed Breps.",
        )

    _delete_object(guid_a)
    for g in guids_b:
        _delete_object(g)

    result_guids = [_add_brep_to_doc(b) for b in results]
    sc.doc.Views.Redraw()

    return {
        "guids": result_guids,
        "count": len(result_guids),
        "objects": [serialize_brep(b) for b in results],
    }


@wrap_handler
@handler("operations.boolean_intersection")
def boolean_intersection(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Boolean intersection: volume common to two sets of Breps.

    Parameters
    ----------
    guids_a : list[str]
        First set of closed Brep GUIDs.
    guids_b : list[str]
        Second set of closed Brep GUIDs.

    Returns
    -------
    dict
        ``{"guids": [...], "count": int, "objects": [...]}``
    """
    guids_a = _list_param(params, "guids_a")
    guids_b = _list_param(params, "guids_b")
    if len(guids_a) == 0 or len(guids_b) == 0:
        raise ValueError("guids_a and guids_b must each contain at least one GUID.")

    breps_a = [_coerce_brep(g) for g in guids_a]
    breps_b = [_coerce_brep(g) for g in guids_b]

    tol = sc.doc.ModelAbsoluteTolerance
    results = RG.Brep.CreateBooleanIntersection(breps_a, breps_b, tol)

    if results is None or len(results) == 0:
        raise GolemError(
            ErrorCode.OPERATION_FAILED,
            "Boolean intersection failed -- the Breps may not intersect or may be "
            "geometrically invalid.",
        )

    for g in guids_a:
        _delete_object(g)
    for g in guids_b:
        _delete_object(g)

    result_guids = [_add_brep_to_doc(b) for b in results]
    sc.doc.Views.Redraw()

    return {
        "guids": result_guids,
        "count": len(result_guids),
        "objects": [serialize_brep(b) for b in results],
    }


@wrap_handler
@handler("operations.boolean_split")
def boolean_split(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Boolean split: divide a Brep with a cutter Brep, keeping all pieces.

    Parameters
    ----------
    guid_to_split : str
        GUID of the Brep to split.
    guid_cutter : str
        GUID of the Brep used as the cutting tool.

    Returns
    -------
    dict
        ``{"guids": [...], "count": int, "objects": [...]}``
    """
    guid_to_split = _require(params, "guid_to_split", str)
    guid_cutter = _require(params, "guid_cutter", str)

    brep_to_split = [_coerce_brep(guid_to_split)]
    brep_cutter = [_coerce_brep(guid_cutter)]

    tol = sc.doc.ModelAbsoluteTolerance
    results = RG.Brep.CreateBooleanSplit(brep_to_split, brep_cutter, tol)

    if results is None or len(results) == 0:
        raise GolemError(
            ErrorCode.OPERATION_FAILED,
            "Boolean split failed -- ensure the cutter intersects the target Brep.",
        )

    _delete_object(guid_to_split)
    _delete_object(guid_cutter)

    result_guids = [_add_brep_to_doc(b) for b in results]
    sc.doc.Views.Redraw()

    return {
        "guids": result_guids,
        "count": len(result_guids),
        "objects": [serialize_brep(b) for b in results],
    }


# ---------------------------------------------------------------------------
# Trim / Split
# ---------------------------------------------------------------------------

@wrap_handler
@handler("operations.trim")
def trim(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Trim a Brep using a cutter Brep, keeping the side containing pick_point.

    Parameters
    ----------
    object_id : str
        GUID of the Brep to trim.
    cutter_id : str
        GUID of the cutting Brep or surface.
    pick_point : list[float]
        [x, y, z] point indicating which side to keep.

    Returns
    -------
    dict
        ``{"guids": [...], "count": int}``
    """
    object_id = _require(params, "object_id", str)
    cutter_id = _require(params, "cutter_id", str)
    pick_raw = _require(params, "pick_point")

    if not isinstance(pick_raw, (list, tuple)) or len(pick_raw) < 3:
        raise ValueError("pick_point must be a list of three numbers [x, y, z].")

    pick_pt = RG.Point3d(
        float(pick_raw[0]),
        float(pick_raw[1]),
        float(pick_raw[2]),
    )

    brep = _coerce_brep(object_id)
    cutter = _coerce_brep(cutter_id)

    tol = sc.doc.ModelAbsoluteTolerance
    results = brep.Trim(cutter, tol)

    if results is None or len(results) == 0:
        raise GolemError(
            ErrorCode.OPERATION_FAILED,
            "Trim failed -- the cutter may not intersect the target.",
        )

    # Keep only the piece(s) closest to the pick point.
    def _dist_to_pick(b):
        # type: (RG.Brep) -> float
        try:
            cp = b.ClosestPoint(pick_pt)
            return float(pick_pt.DistanceTo(cp))
        except Exception:
            return float("inf")

    closest = min(results, key=_dist_to_pick)

    _delete_object(object_id)

    result_guid = _add_brep_to_doc(closest)
    sc.doc.Views.Redraw()

    return {
        "guids": [result_guid],
        "count": 1,
        "object": serialize_brep(closest),
    }


@wrap_handler
@handler("operations.split")
def split(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Split a Brep with one or more cutter Breps, returning all resulting pieces.

    Parameters
    ----------
    object_id : str
        GUID of the Brep to split.
    cutter_ids : list[str]
        GUIDs of the cutting Breps.

    Returns
    -------
    dict
        ``{"guids": [...], "count": int, "objects": [...]}``
    """
    object_id = _require(params, "object_id", str)
    cutter_ids = _list_param(params, "cutter_ids")
    if len(cutter_ids) == 0:
        raise ValueError("cutter_ids must contain at least one GUID.")

    registry.validate_guid(object_id)
    registry.validate_guids(cutter_ids)

    # rs.SplitBrep returns a list of new GUIDs.
    sys_object_guid = _coerce_guid(object_id)
    sys_cutter_guids = [_coerce_guid(c) for c in cutter_ids]

    result_rhino_guids = rs.SplitBrep(sys_object_guid, sys_cutter_guids, delete_input=True)

    if result_rhino_guids is None or len(result_rhino_guids) == 0:
        raise GolemError(
            ErrorCode.OPERATION_FAILED,
            "Split failed -- the cutters may not intersect the target Brep.",
        )

    registry.unregister(object_id)

    result_guids = []
    result_objects = []
    for rg in result_rhino_guids:
        gs = str(rg)
        registry.register(gs, obj_type="brep")
        result_guids.append(gs)
        b = rs.coercebrep(rg)
        if b is not None:
            result_objects.append(serialize_brep(b))

    sc.doc.Views.Redraw()

    return {
        "guids": result_guids,
        "count": len(result_guids),
        "objects": result_objects,
    }


# ---------------------------------------------------------------------------
# Offset
# ---------------------------------------------------------------------------

@wrap_handler
@handler("operations.offset_curve")
def offset_curve(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Offset a curve by a given distance.

    Parameters
    ----------
    curve_id : str
        GUID of the curve to offset.
    distance : float
        Offset distance.  Positive is to the left of the curve direction.
    direction_point : list[float], optional
        [x, y, z] point that determines the offset side and implicitly the
        offset plane.  Defaults to the world XY plane normal (Z up).
    plane : dict, optional
        Offset plane as ``{"origin": [x,y,z], "x_axis": [x,y,z],
        "y_axis": [x,y,z]}``.  Takes precedence over direction_point when
        provided.

    Returns
    -------
    dict
        ``{"guid": str, "curve": {...}}``
    """
    curve_id = _require(params, "curve_id", str)
    distance = float(_require(params, "distance"))

    registry.validate_guid(curve_id)
    sys_guid = _coerce_guid(curve_id)

    # Build the offset plane normal.
    plane_raw = params.get("plane")
    dir_raw = params.get("direction_point")

    if plane_raw is not None:
        try:
            origin = RG.Point3d(
                float(plane_raw["origin"][0]),
                float(plane_raw["origin"][1]),
                float(plane_raw["origin"][2]),
            )
            x_axis = RG.Vector3d(
                float(plane_raw["x_axis"][0]),
                float(plane_raw["x_axis"][1]),
                float(plane_raw["x_axis"][2]),
            )
            y_axis = RG.Vector3d(
                float(plane_raw["y_axis"][0]),
                float(plane_raw["y_axis"][1]),
                float(plane_raw["y_axis"][2]),
            )
            offset_plane = RG.Plane(origin, x_axis, y_axis)
        except Exception as exc:
            raise ValueError(
                "Invalid 'plane' parameter: {e}".format(e=exc)
            )
    elif dir_raw is not None:
        if not isinstance(dir_raw, (list, tuple)) or len(dir_raw) < 3:
            raise ValueError("direction_point must be [x, y, z].")
        normal = RG.Vector3d(float(dir_raw[0]), float(dir_raw[1]), float(dir_raw[2]))
        normal.Unitize()
        # Build an arbitrary plane perpendicular to the normal.
        perp = RG.Vector3d.CrossProduct(normal, RG.Vector3d.ZAxis)
        if perp.Length < 1e-10:
            perp = RG.Vector3d.CrossProduct(normal, RG.Vector3d.XAxis)
        perp.Unitize()
        offset_plane = RG.Plane(RG.Point3d.Origin, perp, RG.Vector3d.CrossProduct(normal, perp))
    else:
        # Default: world XY plane.
        offset_plane = RG.Plane.WorldXY

    result_guids = rs.OffsetCurve(sys_guid, offset_plane.Origin, distance,
                                  offset_plane.Normal)

    if result_guids is None or len(result_guids) == 0:
        raise GolemError(
            ErrorCode.OPERATION_FAILED,
            "Offset curve failed -- check that the curve and plane are valid.",
        )

    first_guid = str(result_guids[0])
    registry.register(first_guid, obj_type="curve")

    out_curve = rs.coercecurve(result_guids[0])
    sc.doc.Views.Redraw()

    return {
        "guid": first_guid,
        "curve": serialize_curve(out_curve) if out_curve is not None else None,
    }


@wrap_handler
@handler("operations.offset_surface")
def offset_surface(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Offset a surface (or Brep face) by a given distance.

    Parameters
    ----------
    surface_id : str
        GUID of the surface or Brep to offset.
    distance : float
        Offset distance.  Positive is in the direction of the surface normal.
    both_sides : bool, optional
        If True, offset in both normal directions (default False).

    Returns
    -------
    dict
        ``{"guid": str, "surface": {...}}``
    """
    surface_id = _require(params, "surface_id", str)
    distance = float(_require(params, "distance"))
    both_sides = _optional_bool(params, "both_sides", False)

    registry.validate_guid(surface_id)
    sys_guid = _coerce_guid(surface_id)

    result_guid = rs.OffsetSurface(sys_guid, distance, None, both_sides, False)

    if result_guid is None:
        raise GolemError(
            ErrorCode.OPERATION_FAILED,
            "Offset surface failed -- the surface may be degenerate or the distance "
            "may cause self-intersection.",
        )

    gs = str(result_guid)
    registry.register(gs, obj_type="surface")

    # Try to serialise as brep first, then surface.
    out_srf = rs.coercesurface(result_guid)
    serialized = serialize_surface(out_srf) if out_srf is not None else None

    sc.doc.Views.Redraw()

    return {
        "guid": gs,
        "surface": serialized,
    }


# ---------------------------------------------------------------------------
# Fillet / Chamfer
# ---------------------------------------------------------------------------

@wrap_handler
@handler("operations.fillet_edge")
def fillet_edge(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Fillet specified edges of a Brep by *radius*.

    Parameters
    ----------
    brep_id : str
        GUID of the Brep whose edges to fillet.
    edge_indices : list[int]
        Indices of the edges to fillet (0-based, from ``Brep.Edges``).
    radius : float
        Fillet radius.

    Returns
    -------
    dict
        ``{"guids": [...], "count": int, "objects": [...]}``
    """
    brep_id = _require(params, "brep_id", str)
    edge_indices = _list_param(params, "edge_indices")
    radius = float(_require(params, "radius"))

    if radius <= 0.0:
        raise ValueError("radius must be greater than zero.")
    if len(edge_indices) == 0:
        raise ValueError("edge_indices must contain at least one index.")

    brep = _coerce_brep(brep_id)
    edge_idx = [int(i) for i in edge_indices]

    # Validate edge indices.
    edge_count = brep.Edges.Count
    for i in edge_idx:
        if i < 0 or i >= edge_count:
            raise ValueError(
                "Edge index {i} is out of range (Brep has {n} edges).".format(
                    i=i, n=edge_count
                )
            )

    # CreateFilletEdges expects parallel arrays: indices, start/end radii, blend type.
    start_radii = [radius] * len(edge_idx)
    end_radii = [radius] * len(edge_idx)
    blend_type = RG.BlendType.Fillet
    rail_type = RG.RailType.RollingBall
    tol = sc.doc.ModelAbsoluteTolerance

    results = RG.Brep.CreateFilletEdges(
        brep,
        edge_idx,
        start_radii,
        end_radii,
        blend_type,
        rail_type,
        tol,
    )

    if results is None or len(results) == 0:
        raise GolemError(
            ErrorCode.OPERATION_FAILED,
            "Fillet edge failed -- the radius may be too large for the selected edges, "
            "or the Brep geometry may be invalid.",
        )

    _delete_object(brep_id)

    result_guids = [_add_brep_to_doc(b) for b in results]
    sc.doc.Views.Redraw()

    return {
        "guids": result_guids,
        "count": len(result_guids),
        "objects": [serialize_brep(b) for b in results],
    }


@wrap_handler
@handler("operations.fillet_curves")
def fillet_curves(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Create a fillet arc between two coplanar curves.

    Parameters
    ----------
    curve_id_a : str
        GUID of the first curve.
    curve_id_b : str
        GUID of the second curve.
    radius : float
        Fillet arc radius.
    join : bool, optional
        If True, attempt to join the trimmed curves and the fillet arc into a
        single polycurve (default False).

    Returns
    -------
    dict
        ``{"guid": str, "curve": {...}}`` or
        ``{"guids": [fillet, curve_a_trimmed, curve_b_trimmed], ...}`` depending
        on whether *join* is True.
    """
    curve_id_a = _require(params, "curve_id_a", str)
    curve_id_b = _require(params, "curve_id_b", str)
    radius = float(_require(params, "radius"))
    join = _optional_bool(params, "join", False)

    if radius <= 0.0:
        raise ValueError("radius must be greater than zero.")

    registry.validate_guid(curve_id_a)
    registry.validate_guid(curve_id_b)

    sys_a = _coerce_guid(curve_id_a)
    sys_b = _coerce_guid(curve_id_b)

    # rs.AddFilletCurve returns the fillet arc guid.
    fillet_guid = rs.AddFilletCurve(sys_a, sys_b, radius)

    if fillet_guid is None:
        raise GolemError(
            ErrorCode.OPERATION_FAILED,
            "Fillet curves failed -- the curves may be non-coplanar, parallel, or the "
            "radius may be too large.",
        )

    fillet_str = str(fillet_guid)
    registry.register(fillet_str, obj_type="curve")

    fillet_curve = rs.coercecurve(fillet_guid)

    if join:
        # Attempt to join trimmed curves + fillet into one polycurve.
        joined = rs.JoinCurves(
            [sys_a, fillet_guid, sys_b], delete_input=True
        )
        if joined:
            joined_strs = [str(g) for g in joined]
            for gs in joined_strs:
                registry.register(gs, obj_type="curve")
            registry.unregister(curve_id_a)
            registry.unregister(curve_id_b)
            sc.doc.Views.Redraw()
            return {
                "guid": joined_strs[0],
                "guids": joined_strs,
                "count": len(joined_strs),
            }

    sc.doc.Views.Redraw()

    return {
        "guid": fillet_str,
        "curve": serialize_curve(fillet_curve) if fillet_curve is not None else None,
    }


@wrap_handler
@handler("operations.chamfer_curves")
def chamfer_curves(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Create a chamfer line between two curves.

    Parameters
    ----------
    curve_id_a : str
        GUID of the first curve.
    curve_id_b : str
        GUID of the second curve.
    distance_a : float
        Chamfer distance measured along the first curve from the intersection.
    distance_b : float
        Chamfer distance measured along the second curve from the intersection.

    Returns
    -------
    dict
        ``{"guid": str, "curve": {...}}``
    """
    curve_id_a = _require(params, "curve_id_a", str)
    curve_id_b = _require(params, "curve_id_b", str)
    distance_a = float(_require(params, "distance_a"))
    distance_b = float(_require(params, "distance_b"))

    if distance_a <= 0.0 or distance_b <= 0.0:
        raise ValueError("distance_a and distance_b must both be greater than zero.")

    registry.validate_guid(curve_id_a)
    registry.validate_guid(curve_id_b)

    sys_a = _coerce_guid(curve_id_a)
    sys_b = _coerce_guid(curve_id_b)

    chamfer_guid = rs.AddChamferCurve(sys_a, sys_b, distance_a, distance_b)

    if chamfer_guid is None:
        raise GolemError(
            ErrorCode.OPERATION_FAILED,
            "Chamfer curves failed -- the curves may not intersect or the distances "
            "may be too large.",
        )

    gs = str(chamfer_guid)
    registry.register(gs, obj_type="curve")

    chamfer_curve = rs.coercecurve(chamfer_guid)
    sc.doc.Views.Redraw()

    return {
        "guid": gs,
        "curve": serialize_curve(chamfer_curve) if chamfer_curve is not None else None,
    }


@wrap_handler
@handler("operations.chamfer_edge")
def chamfer_edge(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Chamfer specified edges of a Brep.

    Uses ``Rhino.Geometry.Brep.CreateFilletEdges`` with ``BlendType.Chamfer``
    when available (Rhino 7+).  Falls back to a Rhino command string on older
    builds.

    Parameters
    ----------
    brep_id : str
        GUID of the Brep whose edges to chamfer.
    edge_indices : list[int]
        Indices of the edges to chamfer (0-based).
    distance : float
        Chamfer distance (symmetric on both sides of the edge).

    Returns
    -------
    dict
        ``{"guids": [...], "count": int, "objects": [...]}``
    """
    brep_id = _require(params, "brep_id", str)
    edge_indices = _list_param(params, "edge_indices")
    distance = float(_require(params, "distance"))

    if distance <= 0.0:
        raise ValueError("distance must be greater than zero.")
    if len(edge_indices) == 0:
        raise ValueError("edge_indices must contain at least one index.")

    brep = _coerce_brep(brep_id)
    edge_idx = [int(i) for i in edge_indices]

    edge_count = brep.Edges.Count
    for i in edge_idx:
        if i < 0 or i >= edge_count:
            raise ValueError(
                "Edge index {i} is out of range (Brep has {n} edges).".format(
                    i=i, n=edge_count
                )
            )

    start_distances = [distance] * len(edge_idx)
    end_distances = [distance] * len(edge_idx)
    tol = sc.doc.ModelAbsoluteTolerance

    results = None

    # BlendType.Chamfer is available in RhinoCommon >= 7.
    try:
        blend_type = RG.BlendType.Chamfer
        rail_type = RG.RailType.RollingBall
        results = RG.Brep.CreateFilletEdges(
            brep,
            edge_idx,
            start_distances,
            end_distances,
            blend_type,
            rail_type,
            tol,
        )
    except AttributeError:
        # BlendType.Chamfer not available -- fall back to a Rhino command.
        rs.SelectObject(_coerce_guid(brep_id))
        edge_list = " ".join(str(i) for i in edge_idx)
        Rhino.RhinoApp.RunScript(
            "_ChamferEdge Distance={d} {edges} _Enter _Enter".format(
                d=distance, edges=edge_list
            ),
            False,
        )
        # After the command the original is replaced; try to find the new object.
        results = None

    if results is None or len(results) == 0:
        raise GolemError(
            ErrorCode.OPERATION_FAILED,
            "Chamfer edge failed -- the distance may be too large for the selected "
            "edges or the Brep geometry may be invalid.",
        )

    _delete_object(brep_id)

    result_guids = [_add_brep_to_doc(b) for b in results]
    sc.doc.Views.Redraw()

    return {
        "guids": result_guids,
        "count": len(result_guids),
        "objects": [serialize_brep(b) for b in results],
    }


# ---------------------------------------------------------------------------
# Intersection
# ---------------------------------------------------------------------------

@wrap_handler
@handler("operations.intersect")
def intersect(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Compute the intersection of two objects.

    Auto-detects the geometry types and chooses the appropriate RhinoCommon
    intersection routine:

    * curve + curve  -> ``Intersect.CurveCurve``     -> intersection points
    * curve + brep   -> ``Intersect.CurveBrep``      -> intersection points + overlap curves
    * brep  + brep   -> ``Intersect.BrepBrep``        -> intersection curves

    Parameters
    ----------
    id_a : str
        GUID of the first object.
    id_b : str
        GUID of the second object.

    Returns
    -------
    dict
        ``{"type": str, "point_guids": [...], "curve_guids": [...],
           "points": [...], "curves": [...]}``
    """
    id_a = _require(params, "id_a", str)
    id_b = _require(params, "id_b", str)

    registry.validate_guid(id_a)
    registry.validate_guid(id_b)

    sys_a = _coerce_guid(id_a)
    sys_b = _coerce_guid(id_b)

    tol = sc.doc.ModelAbsoluteTolerance
    angle_tol = sc.doc.ModelAngleToleranceRadians

    # Determine geometry types.
    geom_a = sc.doc.Objects.FindId(sys_a)
    geom_b = sc.doc.Objects.FindId(sys_b)

    if geom_a is None or geom_b is None:
        raise GolemError(
            ErrorCode.OBJECT_NOT_FOUND,
            "One or both objects could not be retrieved from the document.",
        )

    type_a = type(geom_a.Geometry).__name__
    type_b = type(geom_b.Geometry).__name__

    def _is_curve(type_name):
        # type: (str) -> bool
        return "Curve" in type_name

    def _is_brep(type_name):
        # type: (str) -> bool
        return "Brep" in type_name or "Extrusion" in type_name or "Surface" in type_name

    point_guids = []   # type: List[str]
    curve_guids = []   # type: List[str]
    point_data = []    # type: List[Any]
    curve_data = []    # type: List[Any]
    intersection_type = "unknown"

    if _is_curve(type_a) and _is_curve(type_b):
        # Curve-Curve intersection.
        intersection_type = "curve_curve"
        curve_a = rs.coercecurve(sys_a)
        curve_b = rs.coercecurve(sys_b)
        if curve_a is None or curve_b is None:
            raise GolemError(
                ErrorCode.INVALID_PARAMS,
                "Failed to coerce one or both objects to Curve.",
            )
        events = RGI.Intersection.CurveCurve(curve_a, curve_b, tol, tol)
        if events is not None:
            for ev in events:
                try:
                    pt = ev.PointA
                    gs = _add_point_to_doc(pt)
                    point_guids.append(gs)
                    point_data.append(serialize_point3d(pt))
                except Exception:
                    pass

    elif _is_curve(type_a) and _is_brep(type_b):
        # Curve-Surface/Brep intersection.
        intersection_type = "curve_brep"
        curve_a = rs.coercecurve(sys_a)
        brep_b = rs.coercebrep(sys_b)
        if curve_a is None or brep_b is None:
            raise GolemError(
                ErrorCode.INVALID_PARAMS,
                "Failed to coerce objects to Curve and Brep.",
            )
        ok, pt_params, overlap_curves = RGI.Intersection.CurveBrep(
            curve_a, brep_b, tol
        )
        if ok:
            for t in (pt_params or []):
                try:
                    pt = curve_a.PointAt(t)
                    gs = _add_point_to_doc(pt)
                    point_guids.append(gs)
                    point_data.append(serialize_point3d(pt))
                except Exception:
                    pass
            for oc in (overlap_curves or []):
                try:
                    gs = _add_curve_to_doc(oc)
                    curve_guids.append(gs)
                    curve_data.append(serialize_curve(oc))
                except Exception:
                    pass

    elif _is_brep(type_a) and _is_curve(type_b):
        # Flip and recurse via the same logic.
        intersection_type = "curve_brep"
        curve_b = rs.coercecurve(sys_b)
        brep_a = rs.coercebrep(sys_a)
        if curve_b is None or brep_a is None:
            raise GolemError(
                ErrorCode.INVALID_PARAMS,
                "Failed to coerce objects to Brep and Curve.",
            )
        ok, pt_params, overlap_curves = RGI.Intersection.CurveBrep(
            curve_b, brep_a, tol
        )
        if ok:
            for t in (pt_params or []):
                try:
                    pt = curve_b.PointAt(t)
                    gs = _add_point_to_doc(pt)
                    point_guids.append(gs)
                    point_data.append(serialize_point3d(pt))
                except Exception:
                    pass
            for oc in (overlap_curves or []):
                try:
                    gs = _add_curve_to_doc(oc)
                    curve_guids.append(gs)
                    curve_data.append(serialize_curve(oc))
                except Exception:
                    pass

    else:
        # Surface-Surface / Brep-Brep intersection.
        intersection_type = "brep_brep"
        brep_a = rs.coercebrep(sys_a)
        brep_b = rs.coercebrep(sys_b)
        if brep_a is None or brep_b is None:
            raise GolemError(
                ErrorCode.INVALID_PARAMS,
                "Failed to coerce both objects to Breps.",
            )
        ok, int_curves, pt_clouds = RGI.Intersection.BrepBrep(
            brep_a, brep_b, tol
        )
        if ok:
            for ic in (int_curves or []):
                try:
                    gs = _add_curve_to_doc(ic)
                    curve_guids.append(gs)
                    curve_data.append(serialize_curve(ic))
                except Exception:
                    pass

    if not point_guids and not curve_guids:
        # No intersection found -- return an informative result, not an error.
        sc.doc.Views.Redraw()
        return {
            "type": intersection_type,
            "intersects": False,
            "point_guids": [],
            "curve_guids": [],
            "points": [],
            "curves": [],
        }

    sc.doc.Views.Redraw()

    return {
        "type": intersection_type,
        "intersects": True,
        "point_guids": point_guids,
        "curve_guids": curve_guids,
        "points": point_data,
        "curves": curve_data,
    }


# ---------------------------------------------------------------------------
# Meshing
# ---------------------------------------------------------------------------

_MESH_QUALITY_PRESETS = {
    "coarse": {
        "max_edge_length": 0.0,
        "min_edge_length": 0.0001,
        "max_angle": 35.0,
        "grid_ratio": 0.0,
        "grid_min_count": 1,
        "min_initial_grid_quads": 0,
        "refine": True,
        "jagged_seams": False,
        "simple_planes": True,
    },
    "medium": {
        "max_edge_length": 0.0,
        "min_edge_length": 0.0001,
        "max_angle": 20.0,
        "grid_ratio": 0.0,
        "grid_min_count": 1,
        "min_initial_grid_quads": 0,
        "refine": True,
        "jagged_seams": False,
        "simple_planes": False,
    },
    "fine": {
        "max_edge_length": 0.0,
        "min_edge_length": 0.0001,
        "max_angle": 10.0,
        "grid_ratio": 0.0,
        "grid_min_count": 2,
        "min_initial_grid_quads": 16,
        "refine": True,
        "jagged_seams": False,
        "simple_planes": False,
    },
}


@wrap_handler
@handler("operations.mesh_from_brep")
def mesh_from_brep(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Generate a render mesh from a Brep.

    Parameters
    ----------
    brep_id : str
        GUID of the Brep to mesh.
    quality : str, optional
        Preset quality level: ``"coarse"``, ``"medium"`` (default), ``"fine"``,
        or ``"custom"``.
    max_edge_length : float, optional
        Maximum mesh edge length (0 = no limit).  Used when quality is
        ``"custom"`` or to override a preset.
    min_edge_length : float, optional
        Minimum mesh edge length.
    max_angle : float, optional
        Maximum allowed angle in degrees between adjacent mesh face normals.

    Returns
    -------
    dict
        ``{"guids": [...], "count": int, "meshes": [...]}``
    """
    brep_id = _require(params, "brep_id", str)
    quality = params.get("quality", "medium")

    if quality not in ("coarse", "medium", "fine", "custom"):
        raise ValueError(
            "quality must be one of 'coarse', 'medium', 'fine', or 'custom' "
            "(got '{q}').".format(q=quality)
        )

    brep = _coerce_brep(brep_id)

    # Build MeshingParameters.
    mp = RG.MeshingParameters()

    if quality != "custom":
        preset = _MESH_QUALITY_PRESETS[quality]
        mp.MaximumEdgeLength = preset["max_edge_length"]
        mp.MinimumEdgeLength = preset["min_edge_length"]
        mp.MaximumAngle = preset["max_angle"]
        mp.GridAspectRatio = preset["grid_ratio"]
        mp.GridMinCount = preset["grid_min_count"]
        mp.MinimumGridQuads = preset["min_initial_grid_quads"]
        mp.Refine = preset["refine"]
        mp.JaggedSeams = preset["jagged_seams"]
        mp.SimplePlanes = preset["simple_planes"]

    # Allow caller overrides regardless of quality preset.
    max_edge = _optional_float(params, "max_edge_length", -1.0)
    if max_edge >= 0.0:
        mp.MaximumEdgeLength = max_edge

    min_edge = _optional_float(params, "min_edge_length", -1.0)
    if min_edge >= 0.0:
        mp.MinimumEdgeLength = min_edge

    max_ang = _optional_float(params, "max_angle", -1.0)
    if max_ang >= 0.0:
        mp.MaximumAngle = max_ang

    meshes = RG.Mesh.CreateFromBrep(brep, mp)

    if meshes is None or len(meshes) == 0:
        raise GolemError(
            ErrorCode.OPERATION_FAILED,
            "Mesh from Brep failed -- the Brep may be invalid or non-manifold.",
        )

    result_guids = [_add_mesh_to_doc(m) for m in meshes]
    sc.doc.Views.Redraw()

    return {
        "guids": result_guids,
        "count": len(result_guids),
        "meshes": [serialize_mesh(m) for m in meshes],
    }


# ---------------------------------------------------------------------------
# Curve operations
# ---------------------------------------------------------------------------

@wrap_handler
@handler("operations.project_curve")
def project_curve(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Project a curve onto one or more Breps along a direction vector.

    Parameters
    ----------
    curve_id : str
        GUID of the curve to project.
    brep_ids : list[str]
        GUIDs of the target Brep(s).
    direction : list[float]
        [x, y, z] projection direction vector.

    Returns
    -------
    dict
        ``{"guids": [...], "count": int, "curves": [...]}``
    """
    curve_id = _require(params, "curve_id", str)
    brep_ids = _list_param(params, "brep_ids")
    dir_raw = _require(params, "direction")

    if not isinstance(dir_raw, (list, tuple)) or len(dir_raw) < 3:
        raise ValueError("direction must be a list of three numbers [x, y, z].")

    direction = RG.Vector3d(float(dir_raw[0]), float(dir_raw[1]), float(dir_raw[2]))
    if direction.Length < 1e-12:
        raise ValueError("direction vector must be non-zero.")
    direction.Unitize()

    curve = _coerce_curve(curve_id)
    breps = [_coerce_brep(g) for g in brep_ids]

    tol = sc.doc.ModelAbsoluteTolerance
    projected = RG.Curve.ProjectToBrep(curve, breps, direction, tol)

    if projected is None or len(projected) == 0:
        raise GolemError(
            ErrorCode.OPERATION_FAILED,
            "Project curve failed -- the curve projection may miss all target Breps "
            "in the given direction.",
        )

    result_guids = [_add_curve_to_doc(c) for c in projected]
    sc.doc.Views.Redraw()

    return {
        "guids": result_guids,
        "count": len(result_guids),
        "curves": [serialize_curve(c) for c in projected],
    }


@wrap_handler
@handler("operations.extend_curve")
def extend_curve(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Extend a curve by a length or to a boundary object.

    Parameters
    ----------
    curve_id : str
        GUID of the curve to extend.
    extension_type : str
        ``"line"``, ``"arc"``, or ``"smooth"`` (default ``"smooth"``).
    side : str
        Which end to extend: ``"start"``, ``"end"``, or ``"both"``
        (default ``"end"``).
    length : float, optional
        Extension length.  Used when *boundary_id* is not given.
    boundary_id : str, optional
        GUID of a bounding object (curve or Brep) to extend to.  Takes
        precedence over *length*.

    Returns
    -------
    dict
        ``{"guid": str, "curve": {...}}``
    """
    curve_id = _require(params, "curve_id", str)
    extension_type_str = params.get("extension_type", "smooth")
    side_str = params.get("side", "end")
    length = _optional_float(params, "length", 0.0)
    boundary_id = params.get("boundary_id")

    # Map extension type string.
    _ext_type_map = {
        "line": RG.CurveExtensionStyle.Line,
        "arc": RG.CurveExtensionStyle.Arc,
        "smooth": RG.CurveExtensionStyle.Smooth,
    }
    if extension_type_str not in _ext_type_map:
        raise ValueError(
            "extension_type must be 'line', 'arc', or 'smooth' "
            "(got '{t}').".format(t=extension_type_str)
        )
    ext_style = _ext_type_map[extension_type_str]

    # Map side string.
    _side_map = {
        "start": RG.CurveEnd.Start,
        "end": RG.CurveEnd.End,
        "both": RG.CurveEnd.Both,
    }
    if side_str not in _side_map:
        raise ValueError(
            "side must be 'start', 'end', or 'both' (got '{s}').".format(s=side_str)
        )
    curve_end = _side_map[side_str]

    curve = _coerce_curve(curve_id)
    result_curve = None  # type: Optional[RG.Curve]

    if boundary_id is not None:
        # Extend to a boundary geometry object.
        registry.validate_guid(boundary_id)
        sys_boundary = _coerce_guid(boundary_id)
        boundary_obj = sc.doc.Objects.FindId(sys_boundary)
        if boundary_obj is None:
            raise GolemError(
                ErrorCode.OBJECT_NOT_FOUND,
                "Boundary object not found: '{g}'".format(g=boundary_id),
            )
        boundary_geom = boundary_obj.Geometry
        # Build a list of GeometryBase for the boundary.
        boundaries = [boundary_geom]  # type: List[RG.GeometryBase]
        result_curve = curve.Extend(curve_end, ext_style, boundaries)
    else:
        if length <= 0.0:
            raise ValueError(
                "length must be > 0 when no boundary_id is provided."
            )
        result_curve = curve.Extend(curve_end, length, ext_style)

    if result_curve is None:
        raise GolemError(
            ErrorCode.OPERATION_FAILED,
            "Extend curve failed -- check the extension type, side, and boundary.",
        )

    # Replace the original curve in the document.
    sys_orig = _coerce_guid(curve_id)
    sc.doc.Objects.Replace(sys_orig, result_curve)
    sc.doc.Views.Redraw()

    return {
        "guid": curve_id,
        "curve": serialize_curve(result_curve),
    }


@wrap_handler
@handler("operations.blend_curves")
def blend_curves(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Create a blend curve connecting the endpoints of two curves.

    Parameters
    ----------
    curve_id_a : str
        GUID of the first curve.
    curve_id_b : str
        GUID of the second curve.
    continuity : str
        Geometric continuity at both ends:
        ``"position"``, ``"tangent"``, or ``"curvature"``
        (default ``"tangent"``).

    Returns
    -------
    dict
        ``{"guid": str, "curve": {...}}``
    """
    curve_id_a = _require(params, "curve_id_a", str)
    curve_id_b = _require(params, "curve_id_b", str)
    continuity_str = params.get("continuity", "tangent")

    _cont_map = {
        "position":  RG.BlendContinuity.Position,
        "tangent":   RG.BlendContinuity.Tangency,
        "curvature": RG.BlendContinuity.Curvature,
    }
    if continuity_str not in _cont_map:
        raise ValueError(
            "continuity must be 'position', 'tangent', or 'curvature' "
            "(got '{c}').".format(c=continuity_str)
        )
    continuity = _cont_map[continuity_str]

    curve_a = _coerce_curve(curve_id_a)
    curve_b = _coerce_curve(curve_id_b)

    # Blend from the end of curve_a to the start of curve_b.
    blend = RG.Curve.CreateBlendCurve(
        curve_a, RG.CurveEnd.End,
        curve_b, RG.CurveEnd.Start,
        continuity,
    )

    if blend is None:
        raise GolemError(
            ErrorCode.OPERATION_FAILED,
            "Blend curves failed -- the curves may have incompatible end conditions "
            "for the requested continuity.",
        )

    result_guid = _add_curve_to_doc(blend)
    sc.doc.Views.Redraw()

    return {
        "guid": result_guid,
        "curve": serialize_curve(blend),
    }


@wrap_handler
@handler("operations.rebuild_curve")
def rebuild_curve(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Rebuild a curve to a specified degree and point count.

    The original curve object is replaced in the document.

    Parameters
    ----------
    curve_id : str
        GUID of the curve to rebuild.
    degree : int
        NURBS degree for the rebuilt curve (1–11).
    point_count : int
        Number of control points in the rebuilt curve (>= degree + 1).

    Returns
    -------
    dict
        ``{"guid": str, "curve": {...}}``
    """
    curve_id = _require(params, "curve_id", str)
    degree = _optional_int(params, "degree", 3)
    point_count = _optional_int(params, "point_count", 10)

    if degree < 1 or degree > 11:
        raise ValueError("degree must be between 1 and 11 (got {d}).".format(d=degree))
    if point_count < degree + 1:
        raise ValueError(
            "point_count must be at least degree + 1 (degree={d}, point_count={p}).".format(
                d=degree, p=point_count
            )
        )

    curve = _coerce_curve(curve_id)

    rebuilt = curve.Rebuild(point_count, degree, True)

    if rebuilt is None:
        raise GolemError(
            ErrorCode.OPERATION_FAILED,
            "Rebuild curve failed -- the curve may not support NURBS rebuilding.",
        )

    sys_orig = _coerce_guid(curve_id)
    sc.doc.Objects.Replace(sys_orig, rebuilt)
    sc.doc.Views.Redraw()

    return {
        "guid": curve_id,
        "curve": serialize_curve(rebuilt),
    }


@wrap_handler
@handler("operations.rebuild_surface")
def rebuild_surface(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Rebuild a NURBS surface to specified degrees and point counts.

    The original surface / Brep object is replaced in the document.

    Parameters
    ----------
    surface_id : str
        GUID of the surface or single-face Brep to rebuild.
    degree_u : int
        NURBS degree in the U direction (1–11).
    degree_v : int
        NURBS degree in the V direction (1–11).
    point_count_u : int
        Control point count in the U direction (>= degree_u + 1).
    point_count_v : int
        Control point count in the V direction (>= degree_v + 1).

    Returns
    -------
    dict
        ``{"guid": str, "surface": {...}}``
    """
    surface_id = _require(params, "surface_id", str)
    degree_u = _optional_int(params, "degree_u", 3)
    degree_v = _optional_int(params, "degree_v", 3)
    point_count_u = _optional_int(params, "point_count_u", 10)
    point_count_v = _optional_int(params, "point_count_v", 10)

    for label, deg in (("degree_u", degree_u), ("degree_v", degree_v)):
        if deg < 1 or deg > 11:
            raise ValueError(
                "{l} must be between 1 and 11 (got {d}).".format(l=label, d=deg)
            )

    if point_count_u < degree_u + 1:
        raise ValueError(
            "point_count_u must be at least degree_u + 1 "
            "(degree_u={d}, point_count_u={p}).".format(d=degree_u, p=point_count_u)
        )
    if point_count_v < degree_v + 1:
        raise ValueError(
            "point_count_v must be at least degree_v + 1 "
            "(degree_v={d}, point_count_v={p}).".format(d=degree_v, p=point_count_v)
        )

    registry.validate_guid(surface_id)
    sys_guid = _coerce_guid(surface_id)

    # rs.RebuildSurface returns the same GUID with the geometry replaced, or
    # raises on failure.
    result = rs.RebuildSurface(sys_guid, [degree_u, degree_v],
                                [point_count_u, point_count_v])

    if result is False or result is None:
        raise GolemError(
            ErrorCode.OPERATION_FAILED,
            "Rebuild surface failed -- ensure the object is a single NURBS surface.",
        )

    srf = rs.coercesurface(sys_guid)
    sc.doc.Views.Redraw()

    return {
        "guid": surface_id,
        "surface": serialize_surface(srf) if srf is not None else None,
    }
