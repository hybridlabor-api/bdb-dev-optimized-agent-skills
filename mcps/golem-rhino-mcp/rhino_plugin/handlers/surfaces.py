# -*- coding: utf-8 -*-
"""
rhino_plugin/handlers/surfaces.py
===================================
Surface operation handlers for GOLEM-3DMCP.

Covers: loft, sweep1, sweep2, revolve, extrude_curve, extrude_surface,
network_surface, patch, edge_surface, cap_planar_holes, unroll,
planar_surface.

Design notes
------------
* Runs INSIDE Rhino 3D under Python 3.9.
* Zero external dependencies -- only Python stdlib + Rhino/RhinoCommon APIs.
* Python 3.9 compatible: no ``match``/``case``, no ``X | Y`` union syntax,
  no lowercase ``dict[...]`` / ``list[...]`` generics in annotations.
* Every handler is registered via ``@handler("surfaces.<name>")`` from
  :mod:`rhino_plugin.dispatcher` so that
  :func:`~rhino_plugin.dispatcher.register_handlers_from_module` can
  discover and bulk-register them.
* GUID validation delegates to
  :class:`~rhino_plugin.utils.guid_registry.GuidRegistry`, whose
  :meth:`validate_guid` / :meth:`validate_guids` raise ``KeyError`` (message
  contains ``"not found"``) when an object is absent -- the dispatcher maps
  this to ``OBJECT_NOT_FOUND``.
* Bounding-box serialisation uses
  :func:`~rhino_plugin.utils.geometry_serializer.serialize_bounding_box`.

Rhino imports resolved at runtime:
    import Rhino
    import Rhino.Geometry as RG
    import scriptcontext as sc
    import rhinoscriptsyntax as rs
    import System
"""

import math
try:
    from typing import Any, Dict, List, Optional
except ImportError:
    pass

# ---------------------------------------------------------------------------
# Rhino imports -- guarded so linters outside Rhino do not explode.
# ---------------------------------------------------------------------------

try:
    import Rhino                          # noqa: F401
    import Rhino.Geometry as RG
    import scriptcontext as sc
    import rhinoscriptsyntax as rs        # noqa: F401
    import System
    _RHINO_AVAILABLE = True
except ImportError:
    _RHINO_AVAILABLE = False

# ---------------------------------------------------------------------------
# GOLEM-internal imports
# ---------------------------------------------------------------------------

from rhino_plugin.dispatcher import handler
from rhino_plugin.utils.guid_registry import registry
from rhino_plugin.utils.geometry_serializer import serialize_bounding_box


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

# Loft type string -> RhinoCommon LoftType enum integer mapping.
_LOFT_TYPE_MAP = {
    "normal":      0,   # LoftType.Normal
    "loose":       1,   # LoftType.Loose
    "tight":       2,   # LoftType.Tight
    "straight":    3,   # LoftType.Straight
    "developable": 4,   # LoftType.Developable
    "uniform":     5,   # LoftType.Uniform (rs alias, falls back to Normal)
}


def _get_curve_geometry(guid_str):
    # type: (str) -> Any
    """
    Look up *guid_str* in the Rhino document and return its
    ``Rhino.Geometry.Curve``.

    Raises
    ------
    KeyError
        If the object is not found (message contains "not found").
    ValueError
        If the object's geometry is not a Curve.
    """
    validated = registry.validate_guid(guid_str)
    sys_guid = System.Guid(validated)
    obj = sc.doc.Objects.FindId(sys_guid)
    if obj is None:
        raise KeyError(
            "Object not found in Rhino document: '{g}'".format(g=guid_str)
        )
    geom = obj.Geometry
    if not isinstance(geom, RG.Curve):
        raise ValueError(
            "Object '{g}' is not a Curve (got {t}).".format(
                g=guid_str, t=type(geom).__name__
            )
        )
    return geom


def _get_brep_geometry(guid_str):
    # type: (str) -> Any
    """
    Look up *guid_str* and return its ``Rhino.Geometry.Brep``.

    Raises
    ------
    KeyError
        If the object is not found.
    ValueError
        If the geometry is not a Brep.
    """
    validated = registry.validate_guid(guid_str)
    sys_guid = System.Guid(validated)
    obj = sc.doc.Objects.FindId(sys_guid)
    if obj is None:
        raise KeyError(
            "Object not found in Rhino document: '{g}'".format(g=guid_str)
        )
    geom = obj.Geometry
    if not isinstance(geom, RG.Brep):
        raise ValueError(
            "Object '{g}' is not a Brep (got {t}).".format(
                g=guid_str, t=type(geom).__name__
            )
        )
    return geom


def _bbox_from_guid(guid_str):
    # type: (str) -> Optional[Dict[str, Any]]
    """Return a serialised bounding box for the object with *guid_str*."""
    try:
        sys_guid = System.Guid(str(guid_str).strip().strip("{}").lower())
        obj = sc.doc.Objects.FindId(sys_guid)
        if obj is None:
            return None
        bbox = obj.Geometry.GetBoundingBox(True)
        return serialize_bounding_box(bbox)
    except Exception:
        return None


def _bbox_from_guids(guid_strs):
    # type: (List[str]) -> Optional[Dict[str, Any]]
    """
    Compute the union bounding box over a list of GUIDs and return it
    serialised.  Returns ``None`` if the list is empty or all lookups fail.
    """
    if not guid_strs:
        return None
    bbox = RG.BoundingBox.Empty
    for gs in guid_strs:
        try:
            sys_guid = System.Guid(str(gs).strip().strip("{}").lower())
            obj = sc.doc.Objects.FindId(sys_guid)
            if obj is not None:
                bbox = RG.BoundingBox.Union(bbox, obj.Geometry.GetBoundingBox(True))
        except Exception:
            pass
    if not bbox.IsValid:
        return None
    return serialize_bounding_box(bbox)


def _require_list(params, key):
    # type: (Dict[str, Any], str) -> List[Any]
    """Pull *key* from *params* as a non-empty list, raising ``ValueError`` if absent."""
    val = params.get(key)
    if not isinstance(val, list):
        raise ValueError(
            "Parameter '{k}' must be a list of GUID strings.".format(k=key)
        )
    if len(val) == 0:
        raise ValueError(
            "Parameter '{k}' must contain at least one GUID.".format(k=key)
        )
    return val


def _require_str(params, key):
    # type: (Dict[str, Any], str) -> str
    """Pull *key* from *params* as a non-empty string."""
    val = params.get(key)
    if not isinstance(val, str) or not val.strip():
        raise ValueError(
            "Parameter '{k}' must be a non-empty GUID string.".format(k=key)
        )
    return val


def _opt_xyz(params, key):
    # type: (Dict[str, Any], str) -> Optional[RG.Point3d]
    """
    Parse an optional ``[x, y, z]`` list from *params[key]* into a
    ``Rhino.Geometry.Point3d``.  Returns ``None`` if key is absent or ``None``.
    """
    val = params.get(key)
    if val is None:
        return None
    if not (isinstance(val, (list, tuple)) and len(val) == 3):
        raise ValueError(
            "Parameter '{k}' must be a list [x, y, z].".format(k=key)
        )
    try:
        return RG.Point3d(float(val[0]), float(val[1]), float(val[2]))
    except (TypeError, ValueError):
        raise ValueError(
            "Parameter '{k}' values must be numeric.".format(k=key)
        )


def _req_xyz_point(params, key):
    # type: (Dict[str, Any], str) -> RG.Point3d
    """Like ``_opt_xyz`` but raises ``ValueError`` when the key is absent."""
    pt = _opt_xyz(params, key)
    if pt is None:
        raise ValueError(
            "Required parameter '{k}' ([x, y, z]) is missing.".format(k=key)
        )
    return pt


def _tolerance():
    # type: () -> float
    """Return the absolute tolerance of the active Rhino document."""
    try:
        return sc.doc.ModelAbsoluteTolerance
    except Exception:
        return 0.001


# ---------------------------------------------------------------------------
# Handler: loft
# ---------------------------------------------------------------------------

@handler("surfaces.loft")
def loft(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Create a loft surface through an ordered sequence of cross-section curves.

    Parameters (params dict)
    ------------------------
    curve_ids : list[str]
        Ordered GUID strings of the cross-section curves (minimum 2).
    loft_type : str, optional
        One of "normal" (default), "loose", "tight", "straight",
        "developable", "uniform".
    closed : bool, optional
        Close the loft back to the first section (default False).
    start_point : [x, y, z], optional
        A tangent start point (adds an extra tangency condition at the start).
    end_point : [x, y, z], optional
        A tangent end point (adds an extra tangency condition at the end).

    Returns
    -------
    dict
        ``{"guid": str, "bounding_box": {...}}`` on success, or a GOLEM
        error dict on failure.
    """
    curve_ids = _require_list(params, "curve_ids")
    if len(curve_ids) < 2:
        raise ValueError("loft requires at least 2 curve GUIDs in 'curve_ids'.")

    loft_type_str = str(params.get("loft_type", "normal")).lower()
    if loft_type_str not in _LOFT_TYPE_MAP:
        raise ValueError(
            "Unknown loft_type '{t}'. Valid values: {v}.".format(
                t=loft_type_str, v=list(_LOFT_TYPE_MAP.keys())
            )
        )
    loft_type_int = _LOFT_TYPE_MAP[loft_type_str]

    closed = bool(params.get("closed", False))
    start_pt = _opt_xyz(params, "start_point")
    end_pt = _opt_xyz(params, "end_point")

    # Validate all curve GUIDs exist in the document.
    registry.validate_guids(curve_ids)

    # rs.AddLoftSrf expects the raw GUID strings (rhinoscriptsyntax resolves
    # them internally).  Pass start/end as a two-element tuple when provided;
    # rs docs state the optional second argument is a list/tuple of two points.
    start_end = None
    if start_pt is not None and end_pt is not None:
        start_end = (start_pt, end_pt)
    elif start_pt is not None:
        start_end = (start_pt, start_pt)  # degenerate; let Rhino handle it
    elif end_pt is not None:
        start_end = (end_pt, end_pt)

    try:
        if start_end is not None:
            result_ids = rs.AddLoftSrf(
                curve_ids,
                start_end[0], start_end[1],
                loft_type_int,
                closed=closed,
            )
        else:
            result_ids = rs.AddLoftSrf(
                curve_ids,
                loft_type=loft_type_int,
                closed=closed,
            )
    except Exception as exc:
        from rhino_plugin.utils.error_handler import ErrorCode, make_error
        return make_error(
            ErrorCode.OPERATION_FAILED,
            "rs.AddLoftSrf failed: {exc}".format(exc=exc),
        )

    if not result_ids:
        from rhino_plugin.utils.error_handler import ErrorCode, make_error
        return make_error(
            ErrorCode.OPERATION_FAILED,
            "Loft produced no geometry. Check that curves are compatible.",
        )

    sc.doc.Views.Redraw()

    # rs.AddLoftSrf may return a list of GUIDs when the loft creates multiple
    # faces.  Return the first (and usually only) GUID; expose all as extras.
    primary_guid = str(result_ids[0])
    all_guids = [str(g) for g in result_ids]
    bbox = _bbox_from_guids(all_guids)
    result = {"guid": primary_guid, "bounding_box": bbox}
    if len(all_guids) > 1:
        result["guids"] = all_guids
    return result


# ---------------------------------------------------------------------------
# Handler: sweep1
# ---------------------------------------------------------------------------

@handler("surfaces.sweep1")
def sweep1(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Create a surface by sweeping cross-section curves along a single rail.

    Parameters (params dict)
    ------------------------
    rail_id : str
        GUID of the rail (path) curve.
    shape_ids : list[str]
        Ordered GUIDs of cross-section curves.
    closed : bool, optional
        Close the sweep (default False).

    Returns
    -------
    dict
        ``{"guid": str, "bounding_box": {...}}`` on success.
    """
    rail_id = _require_str(params, "rail_id")
    shape_ids = _require_list(params, "shape_ids")
    closed = bool(params.get("closed", False))

    # Validate all GUIDs.
    registry.validate_guid(rail_id)
    registry.validate_guids(shape_ids)

    rail_curve = _get_curve_geometry(rail_id)
    shape_curves = [_get_curve_geometry(sid) for sid in shape_ids]

    tol = _tolerance()

    # RhinoCommon Brep.CreateFromSweep returns an array of Breps.
    try:
        breps = RG.Brep.CreateFromSweep(rail_curve, shape_curves, closed, tol)
    except Exception as exc:
        from rhino_plugin.utils.error_handler import ErrorCode, make_error
        return make_error(
            ErrorCode.OPERATION_FAILED,
            "Brep.CreateFromSweep (1-rail) failed: {exc}".format(exc=exc),
        )

    if not breps or len(breps) == 0:
        from rhino_plugin.utils.error_handler import ErrorCode, make_error
        return make_error(
            ErrorCode.OPERATION_FAILED,
            "Sweep1 produced no geometry. "
            "Check that the rail and cross-sections are compatible.",
        )

    # Add resulting Breps to the document.
    guids = []
    for brep in breps:
        brep.SetUserString("golem_source", "sweep1")
        obj_id = sc.doc.Objects.AddBrep(brep)
        if obj_id != System.Guid.Empty:
            guids.append(str(obj_id))
            registry.register(str(obj_id), obj_type="brep")

    sc.doc.Views.Redraw()

    if not guids:
        from rhino_plugin.utils.error_handler import ErrorCode, make_error
        return make_error(
            ErrorCode.OPERATION_FAILED,
            "Sweep1 geometry was created but could not be added to the document.",
        )

    bbox = _bbox_from_guids(guids)
    result = {"guid": guids[0], "bounding_box": bbox}
    if len(guids) > 1:
        result["guids"] = guids
    return result


# ---------------------------------------------------------------------------
# Handler: sweep2
# ---------------------------------------------------------------------------

@handler("surfaces.sweep2")
def sweep2(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Create a surface by sweeping cross-section curves along two rails.

    Parameters (params dict)
    ------------------------
    rail1_id : str
        GUID of the first rail curve.
    rail2_id : str
        GUID of the second rail curve.
    shape_ids : list[str]
        Ordered GUIDs of cross-section curves.
    closed : bool, optional
        Close the sweep (default False).

    Returns
    -------
    dict
        ``{"guid": str, "bounding_box": {...}}`` on success.
    """
    rail1_id = _require_str(params, "rail1_id")
    rail2_id = _require_str(params, "rail2_id")
    shape_ids = _require_list(params, "shape_ids")
    closed = bool(params.get("closed", False))

    registry.validate_guid(rail1_id)
    registry.validate_guid(rail2_id)
    registry.validate_guids(shape_ids)

    rail1 = _get_curve_geometry(rail1_id)
    rail2 = _get_curve_geometry(rail2_id)
    shapes = [_get_curve_geometry(sid) for sid in shape_ids]

    tol = _tolerance()

    try:
        breps = RG.Brep.CreateFromSweep(rail1, rail2, shapes, closed, tol)
    except Exception as exc:
        from rhino_plugin.utils.error_handler import ErrorCode, make_error
        return make_error(
            ErrorCode.OPERATION_FAILED,
            "Brep.CreateFromSweep (2-rail) failed: {exc}".format(exc=exc),
        )

    if not breps or len(breps) == 0:
        from rhino_plugin.utils.error_handler import ErrorCode, make_error
        return make_error(
            ErrorCode.OPERATION_FAILED,
            "Sweep2 produced no geometry. "
            "Check that both rails and cross-sections are compatible.",
        )

    guids = []
    for brep in breps:
        brep.SetUserString("golem_source", "sweep2")
        obj_id = sc.doc.Objects.AddBrep(brep)
        if obj_id != System.Guid.Empty:
            guids.append(str(obj_id))
            registry.register(str(obj_id), obj_type="brep")

    sc.doc.Views.Redraw()

    if not guids:
        from rhino_plugin.utils.error_handler import ErrorCode, make_error
        return make_error(
            ErrorCode.OPERATION_FAILED,
            "Sweep2 geometry was created but could not be added to the document.",
        )

    bbox = _bbox_from_guids(guids)
    result = {"guid": guids[0], "bounding_box": bbox}
    if len(guids) > 1:
        result["guids"] = guids
    return result


# ---------------------------------------------------------------------------
# Handler: revolve
# ---------------------------------------------------------------------------

@handler("surfaces.revolve")
def revolve(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Revolve a curve around an axis to create a surface of revolution.

    Parameters (params dict)
    ------------------------
    curve_id : str
        GUID of the profile curve.
    axis_start : [x, y, z]
        Start point of the revolution axis.
    axis_end : [x, y, z]
        End point of the revolution axis.
    start_angle : float, optional
        Start angle in degrees (default 0).
    end_angle : float, optional
        End angle in degrees (default 360).

    Returns
    -------
    dict
        ``{"guid": str, "bounding_box": {...}}`` on success.
    """
    curve_id = _require_str(params, "curve_id")
    axis_start = _req_xyz_point(params, "axis_start")
    axis_end = _req_xyz_point(params, "axis_end")
    start_angle = float(params.get("start_angle", 0.0))
    end_angle = float(params.get("end_angle", 360.0))

    if start_angle == end_angle:
        raise ValueError(
            "start_angle and end_angle must differ "
            "(got both as {a}).".format(a=start_angle)
        )

    registry.validate_guid(curve_id)

    # rs.AddRevSrf expects a list/tuple of two points for the axis, angles in
    # degrees, and the GUID string directly.
    try:
        result_id = rs.AddRevSrf(
            curve_id,
            (axis_start, axis_end),
            start_angle,
            end_angle,
        )
    except Exception as exc:
        from rhino_plugin.utils.error_handler import ErrorCode, make_error
        return make_error(
            ErrorCode.OPERATION_FAILED,
            "rs.AddRevSrf failed: {exc}".format(exc=exc),
        )

    if result_id is None:
        from rhino_plugin.utils.error_handler import ErrorCode, make_error
        return make_error(
            ErrorCode.OPERATION_FAILED,
            "Revolve produced no geometry. "
            "Check that the profile and axis are valid.",
        )

    sc.doc.Views.Redraw()
    guid_str = str(result_id)
    registry.register(guid_str, obj_type="surface")
    return {"guid": guid_str, "bounding_box": _bbox_from_guid(guid_str)}


# ---------------------------------------------------------------------------
# Handler: extrude_curve
# ---------------------------------------------------------------------------

@handler("surfaces.extrude_curve")
def extrude_curve(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Extrude a curve to create a surface or solid.

    Two modes are supported, selected by which parameters are present:

    **Direction mode** (``direction`` key present):
        Extrudes the curve in a straight line by the given vector distance.
        Uses ``rs.ExtrudeCurveStraight(curve_id, start_point, end_point)``.

    **Path mode** (``path_id`` key present):
        Extrudes the curve along an arbitrary path curve.
        Uses ``rs.ExtrudeCurve(curve_id, path_id)``.

    Parameters (params dict)
    ------------------------
    curve_id : str
        GUID of the curve to extrude.
    direction : [x, y, z], optional
        Extrusion direction vector (used in direction mode).
    distance : float, optional
        Scalar multiplier applied to *direction* (default 1.0).
    path_id : str, optional
        GUID of a path curve (used in path mode).
    cap : bool, optional
        Attempt to cap planar holes after extrusion (default False).

    Returns
    -------
    dict
        ``{"guid": str, "bounding_box": {...}}`` on success.
    """
    curve_id = _require_str(params, "curve_id")
    cap = bool(params.get("cap", False))

    registry.validate_guid(curve_id)

    direction_raw = params.get("direction")
    path_id = params.get("path_id")

    if direction_raw is None and path_id is None:
        raise ValueError(
            "Either 'direction' ([x, y, z]) or 'path_id' (GUID) must be provided."
        )

    result_id = None

    if direction_raw is not None:
        # Direction mode -- build a straight extrusion vector.
        if not (isinstance(direction_raw, (list, tuple)) and len(direction_raw) == 3):
            raise ValueError("'direction' must be a list [x, y, z].")
        dx, dy, dz = (float(v) for v in direction_raw)
        distance = float(params.get("distance", 1.0))
        length = math.sqrt(dx * dx + dy * dy + dz * dz)
        if length < 1e-12:
            raise ValueError(
                "'direction' vector has zero or near-zero length."
            )
        # Scale direction to the requested distance.
        scale = distance / length
        dx2, dy2, dz2 = dx * scale, dy * scale, dz * scale

        start_pt = RG.Point3d(0.0, 0.0, 0.0)
        end_pt = RG.Point3d(dx2, dy2, dz2)

        try:
            result_id = rs.ExtrudeCurveStraight(curve_id, start_pt, end_pt)
        except Exception as exc:
            from rhino_plugin.utils.error_handler import ErrorCode, make_error
            return make_error(
                ErrorCode.OPERATION_FAILED,
                "rs.ExtrudeCurveStraight failed: {exc}".format(exc=exc),
            )
    else:
        # Path mode -- extrude along an existing curve.
        registry.validate_guid(path_id)
        try:
            result_id = rs.ExtrudeCurve(curve_id, path_id)
        except Exception as exc:
            from rhino_plugin.utils.error_handler import ErrorCode, make_error
            return make_error(
                ErrorCode.OPERATION_FAILED,
                "rs.ExtrudeCurve failed: {exc}".format(exc=exc),
            )

    if result_id is None:
        from rhino_plugin.utils.error_handler import ErrorCode, make_error
        return make_error(
            ErrorCode.OPERATION_FAILED,
            "Extrude curve produced no geometry.",
        )

    guid_str = str(result_id)
    registry.register(guid_str, obj_type="brep")

    # Optionally cap planar holes.
    if cap:
        try:
            capped = rs.CapPlanarHoles(guid_str)
            if capped is not None:
                guid_str = str(capped)
                registry.register(guid_str, obj_type="brep")
        except Exception:
            pass  # Cap failure is non-fatal; return the uncapped result.

    sc.doc.Views.Redraw()
    return {"guid": guid_str, "bounding_box": _bbox_from_guid(guid_str)}


# ---------------------------------------------------------------------------
# Handler: extrude_surface
# ---------------------------------------------------------------------------

@handler("surfaces.extrude_surface")
def extrude_surface(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Extrude a surface (or Brep face) along a direction vector.

    ``rs.ExtrudeSurface`` requires a path *curve* rather than a bare vector.
    This handler creates a temporary ``LineCurve`` from the origin to
    ``direction * distance``, passes it to ``rs.ExtrudeSurface``, and then
    deletes the temporary curve.

    Parameters (params dict)
    ------------------------
    surface_id : str
        GUID of the surface or Brep to extrude.
    direction : [x, y, z]
        Extrusion direction vector.
    distance : float
        Extrusion distance (scales the direction vector).
    cap : bool, optional
        Cap planar open holes after extrusion (default False).

    Returns
    -------
    dict
        ``{"guid": str, "bounding_box": {...}}`` on success.
    """
    surface_id = _require_str(params, "surface_id")
    direction_raw = params.get("direction")
    distance = float(params.get("distance", 1.0))
    cap = bool(params.get("cap", False))

    if direction_raw is None:
        raise ValueError("'direction' ([x, y, z]) is required for extrude_surface.")
    if not (isinstance(direction_raw, (list, tuple)) and len(direction_raw) == 3):
        raise ValueError("'direction' must be a list [x, y, z].")

    dx, dy, dz = (float(v) for v in direction_raw)
    length = math.sqrt(dx * dx + dy * dy + dz * dz)
    if length < 1e-12:
        raise ValueError("'direction' vector has zero or near-zero length.")

    scale = distance / length
    dx2, dy2, dz2 = dx * scale, dy * scale, dz * scale

    registry.validate_guid(surface_id)

    # Build a temporary LineCurve as the extrusion path.
    path_start = RG.Point3d(0.0, 0.0, 0.0)
    path_end = RG.Point3d(dx2, dy2, dz2)
    path_line = RG.Line(path_start, path_end)
    path_curve = RG.LineCurve(path_line)

    # Add the path curve to the document so rs.ExtrudeSurface can find it.
    temp_path_id = sc.doc.Objects.AddCurve(path_curve)
    if temp_path_id == System.Guid.Empty:
        from rhino_plugin.utils.error_handler import ErrorCode, make_error
        return make_error(
            ErrorCode.OPERATION_FAILED,
            "Failed to create temporary path curve for extrude_surface.",
        )
    temp_path_str = str(temp_path_id)

    try:
        result_id = rs.ExtrudeSurface(surface_id, temp_path_str, cap)
    except Exception as exc:
        from rhino_plugin.utils.error_handler import ErrorCode, make_error
        return make_error(
            ErrorCode.OPERATION_FAILED,
            "rs.ExtrudeSurface failed: {exc}".format(exc=exc),
        )
    finally:
        # Always clean up the temporary path curve.
        try:
            sc.doc.Objects.Delete(temp_path_id, True)
        except Exception:
            pass

    if result_id is None:
        from rhino_plugin.utils.error_handler import ErrorCode, make_error
        return make_error(
            ErrorCode.OPERATION_FAILED,
            "Extrude surface produced no geometry.",
        )

    sc.doc.Views.Redraw()
    guid_str = str(result_id)
    registry.register(guid_str, obj_type="brep")
    return {"guid": guid_str, "bounding_box": _bbox_from_guid(guid_str)}


# ---------------------------------------------------------------------------
# Handler: network_surface
# ---------------------------------------------------------------------------

@handler("surfaces.network_surface")
def network_surface(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Create a surface from a network of U and V curves.

    Uses ``Rhino.Geometry.NurbsSurface.CreateNetworkSurface``.

    Parameters (params dict)
    ------------------------
    curves_u : list[str]
        GUIDs of curves running in the U direction.
    curves_v : list[str]
        GUIDs of curves running in the V direction.
    continuity : int, optional
        Continuity at boundaries: 0 = position, 1 = tangent (default),
        2 = curvature.

    Returns
    -------
    dict
        ``{"guid": str, "bounding_box": {...}}`` on success.
    """
    curves_u_ids = _require_list(params, "curves_u")
    curves_v_ids = _require_list(params, "curves_v")
    continuity = int(params.get("continuity", 1))

    if continuity not in (0, 1, 2):
        raise ValueError(
            "'continuity' must be 0 (position), 1 (tangent), or 2 (curvature). "
            "Got {c}.".format(c=continuity)
        )

    registry.validate_guids(curves_u_ids)
    registry.validate_guids(curves_v_ids)

    curves_u_geom = [_get_curve_geometry(cid) for cid in curves_u_ids]
    curves_v_geom = [_get_curve_geometry(cid) for cid in curves_v_ids]

    tol = _tolerance()

    # NurbsSurface.CreateNetworkSurface signature (RhinoCommon):
    #   CreateNetworkSurface(uCurves, uContinuity, vCurves, vContinuity,
    #                        edgeTolerance, out error) -> NurbsSurface
    # The continuity argument applies to both families of curves here.
    try:
        error = System.Int32(0)
        nurbs_srf = RG.NurbsSurface.CreateNetworkSurface(
            curves_u_geom,
            continuity,
            curves_v_geom,
            continuity,
            tol,
            error,
        )
    except TypeError:
        # Some Rhino versions expose a simpler overload without the error out-
        # parameter.  Fall back to it.
        try:
            nurbs_srf = RG.NurbsSurface.CreateNetworkSurface(
                curves_u_geom + curves_v_geom,
                continuity,
                tol,
                tol,
                tol,
            )
        except Exception as exc2:
            from rhino_plugin.utils.error_handler import ErrorCode, make_error
            return make_error(
                ErrorCode.OPERATION_FAILED,
                "NurbsSurface.CreateNetworkSurface failed: {exc}".format(exc=exc2),
            )
    except Exception as exc:
        from rhino_plugin.utils.error_handler import ErrorCode, make_error
        return make_error(
            ErrorCode.OPERATION_FAILED,
            "NurbsSurface.CreateNetworkSurface failed: {exc}".format(exc=exc),
        )

    if nurbs_srf is None:
        from rhino_plugin.utils.error_handler import ErrorCode, make_error
        return make_error(
            ErrorCode.OPERATION_FAILED,
            "Network surface produced no geometry. "
            "Check that U and V curves form a valid network.",
        )

    obj_id = sc.doc.Objects.AddSurface(nurbs_srf)
    if obj_id == System.Guid.Empty:
        from rhino_plugin.utils.error_handler import ErrorCode, make_error
        return make_error(
            ErrorCode.OPERATION_FAILED,
            "Network surface was created but could not be added to the document.",
        )

    sc.doc.Views.Redraw()
    guid_str = str(obj_id)
    registry.register(guid_str, obj_type="surface")
    return {"guid": guid_str, "bounding_box": _bbox_from_guid(guid_str)}


# ---------------------------------------------------------------------------
# Handler: patch
# ---------------------------------------------------------------------------

@handler("surfaces.patch")
def patch(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Fit a patch surface through / to a collection of curves and/or points.

    Uses ``rs.AddPatch``.

    Parameters (params dict)
    ------------------------
    object_ids : list[str]
        GUIDs of boundary curves, point objects, or a mix.
    spans_u : int, optional
        Number of surface spans in U (default 10).
    spans_v : int, optional
        Number of surface spans in V (default 10).
    flexibility : float, optional
        Surface stiffness; higher values allow the patch to deviate from
        the input (default 1.0).

    Returns
    -------
    dict
        ``{"guid": str, "bounding_box": {...}}`` on success.
    """
    object_ids = _require_list(params, "object_ids")
    spans_u = int(params.get("spans_u", 10))
    spans_v = int(params.get("spans_v", 10))
    flexibility = float(params.get("flexibility", 1.0))

    if spans_u < 1 or spans_v < 1:
        raise ValueError("'spans_u' and 'spans_v' must each be at least 1.")

    registry.validate_guids(object_ids)

    try:
        result_id = rs.AddPatch(object_ids, spans_u, spans_v, flexibility)
    except Exception as exc:
        from rhino_plugin.utils.error_handler import ErrorCode, make_error
        return make_error(
            ErrorCode.OPERATION_FAILED,
            "rs.AddPatch failed: {exc}".format(exc=exc),
        )

    if result_id is None:
        from rhino_plugin.utils.error_handler import ErrorCode, make_error
        return make_error(
            ErrorCode.OPERATION_FAILED,
            "Patch produced no geometry. "
            "Check that the input curves or points form a valid boundary.",
        )

    sc.doc.Views.Redraw()
    guid_str = str(result_id)
    registry.register(guid_str, obj_type="surface")
    return {"guid": guid_str, "bounding_box": _bbox_from_guid(guid_str)}


# ---------------------------------------------------------------------------
# Handler: edge_surface
# ---------------------------------------------------------------------------

@handler("surfaces.edge_surface")
def edge_surface(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Create a surface from 2, 3, or 4 edge curves.

    Uses ``rs.AddEdgeSrf``.

    Parameters (params dict)
    ------------------------
    curve_ids : list[str]
        2, 3, or 4 GUIDs of edge curves that together bound the surface.

    Returns
    -------
    dict
        ``{"guid": str, "bounding_box": {...}}`` on success.
    """
    curve_ids = _require_list(params, "curve_ids")
    if len(curve_ids) < 2 or len(curve_ids) > 4:
        raise ValueError(
            "edge_surface requires 2, 3, or 4 curves in 'curve_ids' "
            "(got {n}).".format(n=len(curve_ids))
        )

    registry.validate_guids(curve_ids)

    try:
        result_id = rs.AddEdgeSrf(curve_ids)
    except Exception as exc:
        from rhino_plugin.utils.error_handler import ErrorCode, make_error
        return make_error(
            ErrorCode.OPERATION_FAILED,
            "rs.AddEdgeSrf failed: {exc}".format(exc=exc),
        )

    if result_id is None:
        from rhino_plugin.utils.error_handler import ErrorCode, make_error
        return make_error(
            ErrorCode.OPERATION_FAILED,
            "Edge surface produced no geometry. "
            "Check that the curves meet at their endpoints.",
        )

    sc.doc.Views.Redraw()
    guid_str = str(result_id)
    registry.register(guid_str, obj_type="surface")
    return {"guid": guid_str, "bounding_box": _bbox_from_guid(guid_str)}


# ---------------------------------------------------------------------------
# Handler: cap_planar_holes
# ---------------------------------------------------------------------------

@handler("surfaces.cap_planar_holes")
def cap_planar_holes(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Cap all planar holes in a Brep with flat surfaces.

    Uses ``rs.CapPlanarHoles``.  The Rhino operation may return the same GUID
    (modified in place) or a new GUID if the object was replaced.

    Parameters (params dict)
    ------------------------
    brep_id : str
        GUID of the Brep to cap.

    Returns
    -------
    dict
        ``{"guid": str, "bounding_box": {...}}`` on success.
    """
    brep_id = _require_str(params, "brep_id")
    registry.validate_guid(brep_id)

    try:
        result_id = rs.CapPlanarHoles(brep_id)
    except Exception as exc:
        from rhino_plugin.utils.error_handler import ErrorCode, make_error
        return make_error(
            ErrorCode.OPERATION_FAILED,
            "rs.CapPlanarHoles failed: {exc}".format(exc=exc),
        )

    # rs.CapPlanarHoles returns None if no holes could be capped or if the
    # operation failed.  In that case we still return the original GUID so the
    # caller is not left empty-handed; but we signal the condition via a flag.
    if result_id is None:
        # Not necessarily a hard failure -- the brep may have had no planar
        # holes. Return the original GUID and flag it.
        sc.doc.Views.Redraw()
        return {
            "guid": brep_id,
            "bounding_box": _bbox_from_guid(brep_id),
            "caps_added": False,
            "note": "No planar holes were found or the operation had no effect.",
        }

    sc.doc.Views.Redraw()
    guid_str = str(result_id)
    registry.register(guid_str, obj_type="brep")
    return {
        "guid": guid_str,
        "bounding_box": _bbox_from_guid(guid_str),
        "caps_added": True,
    }


# ---------------------------------------------------------------------------
# Handler: unroll
# ---------------------------------------------------------------------------

@handler("surfaces.unroll")
def unroll(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Unroll a developable surface or Brep face into a flat 2-D layout.

    Uses ``Rhino.Geometry.Unroller``.  The unrolled curves and surfaces are
    added to the document and their GUIDs returned.

    Parameters (params dict)
    ------------------------
    surface_id : str
        GUID of the surface or Brep to unroll.
    explode : bool, optional
        If True, explode a multi-face Brep and unroll each face independently
        (default False).

    Returns
    -------
    dict
        ``{"guids": [str, ...], "bounding_box": {...}}`` on success.
        ``"guids"`` contains all added objects (surfaces and curves).
    """
    surface_id = _require_str(params, "surface_id")
    explode = bool(params.get("explode", False))

    registry.validate_guid(surface_id)

    # Retrieve the geometry.  Accept both Brep and Surface.
    validated = str(surface_id).strip().strip("{}").lower()
    sys_guid = System.Guid(validated)
    obj = sc.doc.Objects.FindId(sys_guid)
    if obj is None:
        raise KeyError(
            "Object not found in Rhino document: '{g}'".format(g=surface_id)
        )

    geom = obj.Geometry

    # Build a list of Breps to unroll.
    breps_to_unroll = []  # type: List[Any]
    if isinstance(geom, RG.Brep):
        if explode:
            for face in geom.Faces:
                face_brep = face.DuplicateFace(False)
                if face_brep is not None:
                    breps_to_unroll.append(face_brep)
        else:
            breps_to_unroll.append(geom)
    elif isinstance(geom, RG.Surface):
        brep = geom.ToBrep()
        if brep is not None:
            breps_to_unroll.append(brep)
    else:
        raise ValueError(
            "Object '{g}' is not a Surface or Brep (got {t}).".format(
                g=surface_id, t=type(geom).__name__
            )
        )

    if not breps_to_unroll:
        from rhino_plugin.utils.error_handler import ErrorCode, make_error
        return make_error(
            ErrorCode.OPERATION_FAILED,
            "Could not extract any faces to unroll from '{g}'.".format(g=surface_id),
        )

    added_guids = []

    for brep in breps_to_unroll:
        try:
            unroller = RG.Unroller(brep)
            unroller.ExplodeOutput = False  # keep as single output per face

            # PerformUnroll returns four arrays:
            #   (unrolled_surfaces, unrolled_curves, unrolled_points, unrolled_dots)
            unrolled_surfaces, unrolled_curves, _, _ = unroller.PerformUnroll()
        except Exception as exc:
            from rhino_plugin.utils.error_handler import ErrorCode, make_error
            return make_error(
                ErrorCode.OPERATION_FAILED,
                "Unroller.PerformUnroll failed: {exc}".format(exc=exc),
            )

        for srf in unrolled_surfaces:
            if srf is not None:
                brep_from_srf = srf.ToBrep() if isinstance(srf, RG.Surface) else srf
                if brep_from_srf is not None:
                    oid = sc.doc.Objects.AddBrep(brep_from_srf)
                else:
                    oid = sc.doc.Objects.AddSurface(srf)
                if oid != System.Guid.Empty:
                    gs = str(oid)
                    added_guids.append(gs)
                    registry.register(gs, obj_type="surface")

        for crv in unrolled_curves:
            if crv is not None:
                oid = sc.doc.Objects.AddCurve(crv)
                if oid != System.Guid.Empty:
                    gs = str(oid)
                    added_guids.append(gs)
                    registry.register(gs, obj_type="curve")

    sc.doc.Views.Redraw()

    if not added_guids:
        from rhino_plugin.utils.error_handler import ErrorCode, make_error
        return make_error(
            ErrorCode.OPERATION_FAILED,
            "Unroll produced no output. "
            "The surface may not be developable.",
        )

    bbox = _bbox_from_guids(added_guids)
    return {"guids": added_guids, "bounding_box": bbox}


# ---------------------------------------------------------------------------
# Handler: planar_surface
# ---------------------------------------------------------------------------

@handler("surfaces.planar_surface")
def planar_surface(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Create one or more planar surfaces from closed planar curves.

    Uses ``rs.AddPlanarSrf``.  Each closed planar curve in *curve_ids*
    that encloses an area will generate one planar surface.

    Parameters (params dict)
    ------------------------
    curve_ids : list[str]
        GUIDs of closed, planar boundary curves.

    Returns
    -------
    dict
        ``{"guid": str, "guids": [str, ...], "bounding_box": {...}}`` on
        success.  ``"guid"`` is always the first result GUID for convenience.
    """
    curve_ids = _require_list(params, "curve_ids")
    registry.validate_guids(curve_ids)

    try:
        result_ids = rs.AddPlanarSrf(curve_ids)
    except Exception as exc:
        from rhino_plugin.utils.error_handler import ErrorCode, make_error
        return make_error(
            ErrorCode.OPERATION_FAILED,
            "rs.AddPlanarSrf failed: {exc}".format(exc=exc),
        )

    if not result_ids:
        from rhino_plugin.utils.error_handler import ErrorCode, make_error
        return make_error(
            ErrorCode.OPERATION_FAILED,
            "Planar surface produced no geometry. "
            "Check that the boundary curves are closed and planar.",
        )

    sc.doc.Views.Redraw()

    guids = [str(g) for g in result_ids]
    for g in guids:
        registry.register(g, obj_type="surface")

    bbox = _bbox_from_guids(guids)
    result = {"guid": guids[0], "guids": guids, "bounding_box": bbox}
    return result
