# -*- coding: utf-8 -*-
"""
rhino_plugin/grasshopper/gh_handlers.py
=========================================
Low-level Grasshopper utility functions used by the main handler layer.

These functions sit one step below ``handlers/grasshopper.py``.  They deal
directly with the Grasshopper object model -- serialising components and
parameters, reading/writing values, and baking geometry -- but they do NOT
register dispatcher handlers or raise JSON-RPC errors.  All errors propagate
as plain Python exceptions for the caller to handle.

Public API
----------
  serialize_gh_component(component) -> dict
  serialize_gh_param(param) -> dict
  get_param_value(param) -> any
  set_param_value(component, param_name, value)
  bake_component_output(component, doc, layer=None) -> list[str]

Python 3.9 compatibility
------------------------
* No ``match``/``case``.
* No ``X | Y`` union type syntax.
* No lowercase ``dict[...]`` / ``list[...]`` in runtime annotations.
* Only stdlib plus Rhino/Grasshopper APIs available inside Rhino.

Author: GOLEM-3DMCP
"""

try:
    from typing import Any, Dict, List, Optional
except ImportError:
    pass

# ---------------------------------------------------------------------------
# Grasshopper / Rhino availability guard
# ---------------------------------------------------------------------------

_GH_AVAILABLE = False
_GH_IMPORT_ERROR = ""

try:
    import clr                                                   # type: ignore
    clr.AddReference("Grasshopper")
    import Grasshopper                                           # type: ignore
    from Grasshopper.Kernel import GH_Document                  # type: ignore
    from Grasshopper.Kernel.Special import GH_NumberSlider      # type: ignore
    from Grasshopper.Kernel.Special import GH_Panel             # type: ignore
    from Grasshopper.Kernel.Special import GH_BooleanToggle     # type: ignore
    import Rhino                                                 # type: ignore
    import Rhino.Geometry as RG                                  # type: ignore
    import scriptcontext as sc                                   # type: ignore
    _GH_AVAILABLE = True
except Exception as _exc:
    _GH_IMPORT_ERROR = str(_exc)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _gh_type_name(obj):
    # type: (Any) -> str
    """Return a short, human-readable type label for a GH object."""
    try:
        return type(obj).__name__
    except Exception:
        return "unknown"


def _safe_str(value):
    # type: (Any) -> str
    """Convert *value* to str without raising."""
    try:
        return str(value)
    except Exception:
        return ""


def _list_input_params(component):
    # type: (Any) -> List[Any]
    """Return the list of input IGH_Param objects for *component*."""
    try:
        if hasattr(component, "Params") and hasattr(component.Params, "Input"):
            return list(component.Params.Input)
    except Exception:
        pass
    return []


def _list_output_params(component):
    # type: (Any) -> List[Any]
    """Return the list of output IGH_Param objects for *component*."""
    try:
        if hasattr(component, "Params") and hasattr(component.Params, "Output"):
            return list(component.Params.Output)
    except Exception:
        pass
    return []


# ---------------------------------------------------------------------------
# serialize_gh_component
# ---------------------------------------------------------------------------

def serialize_gh_component(component):
    # type: (Any) -> Dict[str, Any]
    """
    Serialise a Grasshopper component (IGH_DocumentObject) to a plain dict.

    Returns
    -------
    dict with keys:
        nickname       : str    -- component NickName
        name           : str    -- component Name
        type           : str    -- Python type name of the component class
        guid           : str    -- instance GUID as string
        position       : dict   -- {"x": float, "y": float}
        input_params   : list   -- each entry is a serialised input param dict
        output_params  : list   -- each entry is a serialised output param dict
    """
    result = {
        "nickname": "",
        "name": "",
        "type": _gh_type_name(component),
        "guid": "",
        "position": {"x": 0.0, "y": 0.0},
        "input_params": [],
        "output_params": [],
    }  # type: Dict[str, Any]

    try:
        result["nickname"] = _safe_str(getattr(component, "NickName", ""))
    except Exception:
        pass

    try:
        result["name"] = _safe_str(getattr(component, "Name", ""))
    except Exception:
        pass

    try:
        result["guid"] = _safe_str(component.InstanceGuid)
    except Exception:
        pass

    # Canvas pivot / position.
    try:
        attrs = component.Attributes
        if attrs is not None:
            pivot = attrs.Pivot
            result["position"] = {"x": float(pivot.X), "y": float(pivot.Y)}
    except Exception:
        pass

    # Input parameters.
    for p in _list_input_params(component):
        try:
            param_dict = {
                "name": _safe_str(getattr(p, "NickName", "")),
                "type": _gh_type_name(p),
                "value_summary": _summarise_param_data(p),
            }
            result["input_params"].append(param_dict)
        except Exception:
            pass

    # Output parameters.
    for p in _list_output_params(component):
        try:
            param_dict = {
                "name": _safe_str(getattr(p, "NickName", "")),
                "type": _gh_type_name(p),
            }
            result["output_params"].append(param_dict)
        except Exception:
            pass

    return result


# ---------------------------------------------------------------------------
# serialize_gh_param
# ---------------------------------------------------------------------------

def serialize_gh_param(component):
    # type: (Any) -> Dict[str, Any]
    """
    Serialise a *standalone* parameter component (slider, panel, toggle, etc.)
    into a typed value dict.

    This is used by ``gh_get_param`` to read the current value of a named
    input component.

    Returns
    -------
    dict -- type-specific structure:

    Slider::

        {"type": "slider", "value": float, "min": float, "max": float,
         "slider_type": "integer" | "float" | "odd" | "even"}

    Panel::

        {"type": "panel", "value": str}

    Toggle::

        {"type": "toggle", "value": bool}

    Number parameter::

        {"type": "number", "value": float}

    Generic::

        {"type": "param", "value": <any>, "component_type": <str>}
    """
    if not _GH_AVAILABLE:
        raise RuntimeError(
            "Grasshopper is not available. "
            "Import error: {err}".format(err=_GH_IMPORT_ERROR)
        )

    # --- GH_NumberSlider ---
    try:
        if isinstance(component, GH_NumberSlider):
            result = {
                "type": "slider",
                "value": float(component.CurrentValue),
                "min": float(component.Slider.Minimum),
                "max": float(component.Slider.Maximum),
                "slider_type": _safe_str(component.Slider.Type).lower(),
            }
            return result
    except Exception:
        pass

    # --- GH_Panel ---
    try:
        if isinstance(component, GH_Panel):
            return {
                "type": "panel",
                "value": _safe_str(component.UserText),
            }
    except Exception:
        pass

    # --- GH_BooleanToggle ---
    try:
        if isinstance(component, GH_BooleanToggle):
            return {
                "type": "toggle",
                "value": bool(component.Value),
            }
    except Exception:
        pass

    # --- Generic IGH_Param with VolatileData ---
    try:
        if hasattr(component, "VolatileData"):
            vd = component.VolatileData
            if vd is not None and vd.DataCount == 1:
                branch = vd.get_Branch(vd.Paths[0])
                if branch is not None and len(branch) > 0:
                    raw = branch[0]
                    val = _unwrap_gh_goo(raw)
                    if isinstance(val, float) or isinstance(val, int):
                        return {"type": "number", "value": float(val)}
    except Exception:
        pass

    # Fallback: return a summary using serialize_gh_component.
    return {
        "type": "param",
        "component_type": _gh_type_name(component),
        "value": _summarise_param_data(component),
    }


# ---------------------------------------------------------------------------
# get_param_value
# ---------------------------------------------------------------------------

def get_param_value(param):
    # type: (Any) -> Any
    """
    Extract the current data value(s) from an IGH_Param.

    Handles the GH_Structure / GH_Path data tree by flattening the first
    branch into a list if multiple values are present, or returning a scalar
    for single-value params.

    Returns a JSON-serialisable value (str, float, bool, list, or dict).
    """
    if not _GH_AVAILABLE:
        return None

    try:
        vd = getattr(param, "VolatileData", None)
        if vd is None or vd.DataCount == 0:
            return None

        all_values = []  # type: List[Any]
        for path in vd.Paths:
            branch = vd.get_Branch(path)
            if branch is None:
                continue
            for item in branch:
                try:
                    all_values.append(_unwrap_gh_goo(item))
                except Exception:
                    all_values.append(None)

        if len(all_values) == 0:
            return None
        if len(all_values) == 1:
            return all_values[0]
        return all_values
    except Exception:
        return None


# ---------------------------------------------------------------------------
# set_param_value
# ---------------------------------------------------------------------------

def set_param_value(component, param_name, value):
    # type: (Any, Optional[str], Any) -> None
    """
    Set a value on a Grasshopper component.

    The function inspects the concrete type of *component* and applies the
    appropriate setter.  *param_name* is accepted for API consistency but is
    currently unused -- the value is applied to the component itself (for
    standalone param components such as sliders, panels, and toggles).

    Supports:
    * ``GH_NumberSlider``  -- clamps *value* to [min, max] and calls
      ``SetSliderValue(Decimal)``
    * ``GH_Panel``         -- sets ``UserText`` string property
    * ``GH_BooleanToggle`` -- sets ``Value`` bool property
    * Generic ``IGH_Param`` with ``AddVolatileData`` -- injects a single
      GH_Number / GH_String via the volatile data mechanism
    * ``Grasshopper.Kernel.Parameters.Param_Number`` -- same mechanism

    Raises
    ------
    TypeError
        If the component type is not recognised and no fallback applies.
    """
    if not _GH_AVAILABLE:
        raise RuntimeError(
            "Grasshopper is not available. "
            "Import error: {err}".format(err=_GH_IMPORT_ERROR)
        )

    # --- GH_NumberSlider ---
    try:
        if isinstance(component, GH_NumberSlider):
            import System                                        # type: ignore
            min_val = float(component.Slider.Minimum)
            max_val = float(component.Slider.Maximum)
            clamped = max(min_val, min(max_val, float(value)))
            component.SetSliderValue(System.Decimal(clamped))
            return
    except Exception as exc:
        raise TypeError(
            "Failed to set slider '{nick}': {err}".format(
                nick=getattr(component, "NickName", "?"), err=exc
            )
        )

    # --- GH_Panel ---
    try:
        if isinstance(component, GH_Panel):
            component.UserText = str(value)
            return
    except Exception as exc:
        raise TypeError(
            "Failed to set panel '{nick}': {err}".format(
                nick=getattr(component, "NickName", "?"), err=exc
            )
        )

    # --- GH_BooleanToggle ---
    try:
        if isinstance(component, GH_BooleanToggle):
            component.Value = bool(value)
            return
    except Exception as exc:
        raise TypeError(
            "Failed to set toggle '{nick}': {err}".format(
                nick=getattr(component, "NickName", "?"), err=exc
            )
        )

    # --- Generic IGH_Param: inject via volatile data ---
    try:
        if hasattr(component, "AddVolatileData"):
            from Grasshopper.Kernel.Data import GH_Path        # type: ignore
            from Grasshopper import DataTree                    # type: ignore
            component.ClearData()
            gh_path = GH_Path(0)
            gh_value = _wrap_as_gh_goo(value)
            component.AddVolatileData(gh_path, 0, gh_value)
            return
    except Exception as exc:
        raise TypeError(
            "Failed to inject volatile data into '{nick}': {err}".format(
                nick=getattr(component, "NickName", "?"), err=exc
            )
        )

    raise TypeError(
        "Component '{nick}' (type: {t}) is not a recognised settable type.".format(
            nick=getattr(component, "NickName", "?"),
            t=_gh_type_name(component),
        )
    )


# ---------------------------------------------------------------------------
# bake_component_output
# ---------------------------------------------------------------------------

def bake_component_output(component, doc, layer=None):
    # type: (Any, Any, Optional[str]) -> List[str]
    """
    Bake all output geometry from *component* into the Rhino document *doc*.

    Parameters
    ----------
    component:
        A Grasshopper IGH_DocumentObject whose output parameters may carry
        geometry.
    doc:
        The ``scriptcontext.doc`` (``Rhino.RhinoDoc``) instance to bake into.
    layer:
        Optional layer name.  If the layer does not exist it is created.
        Defaults to the active layer if None.

    Returns
    -------
    list[str]
        GUIDs (as strings) of the newly added Rhino document objects.
    """
    if not _GH_AVAILABLE:
        raise RuntimeError(
            "Grasshopper is not available. "
            "Import error: {err}".format(err=_GH_IMPORT_ERROR)
        )

    baked_guids = []  # type: List[str]

    # Resolve the layer index.
    layer_index = _resolve_layer(doc, layer)

    for out_param in _list_output_params(component):
        try:
            vd = getattr(out_param, "VolatileData", None)
            if vd is None or vd.DataCount == 0:
                continue
            for path in vd.Paths:
                branch = vd.get_Branch(path)
                if branch is None:
                    continue
                for item in branch:
                    guid = _bake_single_item(item, doc, layer_index)
                    if guid:
                        baked_guids.append(guid)
        except Exception:
            pass

    return baked_guids


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _summarise_param_data(param):
    # type: (Any) -> Any
    """
    Return a compact JSON-friendly summary of the data held by an IGH_Param.

    Used for the ``value_summary`` field in serialised input params.
    """
    try:
        vd = getattr(param, "VolatileData", None)
        if vd is None:
            return None
        count = int(vd.DataCount)
        if count == 0:
            return None
        if count == 1:
            branch = vd.get_Branch(vd.Paths[0])
            if branch and len(branch) > 0:
                return _safe_str(_unwrap_gh_goo(branch[0]))
        return "<{n} items>".format(n=count)
    except Exception:
        return None


def _unwrap_gh_goo(goo):
    # type: (Any) -> Any
    """
    Extract the underlying Python / .NET value from a GH_Goo wrapper.

    Tries several unwrapping strategies in order:
    1. ``goo.Value``   -- works for GH_Number, GH_Boolean, GH_String, etc.
    2. ``goo.IsValid`` check + cast to float / str / bool
    3. Fall back to ``str(goo)``

    Returns a JSON-serialisable type: float, int, bool, str, dict, or None.
    """
    if goo is None:
        return None

    # Most GH_Goo types expose .Value.
    value = None
    try:
        value = goo.Value
    except Exception:
        pass

    if value is None:
        try:
            value = goo
        except Exception:
            return None

    # Try numeric.
    try:
        return float(value)
    except (TypeError, ValueError):
        pass

    # Try bool (must check before str to avoid "True"/"False" strings).
    try:
        if isinstance(value, bool):
            return bool(value)
    except Exception:
        pass

    # Try geometry -- return a compact summary dict.
    if _GH_AVAILABLE:
        try:
            if isinstance(value, RG.Point3d):
                return {"x": float(value.X), "y": float(value.Y), "z": float(value.Z)}
        except Exception:
            pass
        try:
            if isinstance(value, RG.Vector3d):
                return {"x": float(value.X), "y": float(value.Y), "z": float(value.Z)}
        except Exception:
            pass
        try:
            if isinstance(value, (RG.Curve, RG.Brep, RG.Mesh, RG.Surface)):
                return {"geometry_type": _gh_type_name(value)}
        except Exception:
            pass

    # Fallback: string.
    return _safe_str(value)


def _wrap_as_gh_goo(value):
    # type: (Any) -> Any
    """
    Wrap a Python value in the appropriate GH_Goo subclass for injection into
    Grasshopper's volatile data mechanism.
    """
    try:
        from Grasshopper.Kernel.Types import GH_Number    # type: ignore
        from Grasshopper.Kernel.Types import GH_String    # type: ignore
        from Grasshopper.Kernel.Types import GH_Boolean   # type: ignore
        from Grasshopper.Kernel.Types import GH_Point     # type: ignore
    except Exception:
        # If we cannot import the wrappers, return the raw value and let GH
        # handle the conversion.
        return value

    if isinstance(value, bool):
        return GH_Boolean(value)
    if isinstance(value, (int, float)):
        return GH_Number(float(value))
    if isinstance(value, str):
        return GH_String(value)
    if isinstance(value, dict) and "x" in value and "y" in value and "z" in value:
        try:
            pt = RG.Point3d(float(value["x"]), float(value["y"]), float(value["z"]))
            return GH_Point(pt)
        except Exception:
            pass
    # Return as-is and rely on Grasshopper's implicit conversion.
    return value


def _resolve_layer(doc, layer_name):
    # type: (Any, Optional[str]) -> int
    """
    Return the layer index for *layer_name* in *doc*, creating it if needed.

    Falls back to the current active layer index if *layer_name* is None or
    the layer cannot be created.
    """
    if layer_name is None:
        try:
            return doc.Layers.CurrentLayerIndex
        except Exception:
            return 0

    try:
        existing_index = doc.Layers.FindByFullPath(layer_name, True)
        if existing_index >= 0:
            return existing_index

        # Create the layer.
        import Rhino.DocObjects as RDO                    # type: ignore
        new_layer = RDO.Layer()
        new_layer.Name = layer_name
        new_index = doc.Layers.Add(new_layer)
        if new_index >= 0:
            return new_index
    except Exception:
        pass

    try:
        return doc.Layers.CurrentLayerIndex
    except Exception:
        return 0


def _bake_single_item(goo_item, doc, layer_index):
    # type: (Any, Any, int) -> Optional[str]
    """
    Bake a single GH_Goo geometry item into *doc* on *layer_index*.

    Returns the GUID string of the new object, or None if the item could not
    be baked (e.g. it carries non-geometry data).
    """
    try:
        import Rhino.DocObjects as RDO                    # type: ignore
        value = _unwrap_gh_goo(goo_item)

        # If the goo exposes a BakeGeometry method, use it (honoured by
        # custom GH components that override baking).
        if hasattr(goo_item, "BakeGeometry"):
            attrs = RDO.ObjectAttributes()
            attrs.LayerIndex = layer_index
            guid_out = [None]
            ok = goo_item.BakeGeometry(doc, attrs, guid_out)
            if ok and guid_out[0] is not None:
                return _safe_str(guid_out[0])

        # Otherwise fall back to adding geometry directly.
        raw = getattr(goo_item, "Value", goo_item)
        if raw is None:
            return None

        attrs = RDO.ObjectAttributes()
        attrs.LayerIndex = layer_index
        added_guid = None

        if isinstance(raw, RG.Brep):
            added_guid = doc.Objects.AddBrep(raw, attrs)
        elif isinstance(raw, RG.Mesh):
            added_guid = doc.Objects.AddMesh(raw, attrs)
        elif isinstance(raw, RG.Curve):
            added_guid = doc.Objects.AddCurve(raw, attrs)
        elif isinstance(raw, RG.Surface):
            brep = raw.ToBrep()
            if brep is not None:
                added_guid = doc.Objects.AddBrep(brep, attrs)
        elif isinstance(raw, RG.Point3d):
            added_guid = doc.Objects.AddPoint(raw, attrs)
        elif isinstance(raw, RG.Extrusion):
            added_guid = doc.Objects.AddExtrusion(raw, attrs)
        elif isinstance(raw, RG.SubD):
            added_guid = doc.Objects.AddSubD(raw, attrs)

        if added_guid is not None:
            empty_guid = _safe_str(
                __import__("System").Guid.Empty
            ) if _GH_AVAILABLE else "00000000-0000-0000-0000-000000000000"
            if _safe_str(added_guid) != empty_guid:
                return _safe_str(added_guid)
    except Exception:
        pass

    return None
