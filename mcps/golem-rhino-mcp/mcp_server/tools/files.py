"""
mcp_server/tools/files.py
==========================
MCP tools for file I/O — opening, saving, importing, and exporting Rhino
documents and geometry in various formats.

Registered tools:
  - get_document_path
  - save_document
  - save_document_as
  - new_document
  - import_file
  - export_objects
  - export_document
"""

from __future__ import annotations

from typing import Any, Optional

from mcp_server.server import mcp
from mcp_server.connection import get_connection


def _send(method: str, params: dict) -> dict:
    return get_connection().send_command(method, params)


# ---------------------------------------------------------------------------
# Document management
# ---------------------------------------------------------------------------

@mcp.tool()
def get_document_path() -> dict[str, Any]:
    """
    Return the file path of the currently open Rhino document.

    Returns:
        dict with 'file_path' (absolute path or None if unsaved),
        'is_modified' (unsaved changes), and 'file_name'.
    """
    return _send("files.get_document_path", {})


@mcp.tool()
def save_document() -> dict[str, Any]:
    """
    Save the current Rhino document to its existing file path.

    Returns an error if the document has never been saved (use
    save_document_as instead).
    """
    return _send("files.save_document", {})


@mcp.tool()
def save_document_as(
    file_path: str,
    overwrite: bool = False,
) -> dict[str, Any]:
    """
    Save the current Rhino document to a new file path.

    Args:
        file_path: Absolute path including filename and .3dm extension.
        overwrite: Overwrite if the file already exists (default: False for safety).
    """
    return _send("files.save_document_as", {
        "file_path": file_path,
        "overwrite": overwrite,
    })


@mcp.tool()
def new_document(
    template_path: Optional[str] = None,
    units: str = "Millimeters",
) -> dict[str, Any]:
    """
    Open a new, empty Rhino document.

    Warning: any unsaved changes to the current document will be lost.

    Args:
        template_path: Absolute path to a .3dm template file.  Uses the
                       default Rhino template if None.
        units:         Unit system for the new document: 'Millimeters',
                       'Centimeters', 'Meters', 'Inches', 'Feet'.
    """
    return _send("files.new_document", {
        "template_path": template_path,
        "units": units,
    })


# ---------------------------------------------------------------------------
# Import
# ---------------------------------------------------------------------------

@mcp.tool()
def import_file(
    file_path: str,
    layer: Optional[str] = None,
    import_units: Optional[str] = None,
) -> dict[str, Any]:
    """
    Import geometry from a file into the current Rhino document.

    Supported formats (depends on installed Rhino plugins):
    .3dm, .obj, .fbx, .dxf, .dwg, .igs / .iges, .stp / .step, .stl,
    .skp, .ifc, .sat, .x_t

    Args:
        file_path:    Absolute path to the file to import.
        layer:        Layer to place imported objects on.  Uses import file's
                      layers if None.
        import_units: Override the unit system of the import file:
                      'Millimeters', 'Meters', 'Inches', etc.

    Returns:
        dict with 'guids' list of the imported object GUIDs and 'object_count'.
    """
    return _send("files.import_file", {
        "file_path": file_path,
        "layer": layer,
        "import_units": import_units,
    })


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

@mcp.tool()
def export_objects(
    guids: list[str],
    file_path: str,
    file_format: Optional[str] = None,
    overwrite: bool = False,
) -> dict[str, Any]:
    """
    Export specific objects to a file.

    Args:
        guids:       GUIDs of objects to export.
        file_path:   Absolute path including filename and extension.
        file_format: Explicit format override (e.g. 'OBJ', 'STL', 'STEP').
                     Inferred from file_path extension if None.
        overwrite:   Overwrite the file if it exists.

    Returns:
        dict with 'file_path', 'object_count', and 'file_size_bytes'.
    """
    return _send("files.export_objects", {
        "guids": guids,
        "file_path": file_path,
        "file_format": file_format,
        "overwrite": overwrite,
    })


@mcp.tool()
def export_document(
    file_path: str,
    file_format: Optional[str] = None,
    overwrite: bool = False,
    selected_only: bool = False,
) -> dict[str, Any]:
    """
    Export the entire document (or selected objects) to a file.

    Args:
        file_path:      Absolute path including filename and extension.
        file_format:    Explicit format override.  Inferred from extension if None.
        overwrite:      Overwrite the file if it exists.
        selected_only:  Export only the currently selected objects if True.

    Returns:
        dict with 'file_path', 'object_count', and 'file_size_bytes'.
    """
    return _send("files.export_document", {
        "file_path": file_path,
        "file_format": file_format,
        "overwrite": overwrite,
        "selected_only": selected_only,
    })
