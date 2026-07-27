# -*- coding: utf-8 -*-
"""
rhino_plugin/utils/screenshot.py
==================================
Capture a Rhino viewport to a base64-encoded PNG string.

Design notes
------------
* Python 3.9 compatible -- no ``match``/``case``, no ``X | Y`` union syntax.
* Zero external dependencies beyond what Rhino ships (System.Drawing,
  System.IO, the built-in ``base64`` module).
* Runs **inside Rhino 3D** where ``Rhino``, ``System``, and
  ``scriptcontext`` are always available.
* The function is intentionally free of side effects on the Rhino document:
  it does not change the active view, the display mode, or any object.

Display mode names accepted (case-insensitive) examples:
  ``"Wireframe"``, ``"Shaded"``, ``"Rendered"``, ``"Arctic"``,
  ``"Technical"``, ``"Pen"``, ``"Ghosted"``, ``"X-Ray"``
"""

import base64
try:
    from typing import Dict, Optional
except ImportError:
    pass

try:
    import Rhino
    import scriptcontext as sc
    import System
    import System.Drawing
    import System.IO
    _RHINO_AVAILABLE = True
except ImportError:
    _RHINO_AVAILABLE = False


def capture_viewport_to_base64(
    view_name=None,   # type: Optional[str]
    width=1920,       # type: int
    height=1080,      # type: int
    display_mode=None,  # type: Optional[str]
):
    # type: (...) -> Dict
    """
    Capture a Rhino viewport to a base64-encoded PNG and return a metadata
    dict.

    Parameters
    ----------
    view_name:
        Name of the Rhino view to capture (e.g. ``"Perspective"``,
        ``"Top"``, ``"Right"``).  If ``None`` or not found, the currently
        active view is used.
    width:
        Output image width in pixels.  Defaults to 1920.
    height:
        Output image height in pixels.  Defaults to 1080.
    display_mode:
        Name of the display mode to apply during capture (e.g.
        ``"Rendered"``, ``"Wireframe"``).  If ``None`` the view's current
        display mode is kept.  The original display mode is restored
        after capture.

    Returns
    -------
    dict
        On success::

            {
                "image":        str,   # base64-encoded PNG
                "width":        int,
                "height":       int,
                "display_mode": str,   # actual display mode used
                "view_name":    str,   # actual view name used
            }

        On failure::

            {
                "error":   str,   # human-readable description
                "code":    str,   # GOLEM error code constant
            }

    Raises
    ------
    Does not raise -- all exceptions are caught and returned as error dicts.
    """
    if not _RHINO_AVAILABLE:
        return {
            "error": "Rhino environment not available (running outside Rhino).",
            "code": "INTERNAL_ERROR",
        }

    # ------------------------------------------------------------------
    # 1. Resolve the target view.
    # ------------------------------------------------------------------
    view = None

    if view_name is not None:
        try:
            for v in sc.doc.Views:
                if v.ActiveViewport.Name.lower() == view_name.lower():
                    view = v
                    break
        except Exception:
            pass

        if view is None:
            return {
                "error": "View not found: '{name}'".format(name=view_name),
                "code": "OBJECT_NOT_FOUND",
            }
    else:
        try:
            view = sc.doc.Views.ActiveView
        except Exception:
            pass

    if view is None:
        return {
            "error": "No active Rhino view available.",
            "code": "INTERNAL_ERROR",
        }

    actual_view_name = "unknown"
    try:
        actual_view_name = str(view.ActiveViewport.Name)
    except Exception:
        pass

    # ------------------------------------------------------------------
    # 2. Optionally switch the display mode.
    # ------------------------------------------------------------------
    original_display_mode = None
    actual_display_mode = "unknown"

    try:
        original_display_mode = view.ActiveViewport.DisplayMode
        actual_display_mode = str(original_display_mode.EnglishName)
    except Exception:
        pass

    if display_mode is not None:
        try:
            target_mode = Rhino.Display.DisplayModeDescription.FindByName(display_mode)
            if target_mode is not None:
                view.ActiveViewport.DisplayMode = target_mode
                actual_display_mode = str(target_mode.EnglishName)
                sc.doc.Views.Redraw()
            else:
                # Non-fatal: continue with the current display mode.
                pass
        except Exception:
            pass

    # ------------------------------------------------------------------
    # 3. Capture the viewport to a .NET Bitmap.
    # ------------------------------------------------------------------
    bitmap = None
    try:
        capture_size = System.Drawing.Size(int(width), int(height))
        bitmap = view.CaptureToBitmap(capture_size)
    except Exception as exc:
        # Restore display mode before returning.
        if original_display_mode is not None:
            try:
                view.ActiveViewport.DisplayMode = original_display_mode
                sc.doc.Views.Redraw()
            except Exception:
                pass
        return {
            "error": "CaptureToBitmap failed: {exc}".format(exc=repr(exc)),
            "code": "OPERATION_FAILED",
        }

    if bitmap is None:
        if original_display_mode is not None:
            try:
                view.ActiveViewport.DisplayMode = original_display_mode
                sc.doc.Views.Redraw()
            except Exception:
                pass
        return {
            "error": "CaptureToBitmap returned None.",
            "code": "OPERATION_FAILED",
        }

    # ------------------------------------------------------------------
    # 4. Encode the bitmap as PNG bytes via MemoryStream.
    # ------------------------------------------------------------------
    image_b64 = None
    actual_width = width
    actual_height = height

    try:
        with System.IO.MemoryStream() as stream:
            bitmap.Save(stream, System.Drawing.Imaging.ImageFormat.Png)
            png_bytes = bytes(stream.ToArray())
        image_b64 = base64.b64encode(png_bytes).decode("ascii")
        try:
            actual_width = int(bitmap.Width)
            actual_height = int(bitmap.Height)
        except Exception:
            pass
    except Exception as exc:
        if original_display_mode is not None:
            try:
                view.ActiveViewport.DisplayMode = original_display_mode
                sc.doc.Views.Redraw()
            except Exception:
                pass
        return {
            "error": "Failed to encode bitmap as PNG: {exc}".format(exc=repr(exc)),
            "code": "INTERNAL_ERROR",
        }
    finally:
        try:
            bitmap.Dispose()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # 5. Restore original display mode.
    # ------------------------------------------------------------------
    if original_display_mode is not None and display_mode is not None:
        try:
            view.ActiveViewport.DisplayMode = original_display_mode
            sc.doc.Views.Redraw()
        except Exception:
            pass

    return {
        "image": image_b64,
        "width": actual_width,
        "height": actual_height,
        "display_mode": actual_display_mode,
        "view_name": actual_view_name,
    }
