# -*- coding: utf-8 -*-
"""
rhino_plugin/utils/error_handler.py
=====================================
Standardised error codes, helpers, and a decorator for converting Python
exceptions into structured GOLEM error dicts.

Design notes
------------
* Python 3.9 compatible -- no ``match``/``case``, no ``X | Y`` union syntax.
* Zero external dependencies -- only Python stdlib.
* :func:`wrap_handler` is intended to wrap individual handler functions
  **before** they are registered in the dispatcher so that every handler
  automatically produces consistent error responses without boilerplate.

Error dict schema::

    {
        "code":    str,          # one of the ErrorCode constants
        "message": str,          # human-readable description
        "details": Any | None,   # optional extra context (traceback, etc.)
    }
"""

import functools
import traceback
try:
    from typing import Any, Callable, Dict, Optional
except ImportError:
    pass


# ---------------------------------------------------------------------------
# Error code constants
# ---------------------------------------------------------------------------

class ErrorCode:
    """Namespace for GOLEM-3DMCP error code constants."""

    INVALID_PARAMS = "INVALID_PARAMS"
    """A required parameter was missing, wrong type, or out of range."""

    OBJECT_NOT_FOUND = "OBJECT_NOT_FOUND"
    """A referenced Rhino object (by GUID or name) does not exist."""

    OPERATION_FAILED = "OPERATION_FAILED"
    """The Rhino geometry operation returned ``False`` or ``None``."""

    TIMEOUT = "TIMEOUT"
    """The operation exceeded its time budget."""

    INTERNAL_ERROR = "INTERNAL_ERROR"
    """An unexpected exception occurred inside a handler."""

    NOT_FOUND = "NOT_FOUND"
    """The requested MCP method/tool name is not registered."""

    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"
    """The method is known but has not been implemented yet."""


# ---------------------------------------------------------------------------
# Custom exception
# ---------------------------------------------------------------------------

class GolemError(Exception):
    """
    Application-level exception that carries a structured GOLEM error code.

    Raising a ``GolemError`` inside a handler decorated with
    :func:`wrap_handler` will produce a clean error response without
    emitting a full stack trace to the caller.

    Example::

        raise GolemError(ErrorCode.OPERATION_FAILED, "BooleanUnion returned None")
    """

    def __init__(self, code, message, details=None):
        # type: (str, str, Optional[Any]) -> None
        super(GolemError, self).__init__(message)
        self.code = code
        self.message = message
        self.details = details

    def to_dict(self):
        # type: () -> Dict[str, Any]
        """Serialise to the standard GOLEM error dict."""
        return make_error(self.code, self.message, self.details)


# ---------------------------------------------------------------------------
# Error dict factory
# ---------------------------------------------------------------------------

def make_error(code, message, details=None):
    # type: (str, str, Optional[Any]) -> Dict[str, Any]
    """
    Create a standardised GOLEM error dict.

    Parameters
    ----------
    code:
        One of the :class:`ErrorCode` constants.
    message:
        Human-readable description of the error.
    details:
        Optional extra context -- a stack trace string, a field name, the
        invalid value, etc.  Must be JSON-serialisable.

    Returns
    -------
    dict
        ``{"code": ..., "message": ..., "details": ...}``
    """
    result = {
        "code": code,
        "message": message,
    }
    if details is not None:
        result["details"] = details
    return result


# ---------------------------------------------------------------------------
# Handler decorator
# ---------------------------------------------------------------------------

def wrap_handler(fn):
    # type: (Callable) -> Callable
    """
    Decorator that catches common exceptions from *fn* and returns a
    structured GOLEM error dict instead of propagating the exception.

    Exception-to-error-code mapping:

    ==================== ==========================
    Exception type        Error code
    ==================== ==========================
    ``GolemError``        ``error.code`` (passthrough)
    ``ValueError``        ``INVALID_PARAMS``
    ``TypeError``         ``INVALID_PARAMS``
    ``KeyError`` (*)      ``OBJECT_NOT_FOUND`` if ``"not found"`` appears in
                          the message; otherwise ``INVALID_PARAMS``
    ``TimeoutError``      ``TIMEOUT``
    ``NotImplementedError`` ``NOT_IMPLEMENTED``
    Any other ``Exception`` ``INTERNAL_ERROR`` (includes traceback)
    ==================== ==========================

    (*) ``KeyError`` is used by :meth:`GuidRegistry.validate_guid` to signal
    that a GUID does not exist in the Rhino document.

    The wrapped function preserves its original ``__name__`` and
    ``__doc__`` attributes (via ``functools.wraps``) and also keeps any
    ``_handler_name`` tag so that the dispatcher can still discover it.

    Usage::

        @wrap_handler
        @handler("geometry.create_box")
        def create_box(params):
            ...

        # Or equivalently, applied during registration:
        handler("geometry.create_box")(wrap_handler(create_box))
    """

    @functools.wraps(fn)
    def wrapper(params):
        # type: (Dict[str, Any]) -> Any
        try:
            return fn(params)

        except GolemError as exc:
            return exc.to_dict()

        except (ValueError, TypeError) as exc:
            return make_error(
                ErrorCode.INVALID_PARAMS,
                str(exc),
                details={"exception_type": type(exc).__name__},
            )

        except KeyError as exc:
            msg = str(exc).strip("'\"")
            if "not found" in msg.lower():
                return make_error(ErrorCode.OBJECT_NOT_FOUND, msg)
            return make_error(
                ErrorCode.INVALID_PARAMS,
                "Missing or invalid key: {msg}".format(msg=msg),
                details={"exception_type": "KeyError"},
            )

        except TimeoutError as exc:
            return make_error(
                ErrorCode.TIMEOUT,
                str(exc) or "Operation timed out",
            )

        except NotImplementedError as exc:
            return make_error(
                ErrorCode.NOT_IMPLEMENTED,
                str(exc) or "Not implemented",
            )

        except Exception as exc:  # pylint: disable=broad-except
            tb = traceback.format_exc()
            return make_error(
                ErrorCode.INTERNAL_ERROR,
                "Unhandled exception: {exc}".format(exc=repr(exc)),
                details={"traceback": tb},
            )

    # Preserve the _handler_name tag if the original function was decorated
    # with @handler before @wrap_handler.
    if hasattr(fn, "_handler_name"):
        wrapper._handler_name = fn._handler_name  # type: ignore[attr-defined]

    return wrapper
