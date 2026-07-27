from __future__ import annotations

import asyncio
import contextlib

import uvicorn

from .api import app as fastapi_app
from .config import settings
from .mcp_server import run_server as run_mcp


async def main_async():
    config = uvicorn.Config(fastapi_app, host=settings.api_host, port=settings.api_port, log_level="info")
    server = uvicorn.Server(config)

    async def run_api():
        await server.serve()

    async def run_ws():
        await run_mcp()

    await asyncio.gather(run_api(), run_ws())


def main():
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(main_async())


if __name__ == "__main__":
    main()

