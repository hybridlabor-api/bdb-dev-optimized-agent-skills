"""
GOLEM-3DMCP — The most powerful MCP server for Rhinoceros 3D.

105 tools giving AI agents full read/write access to Rhino 8.
"""

try:
    from importlib.metadata import PackageNotFoundError, version
    try:
        __version__ = version("golem-3dmcp")
    except PackageNotFoundError:
        __version__ = "0.0.0-dev"
except ImportError:
    __version__ = "0.0.0-dev"

__all__ = ["__version__"]
