# -*- coding: utf-8 -*-
"""
rhino_plugin/handlers/files.py
================================
Handler functions for file I/O operations executed inside Rhino 3D.

Registered methods (dispatched via rhino_plugin.dispatcher):
  - files.get_document_path
  - files.save_document
  - files.save_document_as
  - files.new_document
  - files.import_file
  - files.export_objects
  - files.export_document

Design notes
------------
* Python 3.9 compatible -- no match/case, no X | Y union syntax, no
  lowercase-generic annotations at runtime (Dict/List from typing).
* Zero external dependencies -- only Python stdlib, RhinoCommon, and
  rhinoscriptsyntax (all available inside Rhino's runtime).
* Every handler receives a plain dict (params) and returns a plain dict
  (result).  The dispatcher wraps the result in a JSON-RPC envelope.
* File path arguments are never modified; callers are responsible for
  providing absolute paths with the correct extension.

Supported export formats (extension → Rhino recognises via plug-in):
  .3dm .stl .obj .step .stp .iges .igs .fbx .3mf .dwg .dxf .pdf
  .3ds .ply .gltf .glb .usd
"""

# These imports are only available inside the Rhino Python environment.
# The try/except lets linters and unit-test runners import the module without
# exploding; at runtime inside Rhino they will always succeed.
try:
    import Rhino                              # type: ignore
    import scriptcontext as sc                # type: ignore
    import rhinoscriptsyntax as rs            # type: ignore
    _RHINO_AVAILABLE = True
except ImportError:
    _RHINO_AVAILABLE = False

from rhino_plugin.dispatcher import handler  # noqa: E402


# ---------------------------------------------------------------------------
# Supported export extensions (informational -- Rhino enforces the real list)
# ---------------------------------------------------------------------------

_SUPPORTED_EXPORT_EXTENSIONS = {
    ".3dm", ".stl", ".obj", ".step", ".stp", ".iges", ".igs",
    ".fbx", ".3mf", ".dwg", ".dxf", ".pdf", ".3ds", ".ply",
    ".gltf", ".glb", ".usd",
}


# ---------------------------------------------------------------------------
# Helper: get file size safely
# ---------------------------------------------------------------------------

def _file_size(path):
    # type: (str) -> int
    """Return the size in bytes of *path*, or -1 if the file is inaccessible."""
    try:
        import os
        return os.path.getsize(path)
    except Exception:
        return -1


# ---------------------------------------------------------------------------
# handlers
# ---------------------------------------------------------------------------

@handler("files.get_document_path")
def handle_get_document_path(params):
    # type: (dict) -> dict
    """
    Return the file path of the currently open Rhino document.

    Returns
    -------
    dict
        ``file_path``   -- Absolute path string, or None if the document has
                          never been saved.
        ``file_name``   -- Base filename (e.g. "model.3dm"), or None.
        ``is_modified`` -- True if there are unsaved changes.
    """
    result = {
        "file_path": None,
        "file_name": None,
        "is_modified": False,
    }

    try:
        path = sc.doc.Path
        result["file_path"] = str(path) if path else None
    except Exception:
        pass

    try:
        name = sc.doc.Name
        result["file_name"] = str(name) if name else None
    except Exception:
        pass

    try:
        result["is_modified"] = bool(sc.doc.Modified)
    except Exception:
        pass

    return result


@handler("files.save_document")
def handle_save_document(params):
    # type: (dict) -> dict
    """
    Save the current document to its existing file path.

    Raises ``ValueError`` if the document has never been saved (no path is
    set).  In that case, callers should use ``files.save_document_as``
    instead.

    Returns
    -------
    dict
        ``success``   -- True on success.
        ``file_path`` -- The path the document was saved to.
    """
    path = None
    try:
        path = sc.doc.Path
    except Exception:
        pass

    if not path:
        raise ValueError(
            "Document has no file path -- it has never been saved. "
            "Use files.save_document_as to save to a new path."
        )

    options = Rhino.FileIO.FileWriteOptions()
    saved = sc.doc.WriteFile(path, options)

    if not saved:
        raise RuntimeError(
            "Rhino WriteFile returned False for path: {path}".format(path=path)
        )

    return {
        "success": True,
        "file_path": str(path),
    }


@handler("files.save_document_as")
def handle_save_document_as(params):
    # type: (dict) -> dict
    """
    Save the current document to a new file path.

    Parameters
    ----------
    params : dict
        ``file_path`` (str, required) -- Absolute destination path, including
            the filename and ``.3dm`` extension.
        ``overwrite`` (bool, optional, default True) -- If False and the file
            already exists, raise an error rather than overwriting it.

    Returns
    -------
    dict
        ``success``   -- True on success.
        ``file_path`` -- The path the document was saved to.
    """
    import os

    file_path = params.get("file_path")
    if not file_path:
        raise ValueError("params['file_path'] is required for files.save_document_as")

    overwrite = params.get("overwrite", True)

    if not overwrite and os.path.exists(file_path):
        raise ValueError(
            "File already exists and overwrite=False: {path}".format(path=file_path)
        )

    options = Rhino.FileIO.FileWriteOptions()
    saved = sc.doc.WriteFile(file_path, options)

    if not saved:
        raise RuntimeError(
            "Rhino WriteFile returned False for path: {path}".format(path=file_path)
        )

    return {
        "success": True,
        "file_path": str(file_path),
    }


@handler("files.new_document")
def handle_new_document(params):
    # type: (dict) -> dict
    """
    Create a new Rhino document, discarding the current one.

    WARNING: Any unsaved changes to the current document will be lost.
    The document reference (``sc.doc``) is reset after this call.

    Parameters
    ----------
    params : dict
        ``template_path`` (str, optional) -- Absolute path to a ``.3dm``
            template file.  Uses Rhino's default template when omitted.

    Returns
    -------
    dict
        ``success`` -- True if the command was issued without error.
        ``template`` -- The template argument passed to Rhino, or "_None".
    """
    template = params.get("template_path") or params.get("template")

    if template:
        command_str = '_-New "{tmpl}"'.format(tmpl=template)
        template_used = str(template)
    else:
        command_str = "_-New _None"
        template_used = "_None"

    rs.Command(command_str, echo=False)

    return {
        "success": True,
        "template": template_used,
    }


@handler("files.import_file")
def handle_import_file(params):
    # type: (dict) -> dict
    """
    Import geometry from a file into the current Rhino document.

    Supported formats depend on installed Rhino import plug-ins, but
    typically include: .3dm, .obj, .fbx, .dxf, .dwg, .igs/.iges,
    .stp/.step, .stl, .skp, .ifc, .sat, .x_t.

    Parameters
    ----------
    params : dict
        ``file_path`` (str, required) -- Absolute path to the file to import.

    Returns
    -------
    dict
        ``success``      -- True if the import command completed.
        ``file_path``    -- The path that was imported.
        ``object_count`` -- Number of objects in the document after import
                           minus the count before (newly added objects).
                           May be 0 if the import produced no geometry.
    """
    file_path = params.get("file_path")
    if not file_path:
        raise ValueError("params['file_path'] is required for files.import_file")

    # Snapshot the object count before importing so we can return a delta.
    count_before = 0
    try:
        count_before = sc.doc.Objects.Count
    except Exception:
        pass

    rs.Command('_-Import "{path}" _Enter'.format(path=file_path), echo=False)

    count_after = 0
    try:
        count_after = sc.doc.Objects.Count
    except Exception:
        pass

    return {
        "success": True,
        "file_path": str(file_path),
        "object_count": max(0, count_after - count_before),
    }


@handler("files.export_objects")
def handle_export_objects(params):
    # type: (dict) -> dict
    """
    Export specific objects (identified by GUID) to a file.

    The extension of ``file_path`` determines the export format.
    Supported extensions: .stl .obj .step .stp .iges .igs .fbx .3mf
    .dwg .dxf .pdf .3ds .ply .gltf .glb .usd .3dm

    Parameters
    ----------
    params : dict
        ``guids``     (list[str], required) -- GUIDs of objects to export.
        ``file_path`` (str, required)       -- Absolute destination path
                                              including extension.
        ``overwrite`` (bool, optional)      -- Overwrite if file exists
                                              (default: True).

    Returns
    -------
    dict
        ``success``         -- True if the export command completed.
        ``file_path``       -- Destination path.
        ``object_count``    -- Number of GUIDs that were selected.
        ``file_size_bytes`` -- Size of the exported file, or -1 on error.
    """
    import os

    file_path = params.get("file_path")
    if not file_path:
        raise ValueError("params['file_path'] is required for files.export_objects")

    guids = params.get("guids") or params.get("object_ids") or []
    if not guids:
        raise ValueError("params['guids'] must be a non-empty list for files.export_objects")

    overwrite = params.get("overwrite", True)

    if not overwrite and os.path.exists(file_path):
        raise ValueError(
            "File already exists and overwrite=False: {path}".format(path=file_path)
        )

    # Deselect everything, then select only the requested objects.
    rs.UnselectAllObjects()
    selected_count = 0
    for guid_str in guids:
        try:
            import System
            guid_obj = System.Guid(str(guid_str))
            obj = sc.doc.Objects.Find(guid_obj)
            if obj is not None:
                obj.Select(True)
                selected_count += 1
        except Exception:
            pass

    if selected_count == 0:
        raise ValueError(
            "None of the provided GUIDs could be found in the document."
        )

    rs.Command('_-Export "{path}" _Enter'.format(path=file_path), echo=False)

    # Clean up selection state.
    try:
        rs.UnselectAllObjects()
    except Exception:
        pass

    return {
        "success": True,
        "file_path": str(file_path),
        "object_count": selected_count,
        "file_size_bytes": _file_size(file_path),
    }


@handler("files.export_document")
def handle_export_document(params):
    # type: (dict) -> dict
    """
    Export the entire document (or the current selection) to a file.

    The extension of ``file_path`` determines the export format.
    See ``files.export_objects`` for the list of supported extensions.

    Parameters
    ----------
    params : dict
        ``file_path``    (str, required) -- Absolute destination path.
        ``overwrite``    (bool, optional, default True) -- Overwrite if exists.
        ``selected_only`` (bool, optional, default False) -- When True, only
            currently selected objects are exported (equivalent to
            ``export_selected``).

    Returns
    -------
    dict
        ``success``         -- True if the export command completed.
        ``file_path``       -- Destination path.
        ``object_count``    -- Total objects in the document (or selection).
        ``file_size_bytes`` -- Size of the exported file, or -1 on error.
    """
    import os

    file_path = params.get("file_path")
    if not file_path:
        raise ValueError("params['file_path'] is required for files.export_document")

    overwrite = params.get("overwrite", True)
    selected_only = params.get("selected_only", False)

    if not overwrite and os.path.exists(file_path):
        raise ValueError(
            "File already exists and overwrite=False: {path}".format(path=file_path)
        )

    if not selected_only:
        # Ensure nothing is selected so Rhino exports all objects.
        try:
            rs.UnselectAllObjects()
        except Exception:
            pass

    rs.Command('_-Export "{path}" _Enter'.format(path=file_path), echo=False)

    object_count = 0
    try:
        if selected_only:
            object_count = len(rs.SelectedObjects() or [])
        else:
            object_count = sc.doc.Objects.Count
    except Exception:
        pass

    return {
        "success": True,
        "file_path": str(file_path),
        "object_count": object_count,
        "file_size_bytes": _file_size(file_path),
    }


@handler("files.export_selected")
def handle_export_selected(params):
    # type: (dict) -> dict
    """
    Export currently selected objects to a file.

    This is a convenience wrapper around ``files.export_document`` with
    ``selected_only=True``.  The current selection is not modified.

    Parameters
    ----------
    params : dict
        ``file_path`` (str, required) -- Absolute destination path.

    Returns
    -------
    dict
        ``success``         -- True if the export command completed.
        ``file_path``       -- Destination path.
        ``object_count``    -- Number of objects that were selected at
                              the time of export.
        ``file_size_bytes`` -- Size of the exported file, or -1 on error.
    """
    file_path = params.get("file_path")
    if not file_path:
        raise ValueError("params['file_path'] is required for files.export_selected")

    rs.Command('_-Export "{path}" _Enter'.format(path=file_path), echo=False)

    object_count = 0
    try:
        object_count = len(rs.SelectedObjects() or [])
    except Exception:
        pass

    return {
        "success": True,
        "file_path": str(file_path),
        "object_count": object_count,
        "file_size_bytes": _file_size(file_path),
    }


@handler("files.open_document")
def handle_open_document(params):
    # type: (dict) -> dict
    """
    Open a ``.3dm`` file, replacing the current document.

    WARNING: Any unsaved changes to the current document will be lost.

    Parameters
    ----------
    params : dict
        ``file_path`` (str, required) -- Absolute path to the ``.3dm`` file.

    Returns
    -------
    dict
        ``success``   -- True if the open command was issued.
        ``file_path`` -- The path that was opened.
    """
    file_path = params.get("file_path")
    if not file_path:
        raise ValueError("params['file_path'] is required for files.open_document")

    rs.Command('_-Open "{path}"'.format(path=file_path), echo=False)

    return {
        "success": True,
        "file_path": str(file_path),
    }
