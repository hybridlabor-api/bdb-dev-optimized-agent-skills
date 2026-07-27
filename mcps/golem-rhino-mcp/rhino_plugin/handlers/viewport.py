# -*- coding: utf-8 -*-
"""
rhino_plugin/handlers/viewport.py
===================================
Viewport & Visualization handlers for GOLEM-3DMCP.

Runs INSIDE Rhino 3D with Python 3.9.  Zero external dependencies -- only the
Python stdlib plus the Rhino host environment (Rhino, rhinoscriptsyntax,
scriptcontext, System).

Registered methods
------------------
  viewport.capture          -- Capture a viewport to base64 PNG
  viewport.set_view         -- Set a standard or named view
  viewport.zoom_object      -- Zoom to bounding box of specific objects
  viewport.zoom_extents     -- Zoom to extents of all objects (one or all views)
  viewport.zoom_selected    -- Zoom to currently selected objects
  viewport.set_display_mode -- Change viewport display mode
  viewport.set_camera       -- Set camera location, target, and lens length
  viewport.create_named_view  -- Save current camera as a named view
  viewport.restore_named_view -- Restore a previously saved named view
  viewport.list_named_views   -- Return all saved named view names
  viewport.get_view_info      -- Return camera and viewport metadata

Design notes
------------
* Python 3.9 compatible -- no ``match``/``case``, no ``X | Y`` union syntax,
  no ``dict[str, ...]`` lowercase generics in runtime annotations.
* Every handler receives a single ``params`` dict from the dispatcher and
  returns a JSON-serialisable dict.
* Validation errors raise ``ValueError`` or ``TypeError``; the dispatcher
  catches these and converts them to INVALID_PARAMS responses automatically.
* Rhino API calls that return ``None`` or ``False`` are treated as failures
  and return an OPERATION_FAILED result dict (never raise).
"""

import Rhino                                          # noqa: F401 (Rhino host)
import scriptcontext as sc
import rhinoscriptsyntax as rs
import System
import System.Drawing

from rhino_plugin.dispatcher import handler
from rhino_plugin.utils.screenshot import capture_viewport_to_base64


# ---------------------------------------------------------------------------
# Standard view name constants and helpers
# ---------------------------------------------------------------------------

_STANDARD_VIEWS = {
    "top",
    "bottom",
    "left",
    "right",
    "front",
    "back",
    "perspective",
    "twopointperspective",
}

# rhinoscriptsyntax projection constants
# rs.ViewProjection() accepts an integer projection type:
#   0 = parallel, 1 = perspective, 2 = two-point perspective
_PERSPECTIVE_VIEWS = {"perspective", "twopointperspective"}


def _resolve_view(view_name):
    # type: (object) -> object
    """
    Return the RhinoView for *view_name*, or the active view if *view_name* is
    None.  Raises ``ValueError`` when the name is given but not found.
    """
    if view_name is None:
        view = sc.doc.Views.ActiveView
        if view is None:
            raise ValueError("No active Rhino view available.")
        return view

    name_lower = str(view_name).lower()
    for v in sc.doc.Views:
        if v.ActiveViewport.Name.lower() == name_lower:
            return v

    raise ValueError("View not found: '{name}'".format(name=view_name))


def _point3d(x, y, z):
    # type: (float, float, float) -> object
    return Rhino.Geometry.Point3d(float(x), float(y), float(z))


def _serialize_point3d(pt):
    # type: (object) -> dict
    return {"x": float(pt.X), "y": float(pt.Y), "z": float(pt.Z)}


def _serialize_vector3d(v):
    # type: (object) -> dict
    return {"x": float(v.X), "y": float(v.Y), "z": float(v.Z)}


# ---------------------------------------------------------------------------
# 1. capture_viewport
# ---------------------------------------------------------------------------

@handler("viewport.capture")
def capture_viewport(params):
    # type: (dict) -> dict
    """
    Capture a Rhino viewport to a base64-encoded PNG.

    Params
    ------
    width        : int, optional  -- pixel width  (default 1920)
    height       : int, optional  -- pixel height (default 1080)
    display_mode : str, optional  -- display mode for the capture
    view_name    : str, optional  -- viewport name; active view if omitted

    Returns
    -------
    dict
        image, width, height, view_name, display_mode
    """
    width = int(params.get("width", 1920))
    height = int(params.get("height", 1080))
    display_mode = params.get("display_mode", None)
    view_name = params.get("view_name", None)

    if width < 1 or width > 16384:
        raise ValueError("width must be between 1 and 16384, got {w}".format(w=width))
    if height < 1 or height > 16384:
        raise ValueError("height must be between 1 and 16384, got {h}".format(h=height))

    result = capture_viewport_to_base64(
        view_name=view_name,
        width=width,
        height=height,
        display_mode=display_mode,
    )

    # The screenshot utility returns an error dict on failure.
    if "error" in result:
        return {
            "success": False,
            "error": result["error"],
            "code": result.get("code", "OPERATION_FAILED"),
        }

    return {
        "success": True,
        "image": result["image"],
        "width": result["width"],
        "height": result["height"],
        "view_name": result["view_name"],
        "display_mode": result["display_mode"],
    }


# ---------------------------------------------------------------------------
# 2. set_view
# ---------------------------------------------------------------------------

@handler("viewport.set_view")
def set_view(params):
    # type: (dict) -> dict
    """
    Set a standard orthographic / perspective view or restore a named view.

    Params
    ------
    view_name   : str, optional -- standard view name: Top, Bottom, Left, Right,
                  Front, Back, Perspective, TwoPointPerspective
    named_view  : str, optional -- name of a saved named view to restore instead

    Exactly one of ``view_name`` or ``named_view`` should be supplied.
    If both are present, ``named_view`` takes precedence.
    """
    view_name = params.get("view_name", None)
    named_view = params.get("named_view", None)

    if named_view is not None:
        # Restore a saved named view into the active viewport.
        result = rs.RestoreNamedView(named_view)
        if not result:
            return {
                "success": False,
                "error": "RestoreNamedView failed for '{name}'.".format(name=named_view),
                "code": "OPERATION_FAILED",
            }
        sc.doc.Views.Redraw()
        return {
            "success": True,
            "restored_named_view": named_view,
        }

    if view_name is None:
        raise ValueError("Either 'view_name' or 'named_view' must be provided.")

    key = str(view_name).lower()
    if key not in _STANDARD_VIEWS:
        raise ValueError(
            "view_name '{v}' is not a recognised standard view. "
            "Choose from: Top, Bottom, Left, Right, Front, Back, "
            "Perspective, TwoPointPerspective.".format(v=view_name)
        )

    # rhinoscriptsyntax uses the view's ActiveViewport.Name as the first arg.
    # We operate on the active view and rename only the camera, not the panel.
    active_view = sc.doc.Views.ActiveView
    if active_view is None:
        raise ValueError("No active Rhino view available.")

    viewport = active_view.ActiveViewport

    # Map the requested standard view to a Rhino ViewportType / projection.
    _VIEW_INFO = {
        "top": {
            "projection": Rhino.Display.DefinedViewportProjection.Top,
            "parallel": True,
        },
        "bottom": {
            "projection": Rhino.Display.DefinedViewportProjection.Bottom,
            "parallel": True,
        },
        "left": {
            "projection": Rhino.Display.DefinedViewportProjection.Left,
            "parallel": True,
        },
        "right": {
            "projection": Rhino.Display.DefinedViewportProjection.Right,
            "parallel": True,
        },
        "front": {
            "projection": Rhino.Display.DefinedViewportProjection.Front,
            "parallel": True,
        },
        "back": {
            "projection": Rhino.Display.DefinedViewportProjection.Back,
            "parallel": True,
        },
        "perspective": {
            "projection": Rhino.Display.DefinedViewportProjection.Perspective,
            "parallel": False,
        },
        "twopointperspective": {
            "projection": Rhino.Display.DefinedViewportProjection.TwoPointPerspective,
            "parallel": False,
        },
    }

    info = _VIEW_INFO[key]
    viewport.SetProjection(info["projection"], None, True)
    sc.doc.Views.Redraw()

    return {
        "success": True,
        "view_set": view_name,
    }


# ---------------------------------------------------------------------------
# 3. zoom_object
# ---------------------------------------------------------------------------

@handler("viewport.zoom_object")
def zoom_object(params):
    # type: (dict) -> dict
    """
    Zoom to the combined bounding box of the given objects.

    Params
    ------
    ids : list of str -- GUIDs of objects to zoom to
    """
    ids = params.get("ids", None)
    if ids is None:
        raise ValueError("'ids' parameter is required.")
    if not isinstance(ids, list) or len(ids) == 0:
        raise ValueError("'ids' must be a non-empty list of GUID strings.")

    # Build a combined bounding box across all objects.
    combined_bbox = None
    missing = []

    for guid_str in ids:
        obj = sc.doc.Objects.FindId(System.Guid(str(guid_str)))
        if obj is None:
            missing.append(guid_str)
            continue
        bbox = obj.Geometry.GetBoundingBox(True)
        if not bbox.IsValid:
            continue
        if combined_bbox is None:
            combined_bbox = bbox
        else:
            combined_bbox.Union(bbox)

    if combined_bbox is None or not combined_bbox.IsValid:
        return {
            "success": False,
            "error": "Could not compute a valid bounding box for the supplied objects.",
            "code": "OPERATION_FAILED",
            "missing_ids": missing,
        }

    rs.ZoomBoundingBox(combined_bbox.Min, combined_bbox.Max)
    sc.doc.Views.Redraw()

    result = {
        "success": True,
        "bounding_box": {
            "min": _serialize_point3d(combined_bbox.Min),
            "max": _serialize_point3d(combined_bbox.Max),
        },
        "object_count": len(ids) - len(missing),
    }
    if missing:
        result["missing_ids"] = missing
    return result


# ---------------------------------------------------------------------------
# 4. zoom_extents
# ---------------------------------------------------------------------------

@handler("viewport.zoom_extents")
def zoom_extents(params):
    # type: (dict) -> dict
    """
    Zoom to the extents of all objects in one viewport or all viewports.

    Params
    ------
    view_name : str, optional -- target viewport; zooms all views if omitted
    """
    view_name = params.get("view_name", None)

    if view_name is None:
        # Zoom all viewports.
        rs.ZoomExtents(all=True)
        sc.doc.Views.Redraw()
        return {"success": True, "zoomed": "all_views"}

    # Validate the view exists first.
    _resolve_view(view_name)  # raises ValueError if not found
    rs.ZoomExtents(view=view_name)
    sc.doc.Views.Redraw()
    return {"success": True, "zoomed": view_name}


# ---------------------------------------------------------------------------
# 5. zoom_selected
# ---------------------------------------------------------------------------

@handler("viewport.zoom_selected")
def zoom_selected(params):
    # type: (dict) -> dict
    """
    Zoom to the currently selected objects.

    Params
    ------
    (no required params -- operates on the current selection)
    """
    rs.ZoomSelected()
    sc.doc.Views.Redraw()
    return {"success": True}


# ---------------------------------------------------------------------------
# 6. set_display_mode
# ---------------------------------------------------------------------------

_VALID_DISPLAY_MODES = {
    "wireframe", "shaded", "rendered", "ghosted",
    "xray", "technical", "artistic", "pen",
}


@handler("viewport.set_display_mode")
def set_display_mode(params):
    # type: (dict) -> dict
    """
    Change the display mode of a viewport.

    Params
    ------
    mode      : str           -- Wireframe, Shaded, Rendered, Ghosted, XRay,
                                Technical, Artistic, Pen
    view_name : str, optional -- target viewport; active view if omitted
    """
    mode = params.get("mode", None)
    if mode is None:
        raise ValueError("'mode' parameter is required.")

    view_name = params.get("view_name", None)

    mode_str = str(mode)
    if mode_str.lower() not in _VALID_DISPLAY_MODES:
        raise ValueError(
            "Unrecognised display mode '{m}'. Valid modes: "
            "Wireframe, Shaded, Rendered, Ghosted, XRay, Technical, Artistic, Pen.".format(
                m=mode_str
            )
        )

    # Resolve the target view name string for rhinoscriptsyntax.
    if view_name is not None:
        view = _resolve_view(view_name)  # raises ValueError if not found
        target_name = view.ActiveViewport.Name
    else:
        view = sc.doc.Views.ActiveView
        if view is None:
            raise ValueError("No active Rhino view available.")
        target_name = view.ActiveViewport.Name

    result = rs.ViewDisplayMode(target_name, mode_str)
    if result is None:
        return {
            "success": False,
            "error": "ViewDisplayMode returned None for mode '{m}'.".format(m=mode_str),
            "code": "OPERATION_FAILED",
        }

    sc.doc.Views.Redraw()
    return {
        "success": True,
        "view_name": target_name,
        "display_mode": mode_str,
    }


# ---------------------------------------------------------------------------
# 7. set_camera
# ---------------------------------------------------------------------------

@handler("viewport.set_camera")
def set_camera(params):
    # type: (dict) -> dict
    """
    Set the camera location, target, and optional lens length for a viewport.

    Params
    ------
    camera_location : list [x, y, z] or dict {x, y, z}
    target          : list [x, y, z] or dict {x, y, z}
    lens_length     : float, optional -- perspective lens length in mm (default 50)
    view_name       : str,   optional -- target viewport; active view if omitted
    """
    camera_location = params.get("camera_location", None)
    target = params.get("target", None)
    lens_length = params.get("lens_length", 50)
    view_name = params.get("view_name", None)

    if camera_location is None:
        raise ValueError("'camera_location' parameter is required.")
    if target is None:
        raise ValueError("'target' parameter is required.")

    def _parse_point(value, name):
        # type: (object, str) -> tuple
        """Accept [x,y,z] list or {x,y,z} dict."""
        if isinstance(value, (list, tuple)):
            if len(value) != 3:
                raise ValueError(
                    "'{n}' must have exactly 3 elements [x, y, z].".format(n=name)
                )
            return (float(value[0]), float(value[1]), float(value[2]))
        if isinstance(value, dict):
            try:
                return (float(value["x"]), float(value["y"]), float(value["z"]))
            except KeyError as exc:
                raise ValueError(
                    "'{n}' dict is missing key: {k}".format(n=name, k=exc)
                )
        raise TypeError(
            "'{n}' must be a list [x,y,z] or dict {{x,y,z}}, got {t}.".format(
                n=name, t=type(value).__name__
            )
        )

    cam_x, cam_y, cam_z = _parse_point(camera_location, "camera_location")
    tgt_x, tgt_y, tgt_z = _parse_point(target, "target")

    if lens_length is not None:
        lens_length = float(lens_length)
        if lens_length <= 0:
            raise ValueError("lens_length must be positive, got {l}".format(l=lens_length))

    # Resolve view name string for rhinoscriptsyntax.
    if view_name is not None:
        view = _resolve_view(view_name)
        target_name = view.ActiveViewport.Name
    else:
        view = sc.doc.Views.ActiveView
        if view is None:
            raise ValueError("No active Rhino view available.")
        target_name = view.ActiveViewport.Name

    rs.ViewCamera(target_name, (cam_x, cam_y, cam_z))
    rs.ViewTarget(target_name, (tgt_x, tgt_y, tgt_z))

    if lens_length is not None:
        rs.ViewCameraLens(target_name, lens_length)

    sc.doc.Views.Redraw()

    return {
        "success": True,
        "view_name": target_name,
        "camera_location": {"x": cam_x, "y": cam_y, "z": cam_z},
        "target": {"x": tgt_x, "y": tgt_y, "z": tgt_z},
        "lens_length": lens_length,
    }


# ---------------------------------------------------------------------------
# 8. create_named_view
# ---------------------------------------------------------------------------

def _create_named_view_impl(params):
    # type: (dict) -> dict
    """
    Shared implementation for viewport.create_named_view and
    viewport.add_named_view.

    Accepts two equivalent param shapes:
      - Task-spec shape:  ``name`` (str), ``view_name`` (str, optional)
      - MCP-server shape: ``save_as`` (str), ``source_view_name`` (str, optional)
    """
    # Support both param key conventions.
    name = params.get("name", None) or params.get("save_as", None)
    view_name = params.get("view_name", None) or params.get("source_view_name", None)

    if name is None or str(name).strip() == "":
        raise ValueError(
            "'name' (or 'save_as') parameter is required and must not be empty."
        )

    name = str(name).strip()

    # Resolve the source viewport name string.
    if view_name is not None:
        view = _resolve_view(view_name)
        source_name = view.ActiveViewport.Name
    else:
        view = sc.doc.Views.ActiveView
        if view is None:
            raise ValueError("No active Rhino view available.")
        source_name = view.ActiveViewport.Name

    result = rs.AddNamedView(name, source_name)
    if result is None:
        return {
            "success": False,
            "error": "AddNamedView failed for '{name}'.".format(name=name),
            "code": "OPERATION_FAILED",
        }

    return {
        "success": True,
        "name": name,
        "saved_from": source_name,
    }


@handler("viewport.create_named_view")
def create_named_view(params):
    # type: (dict) -> dict
    """
    Save the current camera of a viewport as a named view.

    Params
    ------
    name      : str           -- name to save the view under
    view_name : str, optional -- viewport to save from; active view if omitted
    """
    return _create_named_view_impl(params)


@handler("viewport.add_named_view")
def add_named_view(params):
    # type: (dict) -> dict
    """
    Alias for viewport.create_named_view.  Accepts the MCP server param
    convention: ``save_as`` (str) and ``source_view_name`` (str, optional).
    """
    return _create_named_view_impl(params)


# ---------------------------------------------------------------------------
# 9. restore_named_view
# ---------------------------------------------------------------------------

@handler("viewport.restore_named_view")
def restore_named_view(params):
    # type: (dict) -> dict
    """
    Restore a previously saved named view.

    Params
    ------
    name      : str           -- name of the saved view to restore
    view_name : str, optional -- viewport to restore into; active view if omitted
    """
    name = params.get("name", None)
    view_name = params.get("view_name", None)

    if name is None or str(name).strip() == "":
        raise ValueError("'name' parameter is required and must not be empty.")

    name = str(name).strip()

    # RestoreNamedView accepts an optional viewport name as the second arg.
    if view_name is not None:
        view = _resolve_view(view_name)
        target_name = view.ActiveViewport.Name
        result = rs.RestoreNamedView(name, target_name)
    else:
        result = rs.RestoreNamedView(name)

    if not result:
        return {
            "success": False,
            "error": "RestoreNamedView failed for '{name}'. "
                     "Check that the named view exists.".format(name=name),
            "code": "OPERATION_FAILED",
        }

    sc.doc.Views.Redraw()
    return {
        "success": True,
        "restored": name,
    }


# ---------------------------------------------------------------------------
# 10. list_named_views
# ---------------------------------------------------------------------------

@handler("viewport.list_named_views")
def list_named_views(params):
    # type: (dict) -> dict
    """
    Return all named views saved in the document.

    Returns
    -------
    dict
        named_views : list of str
        count       : int
    """
    views = rs.NamedViews()
    if views is None:
        views = []

    return {
        "success": True,
        "named_views": list(views),
        "count": len(views),
    }


# ---------------------------------------------------------------------------
# 11. get_view_info
# ---------------------------------------------------------------------------

@handler("viewport.get_view_info")
def get_view_info(params):
    # type: (dict) -> dict
    """
    Return camera and display metadata for a viewport.

    Params
    ------
    view_name : str, optional -- target viewport; active view if omitted

    Returns
    -------
    dict
        camera_location, target, up_vector, lens_length, projection,
        display_mode, viewport_size
    """
    view_name = params.get("view_name", None)
    view = _resolve_view(view_name)

    viewport = view.ActiveViewport
    actual_name = str(viewport.Name)

    # Camera location and target.
    cam_loc = viewport.CameraLocation
    cam_target = viewport.CameraTarget
    cam_up = viewport.CameraUp

    # Lens length (only meaningful for perspective viewports).
    try:
        lens = float(viewport.Camera35mmLensLength)
    except Exception:
        lens = None

    # Projection type as a human-readable string.
    try:
        is_parallel = viewport.IsParallelProjection
        is_two_point = viewport.IsTwoPointPerspectiveProjection
        if is_parallel:
            projection = "parallel"
        elif is_two_point:
            projection = "two_point_perspective"
        else:
            projection = "perspective"
    except Exception:
        projection = "unknown"

    # Current display mode name.
    try:
        display_mode = str(viewport.DisplayMode.EnglishName)
    except Exception:
        display_mode = "unknown"

    # Viewport pixel size.
    try:
        vp_size = view.ClientRectangle
        viewport_size = {
            "width": int(vp_size.Width),
            "height": int(vp_size.Height),
        }
    except Exception:
        viewport_size = {"width": None, "height": None}

    return {
        "success": True,
        "view_name": actual_name,
        "camera_location": _serialize_point3d(cam_loc),
        "target": _serialize_point3d(cam_target),
        "up_vector": _serialize_vector3d(cam_up),
        "lens_length": lens,
        "projection": projection,
        "display_mode": display_mode,
        "viewport_size": viewport_size,
    }


# ---------------------------------------------------------------------------
# 12. set_background_color
# ---------------------------------------------------------------------------

@handler("viewport.set_background_color")
def set_background_color(params):
    # type: (dict) -> dict
    """
    Set the Rhino application viewport background color.

    Params
    ------
    color : list [r, g, b] or dict {r, g, b} -- RGB channels 0-255
    """
    color = params.get("color", None)
    if color is None:
        raise ValueError("'color' parameter is required.")

    # Accept [r, g, b] list or {r, g, b} dict.
    if isinstance(color, (list, tuple)):
        if len(color) != 3:
            raise ValueError("'color' list must have exactly 3 elements [r, g, b].")
        r, g, b = int(color[0]), int(color[1]), int(color[2])
    elif isinstance(color, dict):
        try:
            r, g, b = int(color["r"]), int(color["g"]), int(color["b"])
        except KeyError as exc:
            raise ValueError("'color' dict is missing key: {k}".format(k=exc))
    else:
        raise TypeError(
            "'color' must be a list [r,g,b] or dict {{r,g,b}}, "
            "got {t}.".format(t=type(color).__name__)
        )

    for channel, val in (("r", r), ("g", g), ("b", b)):
        if not 0 <= val <= 255:
            raise ValueError(
                "Color channel '{c}' must be between 0 and 255, got {v}.".format(
                    c=channel, v=val
                )
            )

    new_color = System.Drawing.Color.FromArgb(r, g, b)
    Rhino.ApplicationSettings.AppearanceSettings.ViewportBackgroundColor = new_color
    sc.doc.Views.Redraw()

    return {
        "success": True,
        "color": {"r": r, "g": g, "b": b},
    }
