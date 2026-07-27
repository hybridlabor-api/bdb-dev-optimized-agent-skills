# -*- coding: utf-8 -*-
"""
rhino_plugin/utils/geometry_serializer.py
==========================================
Convert RhinoCommon geometry objects to plain JSON-serialisable Python dicts.

Design notes
------------
* Runs **inside Rhino 3D** under Python 3.9 -- no external deps, no
  ``match``/``case``, no ``X | Y`` union syntax.
* Every property access is wrapped in try/except because many geometry types
  do not expose all properties (e.g. a LineCurve has no NURBS knots, a
  PlaneSurface has no NURBS weights).  We always emit *something* rather than
  crashing the whole serialisation.
* All public functions are pure (no side effects on the Rhino document) and
  return JSON-serialisable dicts or lists.

Imports that only resolve inside Rhino:
    import Rhino
    import scriptcontext
    import rhinoscriptsyntax as rs
    import System
"""

# These imports are only available inside the Rhino Python environment.
# The try/except lets linters and unit-test runners import the module without
# exploding; at runtime inside Rhino they will always succeed.
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
# Primitive serialisers
# ---------------------------------------------------------------------------

def serialize_point3d(point):
    """Serialise a ``Rhino.Geometry.Point3d`` to ``[x, y, z]``."""
    try:
        return [float(point.X), float(point.Y), float(point.Z)]
    except Exception:
        return [0.0, 0.0, 0.0]


def serialize_vector3d(vec):
    """Serialise a ``Rhino.Geometry.Vector3d`` to ``[x, y, z]``."""
    try:
        return [float(vec.X), float(vec.Y), float(vec.Z)]
    except Exception:
        return [0.0, 0.0, 0.0]


def serialize_plane(plane):
    """
    Serialise a ``Rhino.Geometry.Plane`` to::

        {
            "origin":  [x, y, z],
            "x_axis":  [x, y, z],
            "y_axis":  [x, y, z],
            "normal":  [x, y, z],
        }
    """
    result = {
        "origin": [0.0, 0.0, 0.0],
        "x_axis": [1.0, 0.0, 0.0],
        "y_axis": [0.0, 1.0, 0.0],
        "normal": [0.0, 0.0, 1.0],
    }
    try:
        result["origin"] = serialize_point3d(plane.Origin)
    except Exception:
        pass
    try:
        result["x_axis"] = serialize_vector3d(plane.XAxis)
    except Exception:
        pass
    try:
        result["y_axis"] = serialize_vector3d(plane.YAxis)
    except Exception:
        pass
    try:
        result["normal"] = serialize_vector3d(plane.Normal)
    except Exception:
        pass
    return result


def serialize_bounding_box(bbox):
    """
    Serialise a ``Rhino.Geometry.BoundingBox`` to::

        {"min": [x, y, z], "max": [x, y, z]}
    """
    result = {"min": [0.0, 0.0, 0.0], "max": [0.0, 0.0, 0.0]}
    try:
        result["min"] = serialize_point3d(bbox.Min)
    except Exception:
        pass
    try:
        result["max"] = serialize_point3d(bbox.Max)
    except Exception:
        pass
    return result


# ---------------------------------------------------------------------------
# Curve serialiser
# ---------------------------------------------------------------------------

def serialize_curve(curve):
    """
    Serialise any ``Rhino.Geometry.Curve`` subclass.

    The ``"type"`` field is one of: ``"line"``, ``"arc"``, ``"circle"``,
    ``"polyline"``, ``"nurbs"``.  NURBS curves additionally include
    ``"control_points"``, ``"weights"``, and ``"knots"``.
    """
    result = {
        "type": "curve",
        "degree": None,
        "domain": None,
        "length": None,
        "is_closed": False,
        "start_point": None,
        "end_point": None,
    }

    if not _RHINO_AVAILABLE:
        return result

    # Determine the concrete curve type.
    try:
        if isinstance(curve, RG.LineCurve):
            result["type"] = "line"
        elif isinstance(curve, RG.ArcCurve):
            # ArcCurve covers both arcs and full circles.
            try:
                arc = curve.Arc
                result["type"] = "circle" if arc.IsCircle else "arc"
                result["radius"] = float(arc.Radius)
                result["center"] = serialize_point3d(arc.Center)
            except Exception:
                result["type"] = "arc"
        elif isinstance(curve, RG.PolylineCurve):
            result["type"] = "polyline"
            try:
                result["point_count"] = int(curve.PointCount)
            except Exception:
                pass
        elif isinstance(curve, RG.NurbsCurve):
            result["type"] = "nurbs"
        else:
            # Try to cast to NURBS as a fallback for composite curve types.
            result["type"] = "nurbs"
    except Exception:
        result["type"] = "curve"

    try:
        result["degree"] = int(curve.Degree)
    except Exception:
        pass

    try:
        dom = curve.Domain
        result["domain"] = [float(dom.Min), float(dom.Max)]
    except Exception:
        pass

    try:
        result["length"] = float(curve.GetLength())
    except Exception:
        pass

    try:
        result["is_closed"] = bool(curve.IsClosed)
    except Exception:
        pass

    try:
        result["start_point"] = serialize_point3d(curve.PointAtStart)
    except Exception:
        pass

    try:
        result["end_point"] = serialize_point3d(curve.PointAtEnd)
    except Exception:
        pass

    # NURBS-specific data.
    if result["type"] == "nurbs":
        try:
            nc = curve.ToNurbsCurve()
            if nc is not None:
                control_points = []
                weights = []
                for i in range(nc.Points.Count):
                    pt = nc.Points[i]
                    try:
                        control_points.append(serialize_point3d(pt.Location))
                        weights.append(float(pt.Weight))
                    except Exception:
                        pass
                result["control_points"] = control_points
                result["weights"] = weights

                knots = []
                for i in range(nc.Knots.Count):
                    try:
                        knots.append(float(nc.Knots[i]))
                    except Exception:
                        pass
                result["knots"] = knots
        except Exception:
            pass

    return result


# ---------------------------------------------------------------------------
# Surface serialiser
# ---------------------------------------------------------------------------

def serialize_surface(surface):
    """
    Serialise any ``Rhino.Geometry.Surface`` subclass.

    NURBS surfaces additionally include ``"control_points"`` and
    ``"weights"``.
    """
    result = {
        "type": "surface",
        "degree_u": None,
        "degree_v": None,
        "domain_u": None,
        "domain_v": None,
        "is_closed_u": False,
        "is_closed_v": False,
    }

    if not _RHINO_AVAILABLE:
        return result

    try:
        if isinstance(surface, RG.NurbsSurface):
            result["type"] = "nurbs"
        elif isinstance(surface, RG.PlaneSurface):
            result["type"] = "plane"
        elif isinstance(surface, RG.RevSurface):
            result["type"] = "revolution"
        elif isinstance(surface, RG.SumSurface):
            result["type"] = "sum"
        else:
            result["type"] = "surface"
    except Exception:
        pass

    for direction, label in ((0, "u"), (1, "v")):
        try:
            result["degree_" + label] = int(surface.Degree(direction))
        except Exception:
            pass
        try:
            dom = surface.Domain(direction)
            result["domain_" + label] = [float(dom.Min), float(dom.Max)]
        except Exception:
            pass
        try:
            result["is_closed_" + label] = bool(surface.IsClosed(direction))
        except Exception:
            pass

    # NURBS-specific data.
    if result["type"] == "nurbs":
        try:
            ns = surface.ToNurbsSurface()
            if ns is not None:
                control_points = []
                weights = []
                for i in range(ns.Points.CountU):
                    row_pts = []
                    row_wts = []
                    for j in range(ns.Points.CountV):
                        try:
                            pt = ns.Points.GetControlPoint(i, j)
                            row_pts.append(serialize_point3d(pt.Location))
                            row_wts.append(float(pt.Weight))
                        except Exception:
                            pass
                    control_points.append(row_pts)
                    weights.append(row_wts)
                result["control_points"] = control_points
                result["weights"] = weights
        except Exception:
            pass

    return result


# ---------------------------------------------------------------------------
# Brep serialiser
# ---------------------------------------------------------------------------

def serialize_brep(brep):
    """
    Serialise a ``Rhino.Geometry.Brep`` to a topology + metric summary dict.
    """
    result = {
        "face_count": 0,
        "edge_count": 0,
        "vertex_count": 0,
        "is_solid": False,
        "is_valid": False,
        "volume": None,
        "area": None,
        "bounding_box": None,
    }

    if not _RHINO_AVAILABLE:
        return result

    try:
        result["face_count"] = int(brep.Faces.Count)
    except Exception:
        pass
    try:
        result["edge_count"] = int(brep.Edges.Count)
    except Exception:
        pass
    try:
        result["vertex_count"] = int(brep.Vertices.Count)
    except Exception:
        pass
    try:
        result["is_solid"] = bool(brep.IsSolid)
    except Exception:
        pass
    try:
        result["is_valid"] = bool(brep.IsValid)
    except Exception:
        pass
    try:
        if result["is_solid"]:
            vol_mp = RG.VolumeMassProperties.Compute(brep)
            if vol_mp is not None:
                result["volume"] = float(vol_mp.Volume)
    except Exception:
        pass
    try:
        amp = RG.AreaMassProperties.Compute(brep)
        if amp is not None:
            result["area"] = float(amp.Area)
    except Exception:
        pass
    try:
        result["bounding_box"] = serialize_bounding_box(brep.GetBoundingBox(True))
    except Exception:
        pass

    return result


# ---------------------------------------------------------------------------
# Mesh serialiser
# ---------------------------------------------------------------------------

def serialize_mesh(mesh):
    """
    Serialise a ``Rhino.Geometry.Mesh`` to a topology + attribute summary.
    """
    result = {
        "vertex_count": 0,
        "face_count": 0,
        "has_normals": False,
        "has_vertex_colors": False,
        "bounding_box": None,
    }

    if not _RHINO_AVAILABLE:
        return result

    try:
        result["vertex_count"] = int(mesh.Vertices.Count)
    except Exception:
        pass
    try:
        result["face_count"] = int(mesh.Faces.Count)
    except Exception:
        pass
    try:
        result["has_normals"] = int(mesh.Normals.Count) > 0
    except Exception:
        pass
    try:
        result["has_vertex_colors"] = int(mesh.VertexColors.Count) > 0
    except Exception:
        pass
    try:
        result["bounding_box"] = serialize_bounding_box(mesh.GetBoundingBox(True))
    except Exception:
        pass

    return result


# ---------------------------------------------------------------------------
# Extrusion serialiser
# ---------------------------------------------------------------------------

def serialize_extrusion(extrusion):
    """
    Serialise a ``Rhino.Geometry.Extrusion``.
    """
    result = {
        "profile_count": 0,
        "capped": False,
        "path_direction": None,
        "path_length": None,
    }

    if not _RHINO_AVAILABLE:
        return result

    try:
        result["profile_count"] = int(extrusion.ProfileCount)
    except Exception:
        pass
    try:
        result["capped"] = bool(extrusion.IsCapped)
    except Exception:
        pass
    try:
        path_start = extrusion.PathStart
        path_end = extrusion.PathEnd
        dx = path_end.X - path_start.X
        dy = path_end.Y - path_start.Y
        dz = path_end.Z - path_start.Z
        length = (dx * dx + dy * dy + dz * dz) ** 0.5
        if length > 1e-12:
            result["path_direction"] = [dx / length, dy / length, dz / length]
        else:
            result["path_direction"] = [0.0, 0.0, 1.0]
        result["path_length"] = float(length)
    except Exception:
        pass

    return result


# ---------------------------------------------------------------------------
# SubD serialiser
# ---------------------------------------------------------------------------

def serialize_subd(subd):
    """
    Serialise a ``Rhino.Geometry.SubD``.
    """
    result = {
        "vertex_count": 0,
        "face_count": 0,
        "edge_count": 0,
        "level": None,
    }

    if not _RHINO_AVAILABLE:
        return result

    try:
        result["vertex_count"] = int(subd.Vertices.Count)
    except Exception:
        pass
    try:
        result["face_count"] = int(subd.Faces.Count)
    except Exception:
        pass
    try:
        result["edge_count"] = int(subd.Edges.Count)
    except Exception:
        pass
    try:
        result["level"] = int(subd.SubdivisionCount)
    except Exception:
        pass

    return result


# ---------------------------------------------------------------------------
# Transform serialiser
# ---------------------------------------------------------------------------

def serialize_transform(transform):
    """
    Serialise a ``Rhino.Geometry.Transform`` (4x4 matrix) to a nested list::

        [[m00, m01, m02, m03],
         [m10, m11, m12, m13],
         [m20, m21, m22, m23],
         [m30, m31, m32, m33]]
    """
    matrix = []
    for row in range(4):
        row_data = []
        for col in range(4):
            try:
                row_data.append(float(transform[row, col]))
            except Exception:
                row_data.append(0.0)
        matrix.append(row_data)
    return matrix


# ---------------------------------------------------------------------------
# Generic geometry dispatcher
# ---------------------------------------------------------------------------

def serialize_any(geometry_base):
    """
    Detect the concrete type of *geometry_base* and call the appropriate
    specialised serialiser.  Falls back to a minimal ``{"type": "unknown"}``
    dict if the type is not recognised.
    """
    if not _RHINO_AVAILABLE:
        return {"type": "unknown"}

    try:
        if isinstance(geometry_base, RG.Curve):
            return serialize_curve(geometry_base)
        if isinstance(geometry_base, RG.Brep):
            return serialize_brep(geometry_base)
        if isinstance(geometry_base, RG.Mesh):
            return serialize_mesh(geometry_base)
        if isinstance(geometry_base, RG.Surface):
            return serialize_surface(geometry_base)
        if isinstance(geometry_base, RG.Extrusion):
            return serialize_extrusion(geometry_base)
        if isinstance(geometry_base, RG.SubD):
            return serialize_subd(geometry_base)
        if isinstance(geometry_base, RG.Point):
            return {"type": "point", "location": serialize_point3d(geometry_base.Location)}
        if isinstance(geometry_base, RG.PointCloud):
            return {"type": "point_cloud", "count": int(geometry_base.Count)}
        if isinstance(geometry_base, RG.Hatch):
            return {"type": "hatch"}
        if isinstance(geometry_base, RG.TextEntity):
            return {"type": "text"}
        if isinstance(geometry_base, RG.Leader):
            return {"type": "leader"}
        if isinstance(geometry_base, RG.Annotation):
            return {"type": "annotation"}
    except Exception:
        pass

    return {"type": "unknown"}


# ---------------------------------------------------------------------------
# Full Rhino object serialiser
# ---------------------------------------------------------------------------

def serialize_object(rhino_object):
    """
    Serialise a ``Rhino.DocObjects.RhinoObject`` (a document object, not raw
    geometry) to a comprehensive dict suitable for returning to an MCP tool.

    Includes:
    - ``guid`` -- object GUID as a string
    - ``type`` -- geometry type string
    - ``layer`` -- layer name
    - ``name`` -- object name (may be empty string)
    - ``color`` -- ``{"r", "g", "b", "a"}``
    - ``visible`` -- bool
    - ``locked`` -- bool
    - ``geometry`` -- geometry summary from :func:`serialize_any`
    - ``bounding_box`` -- ``{"min", "max"}``
    - ``user_text`` -- ``{key: value}`` dict of all custom user data
    """
    result = {
        "guid": None,
        "type": "unknown",
        "layer": None,
        "name": None,
        "color": {"r": 0, "g": 0, "b": 0, "a": 255},
        "visible": True,
        "locked": False,
        "geometry": None,
        "bounding_box": None,
        "user_text": {},
    }

    if not _RHINO_AVAILABLE or rhino_object is None:
        return result

    try:
        result["guid"] = str(rhino_object.Id)
    except Exception:
        pass

    try:
        geom = rhino_object.Geometry
        if geom is not None:
            result["geometry"] = serialize_any(geom)
            result["type"] = result["geometry"].get("type", "unknown")
    except Exception:
        pass

    try:
        attrs = rhino_object.Attributes
        if attrs is not None:
            try:
                layer_index = attrs.LayerIndex
                layer = sc.doc.Layers[layer_index]
                result["layer"] = str(layer.FullPath)
            except Exception:
                pass

            try:
                result["name"] = str(attrs.Name) if attrs.Name else ""
            except Exception:
                pass

            try:
                color = attrs.ObjectColor
                result["color"] = {
                    "r": int(color.R),
                    "g": int(color.G),
                    "b": int(color.B),
                    "a": int(color.A),
                }
            except Exception:
                pass

            try:
                result["visible"] = bool(attrs.Visible)
            except Exception:
                pass

            try:
                from Rhino.DocObjects import ObjectMode
                result["locked"] = (attrs.Mode == ObjectMode.Locked)
            except Exception:
                pass

            # Collect all user-text key-value pairs.
            try:
                keys = attrs.GetUserStrings()
                if keys:
                    user_text = {}
                    for key in keys:
                        try:
                            user_text[str(key)] = str(attrs.GetUserString(key))
                        except Exception:
                            pass
                    result["user_text"] = user_text
            except Exception:
                pass
    except Exception:
        pass

    try:
        bbox = rhino_object.Geometry.GetBoundingBox(True)
        result["bounding_box"] = serialize_bounding_box(bbox)
    except Exception:
        pass

    return result
