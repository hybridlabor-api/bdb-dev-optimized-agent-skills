"""
golem_3dmcp/models/common.py
============================
Shared Pydantic v2 models used across GOLEM-3DMCP MCP tools.

These models serve two purposes:
1. Type-safe parameter validation for incoming MCP tool calls.
2. Structured return types that the MCP framework can serialise for Claude.

Python >= 3.10 is assumed on the MCP server side (see pyproject.toml).
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Geometric primitives
# ---------------------------------------------------------------------------

class Point3D(BaseModel):
    """A point in 3D Euclidean space."""

    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def to_list(self) -> list[float]:
        """Return ``[x, y, z]`` for passing to RhinoCommon."""
        return [self.x, self.y, self.z]


class Vector3D(BaseModel):
    """A direction vector in 3D space (not necessarily unit-length)."""

    x: float = 0.0
    y: float = 0.0
    z: float = 1.0

    def to_list(self) -> list[float]:
        return [self.x, self.y, self.z]


class Plane(BaseModel):
    """
    An oriented plane defined by an origin and two orthogonal axes.

    The normal is implicitly ``x_axis cross y_axis``; it is not stored to
    avoid redundancy and potential inconsistency.
    """

    origin: Point3D = Field(default_factory=Point3D)
    x_axis: Vector3D = Field(default_factory=lambda: Vector3D(x=1.0, y=0.0, z=0.0))
    y_axis: Vector3D = Field(default_factory=lambda: Vector3D(x=0.0, y=1.0, z=0.0))


class Color(BaseModel):
    """RGBA colour with integer channels in the range [0, 255]."""

    r: int = Field(default=0, ge=0, le=255)
    g: int = Field(default=0, ge=0, le=255)
    b: int = Field(default=0, ge=0, le=255)
    a: int = Field(default=255, ge=0, le=255)

    def to_hex(self) -> str:
        """Return a CSS-style hex string, e.g. ``"#ff0000"``."""
        return f"#{self.r:02x}{self.g:02x}{self.b:02x}"


class BoundingBox(BaseModel):
    """Axis-aligned bounding box."""

    min: Point3D
    max: Point3D

    @property
    def diagonal(self) -> list[float]:
        """Vector from min to max corner."""
        return [
            self.max.x - self.min.x,
            self.max.y - self.min.y,
            self.max.z - self.min.z,
        ]


# ---------------------------------------------------------------------------
# Operation result
# ---------------------------------------------------------------------------

class OperationResult(BaseModel):
    """
    Generic result envelope returned by geometry creation and mutation tools.

    Fields
    ------
    guid:
        The GUID of the single object that was created/modified.
    guids:
        Multiple GUIDs when the operation produced or affected several objects.
    success:
        ``True`` if the operation succeeded without errors.
    message:
        Human-readable summary, especially useful when ``success=False``.
    data:
        Optional arbitrary payload for tool-specific extra information.
    """

    guid: str | None = None
    guids: list[str] | None = None
    success: bool = True
    message: str | None = None
    data: dict[str, Any] | None = None

    @classmethod
    def ok(
        cls,
        guid: str | None = None,
        guids: list[str] | None = None,
        message: str | None = None,
        data: dict[str, Any] | None = None,
    ) -> OperationResult:
        """Convenience constructor for successful results."""
        return cls(guid=guid, guids=guids, success=True, message=message, data=data)

    @classmethod
    def fail(cls, message: str, data: dict[str, Any] | None = None) -> OperationResult:
        """Convenience constructor for failed results."""
        return cls(success=False, message=message, data=data)
