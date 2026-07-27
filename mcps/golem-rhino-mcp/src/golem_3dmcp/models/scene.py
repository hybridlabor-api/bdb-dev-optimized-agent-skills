"""
golem_3dmcp/models/scene.py
===========================
Pydantic v2 models representing Rhino document and scene state.

These are return types used by scene-inspection MCP tools (get_document_info,
list_layers, list_objects, etc.).  They are also used as input parameters for
tools that create or modify layers and object attributes.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from .common import BoundingBox, Color

# ---------------------------------------------------------------------------
# Document / file level
# ---------------------------------------------------------------------------

class DocumentInfo(BaseModel):
    """
    High-level information about the currently open Rhino document.
    """

    file_path: str | None = Field(
        default=None,
        description="Absolute path of the .3dm file on disk, or ``None`` if unsaved.",
    )
    units: str = Field(
        default="Millimeters",
        description="Model unit system (e.g. 'Millimeters', 'Meters', 'Feet').",
    )
    tolerance: float = Field(
        default=0.001,
        description="Absolute model tolerance in model units.",
    )
    angle_tolerance: float = Field(
        default=1.0,
        description="Angle tolerance in degrees.",
    )
    object_count: int = Field(
        default=0,
        ge=0,
        description="Total number of objects in the document.",
    )
    layer_count: int = Field(
        default=0,
        ge=0,
        description="Total number of layers in the document.",
    )
    is_modified: bool = Field(
        default=False,
        description="``True`` if there are unsaved changes.",
    )


# ---------------------------------------------------------------------------
# Layers
# ---------------------------------------------------------------------------

class LayerInfo(BaseModel):
    """
    Information about a single Rhino layer.
    """

    name: str = Field(description="Layer short name (without parent path).")
    full_path: str = Field(
        description="Full layer path including all parents, e.g. 'Site::Buildings::Walls'.",
    )
    color: Color = Field(default_factory=Color)
    visible: bool = Field(default=True)
    locked: bool = Field(default=False)
    parent: str | None = Field(
        default=None,
        description="Full path of the parent layer, or ``None`` for top-level layers.",
    )
    object_count: int = Field(
        default=0,
        ge=0,
        description="Number of objects on this layer (not including child layers).",
    )
    index: int = Field(
        default=0,
        ge=0,
        description="Zero-based layer index in the document layer table.",
    )


class LayerCreateParams(BaseModel):
    """Parameters for creating a new layer."""

    name: str = Field(description="Layer name.  Use '::' as a separator for nested layers.")
    color: Color | None = Field(default=None)
    visible: bool = Field(default=True)
    locked: bool = Field(default=False)
    parent: str | None = Field(
        default=None,
        description="Full path of the parent layer.  Creates top-level layer if omitted.",
    )


# ---------------------------------------------------------------------------
# Objects
# ---------------------------------------------------------------------------

class ObjectInfo(BaseModel):
    """
    Summary information about a single Rhino document object.

    Returned by list_objects, get_object_info, and selection tools.
    """

    guid: str = Field(description="Object GUID as a string.")
    type: str = Field(
        description="Geometry type: 'brep', 'curve', 'mesh', 'point', "
                    "'extrusion', 'subd', 'annotation', etc.",
    )
    layer: str | None = Field(
        default=None,
        description="Full layer path the object lives on.",
    )
    name: str | None = Field(
        default=None,
        description="Object name (may be empty string if unnamed).",
    )
    color: Color | None = Field(
        default=None,
        description="Object colour override.  ``None`` means 'by layer'.",
    )
    visible: bool = Field(default=True)
    locked: bool = Field(default=False)
    bounding_box: BoundingBox | None = Field(default=None)
    user_text: dict[str, str] = Field(
        default_factory=dict,
        description="All user-text key-value pairs attached to the object.",
    )


class ObjectFilter(BaseModel):
    """
    Filter criteria for querying objects from the Rhino document.

    All fields are optional; unset fields are not used to filter.
    Multiple set fields are combined with AND logic.
    """

    layer: str | None = Field(
        default=None,
        description="Return only objects on this layer (full path match).",
    )
    object_type: str | None = Field(
        default=None,
        description="Return only objects of this geometry type.",
    )
    name: str | None = Field(
        default=None,
        description="Return only objects whose name contains this substring.",
    )
    visible_only: bool = Field(
        default=False,
        description="If ``True`` exclude hidden objects.",
    )
    unlocked_only: bool = Field(
        default=False,
        description="If ``True`` exclude locked objects.",
    )


# ---------------------------------------------------------------------------
# Named views and camera
# ---------------------------------------------------------------------------

class ViewInfo(BaseModel):
    """Information about a named or active Rhino view."""

    name: str
    is_perspective: bool = False
    camera_location: list[float] | None = Field(
        default=None,
        description="[x, y, z] of the camera position.",
    )
    camera_target: list[float] | None = Field(
        default=None,
        description="[x, y, z] of the camera target.",
    )
    display_mode: str | None = None
    width_pixels: int | None = None
    height_pixels: int | None = None


# ---------------------------------------------------------------------------
# Selection result
# ---------------------------------------------------------------------------

class SelectionResult(BaseModel):
    """
    Returned by tools that select, highlight, or focus on objects.
    """

    selected_count: int = Field(default=0, ge=0)
    guids: list[str] = Field(default_factory=list)
    message: str | None = None
