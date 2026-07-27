FROM python:3.12-slim AS base

LABEL maintainer="Adam Djellouli <adam@djellouli.com>"
LABEL description="Blender MCP Server — headless mode (no addon bridge)"

WORKDIR /app

COPY pyproject.toml README.md LICENSE ./
COPY src/ src/
COPY addon/ addon/

RUN pip install --no-cache-dir .

# Blender is NOT bundled — mount or install Blender separately.
# The MCP server itself runs without Blender; headless transport
# needs BLENDER_BIN pointing to a blender binary.
ENV BLENDER_BIN=blender

ENTRYPOINT ["blender-mcp-server"]
