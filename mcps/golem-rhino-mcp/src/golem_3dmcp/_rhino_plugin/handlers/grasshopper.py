# -*- coding: utf-8 -*-
"""
rhino_plugin/handlers/grasshopper.py
=====================================
Dispatcher-registered handlers for all Grasshopper operations.

These functions run **inside Rhino 3D** under Python 3.9. Each is registered
with the ``@handler`` decorator from ``rhino_plugin.dispatcher``.  The
dispatcher routes incoming JSON-RPC method calls to the appropriate function.

Supported methods
-----------------
  grasshopper.open_definition
  grasshopper.close_definition
  grasshopper.list_components
  grasshopper.get_param
  grasshopper.set_param
  grasshopper.recompute
  grasshopper.bake
  grasshopper.run_definition
  grasshopper.get_connections

Design notes
------------
* Python 3.9 compatible -- no ``match``/``case``, no ``X | Y`` union syntax,
  no lowercase ``dict[...]`` / ``list[...]`` runtime annotations.
* Zero external dependencies -- only Python stdlib plus Rhino/Grasshopper APIs.
* All Grasshopper API access is guarded by try/except; if GH is not loaded a
  clear error message is returned rather than raising.
* Handler functions accept a single ``params`` dict (the dispatcher contract).

Rhino / Grasshopper import pattern
-----------------------------------
The CLR references and GH imports are attempted at module load time.  If they
fail (e.g. when running outside Rhino for unit tests) ``_GH_AVAILABLE`` is
False and every handler returns an informative error immediately.

Author: GOLEM-3DMCP
"""

import traceback
try:
    from typing import Any, Dict, List, Optional
except ImportError:
    pass

from rhino_plugin.dispatcher import handler
from rhino_plugin.grasshopper.gh_handlers import (
    serialize_gh_component,
    serialize_gh_param,
    get_param_value,
    set_param_value,
    bake_component_output,
)

# ---------------------------------------------------------------------------
# Rhino / Grasshopper availability guard
# ---------------------------------------------------------------------------

_GH_AVAILABLE = False
_GH_IMPORT_ERROR = ""

try:
    import clr                                              # type: ignore
    clr.AddReference("Grasshopper")
    import Grasshopper                                      # type: ignore
    from Grasshopper.Kernel import GH_Document             # type: ignore
    from Grasshopper.Kernel.Special import GH_NumberSlider  # type: ignore
    import rhinoscriptsyntax as rs                         # type: ignore
    import scriptcontext as sc                             # type: ignore
    import Rhino                                           # type: ignore
    _GH_AVAILABLE = True
except Exception as _exc:
    _GH_IMPORT_ERROR = str(_exc)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_gh_doc():
    # type: () -> Any
    """
    Return the active Grasshopper GH_Document.

    Raises ValueError if Grasshopper is not open or no definition is loaded.
    """
    canvas = Grasshopper.Instances.ActiveCanvas
    if canvas is None:
        raise ValueError(
            "Grasshopper canvas is not open. "
            "Open Grasshopper first via the 'Grasshopper' command."
        )
    doc = canvas.Document
    if doc is None:
        raise ValueError(
            "No active Grasshopper definition. "
            "Open or create a .gh / .ghx file first."
        )
    return doc


def _ensure_gh_available():
    # type: () -> None
    """Raise RuntimeError if GH assemblies could not be loaded."""
    if not _GH_AVAILABLE:
        raise RuntimeError(
            "Grasshopper assemblies are not available in this environment. "
            "This handler must run inside Rhino 3D. "
            "Import error: {err}".format(err=_GH_IMPORT_ERROR)
        )


def _find_component(gh_doc, nickname=None, guid=None):
    # type: (Any, Optional[str], Optional[str]) -> Any
    """
    Locate a component in *gh_doc* by nickname or instance GUID string.

    Raises ValueError if no matching component is found.
    """
    for obj in gh_doc.Objects:
        if guid is not None and str(obj.InstanceGuid) == guid:
            return obj
        if nickname is not None and hasattr(obj, "NickName") and obj.NickName == nickname:
            return obj
    raise ValueError(
        "Component not found in active definition: {ident}".format(
            ident=nickname if nickname is not None else guid
        )
    )


def _try_open_grasshopper():
    # type: () -> None
    """Attempt to open the Grasshopper window via the Rhino command line."""
    try:
        rs.Command("_Grasshopper", echo=False)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Handler: open_definition
# ---------------------------------------------------------------------------

@handler("grasshopper.open_definition")
def gh_open_definition(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Open a .gh or .ghx file in Grasshopper.

    Parameters
    ----------
    file_path : str
        Absolute path to the .gh or .ghx file.

    Returns
    -------
    dict
        ``{"status": "opened", "file_path": <str>, "component_count": <int>}``
    """
    _ensure_gh_available()

    file_path = params.get("file_path")
    if not file_path:
        raise ValueError("'file_path' parameter is required.")

    # If canvas is not open yet, try launching Grasshopper.
    canvas = Grasshopper.Instances.ActiveCanvas
    if canvas is None:
        _try_open_grasshopper()
        import time
        time.sleep(1.5)  # Brief pause for GH window to initialise.
        canvas = Grasshopper.Instances.ActiveCanvas

    if canvas is None:
        raise RuntimeError(
            "Could not open Grasshopper. "
            "Please open Grasshopper manually and try again."
        )

    try:
        # GH_DocumentIO handles both .gh (binary) and .ghx (XML) formats.
        doc_io = Grasshopper.Kernel.GH_DocumentIO()
        ok = doc_io.Open(file_path)
        if not ok:
            raise RuntimeError(
                "GH_DocumentIO.Open() returned False for path: {p}".format(p=file_path)
            )
        new_doc = doc_io.Document
        if new_doc is None:
            raise RuntimeError("GH_DocumentIO produced a null document.")
        canvas.Document = new_doc
        canvas.Document.Enabled = True
        component_count = new_doc.ObjectCount
    except Exception as exc:
        raise RuntimeError(
            "Failed to open Grasshopper definition '{p}': {err}".format(
                p=file_path, err=exc
            )
        )

    return {
        "status": "opened",
        "file_path": file_path,
        "component_count": component_count,
    }


# ---------------------------------------------------------------------------
# Handler: close_definition
# ---------------------------------------------------------------------------

@handler("grasshopper.close_definition")
def gh_close_definition(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Close the currently active Grasshopper definition.

    Parameters
    ----------
    (none required)

    Returns
    -------
    dict
        ``{"status": "closed"}``
    """
    _ensure_gh_available()

    gh_doc = _get_gh_doc()
    try:
        gh_doc.Enabled = False
        gh_doc.Clear()
        canvas = Grasshopper.Instances.ActiveCanvas
        if canvas is not None:
            canvas.Document = None
    except Exception as exc:
        raise RuntimeError("Failed to close Grasshopper definition: {err}".format(err=exc))

    return {"status": "closed"}


# ---------------------------------------------------------------------------
# Handler: list_components
# ---------------------------------------------------------------------------

@handler("grasshopper.list_components")
def gh_list_components(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Return a description of every component in the active definition.

    Parameters
    ----------
    (none required)

    Returns
    -------
    dict
        ``{"components": [<component_dict>, ...]}``

    Each component dict is produced by
    :func:`~rhino_plugin.grasshopper.gh_handlers.serialize_gh_component`.
    """
    _ensure_gh_available()

    gh_doc = _get_gh_doc()
    components = []  # type: List[Dict[str, Any]]
    for obj in gh_doc.Objects:
        try:
            components.append(serialize_gh_component(obj))
        except Exception:
            # Skip components that cannot be serialised rather than aborting.
            pass

    return {"components": components}


# ---------------------------------------------------------------------------
# Handler: get_param
# ---------------------------------------------------------------------------

@handler("grasshopper.get_param")
def gh_get_param(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Read the current value of a Grasshopper parameter component.

    Parameters
    ----------
    component_nickname : str, optional
        NickName of the component (e.g. ``"MySlider"``).
    component_guid : str, optional
        Instance GUID string of the component.

    Exactly one of the two must be supplied.

    Returns
    -------
    dict
        For sliders:  ``{"type": "slider", "value": <float>, "min": <float>, "max": <float>, "slider_type": <str>}``
        For panels:   ``{"type": "panel", "value": <str>}``
        For toggles:  ``{"type": "toggle", "value": <bool>}``
        For numbers:  ``{"type": "number", "value": <float>}``
        Generic:      ``{"type": "param", "value": <any>}``
    """
    _ensure_gh_available()

    nickname = params.get("component_nickname")
    guid = params.get("component_guid")
    if not nickname and not guid:
        raise ValueError(
            "Either 'component_nickname' or 'component_guid' must be supplied."
        )

    gh_doc = _get_gh_doc()
    component = _find_component(gh_doc, nickname=nickname, guid=guid)

    # Serialise the single component and extract its param value.
    return serialize_gh_param(component)


# ---------------------------------------------------------------------------
# Handler: set_param
# ---------------------------------------------------------------------------

@handler("grasshopper.set_param")
def gh_set_param(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Set the value of a Grasshopper parameter component and expire the solution.

    Parameters
    ----------
    component_nickname : str, optional
        NickName of the target component.
    component_guid : str, optional
        Instance GUID string of the target component.
    value : any
        New value.  The handler inspects the component type and applies the
        correct setter (slider float, toggle bool, panel string, etc.).

    Returns
    -------
    dict
        ``{"status": "set", "component": <str>, "value": <any>}``
    """
    _ensure_gh_available()

    nickname = params.get("component_nickname")
    guid = params.get("component_guid")
    if not nickname and not guid:
        raise ValueError(
            "Either 'component_nickname' or 'component_guid' must be supplied."
        )
    if "value" not in params:
        raise ValueError("'value' parameter is required.")

    value = params["value"]
    gh_doc = _get_gh_doc()
    component = _find_component(gh_doc, nickname=nickname, guid=guid)

    set_param_value(component, None, value)

    # Expire the downstream solution so Grasshopper recomputes.
    try:
        component.ExpireSolution(True)
    except Exception:
        pass

    return {
        "status": "set",
        "component": nickname if nickname is not None else guid,
        "value": value,
    }


# ---------------------------------------------------------------------------
# Handler: recompute
# ---------------------------------------------------------------------------

@handler("grasshopper.recompute")
def gh_recompute(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Force a full recompute of the active Grasshopper definition.

    Parameters
    ----------
    (none required)

    Returns
    -------
    dict
        ``{"status": "ok", "solution_state": <str>}``
    """
    _ensure_gh_available()

    gh_doc = _get_gh_doc()
    try:
        gh_doc.NewSolution(True)
        solution_state = str(gh_doc.SolutionState)
    except Exception as exc:
        raise RuntimeError("Recompute failed: {err}".format(err=exc))

    return {"status": "ok", "solution_state": solution_state}


# ---------------------------------------------------------------------------
# Handler: bake
# ---------------------------------------------------------------------------

@handler("grasshopper.bake")
def gh_bake(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Bake geometry from Grasshopper output components into the Rhino document.

    Parameters
    ----------
    component_nickname : str, optional
        Bake only the outputs of this component.
    component_guid : str, optional
        Bake only the outputs of the component with this GUID.
    layer : str, optional
        Target Rhino layer name.  Created if it does not exist.

    If neither ``component_nickname`` nor ``component_guid`` is given, all
    components in the definition are baked.

    Returns
    -------
    dict
        ``{"baked_guids": [<str>, ...], "count": <int>}``
    """
    _ensure_gh_available()

    nickname = params.get("component_nickname")
    guid = params.get("component_guid")
    layer = params.get("layer")

    gh_doc = _get_gh_doc()
    rhino_doc = sc.doc

    baked_guids = []  # type: List[str]

    if nickname or guid:
        component = _find_component(gh_doc, nickname=nickname, guid=guid)
        baked_guids.extend(bake_component_output(component, rhino_doc, layer=layer))
    else:
        for obj in gh_doc.Objects:
            try:
                guids = bake_component_output(obj, rhino_doc, layer=layer)
                baked_guids.extend(guids)
            except Exception:
                pass

    rhino_doc.Views.Redraw()

    return {"baked_guids": baked_guids, "count": len(baked_guids)}


# ---------------------------------------------------------------------------
# Handler: run_definition
# ---------------------------------------------------------------------------

@handler("grasshopper.run_definition")
def gh_run_definition(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Open a definition (or use the active one), set inputs, compute, and return
    output geometry summaries.

    Parameters
    ----------
    file_path : str, optional
        Path to a .gh / .ghx file to open before running.  If omitted the
        currently active definition is used.
    inputs : dict, optional
        Mapping of ``component_nickname`` -> value to set before computing.
    bake : bool, optional
        If True, bake all output geometry into the Rhino document (default False).
    layer : str, optional
        Layer to bake onto (only used when ``bake`` is True).

    Returns
    -------
    dict
        ``{"status": "ok", "outputs": {nickname: <value>}, "baked_guids": [...]}``
    """
    _ensure_gh_available()

    file_path = params.get("file_path")
    inputs = params.get("inputs") or {}
    do_bake = bool(params.get("bake", False))
    layer = params.get("layer")

    # Optionally open a definition first.
    if file_path:
        gh_open_definition({"file_path": file_path})

    gh_doc = _get_gh_doc()

    # Apply inputs.
    for component_name, value in inputs.items():
        try:
            component = _find_component(gh_doc, nickname=component_name)
            set_param_value(component, None, value)
            component.ExpireSolution(True)
        except Exception as exc:
            # Non-fatal: log and continue so other inputs are still applied.
            pass

    # Recompute.
    try:
        gh_doc.NewSolution(True)
    except Exception as exc:
        raise RuntimeError("Solution failed during run_definition: {err}".format(err=exc))

    # Collect outputs.
    outputs = {}  # type: Dict[str, Any]
    for obj in gh_doc.Objects:
        try:
            nick = getattr(obj, "NickName", None)
            if nick and hasattr(obj, "Params") and hasattr(obj.Params, "Output"):
                for out_param in obj.Params.Output:
                    try:
                        val = get_param_value(out_param)
                        key = "{nick}.{pname}".format(
                            nick=nick, pname=getattr(out_param, "NickName", "out")
                        )
                        outputs[key] = val
                    except Exception:
                        pass
        except Exception:
            pass

    baked_guids = []  # type: List[str]
    if do_bake:
        bake_result = gh_bake({"layer": layer})
        baked_guids = bake_result.get("baked_guids", [])

    return {
        "status": "ok",
        "outputs": outputs,
        "baked_guids": baked_guids,
    }


# ---------------------------------------------------------------------------
# Handler: get_connections
# ---------------------------------------------------------------------------

@handler("grasshopper.get_connections")
def gh_get_connections(params):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Return the wire (connection) graph of the active definition.

    Parameters
    ----------
    (none required)

    Returns
    -------
    dict
        ``{"connections": [<connection_dict>, ...]}``

    Each connection dict has the shape::

        {
            "source_component":  <str>,   // NickName of the source component
            "source_param":      <str>,   // NickName of the source output param
            "target_component":  <str>,   // NickName of the target component
            "target_param":      <str>,   // NickName of the target input param
        }
    """
    _ensure_gh_available()

    gh_doc = _get_gh_doc()
    connections = []  # type: List[Dict[str, str]]

    # Build a GUID -> NickName lookup for fast reverse resolution.
    guid_to_nick = {}  # type: Dict[str, str]
    for obj in gh_doc.Objects:
        try:
            g = str(obj.InstanceGuid)
            nick = getattr(obj, "NickName", str(g))
            guid_to_nick[g] = nick
        except Exception:
            pass

    for obj in gh_doc.Objects:
        try:
            source_nick = getattr(obj, "NickName", str(obj.InstanceGuid))
            if not hasattr(obj, "Params") or not hasattr(obj.Params, "Output"):
                continue
            for out_param in obj.Params.Output:
                try:
                    out_param_nick = getattr(out_param, "NickName", "out")
                    for recipient in out_param.Recipients:
                        try:
                            # Recipient is an input IGH_Param whose owner is the target component.
                            target_obj = recipient.Attributes.GetTopLevel.DocObject
                            target_nick = getattr(
                                target_obj, "NickName", str(target_obj.InstanceGuid)
                            )
                            target_param_nick = getattr(recipient, "NickName", "in")
                            connections.append({
                                "source_component": source_nick,
                                "source_param":     out_param_nick,
                                "target_component": target_nick,
                                "target_param":     target_param_nick,
                            })
                        except Exception:
                            pass
                except Exception:
                    pass
        except Exception:
            pass

    return {"connections": connections}
