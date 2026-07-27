"""
mcp_server/models/geometry.py
==============================
Pydantic v2 parameter models for geometry creation MCP tools.

These are used as type annotations in FastMCP tool definitions and provide
automatic input validation, schema generation, and documentation for Claude.

Design notes
------------
* Keep models thin — they validate input, not business logic.
* Optional fields default to ``None`` so that Claude does not need to supply
  every parameter for simple cases.
* Layer, name, and color fields appear on every creation model so that a
  single tool call can position the object AND assign it to a layer.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from .common import Color, Plane, Point3D, Vector3D


# ---------------------------------------------------------------------------
# Shared mixin for common object attributes
# ---------------------------------------------------------------------------

class ObjectAttributes(BaseModel):
    """
    Common object attributes shared by all geometry creation models.

    Mixed into creation param models so that every tool can optionally set
    the layer, name, and colour of the created object in a single call.
    """

    layer: Optional[str] = Field(
        default=None,
        description="Full layer path, e.g. 'Walls' or 'Site::Landscaping'.",
    )
    name: Optional[str] = Field(
        default=None,
        description="Object name / label.",
    )
    color: Optional[Color] = Field(
        default=None,
        description="Object colour override.  Defaults to the layer colour if omitted.",
    )


# ---------------------------------------------------------------------------
# Primitive solids
# ---------------------------------------------------------------------------

class BoxParams(ObjectAttributes):
    """Parameters for creating a rectangular box (cuboid)."""

    corner: Point3D = Field(
        default_factory=Point3D,
        description="One corner of the base rectangle in world XY.",
    )
    width: float = Field(
        default=1.0,
        gt=0,
        description="Box dimension along the X axis.",
    )
    depth: float = Field(
        default=1.0,
        gt=0,
        description="Box dimension along the Y axis.",
    )
    height: float = Field(
        default=1.0,
        gt=0,
        description="Box dimension along the Z axis.",
    )


class SphereParams(ObjectAttributes):
    """Parameters for creating a sphere."""

    center: Point3D = Field(
        default_factory=Point3D,
        description="Centre point of the sphere.",
    )
    radius: float = Field(
        default=1.0,
        gt=0,
        description="Sphere radius.",
    )


class CylinderParams(ObjectAttributes):
    """Parameters for creating a capped or uncapped cylinder."""

    base_center: Point3D = Field(
        default_factory=Point3D,
        description="Centre of the bottom circle.",
    )
    height: float = Field(
        default=1.0,
        gt=0,
        description="Height of the cylinder.",
    )
    radius: float = Field(
        default=1.0,
        gt=0,
        description="Radius of the circular cross-section.",
    )
    cap: bool = Field(
        default=True,
        description="If ``True`` both ends are capped (closed solid).",
    )


class ConeParams(ObjectAttributes):
    """Parameters for creating a cone."""

    base_center: Point3D = Field(default_factory=Point3D)
    radius: float = Field(default=1.0, gt=0)
    height: float = Field(default=1.0, gt=0)
    cap: bool = Field(default=True)


class TorusParams(ObjectAttributes):
    """Parameters for creating a torus."""

    center: Point3D = Field(default_factory=Point3D)
    major_radius: float = Field(
        default=2.0,
        gt=0,
        description="Distance from the torus centre to the tube centre.",
    )
    minor_radius: float = Field(
        default=0.5,
        gt=0,
        description="Radius of the tube cross-section.",
    )


# ---------------------------------------------------------------------------
# Curves
# ---------------------------------------------------------------------------

class CurveParams(ObjectAttributes):
    """
    Parameters for creating a NURBS curve through or near a set of points.
    """

    points: List[Point3D] = Field(
        min_length=2,
        description="Ordered list of control or through-points.",
    )
    degree: int = Field(
        default=3,
        ge=1,
        le=11,
        description="Polynomial degree of the NURBS curve.",
    )
    weights: Optional[List[float]] = Field(
        default=None,
        description="Per-point weights (same length as ``points``).  Uniform weights if omitted.",
    )
    knots: Optional[List[float]] = Field(
        default=None,
        description="Full knot vector.  Auto-generated if omitted.",
    )
    interpolate: bool = Field(
        default=True,
        description="If ``True`` the curve passes through all points (interpolated).  "
                    "If ``False`` the points are used as NURBS control points.",
    )


class PolylineParams(ObjectAttributes):
    """Parameters for creating a polyline through an ordered point list."""

    points: List[Point3D] = Field(min_length=2)
    closed: bool = Field(
        default=False,
        description="If ``True`` the last point is connected back to the first.",
    )


class LineParams(ObjectAttributes):
    """Parameters for creating a straight line segment."""

    start: Point3D = Field(default_factory=Point3D)
    end: Point3D = Field(default_factory=lambda: Point3D(x=1.0, y=0.0, z=0.0))


class ArcParams(ObjectAttributes):
    """Parameters for creating an arc by centre, radius, and angle range."""

    center: Point3D = Field(default_factory=Point3D)
    radius: float = Field(default=1.0, gt=0)
    start_angle: float = Field(
        default=0.0,
        description="Start angle in degrees.",
    )
    end_angle: float = Field(
        default=180.0,
        description="End angle in degrees.",
    )
    plane: Optional[Plane] = Field(
        default=None,
        description="Construction plane for the arc.  Defaults to world XY.",
    )


class CircleParams(ObjectAttributes):
    """Parameters for creating a full circle."""

    center: Point3D = Field(default_factory=Point3D)
    radius: float = Field(default=1.0, gt=0)
    plane: Optional[Plane] = Field(
        default=None,
        description="Construction plane.  Defaults to world XY.",
    )


# ---------------------------------------------------------------------------
# Surfaces and breps
# ---------------------------------------------------------------------------

class ExtrudeParams(ObjectAttributes):
    """Extrude a curve profile along a direction vector."""

    profile_guid: str = Field(
        description="GUID of the curve to extrude.",
    )
    direction: Vector3D = Field(
        default_factory=lambda: Vector3D(x=0.0, y=0.0, z=1.0),
        description="Extrusion direction vector (not required to be unit-length).",
    )
    distance: float = Field(
        default=1.0,
        gt=0,
        description="Extrusion distance (scales the direction vector).",
    )
    cap: bool = Field(
        default=True,
        description="Cap the ends if the profile is a closed curve.",
    )


class LoftParams(ObjectAttributes):
    """Loft a surface through an ordered list of section curves."""

    curve_guids: List[str] = Field(
        min_length=2,
        description="Ordered list of cross-section curve GUIDs.",
    )
    closed: bool = Field(
        default=False,
        description="Close the loft back to the first section.",
    )
    loft_type: str = Field(
        default="Normal",
        description="Loft type: Normal, Loose, Tight, Straight, Developable, Uniform.",
    )


class RevolutionParams(ObjectAttributes):
    """Revolve a profile curve around an axis."""

    profile_guid: str = Field(description="GUID of the profile curve.")
    axis_start: Point3D = Field(default_factory=Point3D)
    axis_end: Point3D = Field(
        default_factory=lambda: Point3D(x=0.0, y=0.0, z=1.0),
    )
    start_angle: float = Field(default=0.0, description="Start angle in degrees.")
    end_angle: float = Field(default=360.0, description="End angle in degrees.")


class PatchParams(ObjectAttributes):
    """Fit a patch surface to a set of curves or points."""

    input_guids: List[str] = Field(
        min_length=1,
        description="GUIDs of boundary curves, points, or a mix thereof.",
    )
    u_spans: int = Field(default=10, ge=1, description="Number of spans in U direction.")
    v_spans: int = Field(default=10, ge=1, description="Number of spans in V direction.")
    trim: bool = Field(default=True, description="Trim the surface to the boundary.")


# ---------------------------------------------------------------------------
# Mesh
# ---------------------------------------------------------------------------

class MeshFromSurfaceParams(ObjectAttributes):
    """Mesh a brep or surface with given density settings."""

    source_guid: str = Field(description="GUID of the brep or surface to mesh.")
    max_edge_length: Optional[float] = Field(
        default=None,
        gt=0,
        description="Maximum mesh edge length.  Auto-calculated if omitted.",
    )
    refine_mesh: bool = Field(default=True)
    simple_planes: bool = Field(default=False)
