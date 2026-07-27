# -*- coding: utf-8 -*-
"""
rhino_plugin/handlers/manipulation.py
======================================
Handlers for all object-manipulation operations: transforms, arrays, grouping,
join/explode, properties, and selection.

Registered methods (21 total):
  manipulation.move
  manipulation.copy
  manipulation.rotate
  manipulation.scale
  manipulation.mirror
  manipulation.orient
  manipulation.shear
  manipulation.array_linear
  manipulation.array_polar
  manipulation.array_along_curve
  manipulation.apply_transform
  manipulation.delete
  manipulation.group
  manipulation.ungroup
  manipulation.join
  manipulation.explode
  manipulation.set_properties
  manipulation.set_user_text
  manipulation.get_user_text
  manipulation.select_objects
  manipulation.unselect_all

Design notes
------------
* Python 3.9 compatible -- no ``match``/``case``, no ``X | Y`` union syntax,
  no lowercase ``list[...]`` / ``dict[...]`` generics in runtime annotations.
* Zero external dependencies -- only Python stdlib + Rhino-provided modules.
* All Rhino imports are guarded by a try/except so linters/CI outside Rhino
  can still import this module without exploding.
* Every handler is decorated with both ``@handler`` (registration) and
  ``@wrap_handler`` (uniform exception-to-error-dict conversion).
* Handlers raise ``ValueError`` for bad params and ``KeyError`` (with the
  phrase "not found") for missing objects so that ``wrap_handler`` maps them
  to the correct error codes.

Usage (from startup / server code)::

    import rhino_plugin.handlers.manipulation
    from rhino_plugin.dispatcher import register_handlers_from_module
    register_handlers_from_module(rhino_plugin.handlers.manipulation)
"""

import math
try:
    from typing import Any, Dict, List, Optional
except ImportError:
    pass

from rhino_plugin.dispatcher import handler
from rhino_plugin.utils.error_handler import wrap_handler, GolemError, ErrorCode

# ---------------------------------------------------------------------------
# Rhino-environment imports
# ---------------------------------------------------------------------------
# These are only available inside the Rhino Python environment.
# The try/except lets linters and unit-test runners import this module
# without crashing; at runtime inside Rhino they always succeed.

try:
    import Rhino                           # noqa: F401
    import Rhino.Geometry as RG
    import scriptcontext as sc
    import rhinoscriptsyntax as rs
    import System
    _RHINO_AVAILABLE = True
except ImportError:
    _RHINO_AVAILABLE = False


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _require_rhino():
    # type: () -> None
    """Raise GolemError if not running inside Rhino."""
    if not _RHINO_AVAILABLE:
        raise GolemError(
            ErrorCode.INTERNAL_ERROR,
            "Rhino environment is not available",
        )


def _parse_point(raw, field_name="point"):
    # type: (Any, str) -> List[float]
    """
    Coerce *raw* to a validated [x, y, z] float list.

    Accepts:
    - a list/tuple of 3 numbers
    - a dict with 'x', 'y', 'z' keys

    Raises ValueError on invalid input.
    """
    if isinstance(raw, dict):
        try:
            return [float(raw["x"]), float(raw["y"]), float(raw["z"])]
        except (KeyError, TypeError, ValueError):
            raise ValueError(
                "'{field}' dict must contain numeric 'x', 'y', 'z' keys".format(
                    field=field_name
                )
            )
    if isinstance(raw, (list, tuple)) and len(raw) == 3:
        try:
            return [float(raw[0]), float(raw[1]), float(raw[2])]
        except (TypeError, ValueError):
            raise ValueError(
                "'{field}' list must contain 3 numbers".format(field=field_name)
            )
    raise ValueError(
        "'{field}' must be a list [x, y, z] or dict with 'x','y','z' keys, "
        "got: {t}".format(field=field_name, t=type(raw).__name__)
    )


def _parse_point_or_default(raw, default, field_name="point"):
    # type: (Any, List[float], str) -> List[float]
    """Return *default* when *raw* is None; otherwise delegate to _parse_point."""
    if raw is None:
        return list(default)
    return _parse_point(raw, field_name)


def _to_rhino_point(xyz):
    # type: (List[float]) -> Any
    """Convert a [x, y, z] list to a ``Rhino.Geometry.Point3d``."""
    return RG.Point3d(xyz[0], xyz[1], xyz[2])


def _to_rhino_vector(xyz):
    # type: (List[float]) -> Any
    """Convert a [x, y, z] list to a ``Rhino.Geometry.Vector3d``."""
    return RG.Vector3d(xyz[0], xyz[1], xyz[2])


def _require_list_of_strings(value, field_name="ids"):
    # type: (Any, str) -> List[str]
    """Validate that *value* is a non-empty list of strings."""
    if not isinstance(value, (list, tuple)) or len(value) == 0:
        raise ValueError(
            "'{field}' must be a non-empty list of GUID strings".format(
                field=field_name
            )
        )
    result = []
    for item in value:
        if not isinstance(item, str):
            raise ValueError(
                "Each item in '{field}' must be a string GUID, got: {t}".format(
                    field=field_name, t=type(item).__name__
                )
            )
        result.append(item)
    return result


def _find_object(guid):
    # type: (str) -> Any
    """
    Locate a Rhino document object by GUID string.

    Raises KeyError (containing 'not found') if missing so that wrap_handler
    maps it to OBJECT_NOT_FOUND.
    """
    try:
        sys_guid = System.Guid(guid)
    except Exception:
        raise ValueError("Invalid GUID format: '{guid}'".format(guid=guid))
    obj = sc.doc.Objects.FindId(sys_guid)
    if obj is None:
        raise KeyError("Object not found in Rhino document: '{guid}'".format(guid=guid))
    return obj


def _guids_to_string_list(rhino_guids):
    # type: (Any) -> List[str]
    """
    Convert an iterable of Rhino GUIDs (or None/empty) to a list of strings.
    Returns an empty list if *rhino_guids* is None or empty.
    """
    if not rhino_guids:
        return []
    return [str(g) for g in rhino_guids]


def _detect_object_type(guid):
    # type: (str) -> str
    """
    Return a simple type label for the Rhino object: 'brep', 'curve',
    'mesh', 'extrusion', 'subd', or 'other'.
    """
    try:
        obj = _find_object(guid)
        geom = obj.Geometry
        if isinstance(geom, RG.Brep):
            return "brep"
        if isinstance(geom, RG.Extrusion):
            return "extrusion"
        if isinstance(geom, RG.Curve):
            return "curve"
        if isinstance(geom, RG.Mesh):
            return "mesh"
        if isinstance(geom, RG.SubD):
            return "subd"
    except Exception:
        pass
    return "other"


# ---------------------------------------------------------------------------
# 1. move
# ---------------------------------------------------------------------------

@wrap_handler
@handler("manipulation.move")
def move(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Translate one or more objects by a displacement vector.

    Required params:
        ids          (list[str]) -- GUIDs of objects to move.
        translation  (list[x,y,z] or dict) -- displacement vector.

    Returns:
        {"moved_ids": list[str], "count": int}
    """
    _require_rhino()

    ids = _require_list_of_strings(params.get("ids"), "ids")
    translation = _parse_point(
        params.get("translation", [0.0, 0.0, 0.0]), "translation"
    )

    start_pt = RG.Point3d(0.0, 0.0, 0.0)
    end_pt = _to_rhino_point(translation)

    result_guids = rs.MoveObjects(ids, start_pt, end_pt)

    if result_guids is None:
        raise GolemError(
            ErrorCode.OPERATION_FAILED,
            "rs.MoveObjects returned None -- check that all GUIDs exist",
            details={"ids": ids},
        )

    sc.doc.Views.Redraw()
    moved = _guids_to_string_list(result_guids)
    return {"moved_ids": moved, "count": len(moved)}


# ---------------------------------------------------------------------------
# 2. copy
# ---------------------------------------------------------------------------

@wrap_handler
@handler("manipulation.copy")
def copy(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Copy objects and optionally displace the copies.

    Required params:
        ids          (list[str]) -- GUIDs of objects to copy.

    Optional params:
        translation  (list[x,y,z] or dict, default [0,0,0]) -- displacement.

    Returns:
        {"new_ids": list[str], "count": int}
    """
    _require_rhino()

    ids = _require_list_of_strings(params.get("ids"), "ids")
    translation = _parse_point_or_default(
        params.get("translation"), [0.0, 0.0, 0.0], "translation"
    )

    start_pt = RG.Point3d(0.0, 0.0, 0.0)
    end_pt = _to_rhino_point(translation)

    result_guids = rs.CopyObjects(ids, start_pt, end_pt)

    if result_guids is None:
        raise GolemError(
            ErrorCode.OPERATION_FAILED,
            "rs.CopyObjects returned None -- check that all GUIDs exist",
            details={"ids": ids},
        )

    sc.doc.Views.Redraw()
    new_ids = _guids_to_string_list(result_guids)
    return {"new_ids": new_ids, "count": len(new_ids)}


# ---------------------------------------------------------------------------
# 3. rotate
# ---------------------------------------------------------------------------

@wrap_handler
@handler("manipulation.rotate")
def rotate(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Rotate objects around an axis point by a given angle.

    Required params:
        ids    (list[str])  -- GUIDs of objects to rotate.
        center (list[x,y,z] or dict) -- point on the rotation axis.
        angle  (float) -- rotation angle in degrees.

    Optional params:
        axis   (list[x,y,z] or dict, default [0,0,1]) -- rotation axis vector.
        copy   (bool, default False) -- rotate copies, leave originals.

    Returns:
        {"result_ids": list[str], "count": int}
    """
    _require_rhino()

    ids = _require_list_of_strings(params.get("ids"), "ids")
    center = _parse_point(params.get("center"), "center")
    angle_deg = params.get("angle")
    if angle_deg is None:
        raise ValueError("'angle' (degrees) is required")
    try:
        angle_deg = float(angle_deg)
    except (TypeError, ValueError):
        raise ValueError("'angle' must be a number, got: {v}".format(v=angle_deg))

    axis = _parse_point_or_default(params.get("axis"), [0.0, 0.0, 1.0], "axis")
    copy_flag = bool(params.get("copy", False))

    center_pt = _to_rhino_point(center)
    axis_vec = _to_rhino_vector(axis)

    result_guids = rs.RotateObjects(ids, center_pt, angle_deg, axis_vec, copy_flag)

    if result_guids is None:
        raise GolemError(
            ErrorCode.OPERATION_FAILED,
            "rs.RotateObjects returned None -- verify GUIDs and parameters",
            details={"ids": ids, "center": center, "angle": angle_deg},
        )

    sc.doc.Views.Redraw()
    result = _guids_to_string_list(result_guids)
    return {"result_ids": result, "count": len(result)}


# ---------------------------------------------------------------------------
# 4. scale
# ---------------------------------------------------------------------------

@wrap_handler
@handler("manipulation.scale")
def scale(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Scale objects uniformly or non-uniformly.

    Required params:
        ids          (list[str]) -- GUIDs of objects to scale.
        origin       (list[x,y,z] or dict) -- centre of scaling.
        scale_factor (float or list[x,y,z]) -- uniform scale if float;
                     non-uniform if a 3-element list.

    Optional params:
        copy (bool, default False) -- scale copies, leave originals.

    Returns:
        {"result_ids": list[str], "count": int}
    """
    _require_rhino()

    ids = _require_list_of_strings(params.get("ids"), "ids")
    origin_raw = params.get("origin")
    if origin_raw is None:
        raise ValueError("'origin' [x,y,z] is required")
    origin = _parse_point(origin_raw, "origin")

    scale_raw = params.get("scale_factor")
    if scale_raw is None:
        raise ValueError("'scale_factor' is required (float or [x,y,z])")

    copy_flag = bool(params.get("copy", False))
    origin_pt = _to_rhino_point(origin)

    # Determine uniform vs. non-uniform.
    if isinstance(scale_raw, (int, float)):
        sx = sy = sz = float(scale_raw)
    elif isinstance(scale_raw, (list, tuple)) and len(scale_raw) == 3:
        try:
            sx, sy, sz = float(scale_raw[0]), float(scale_raw[1]), float(scale_raw[2])
        except (TypeError, ValueError):
            raise ValueError("'scale_factor' list must contain 3 numbers")
    else:
        raise ValueError(
            "'scale_factor' must be a float (uniform) or list [sx, sy, sz] "
            "(non-uniform), got: {t}".format(t=type(scale_raw).__name__)
        )

    scale_pt = RG.Point3d(sx, sy, sz)
    result_guids = rs.ScaleObjects(ids, origin_pt, scale_pt, copy_flag)

    if result_guids is None:
        raise GolemError(
            ErrorCode.OPERATION_FAILED,
            "rs.ScaleObjects returned None -- verify GUIDs and parameters",
            details={"ids": ids, "origin": origin, "scale_factor": scale_raw},
        )

    sc.doc.Views.Redraw()
    result = _guids_to_string_list(result_guids)
    return {"result_ids": result, "count": len(result)}


# ---------------------------------------------------------------------------
# 5. mirror
# ---------------------------------------------------------------------------

@wrap_handler
@handler("manipulation.mirror")
def mirror(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Mirror objects across a plane defined by two points.

    Required params:
        ids   (list[str]) -- GUIDs of objects to mirror.
        start (list[x,y,z] or dict) -- first point on the mirror plane.
        end   (list[x,y,z] or dict) -- second point on the mirror plane.

    Optional params:
        copy (bool, default False) -- mirror copies, leave originals.

    Returns:
        {"result_ids": list[str], "count": int}
    """
    _require_rhino()

    ids = _require_list_of_strings(params.get("ids"), "ids")
    start = _parse_point(params.get("start"), "start")
    end = _parse_point(params.get("end"), "end")
    copy_flag = bool(params.get("copy", False))

    start_pt = _to_rhino_point(start)
    end_pt = _to_rhino_point(end)

    result_guids = rs.MirrorObjects(ids, start_pt, end_pt, copy_flag)

    if result_guids is None:
        raise GolemError(
            ErrorCode.OPERATION_FAILED,
            "rs.MirrorObjects returned None -- verify GUIDs and parameters",
            details={"ids": ids, "start": start, "end": end},
        )

    sc.doc.Views.Redraw()
    result = _guids_to_string_list(result_guids)
    return {"result_ids": result, "count": len(result)}


# ---------------------------------------------------------------------------
# 6. orient
# ---------------------------------------------------------------------------

@wrap_handler
@handler("manipulation.orient")
def orient(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Orient objects by mapping reference points to target points.

    Supports 2-point or 3-point orient (same as Rhino Orient command).
    When multiple objects are provided each is oriented independently using
    rs.OrientObject (which operates on a single object per call).

    Required params:
        ids              (list[str]) -- GUIDs of objects to orient.
        reference_points (list of [x,y,z]) -- 2 or 3 source points.
        target_points    (list of [x,y,z]) -- 2 or 3 destination points.

    Optional params:
        copy (bool, default False) -- orient copies, leave originals.

    Returns:
        {"result_ids": list[str], "count": int}
    """
    _require_rhino()

    ids = _require_list_of_strings(params.get("ids"), "ids")
    ref_raw = params.get("reference_points")
    tgt_raw = params.get("target_points")
    if ref_raw is None or not isinstance(ref_raw, (list, tuple)):
        raise ValueError("'reference_points' must be a list of [x,y,z] points")
    if tgt_raw is None or not isinstance(tgt_raw, (list, tuple)):
        raise ValueError("'target_points' must be a list of [x,y,z] points")
    if len(ref_raw) != len(tgt_raw):
        raise ValueError("'reference_points' and 'target_points' must have the same length")
    if len(ref_raw) < 2:
        raise ValueError("At least 2 reference/target point pairs are required")

    ref_pts = [_to_rhino_point(_parse_point(p, "reference_points[{i}]".format(i=i)))
               for i, p in enumerate(ref_raw)]
    tgt_pts = [_to_rhino_point(_parse_point(p, "target_points[{i}]".format(i=i)))
               for i, p in enumerate(tgt_raw)]
    copy_flag = bool(params.get("copy", False))

    result_ids = []
    for obj_id in ids:
        new_id = rs.OrientObject(obj_id, ref_pts, tgt_pts, copy_flag)
        if new_id is not None:
            result_ids.append(str(new_id))

    if not result_ids:
        raise GolemError(
            ErrorCode.OPERATION_FAILED,
            "rs.OrientObject returned None for all objects -- verify GUIDs",
            details={"ids": ids},
        )

    sc.doc.Views.Redraw()
    return {"result_ids": result_ids, "count": len(result_ids)}


# ---------------------------------------------------------------------------
# 7. shear
# ---------------------------------------------------------------------------

@wrap_handler
@handler("manipulation.shear")
def shear(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Shear objects using a Rhino.Geometry.Transform.Shear transform.

    Required params:
        ids             (list[str]) -- GUIDs of objects to shear.
        plane           (dict with 'origin', 'x_axis', 'y_axis') -- shear plane.
        shear_angle     (float) -- shear angle in degrees.
        shear_direction (list[x,y,z] or dict) -- direction vector of shear.

    Optional params:
        copy (bool, default False) -- shear copies, leave originals.

    Returns:
        {"result_ids": list[str], "count": int}
    """
    _require_rhino()

    ids = _require_list_of_strings(params.get("ids"), "ids")
    plane_raw = params.get("plane")
    if plane_raw is None or not isinstance(plane_raw, dict):
        raise ValueError(
            "'plane' must be a dict with 'origin', 'x_axis', 'y_axis' keys"
        )
    angle_raw = params.get("shear_angle")
    if angle_raw is None:
        raise ValueError("'shear_angle' (degrees) is required")
    try:
        angle_deg = float(angle_raw)
    except (TypeError, ValueError):
        raise ValueError("'shear_angle' must be a number")

    shear_dir_raw = params.get("shear_direction")
    if shear_dir_raw is None:
        raise ValueError("'shear_direction' [x,y,z] is required")
    shear_dir = _parse_point(shear_dir_raw, "shear_direction")
    copy_flag = bool(params.get("copy", False))

    # Build the Rhino Plane for the shear.
    plane_origin = _parse_point_or_default(
        plane_raw.get("origin"), [0.0, 0.0, 0.0], "plane.origin"
    )
    plane_x = _parse_point_or_default(
        plane_raw.get("x_axis"), [1.0, 0.0, 0.0], "plane.x_axis"
    )
    plane_y = _parse_point_or_default(
        plane_raw.get("y_axis"), [0.0, 1.0, 0.0], "plane.y_axis"
    )

    rg_plane = RG.Plane(
        _to_rhino_point(plane_origin),
        _to_rhino_vector(plane_x),
        _to_rhino_vector(plane_y),
    )

    # Build the shear vector: shear_direction scaled by tan(angle).
    angle_rad = math.radians(angle_deg)
    shear_vec = _to_rhino_vector(
        [shear_dir[0] * math.tan(angle_rad),
         shear_dir[1] * math.tan(angle_rad),
         shear_dir[2] * math.tan(angle_rad)]
    )

    xform = RG.Transform.Shear(rg_plane, shear_vec)
    if not xform.IsValid:
        raise GolemError(
            ErrorCode.OPERATION_FAILED,
            "Rhino.Geometry.Transform.Shear produced an invalid transform",
            details={"angle_deg": angle_deg, "shear_direction": shear_dir},
        )

    result_ids = []
    for obj_id in ids:
        try:
            sys_guid = System.Guid(obj_id)
        except Exception:
            raise ValueError("Invalid GUID format: '{g}'".format(g=obj_id))

        if copy_flag:
            new_guid = sc.doc.Objects.Transform(sys_guid, xform, False)
            if new_guid != System.Guid.Empty:
                result_ids.append(str(new_guid))
        else:
            success = sc.doc.Objects.Transform(sys_guid, xform, True)
            if success != System.Guid.Empty:
                result_ids.append(obj_id)

    if not result_ids:
        raise GolemError(
            ErrorCode.OPERATION_FAILED,
            "Shear transform could not be applied to any of the given objects",
            details={"ids": ids},
        )

    sc.doc.Views.Redraw()
    return {"result_ids": result_ids, "count": len(result_ids)}


# ---------------------------------------------------------------------------
# 8. array_linear
# ---------------------------------------------------------------------------

@wrap_handler
@handler("manipulation.array_linear")
def array_linear(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Create a linear array of an object along a direction vector.

    Required params:
        id        (str) -- GUID of the object to array.
        count     (int) -- total number of items in the array (including original).
        direction (list[x,y,z] or dict) -- spacing vector between copies.

    Returns:
        {"array_ids": list[str], "count": int}
    """
    _require_rhino()

    obj_id = params.get("id")
    if not isinstance(obj_id, str) or not obj_id:
        raise ValueError("'id' must be a non-empty GUID string")
    count = params.get("count")
    if count is None:
        raise ValueError("'count' (int) is required")
    try:
        count = int(count)
    except (TypeError, ValueError):
        raise ValueError("'count' must be an integer")
    if count < 2:
        raise ValueError("'count' must be at least 2")

    direction = _parse_point(params.get("direction"), "direction")
    dir_pt = _to_rhino_point(direction)

    result_guids = rs.ArrayLinear(obj_id, dir_pt, count)

    if result_guids is None:
        raise GolemError(
            ErrorCode.OPERATION_FAILED,
            "rs.ArrayLinear returned None -- verify the GUID and parameters",
            details={"id": obj_id, "count": count, "direction": direction},
        )

    sc.doc.Views.Redraw()
    array_ids = _guids_to_string_list(result_guids)
    return {"array_ids": array_ids, "count": len(array_ids)}


# ---------------------------------------------------------------------------
# 9. array_polar
# ---------------------------------------------------------------------------

@wrap_handler
@handler("manipulation.array_polar")
def array_polar(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Create a polar (circular) array of an object around a centre point.

    Required params:
        id     (str) -- GUID of the object to array.
        count  (int) -- total number of items (including original).
        center (list[x,y,z] or dict) -- centre of rotation.

    Optional params:
        angle (float, default 360) -- total arc angle in degrees.
        axis  (list[x,y,z] or dict, default [0,0,1]) -- rotation axis.

    Returns:
        {"array_ids": list[str], "count": int}
    """
    _require_rhino()

    obj_id = params.get("id")
    if not isinstance(obj_id, str) or not obj_id:
        raise ValueError("'id' must be a non-empty GUID string")
    count = params.get("count")
    if count is None:
        raise ValueError("'count' (int) is required")
    try:
        count = int(count)
    except (TypeError, ValueError):
        raise ValueError("'count' must be an integer")
    if count < 2:
        raise ValueError("'count' must be at least 2")

    center = _parse_point(params.get("center"), "center")
    angle_deg = float(params.get("angle", 360.0))
    axis = _parse_point_or_default(params.get("axis"), [0.0, 0.0, 1.0], "axis")

    center_pt = _to_rhino_point(center)
    axis_vec = _to_rhino_vector(axis)

    result_guids = rs.ArrayPolar(obj_id, count, center_pt, angle_deg, axis_vec)

    if result_guids is None:
        raise GolemError(
            ErrorCode.OPERATION_FAILED,
            "rs.ArrayPolar returned None -- verify the GUID and parameters",
            details={"id": obj_id, "count": count, "center": center},
        )

    sc.doc.Views.Redraw()
    array_ids = _guids_to_string_list(result_guids)
    return {"array_ids": array_ids, "count": len(array_ids)}


# ---------------------------------------------------------------------------
# 10. array_along_curve
# ---------------------------------------------------------------------------

@wrap_handler
@handler("manipulation.array_along_curve")
def array_along_curve(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Distribute copies of an object at evenly-spaced points along a curve,
    optionally orienting each copy to the curve tangent.

    This implements the equivalent of Rhino's ArrayCrv command by:
      1. Dividing the curve into ``count`` equal segments with DivideByCount.
      2. Copying the object to each division point.
      3. If orient=True, rotating each copy so its local Z aligns with
         the curve tangent at that point.

    Required params:
        id       (str) -- GUID of the object to array.
        curve_id (str) -- GUID of the guide curve.
        count    (int) -- number of copies to place (not including the original).

    Optional params:
        orient (bool, default True) -- align each copy to the curve tangent.

    Returns:
        {"array_ids": list[str], "count": int}
    """
    _require_rhino()

    obj_id = params.get("id")
    if not isinstance(obj_id, str) or not obj_id:
        raise ValueError("'id' must be a non-empty GUID string")
    curve_id = params.get("curve_id")
    if not isinstance(curve_id, str) or not curve_id:
        raise ValueError("'curve_id' must be a non-empty GUID string")
    count = params.get("count")
    if count is None:
        raise ValueError("'count' (int) is required")
    try:
        count = int(count)
    except (TypeError, ValueError):
        raise ValueError("'count' must be an integer")
    if count < 1:
        raise ValueError("'count' must be at least 1")

    orient_flag = bool(params.get("orient", True))

    # Validate both objects exist.
    _find_object(obj_id)
    crv_obj = _find_object(curve_id)

    curve_geom = crv_obj.Geometry
    if not isinstance(curve_geom, RG.Curve):
        raise ValueError(
            "'curve_id' does not refer to a curve object: '{g}'".format(g=curve_id)
        )

    # Divide the curve into count segments -> (count+1) points but we want
    # exactly 'count' placement points starting at index 0 (the start may be
    # the same as the original position; we place count new copies).
    t_values = curve_geom.DivideByCount(count, True)
    if t_values is None or len(t_values) == 0:
        raise GolemError(
            ErrorCode.OPERATION_FAILED,
            "Curve.DivideByCount returned no parameter values",
            details={"curve_id": curve_id, "count": count},
        )

    # Get the bounding box of the source object so we can use its centroid
    # as the placement reference (instead of the Rhino origin).
    src_obj = _find_object(obj_id)
    src_bbox = src_obj.Geometry.GetBoundingBox(True)
    src_centroid = src_bbox.Center

    array_ids = []
    for t in t_values:
        pt = curve_geom.PointAt(t)
        translation = RG.Vector3d(
            pt.X - src_centroid.X,
            pt.Y - src_centroid.Y,
            pt.Z - src_centroid.Z,
        )

        # Copy the object to the curve point.
        new_guids = rs.CopyObjects([obj_id], RG.Point3d(0, 0, 0),
                                   RG.Point3d(translation.X, translation.Y, translation.Z))
        if not new_guids:
            continue
        new_id = str(new_guids[0])

        if orient_flag:
            # Rotate the copy so that world Z aligns with the curve tangent.
            tangent = curve_geom.TangentAt(t)
            if tangent.IsValid and tangent.Length > 1e-12:
                world_z = RG.Vector3d(0.0, 0.0, 1.0)
                rotation_axis = RG.Vector3d.CrossProduct(world_z, tangent)
                if rotation_axis.Length > 1e-12:
                    rotation_axis.Unitize()
                    dot = world_z * tangent
                    # Clamp to [-1, 1] to guard against floating-point noise.
                    dot = max(-1.0, min(1.0, dot))
                    angle_rad = math.acos(dot)
                    xform = RG.Transform.Rotation(
                        angle_rad,
                        rotation_axis,
                        pt,
                    )
                    try:
                        new_sys_guid = System.Guid(new_id)
                        sc.doc.Objects.Transform(new_sys_guid, xform, True)
                    except Exception:
                        pass

        array_ids.append(new_id)

    if not array_ids:
        raise GolemError(
            ErrorCode.OPERATION_FAILED,
            "No copies were created along the curve",
            details={"id": obj_id, "curve_id": curve_id, "count": count},
        )

    sc.doc.Views.Redraw()
    return {"array_ids": array_ids, "count": len(array_ids)}


# ---------------------------------------------------------------------------
# 11. apply_transform
# ---------------------------------------------------------------------------

@wrap_handler
@handler("manipulation.apply_transform")
def apply_transform(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Apply an arbitrary 4x4 affine transformation matrix to objects.

    Required params:
        ids    (list[str]) -- GUIDs of objects to transform.
        matrix (list[list[float]]) -- 4x4 nested list (row-major).

    Optional params:
        copy (bool, default False) -- transform copies, leave originals.

    Returns:
        {"result_ids": list[str], "count": int}
    """
    _require_rhino()

    ids = _require_list_of_strings(params.get("ids"), "ids")
    matrix_raw = params.get("matrix")
    if matrix_raw is None:
        raise ValueError("'matrix' (4x4 nested list) is required")
    if not isinstance(matrix_raw, (list, tuple)) or len(matrix_raw) != 4:
        raise ValueError("'matrix' must be a list of exactly 4 rows")
    for row_idx, row in enumerate(matrix_raw):
        if not isinstance(row, (list, tuple)) or len(row) != 4:
            raise ValueError(
                "'matrix' row {r} must have exactly 4 elements".format(r=row_idx)
            )

    copy_flag = bool(params.get("copy", False))

    # Build a Rhino Transform from the 4x4 matrix.
    xform = RG.Transform()
    for r in range(4):
        for c in range(4):
            try:
                xform[r, c] = float(matrix_raw[r][c])
            except (TypeError, ValueError):
                raise ValueError(
                    "'matrix[{r}][{c}]' must be a number".format(r=r, c=c)
                )

    if not xform.IsValid:
        raise GolemError(
            ErrorCode.OPERATION_FAILED,
            "The provided 4x4 matrix produces an invalid Rhino Transform",
            details={"matrix": matrix_raw},
        )

    result_ids = []
    for obj_id in ids:
        try:
            sys_guid = System.Guid(obj_id)
        except Exception:
            raise ValueError("Invalid GUID format: '{g}'".format(g=obj_id))

        new_guid = sc.doc.Objects.Transform(sys_guid, xform, not copy_flag)
        if new_guid != System.Guid.Empty:
            result_ids.append(str(new_guid) if copy_flag else obj_id)

    if not result_ids:
        raise GolemError(
            ErrorCode.OPERATION_FAILED,
            "Transform could not be applied to any of the given objects",
            details={"ids": ids},
        )

    sc.doc.Views.Redraw()
    return {"result_ids": result_ids, "count": len(result_ids)}


# ---------------------------------------------------------------------------
# 12. delete
# ---------------------------------------------------------------------------

@wrap_handler
@handler("manipulation.delete")
def delete(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Delete one or more objects from the Rhino document.

    Required params:
        ids (list[str]) -- GUIDs of objects to delete.

    Returns:
        {"deleted_count": int}
    """
    _require_rhino()

    ids = _require_list_of_strings(params.get("ids"), "ids")
    deleted = rs.DeleteObjects(ids)
    count = int(deleted) if deleted is not None else 0
    sc.doc.Views.Redraw()
    return {"deleted_count": count}


# ---------------------------------------------------------------------------
# 13. group
# ---------------------------------------------------------------------------

@wrap_handler
@handler("manipulation.group")
def group(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Add objects to a new named group.

    Required params:
        ids  (list[str]) -- GUIDs of objects to group.

    Optional params:
        name (str) -- desired group name; Rhino will auto-generate one if omitted.

    Returns:
        {"group_name": str}
    """
    _require_rhino()

    ids = _require_list_of_strings(params.get("ids"), "ids")
    name_raw = params.get("name")

    if name_raw is not None and not isinstance(name_raw, str):
        raise ValueError("'name' must be a string")

    group_name = rs.AddGroup(name_raw) if name_raw else rs.AddGroup()

    if group_name is None:
        raise GolemError(
            ErrorCode.OPERATION_FAILED,
            "rs.AddGroup failed to create a group",
            details={"requested_name": name_raw},
        )

    result = rs.AddObjectsToGroup(ids, group_name)
    if result is None or result == 0:
        # Try to clean up the empty group.
        try:
            rs.DeleteGroup(group_name)
        except Exception:
            pass
        raise GolemError(
            ErrorCode.OPERATION_FAILED,
            "rs.AddObjectsToGroup could not add objects to group '{g}'".format(
                g=group_name
            ),
            details={"ids": ids, "group_name": group_name},
        )

    return {"group_name": group_name}


# ---------------------------------------------------------------------------
# 14. ungroup
# ---------------------------------------------------------------------------

@wrap_handler
@handler("manipulation.ungroup")
def ungroup(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Dissolve a group, freeing all member objects.

    Required params:
        group_name (str) -- name of the group to dissolve.

    Returns:
        {"freed_ids": list[str], "count": int}
    """
    _require_rhino()

    group_name = params.get("group_name")
    if not isinstance(group_name, str) or not group_name:
        raise ValueError("'group_name' must be a non-empty string")

    # Collect member GUIDs before dissolving.
    member_ids = rs.ObjectsByGroup(group_name)
    if member_ids is None:
        member_ids = []

    freed = [str(g) for g in member_ids]

    success = rs.DeleteGroup(group_name)
    if not success:
        raise GolemError(
            ErrorCode.OPERATION_FAILED,
            "rs.DeleteGroup failed for group '{g}'".format(g=group_name),
            details={"group_name": group_name},
        )

    return {"freed_ids": freed, "count": len(freed)}


# ---------------------------------------------------------------------------
# 15. join
# ---------------------------------------------------------------------------

@wrap_handler
@handler("manipulation.join")
def join(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Join multiple objects into one.

    Auto-detects geometry type:
    - If the majority are Brep/Extrusion → rs.JoinSurfaces
    - If the majority are Curve → rs.JoinCurves

    Required params:
        ids (list[str]) -- GUIDs of objects to join (minimum 2).

    Optional params:
        delete_input (bool, default True) -- delete input objects after join.

    Returns:
        {"joined_ids": list[str], "count": int}
    """
    _require_rhino()

    ids = _require_list_of_strings(params.get("ids"), "ids")
    if len(ids) < 2:
        raise ValueError("'ids' must contain at least 2 objects to join")
    delete_input = bool(params.get("delete_input", True))

    # Type-detect: count brep vs. curve objects.
    brep_count = 0
    curve_count = 0
    for obj_id in ids:
        t = _detect_object_type(obj_id)
        if t in ("brep", "extrusion"):
            brep_count += 1
        elif t == "curve":
            curve_count += 1

    if brep_count >= curve_count:
        joined = rs.JoinSurfaces(ids, delete_input)
    else:
        joined = rs.JoinCurves(ids, delete_input)

    if not joined:
        raise GolemError(
            ErrorCode.OPERATION_FAILED,
            "Join operation returned no results -- objects may not be joinable",
            details={"ids": ids},
        )

    if isinstance(joined, (list, tuple)):
        joined_ids = [str(g) for g in joined]
    else:
        joined_ids = [str(joined)]

    sc.doc.Views.Redraw()
    return {"joined_ids": joined_ids, "count": len(joined_ids)}


# ---------------------------------------------------------------------------
# 16. explode
# ---------------------------------------------------------------------------

@wrap_handler
@handler("manipulation.explode")
def explode(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Explode a joined object into its component parts.

    Required params:
        id (str) -- GUID of the object to explode.

    Optional params:
        delete_input (bool, default True) -- delete the input object after explode.

    Returns:
        {"exploded_ids": list[str], "count": int}
    """
    _require_rhino()

    obj_id = params.get("id")
    if not isinstance(obj_id, str) or not obj_id:
        raise ValueError("'id' must be a non-empty GUID string")
    delete_input = bool(params.get("delete_input", True))

    # Validate the object exists.
    _find_object(obj_id)

    result = rs.ExplodeObjects(obj_id, delete_input)

    if not result:
        raise GolemError(
            ErrorCode.OPERATION_FAILED,
            "rs.ExplodeObjects returned no results -- object may not be explodable",
            details={"id": obj_id},
        )

    exploded_ids = [str(g) for g in result]
    sc.doc.Views.Redraw()
    return {"exploded_ids": exploded_ids, "count": len(exploded_ids)}


# ---------------------------------------------------------------------------
# 17. set_properties
# ---------------------------------------------------------------------------

@wrap_handler
@handler("manipulation.set_properties")
def set_properties(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Set display/document properties on one or more objects.

    Required params:
        ids (list[str]) -- GUIDs of objects to modify.

    Optional params (apply whichever are provided):
        layer          (str) -- layer name (must already exist in document).
        color          (list [r,g,b] or [r,g,b,a]) -- object colour (0-255 per channel).
        name           (str) -- object name.
        visible        (bool) -- show/hide the object.
        locked         (bool) -- lock/unlock the object.
        material_index (int) -- render material index.

    Returns:
        {"updated_ids": list[str], "count": int, "applied": dict}
    """
    _require_rhino()

    ids = _require_list_of_strings(params.get("ids"), "ids")
    applied = {}  # type: Dict[str, Any]

    layer = params.get("layer")
    color_raw = params.get("color")
    name = params.get("name")
    visible = params.get("visible")
    locked = params.get("locked")
    material_index = params.get("material_index")

    # Validate layer existence before doing any work.
    if layer is not None:
        if not isinstance(layer, str):
            raise ValueError("'layer' must be a string")
        if rs.IsLayer(layer) is False:
            raise ValueError(
                "Layer '{l}' does not exist in the document".format(l=layer)
            )

    # Validate colour.
    rh_color = None
    if color_raw is not None:
        if not isinstance(color_raw, (list, tuple)) or len(color_raw) not in (3, 4):
            raise ValueError("'color' must be a list [r,g,b] or [r,g,b,a] (0-255)")
        try:
            ch = [int(c) for c in color_raw]
        except (TypeError, ValueError):
            raise ValueError("All 'color' channel values must be integers 0-255")
        for v in ch:
            if not 0 <= v <= 255:
                raise ValueError("Color channel values must be in range 0-255")
        a = ch[3] if len(ch) == 4 else 255
        rh_color = System.Drawing.Color.FromArgb(a, ch[0], ch[1], ch[2])

    updated_ids = []
    for obj_id in ids:
        changed = False
        try:
            sys_guid = System.Guid(obj_id)
        except Exception:
            raise ValueError("Invalid GUID format: '{g}'".format(g=obj_id))

        rh_obj = sc.doc.Objects.FindId(sys_guid)
        if rh_obj is None:
            raise KeyError("Object not found in Rhino document: '{g}'".format(g=obj_id))

        attrs = rh_obj.Attributes.Duplicate()

        if layer is not None:
            layer_idx = sc.doc.Layers.FindByFullPath(layer, -1)
            if layer_idx < 0:
                # Try non-full-path lookup.
                layer_idx = sc.doc.Layers.Find(layer, True)
            if layer_idx >= 0:
                attrs.LayerIndex = layer_idx
                changed = True
                applied["layer"] = layer

        if rh_color is not None:
            from Rhino.DocObjects import ObjectColorSource
            attrs.ColorSource = ObjectColorSource.ColorFromObject
            attrs.ObjectColor = rh_color
            changed = True
            applied["color"] = list(color_raw)

        if name is not None:
            if not isinstance(name, str):
                raise ValueError("'name' must be a string")
            attrs.Name = name
            changed = True
            applied["name"] = name

        if visible is not None:
            attrs.Visible = bool(visible)
            changed = True
            applied["visible"] = bool(visible)

        if locked is not None:
            from Rhino.DocObjects import ObjectMode
            attrs.Mode = ObjectMode.Locked if bool(locked) else ObjectMode.Normal
            changed = True
            applied["locked"] = bool(locked)

        if material_index is not None:
            try:
                mat_idx = int(material_index)
            except (TypeError, ValueError):
                raise ValueError("'material_index' must be an integer")
            from Rhino.DocObjects import ObjectMaterialSource
            attrs.MaterialSource = ObjectMaterialSource.MaterialFromObject
            attrs.MaterialIndex = mat_idx
            changed = True
            applied["material_index"] = mat_idx

        if changed:
            sc.doc.Objects.ModifyAttributes(rh_obj, attrs, True)
            updated_ids.append(obj_id)

    sc.doc.Views.Redraw()
    return {"updated_ids": updated_ids, "count": len(updated_ids), "applied": applied}


# ---------------------------------------------------------------------------
# 18. set_user_text
# ---------------------------------------------------------------------------

@wrap_handler
@handler("manipulation.set_user_text")
def set_user_text(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Set a user-text key/value pair on an object.

    Required params:
        id    (str) -- GUID of the target object.
        key   (str) -- user-text key.
        value (str) -- user-text value.

    Optional params:
        attached_to_geometry (bool, default False) -- attach to geometry rather
            than object attributes.

    Returns:
        {"id": str, "key": str, "value": str, "attached_to_geometry": bool}
    """
    _require_rhino()

    obj_id = params.get("id")
    if not isinstance(obj_id, str) or not obj_id:
        raise ValueError("'id' must be a non-empty GUID string")
    key = params.get("key")
    if not isinstance(key, str) or not key:
        raise ValueError("'key' must be a non-empty string")
    value = params.get("value")
    if not isinstance(value, str):
        raise ValueError("'value' must be a string")
    attached_to_geometry = bool(params.get("attached_to_geometry", False))

    # Validate the object exists.
    _find_object(obj_id)

    result = rs.SetUserText(obj_id, key, value, attached_to_geometry)
    if not result:
        raise GolemError(
            ErrorCode.OPERATION_FAILED,
            "rs.SetUserText returned False -- could not set user text",
            details={"id": obj_id, "key": key},
        )

    return {
        "id": obj_id,
        "key": key,
        "value": value,
        "attached_to_geometry": attached_to_geometry,
    }


# ---------------------------------------------------------------------------
# 19. get_user_text
# ---------------------------------------------------------------------------

@wrap_handler
@handler("manipulation.get_user_text")
def get_user_text(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Retrieve user-text from an object.

    Required params:
        id (str) -- GUID of the target object.

    Optional params:
        key (str) -- specific key to retrieve; if omitted, returns all
            key/value pairs as a dict.

    Returns:
        {"id": str, "user_text": str | dict}
        Where ``user_text`` is the string value (single key) or a
        ``{key: value}`` dict (all keys).
    """
    _require_rhino()

    obj_id = params.get("id")
    if not isinstance(obj_id, str) or not obj_id:
        raise ValueError("'id' must be a non-empty GUID string")
    key = params.get("key")  # Optional[str]

    # Validate the object exists.
    _find_object(obj_id)

    if key is not None:
        if not isinstance(key, str):
            raise ValueError("'key' must be a string when provided")
        value = rs.GetUserText(obj_id, key)
        return {"id": obj_id, "user_text": value}

    # Return all keys and values.
    all_keys = rs.GetUserText(obj_id)
    if not all_keys:
        return {"id": obj_id, "user_text": {}}

    user_text = {}  # type: Dict[str, str]
    if isinstance(all_keys, (list, tuple)):
        for k in all_keys:
            v = rs.GetUserText(obj_id, k)
            user_text[str(k)] = str(v) if v is not None else ""
    else:
        # Some Rhino versions return a single string if only one key exists.
        user_text[str(all_keys)] = str(rs.GetUserText(obj_id, all_keys) or "")

    return {"id": obj_id, "user_text": user_text}


# ---------------------------------------------------------------------------
# 20. select_objects
# ---------------------------------------------------------------------------

@wrap_handler
@handler("manipulation.select_objects")
def select_objects(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Select one or more objects in the Rhino viewport.

    Required params:
        ids (list[str]) -- GUIDs of objects to select.

    Returns:
        {"selected_ids": list[str], "count": int}
    """
    _require_rhino()

    ids = _require_list_of_strings(params.get("ids"), "ids")
    result = rs.SelectObjects(ids)
    selected = _guids_to_string_list(result) if result else []
    sc.doc.Views.Redraw()
    return {"selected_ids": selected, "count": len(selected)}


# ---------------------------------------------------------------------------
# 21. unselect_all
# ---------------------------------------------------------------------------

@wrap_handler
@handler("manipulation.unselect_all")
def unselect_all(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Deselect all currently selected objects in the Rhino viewport.

    No params required.

    Returns:
        {"unselected_count": int}
    """
    _require_rhino()

    count = rs.UnselectAllObjects()
    sc.doc.Views.Redraw()
    return {"unselected_count": int(count) if count is not None else 0}
