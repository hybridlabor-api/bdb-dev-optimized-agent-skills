"""
golem_3dmcp/tools/scripting.py
===============================
MCP tools for executing arbitrary Python and RhinoScript code inside Rhino.

Registered tools:
  - execute_python
  - execute_rhinoscript
  - evaluate_expression
  - run_rhino_command
"""

from __future__ import annotations

from typing import Any

from golem_3dmcp.connection import get_connection
from golem_3dmcp.server import mcp


def _send(method: str, params: dict[str, Any]) -> dict[str, Any]:
    return get_connection().send_command(method, params)


# ---------------------------------------------------------------------------
# Python execution
# ---------------------------------------------------------------------------

@mcp.tool()
def execute_python(
    code: str,
    context: dict[str, Any] | None = None,
    timeout_seconds: int = 30,
    capture_output: bool = True,
) -> dict[str, Any]:
    """
    Execute arbitrary Python code inside Rhino's Python runtime.

    The code runs with full access to RhinoCommon (``import Rhino``),
    scriptcontext (``import scriptcontext as sc``), rhinoscriptsyntax
    (``import rhinoscriptsyntax as rs``), and System (``import System``).

    IMPORTANT: This is an unrestricted execution environment.  Only use
    it with code you trust.

    The execution context has a pre-populated ``_output`` dict that the code
    can populate with return values:
        _output["result"] = my_computed_value

    Args:
        code:            Python source code to execute.
        context:         Optional dict of variables to inject into the
                         execution namespace before running the code.
        timeout_seconds: Maximum execution time in seconds.
        capture_output:  Capture print() output and return it in the
                         'stdout' field if True.

    Returns:
        dict with:
          'success'  — True if no exception was raised
          'output'   — the '_output' dict populated by the code
          'stdout'   — captured print output (if capture_output=True)
          'error'    — exception message if success=False
          'traceback'— full traceback if success=False

    Example::

        execute_python(
            code='''
    import Rhino.Geometry as RG
    sphere = RG.Sphere(RG.Point3d(0, 0, 0), 5.0)
    brep = sphere.ToBrep()
    obj_id = scriptcontext.doc.Objects.AddBrep(brep)
    scriptcontext.doc.Views.Redraw()
    _output["guid"] = str(obj_id)
    '''
        )
    """
    return _send("scripting.execute_python", {
        "code": code,
        "context": context or {},
        "timeout_seconds": timeout_seconds,
        "capture_output": capture_output,
    })


# ---------------------------------------------------------------------------
# RhinoScript execution
# ---------------------------------------------------------------------------

@mcp.tool()
def execute_rhinoscript(
    code: str,
    timeout_seconds: int = 30,
) -> dict[str, Any]:
    """
    Execute RhinoScript (VBScript) code inside Rhino.

    RhinoScript is Rhino's legacy scripting language.  It is still fully
    supported and many existing automation scripts are written in it.

    Args:
        code:            VBScript source code to execute.
        timeout_seconds: Maximum execution time.

    Returns:
        dict with 'success', 'error' (if any), and 'result'.
    """
    return _send("scripting.execute_rhinoscript", {
        "code": code,
        "timeout_seconds": timeout_seconds,
    })


# ---------------------------------------------------------------------------
# Expression evaluation
# ---------------------------------------------------------------------------

@mcp.tool()
def evaluate_expression(
    expression: str,
    variables: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Evaluate a single Python expression and return its value.

    The expression has access to math functions, Rhino geometry classes,
    and any variables passed via the ``variables`` argument.

    Args:
        expression: A single Python expression (not a statement).
                    Example: "math.sqrt(x**2 + y**2 + z**2)"
        variables:  Dict of variable names and values available in the
                    expression context.
                    Example: {"x": 3.0, "y": 4.0, "z": 0.0}

    Returns:
        dict with 'value' (the evaluated result) and 'type' (its Python type name).
    """
    return _send("scripting.evaluate_expression", {
        "expression": expression,
        "variables": variables or {},
    })


# ---------------------------------------------------------------------------
# Rhino command execution
# ---------------------------------------------------------------------------

@mcp.tool()
def run_rhino_command(
    command: str,
    echo: bool = False,
) -> dict[str, Any]:
    """
    Run a Rhino command string exactly as if typed into the command line.

    This provides access to ALL Rhino commands, including those not yet
    exposed as dedicated MCP tools.

    Command syntax is identical to the Rhino command line.  Use underscore
    prefixes for locale-independent commands (e.g. "_Move" instead of "Move").

    Args:
        command: The Rhino command string.  Can include command options
                 separated by spaces or newlines.
                 Example: "_-Export /Users/me/model.obj _Enter"
        echo:    Echo the command to the Rhino command history window if True.

    Returns:
        dict with 'success' and 'command_result' (Rhino's return code).
    """
    return _send("scripting.run_rhino_command", {
        "command": command,
        "echo": echo,
    })
