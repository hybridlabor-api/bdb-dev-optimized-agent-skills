# -*- coding: utf-8 -*-
"""
GOLEM-3DMCP Handler Registration

Import this module to register all handlers with the dispatcher.

Call ``register_all_handlers()`` once during server startup (e.g. from
``startup.py`` or ``server.start_server()``) before the first client
connection is accepted.  It is safe to call multiple times -- the dispatcher
simply overwrites any previously registered handler with the same name,
which is idempotent in practice because the same function objects are
re-registered.

Handler modules
---------------
scene        -- Document info, layer management, object queries
creation     -- Primitive geometry creation (box, sphere, cylinder, …)
operations   -- Boolean ops, mirroring, grouping, curve ops
surfaces     -- Extrude, loft, revolve, sweep, patch, …
manipulation -- Move, rotate, scale, copy, orient, align, …
grasshopper  -- Grasshopper definition control and baking
viewport     -- Viewport capture, camera, display mode, named views
files        -- Open, save, import, export
scripting    -- Execute Python / RhinoScript, run Rhino commands
"""

from rhino_plugin.dispatcher import register_handlers_from_module, get_registered_methods


def register_all_handlers():
    # type: () -> int
    """
    Import every handler module and register its handlers with the dispatcher.

    Each module uses the ``@handler("namespace.method_name")`` decorator
    which auto-registers handlers at import time.  Calling
    ``register_handlers_from_module`` afterwards is a belt-and-suspenders
    pass that also catches any handler functions that were defined before
    the decorator ran (edge case during hot-reload).

    Returns
    -------
    int
        Total number of registered method names after all modules are loaded.
    """
    from rhino_plugin.handlers import scene
    from rhino_plugin.handlers import creation
    from rhino_plugin.handlers import operations
    from rhino_plugin.handlers import surfaces
    from rhino_plugin.handlers import manipulation
    from rhino_plugin.handlers import grasshopper
    from rhino_plugin.handlers import viewport
    from rhino_plugin.handlers import files
    from rhino_plugin.handlers import scripting

    modules = [
        scene,
        creation,
        operations,
        surfaces,
        manipulation,
        grasshopper,
        viewport,
        files,
        scripting,
    ]

    for module in modules:
        register_handlers_from_module(module)

    return len(get_registered_methods())
