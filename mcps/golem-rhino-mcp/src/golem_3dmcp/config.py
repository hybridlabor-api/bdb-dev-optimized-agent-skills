"""
GOLEM-3DMCP runtime configuration.

All values are read from environment variables at import time so that the
server can be reconfigured without code changes (e.g. for different Rhino
instances or CI environments).  Defaults are suitable for local development.
"""

import os

# ---------------------------------------------------------------------------
# Rhino TCP bridge
# ---------------------------------------------------------------------------

RHINO_HOST: str = os.environ.get("GOLEM_RHINO_HOST", "127.0.0.1")
RHINO_PORT: int = int(os.environ.get("GOLEM_RHINO_PORT", "9876"))

# Grasshopper sub-channel (separate port keeps GH traffic isolated)
RHINO_GH_PORT: int = int(os.environ.get("GOLEM_GH_PORT", "9877"))

# ---------------------------------------------------------------------------
# Timeouts (seconds)
# ---------------------------------------------------------------------------

# Default command timeout — fast operations (geometry queries, script eval)
COMMAND_TIMEOUT: int = int(os.environ.get("GOLEM_TIMEOUT", "30"))

# Heavy operations timeout — mesh generation, export, complex Grasshopper runs
HEAVY_TIMEOUT: int = int(os.environ.get("GOLEM_HEAVY_TIMEOUT", "120"))

# ---------------------------------------------------------------------------
# Connection resilience
# ---------------------------------------------------------------------------

RECONNECT_ATTEMPTS: int = 3
RECONNECT_DELAY: float = 2.0       # seconds between reconnect attempts
HEARTBEAT_INTERVAL: int = 10       # seconds between keep-alive pings
