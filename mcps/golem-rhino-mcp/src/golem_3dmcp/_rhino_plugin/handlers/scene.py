# -*- coding: utf-8 -*-
"""
rhino_plugin/handlers/scene.py
================================
Scene Intelligence handlers for GOLEM-3DMCP.

Provides document inspection, layer management, object querying, group and
block enumeration, and layer mutation -- all running **inside Rhino 3D** under
Python 3.9.

Design notes
------------
* Python 3.9 compatible -- no ``match``/``case``, no ``X | Y`` union syntax,
  no lowercase ``dict[...]`` / ``list[...]`` generics in runtime annotations.
* Zero external dependencies -- only Python stdlib + Rhino APIs.
* Every handler accepts a single ``params`` dict and returns a JSON-serialisable
  dict.  All handlers are decorated with ``@handler("scene.<name>")`` so that
  the dispatcher routes ``scene.*`` method names here automatically.
* Rhino-specific imports are guarded by a ``try/except ImportError`` block so
  the module can be parsed by linters outside of the Rhino runtime.

Wire method names (must match ``mcp_server/tools/scene.py`` exactly):
    scene.get_document_info
    scene.list_layers
    scene.list_objects
    scene.get_object_info
    scene.get_selected_objects
    scene.get_groups
    scene.get_blocks
    scene.create_layer
    scene.delete_layer
    scene.set_current_layer
"""

import fnmatch
try:
    from typing import Any, Dict, List, Optional
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
from rhino_plugin.utils.geometry_serializer import serialize_object, serialize_any


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _units_string(unit_system):
    # type: (Any) -> str
    """Convert a Rhino UnitSystem enum value to a human-readable string."""
    _MAP = {
        0:  "None",
        1:  "Microns",
        2:  "Millimeters",
        3:  "Centimeters",
        4:  "Meters",
        5:  "Kilometers",
        6:  "Microinches",
        7:  "Mils",
        8:  "Inches",
        9:  "Feet",
        10: "Miles",
        11: "CustomUnits",
        12: "Angstroms",
        13: "Nanometers",
        14: "Decimeters",
        15: "Dekameters",
        16: "Hectometers",
        17: "Megameters",
        18: "Gigameters",
        19: "Lightyears",
    }
    try:
        # The enum value is an integer in the Rhino API.
        return _MAP.get(int(unit_system), str(unit_system))
    except Exception:
        return str(unit_system)


def _object_type_matches(rhino_object, type_filter):
    # type: (Any, str) -> bool
    """
    Return True if *rhino_object* matches the requested *type_filter* string.

    Recognised filter values (case-insensitive):
        all, point, curve, surface, brep, mesh, extrusion, subd,
        annotation, light
    """
    if not _RHINO_AVAILABLE or rhino_object is None:
        return False

    tf = type_filter.lower().strip()
    if tf in ("all", ""):
        return True

    geom = None
    try:
        geom = rhino_object.Geometry
    except Exception:
        return False

    if geom is None:
        return False

    if tf == "point":
        return isinstance(geom, RG.Point)
    if tf == "curve":
        return isinstance(geom, RG.Curve)
    if tf == "surface":
        return isinstance(geom, RG.Surface) and not isinstance(geom, (RG.Brep, RG.Extrusion))
    if tf == "brep":
        return isinstance(geom, RG.Brep)
    if tf == "mesh":
        return isinstance(geom, RG.Mesh)
    if tf == "extrusion":
        return isinstance(geom, RG.Extrusion)
    if tf == "subd":
        return isinstance(geom, RG.SubD)
    if tf == "annotation":
        return isinstance(geom, RG.AnnotationBase)
    if tf == "light":
        return isinstance(geom, RG.Light)
    # Unknown filter -- include everything so callers get data rather than nothing.
    return True


def _layer_object_count(layer_index):
    # type: (int) -> int
    """Count objects whose layer index matches *layer_index*."""
    count = 0
    if not _RHINO_AVAILABLE:
        return count
    try:
        for obj in sc.doc.Objects:
            try:
                if obj.Attributes.LayerIndex == layer_index:
                    count += 1
            except Exception:
                pass
    except Exception:
        pass
    return count


def _serialize_layer(layer):
    # type: (Any) -> Dict[str, Any]
    """Convert a Rhino Layer object to a JSON-serialisable dict."""
    result = {
        "name": "",
        "full_path": "",
        "color": {"r": 0, "g": 0, "b": 0, "a": 255},
        "visible": True,
        "locked": False,
        "parent_name": None,
        "object_count": 0,
        "is_current": False,
    }

    try:
        result["name"] = str(layer.Name)
    except Exception:
        pass

    try:
        result["full_path"] = str(layer.FullPath)
    except Exception:
        pass

    try:
        c = layer.Color
        result["color"] = {
            "r": int(c.R),
            "g": int(c.G),
            "b": int(c.B),
            "a": int(c.A),
        }
    except Exception:
        pass

    try:
        result["visible"] = bool(layer.IsVisible)
    except Exception:
        pass

    try:
        result["locked"] = bool(layer.IsLocked)
    except Exception:
        pass

    try:
        parent_index = layer.ParentLayerId
        # ParentLayerId is a System.Guid; Guid.Empty means no parent.
        if parent_index != System.Guid.Empty:
            parent_layer = sc.doc.Layers.FindId(parent_index)
            if parent_layer is not None:
                result["parent_name"] = str(parent_layer.FullPath)
    except Exception:
        pass

    try:
        result["object_count"] = _layer_object_count(layer.Index)
    except Exception:
        pass

    try:
        result["is_current"] = (layer.Index == sc.doc.Layers.CurrentLayerIndex)
    except Exception:
        pass

    return result


# ---------------------------------------------------------------------------
# 1. get_document_info
# ---------------------------------------------------------------------------

@handler("scene.get_document_info")
def get_document_info(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Return high-level metadata about the currently open Rhino document.

    Returns
    -------
    dict with keys:
        file_path       : str   -- absolute path to the 3dm file (empty if unsaved)
        units           : str   -- model unit system as a human-readable string
        absolute_tolerance : float
        angle_tolerance : float -- in degrees
        object_count    : int
        layer_count     : int
    """
    result = {
        "file_path": "",
        "units": "Unknown",
        "absolute_tolerance": 0.0,
        "angle_tolerance": 0.0,
        "object_count": 0,
        "layer_count": 0,
    }

    if not _RHINO_AVAILABLE:
        return result

    doc = sc.doc

    try:
        result["file_path"] = str(doc.Path) if doc.Path else ""
    except Exception:
        pass

    try:
        result["units"] = _units_string(doc.ModelUnitSystem)
    except Exception:
        pass

    try:
        result["absolute_tolerance"] = float(doc.ModelAbsoluteTolerance)
    except Exception:
        pass

    try:
        result["angle_tolerance"] = float(doc.ModelAngleToleranceDegrees)
    except Exception:
        pass

    try:
        result["object_count"] = int(doc.Objects.Count)
    except Exception:
        pass

    try:
        result["layer_count"] = int(doc.Layers.Count)
    except Exception:
        pass

    return result


# ---------------------------------------------------------------------------
# 2. list_layers  (task spec calls this get_layers; wire name is list_layers)
# ---------------------------------------------------------------------------

@handler("scene.list_layers")
def list_layers(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Return all layers in the document as a list of dicts.

    Each layer dict includes: name, full_path, color (r/g/b/a), visible,
    locked, parent_name, object_count, is_current.

    Returns
    -------
    dict with key ``layers`` containing a list of layer dicts.
    """
    if not _RHINO_AVAILABLE:
        return {"layers": []}

    layers = []  # type: List[Dict[str, Any]]
    try:
        for layer in sc.doc.Layers:
            try:
                layers.append(_serialize_layer(layer))
            except Exception:
                pass
    except Exception:
        pass

    return {"layers": layers}


# ---------------------------------------------------------------------------
# 3. list_objects  (task spec calls this get_objects; wire name is list_objects)
# ---------------------------------------------------------------------------

@handler("scene.list_objects")
def list_objects(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Return document objects with optional filters and pagination.

    Params (all optional)
    -----
    object_type   : str  -- one of "point","curve","surface","brep","mesh",
                          "extrusion","subd","annotation","light","all"
                          (default "all")
    layer         : str  -- full layer path; restrict to objects on this layer
    name_pattern  : str  -- wildcard pattern (fnmatch style) matched against
                          object names
    selected_only : bool -- only return currently selected objects (default False)
    offset        : int  -- skip this many objects before collecting (default 0)
    limit         : int  -- maximum objects to return (default 100, 0 = no cap)

    Returns
    -------
    dict with keys:
        objects : list of serialised object dicts
        total   : int -- total matching objects before pagination
        offset  : int -- echoed back
        limit   : int -- echoed back
    """
    if not _RHINO_AVAILABLE:
        return {"objects": [], "total": 0, "offset": 0, "limit": 100}

    # Parse filter parameters.
    object_type = str(params.get("object_type", "all") or "all").lower().strip()
    layer_filter = params.get("layer", None)       # type: Optional[str]
    name_pattern = params.get("name_pattern", None)  # type: Optional[str]
    selected_only = bool(params.get("selected_only", False))
    offset = int(params.get("offset", 0))
    limit = int(params.get("limit", 100))

    if layer_filter is not None:
        layer_filter = str(layer_filter).strip()

    if name_pattern is not None:
        name_pattern = str(name_pattern).strip()

    # Resolve layer index once if a layer filter was given.
    target_layer_index = None  # type: Optional[int]
    if layer_filter:
        try:
            li = sc.doc.Layers.FindByFullPath(layer_filter, -1)
            if li < 0:
                # Layer not found -- return empty result rather than everything.
                return {"objects": [], "total": 0, "offset": offset, "limit": limit}
            target_layer_index = li
        except Exception:
            return {"objects": [], "total": 0, "offset": offset, "limit": limit}

    # Collect all matching objects (before pagination).
    matching = []  # type: List[Any]

    try:
        if selected_only:
            candidates = list(sc.doc.Objects.GetSelectedObjects(False, False))
        else:
            candidates = list(sc.doc.Objects)
    except Exception:
        candidates = []

    for obj in candidates:
        if obj is None:
            continue

        # Type filter.
        if object_type not in ("all", ""):
            if not _object_type_matches(obj, object_type):
                continue

        # Layer filter.
        if target_layer_index is not None:
            try:
                if obj.Attributes.LayerIndex != target_layer_index:
                    continue
            except Exception:
                continue

        # Name pattern filter.
        if name_pattern:
            try:
                obj_name = str(obj.Attributes.Name) if obj.Attributes.Name else ""
                if not fnmatch.fnmatch(obj_name, name_pattern):
                    continue
            except Exception:
                continue

        matching.append(obj)

    total = len(matching)

    # Apply pagination.
    if offset > 0:
        matching = matching[offset:]

    if limit > 0:
        matching = matching[:limit]

    # Serialise.
    serialised = []  # type: List[Dict[str, Any]]
    for obj in matching:
        try:
            serialised.append(serialize_object(obj))
        except Exception:
            pass

    return {
        "objects": serialised,
        "total": total,
        "offset": offset,
        "limit": limit,
    }


# ---------------------------------------------------------------------------
# 4. get_object_info  (task spec calls this get_object_details)
# ---------------------------------------------------------------------------

@handler("scene.get_object_info")
def get_object_info(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Return full geometry details and attributes for a single object by GUID.

    Params
    ------
    guid : str  -- object GUID (braces optional)

    Returns
    -------
    dict -- serialised object (same schema as serialize_object) plus a
    ``geometry_detail`` key containing the output of ``serialize_any`` on the
    raw geometry object.

    Raises
    ------
    ValueError  -- if ``guid`` param is missing or empty
    KeyError    -- if no object with that GUID exists in the document
    """
    guid_str = params.get("guid", "")  # type: str
    if not guid_str:
        raise ValueError("'guid' parameter is required and must be a non-empty string.")

    if not _RHINO_AVAILABLE:
        raise RuntimeError("Rhino is not available in this environment.")

    # Normalise: strip braces and whitespace.
    normalised = str(guid_str).strip().strip("{}")

    try:
        sys_guid = System.Guid(normalised)
    except Exception:
        raise ValueError(
            "Invalid GUID format: '{guid}'".format(guid=guid_str)
        )

    obj = sc.doc.Objects.FindId(sys_guid)
    if obj is None:
        raise KeyError(
            "Object not found in Rhino document: '{guid}'".format(guid=guid_str)
        )

    result = serialize_object(obj)  # type: Dict[str, Any]

    # Augment with full geometry detail via serialize_any.
    try:
        geom = obj.Geometry
        if geom is not None:
            result["geometry_detail"] = serialize_any(geom)
    except Exception:
        result["geometry_detail"] = {"type": "unknown"}

    # Include all object attributes as a flat dict.
    attrs_dict = {}  # type: Dict[str, Any]
    try:
        attrs = obj.Attributes
        if attrs is not None:
            try:
                attrs_dict["object_id"] = str(attrs.ObjectId)
            except Exception:
                pass
            try:
                attrs_dict["name"] = str(attrs.Name) if attrs.Name else ""
            except Exception:
                pass
            try:
                attrs_dict["layer_index"] = int(attrs.LayerIndex)
            except Exception:
                pass
            try:
                attrs_dict["space"] = int(attrs.Space)
            except Exception:
                pass
            try:
                attrs_dict["linetype_index"] = int(attrs.LinetypeIndex)
            except Exception:
                pass
            try:
                attrs_dict["material_index"] = int(attrs.MaterialIndex)
            except Exception:
                pass
            try:
                attrs_dict["wire_density"] = int(attrs.WireDensity)
            except Exception:
                pass
            try:
                from Rhino.DocObjects import ObjectColorSource
                attrs_dict["color_source"] = str(attrs.ColorSource)
            except Exception:
                pass
            try:
                attrs_dict["visible"] = bool(attrs.Visible)
            except Exception:
                pass
            try:
                from Rhino.DocObjects import ObjectMode
                attrs_dict["mode"] = str(attrs.Mode)
            except Exception:
                pass
    except Exception:
        pass

    result["attributes"] = attrs_dict

    return result


# ---------------------------------------------------------------------------
# 5. get_selected_objects
# ---------------------------------------------------------------------------

@handler("scene.get_selected_objects")
def get_selected_objects(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Return all currently selected objects in the Rhino viewport.

    Returns
    -------
    dict with key ``objects`` containing a list of serialised object dicts.
    """
    if not _RHINO_AVAILABLE:
        return {"objects": []}

    serialised = []  # type: List[Dict[str, Any]]
    try:
        selected = sc.doc.Objects.GetSelectedObjects(False, False)
        for obj in selected:
            if obj is not None:
                try:
                    serialised.append(serialize_object(obj))
                except Exception:
                    pass
    except Exception:
        pass

    return {"objects": serialised}


# ---------------------------------------------------------------------------
# 6. get_groups
# ---------------------------------------------------------------------------

@handler("scene.get_groups")
def get_groups(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Return all groups defined in the document.

    Returns
    -------
    dict with key ``groups``, each entry containing:
        name         : str
        index        : int
        member_count : int
        member_guids : list of str
    """
    if not _RHINO_AVAILABLE:
        return {"groups": []}

    groups_list = []  # type: List[Dict[str, Any]]

    try:
        group_table = sc.doc.Groups
        for i in range(group_table.Count):
            try:
                group = group_table[i]
                entry = {
                    "name": "",
                    "index": i,
                    "member_count": 0,
                    "member_guids": [],
                }  # type: Dict[str, Any]

                try:
                    entry["name"] = str(group.Name) if group.Name else ""
                except Exception:
                    pass

                # Collect member GUIDs by scanning object attributes.
                member_guids = []  # type: List[str]
                try:
                    for obj in sc.doc.Objects:
                        try:
                            groups_for_obj = obj.Attributes.GetGroupList()
                            if groups_for_obj is not None and i in groups_for_obj:
                                member_guids.append(str(obj.Id))
                        except Exception:
                            pass
                except Exception:
                    pass

                entry["member_count"] = len(member_guids)
                entry["member_guids"] = member_guids

                groups_list.append(entry)
            except Exception:
                pass
    except Exception:
        pass

    return {"groups": groups_list}


# ---------------------------------------------------------------------------
# 7. get_blocks
# ---------------------------------------------------------------------------

@handler("scene.get_blocks")
def get_blocks(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Return all block (instance) definitions in the document.

    Returns
    -------
    dict with key ``blocks``, each entry containing:
        name           : str
        description    : str
        object_count   : int
        geometry_guids : list of str -- GUIDs of the geometry objects inside the block
        is_referenced  : bool -- True if the block came from a linked/embedded file
    """
    if not _RHINO_AVAILABLE:
        return {"blocks": []}

    blocks_list = []  # type: List[Dict[str, Any]]

    try:
        idef_table = sc.doc.InstanceDefinitions
        for idef in idef_table:
            if idef is None:
                continue
            try:
                # Skip deleted definitions.
                if idef.IsDeleted:
                    continue
            except Exception:
                pass

            entry = {
                "name": "",
                "description": "",
                "object_count": 0,
                "geometry_guids": [],
                "is_referenced": False,
            }  # type: Dict[str, Any]

            try:
                entry["name"] = str(idef.Name) if idef.Name else ""
            except Exception:
                pass

            try:
                entry["description"] = str(idef.Description) if idef.Description else ""
            except Exception:
                pass

            geom_guids = []  # type: List[str]
            try:
                geom_objects = idef.GetObjects()
                if geom_objects is not None:
                    for geom_obj in geom_objects:
                        try:
                            geom_guids.append(str(geom_obj.Id))
                        except Exception:
                            pass
            except Exception:
                pass

            entry["object_count"] = len(geom_guids)
            entry["geometry_guids"] = geom_guids

            try:
                # InstanceDefinitionUpdateType: Static=0, Linked=1, LinkedAndEmbedded=2
                update_type = int(idef.UpdateType)
                entry["is_referenced"] = update_type in (1, 2)
            except Exception:
                pass

            blocks_list.append(entry)
    except Exception:
        pass

    return {"blocks": blocks_list}


# ---------------------------------------------------------------------------
# 8. create_layer
# ---------------------------------------------------------------------------

@handler("scene.create_layer")
def create_layer(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Create a new layer in the document.

    Params
    ------
    name        : str  -- layer name (required); use '::' for nested paths
    color       : dict -- optional {r, g, b, a} (defaults to black)
    parent_name : str  -- optional full path of parent layer
    visible     : bool -- default True
    locked      : bool -- default False

    Returns
    -------
    dict with keys:
        layer_index : int  -- index of the newly created layer
        full_path   : str  -- full layer path as created
        success     : bool
    """
    name = params.get("name", "")  # type: str
    if not name:
        raise ValueError("'name' parameter is required for create_layer.")

    if not _RHINO_AVAILABLE:
        raise RuntimeError("Rhino is not available in this environment.")

    # Colour.
    color_param = params.get("color", {}) or {}
    try:
        r = int(color_param.get("r", 0))
        g = int(color_param.get("g", 0))
        b = int(color_param.get("b", 0))
        a = int(color_param.get("a", 255))
        layer_color = System.Drawing.Color.FromArgb(a, r, g, b)
    except Exception:
        layer_color = System.Drawing.Color.Black

    visible = bool(params.get("visible", True))
    locked = bool(params.get("locked", False))
    parent_name = params.get("parent_name", None)  # type: Optional[str]
    # Also accept the key name used by the MCP tool ("parent").
    if parent_name is None:
        parent_name = params.get("parent", None)

    layer = Rhino.DocObjects.Layer()
    layer.Name = str(name)
    layer.Color = layer_color
    layer.IsVisible = visible
    layer.IsLocked = locked

    # Resolve parent layer if specified.
    if parent_name:
        try:
            parent_index = sc.doc.Layers.FindByFullPath(str(parent_name), -1)
            if parent_index >= 0:
                parent_layer = sc.doc.Layers[parent_index]
                layer.ParentLayerId = parent_layer.Id
        except Exception:
            pass

    layer_index = sc.doc.Layers.Add(layer)

    if layer_index < 0:
        raise RuntimeError(
            "Rhino failed to create layer '{name}'.".format(name=name)
        )

    full_path = ""
    try:
        full_path = str(sc.doc.Layers[layer_index].FullPath)
    except Exception:
        pass

    sc.doc.Views.Redraw()

    return {
        "layer_index": int(layer_index),
        "full_path": full_path,
        "success": True,
    }


# ---------------------------------------------------------------------------
# 9. delete_layer
# ---------------------------------------------------------------------------

@handler("scene.delete_layer")
def delete_layer(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Delete a layer from the document.

    Params
    ------
    name           : str  -- full layer path (required)
    delete_objects : bool -- if True, delete objects on the layer too;
                           if False (default), the call fails when objects exist

    Returns
    -------
    dict with keys:
        success         : bool
        deleted_objects : int -- count of objects deleted (0 unless delete_objects=True)
        message         : str -- human-readable status

    Raises
    ------
    ValueError   -- if layer name is missing or layer is not found
    RuntimeError -- if the layer has objects and delete_objects is False,
                   or if Rhino refuses to delete it (e.g. current layer)
    """
    name = params.get("name", "")  # type: str
    if not name:
        raise ValueError("'name' parameter is required for delete_layer.")

    delete_objects = bool(params.get("delete_objects", False))

    if not _RHINO_AVAILABLE:
        raise RuntimeError("Rhino is not available in this environment.")

    layer_index = sc.doc.Layers.FindByFullPath(str(name), -1)
    if layer_index < 0:
        raise ValueError(
            "Layer not found: '{name}'".format(name=name)
        )

    # Guard: cannot delete the current layer.
    if layer_index == sc.doc.Layers.CurrentLayerIndex:
        raise RuntimeError(
            "Cannot delete the current active layer: '{name}'.".format(name=name)
        )

    # Count objects on this layer.
    object_count = _layer_object_count(layer_index)
    deleted_objects = 0

    if object_count > 0:
        if not delete_objects:
            raise RuntimeError(
                "Layer '{name}' has {count} object(s). "
                "Set delete_objects=True to remove them along with the layer.".format(
                    name=name, count=object_count
                )
            )
        # Delete objects on the layer first.
        try:
            objects_to_delete = [
                obj for obj in sc.doc.Objects
                if obj is not None and obj.Attributes.LayerIndex == layer_index
            ]
            for obj in objects_to_delete:
                try:
                    if sc.doc.Objects.Delete(obj, True):
                        deleted_objects += 1
                except Exception:
                    pass
        except Exception:
            pass

    # Delete the layer.
    success = sc.doc.Layers.Delete(layer_index, True)
    if not success:
        raise RuntimeError(
            "Rhino refused to delete layer '{name}'. "
            "It may have sub-layers; delete those first.".format(name=name)
        )

    sc.doc.Views.Redraw()

    return {
        "success": True,
        "deleted_objects": deleted_objects,
        "message": "Layer '{name}' deleted.".format(name=name),
    }


# ---------------------------------------------------------------------------
# 10. set_current_layer
# ---------------------------------------------------------------------------

@handler("scene.set_current_layer")
def set_current_layer(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Set the active (current) layer by name.

    Params
    ------
    name : str -- full layer path (required)

    Returns
    -------
    dict with keys:
        success     : bool
        layer_index : int  -- index of the layer that is now current
        full_path   : str

    Raises
    ------
    ValueError   -- if name is missing or the layer is not found
    RuntimeError -- if Rhino refuses to set the layer as current (locked/hidden)
    """
    name = params.get("name", "")  # type: str
    if not name:
        raise ValueError("'name' parameter is required for set_current_layer.")

    if not _RHINO_AVAILABLE:
        raise RuntimeError("Rhino is not available in this environment.")

    layer_index = sc.doc.Layers.FindByFullPath(str(name), -1)
    if layer_index < 0:
        raise ValueError(
            "Layer not found: '{name}'".format(name=name)
        )

    # Rhino requires the target layer to be visible and unlocked.
    layer = sc.doc.Layers[layer_index]

    try:
        if not layer.IsVisible:
            raise RuntimeError(
                "Cannot set a hidden layer as current: '{name}'.".format(name=name)
            )
    except RuntimeError:
        raise
    except Exception:
        pass

    try:
        if layer.IsLocked:
            raise RuntimeError(
                "Cannot set a locked layer as current: '{name}'.".format(name=name)
            )
    except RuntimeError:
        raise
    except Exception:
        pass

    sc.doc.Layers.CurrentLayerIndex = layer_index

    full_path = ""
    try:
        full_path = str(sc.doc.Layers[layer_index].FullPath)
    except Exception:
        pass

    return {
        "success": True,
        "layer_index": int(layer_index),
        "full_path": full_path,
    }
