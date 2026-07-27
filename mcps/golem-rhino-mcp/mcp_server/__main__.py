"""
mcp_server/__main__.py
=======================
Package entry point for ``python -m mcp_server``.

This makes both of the following equivalent:

    python -m mcp_server
    python -m mcp_server.server

The ``.mcp.json`` configuration uses ``python -m mcp_server.server``, but
having ``__main__.py`` in the package root provides a convenient shorthand
for local development and testing.
"""

from mcp_server.server import main

main()
