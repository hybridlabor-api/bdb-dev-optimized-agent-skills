"""
mcp_server/tools
================
MCP tool wrappers for GOLEM-3DMCP.

Each module in this package exposes a set of FastMCP tool functions that
translate Claude Code / MCP client calls into JSON-RPC messages sent over the
TCP socket to the GOLEM-3DMCP server running inside Rhino 3D.

Tool modules
------------
scene
    Document-level queries and layer management.
    Methods: scene.get_document_info, scene.list_layers, scene.list_objects,
             scene.get_object_info, scene.get_selected_objects, scene.get_groups,
             scene.get_blocks, scene.create_layer, scene.delete_layer,
             scene.set_current_layer

creation
    Primitive and curve geometry creation.
    Methods: creation.create_box, creation.create_sphere, creation.create_cylinder,
             creation.create_cone, creation.create_torus, creation.create_line,
             creation.create_circle, creation.create_arc, creation.create_polyline,
             creation.create_nurbs_curve, creation.create_point, creation.create_text

operations
    Boolean operations, trimming, filleting, meshing, and curve/surface rebuilding.
    Methods: operations.boolean_union, operations.boolean_difference,
             operations.boolean_intersection, operations.boolean_split,
             operations.trim, operations.split, operations.offset_curve,
             operations.offset_surface, operations.fillet_edge,
             operations.fillet_curves, operations.chamfer_curves,
             operations.chamfer_edge, operations.intersect,
             operations.mesh_from_brep, operations.project_curve,
             operations.extend_curve, operations.blend_curves,
             operations.rebuild_curve, operations.rebuild_surface

surfaces
    Advanced surface generation from curves and existing geometry.
    Methods: surfaces.loft, surfaces.sweep1, surfaces.sweep2, surfaces.revolve,
             surfaces.extrude_curve, surfaces.extrude_surface,
             surfaces.network_surface, surfaces.patch, surfaces.edge_surface,
             surfaces.cap_planar_holes, surfaces.unroll, surfaces.planar_surface

manipulation
    Object transforms, array operations, grouping, and property editing.
    Methods: manipulation.move, manipulation.copy, manipulation.rotate,
             manipulation.scale, manipulation.mirror, manipulation.orient,
             manipulation.shear, manipulation.array_linear,
             manipulation.array_polar, manipulation.array_along_curve,
             manipulation.apply_transform, manipulation.delete,
             manipulation.group, manipulation.ungroup, manipulation.join,
             manipulation.explode, manipulation.set_properties,
             manipulation.set_user_text, manipulation.get_user_text,
             manipulation.select_objects, manipulation.unselect_all

grasshopper
    Grasshopper definition control: open, close, parameterise, bake, recompute.
    Methods: grasshopper.open_definition, grasshopper.close_definition,
             grasshopper.list_components, grasshopper.get_param,
             grasshopper.set_param, grasshopper.recompute, grasshopper.bake,
             grasshopper.run_definition, grasshopper.get_connections

viewport
    Viewport capture, camera control, display modes, and named views.
    Methods: viewport.capture, viewport.set_view, viewport.zoom_object,
             viewport.zoom_extents, viewport.zoom_selected,
             viewport.set_display_mode, viewport.set_camera,
             viewport.create_named_view, viewport.add_named_view,
             viewport.restore_named_view, viewport.list_named_views,
             viewport.get_view_info, viewport.set_background_color

files
    Document I/O: open, save, import, export in various formats.
    Methods: files.get_document_path, files.save_document,
             files.save_document_as, files.new_document, files.import_file,
             files.export_objects, files.export_document,
             files.export_selected, files.open_document

scripting
    Arbitrary Python execution, Rhino command dispatch, and expression evaluation.
    Methods: scripting.execute_python, scripting.execute_rhinocommand,
             scripting.evaluate_expression, scripting.run_rhino_script

Wire protocol
-------------
Every tool calls the module-private ``_send(method, params)`` helper, which
opens a short-lived TCP connection to ``127.0.0.1:9876`` (configurable via
``GOLEM_HOST`` / ``GOLEM_PORT`` environment variables), sends a length-prefixed
JSON-RPC request, and returns the decoded result dict or raises on error.

Python 3.9 compatibility
------------------------
All modules use ``typing.Dict``, ``typing.List``, ``typing.Optional`` instead of
the lowercase generic aliases introduced in Python 3.10.  No ``match/case``
statements are used.
"""
