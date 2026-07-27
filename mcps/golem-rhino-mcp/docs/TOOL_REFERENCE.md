# GOLEM-3DMCP — Tool Reference

Complete reference for all 105 tools, organized by category. Each tool is accessible from Claude Code when the GOLEM-3DMCP MCP server is active.

**Conventions used in this document:**

- Parameter types: `str`, `float`, `int`, `bool`, `list[float]` (three numbers), `list[str]` (list of GUIDs)
- `optional` parameters have a default value shown in parentheses
- All GUIDs are returned as strings in the format `"xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"`
- `[x, y, z]` means a JSON array of three floats, e.g. `[10.0, 0.0, 5.0]`

---

## Category 1 — Scene Intelligence (10 tools)

Query and manage the Rhino document structure: metadata, layers, objects, groups, and block definitions.

### `scene.get_document_info`

Return high-level metadata about the currently open Rhino document.

**Parameters:** none

**Returns:**
```json
{
  "file_path": "/path/to/model.3dm",
  "units": "Millimeters",
  "absolute_tolerance": 0.01,
  "angle_tolerance": 1.0,
  "object_count": 42,
  "layer_count": 8
}
```

---

### `scene.list_layers`

Return all layers in the document.

**Parameters:** none

**Returns:** `{"layers": [...]}`

Each layer object contains:
```json
{
  "name": "Structure",
  "full_path": "Building::Structure",
  "color": {"r": 255, "g": 0, "b": 0, "a": 255},
  "visible": true,
  "locked": false,
  "parent_name": "Building",
  "object_count": 12,
  "is_current": false
}
```

---

### `scene.list_objects`

Return document objects with optional filtering and pagination.

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `object_type` | str | `"all"` | Filter by type: `"point"`, `"curve"`, `"surface"`, `"brep"`, `"mesh"`, `"extrusion"`, `"subd"`, `"annotation"`, `"light"`, or `"all"` |
| `layer` | str | none | Restrict to objects on this layer (full path) |
| `name_pattern` | str | none | Wildcard pattern (fnmatch style) matched against object names |
| `selected_only` | bool | `false` | Return only currently selected objects |
| `offset` | int | `0` | Skip this many objects before collecting (for pagination) |
| `limit` | int | `100` | Maximum objects to return; `0` means no cap |

**Returns:**
```json
{
  "objects": [...],
  "total": 150,
  "offset": 0,
  "limit": 100
}
```

---

### `scene.get_object_info`

Return full geometry details and attributes for a single object.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `guid` | str | yes | Object GUID |

**Returns:** Serialised object dict plus `geometry_detail` and `attributes` keys containing detailed geometry data and all object attributes.

---

### `scene.get_selected_objects`

Return all currently selected objects in the Rhino viewport.

**Parameters:** none

**Returns:** `{"objects": [...]}`

---

### `scene.get_groups`

Return all groups defined in the document.

**Parameters:** none

**Returns:**
```json
{
  "groups": [
    {
      "name": "Frame",
      "index": 0,
      "member_count": 4,
      "member_guids": ["guid1", "guid2", "guid3", "guid4"]
    }
  ]
}
```

---

### `scene.get_blocks`

Return all block (instance) definitions in the document.

**Parameters:** none

**Returns:**
```json
{
  "blocks": [
    {
      "name": "Column",
      "description": "Structural column",
      "object_count": 3,
      "geometry_guids": ["guid1", "guid2", "guid3"],
      "is_referenced": false
    }
  ]
}
```

---

### `scene.create_layer`

Create a new layer in the document.

**Parameters:**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `name` | str | yes | — | Layer name; use `::` separator for nested paths |
| `color` | dict | no | black | `{"r": 0, "g": 0, "b": 0, "a": 255}` |
| `parent_name` | str | no | none | Full path of parent layer |
| `visible` | bool | no | `true` | |
| `locked` | bool | no | `false` | |

**Returns:** `{"layer_index": 5, "full_path": "Building::Structure", "success": true}`

---

### `scene.delete_layer`

Delete a layer from the document.

**Parameters:**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `name` | str | yes | — | Full layer path |
| `delete_objects` | bool | no | `false` | If `true`, also delete all objects on the layer |

**Returns:** `{"success": true, "deleted_objects": 0, "message": "Layer 'X' deleted."}`

**Errors:** Raises if the layer is the current active layer, or if it has objects and `delete_objects` is `false`.

---

### `scene.set_current_layer`

Set the active (current) layer by name.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `name` | str | yes | Full layer path |

**Returns:** `{"success": true, "layer_index": 2, "full_path": "Structure"}`

**Errors:** Raises if the layer is hidden or locked.

---

## Category 2 — Geometry Creation (12 tools)

Create primitive solids, curves, points, and text objects.

### `create_box`

Create an axis-aligned rectangular box.

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `corner_x` | float | `0.0` | X of minimum corner |
| `corner_y` | float | `0.0` | Y of minimum corner |
| `corner_z` | float | `0.0` | Z of minimum corner |
| `width` | float | `1.0` | Dimension along X |
| `depth` | float | `1.0` | Dimension along Y |
| `height` | float | `1.0` | Dimension along Z |
| `layer` | str | current | Layer full path |
| `name` | str | none | Object name |

**Returns:** `{"guid": "...", "bounding_box": {...}}`

**Example:** `create_box(width=100, depth=50, height=30)` creates a 100×50×30 box at the origin.

---

### `create_sphere`

Create a sphere.

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `center_x` | float | `0.0` | X of centre |
| `center_y` | float | `0.0` | Y of centre |
| `center_z` | float | `0.0` | Z of centre |
| `radius` | float | `1.0` | Sphere radius |
| `layer` | str | current | Layer full path |
| `name` | str | none | Object name |

**Returns:** `{"guid": "...", "bounding_box": {...}}`

---

### `create_cylinder`

Create a cylinder aligned to the Z axis.

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `base_x` | float | `0.0` | X of base centre |
| `base_y` | float | `0.0` | Y of base centre |
| `base_z` | float | `0.0` | Z of base centre |
| `radius` | float | `1.0` | Cylinder radius |
| `height` | float | `1.0` | Cylinder height (along Z) |
| `cap` | bool | `true` | Cap the top and bottom |
| `layer` | str | current | Layer full path |
| `name` | str | none | Object name |

**Returns:** `{"guid": "...", "bounding_box": {...}}`

---

### `create_cone`

Create a cone aligned to the Z axis.

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `base_x` | float | `0.0` | X of base centre |
| `base_y` | float | `0.0` | Y of base centre |
| `base_z` | float | `0.0` | Z of base centre |
| `radius` | float | `1.0` | Base radius |
| `height` | float | `1.0` | Height along Z |
| `cap` | bool | `true` | Cap the base |
| `layer` | str | current | Layer |
| `name` | str | none | Object name |

**Returns:** `{"guid": "...", "bounding_box": {...}}`

---

### `create_torus`

Create a torus in the XY plane.

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `center_x` | float | `0.0` | X of centre |
| `center_y` | float | `0.0` | Y of centre |
| `center_z` | float | `0.0` | Z of centre |
| `major_radius` | float | `2.0` | Distance from torus centre to tube centre |
| `minor_radius` | float | `0.5` | Tube radius |
| `layer` | str | current | Layer |
| `name` | str | none | Object name |

**Returns:** `{"guid": "...", "bounding_box": {...}}`

---

### `create_line`

Create a line segment.

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `start` | list[float] | `[0,0,0]` | Start point `[x, y, z]` |
| `end` | list[float] | `[1,0,0]` | End point `[x, y, z]` |
| `layer` | str | current | Layer |
| `name` | str | none | Object name |

**Returns:** `{"guid": "...", "length": 10.0}`

---

### `create_arc`

Create an arc on a plane.

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `center` | list[float] | `[0,0,0]` | Centre point |
| `radius` | float | `1.0` | Arc radius |
| `start_angle` | float | `0.0` | Start angle in degrees |
| `end_angle` | float | `90.0` | End angle in degrees |
| `plane` | str | `"xy"` | Plane: `"xy"`, `"yz"`, or `"xz"` |
| `layer` | str | current | Layer |
| `name` | str | none | Object name |

**Returns:** `{"guid": "...", "length": 15.7}`

---

### `create_circle`

Create a full circle.

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `center` | list[float] | `[0,0,0]` | Centre point |
| `radius` | float | `1.0` | Radius |
| `plane` | str | `"xy"` | Plane: `"xy"`, `"yz"`, or `"xz"` |
| `layer` | str | current | Layer |
| `name` | str | none | Object name |

**Returns:** `{"guid": "...", "circumference": 6.28}`

---

### `create_polyline`

Create a polyline through a list of points.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `points` | list of `[x,y,z]` | yes | Ordered vertex list (minimum 2 points) |
| `closed` | bool | no | Close back to first point (default `false`) |
| `layer` | str | no | Layer |
| `name` | str | no | Object name |

**Returns:** `{"guid": "...", "point_count": 5, "length": 42.3}`

---

### `create_nurbs_curve`

Create a NURBS curve from control points.

**Parameters:**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `points` | list of `[x,y,z]` | yes | — | Control points (minimum 2) |
| `degree` | int | no | `3` | NURBS degree (1–11) |
| `closed` | bool | no | `false` | Periodic closure |
| `layer` | str | no | current | Layer |
| `name` | str | no | none | Object name |

**Returns:** `{"guid": "...", "degree": 3, "point_count": 6, "length": 55.2}`

---

### `create_point`

Create a point object.

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `x` | float | `0.0` | X coordinate |
| `y` | float | `0.0` | Y coordinate |
| `z` | float | `0.0` | Z coordinate |
| `layer` | str | current | Layer |
| `name` | str | none | Object name |

**Returns:** `{"guid": "...", "location": [0.0, 0.0, 0.0]}`

---

### `create_text`

Create a text annotation object.

**Parameters:**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `text` | str | yes | — | Text content |
| `location` | list[float] | no | `[0,0,0]` | Insertion point |
| `height` | float | no | `1.0` | Text height in model units |
| `font` | str | no | `"Arial"` | Font name |
| `plane` | str | no | `"xy"` | Annotation plane: `"xy"`, `"yz"`, `"xz"` |
| `layer` | str | no | current | Layer |
| `name` | str | no | none | Object name |

**Returns:** `{"guid": "..."}`

---

## Category 3 — Geometry Operations (19 tools)

Boolean operations, trim/split, offsets, fillets, chamfers, intersections, meshing, and curve/surface rebuilding.

### `operations.boolean_union`

Boolean union of two or more closed Breps. Consumes all inputs.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `guids` | list[str] | yes | Two or more closed Brep GUIDs |

**Returns:** `{"guids": [...], "count": 1, "objects": [...]}`

---

### `operations.boolean_difference`

Subtract cutter Breps from a target Brep. Consumes all inputs.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `guid_a` | str | yes | GUID of the Brep to cut from |
| `guids_b` | list[str] | yes | GUIDs of the cutting Breps |

**Returns:** `{"guids": [...], "count": int, "objects": [...]}`

---

### `operations.boolean_intersection`

Retain only the volume common to two sets of Breps. Consumes all inputs.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `guids_a` | list[str] | yes | First set of closed Brep GUIDs |
| `guids_b` | list[str] | yes | Second set of closed Brep GUIDs |

**Returns:** `{"guids": [...], "count": int, "objects": [...]}`

---

### `operations.boolean_split`

Divide a Brep with a cutter, returning all resulting pieces. Consumes both inputs.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `guid_to_split` | str | yes | GUID of the Brep to split |
| `guid_cutter` | str | yes | GUID of the cutting Brep |

**Returns:** `{"guids": [...], "count": int, "objects": [...]}`

---

### `operations.trim`

Trim a Brep using a cutter, keeping the side nearest to `pick_point`. Consumes the target; preserves the cutter.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `object_id` | str | yes | GUID of the Brep to trim |
| `cutter_id` | str | yes | GUID of the cutting surface/Brep |
| `pick_point` | list[float] | yes | `[x, y, z]` point indicating which side to keep |

**Returns:** `{"guids": ["..."], "count": 1, "object": {...}}`

---

### `operations.split`

Split a Brep with one or more cutters, returning all pieces. Consumes the target.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `object_id` | str | yes | GUID of the Brep to split |
| `cutter_ids` | list[str] | yes | GUIDs of the cutting Breps |

**Returns:** `{"guids": [...], "count": int, "objects": [...]}`

---

### `operations.offset_curve`

Offset a curve by a distance. Preserves the original.

**Parameters:**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `curve_id` | str | yes | — | GUID of the curve to offset |
| `distance` | float | yes | — | Offset distance (positive = left of direction) |
| `direction_point` | list[float] | no | Z-up | `[x, y, z]` point that determines the offset side and plane |
| `plane` | dict | no | none | Explicit offset plane: `{"origin": [...], "x_axis": [...], "y_axis": [...]}` |

**Returns:** `{"guid": "...", "curve": {...}}`

---

### `operations.offset_surface`

Offset a surface in the normal direction. Preserves the original.

**Parameters:**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `surface_id` | str | yes | — | GUID of the surface |
| `distance` | float | yes | — | Offset distance (positive = outward normal) |
| `both_sides` | bool | no | `false` | Offset in both normal directions |

**Returns:** `{"guid": "...", "surface": {...}}`

---

### `operations.fillet_edge`

Fillet specified edges of a Brep by radius. Replaces the input Brep.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `brep_id` | str | yes | GUID of the Brep |
| `edge_indices` | list[int] | yes | 0-based edge indices (from `Brep.Edges`) |
| `radius` | float | yes | Fillet radius |

**Returns:** `{"guids": [...], "count": int, "objects": [...]}`

---

### `operations.fillet_curves`

Create a fillet arc between two coplanar curves.

**Parameters:**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `curve_id_a` | str | yes | — | GUID of first curve |
| `curve_id_b` | str | yes | — | GUID of second curve |
| `radius` | float | yes | — | Fillet arc radius |
| `join` | bool | no | `false` | Join trimmed curves and arc into a polycurve |

**Returns:** `{"guid": "...", "curve": {...}}` or joined result

---

### `operations.chamfer_curves`

Create a chamfer line between two intersecting curves.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `curve_id_a` | str | yes | GUID of first curve |
| `curve_id_b` | str | yes | GUID of second curve |
| `distance_a` | float | yes | Chamfer distance along first curve |
| `distance_b` | float | yes | Chamfer distance along second curve |

**Returns:** `{"guid": "...", "curve": {...}}`

---

### `operations.chamfer_edge`

Chamfer specified edges of a Brep. Replaces the input Brep.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `brep_id` | str | yes | GUID of the Brep |
| `edge_indices` | list[int] | yes | 0-based edge indices |
| `distance` | float | yes | Symmetric chamfer distance |

**Returns:** `{"guids": [...], "count": int, "objects": [...]}`

---

### `operations.intersect`

Compute the intersection of two objects. Auto-detects curve/surface/Brep combinations.

- Curve + Curve → intersection points
- Curve + Brep → intersection points and overlap curves
- Brep + Brep → intersection curves

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `id_a` | str | yes | GUID of first object |
| `id_b` | str | yes | GUID of second object |

**Returns:**
```json
{
  "type": "curve_brep",
  "intersects": true,
  "point_guids": ["..."],
  "curve_guids": ["..."],
  "points": [...],
  "curves": [...]
}
```

---

### `operations.mesh_from_brep`

Generate a render mesh from a Brep. Preserves the original.

**Parameters:**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `brep_id` | str | yes | — | GUID of the Brep to mesh |
| `quality` | str | no | `"medium"` | `"coarse"`, `"medium"`, `"fine"`, or `"custom"` |
| `max_edge_length` | float | no | preset | Maximum mesh edge length |
| `min_edge_length` | float | no | preset | Minimum mesh edge length |
| `max_angle` | float | no | preset | Maximum angle between adjacent face normals (degrees) |

**Returns:** `{"guids": [...], "count": int, "meshes": [...]}`

---

### `operations.project_curve`

Project a curve onto Breps along a direction vector. Preserves originals.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `curve_id` | str | yes | GUID of curve to project |
| `brep_ids` | list[str] | yes | GUIDs of target Breps |
| `direction` | list[float] | yes | Projection direction `[x, y, z]` |

**Returns:** `{"guids": [...], "count": int, "curves": [...]}`

---

### `operations.extend_curve`

Extend a curve by length or to a boundary object. Replaces the original.

**Parameters:**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `curve_id` | str | yes | — | GUID of curve to extend |
| `extension_type` | str | no | `"smooth"` | `"line"`, `"arc"`, or `"smooth"` |
| `side` | str | no | `"end"` | `"start"`, `"end"`, or `"both"` |
| `length` | float | no | — | Extension length (used when no `boundary_id`) |
| `boundary_id` | str | no | — | GUID of boundary object to extend to |

**Returns:** `{"guid": "...", "curve": {...}}`

---

### `operations.blend_curves`

Create a blend curve connecting the endpoints of two curves.

**Parameters:**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `curve_id_a` | str | yes | — | GUID of first curve |
| `curve_id_b` | str | yes | — | GUID of second curve |
| `continuity` | str | no | `"tangent"` | `"position"`, `"tangent"`, or `"curvature"` |

**Returns:** `{"guid": "...", "curve": {...}}`

---

### `operations.rebuild_curve`

Rebuild a curve to a specified degree and control point count. Replaces the original.

**Parameters:**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `curve_id` | str | yes | — | GUID of curve |
| `degree` | int | no | `3` | NURBS degree (1–11) |
| `point_count` | int | no | `10` | Control point count (>= degree + 1) |

**Returns:** `{"guid": "...", "curve": {...}}`

---

### `operations.rebuild_surface`

Rebuild a NURBS surface to specified degrees and point counts. Replaces the original.

**Parameters:**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `surface_id` | str | yes | — | GUID of surface |
| `degree_u` | int | no | `3` | NURBS degree in U (1–11) |
| `degree_v` | int | no | `3` | NURBS degree in V (1–11) |
| `point_count_u` | int | no | `10` | Control points in U |
| `point_count_v` | int | no | `10` | Control points in V |

**Returns:** `{"guid": "...", "surface": {...}}`

---

## Category 4 — Surface Operations (12 tools)

Create complex surfaces through lofting, sweeping, revolving, extruding, patching, and unrolling.

### `surfaces.loft`

Create a loft surface through ordered cross-section curves.

**Parameters:**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `curve_ids` | list[str] | yes | — | Ordered GUIDs of cross-section curves (minimum 2) |
| `loft_type` | str | no | `"normal"` | `"normal"`, `"loose"`, `"tight"`, `"straight"`, `"developable"`, `"uniform"` |
| `closed` | bool | no | `false` | Close loft back to first section |
| `start_point` | list[float] | no | none | Tangent start point |
| `end_point` | list[float] | no | none | Tangent end point |

**Returns:** `{"guid": "...", "bounding_box": {...}}`

---

### `surfaces.sweep1`

Sweep cross-section curves along a single rail.

**Parameters:**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `rail_id` | str | yes | — | GUID of the rail (path) curve |
| `shape_ids` | list[str] | yes | — | Ordered GUIDs of cross-section curves |
| `closed` | bool | no | `false` | Close the sweep |

**Returns:** `{"guid": "...", "bounding_box": {...}}`

---

### `surfaces.sweep2`

Sweep cross-section curves along two rails.

**Parameters:**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `rail1_id` | str | yes | — | GUID of first rail |
| `rail2_id` | str | yes | — | GUID of second rail |
| `shape_ids` | list[str] | yes | — | Ordered GUIDs of cross-section curves |
| `closed` | bool | no | `false` | Close the sweep |

**Returns:** `{"guid": "...", "bounding_box": {...}}`

---

### `surfaces.revolve`

Revolve a profile curve around an axis to create a surface of revolution.

**Parameters:**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `curve_id` | str | yes | — | GUID of the profile curve |
| `axis_start` | list[float] | yes | — | Start point of revolution axis `[x, y, z]` |
| `axis_end` | list[float] | yes | — | End point of revolution axis `[x, y, z]` |
| `start_angle` | float | no | `0.0` | Start angle in degrees |
| `end_angle` | float | no | `360.0` | End angle in degrees |

**Returns:** `{"guid": "...", "bounding_box": {...}}`

---

### `surfaces.extrude_curve`

Extrude a curve to create a surface or solid.

**Direction mode** (provide `direction`): extrudes in a straight line.
**Path mode** (provide `path_id`): extrudes along a curve.

**Parameters:**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `curve_id` | str | yes | — | GUID of curve to extrude |
| `direction` | list[float] | if no `path_id` | — | Extrusion direction vector `[x, y, z]` |
| `distance` | float | no | `1.0` | Scalar applied to direction |
| `path_id` | str | if no `direction` | — | GUID of path curve |
| `cap` | bool | no | `false` | Cap planar holes after extrusion |

**Returns:** `{"guid": "...", "bounding_box": {...}}`

---

### `surfaces.extrude_surface`

Extrude a surface or Brep face along a direction vector.

**Parameters:**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `surface_id` | str | yes | — | GUID of surface to extrude |
| `direction` | list[float] | yes | — | Extrusion direction `[x, y, z]` |
| `distance` | float | no | `1.0` | Extrusion distance |
| `cap` | bool | no | `false` | Cap planar holes |

**Returns:** `{"guid": "...", "bounding_box": {...}}`

---

### `surfaces.network_surface`

Create a surface from a network of U and V direction curves.

**Parameters:**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `curves_u` | list[str] | yes | — | GUIDs of curves in U direction |
| `curves_v` | list[str] | yes | — | GUIDs of curves in V direction |
| `continuity` | int | no | `1` | `0`=position, `1`=tangent, `2`=curvature |

**Returns:** `{"guid": "...", "bounding_box": {...}}`

---

### `surfaces.patch`

Fit a patch surface through curves and/or points.

**Parameters:**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `object_ids` | list[str] | yes | — | GUIDs of boundary curves and/or point objects |
| `spans_u` | int | no | `10` | Surface spans in U |
| `spans_v` | int | no | `10` | Surface spans in V |
| `flexibility` | float | no | `1.0` | Higher values allow more deviation from input |

**Returns:** `{"guid": "...", "bounding_box": {...}}`

---

### `surfaces.edge_surface`

Create a surface from 2, 3, or 4 boundary edge curves.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `curve_ids` | list[str] | yes | 2, 3, or 4 GUIDs of edge curves |

**Returns:** `{"guid": "...", "bounding_box": {...}}`

---

### `surfaces.cap_planar_holes`

Cap all planar holes in a Brep with flat surfaces. Modifies the Brep in place.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `brep_id` | str | yes | GUID of Brep to cap |

**Returns:** `{"guid": "...", "bounding_box": {...}, "caps_added": true}`

---

### `surfaces.unroll`

Unroll a developable surface or Brep face into a flat 2D layout.

**Parameters:**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `surface_id` | str | yes | — | GUID of surface or Brep to unroll |
| `explode` | bool | no | `false` | Explode multi-face Brep and unroll each face independently |

**Returns:** `{"guids": [...], "bounding_box": {...}}`

---

### `surfaces.planar_surface`

Create planar surfaces from closed planar boundary curves.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `curve_ids` | list[str] | yes | GUIDs of closed, planar boundary curves |

**Returns:** `{"guid": "...", "guids": [...], "bounding_box": {...}}`

---

## Category 5 — Object Manipulation (21 tools)

Transform, duplicate, array, group, join, and set properties on objects.

### `manipulation.move`

Translate objects by a vector. Modifies in place.

**Parameters:** `ids` (list[str], required), `translation` ([x,y,z], required — the displacement vector)

**Returns:** `{"moved_ids": [...], "count": int}`

---

### `manipulation.copy`

Copy objects and optionally displace the copies.

**Parameters:** `ids` (list[str], required), `translation` ([x,y,z], optional — default [0,0,0])

**Returns:** `{"new_ids": [...], "count": int}`

---

### `manipulation.rotate`

Rotate objects around an axis.

**Parameters:** `ids` (list[str]), `center` ([x,y,z]), `angle` (float, degrees), `axis` ([x,y,z], default [0,0,1] = Z-up), `copy` (bool, default false)

**Returns:** `{"result_ids": [...], "count": int}`

---

### `manipulation.scale`

Scale objects uniformly or non-uniformly.

**Parameters:** `ids` (list[str]), `origin` ([x,y,z]), `scale_factor` (float for uniform or [sx,sy,sz] for non-uniform), `copy` (bool, default false)

**Returns:** `{"result_ids": [...], "count": int}`

---

### `manipulation.mirror`

Mirror objects across a plane defined by two points.

**Parameters:** `ids` (list[str]), `start` ([x,y,z]), `end` ([x,y,z]), `copy` (bool, default false)

**Returns:** `{"result_ids": [...], "count": int}`

---

### `manipulation.orient`

Orient objects by mapping 2 or 3 reference points to target points (equivalent to Rhino's Orient command).

**Parameters:** `ids` (list[str]), `reference_points` (list of [x,y,z]), `target_points` (list of [x,y,z], same length), `copy` (bool, default false)

**Returns:** `{"result_ids": [...], "count": int}`

---

### `manipulation.shear`

Apply a shear transformation using a plane, angle, and direction.

**Parameters:** `ids` (list[str]), `plane` (dict with `origin`, `x_axis`, `y_axis`), `shear_angle` (float, degrees), `shear_direction` ([x,y,z]), `copy` (bool, default false)

**Returns:** `{"result_ids": [...], "count": int}`

---

### `manipulation.array_linear`

Create a linear array of an object along a direction vector.

**Parameters:** `id` (str), `count` (int, total items including original), `direction` ([x,y,z], spacing vector between copies)

**Returns:** `{"array_ids": [...], "count": int}`

---

### `manipulation.array_polar`

Create a polar (circular) array around a centre point.

**Parameters:** `id` (str), `count` (int), `center` ([x,y,z]), `angle` (float, total arc in degrees, default 360), `axis` ([x,y,z], default [0,0,1])

**Returns:** `{"array_ids": [...], "count": int}`

---

### `manipulation.array_along_curve`

Distribute copies of an object at evenly spaced points along a curve, optionally orienting each copy to the curve tangent.

**Parameters:** `id` (str), `curve_id` (str), `count` (int, number of copies), `orient` (bool, default true)

**Returns:** `{"array_ids": [...], "count": int}`

---

### `manipulation.apply_transform`

Apply an arbitrary 4×4 affine transformation matrix.

**Parameters:** `ids` (list[str]), `matrix` (4×4 nested list of floats, row-major), `copy` (bool, default false)

**Returns:** `{"result_ids": [...], "count": int}`

---

### `manipulation.delete`

Delete objects from the Rhino document.

**Parameters:** `ids` (list[str], required)

**Returns:** `{"deleted_count": int}`

---

### `manipulation.group`

Add objects to a new named group.

**Parameters:** `ids` (list[str], required), `name` (str, optional — auto-generated if omitted)

**Returns:** `{"group_name": "GroupA"}`

---

### `manipulation.ungroup`

Dissolve a group, freeing all member objects.

**Parameters:** `group_name` (str, required)

**Returns:** `{"freed_ids": [...], "count": int}`

---

### `manipulation.join`

Join multiple objects into one. Auto-detects curves vs. surfaces/Breps.

**Parameters:** `ids` (list[str], minimum 2), `delete_input` (bool, default true)

**Returns:** `{"joined_ids": [...], "count": int}`

---

### `manipulation.explode`

Explode a joined object into its component parts.

**Parameters:** `id` (str), `delete_input` (bool, default true)

**Returns:** `{"exploded_ids": [...], "count": int}`

---

### `manipulation.set_properties`

Set display/document properties on objects.

**Parameters:** `ids` (list[str], required), plus any of: `layer` (str), `color` ([r,g,b] or [r,g,b,a]), `name` (str), `visible` (bool), `locked` (bool), `material_index` (int)

**Returns:** `{"updated_ids": [...], "count": int, "applied": {...}}`

---

### `manipulation.set_user_text`

Set a user-text key/value pair on an object.

**Parameters:** `id` (str), `key` (str), `value` (str), `attached_to_geometry` (bool, default false)

**Returns:** `{"id": "...", "key": "...", "value": "...", "attached_to_geometry": false}`

---

### `manipulation.get_user_text`

Retrieve user-text from an object.

**Parameters:** `id` (str), `key` (str, optional — if omitted, returns all keys)

**Returns:** `{"id": "...", "user_text": "value"}` or `{"id": "...", "user_text": {"key1": "val1", ...}}`

---

### `manipulation.select_objects`

Select objects in the Rhino viewport.

**Parameters:** `ids` (list[str], required)

**Returns:** `{"selected_ids": [...], "count": int}`

---

### `manipulation.unselect_all`

Deselect all currently selected objects.

**Parameters:** none

**Returns:** `{"unselected_count": int}`

---

## Category 6 — Grasshopper (9 tools)

Control Grasshopper definitions: open/close files, list components, get/set parameters, recompute, bake, and query connections.

> **Note:** All Grasshopper tools require Grasshopper to be loaded in the current Rhino session. If it is not loaded, the tools return an error with `"GH not available"`.

### `grasshopper.open_definition`

Open a Grasshopper definition file.

**Parameters:** `path` (str, required — absolute path to `.gh` or `.ghx` file)

**Returns:** `{"success": true, "component_count": 42}`

---

### `grasshopper.close_definition`

Close the currently active Grasshopper definition.

**Parameters:** `save` (bool, default false)

**Returns:** `{"success": true}`

---

### `grasshopper.list_components`

List all components in the active Grasshopper definition.

**Parameters:** none

**Returns:**
```json
{
  "components": [
    {
      "name": "Number Slider",
      "nickname": "slider",
      "instance_guid": "...",
      "type": "GH_NumberSlider",
      "enabled": true
    }
  ]
}
```

---

### `grasshopper.get_param`

Get the current value of a Grasshopper input parameter.

**Parameters:** `component_name` (str, required), `param_name` (str, optional)

**Returns:** `{"value": 24.0, "type": "number"}`

---

### `grasshopper.set_param`

Set the value of a Grasshopper input parameter (e.g., a number slider).

**Parameters:** `component_name` (str, required), `value` (any, required), `param_name` (str, optional)

**Returns:** `{"success": true, "component_name": "PanelCount", "value": 24}`

---

### `grasshopper.recompute`

Trigger a full recompute of the active Grasshopper definition.

**Parameters:** none

**Returns:** `{"success": true}`

---

### `grasshopper.bake`

Bake geometry from a Grasshopper component output to the Rhino document.

**Parameters:** `component_name` (str, required), `layer` (str, optional)

**Returns:** `{"success": true, "baked_guids": [...], "count": int}`

---

### `grasshopper.run_definition`

Open a definition, optionally set parameters, recompute, and optionally bake — all in one call.

**Parameters:** `path` (str, required), `params` (dict of `{component_name: value}`, optional), `bake` (bool, default false), `bake_layer` (str, optional)

**Returns:** `{"success": true, "baked_guids": [...]}`

---

### `grasshopper.get_connections`

Return the connection (wire) topology of the active Grasshopper definition.

**Parameters:** none

**Returns:**
```json
{
  "connections": [
    {
      "from_component": "Number Slider",
      "from_param": "Value",
      "to_component": "Domain",
      "to_param": "A"
    }
  ]
}
```

---

## Category 7 — Viewport (11 tools)

Capture screenshots, control the camera, manage display modes, and save/restore named views.

### `viewport.capture`

Capture a viewport to a base64-encoded PNG.

**Parameters:** `view_name` (str, optional — active view if omitted), `width` (int, default 1920), `height` (int, default 1080)

**Returns:** `{"image_base64": "iVBORw...", "width": 1920, "height": 1080, "format": "png"}`

---

### `viewport.set_view`

Set a standard or named view.

**Parameters:** `view_name` (str, required — e.g., `"perspective"`, `"top"`, `"front"`, `"right"`)

**Returns:** `{"success": true, "view_name": "perspective"}`

---

### `viewport.zoom_object`

Zoom to the bounding box of specific objects.

**Parameters:** `guids` (list[str], required), `view_name` (str, optional)

**Returns:** `{"success": true}`

---

### `viewport.zoom_extents`

Zoom to extents of all objects.

**Parameters:** `view_name` (str, optional — if omitted, zooms all views), `all_views` (bool, default false)

**Returns:** `{"success": true}`

---

### `viewport.zoom_selected`

Zoom to currently selected objects.

**Parameters:** `view_name` (str, optional)

**Returns:** `{"success": true}`

---

### `viewport.set_display_mode`

Change the display mode of a viewport.

**Parameters:** `mode` (str, required — e.g., `"Shaded"`, `"Wireframe"`, `"Rendered"`, `"Arctic"`, `"Ghosted"`), `view_name` (str, optional)

**Returns:** `{"success": true, "mode": "Shaded"}`

---

### `viewport.set_camera`

Set the camera position, target, and lens length.

**Parameters:** `location` ([x,y,z], optional), `target` ([x,y,z], optional), `lens_length` (float, optional — in mm), `view_name` (str, optional)

**Returns:** `{"success": true}`

---

### `viewport.create_named_view`

Save the current camera as a named view.

**Parameters:** `name` (str, required), `view_name` (str, optional)

**Returns:** `{"success": true, "name": "FrontElevation"}`

---

### `viewport.restore_named_view`

Restore a previously saved named view.

**Parameters:** `name` (str, required), `view_name` (str, optional)

**Returns:** `{"success": true}`

---

### `viewport.list_named_views`

Return all saved named view names.

**Parameters:** none

**Returns:** `{"named_views": ["FrontElevation", "IsometricView", ...]}`

---

### `viewport.get_view_info`

Return camera and viewport metadata for a view.

**Parameters:** `view_name` (str, optional)

**Returns:**
```json
{
  "view_name": "Perspective",
  "display_mode": "Shaded",
  "camera_location": [10.0, -20.0, 15.0],
  "camera_target": [0.0, 0.0, 0.0],
  "lens_length": 50.0,
  "is_perspective": true
}
```

---

## Category 8 — File Operations (7 tools)

Open, save, import, and export Rhino documents and geometry.

### `files.get_document_path`

Return the file path of the currently open Rhino document.

**Parameters:** none

**Returns:** `{"path": "/Users/me/model.3dm", "is_saved": true}`

---

### `files.save_document`

Save the current document to its existing path.

**Parameters:** none

**Returns:** `{"success": true, "path": "/Users/me/model.3dm"}`

---

### `files.save_document_as`

Save the current document to a new path.

**Parameters:** `path` (str, required — absolute path with `.3dm` extension)

**Returns:** `{"success": true, "path": "/Users/me/model_v2.3dm"}`

---

### `files.new_document`

Create a new, empty Rhino document.

**Parameters:** `template` (str, optional — path to a `.3dm` template file)

**Returns:** `{"success": true}`

---

### `files.import_file`

Import geometry from a file into the current document.

**Parameters:** `path` (str, required — absolute path), `layer` (str, optional — import onto this layer)

**Returns:** `{"success": true, "imported_count": 12}`

---

### `files.export_objects`

Export specific objects to a file.

**Parameters:** `guids` (list[str], required), `path` (str, required — absolute path, extension determines format)

Supported export extensions: `.3dm`, `.stl`, `.obj`, `.step`, `.stp`, `.iges`, `.igs`, `.fbx`, `.3mf`, `.dwg`, `.dxf`, `.pdf`, `.3ds`, `.ply`, `.gltf`, `.glb`, `.usd`

**Returns:** `{"success": true, "path": "/output/model.stl", "size_bytes": 1024000}`

---

### `files.export_document`

Export the entire document to a file.

**Parameters:** `path` (str, required)

**Returns:** `{"success": true, "path": "/output/model.obj", "size_bytes": 2048000}`

---

## Category 9 — Script Execution (4 tools)

Execute arbitrary code inside Rhino. These are the most powerful — and least safe — tools in GOLEM-3DMCP.

### `scripting.execute_python`

Execute an arbitrary Python script inside Rhino's Python environment. Full access to RhinoCommon, rhinoscriptsyntax, and all loaded plugins.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `code` | str | yes | Python source code to execute |
| `timeout` | int | no | Execution timeout in seconds (default 30) |

**The `__result__` convention:** If the executed code assigns a value to `__result__`, that value is serialised and included in the response. This is the idiomatic way to return structured data from a script.

**Returns:**
```json
{
  "stdout": "Hello from Rhino\n",
  "stderr": "",
  "result": [1.0, 2.0, 3.0],
  "error": null
}
```

**Example:**
```python
code = """
import Rhino.Geometry as RG
pts = [RG.Point3d(i, i*2, 0) for i in range(5)]
__result__ = [(p.X, p.Y, p.Z) for p in pts]
"""
```

---

### `scripting.execute_rhinocommand`

Run a Rhino command string (equivalent to typing in the command line).

**Parameters:** `command` (str, required — e.g., `"_Zoom _Extents _Enter"`), `echo` (bool, default false — show command in Rhino history)

**Returns:** `{"success": true, "command": "_Zoom _Extents _Enter"}`

---

### `scripting.evaluate_expression`

Evaluate a single Python expression and return its value.

**Parameters:** `expression` (str, required — a single Python expression, not a statement)

**Returns:** `{"result": 42, "type": "int"}`

**Example:** `expression = "sc.doc.Objects.Count * 2"`

---

### `scripting.run_rhino_script`

Execute a RhinoScript (VBScript-compatible) string.

**Parameters:** `script` (str, required), `timeout` (int, optional)

**Returns:** `{"success": true, "output": "..."}`
