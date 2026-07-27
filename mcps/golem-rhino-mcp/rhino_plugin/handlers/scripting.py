# -*- coding: utf-8 -*-
"""
rhino_plugin/handlers/scripting.py
=====================================
Handler functions for arbitrary script execution inside Rhino 3D.

Registered methods (dispatched via rhino_plugin.dispatcher):
  - scripting.execute_python
  - scripting.execute_rhinocommand
  - scripting.evaluate_expression
  - scripting.run_rhino_script

Design notes
------------
* Python 3.9 compatible -- no match/case, no X | Y union syntax.
* Zero external dependencies -- only Python stdlib, RhinoCommon,
  rhinoscriptsyntax, and System (all available inside Rhino's runtime).
* ``execute_python`` is an UNRESTRICTED execution environment.  It is
  intended as an escape hatch for operations not yet covered by dedicated
  handlers.  Only invoke it with code you trust.
* The ``__result__`` convention: if the executed code sets
  ``__result__ = <value>``, that value is serialised and returned in the
  ``result`` field of the response.  This allows structured return values
  from otherwise imperative scripts.
* Output capture uses ``io.StringIO`` + ``contextlib.redirect_stdout /
  redirect_stderr``; this captures ``print()`` calls from the guest code.
  Native Rhino output (RhinoApp.WriteLine) is NOT captured -- it goes to
  the Rhino command history window instead.
"""

import io
import contextlib
try:
    from typing import Any, Optional
except ImportError:
    pass

# These imports are only available inside the Rhino Python environment.
# The try/except lets linters and unit-test runners import the module without
# exploding; at runtime inside Rhino they will always succeed.
try:
    import Rhino                              # type: ignore
    import scriptcontext as sc                # type: ignore
    import rhinoscriptsyntax as rs            # type: ignore
    import System                             # type: ignore
    _RHINO_AVAILABLE = True
except ImportError:
    _RHINO_AVAILABLE = False
    # Provide stubs so the module can at least be imported outside Rhino.
    Rhino = None    # type: ignore
    sc = None       # type: ignore
    rs = None       # type: ignore
    System = None   # type: ignore

from rhino_plugin.dispatcher import handler  # noqa: E402
from rhino_plugin.utils.geometry_serializer import serialize_any  # noqa: E402


# ---------------------------------------------------------------------------
# Serialisation helper
# ---------------------------------------------------------------------------

def try_serialize(obj):
    # type: (Any) -> Any
    """
    Convert *obj* to a JSON-serialisable value as best we can.

    Conversion rules (in priority order):
    1. ``None``                        → ``None``
    2. ``str | int | float | bool``   → returned as-is
    3. ``list``                        → each element recursively serialised
    4. ``dict``                        → each value recursively serialised
    5. ``System.Guid``                 → ``str(obj)``
    6. Rhino geometry (GeometryBase)  → ``serialize_any(obj)``
    7. Anything else                   → ``str(obj)``
    """
    if obj is None:
        return None

    # Primitive pass-throughs.
    if isinstance(obj, (bool, int, float, str)):
        return obj

    # Recursive collection handling.
    if isinstance(obj, list):
        return [try_serialize(item) for item in obj]

    if isinstance(obj, dict):
        return {str(k): try_serialize(v) for k, v in obj.items()}

    # Rhino / .NET types (only reachable inside Rhino).
    if _RHINO_AVAILABLE:
        try:
            if isinstance(obj, System.Guid):
                return str(obj)
        except Exception:
            pass

        try:
            import Rhino.Geometry as RG
            if isinstance(obj, RG.GeometryBase):
                return serialize_any(obj)
        except Exception:
            pass

    # Final fallback -- stringify whatever we got.
    try:
        return str(obj)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Execution namespace builder
# ---------------------------------------------------------------------------

def _build_namespace(extra=None):
    # type: (Optional[dict]) -> dict
    """
    Build the global namespace injected into ``exec`` / ``eval`` calls.

    Always includes: ``rs``, ``sc``, ``Rhino``, ``System``,
    ``__builtins__``, and ``__result__`` (initialised to ``None``).
    Any keys in *extra* are merged on top.
    """
    namespace = {
        "rs": rs,
        "sc": sc,
        "Rhino": Rhino,
        "System": System,
        "__builtins__": __builtins__,
        "__result__": None,
    }  # type: dict
    if extra:
        namespace.update(extra)
    return namespace


# ---------------------------------------------------------------------------
# handlers
# ---------------------------------------------------------------------------

@handler("scripting.execute_python")
def handle_execute_python(params):
    # type: (dict) -> dict
    """
    Execute arbitrary Python code inside Rhino's Python 3.9 runtime.

    The code has full access to:
    - ``rs``     -- rhinoscriptsyntax
    - ``sc``     -- scriptcontext (sc.doc is the active document)
    - ``Rhino``  -- RhinoCommon API
    - ``System`` -- .NET System namespace
    - All Python builtins

    The special variable ``__result__`` can be set inside the code to
    communicate a structured return value back to the caller::

        __result__ = rs.ObjectLayer("some-guid")

    The value of ``__result__`` after execution is serialised via
    ``try_serialize`` and returned in the ``result`` field.

    Parameters
    ----------
    params : dict
        ``code``    (str, required)           -- Python source code to run.
        ``context`` (dict, optional)          -- Extra variables to inject into
                                                the execution namespace.
        ``timeout`` (int, optional, default 30) -- Ignored in this
                                                synchronous implementation
                                                (present for API compatibility
                                                with the MCP tool signature).

    Returns
    -------
    dict
        ``success`` -- True if no exception was raised.
        ``stdout``  -- Captured print() output.
        ``stderr``  -- Exception message (if success=False), else "".
        ``result``  -- Serialised value of ``__result__``, or None.
    """
    code = params.get("code", "")
    if not code or not code.strip():
        raise ValueError("params['code'] is required and must not be empty")

    extra_context = params.get("context") or {}
    namespace = _build_namespace(extra=extra_context)

    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()

    try:
        with contextlib.redirect_stdout(stdout_capture), \
             contextlib.redirect_stderr(stderr_capture):
            exec(code, namespace)  # noqa: S102 -- intentional escape hatch
    except Exception as exc:
        return {
            "success": False,
            "stdout": stdout_capture.getvalue(),
            "stderr": str(exc),
            "result": None,
        }

    result_value = namespace.get("__result__")
    serialised = try_serialize(result_value)

    return {
        "success": True,
        "stdout": stdout_capture.getvalue(),
        "stderr": stderr_capture.getvalue(),
        "result": serialised,
    }


@handler("scripting.execute_rhinocommand")
def handle_execute_rhinocommand(params):
    # type: (dict) -> dict
    """
    Run a Rhino command string exactly as if typed at the command line.

    This provides access to ALL Rhino commands, including those not yet
    exposed as dedicated handler methods.  Use underscore prefixes for
    locale-independent command names (e.g. ``_Move`` instead of ``Move``).

    Parameters
    ----------
    params : dict
        ``command`` (str, required) -- The Rhino command string.  Can include
            options separated by spaces or newlines.
            Example: ``"_Line 0,0,0 10,10,0"``
        ``echo``    (bool, optional, default False) -- Echo the command to the
            Rhino command history window.

    Returns
    -------
    dict
        ``success``        -- True if rs.Command() returned without raising.
        ``command``        -- The command string that was executed.
        ``command_result`` -- The integer return code from rs.Command(), or
                             None if it could not be retrieved.

    Example
    -------
    ``execute_rhinocommand({"command": "_-Export \\"/tmp/model.obj\\" _Enter"})``
    """
    command = params.get("command", "")
    if not command or not command.strip():
        raise ValueError("params['command'] is required and must not be empty")

    echo = params.get("echo", False)

    command_result = None  # type: Optional[int]
    try:
        command_result = rs.Command(command, echo=echo)
    except Exception as exc:
        return {
            "success": False,
            "command": str(command),
            "command_result": None,
            "error": str(exc),
        }

    # rs.Command returns True/1 on success, False/0 on failure in most cases.
    success = bool(command_result) if command_result is not None else True

    return {
        "success": success,
        "command": str(command),
        "command_result": command_result,
    }


@handler("scripting.evaluate_expression")
def handle_evaluate_expression(params):
    # type: (dict) -> dict
    """
    Evaluate a single Python expression and return its value.

    Uses ``eval()`` rather than ``exec()``, so only expressions are
    accepted -- not statements.  This is useful for quick property
    queries and calculations without needing a full ``execute_python``
    call.

    The expression has access to the same namespace as ``execute_python``
    (rs, sc, Rhino, System) plus any variables passed via ``variables``.

    Parameters
    ----------
    params : dict
        ``expression`` (str, required)  -- A single Python expression.
            Example: ``"rs.ObjectLayer('guid-here')"``
        ``variables``  (dict, optional) -- Extra variables available during
            evaluation.
            Example: ``{"x": 3.0, "y": 4.0}``

    Returns
    -------
    dict
        ``success``    -- True if no exception was raised.
        ``value``      -- Serialised result of the expression, or None.
        ``type``       -- Python type name of the raw result (e.g. "str").
        ``error``      -- Exception message if success=False, else None.

    Example
    -------
    ``evaluate_expression({"expression": "sc.doc.Objects.Count"})``
    ``evaluate_expression({"expression": "x ** 2 + y ** 2",
                           "variables": {"x": 3.0, "y": 4.0}})``
    """
    expression = params.get("expression", "")
    if not expression or not expression.strip():
        raise ValueError("params['expression'] is required and must not be empty")

    variables = params.get("variables") or {}
    namespace = _build_namespace(extra=variables)

    try:
        raw = eval(expression, namespace)  # noqa: S307 -- intentional escape hatch
    except Exception as exc:
        return {
            "success": False,
            "value": None,
            "type": None,
            "error": str(exc),
        }

    type_name = type(raw).__name__
    serialised = try_serialize(raw)

    return {
        "success": True,
        "value": serialised,
        "type": str(type_name),
        "error": None,
    }


@handler("scripting.run_rhino_script")
def handle_run_rhino_script(params):
    # type: (dict) -> dict
    """
    Execute a Python script file inside Rhino's Python runtime.

    The file is read from disk and executed via ``exec()`` in the same
    enriched namespace used by ``execute_python`` (rs, sc, Rhino, System).
    The ``__result__`` convention is supported here too.

    Parameters
    ----------
    params : dict
        ``file_path`` (str, required) -- Absolute path to a ``.py`` script
            file on the local filesystem.

    Returns
    -------
    dict
        ``success``    -- True if no exception was raised.
        ``file_path``  -- The path of the script that was run.
        ``stdout``     -- Captured print() output from the script.
        ``stderr``     -- Exception message (if success=False), else "".
        ``result``     -- Serialised value of ``__result__``, or None.

    Notes
    -----
    The file must be readable from inside Rhino's Python process.  Network
    paths and paths inside application bundles may not be accessible.
    """
    import os

    file_path = params.get("file_path", "")
    if not file_path or not file_path.strip():
        raise ValueError("params['file_path'] is required for scripting.run_rhino_script")

    if not os.path.isfile(file_path):
        raise ValueError(
            "Script file not found: {path}".format(path=file_path)
        )

    try:
        with open(file_path, "r", encoding="utf-8") as fh:
            code = fh.read()
    except Exception as exc:
        raise ValueError(
            "Could not read script file {path}: {exc}".format(
                path=file_path, exc=exc
            )
        )

    if not code.strip():
        raise ValueError(
            "Script file is empty: {path}".format(path=file_path)
        )

    namespace = _build_namespace()
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()

    try:
        with contextlib.redirect_stdout(stdout_capture), \
             contextlib.redirect_stderr(stderr_capture):
            exec(code, namespace)  # noqa: S102 -- intentional escape hatch
    except Exception as exc:
        return {
            "success": False,
            "file_path": str(file_path),
            "stdout": stdout_capture.getvalue(),
            "stderr": str(exc),
            "result": None,
        }

    result_value = namespace.get("__result__")
    serialised = try_serialize(result_value)

    return {
        "success": True,
        "file_path": str(file_path),
        "stdout": stdout_capture.getvalue(),
        "stderr": stderr_capture.getvalue(),
        "result": serialised,
    }
