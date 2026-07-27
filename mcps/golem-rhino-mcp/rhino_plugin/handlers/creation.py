# -*- coding: utf-8 -*-
"""
rhino_plugin/handlers/creation.py
==================================
Geometry creation handlers for GOLEM-3DMCP.

Creates primitive solids, curves, points, and text objects directly in the
Rhino document.  All handlers run on Rhino's UI thread via the server's
``run_on_ui_thread`` wrapper.

Python 3.9 compatibility
------------------------
* No ``match``/``case`` statements.
* No ``X | Y`` union type syntax.
* No lowercase ``dict[...]`` / ``list[...]`` generics in runtime annotations.
* Zero external dependencies -- only Python stdlib + Rhino APIs.

Wire method names (must match ``mcp_server/tools/creation.py`` exactly):
    creation.create_box
    creation.create_sphere
    creation.create_cylinder
    creation.create_cone
    creation.create_torus
    creation.create_line
    creation.create_arc
    creation.create_circle
    creation.create_polyline
    creation.create_nurbs_curve
    creation.create_point
    creation.create_text
"""

import math
try:
    from typing import Any, Dict, List, Optional, Union
except ImportError:
    pass

try:
    import Rhino                                   # noqa: F401
    import Rhino.Geometry as RG                    # noqa: F401
    import scriptcontext as sc                     # noqa: F401
    import rhinoscriptsyntax as rs                 # noqa: F401
    import System                                  # noqa: F401
    _RHINO_AVAILABLE = True
except ImportError:
    _RHINO_AVAILABLE = False

from rhino_plugin.dispatcher import handler


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _resolve_layer_index(layer_name):
    # type: (Optional[str]) -> int
    """
    Return the layer index for *layer_name*, or the current layer index if
    *layer_name* is None/empty.  Raises ValueError if the layer is not found.
    """
    if not layer_name:
        return sc.doc.Layers.CurrentLayerIndex
    idx = sc.doc.Layers.FindByFullPath(str(layer_name), -1)
    if idx < 0:
        raise ValueError(
            "Layer not found: '{layer}'.  Create it first with scene.create_layer.".format(
                layer=layer_name
            )
        )
    return idx


def _set_object_attributes(obj_id, name, layer_index):
    # type: (Any, Optional[str], int) -> None
    """Apply optional name and layer to a newly-added Rhino object."""
    if not _RHINO_AVAILABLE or obj_id is None:
        return
    try:
        obj = sc.doc.Objects.FindId(obj_id)
        if obj is None:
            return
        attrs = obj.Attributes.Duplicate()
        if name:
            attrs.Name = str(name)
        attrs.LayerIndex = layer_index
        sc.doc.Objects.ModifyAttributes(obj, attrs, True)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Primitive solids
# ---------------------------------------------------------------------------

@handler("creation.create_box")
def create_box(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Create an axis-aligned rectangular box (cuboid).

    Params
    ------
    corner_x, corner_y, corner_z : float -- minimum corner (default 0)
    width   : float -- X dimension (default 1)
    depth   : float -- Y dimension (default 1)
    height  : float -- Z dimension (default 1)
    layer   : str   -- optional layer full path
    name    : str   -- optional object name

    Returns
    -------
    dict with ``guid`` of the created object.
    """
    if not _RHINO_AVAILABLE:
        raise RuntimeError("Rhino is not available in this environment.")

    cx = float(params.get("corner_x", 0.0))
    cy = float(params.get("corner_y", 0.0))
    cz = float(params.get("corner_z", 0.0))
    w  = float(params.get("width",  1.0))
    d  = float(params.get("depth",  1.0))
    h  = float(params.get("height", 1.0))

    if w <= 0 or d <= 0 or h <= 0:
        raise ValueError("width, depth, and height must all be greater than zero.")

    layer_name = params.get("layer", None)   # type: Optional[str]
    name       = params.get("name",  None)   # type: Optional[str]
    layer_idx  = _resolve_layer_index(layer_name)

    corner = RG.Point3d(cx, cy, cz)
    interval_x = RG.Interval(0.0, w)
    interval_y = RG.Interval(0.0, d)
    interval_z = RG.Interval(0.0, h)
    box = RG.Box(
        RG.Plane(corner, RG.Vector3d.XAxis, RG.Vector3d.YAxis),
        interval_x, interval_y, interval_z,
    )
    brep = box.ToBrep()
    if brep is None:
        raise RuntimeError("Rhino failed to create box geometry.")

    obj_id = sc.doc.Objects.AddBrep(brep)
    if obj_id == System.Guid.Empty:
        raise RuntimeError("Rhino refused to add the box to the document.")

    _set_object_attributes(obj_id, name, layer_idx)
    sc.doc.Views.Redraw()
    return {"guid": str(obj_id)}


@handler("creation.create_sphere")
def create_sphere(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Create a sphere.

    Params
    ------
    center_x, center_y, center_z : float -- sphere centre (default 0)
    radius : float -- sphere radius (default 1)
    layer  : str   -- optional layer full path
    name   : str   -- optional object name

    Returns
    -------
    dict with ``guid`` of the created object.
    """
    if not _RHINO_AVAILABLE:
        raise RuntimeError("Rhino is not available in this environment.")

    cx = float(params.get("center_x", 0.0))
    cy = float(params.get("center_y", 0.0))
    cz = float(params.get("center_z", 0.0))
    r  = float(params.get("radius", 1.0))

    if r <= 0:
        raise ValueError("radius must be greater than zero.")

    layer_name = params.get("layer", None)  # type: Optional[str]
    name       = params.get("name",  None)  # type: Optional[str]
    layer_idx  = _resolve_layer_index(layer_name)

    sphere = RG.Sphere(RG.Point3d(cx, cy, cz), r)
    brep = sphere.ToBrep()
    if brep is None:
        raise RuntimeError("Rhino failed to create sphere geometry.")

    obj_id = sc.doc.Objects.AddBrep(brep)
    if obj_id == System.Guid.Empty:
        raise RuntimeError("Rhino refused to add the sphere to the document.")

    _set_object_attributes(obj_id, name, layer_idx)
    sc.doc.Views.Redraw()
    return {"guid": str(obj_id)}


@handler("creation.create_cylinder")
def create_cylinder(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Create a cylinder.

    Params
    ------
    base_x, base_y, base_z : float -- centre of the base circle (default 0)
    radius : float -- cylinder radius (default 1)
    height : float -- cylinder height along Z (default 1)
    cap    : bool  -- cap both ends (default True)
    layer  : str   -- optional layer full path
    name   : str   -- optional object name

    Returns
    -------
    dict with ``guid`` of the created object.
    """
    if not _RHINO_AVAILABLE:
        raise RuntimeError("Rhino is not available in this environment.")

    bx = float(params.get("base_x", 0.0))
    by = float(params.get("base_y", 0.0))
    bz = float(params.get("base_z", 0.0))
    r  = float(params.get("radius", 1.0))
    h  = float(params.get("height", 1.0))
    cap = bool(params.get("cap", True))

    if r <= 0:
        raise ValueError("radius must be greater than zero.")
    if h == 0:
        raise ValueError("height must be non-zero.")

    layer_name = params.get("layer", None)  # type: Optional[str]
    name       = params.get("name",  None)  # type: Optional[str]
    layer_idx  = _resolve_layer_index(layer_name)

    base_plane = RG.Plane(RG.Point3d(bx, by, bz), RG.Vector3d.ZAxis)
    circle = RG.Circle(base_plane, r)
    cylinder = RG.Cylinder(circle, h)
    brep = cylinder.ToBrep(cap, cap)
    if brep is None:
        raise RuntimeError("Rhino failed to create cylinder geometry.")

    obj_id = sc.doc.Objects.AddBrep(brep)
    if obj_id == System.Guid.Empty:
        raise RuntimeError("Rhino refused to add the cylinder to the document.")

    _set_object_attributes(obj_id, name, layer_idx)
    sc.doc.Views.Redraw()
    return {"guid": str(obj_id)}


@handler("creation.create_cone")
def create_cone(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Create a cone with apex pointing along +Z from the base centre.

    Params
    ------
    base_x, base_y, base_z : float -- centre of the base circle (default 0)
    radius : float -- base radius (default 1)
    height : float -- cone height (default 1)
    cap    : bool  -- cap the base (default True)
    layer  : str   -- optional layer full path
    name   : str   -- optional object name

    Returns
    -------
    dict with ``guid`` of the created object.
    """
    if not _RHINO_AVAILABLE:
        raise RuntimeError("Rhino is not available in this environment.")

    bx = float(params.get("base_x", 0.0))
    by = float(params.get("base_y", 0.0))
    bz = float(params.get("base_z", 0.0))
    r  = float(params.get("radius", 1.0))
    h  = float(params.get("height", 1.0))
    cap = bool(params.get("cap", True))

    if r <= 0:
        raise ValueError("radius must be greater than zero.")
    if h == 0:
        raise ValueError("height must be non-zero.")

    layer_name = params.get("layer", None)  # type: Optional[str]
    name       = params.get("name",  None)  # type: Optional[str]
    layer_idx  = _resolve_layer_index(layer_name)

    base_plane = RG.Plane(RG.Point3d(bx, by, bz), RG.Vector3d.ZAxis)
    cone = RG.Cone(base_plane, h, r)
    brep = cone.ToBrep(cap)
    if brep is None:
        raise RuntimeError("Rhino failed to create cone geometry.")

    obj_id = sc.doc.Objects.AddBrep(brep)
    if obj_id == System.Guid.Empty:
        raise RuntimeError("Rhino refused to add the cone to the document.")

    _set_object_attributes(obj_id, name, layer_idx)
    sc.doc.Views.Redraw()
    return {"guid": str(obj_id)}


@handler("creation.create_torus")
def create_torus(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Create a torus centred at the given point in the XY plane.

    Params
    ------
    center_x, center_y, center_z : float -- torus centre (default 0)
    major_radius : float -- distance from torus centre to tube centre (default 2)
    minor_radius : float -- tube radius (default 0.5)
    layer        : str   -- optional layer full path
    name         : str   -- optional object name

    Returns
    -------
    dict with ``guid`` of the created object.
    """
    if not _RHINO_AVAILABLE:
        raise RuntimeError("Rhino is not available in this environment.")

    cx = float(params.get("center_x", 0.0))
    cy = float(params.get("center_y", 0.0))
    cz = float(params.get("center_z", 0.0))
    major = float(params.get("major_radius", 2.0))
    minor = float(params.get("minor_radius", 0.5))

    if major <= 0 or minor <= 0:
        raise ValueError("major_radius and minor_radius must both be greater than zero.")
    if minor >= major:
        raise ValueError("minor_radius must be less than major_radius.")

    layer_name = params.get("layer", None)  # type: Optional[str]
    name       = params.get("name",  None)  # type: Optional[str]
    layer_idx  = _resolve_layer_index(layer_name)

    base_plane = RG.Plane(RG.Point3d(cx, cy, cz), RG.Vector3d.ZAxis)
    torus = RG.Torus(base_plane, major, minor)
    brep = torus.ToBrep()
    if brep is None:
        raise RuntimeError("Rhino failed to create torus geometry.")

    obj_id = sc.doc.Objects.AddBrep(brep)
    if obj_id == System.Guid.Empty:
        raise RuntimeError("Rhino refused to add the torus to the document.")

    _set_object_attributes(obj_id, name, layer_idx)
    sc.doc.Views.Redraw()
    return {"guid": str(obj_id)}


# ---------------------------------------------------------------------------
# Curves
# ---------------------------------------------------------------------------

@handler("creation.create_line")
def create_line(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Create a line segment between two points.

    Params
    ------
    start_x, start_y, start_z : float -- start point (default 0)
    end_x,   end_y,   end_z   : float -- end point (default 1 on X)
    layer : str  -- optional layer full path
    name  : str  -- optional object name

    Returns
    -------
    dict with ``guid`` of the created curve object.
    """
    if not _RHINO_AVAILABLE:
        raise RuntimeError("Rhino is not available in this environment.")

    sx = float(params.get("start_x", 0.0))
    sy = float(params.get("start_y", 0.0))
    sz = float(params.get("start_z", 0.0))
    ex = float(params.get("end_x", 1.0))
    ey = float(params.get("end_y", 0.0))
    ez = float(params.get("end_z", 0.0))

    layer_name = params.get("layer", None)  # type: Optional[str]
    name       = params.get("name",  None)  # type: Optional[str]
    layer_idx  = _resolve_layer_index(layer_name)

    start = RG.Point3d(sx, sy, sz)
    end   = RG.Point3d(ex, ey, ez)
    line  = RG.Line(start, end)

    if not line.IsValid:
        raise ValueError("start and end points must be distinct.")

    obj_id = sc.doc.Objects.AddLine(line)
    if obj_id == System.Guid.Empty:
        raise RuntimeError("Rhino refused to add the line to the document.")

    _set_object_attributes(obj_id, name, layer_idx)
    sc.doc.Views.Redraw()
    return {"guid": str(obj_id)}


@handler("creation.create_circle")
def create_circle(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Create a circle in the XY plane at the given centre.

    Params
    ------
    center_x, center_y, center_z : float -- circle centre (default 0)
    radius : float -- circle radius (default 1)
    layer  : str   -- optional layer full path
    name   : str   -- optional object name

    Returns
    -------
    dict with ``guid`` of the created curve object.
    """
    if not _RHINO_AVAILABLE:
        raise RuntimeError("Rhino is not available in this environment.")

    cx = float(params.get("center_x", 0.0))
    cy = float(params.get("center_y", 0.0))
    cz = float(params.get("center_z", 0.0))
    r  = float(params.get("radius", 1.0))

    if r <= 0:
        raise ValueError("radius must be greater than zero.")

    layer_name = params.get("layer", None)  # type: Optional[str]
    name       = params.get("name",  None)  # type: Optional[str]
    layer_idx  = _resolve_layer_index(layer_name)

    plane  = RG.Plane(RG.Point3d(cx, cy, cz), RG.Vector3d.ZAxis)
    circle = RG.Circle(plane, r)
    obj_id = sc.doc.Objects.AddCircle(circle)
    if obj_id == System.Guid.Empty:
        raise RuntimeError("Rhino refused to add the circle to the document.")

    _set_object_attributes(obj_id, name, layer_idx)
    sc.doc.Views.Redraw()
    return {"guid": str(obj_id)}


@handler("creation.create_arc")
def create_arc(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Create a circular arc in the XY plane.

    Params
    ------
    center_x, center_y, center_z : float -- arc centre (default 0)
    radius      : float -- arc radius (default 1)
    start_angle : float -- start angle in degrees (default 0)
    end_angle   : float -- end angle in degrees (default 90)
    layer : str  -- optional layer full path
    name  : str  -- optional object name

    Returns
    -------
    dict with ``guid`` of the created curve object.
    """
    if not _RHINO_AVAILABLE:
        raise RuntimeError("Rhino is not available in this environment.")

    import math

    cx = float(params.get("center_x", 0.0))
    cy = float(params.get("center_y", 0.0))
    cz = float(params.get("center_z", 0.0))
    r  = float(params.get("radius", 1.0))
    start_deg = float(params.get("start_angle", 0.0))
    end_deg   = float(params.get("end_angle", 90.0))

    if r <= 0:
        raise ValueError("radius must be greater than zero.")

    layer_name = params.get("layer", None)  # type: Optional[str]
    name       = params.get("name",  None)  # type: Optional[str]
    layer_idx  = _resolve_layer_index(layer_name)

    plane = RG.Plane(RG.Point3d(cx, cy, cz), RG.Vector3d.ZAxis)
    arc   = RG.Arc(
        plane,
        r,
        RG.Interval(
            math.radians(start_deg),
            math.radians(end_deg),
        ),
    )
    obj_id = sc.doc.Objects.AddArc(arc)
    if obj_id == System.Guid.Empty:
        raise RuntimeError("Rhino refused to add the arc to the document.")

    _set_object_attributes(obj_id, name, layer_idx)
    sc.doc.Views.Redraw()
    return {"guid": str(obj_id)}


@handler("creation.create_polyline")
def create_polyline(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Create a polyline through a list of 3-D points.

    Params
    ------
    points : list of {x, y, z} dicts -- at least 2 required
    closed : bool -- close the polyline (default False)
    layer  : str  -- optional layer full path
    name   : str  -- optional object name

    Returns
    -------
    dict with ``guid`` of the created curve object.
    """
    if not _RHINO_AVAILABLE:
        raise RuntimeError("Rhino is not available in this environment.")

    raw_points = params.get("points", [])  # type: List[Any]
    if len(raw_points) < 2:
        raise ValueError("At least 2 points are required to create a polyline.")

    closed    = bool(params.get("closed", False))
    layer_name = params.get("layer", None)  # type: Optional[str]
    name       = params.get("name",  None)  # type: Optional[str]
    layer_idx  = _resolve_layer_index(layer_name)

    pts = []  # type: List[RG.Point3d]
    for i, pt in enumerate(raw_points):
        try:
            pts.append(RG.Point3d(
                float(pt.get("x", 0.0)),
                float(pt.get("y", 0.0)),
                float(pt.get("z", 0.0)),
            ))
        except Exception as exc:
            raise ValueError(
                "Invalid point at index {i}: {exc}".format(i=i, exc=exc)
            )

    if closed and pts[0].DistanceTo(pts[-1]) > 1e-10:
        pts.append(pts[0])

    polyline = RG.Polyline(pts)
    obj_id   = sc.doc.Objects.AddPolyline(polyline)
    if obj_id == System.Guid.Empty:
        raise RuntimeError("Rhino refused to add the polyline to the document.")

    _set_object_attributes(obj_id, name, layer_idx)
    sc.doc.Views.Redraw()
    return {"guid": str(obj_id)}


@handler("creation.create_nurbs_curve")
def create_nurbs_curve(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Create a NURBS curve through a list of control points.

    Params
    ------
    control_points : list of {x, y, z} dicts -- at least 2 required
    degree         : int  -- curve degree (default 3; clamped to 1..11)
    layer          : str  -- optional layer full path
    name           : str  -- optional object name

    Returns
    -------
    dict with ``guid`` of the created curve object and its actual ``degree``.
    """
    if not _RHINO_AVAILABLE:
        raise RuntimeError("Rhino is not available in this environment.")

    raw_pts = params.get("control_points", [])  # type: List[Any]
    if len(raw_pts) < 2:
        raise ValueError(
            "At least 2 control points are required to create a NURBS curve."
        )

    degree    = max(1, min(int(params.get("degree", 3)), 11))
    layer_name = params.get("layer", None)  # type: Optional[str]
    name       = params.get("name",  None)  # type: Optional[str]
    layer_idx  = _resolve_layer_index(layer_name)

    pts = []  # type: List[RG.Point3d]
    for i, pt in enumerate(raw_pts):
        try:
            pts.append(RG.Point3d(
                float(pt.get("x", 0.0)),
                float(pt.get("y", 0.0)),
                float(pt.get("z", 0.0)),
            ))
        except Exception as exc:
            raise ValueError(
                "Invalid control point at index {i}: {exc}".format(i=i, exc=exc)
            )

    # Clamp degree to number of points minus 1.
    degree = min(degree, len(pts) - 1)

    curve = RG.Curve.CreateInterpolatedCurve(pts, degree)
    if curve is None:
        raise RuntimeError("Rhino failed to create a NURBS curve through the given points.")

    obj_id = sc.doc.Objects.AddCurve(curve)
    if obj_id == System.Guid.Empty:
        raise RuntimeError("Rhino refused to add the NURBS curve to the document.")

    _set_object_attributes(obj_id, name, layer_idx)
    sc.doc.Views.Redraw()
    return {"guid": str(obj_id), "degree": degree}


# ---------------------------------------------------------------------------
# Points and annotations
# ---------------------------------------------------------------------------

@handler("creation.create_point")
def create_point(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Create a point object at the given coordinates.

    Params
    ------
    x, y, z : float -- point coordinates (default 0)
    layer   : str   -- optional layer full path
    name    : str   -- optional object name

    Returns
    -------
    dict with ``guid`` of the created point object.
    """
    if not _RHINO_AVAILABLE:
        raise RuntimeError("Rhino is not available in this environment.")

    x = float(params.get("x", 0.0))
    y = float(params.get("y", 0.0))
    z = float(params.get("z", 0.0))

    layer_name = params.get("layer", None)  # type: Optional[str]
    name       = params.get("name",  None)  # type: Optional[str]
    layer_idx  = _resolve_layer_index(layer_name)

    obj_id = sc.doc.Objects.AddPoint(RG.Point3d(x, y, z))
    if obj_id == System.Guid.Empty:
        raise RuntimeError("Rhino refused to add the point to the document.")

    _set_object_attributes(obj_id, name, layer_idx)
    sc.doc.Views.Redraw()
    return {"guid": str(obj_id)}


@handler("creation.create_text")
def create_text(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Create a text annotation object.

    Params
    ------
    text           : str   -- text content (required)
    x, y, z        : float -- insertion point (default 0)
    height         : float -- text height in model units (default 1)
    font           : str   -- font face name (default "Arial")
    bold           : bool  -- bold weight (default False)
    italic         : bool  -- italic style (default False)
    layer          : str   -- optional layer full path
    name           : str   -- optional object name

    Returns
    -------
    dict with ``guid`` of the created text object.
    """
    if not _RHINO_AVAILABLE:
        raise RuntimeError("Rhino is not available in this environment.")

    text_str = str(params.get("text", ""))
    if not text_str:
        raise ValueError("'text' parameter is required and must be non-empty.")

    x      = float(params.get("x", 0.0))
    y      = float(params.get("y", 0.0))
    z      = float(params.get("z", 0.0))
    height = float(params.get("height", 1.0))
    font   = str(params.get("font", "Arial"))
    bold   = bool(params.get("bold", False))
    italic = bool(params.get("italic", False))

    if height <= 0:
        raise ValueError("height must be greater than zero.")

    layer_name = params.get("layer", None)  # type: Optional[str]
    name       = params.get("name",  None)  # type: Optional[str]
    layer_idx  = _resolve_layer_index(layer_name)

    plane = RG.Plane(RG.Point3d(x, y, z), RG.Vector3d.ZAxis)

    try:
        text_entity = RG.TextEntity.Create(
            text_str,
            plane,
            sc.doc.DimStyles.Current,
            False,
            0.0,
            0.0,
        )
        if text_entity is None:
            raise RuntimeError("Rhino returned None for the text entity.")
        text_entity.TextHeight = height
        obj_id = sc.doc.Objects.Add(text_entity)
    except Exception as exc:
        raise RuntimeError(
            "Failed to create text annotation: {exc}".format(exc=exc)
        )

    if obj_id == System.Guid.Empty:
        raise RuntimeError("Rhino refused to add the text object to the document.")

    _set_object_attributes(obj_id, name, layer_idx)
    sc.doc.Views.Redraw()
    return {"guid": str(obj_id)}


# ===========================================================================
# geometry.* handlers  (namespace used by mcp_server/tools/creation.py)
# These extend the creation.* set above with the full 26-handler spec.
# ===========================================================================

# ---------------------------------------------------------------------------
# Private helpers shared by the geometry.* handlers
# ---------------------------------------------------------------------------

def _pt3d(raw):
    # type: (Any) -> Any
    """Accept [x,y,z] list/tuple or {x,y,z} dict → Rhino.Geometry.Point3d."""
    if isinstance(raw, (list, tuple)):
        if len(raw) < 3:
            raise ValueError("Point list needs 3 elements, got {n}.".format(n=len(raw)))
        return RG.Point3d(float(raw[0]), float(raw[1]), float(raw[2]))
    if isinstance(raw, dict):
        try:
            return RG.Point3d(float(raw["x"]), float(raw["y"]), float(raw["z"]))
        except KeyError as exc:
            raise ValueError("Point dict missing key {k}.".format(k=exc))
    raise ValueError("Expected list or dict for point, got {t!r}.".format(t=type(raw).__name__))


def _plane_param(raw):
    # type: (Any) -> Any
    """Build a Rhino.Geometry.Plane from a dict or bare-point list."""
    if raw is None:
        raise ValueError("Plane parameter is None.")
    if isinstance(raw, (list, tuple)):
        return RG.Plane(_pt3d(raw), RG.Vector3d.ZAxis)
    if not isinstance(raw, dict):
        raise ValueError("Plane must be a dict, got {t!r}.".format(t=type(raw).__name__))
    origin = _pt3d(raw.get("origin") or [0.0, 0.0, 0.0])
    if "normal" in raw and raw["normal"] is not None:
        n = raw["normal"]
        nv = RG.Vector3d(float(n[0]), float(n[1]), float(n[2])) \
            if isinstance(n, (list, tuple)) \
            else RG.Vector3d(float(n["x"]), float(n["y"]), float(n["z"]))
        return RG.Plane(origin, nv)
    if "x_axis" in raw and "y_axis" in raw:
        def _v(r):
            # type: (Any) -> Any
            return RG.Vector3d(float(r[0]), float(r[1]), float(r[2])) \
                if isinstance(r, (list, tuple)) \
                else RG.Vector3d(float(r["x"]), float(r["y"]), float(r["z"]))
        return RG.Plane(origin, _v(raw["x_axis"]), _v(raw["y_axis"]))
    return RG.Plane(origin, RG.Vector3d.ZAxis)


def _req(params, key):
    # type: (Dict[str, Any], str) -> Any
    val = params.get(key)
    if val is None:
        raise ValueError("Required parameter '{k}' is missing.".format(k=key))
    return val


def _bbox(geom):
    # type: (Any) -> Dict[str, Any]
    try:
        bb = geom.GetBoundingBox(True)
        return {
            "min": [float(bb.Min.X), float(bb.Min.Y), float(bb.Min.Z)],
            "max": [float(bb.Max.X), float(bb.Max.Y), float(bb.Max.Z)],
        }
    except Exception:
        return {"min": [0.0, 0.0, 0.0], "max": [0.0, 0.0, 0.0]}


def _apply_color(obj_id, color):
    # type: (Any, Any) -> None
    """Apply an [r,g,b] or [r,g,b,a] color to a Rhino object."""
    if color is None or not _RHINO_AVAILABLE:
        return
    try:
        if isinstance(color, (list, tuple)) and len(color) >= 3:
            a = int(color[3]) if len(color) >= 4 else 255
            c = System.Drawing.Color.FromArgb(a, int(color[0]), int(color[1]), int(color[2]))
            obj = sc.doc.Objects.FindId(obj_id)
            if obj is None:
                return
            attrs = obj.Attributes.Duplicate()
            attrs.ColorSource = Rhino.DocObjects.ObjectColorSource.ColorFromObject
            attrs.ObjectColor = c
            sc.doc.Objects.ModifyAttributes(obj, attrs, True)
    except Exception:
        pass


def _g_attrs(params):
    # type: (Dict[str, Any]) -> tuple
    """Return (name, layer_idx) from params, resolving layer."""
    return params.get("name"), _resolve_layer_index(params.get("layer"))


# ---------------------------------------------------------------------------
# Points
# ---------------------------------------------------------------------------

@handler("geometry.create_point")
def geometry_create_point(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Create a point. Accepts x/y/z scalars, 'point' key, or 'location' key.
    Optional: name, layer, color.
    Returns: {guid, type, bounding_box}.
    """
    if not _RHINO_AVAILABLE:
        raise RuntimeError("Rhino is not available.")

    if "x" in params or "y" in params or "z" in params:
        pt = RG.Point3d(
            float(params.get("x", 0.0)),
            float(params.get("y", 0.0)),
            float(params.get("z", 0.0)),
        )
    elif "point" in params:
        pt = _pt3d(params["point"])
    elif "location" in params:
        pt = _pt3d(params["location"])
    else:
        raise ValueError(
            "create_point requires 'x'/'y'/'z', 'point', or 'location'."
        )

    name, layer_idx = _g_attrs(params)
    obj_id = sc.doc.Objects.AddPoint(pt)
    if obj_id == System.Guid.Empty:
        raise RuntimeError("Rhino refused to add the point.")

    _set_object_attributes(obj_id, name, layer_idx)
    _apply_color(obj_id, params.get("color"))
    sc.doc.Views.Redraw()
    return {"guid": str(obj_id), "type": "point", "bounding_box": _bbox(RG.Point(pt))}


@handler("geometry.create_point_cloud")
def geometry_create_point_cloud(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Create a point cloud from a list of [x,y,z] points.
    Optional: name, layer, color.
    """
    if not _RHINO_AVAILABLE:
        raise RuntimeError("Rhino is not available.")

    raw_pts = _req(params, "points")
    if not isinstance(raw_pts, (list, tuple)) or len(raw_pts) == 0:
        raise ValueError("'points' must be a non-empty list.")

    cloud = RG.PointCloud()
    for i, raw in enumerate(raw_pts):
        try:
            cloud.Add(_pt3d(raw))
        except Exception as exc:
            raise ValueError("Invalid point at index {i}: {err}".format(i=i, err=exc))

    name, layer_idx = _g_attrs(params)
    obj_id = sc.doc.Objects.AddPointCloud(cloud)
    if obj_id == System.Guid.Empty:
        raise RuntimeError("Rhino refused to add the point cloud.")

    _set_object_attributes(obj_id, name, layer_idx)
    _apply_color(obj_id, params.get("color"))
    sc.doc.Views.Redraw()
    return {
        "guid": str(obj_id),
        "type": "point_cloud",
        "point_count": cloud.Count,
        "bounding_box": _bbox(cloud),
    }


# ---------------------------------------------------------------------------
# Lines / Polylines
# ---------------------------------------------------------------------------

@handler("geometry.create_line")
def geometry_create_line(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """Create a line. Params: start, end ([x,y,z] each). Optional: name, layer, color."""
    if not _RHINO_AVAILABLE:
        raise RuntimeError("Rhino is not available.")

    start = _pt3d(_req(params, "start"))
    end = _pt3d(_req(params, "end"))
    line = RG.Line(start, end)
    if not line.IsValid:
        raise ValueError("start and end must be distinct points.")

    name, layer_idx = _g_attrs(params)
    obj_id = sc.doc.Objects.AddLine(line)
    if obj_id == System.Guid.Empty:
        raise RuntimeError("Rhino refused to add the line.")

    _set_object_attributes(obj_id, name, layer_idx)
    _apply_color(obj_id, params.get("color"))
    sc.doc.Views.Redraw()
    return {"guid": str(obj_id), "type": "line", "bounding_box": _bbox(RG.LineCurve(line))}


@handler("geometry.create_polyline")
def geometry_create_polyline(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """Create a polyline. Params: points (list of [x,y,z], min 2). Optional: name, layer, color."""
    if not _RHINO_AVAILABLE:
        raise RuntimeError("Rhino is not available.")

    raw_pts = _req(params, "points")
    if not isinstance(raw_pts, (list, tuple)) or len(raw_pts) < 2:
        raise ValueError("'points' must have at least 2 entries.")

    pts = []
    for i, raw in enumerate(raw_pts):
        try:
            pts.append(_pt3d(raw))
        except Exception as exc:
            raise ValueError("Invalid point at index {i}: {err}".format(i=i, err=exc))

    polyline = RG.Polyline(pts)
    name, layer_idx = _g_attrs(params)
    obj_id = sc.doc.Objects.AddPolyline(polyline)
    if obj_id == System.Guid.Empty:
        raise RuntimeError("Rhino refused to add the polyline.")

    _set_object_attributes(obj_id, name, layer_idx)
    _apply_color(obj_id, params.get("color"))
    sc.doc.Views.Redraw()
    return {"guid": str(obj_id), "type": "polyline", "bounding_box": _bbox(polyline)}


# ---------------------------------------------------------------------------
# Curves
# ---------------------------------------------------------------------------

@handler("geometry.create_nurbs_curve")
def geometry_create_nurbs_curve(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Create a NURBS curve from control points.
    Params: points (list of [x,y,z]), degree (int, default 3).
    Optional: weights, knots, periodic (bool), name, layer, color.
    """
    if not _RHINO_AVAILABLE:
        raise RuntimeError("Rhino is not available.")

    raw_pts = _req(params, "points")
    degree = int(params.get("degree", 3))

    if not isinstance(raw_pts, (list, tuple)) or len(raw_pts) < 2:
        raise ValueError("'points' must have at least 2 entries.")
    if degree < 1 or degree > 11:
        raise ValueError("'degree' must be 1-11, got {d}.".format(d=degree))

    pts = []
    for i, raw in enumerate(raw_pts):
        try:
            pts.append(_pt3d(raw))
        except Exception as exc:
            raise ValueError("Invalid point at index {i}: {err}".format(i=i, err=exc))

    degree = min(degree, len(pts) - 1)
    periodic = bool(params.get("periodic", False))
    nc = RG.NurbsCurve.Create(periodic, degree, pts)
    if nc is None:
        raise RuntimeError("NurbsCurve.Create returned None.")

    weights = params.get("weights")
    if weights is not None:
        if len(weights) != len(pts):
            raise ValueError("'weights' length must match 'points' length.")
        for i, w in enumerate(weights):
            nc.Points.SetPoint(i, nc.Points[i].Location, float(w))

    knots = params.get("knots")
    if knots is not None:
        if len(knots) != nc.Knots.Count:
            raise ValueError(
                "'knots' length {kl} must be {ek}.".format(kl=len(knots), ek=nc.Knots.Count)
            )
        for i, k in enumerate(knots):
            nc.Knots[i] = float(k)

    if not nc.IsValid:
        raise RuntimeError("Constructed NurbsCurve is not valid.")

    name, layer_idx = _g_attrs(params)
    obj_id = sc.doc.Objects.AddCurve(nc)
    if obj_id == System.Guid.Empty:
        raise RuntimeError("Rhino refused to add the NURBS curve.")

    _set_object_attributes(obj_id, name, layer_idx)
    _apply_color(obj_id, params.get("color"))
    sc.doc.Views.Redraw()
    return {"guid": str(obj_id), "type": "nurbs_curve", "bounding_box": _bbox(nc)}


@handler("geometry.create_interp_curve")
def geometry_create_interp_curve(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Create an interpolated curve through points.
    Params: points (list of [x,y,z]), degree (int, default 3).
    Optional: name, layer, color.
    """
    if not _RHINO_AVAILABLE:
        raise RuntimeError("Rhino is not available.")

    raw_pts = _req(params, "points")
    degree = max(1, min(int(params.get("degree", 3)), 11))

    if not isinstance(raw_pts, (list, tuple)) or len(raw_pts) < 2:
        raise ValueError("'points' must have at least 2 entries.")

    pts = []
    for i, raw in enumerate(raw_pts):
        try:
            pts.append(_pt3d(raw))
        except Exception as exc:
            raise ValueError("Invalid point at index {i}: {err}".format(i=i, err=exc))

    degree = min(degree, len(pts) - 1)
    curve = RG.Curve.CreateInterpolatedCurve(pts, degree)
    if curve is None:
        raise RuntimeError("CreateInterpolatedCurve returned None.")

    name, layer_idx = _g_attrs(params)
    obj_id = sc.doc.Objects.AddCurve(curve)
    if obj_id == System.Guid.Empty:
        raise RuntimeError("Rhino refused to add the interpolated curve.")

    _set_object_attributes(obj_id, name, layer_idx)
    _apply_color(obj_id, params.get("color"))
    sc.doc.Views.Redraw()
    return {"guid": str(obj_id), "type": "interp_curve", "bounding_box": _bbox(curve)}


@handler("geometry.create_arc")
def geometry_create_arc(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Create an arc.
    3-point mode: start, end, point_on.
    Center/angle mode: (center or plane) + radius + start_angle + end_angle (degrees).
    Optional: name, layer, color.
    """
    if not _RHINO_AVAILABLE:
        raise RuntimeError("Rhino is not available.")

    name, layer_idx = _g_attrs(params)

    if "start" in params and "end" in params and "point_on" in params:
        arc = RG.Arc(_pt3d(params["start"]), _pt3d(params["point_on"]), _pt3d(params["end"]))
        if not arc.IsValid:
            raise ValueError("3-point arc is invalid; points may be collinear.")
    else:
        radius = float(_req(params, "radius"))
        if radius <= 0.0:
            raise ValueError("'radius' must be > 0.")
        start_deg = float(_req(params, "start_angle"))
        end_deg = float(_req(params, "end_angle"))
        if "plane" in params and params["plane"] is not None:
            plane = _plane_param(params["plane"])
        elif "center" in params:
            plane = RG.Plane(_pt3d(params["center"]), RG.Vector3d.ZAxis)
        else:
            raise ValueError(
                "create_arc needs 'start'+'end'+'point_on' OR "
                "'center'/'plane'+'radius'+'start_angle'+'end_angle'."
            )
        arc = RG.Arc(plane, radius, RG.Interval(
            math.radians(start_deg), math.radians(end_deg)
        ))

    obj_id = sc.doc.Objects.AddArc(arc)
    if obj_id == System.Guid.Empty:
        raise RuntimeError("Rhino refused to add the arc.")

    _set_object_attributes(obj_id, name, layer_idx)
    _apply_color(obj_id, params.get("color"))
    sc.doc.Views.Redraw()
    return {"guid": str(obj_id), "type": "arc", "bounding_box": _bbox(RG.ArcCurve(arc))}


@handler("geometry.create_circle")
def geometry_create_circle(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Create a circle. Params: radius, and center [x,y,z] or plane.
    Optional: name, layer, color.
    """
    if not _RHINO_AVAILABLE:
        raise RuntimeError("Rhino is not available.")

    radius = float(_req(params, "radius"))
    if radius <= 0.0:
        raise ValueError("'radius' must be > 0.")

    if "plane" in params and params["plane"] is not None:
        plane = _plane_param(params["plane"])
    elif "center" in params:
        plane = RG.Plane(_pt3d(params["center"]), RG.Vector3d.ZAxis)
    else:
        raise ValueError("create_circle requires 'center' or 'plane'.")

    circle = RG.Circle(plane, radius)
    name, layer_idx = _g_attrs(params)
    obj_id = sc.doc.Objects.AddCircle(circle)
    if obj_id == System.Guid.Empty:
        raise RuntimeError("Rhino refused to add the circle.")

    _set_object_attributes(obj_id, name, layer_idx)
    _apply_color(obj_id, params.get("color"))
    sc.doc.Views.Redraw()
    nc = circle.ToNurbsCurve()
    return {"guid": str(obj_id), "type": "circle", "bounding_box": _bbox(nc) if nc else None}


@handler("geometry.create_ellipse")
def geometry_create_ellipse(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Create an ellipse. Params: rx, ry, and center [x,y,z] or plane.
    Optional: name, layer, color.
    """
    if not _RHINO_AVAILABLE:
        raise RuntimeError("Rhino is not available.")

    rx = float(_req(params, "rx"))
    ry = float(_req(params, "ry"))
    if rx <= 0.0:
        raise ValueError("'rx' must be > 0.")
    if ry <= 0.0:
        raise ValueError("'ry' must be > 0.")

    if "plane" in params and params["plane"] is not None:
        plane = _plane_param(params["plane"])
    elif "center" in params:
        plane = RG.Plane(_pt3d(params["center"]), RG.Vector3d.ZAxis)
    else:
        raise ValueError("create_ellipse requires 'center' or 'plane'.")

    ellipse = RG.Ellipse(plane, rx, ry)
    nc = ellipse.ToNurbsCurve()
    if nc is None:
        raise RuntimeError("Ellipse.ToNurbsCurve returned None.")

    name, layer_idx = _g_attrs(params)
    obj_id = sc.doc.Objects.AddCurve(nc)
    if obj_id == System.Guid.Empty:
        raise RuntimeError("Rhino refused to add the ellipse.")

    _set_object_attributes(obj_id, name, layer_idx)
    _apply_color(obj_id, params.get("color"))
    sc.doc.Views.Redraw()
    return {"guid": str(obj_id), "type": "ellipse", "bounding_box": _bbox(nc)}


@handler("geometry.create_helix")
def geometry_create_helix(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Create a helix. Params: axis_start, axis_end, start_point, pitch, turns.
    Optional: radius (float), name, layer, color.
    """
    if not _RHINO_AVAILABLE:
        raise RuntimeError("Rhino is not available.")

    axis_start = _pt3d(_req(params, "axis_start"))
    axis_end = _pt3d(_req(params, "axis_end"))
    start_point = _pt3d(_req(params, "start_point"))
    pitch = float(_req(params, "pitch"))
    turns = float(_req(params, "turns"))

    if pitch <= 0.0:
        raise ValueError("'pitch' must be > 0.")
    if turns <= 0.0:
        raise ValueError("'turns' must be > 0.")

    axis_dir = RG.Vector3d(
        axis_end.X - axis_start.X,
        axis_end.Y - axis_start.Y,
        axis_end.Z - axis_start.Z,
    )
    if axis_dir.IsZero:
        raise ValueError("'axis_start' and 'axis_end' must differ.")

    if "radius" in params and params["radius"] is not None:
        r0 = float(params["radius"])
    else:
        dx = start_point.X - axis_start.X
        dy = start_point.Y - axis_start.Y
        dz = start_point.Z - axis_start.Z
        r0 = (dx * dx + dy * dy + dz * dz) ** 0.5

    if r0 <= 0.0:
        raise ValueError("Helix radius must be > 0.")

    nc = RG.NurbsCurve.CreateSpiral(axis_start, axis_dir, start_point, pitch, turns, r0, r0)
    if nc is None or not nc.IsValid:
        raise RuntimeError("NurbsCurve.CreateSpiral returned None or invalid curve.")

    name, layer_idx = _g_attrs(params)
    obj_id = sc.doc.Objects.AddCurve(nc)
    if obj_id == System.Guid.Empty:
        raise RuntimeError("Rhino refused to add the helix.")

    _set_object_attributes(obj_id, name, layer_idx)
    _apply_color(obj_id, params.get("color"))
    sc.doc.Views.Redraw()
    return {"guid": str(obj_id), "type": "helix", "bounding_box": _bbox(nc)}


# ---------------------------------------------------------------------------
# Surfaces
# ---------------------------------------------------------------------------

@handler("geometry.create_nurbs_surface")
def geometry_create_nurbs_surface(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Create a NURBS surface from a control point grid.

    Params: degree_u, degree_v (int), count_u, count_v (int),
            points (flat list or nested grid of [x,y,z], row-major U outer V inner).
    Optional: weights (flat list float), name, layer, color.
    """
    if not _RHINO_AVAILABLE:
        raise RuntimeError("Rhino is not available.")

    degree_u = int(_req(params, "degree_u"))
    degree_v = int(_req(params, "degree_v"))
    count_u = int(_req(params, "count_u"))
    count_v = int(_req(params, "count_v"))
    raw_pts = _req(params, "points")

    for label, val, count in (
        ("degree_u", degree_u, count_u),
        ("degree_v", degree_v, count_v),
    ):
        if val < 1 or val > 11:
            raise ValueError("'{l}' must be 1-11, got {v}.".format(l=label, v=val))

    if count_u < degree_u + 1:
        raise ValueError("count_u ({c}) must be >= degree_u+1 ({d}).".format(
            c=count_u, d=degree_u + 1))
    if count_v < degree_v + 1:
        raise ValueError("count_v ({c}) must be >= degree_v+1 ({d}).".format(
            c=count_v, d=degree_v + 1))

    # Flatten nested grid if needed.
    if (isinstance(raw_pts, (list, tuple)) and len(raw_pts) > 0
            and isinstance(raw_pts[0], (list, tuple))
            and len(raw_pts[0]) > 0
            and isinstance(raw_pts[0][0], (list, tuple, dict))):
        flat_pts = [cell for row in raw_pts for cell in row]
    else:
        flat_pts = list(raw_pts)

    expected = count_u * count_v
    if len(flat_pts) != expected:
        raise ValueError(
            "Expected {e} points for {cu}x{cv} surface, got {g}.".format(
                e=expected, cu=count_u, cv=count_v, g=len(flat_pts)
            )
        )

    weights = params.get("weights")
    if weights is not None and len(weights) != expected:
        raise ValueError("'weights' length must equal count_u * count_v = {e}.".format(e=expected))

    is_rational = weights is not None
    ns = RG.NurbsSurface.Create(3, is_rational, degree_u + 1, degree_v + 1, count_u, count_v)
    if ns is None:
        raise RuntimeError("NurbsSurface.Create returned None.")

    for i in range(count_u):
        for j in range(count_v):
            idx = i * count_v + j
            pt = _pt3d(flat_pts[idx])
            w = float(weights[idx]) if weights is not None else 1.0
            try:
                ns.Points.SetControlPoint(i, j, RG.ControlPoint(pt, w))
            except Exception as exc:
                raise ValueError(
                    "Cannot set control point ({i},{j}): {err}".format(i=i, j=j, err=exc)
                )

    # Uniform knots.
    for knots_obj in (ns.KnotsU, ns.KnotsV):
        try:
            knots_obj.CreateUniformKnots(1.0)
        except Exception:
            for ki in range(knots_obj.Count):
                try:
                    knots_obj[ki] = float(ki)
                except Exception:
                    pass

    if not ns.IsValid:
        raise RuntimeError("Constructed NurbsSurface is not valid.")

    name, layer_idx = _g_attrs(params)
    obj_id = sc.doc.Objects.AddSurface(ns)
    if obj_id == System.Guid.Empty:
        raise RuntimeError("Rhino refused to add the NURBS surface.")

    _set_object_attributes(obj_id, name, layer_idx)
    _apply_color(obj_id, params.get("color"))
    sc.doc.Views.Redraw()
    return {"guid": str(obj_id), "type": "nurbs_surface", "bounding_box": _bbox(ns)}


@handler("geometry.create_plane_surface")
def geometry_create_plane_surface(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Create a rectangular planar surface.
    Params: width, height (float), and either plane dict or origin [x,y,z].
    Optional: name, layer, color.
    """
    if not _RHINO_AVAILABLE:
        raise RuntimeError("Rhino is not available.")

    width = float(_req(params, "width"))
    height = float(_req(params, "height"))
    if width <= 0.0:
        raise ValueError("'width' must be > 0.")
    if height <= 0.0:
        raise ValueError("'height' must be > 0.")

    if "plane" in params and params["plane"] is not None:
        plane = _plane_param(params["plane"])
    elif "origin" in params:
        plane = RG.Plane(_pt3d(params["origin"]), RG.Vector3d.ZAxis)
    else:
        raise ValueError("create_plane_surface requires 'plane' or 'origin'.")

    ps = RG.PlaneSurface(plane, RG.Interval(0.0, width), RG.Interval(0.0, height))
    if ps is None or not ps.IsValid:
        raise RuntimeError("PlaneSurface constructor produced an invalid surface.")

    name, layer_idx = _g_attrs(params)
    obj_id = sc.doc.Objects.AddSurface(ps)
    if obj_id == System.Guid.Empty:
        raise RuntimeError("Rhino refused to add the plane surface.")

    _set_object_attributes(obj_id, name, layer_idx)
    _apply_color(obj_id, params.get("color"))
    sc.doc.Views.Redraw()
    return {"guid": str(obj_id), "type": "plane_surface", "bounding_box": _bbox(ps)}


@handler("geometry.create_surface_from_points")
def geometry_create_surface_from_points(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Create a surface from 3 or 4 corner points.
    Params: points (list of 3 or 4 [x,y,z]).
    Optional: name, layer, color.
    """
    if not _RHINO_AVAILABLE:
        raise RuntimeError("Rhino is not available.")

    raw_pts = _req(params, "points")
    if not isinstance(raw_pts, (list, tuple)) or len(raw_pts) not in (3, 4):
        raise ValueError("'points' must be a list of exactly 3 or 4 [x,y,z] entries.")

    pts = []
    for i, raw in enumerate(raw_pts):
        try:
            pts.append(_pt3d(raw))
        except Exception as exc:
            raise ValueError("Invalid point at index {i}: {err}".format(i=i, err=exc))

    if len(pts) == 3:
        brep = RG.Brep.CreateFromCornerPoints(pts[0], pts[1], pts[2], pts[2], 1e-6)
    else:
        brep = RG.Brep.CreateFromCornerPoints(pts[0], pts[1], pts[2], pts[3], 1e-6)

    if brep is None:
        raise RuntimeError("Brep.CreateFromCornerPoints returned None.")

    name, layer_idx = _g_attrs(params)
    obj_id = sc.doc.Objects.AddBrep(brep)
    if obj_id == System.Guid.Empty:
        raise RuntimeError("Rhino refused to add the surface.")

    _set_object_attributes(obj_id, name, layer_idx)
    _apply_color(obj_id, params.get("color"))
    sc.doc.Views.Redraw()
    return {"guid": str(obj_id), "type": "surface", "bounding_box": _bbox(brep)}


# ---------------------------------------------------------------------------
# Solids
# ---------------------------------------------------------------------------

@handler("geometry.create_box")
def geometry_create_box(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Create a box.

    Modes:
      corner+dims: corner [x,y,z], width, height, depth.
      plane+dims:  plane dict, width, height, depth.
      8 corners:   corners (list of 8 [x,y,z]).
    Optional: name, layer, color.
    """
    if not _RHINO_AVAILABLE:
        raise RuntimeError("Rhino is not available.")

    name, layer_idx = _g_attrs(params)

    if "corners" in params:
        raw_c = params["corners"]
        if not isinstance(raw_c, (list, tuple)) or len(raw_c) != 8:
            raise ValueError("'corners' must be a list of exactly 8 [x,y,z] points.")
        corners = []
        for i, raw in enumerate(raw_c):
            try:
                corners.append(_pt3d(raw))
            except Exception as exc:
                raise ValueError("Invalid corner at index {i}: {err}".format(i=i, err=exc))
        box_geo = RG.Box(RG.Plane.WorldXY, corners)
        brep = RG.Brep.CreateFromBox(box_geo)
        if brep is None:
            raise RuntimeError("Brep.CreateFromBox returned None.")
        obj_id = sc.doc.Objects.AddBrep(brep)
        if obj_id == System.Guid.Empty:
            raise RuntimeError("Rhino refused to add the box.")
        _set_object_attributes(obj_id, name, layer_idx)
        _apply_color(obj_id, params.get("color"))
        sc.doc.Views.Redraw()
        return {"guid": str(obj_id), "type": "box", "bounding_box": _bbox(brep)}

    width = float(_req(params, "width"))
    height = float(_req(params, "height"))
    depth = float(_req(params, "depth"))
    if width <= 0.0 or height <= 0.0 or depth <= 0.0:
        raise ValueError("width, height, and depth must all be > 0.")

    if "plane" in params and params["plane"] is not None:
        plane = _plane_param(params["plane"])
    else:
        corner = _pt3d(_req(params, "corner"))
        plane = RG.Plane(corner, RG.Vector3d.XAxis, RG.Vector3d.YAxis)

    box_geo = RG.Box(plane, RG.Interval(0.0, width), RG.Interval(0.0, depth), RG.Interval(0.0, height))
    brep = box_geo.ToBrep()
    if brep is None:
        raise RuntimeError("Box.ToBrep returned None.")

    obj_id = sc.doc.Objects.AddBrep(brep)
    if obj_id == System.Guid.Empty:
        raise RuntimeError("Rhino refused to add the box.")

    _set_object_attributes(obj_id, name, layer_idx)
    _apply_color(obj_id, params.get("color"))
    sc.doc.Views.Redraw()
    return {"guid": str(obj_id), "type": "box", "bounding_box": _bbox(brep)}


@handler("geometry.create_sphere")
def geometry_create_sphere(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Create a sphere. Params: center [x,y,z], radius.
    Optional: name, layer, color.
    """
    if not _RHINO_AVAILABLE:
        raise RuntimeError("Rhino is not available.")

    center = _pt3d(_req(params, "center"))
    radius = float(_req(params, "radius"))
    if radius <= 0.0:
        raise ValueError("'radius' must be > 0.")

    sphere = RG.Sphere(center, radius)
    brep = sphere.ToBrep()
    if brep is None:
        raise RuntimeError("Sphere.ToBrep returned None.")

    name, layer_idx = _g_attrs(params)
    obj_id = sc.doc.Objects.AddBrep(brep)
    if obj_id == System.Guid.Empty:
        raise RuntimeError("Rhino refused to add the sphere.")

    _set_object_attributes(obj_id, name, layer_idx)
    _apply_color(obj_id, params.get("color"))
    sc.doc.Views.Redraw()
    return {"guid": str(obj_id), "type": "sphere", "bounding_box": _bbox(brep)}


@handler("geometry.create_cylinder")
def geometry_create_cylinder(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Create a cylinder. Params: height, radius, and base_center [x,y,z] or base_plane.
    Optional: cap (bool, default True), name, layer, color.
    """
    if not _RHINO_AVAILABLE:
        raise RuntimeError("Rhino is not available.")

    height = float(_req(params, "height"))
    radius = float(_req(params, "radius"))
    cap = bool(params.get("cap", True))
    if height <= 0.0:
        raise ValueError("'height' must be > 0.")
    if radius <= 0.0:
        raise ValueError("'radius' must be > 0.")

    if "base_plane" in params and params["base_plane"] is not None:
        base_plane = _plane_param(params["base_plane"])
    elif "base_center" in params:
        base_plane = RG.Plane(_pt3d(params["base_center"]), RG.Vector3d.ZAxis)
    else:
        raise ValueError("create_cylinder requires 'base_center' or 'base_plane'.")

    cylinder = RG.Cylinder(RG.Circle(base_plane, radius), height)
    brep = cylinder.ToBrep(cap, cap)
    if brep is None:
        raise RuntimeError("Cylinder.ToBrep returned None.")

    name, layer_idx = _g_attrs(params)
    obj_id = sc.doc.Objects.AddBrep(brep)
    if obj_id == System.Guid.Empty:
        raise RuntimeError("Rhino refused to add the cylinder.")

    _set_object_attributes(obj_id, name, layer_idx)
    _apply_color(obj_id, params.get("color"))
    sc.doc.Views.Redraw()
    return {"guid": str(obj_id), "type": "cylinder", "bounding_box": _bbox(brep)}


@handler("geometry.create_cone")
def geometry_create_cone(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Create a cone. Params: height, radius, and base_center [x,y,z] or base_plane.
    Optional: cap (bool, default True), name, layer, color.
    """
    if not _RHINO_AVAILABLE:
        raise RuntimeError("Rhino is not available.")

    height = float(_req(params, "height"))
    radius = float(_req(params, "radius"))
    cap = bool(params.get("cap", True))
    if height <= 0.0:
        raise ValueError("'height' must be > 0.")
    if radius <= 0.0:
        raise ValueError("'radius' must be > 0.")

    if "base_plane" in params and params["base_plane"] is not None:
        base_plane = _plane_param(params["base_plane"])
    elif "base_center" in params:
        base_plane = RG.Plane(_pt3d(params["base_center"]), RG.Vector3d.ZAxis)
    else:
        raise ValueError("create_cone requires 'base_center' or 'base_plane'.")

    cone = RG.Cone(base_plane, height, radius)
    brep = cone.ToBrep(cap)
    if brep is None:
        raise RuntimeError("Cone.ToBrep returned None.")

    name, layer_idx = _g_attrs(params)
    obj_id = sc.doc.Objects.AddBrep(brep)
    if obj_id == System.Guid.Empty:
        raise RuntimeError("Rhino refused to add the cone.")

    _set_object_attributes(obj_id, name, layer_idx)
    _apply_color(obj_id, params.get("color"))
    sc.doc.Views.Redraw()
    return {"guid": str(obj_id), "type": "cone", "bounding_box": _bbox(brep)}


@handler("geometry.create_torus")
def geometry_create_torus(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Create a torus. Params: major_radius, minor_radius, and base_center [x,y,z] or base_plane.
    Optional: name, layer, color.
    """
    if not _RHINO_AVAILABLE:
        raise RuntimeError("Rhino is not available.")

    major = float(_req(params, "major_radius"))
    minor = float(_req(params, "minor_radius"))
    if major <= 0.0:
        raise ValueError("'major_radius' must be > 0.")
    if minor <= 0.0:
        raise ValueError("'minor_radius' must be > 0.")
    if minor >= major:
        raise ValueError("'minor_radius' must be less than 'major_radius'.")

    if "base_plane" in params and params["base_plane"] is not None:
        base_plane = _plane_param(params["base_plane"])
    elif "base_center" in params:
        base_plane = RG.Plane(_pt3d(params["base_center"]), RG.Vector3d.ZAxis)
    else:
        raise ValueError("create_torus requires 'base_center' or 'base_plane'.")

    torus = RG.Torus(base_plane, major, minor)
    brep = torus.ToBrep()
    if brep is None:
        raise RuntimeError("Torus.ToBrep returned None.")

    name, layer_idx = _g_attrs(params)
    obj_id = sc.doc.Objects.AddBrep(brep)
    if obj_id == System.Guid.Empty:
        raise RuntimeError("Rhino refused to add the torus.")

    _set_object_attributes(obj_id, name, layer_idx)
    _apply_color(obj_id, params.get("color"))
    sc.doc.Views.Redraw()
    return {"guid": str(obj_id), "type": "torus", "bounding_box": _bbox(brep)}


@handler("geometry.create_pipe")
def geometry_create_pipe(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Create a pipe along a rail curve.

    Params: curve_id (str GUID), radii (list of float).
    Optional: parameters (list float, curve params per radius),
              cap (int: 0=none, 1=flat, 2=round, default 1),
              name, layer, color.
    """
    if not _RHINO_AVAILABLE:
        raise RuntimeError("Rhino is not available.")

    curve_id = str(_req(params, "curve_id"))
    radii_raw = _req(params, "radii")

    if not isinstance(radii_raw, (list, tuple)) or len(radii_raw) == 0:
        raise ValueError("'radii' must be a non-empty list.")
    radii = [float(r) for r in radii_raw]
    if any(r <= 0.0 for r in radii):
        raise ValueError("All radii must be > 0.")

    cap = int(params.get("cap", 1))
    if cap not in (0, 1, 2):
        raise ValueError("'cap' must be 0, 1, or 2.")

    sys_guid = System.Guid(curve_id)
    doc_obj = sc.doc.Objects.FindId(sys_guid)
    if doc_obj is None:
        raise KeyError("Object not found in Rhino document: '{g}'".format(g=curve_id))

    crv = doc_obj.Geometry
    dom = crv.Domain

    raw_params = params.get("parameters")
    if raw_params is not None:
        if len(raw_params) != len(radii):
            raise ValueError("'parameters' length must match 'radii' length.")
        crv_params = [float(p) for p in raw_params]
    else:
        if len(radii) == 1:
            crv_params = [dom.Min]
        else:
            crv_params = [
                dom.Min + (dom.Max - dom.Min) * i / (len(radii) - 1)
                for i in range(len(radii))
            ]

    result_breps = RG.Brep.CreatePipe(
        crv,
        crv_params,
        radii,
        False,   # localBlending
        RG.PipeCapMode(cap),
        True,    # fitRail
        1e-3,    # absoluteTolerance
        1e-2,    # angleToleranceRadians
    )

    if result_breps is None or len(result_breps) == 0:
        raise RuntimeError("Brep.CreatePipe returned no objects.")

    name, layer_idx = _g_attrs(params)
    brep = result_breps[0]
    obj_id = sc.doc.Objects.AddBrep(brep)
    if obj_id == System.Guid.Empty:
        raise RuntimeError("Rhino refused to add the pipe.")

    _set_object_attributes(obj_id, name, layer_idx)
    _apply_color(obj_id, params.get("color"))

    result = {"guid": str(obj_id), "type": "pipe", "bounding_box": _bbox(brep)}
    if len(result_breps) > 1:
        extras = []
        for extra_brep in result_breps[1:]:
            extra_id = sc.doc.Objects.AddBrep(extra_brep)
            if extra_id != System.Guid.Empty:
                _set_object_attributes(extra_id, None, layer_idx)
                extras.append(str(extra_id))
        if extras:
            result["additional_guids"] = extras

    sc.doc.Views.Redraw()
    return result


@handler("geometry.create_extrusion")
def geometry_create_extrusion(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Extrude a profile curve.

    Params: profile_curve_id (str GUID), and either height (float, along Z)
            or direction [x,y,z].
    Optional: cap (bool, default True), name, layer, color.
    """
    if not _RHINO_AVAILABLE:
        raise RuntimeError("Rhino is not available.")

    curve_id = str(_req(params, "profile_curve_id"))
    cap = bool(params.get("cap", True))

    sys_guid = System.Guid(curve_id)
    doc_obj = sc.doc.Objects.FindId(sys_guid)
    if doc_obj is None:
        raise KeyError("Object not found in Rhino document: '{g}'".format(g=curve_id))

    profile_crv = doc_obj.Geometry
    if not isinstance(profile_crv, RG.Curve):
        raise ValueError("Object '{g}' is not a curve.".format(g=curve_id))

    if "direction" in params and params["direction"] is not None:
        raw_d = params["direction"]
        direction = RG.Vector3d(float(raw_d[0]), float(raw_d[1]), float(raw_d[2])) \
            if isinstance(raw_d, (list, tuple)) \
            else RG.Vector3d(float(raw_d["x"]), float(raw_d["y"]), float(raw_d["z"]))
    elif "height" in params and params["height"] is not None:
        h = float(params["height"])
        if h == 0.0:
            raise ValueError("'height' must not be zero.")
        direction = RG.Vector3d(0.0, 0.0, h)
    else:
        raise ValueError("create_extrusion requires 'height' or 'direction'.")

    if direction.IsZero:
        raise ValueError("Extrusion direction must not be zero-length.")

    extrusion = RG.Extrusion.Create(profile_crv, direction.Length, cap)

    name, layer_idx = _g_attrs(params)

    if extrusion is not None and extrusion.IsValid:
        # Rotate if direction is not pure +Z.
        z_axis = RG.Vector3d.ZAxis
        unit_dir = RG.Vector3d(direction)
        unit_dir.Unitize()
        angle = RG.Vector3d.VectorAngle(z_axis, unit_dir)
        if angle > 1e-10:
            rot_axis = RG.Vector3d.CrossProduct(z_axis, unit_dir)
            if not rot_axis.IsZero:
                rot_axis.Unitize()
                xform = RG.Transform.Rotation(angle, rot_axis, RG.Point3d.Origin)
                extrusion.Transform(xform)

        obj_id = sc.doc.Objects.AddExtrusion(extrusion)
        geom_for_bbox = extrusion  # type: Any
        obj_type = "extrusion"
    else:
        # Fallback: use Brep.CreateFromExtrusion if available, else sweep.
        brep = None
        if extrusion is not None:
            try:
                brep = extrusion.ToBrep(True)
            except Exception:
                pass
        if brep is None:
            raise RuntimeError(
                "Extrusion.Create returned None or invalid; "
                "check that the profile is a valid planar closed or open curve."
            )
        obj_id = sc.doc.Objects.AddBrep(brep)
        geom_for_bbox = brep
        obj_type = "brep"

    if obj_id == System.Guid.Empty:
        raise RuntimeError("Rhino refused to add the extrusion.")

    _set_object_attributes(obj_id, name, layer_idx)
    _apply_color(obj_id, params.get("color"))
    sc.doc.Views.Redraw()
    return {"guid": str(obj_id), "type": obj_type, "bounding_box": _bbox(geom_for_bbox)}


# ---------------------------------------------------------------------------
# Mesh / SubD
# ---------------------------------------------------------------------------

@handler("geometry.create_mesh")
def geometry_create_mesh(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Create a mesh from vertices and face index lists.

    Params: vertices (list of [x,y,z]), faces (list of [i,j,k] or [i,j,k,l]).
    Optional: vertex_normals (list of [x,y,z]), vertex_colors (list of [r,g,b[,a]]),
              name, layer, color.
    """
    if not _RHINO_AVAILABLE:
        raise RuntimeError("Rhino is not available.")

    raw_verts = _req(params, "vertices")
    raw_faces = _req(params, "faces")

    if not isinstance(raw_verts, (list, tuple)) or len(raw_verts) < 3:
        raise ValueError("'vertices' must be a list of at least 3 [x,y,z] entries.")
    if not isinstance(raw_faces, (list, tuple)) or len(raw_faces) < 1:
        raise ValueError("'faces' must be a non-empty list.")

    mesh = RG.Mesh()
    for i, raw in enumerate(raw_verts):
        try:
            pt = _pt3d(raw)
            mesh.Vertices.Add(pt.X, pt.Y, pt.Z)
        except Exception as exc:
            raise ValueError("Invalid vertex at index {i}: {err}".format(i=i, err=exc))

    vertex_count = len(raw_verts)
    for i, face in enumerate(raw_faces):
        if not isinstance(face, (list, tuple)) or len(face) not in (3, 4):
            raise ValueError(
                "Face {i} must have 3 or 4 vertex indices, got {f!r}.".format(i=i, f=face)
            )
        for fi, idx in enumerate(face):
            if int(idx) < 0 or int(idx) >= vertex_count:
                raise ValueError(
                    "Face {i}: index {idx} at pos {fi} is out of range (max {m}).".format(
                        i=i, idx=idx, fi=fi, m=vertex_count - 1
                    )
                )
        if len(face) == 3:
            mesh.Faces.AddFace(int(face[0]), int(face[1]), int(face[2]))
        else:
            mesh.Faces.AddFace(int(face[0]), int(face[1]), int(face[2]), int(face[3]))

    vertex_normals = params.get("vertex_normals")
    if vertex_normals is not None:
        if len(vertex_normals) != vertex_count:
            raise ValueError("'vertex_normals' length must match 'vertices' length.")
        for i, raw_n in enumerate(vertex_normals):
            try:
                v = _pt3d(raw_n)
                mesh.Normals.Add(float(v.X), float(v.Y), float(v.Z))
            except Exception as exc:
                raise ValueError("Invalid normal at index {i}: {err}".format(i=i, err=exc))
    else:
        mesh.Normals.ComputeNormals()

    vertex_colors = params.get("vertex_colors")
    if vertex_colors is not None:
        if len(vertex_colors) != vertex_count:
            raise ValueError("'vertex_colors' length must match 'vertices' length.")
        for i, raw_c in enumerate(vertex_colors):
            if not isinstance(raw_c, (list, tuple)) or len(raw_c) < 3:
                raise ValueError(
                    "vertex_color at index {i} must be [r,g,b] or [r,g,b,a].".format(i=i)
                )
            a = int(raw_c[3]) if len(raw_c) >= 4 else 255
            try:
                c = System.Drawing.Color.FromArgb(a, int(raw_c[0]), int(raw_c[1]), int(raw_c[2]))
                mesh.VertexColors.Add(c)
            except Exception as exc:
                raise ValueError("Invalid vertex color at index {i}: {err}".format(i=i, err=exc))

    mesh.Compact()
    if not mesh.IsValid:
        raise RuntimeError("Constructed Mesh is not valid -- check faces and vertices.")

    name, layer_idx = _g_attrs(params)
    obj_id = sc.doc.Objects.AddMesh(mesh)
    if obj_id == System.Guid.Empty:
        raise RuntimeError("Rhino refused to add the mesh.")

    _set_object_attributes(obj_id, name, layer_idx)
    _apply_color(obj_id, params.get("color"))
    sc.doc.Views.Redraw()
    return {
        "guid": str(obj_id),
        "type": "mesh",
        "vertex_count": mesh.Vertices.Count,
        "face_count": mesh.Faces.Count,
        "bounding_box": _bbox(mesh),
    }


@handler("geometry.create_subd")
def geometry_create_subd(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Create a SubD object.

    From existing mesh: from_mesh_id (str GUID).
    From scratch: vertices (list of [x,y,z]) + faces (list of [i,j,k] or [i,j,k,l]).
    Optional: name, layer, color.
    """
    if not _RHINO_AVAILABLE:
        raise RuntimeError("Rhino is not available.")

    name, layer_idx = _g_attrs(params)

    if "from_mesh_id" in params and params["from_mesh_id"] is not None:
        mesh_id = str(params["from_mesh_id"])
        sys_guid = System.Guid(mesh_id)
        source_obj = sc.doc.Objects.FindId(sys_guid)
        if source_obj is None:
            raise KeyError("Object not found in Rhino document: '{g}'".format(g=mesh_id))
        source_mesh = source_obj.Geometry
        if not isinstance(source_mesh, RG.Mesh):
            raise ValueError("Object '{g}' is not a mesh.".format(g=mesh_id))
        subd = RG.SubD.CreateFromMesh(source_mesh, None)
    elif "vertices" in params and "faces" in params:
        raw_verts = params["vertices"]
        raw_faces = params["faces"]

        if not isinstance(raw_verts, (list, tuple)) or len(raw_verts) < 3:
            raise ValueError("'vertices' must have at least 3 entries.")

        temp = RG.Mesh()
        for i, raw in enumerate(raw_verts):
            try:
                pt = _pt3d(raw)
                temp.Vertices.Add(pt.X, pt.Y, pt.Z)
            except Exception as exc:
                raise ValueError("Invalid vertex at index {i}: {err}".format(i=i, err=exc))

        vc = len(raw_verts)
        for i, face in enumerate(raw_faces):
            if not isinstance(face, (list, tuple)) or len(face) not in (3, 4):
                raise ValueError("Face {i} must have 3 or 4 indices.".format(i=i))
            for idx in face:
                if int(idx) < 0 or int(idx) >= vc:
                    raise ValueError(
                        "Face {i}: index {idx} out of range.".format(i=i, idx=idx)
                    )
            if len(face) == 3:
                temp.Faces.AddFace(int(face[0]), int(face[1]), int(face[2]))
            else:
                temp.Faces.AddFace(int(face[0]), int(face[1]), int(face[2]), int(face[3]))

        temp.Normals.ComputeNormals()
        temp.Compact()
        subd = RG.SubD.CreateFromMesh(temp, None)
    else:
        raise ValueError("create_subd requires 'from_mesh_id' OR 'vertices'+'faces'.")

    if subd is None or not subd.IsValid:
        raise RuntimeError("SubD.CreateFromMesh returned None or invalid SubD.")

    obj_id = sc.doc.Objects.AddSubD(subd)
    if obj_id == System.Guid.Empty:
        raise RuntimeError("Rhino refused to add the SubD.")

    _set_object_attributes(obj_id, name, layer_idx)
    _apply_color(obj_id, params.get("color"))
    sc.doc.Views.Redraw()
    return {"guid": str(obj_id), "type": "subd", "bounding_box": _bbox(subd)}


# ---------------------------------------------------------------------------
# Annotations
# ---------------------------------------------------------------------------

@handler("geometry.create_text")
def geometry_create_text(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Create a text annotation. Params: text (str), and point/position [x,y,z] or plane.
    Optional: height (float), font (str), bold (bool), italic (bool), name, layer, color.
    """
    if not _RHINO_AVAILABLE:
        raise RuntimeError("Rhino is not available.")

    text_str = str(_req(params, "text"))
    if not text_str:
        raise ValueError("'text' must be non-empty.")

    height = float(params.get("height", 1.0))
    if height <= 0.0:
        raise ValueError("'height' must be > 0.")

    if "plane" in params and params["plane"] is not None:
        plane = _plane_param(params["plane"])
    elif "point" in params:
        plane = RG.Plane(_pt3d(params["point"]), RG.Vector3d.ZAxis)
    elif "position" in params:
        plane = RG.Plane(_pt3d(params["position"]), RG.Vector3d.ZAxis)
    else:
        raise ValueError("create_text requires 'point', 'position', or 'plane'.")

    name, layer_idx = _g_attrs(params)

    try:
        text_entity = RG.TextEntity.Create(
            text_str, plane, sc.doc.DimStyles.Current, False, 0.0, 0.0
        )
        if text_entity is None:
            raise RuntimeError("TextEntity.Create returned None.")
        text_entity.TextHeight = height
        obj_id = sc.doc.Objects.Add(text_entity)
    except Exception as exc:
        raise RuntimeError("Failed to create text: {err}".format(err=exc))

    if obj_id == System.Guid.Empty:
        raise RuntimeError("Rhino refused to add the text object.")

    _set_object_attributes(obj_id, name, layer_idx)
    _apply_color(obj_id, params.get("color"))
    sc.doc.Views.Redraw()
    return {"guid": str(obj_id), "type": "text", "bounding_box": None}


@handler("geometry.create_text_dot")
def geometry_create_text_dot(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Create a text dot annotation.
    Params: text (str), point [x,y,z].
    Optional: name, layer, color.
    """
    if not _RHINO_AVAILABLE:
        raise RuntimeError("Rhino is not available.")

    text_str = str(_req(params, "text"))
    pt = _pt3d(_req(params, "point"))

    dot = RG.TextDot(text_str, pt)
    name, layer_idx = _g_attrs(params)
    obj_id = sc.doc.Objects.AddTextDot(dot)
    if obj_id == System.Guid.Empty:
        raise RuntimeError("Rhino refused to add the text dot.")

    _set_object_attributes(obj_id, name, layer_idx)
    _apply_color(obj_id, params.get("color"))
    sc.doc.Views.Redraw()
    return {"guid": str(obj_id), "type": "text_dot", "bounding_box": None}


@handler("geometry.create_dimension")
def geometry_create_dimension(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Create a dimension annotation.

    Params: type (str: "linear","aligned","angular","radial","diameter"),
            points (list of [x,y,z]).

    linear/aligned: points = [ref1, ref2, dim_line_location] (3 points).
    angular:        points = [center, ext1, ext2, arc_location] (4 points).
    radial/diameter: points = [center, point_on_circle] (2 points).
    Optional: name, layer, color.
    """
    if not _RHINO_AVAILABLE:
        raise RuntimeError("Rhino is not available.")

    dim_type = str(_req(params, "type")).lower()
    raw_pts = _req(params, "points")

    valid_types = ("linear", "aligned", "angular", "radial", "diameter")
    if dim_type not in valid_types:
        raise ValueError(
            "'type' must be one of {vt}, got '{dt}'.".format(vt=valid_types, dt=dim_type)
        )
    if not isinstance(raw_pts, (list, tuple)):
        raise ValueError("'points' must be a list.")

    name, layer_idx = _g_attrs(params)

    dim_style = sc.doc.DimStyles.Current
    obj_id = System.Guid.Empty

    if dim_type in ("linear", "aligned"):
        if len(raw_pts) < 3:
            raise ValueError(
                "'{t}' dimension needs 3 points [ref1, ref2, dim_location].".format(t=dim_type)
            )
        pt0 = _pt3d(raw_pts[0])
        pt1 = _pt3d(raw_pts[1])
        pt2 = _pt3d(raw_pts[2])
        plane = RG.Plane(pt0, RG.Vector3d.ZAxis)

        if dim_type == "linear":
            dim = RG.LinearDimension.Create(
                plane, pt0, pt1, pt2, dim_style.Id
            )
        else:
            dim = RG.AlignedDimension.Create(pt0, pt1, pt2, dim_style.Id)

        if dim is not None:
            obj_id = sc.doc.Objects.Add(dim)

    elif dim_type == "angular":
        if len(raw_pts) < 4:
            raise ValueError(
                "'angular' dimension needs 4 points [center, ext1, ext2, arc_loc]."
            )
        center = _pt3d(raw_pts[0])
        ext1 = _pt3d(raw_pts[1])
        ext2 = _pt3d(raw_pts[2])
        arc_loc = _pt3d(raw_pts[3])
        dim = RG.AngularDimension.Create(center, ext1, ext2, arc_loc, dim_style.Id)
        if dim is not None:
            obj_id = sc.doc.Objects.Add(dim)

    elif dim_type in ("radial", "diameter"):
        if len(raw_pts) < 2:
            raise ValueError(
                "'{t}' dimension needs 2 points [center, point_on_circle].".format(t=dim_type)
            )
        center = _pt3d(raw_pts[0])
        pt_on = _pt3d(raw_pts[1])
        if dim_type == "radial":
            dim = RG.RadialDimension.Create(center, pt_on, pt_on, dim_style.Id)
        else:
            dim = RG.RadialDimension.Create(center, pt_on, pt_on, dim_style.Id)
        if dim is not None:
            obj_id = sc.doc.Objects.Add(dim)

    if obj_id == System.Guid.Empty:
        raise RuntimeError(
            "Dimension creation failed for type '{t}' -- check input points.".format(t=dim_type)
        )

    _set_object_attributes(obj_id, name, layer_idx)
    _apply_color(obj_id, params.get("color"))
    sc.doc.Views.Redraw()
    return {"guid": str(obj_id), "type": "dimension", "bounding_box": None}


@handler("geometry.create_hatch")
def geometry_create_hatch(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Create a hatch fill from closed boundary curves.

    Params: curve_ids (list of str GUIDs).
    Optional: pattern (str, default "Solid"), scale (float, default 1.0),
              rotation (float degrees, default 0.0), name, layer, color.
    """
    if not _RHINO_AVAILABLE:
        raise RuntimeError("Rhino is not available.")

    raw_ids = _req(params, "curve_ids")
    if not isinstance(raw_ids, (list, tuple)) or len(raw_ids) == 0:
        raise ValueError("'curve_ids' must be a non-empty list of GUID strings.")

    pattern_name = str(params.get("pattern", "Solid"))
    scale = float(params.get("scale", 1.0))
    rotation_deg = float(params.get("rotation", 0.0))

    if scale <= 0.0:
        raise ValueError("'scale' must be > 0.")

    rotation_rad = math.radians(rotation_deg)

    # Find the hatch pattern index.
    pattern_idx = sc.doc.HatchPatterns.Find(pattern_name, True)
    if pattern_idx < 0:
        raise ValueError(
            "Hatch pattern '{p}' not found in the document. "
            "Load the pattern first or use a built-in name like 'Solid'.".format(p=pattern_name)
        )

    # Collect boundary curves from the document.
    curves = []
    for cid in raw_ids:
        sys_guid = System.Guid(str(cid))
        doc_obj = sc.doc.Objects.FindId(sys_guid)
        if doc_obj is None:
            raise KeyError("Object not found in Rhino document: '{g}'".format(g=cid))
        crv = doc_obj.Geometry
        if not isinstance(crv, RG.Curve):
            raise ValueError("Object '{g}' is not a curve.".format(g=cid))
        curves.append(crv)

    hatches = RG.Hatch.Create(curves, pattern_idx, rotation_rad, scale, 1e-3)

    if hatches is None or len(hatches) == 0:
        raise RuntimeError(
            "Hatch.Create returned no hatches -- verify that boundary curves are "
            "closed and planar, and that pattern '{p}' exists.".format(p=pattern_name)
        )

    name, layer_idx = _g_attrs(params)
    first_id = System.Guid.Empty
    extra_guids = []

    for i, hatch in enumerate(hatches):
        oid = sc.doc.Objects.AddHatch(hatch)
        if oid == System.Guid.Empty:
            continue
        _set_object_attributes(oid, name if i == 0 else None, layer_idx)
        _apply_color(oid, params.get("color"))
        if i == 0:
            first_id = oid
        else:
            extra_guids.append(str(oid))

    if first_id == System.Guid.Empty:
        raise RuntimeError("Rhino refused to add any hatch objects.")

    sc.doc.Views.Redraw()
    result = {"guid": str(first_id), "type": "hatch", "bounding_box": None}  # type: Dict[str, Any]
    if extra_guids:
        result["additional_guids"] = extra_guids
    return result
