"""
tests/test_models.py
=====================
Unit tests for all Pydantic v2 models in:
  - golem_3dmcp/models/common.py
  - golem_3dmcp/models/geometry.py
  - golem_3dmcp/models/scene.py

Tests cover:
  - Default construction
  - Field validation (ge/le constraints, gt constraints, min_length)
  - Required field enforcement
  - model_dump() serialisation shape
  - Helper methods (to_list, to_hex, diagonal, BoundingBox.diagonal, etc.)
  - Factory classmethods (OperationResult.ok, OperationResult.fail)
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

# ---------------------------------------------------------------------------
# common.py
# ---------------------------------------------------------------------------
from golem_3dmcp.models.common import (
    BoundingBox,
    Color,
    OperationResult,
    Plane,
    Point3D,
    Vector3D,
)

# ---------------------------------------------------------------------------
# geometry.py
# ---------------------------------------------------------------------------
from golem_3dmcp.models.geometry import (
    ArcParams,
    BoxParams,
    CircleParams,
    ConeParams,
    CurveParams,
    CylinderParams,
    ExtrudeParams,
    LineParams,
    LoftParams,
    MeshFromSurfaceParams,
    ObjectAttributes,
    PatchParams,
    PolylineParams,
    RevolutionParams,
    SphereParams,
    TorusParams,
)

# ---------------------------------------------------------------------------
# scene.py
# ---------------------------------------------------------------------------
from golem_3dmcp.models.scene import (
    DocumentInfo,
    LayerCreateParams,
    LayerInfo,
    ObjectFilter,
    ObjectInfo,
    SelectionResult,
    ViewInfo,
)

# ===========================================================================
# common.py
# ===========================================================================

class TestPoint3D:

    def test_defaults(self):
        p = Point3D()
        assert p.x == 0.0
        assert p.y == 0.0
        assert p.z == 0.0

    def test_explicit_values(self):
        p = Point3D(x=1.5, y=-2.0, z=3.14)
        assert p.x == 1.5
        assert p.y == -2.0
        assert p.z == 3.14

    def test_to_list(self):
        p = Point3D(x=1.0, y=2.0, z=3.0)
        assert p.to_list() == [1.0, 2.0, 3.0]

    def test_model_dump(self):
        p = Point3D(x=1.0, y=2.0, z=3.0)
        d = p.model_dump()
        assert d == {"x": 1.0, "y": 2.0, "z": 3.0}

    def test_from_dict(self):
        p = Point3D.model_validate({"x": 7.0, "y": 8.0, "z": 9.0})
        assert p.x == 7.0


class TestVector3D:

    def test_defaults(self):
        v = Vector3D()
        assert v.x == 0.0
        assert v.y == 0.0
        assert v.z == 1.0  # default is Z-up

    def test_to_list(self):
        v = Vector3D(x=0.0, y=1.0, z=0.0)
        assert v.to_list() == [0.0, 1.0, 0.0]

    def test_model_dump(self):
        v = Vector3D(x=1.0, y=0.0, z=0.0)
        assert v.model_dump() == {"x": 1.0, "y": 0.0, "z": 0.0}


class TestPlane:

    def test_defaults(self):
        plane = Plane()
        assert plane.origin == Point3D(x=0.0, y=0.0, z=0.0)
        assert plane.x_axis == Vector3D(x=1.0, y=0.0, z=0.0)
        assert plane.y_axis == Vector3D(x=0.0, y=1.0, z=0.0)

    def test_custom_origin(self):
        plane = Plane(origin=Point3D(x=5.0, y=0.0, z=0.0))
        assert plane.origin.x == 5.0

    def test_model_dump_nested(self):
        plane = Plane()
        d = plane.model_dump()
        assert "origin" in d
        assert d["origin"]["x"] == 0.0
        assert d["x_axis"]["x"] == 1.0


class TestColor:

    def test_defaults(self):
        c = Color()
        assert c.r == 0
        assert c.g == 0
        assert c.b == 0
        assert c.a == 255

    def test_explicit_rgba(self):
        c = Color(r=255, g=128, b=0, a=200)
        assert c.r == 255
        assert c.g == 128
        assert c.b == 0
        assert c.a == 200

    def test_to_hex(self):
        c = Color(r=255, g=0, b=0)
        assert c.to_hex() == "#ff0000"

    def test_to_hex_black(self):
        assert Color(r=0, g=0, b=0).to_hex() == "#000000"

    def test_to_hex_white(self):
        assert Color(r=255, g=255, b=255).to_hex() == "#ffffff"

    def test_model_dump(self):
        c = Color(r=10, g=20, b=30, a=255)
        d = c.model_dump()
        assert d == {"r": 10, "g": 20, "b": 30, "a": 255}

    # Validation

    def test_r_below_zero_invalid(self):
        with pytest.raises(ValidationError):
            Color(r=-1, g=0, b=0)

    def test_r_above_255_invalid(self):
        with pytest.raises(ValidationError):
            Color(r=256, g=0, b=0)

    def test_g_below_zero_invalid(self):
        with pytest.raises(ValidationError):
            Color(r=0, g=-1, b=0)

    def test_g_above_255_invalid(self):
        with pytest.raises(ValidationError):
            Color(r=0, g=256, b=0)

    def test_b_below_zero_invalid(self):
        with pytest.raises(ValidationError):
            Color(r=0, g=0, b=-1)

    def test_b_above_255_invalid(self):
        with pytest.raises(ValidationError):
            Color(r=0, g=0, b=256)

    def test_a_below_zero_invalid(self):
        with pytest.raises(ValidationError):
            Color(r=0, g=0, b=0, a=-1)

    def test_a_above_255_invalid(self):
        with pytest.raises(ValidationError):
            Color(r=0, g=0, b=0, a=256)

    def test_boundary_values_accepted(self):
        c = Color(r=0, g=255, b=0, a=0)
        assert c.r == 0
        assert c.g == 255


class TestBoundingBox:

    def test_construction(self):
        bb = BoundingBox(
            min=Point3D(x=0.0, y=0.0, z=0.0),
            max=Point3D(x=10.0, y=5.0, z=3.0),
        )
        assert bb.min.x == 0.0
        assert bb.max.z == 3.0

    def test_diagonal(self):
        bb = BoundingBox(
            min=Point3D(x=1.0, y=2.0, z=3.0),
            max=Point3D(x=4.0, y=6.0, z=9.0),
        )
        assert bb.diagonal == [3.0, 4.0, 6.0]

    def test_zero_size_diagonal(self):
        bb = BoundingBox(
            min=Point3D(x=5.0, y=5.0, z=5.0),
            max=Point3D(x=5.0, y=5.0, z=5.0),
        )
        assert bb.diagonal == [0.0, 0.0, 0.0]

    def test_requires_min_and_max(self):
        with pytest.raises(ValidationError):
            BoundingBox(min=Point3D())  # max is required

    def test_model_dump(self):
        bb = BoundingBox(
            min=Point3D(x=0.0, y=0.0, z=0.0),
            max=Point3D(x=1.0, y=1.0, z=1.0),
        )
        d = bb.model_dump()
        assert d["min"]["x"] == 0.0
        assert d["max"]["x"] == 1.0


class TestOperationResult:

    def test_default_success(self):
        r = OperationResult()
        assert r.success is True
        assert r.guid is None
        assert r.guids is None
        assert r.message is None
        assert r.data is None

    def test_ok_factory(self):
        r = OperationResult.ok(guid="abc-123", message="Created")
        assert r.success is True
        assert r.guid == "abc-123"
        assert r.message == "Created"

    def test_ok_with_guids(self):
        r = OperationResult.ok(guids=["g1", "g2"])
        assert r.guids == ["g1", "g2"]
        assert r.success is True

    def test_ok_with_data(self):
        r = OperationResult.ok(data={"count": 5})
        assert r.data == {"count": 5}

    def test_fail_factory(self):
        r = OperationResult.fail("Something went wrong")
        assert r.success is False
        assert r.message == "Something went wrong"

    def test_fail_with_data(self):
        r = OperationResult.fail("Error", data={"code": 42})
        assert r.data == {"code": 42}

    def test_model_dump(self):
        r = OperationResult.ok(guid="x")
        d = r.model_dump()
        assert d["success"] is True
        assert d["guid"] == "x"
        assert "guids" in d
        assert "message" in d
        assert "data" in d


# ===========================================================================
# geometry.py
# ===========================================================================

class TestObjectAttributes:

    def test_all_optional(self):
        a = ObjectAttributes()
        assert a.layer is None
        assert a.name is None
        assert a.color is None

    def test_with_color(self):
        a = ObjectAttributes(color=Color(r=255, g=0, b=0))
        assert a.color is not None
        assert a.color.r == 255


class TestBoxParams:

    def test_defaults(self):
        b = BoxParams()
        assert b.width == 1.0
        assert b.depth == 1.0
        assert b.height == 1.0
        assert b.corner.x == 0.0

    def test_custom_dimensions(self):
        b = BoxParams(width=2.0, depth=3.0, height=4.0)
        assert b.width == 2.0
        assert b.depth == 3.0
        assert b.height == 4.0

    def test_zero_width_invalid(self):
        with pytest.raises(ValidationError):
            BoxParams(width=0.0)

    def test_negative_depth_invalid(self):
        with pytest.raises(ValidationError):
            BoxParams(depth=-1.0)

    def test_negative_height_invalid(self):
        with pytest.raises(ValidationError):
            BoxParams(height=-0.001)

    def test_layer_and_name(self):
        b = BoxParams(layer="Walls", name="MyBox")
        assert b.layer == "Walls"
        assert b.name == "MyBox"

    def test_model_dump_includes_corner(self):
        b = BoxParams(corner=Point3D(x=1.0, y=2.0, z=3.0))
        d = b.model_dump()
        assert d["corner"]["x"] == 1.0


class TestSphereParams:

    def test_defaults(self):
        s = SphereParams()
        assert s.radius == 1.0
        assert s.center.x == 0.0

    def test_zero_radius_invalid(self):
        with pytest.raises(ValidationError):
            SphereParams(radius=0.0)

    def test_negative_radius_invalid(self):
        with pytest.raises(ValidationError):
            SphereParams(radius=-5.0)


class TestCylinderParams:

    def test_defaults(self):
        c = CylinderParams()
        assert c.height == 1.0
        assert c.radius == 1.0
        assert c.cap is True

    def test_uncapped(self):
        c = CylinderParams(cap=False)
        assert c.cap is False

    def test_zero_height_invalid(self):
        with pytest.raises(ValidationError):
            CylinderParams(height=0.0)

    def test_zero_radius_invalid(self):
        with pytest.raises(ValidationError):
            CylinderParams(radius=0.0)


class TestConeParams:

    def test_defaults(self):
        c = ConeParams()
        assert c.radius == 1.0
        assert c.height == 1.0
        assert c.cap is True

    def test_invalid_radius(self):
        with pytest.raises(ValidationError):
            ConeParams(radius=0.0)


class TestTorusParams:

    def test_defaults(self):
        t = TorusParams()
        assert t.major_radius == 2.0
        assert t.minor_radius == 0.5

    def test_zero_major_invalid(self):
        with pytest.raises(ValidationError):
            TorusParams(major_radius=0.0)

    def test_zero_minor_invalid(self):
        with pytest.raises(ValidationError):
            TorusParams(minor_radius=0.0)


class TestCurveParams:

    def _two_points(self):
        return [Point3D(x=0.0), Point3D(x=1.0)]

    def test_valid_minimum(self):
        c = CurveParams(points=self._two_points())
        assert len(c.points) == 2
        assert c.degree == 3
        assert c.interpolate is True

    def test_requires_at_least_two_points(self):
        with pytest.raises(ValidationError):
            CurveParams(points=[Point3D()])

    def test_degree_bounds(self):
        # degree=1 is valid
        c = CurveParams(points=self._two_points(), degree=1)
        assert c.degree == 1
        # degree=11 is valid
        c = CurveParams(points=self._two_points(), degree=11)
        assert c.degree == 11

    def test_degree_out_of_range(self):
        with pytest.raises(ValidationError):
            CurveParams(points=self._two_points(), degree=0)
        with pytest.raises(ValidationError):
            CurveParams(points=self._two_points(), degree=12)

    def test_optional_weights_and_knots(self):
        c = CurveParams(
            points=self._two_points(),
            weights=[1.0, 1.0],
            knots=[0.0, 0.0, 1.0, 1.0],
        )
        assert c.weights == [1.0, 1.0]
        assert c.knots is not None


class TestPolylineParams:

    def test_valid(self):
        pts = [{"x": 0, "y": 0, "z": 0}, {"x": 1, "y": 0, "z": 0}]
        p = PolylineParams(points=[Point3D(**pt) for pt in pts])
        assert p.closed is False

    def test_requires_two_points(self):
        with pytest.raises(ValidationError):
            PolylineParams(points=[Point3D()])


class TestLineParams:

    def test_defaults(self):
        line = LineParams()
        assert line.start.x == 0.0
        assert line.end.x == 1.0

    def test_model_dump(self):
        line = LineParams(start=Point3D(x=0.0), end=Point3D(x=5.0))
        d = line.model_dump()
        assert d["end"]["x"] == 5.0


class TestArcParams:

    def test_defaults(self):
        a = ArcParams()
        assert a.radius == 1.0
        assert a.start_angle == 0.0
        assert a.end_angle == 180.0

    def test_zero_radius_invalid(self):
        with pytest.raises(ValidationError):
            ArcParams(radius=0.0)

    def test_optional_plane(self):
        a = ArcParams(plane=Plane())
        assert a.plane is not None


class TestCircleParams:

    def test_defaults(self):
        c = CircleParams()
        assert c.radius == 1.0

    def test_zero_radius_invalid(self):
        with pytest.raises(ValidationError):
            CircleParams(radius=0.0)


class TestExtrudeParams:

    def test_requires_profile_guid(self):
        with pytest.raises(ValidationError):
            ExtrudeParams()  # profile_guid is required

    def test_valid(self):
        e = ExtrudeParams(profile_guid="guid-123")
        assert e.profile_guid == "guid-123"
        assert e.distance == 1.0
        assert e.cap is True

    def test_zero_distance_invalid(self):
        with pytest.raises(ValidationError):
            ExtrudeParams(profile_guid="x", distance=0.0)


class TestLoftParams:

    def test_requires_two_curve_guids(self):
        with pytest.raises(ValidationError):
            LoftParams(curve_guids=["only-one"])

    def test_valid(self):
        loft = LoftParams(curve_guids=["g1", "g2"])
        assert loft.loft_type == "Normal"
        assert loft.closed is False

    def test_model_dump(self):
        loft = LoftParams(curve_guids=["g1", "g2", "g3"])
        d = loft.model_dump()
        assert d["curve_guids"] == ["g1", "g2", "g3"]


class TestRevolutionParams:

    def test_requires_profile_guid(self):
        with pytest.raises(ValidationError):
            RevolutionParams()

    def test_valid(self):
        r = RevolutionParams(profile_guid="p-guid")
        assert r.start_angle == 0.0
        assert r.end_angle == 360.0


class TestPatchParams:

    def test_requires_at_least_one_guid(self):
        with pytest.raises(ValidationError):
            PatchParams(input_guids=[])

    def test_valid(self):
        p = PatchParams(input_guids=["g1"])
        assert p.u_spans == 10
        assert p.v_spans == 10
        assert p.trim is True


class TestMeshFromSurfaceParams:

    def test_requires_source_guid(self):
        with pytest.raises(ValidationError):
            MeshFromSurfaceParams()

    def test_valid(self):
        m = MeshFromSurfaceParams(source_guid="s-guid")
        assert m.refine_mesh is True
        assert m.simple_planes is False
        assert m.max_edge_length is None

    def test_zero_max_edge_length_invalid(self):
        with pytest.raises(ValidationError):
            MeshFromSurfaceParams(source_guid="s", max_edge_length=0.0)


# ===========================================================================
# scene.py
# ===========================================================================

class TestDocumentInfo:

    def test_defaults(self):
        d = DocumentInfo()
        assert d.file_path is None
        assert d.units == "Millimeters"
        assert d.tolerance == 0.001
        assert d.angle_tolerance == 1.0
        assert d.object_count == 0
        assert d.layer_count == 0
        assert d.is_modified is False

    def test_custom_values(self):
        d = DocumentInfo(
            file_path="/tmp/model.3dm",
            units="Meters",
            object_count=5,
            is_modified=True,
        )
        assert d.file_path == "/tmp/model.3dm"
        assert d.units == "Meters"
        assert d.object_count == 5
        assert d.is_modified is True

    def test_object_count_non_negative(self):
        with pytest.raises(ValidationError):
            DocumentInfo(object_count=-1)

    def test_layer_count_non_negative(self):
        with pytest.raises(ValidationError):
            DocumentInfo(layer_count=-1)

    def test_model_dump(self):
        d = DocumentInfo(units="Feet")
        dump = d.model_dump()
        assert dump["units"] == "Feet"
        assert "file_path" in dump


class TestLayerInfo:

    def test_required_fields(self):
        with pytest.raises(ValidationError):
            LayerInfo()  # name and full_path are required

    def test_valid(self):
        li = LayerInfo(name="Walls", full_path="Site::Walls")
        assert li.name == "Walls"
        assert li.full_path == "Site::Walls"
        assert li.visible is True
        assert li.locked is False
        assert li.parent is None

    def test_with_parent(self):
        li = LayerInfo(name="Walls", full_path="Site::Walls", parent="Site")
        assert li.parent == "Site"

    def test_object_count_non_negative(self):
        with pytest.raises(ValidationError):
            LayerInfo(name="X", full_path="X", object_count=-1)

    def test_model_dump(self):
        li = LayerInfo(name="L", full_path="L")
        d = li.model_dump()
        assert d["name"] == "L"
        assert "color" in d


class TestLayerCreateParams:

    def test_requires_name(self):
        with pytest.raises(ValidationError):
            LayerCreateParams()

    def test_valid(self):
        lc = LayerCreateParams(name="NewLayer")
        assert lc.visible is True
        assert lc.locked is False
        assert lc.parent is None
        assert lc.color is None


class TestObjectInfo:

    def test_requires_guid_and_type(self):
        with pytest.raises(ValidationError):
            ObjectInfo()

    def test_valid(self):
        oi = ObjectInfo(guid="abc-123", type="brep")
        assert oi.guid == "abc-123"
        assert oi.type == "brep"
        assert oi.visible is True
        assert oi.locked is False
        assert oi.user_text == {}

    def test_with_bounding_box(self):
        bb = BoundingBox(
            min=Point3D(x=0.0, y=0.0, z=0.0),
            max=Point3D(x=1.0, y=1.0, z=1.0),
        )
        oi = ObjectInfo(guid="g", type="mesh", bounding_box=bb)
        assert oi.bounding_box is not None
        assert oi.bounding_box.max.x == 1.0

    def test_model_dump(self):
        oi = ObjectInfo(guid="g", type="curve")
        d = oi.model_dump()
        assert d["guid"] == "g"
        assert d["type"] == "curve"


class TestObjectFilter:

    def test_all_optional(self):
        f = ObjectFilter()
        assert f.layer is None
        assert f.object_type is None
        assert f.name is None
        assert f.visible_only is False
        assert f.unlocked_only is False

    def test_partial_filter(self):
        f = ObjectFilter(layer="Site::Walls", visible_only=True)
        assert f.layer == "Site::Walls"
        assert f.visible_only is True


class TestViewInfo:

    def test_requires_name(self):
        with pytest.raises(ValidationError):
            ViewInfo()

    def test_valid(self):
        v = ViewInfo(name="Perspective")
        assert v.name == "Perspective"
        assert v.is_perspective is False

    def test_with_camera(self):
        v = ViewInfo(
            name="Top",
            camera_location=[0.0, 0.0, 100.0],
            camera_target=[0.0, 0.0, 0.0],
        )
        assert v.camera_location == [0.0, 0.0, 100.0]


class TestSelectionResult:

    def test_defaults(self):
        s = SelectionResult()
        assert s.selected_count == 0
        assert s.guids == []
        assert s.message is None

    def test_with_guids(self):
        s = SelectionResult(selected_count=2, guids=["g1", "g2"])
        assert s.selected_count == 2
        assert len(s.guids) == 2

    def test_negative_count_invalid(self):
        with pytest.raises(ValidationError):
            SelectionResult(selected_count=-1)
