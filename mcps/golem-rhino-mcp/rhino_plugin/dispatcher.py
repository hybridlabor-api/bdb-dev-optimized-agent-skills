# -*- coding: utf-8 -*-
"""
rhino_plugin/dispatcher.py
==========================
Central command router for GOLEM-3DMCP.

Maintains a handler registry that maps JSON-RPC-style method name strings to
callable functions.  Functions are registered with the ``@handler`` decorator
or discovered automatically via :func:`register_handlers_from_module`.

Design notes
------------
* Python 3.9 compatible -- no ``match``/``case``, no ``X | Y`` union syntax,
  no ``dict[str, ...]`` lowercase generics in runtime annotations.
* Zero external dependencies -- only Python stdlib.
* Every public function that touches the registry is thread-safe enough for
  Rhino's single-threaded Python environment; a real lock can be added if
  Rhino ever exposes multi-threaded execution contexts.
"""

import traceback
try:
    from typing import Any, Callable, Dict, List, Optional
except ImportError:
    pass


# ---------------------------------------------------------------------------
# Error codes
# ---------------------------------------------------------------------------

class ErrorCode:
    OK = "OK"
    INVALID_PARAMS = "INVALID_PARAMS"
    OBJECT_NOT_FOUND = "OBJECT_NOT_FOUND"
    OPERATION_FAILED = "OPERATION_FAILED"
    TIMEOUT = "TIMEOUT"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    NOT_FOUND = "NOT_FOUND"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"


# ---------------------------------------------------------------------------
# Handler registry
# ---------------------------------------------------------------------------

_handlers = {}  # type: Dict[str, Callable]


def handler(name):
    # type: (str) -> Callable
    """
    Decorator that registers a function as the handler for *name*.

    Usage::

        @handler("geometry.create_sphere")
        def create_sphere(params):
            ...

    The function is stored in the module-level ``_handlers`` dict and also
    tagged with a ``_handler_name`` attribute so that
    :func:`register_handlers_from_module` can discover it later.
    """
    def decorator(fn):
        # type: (Callable) -> Callable
        fn._handler_name = name
        _handlers[name] = fn
        return fn
    return decorator


def register_handlers_from_module(module):
    # type: (Any) -> List[str]
    """
    Scan *module* for functions that carry a ``_handler_name`` attribute and
    register each one in the global ``_handlers`` dict.

    This allows handler modules to be imported lazily and registered in bulk
    rather than having each module import ``dispatcher`` at definition time.

    Returns
    -------
    list[str]
        The list of method names that were newly registered from this module.
    """
    registered = []
    for attr_name in dir(module):
        obj = getattr(module, attr_name)
        if callable(obj) and hasattr(obj, "_handler_name"):
            method_name = obj._handler_name
            _handlers[method_name] = obj
            registered.append(method_name)
    return registered


def get_registered_methods():
    # type: () -> List[str]
    """Return a sorted list of all currently registered method names."""
    return sorted(_handlers.keys())


# ---------------------------------------------------------------------------
# Response format helpers
# ---------------------------------------------------------------------------

def success_response(id, result):
    # type: (Any, Any) -> Dict[str, Any]
    """
    Build a JSON-RPC-style success envelope.

    Parameters
    ----------
    id:
        The request identifier (string, int, or None) echoed back to the
        caller so it can correlate the response to its request.
    result:
        Any JSON-serialisable value returned by the handler.
    """
    return {
        "jsonrpc": "2.0",
        "id": id,
        "result": result,
    }


def error_response(id, code, message, details=None):
    # type: (Any, str, str, Optional[Any]) -> Dict[str, Any]
    """
    Build a JSON-RPC-style error envelope.

    Parameters
    ----------
    id:
        The request identifier echoed back to the caller.
    code:
        One of the :class:`ErrorCode` constants, e.g. ``ErrorCode.NOT_FOUND``.
    message:
        Human-readable description of the error.
    details:
        Optional extra context (stack trace, invalid field name, etc.).
    """
    error_body = {
        "code": code,
        "message": message,
    }
    if details is not None:
        error_body["details"] = details
    return {
        "jsonrpc": "2.0",
        "id": id,
        "error": error_body,
    }


# ---------------------------------------------------------------------------
# Main dispatch entry point
# ---------------------------------------------------------------------------

def dispatch(method, params, request_id=None):
    # type: (str, Dict[str, Any], Any) -> Dict[str, Any]
    """
    Route *method* to its registered handler and return a response dict.

    The caller is responsible for passing any ``id`` from the original
    JSON-RPC request so that :func:`success_response` / :func:`error_response`
    can echo it back.

    Parameters
    ----------
    method:
        The dot-namespaced method name, e.g. ``"geometry.create_box"``.
    params:
        Keyword-style parameter dict passed directly to the handler.
    request_id:
        Optional JSON-RPC request identifier.

    Returns
    -------
    dict
        Always returns a dict with either a ``"result"`` key (success) or an
        ``"error"`` key (failure).  Never raises.
    """
    if method not in _handlers:
        return error_response(
            request_id,
            ErrorCode.NOT_FOUND,
            "Method not found: {method}".format(method=method),
            details={"available_methods": get_registered_methods()},
        )

    fn = _handlers[method]

    try:
        result = fn(params)
        return success_response(request_id, result)

    except NotImplementedError as exc:
        return error_response(
            request_id,
            ErrorCode.NOT_IMPLEMENTED,
            str(exc) or "Method not implemented: {method}".format(method=method),
        )

    except (ValueError, TypeError, KeyError) as exc:
        # Surface parameter validation errors without a full traceback in the
        # message -- callers receive enough information to fix their input.
        return error_response(
            request_id,
            ErrorCode.INVALID_PARAMS,
            str(exc),
            details={"method": method},
        )

    except Exception as exc:  # pylint: disable=broad-except
        tb = traceback.format_exc()
        return error_response(
            request_id,
            ErrorCode.INTERNAL_ERROR,
            "Unhandled exception in handler '{method}': {exc}".format(
                method=method, exc=repr(exc)
            ),
            details={"traceback": tb},
        )
