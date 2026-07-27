# =============================================================================
# GOLEM-3DMCP — Dockerfile for MCP Server Inspection
# =============================================================================
# This Dockerfile enables Glama.ai server inspection and tool detection.
# It packages the MCP server in a container that can be inspected via stdio.
#
# Build:   docker build -t golem-3dmcp .
# Run:     docker run -i golem-3dmcp
# Inspect: docker run -i golem-3dmcp python -m golem_3dmcp.server
# =============================================================================

FROM python:3.12-slim AS base

# Metadata
LABEL org.opencontainers.image.title="GOLEM-3DMCP"
LABEL org.opencontainers.image.description="The most powerful MCP server for Rhinoceros 3D — 105 tools giving AI full read/write access to Rhino 8"
LABEL org.opencontainers.image.source="https://github.com/TheKingHippopotamus/GOLEM-3DMCP-Rhino-"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.authors="TheKingHippopotamus"
LABEL ai.glama.mcp.server="true"
LABEL ai.glama.mcp.transport="stdio"

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install dependencies first (layer caching)
COPY pyproject.toml README.md LICENSE ./
COPY src/ ./src/

# Install the package
# Set fallback version for builds without .git (setuptools-scm / hatch-vcs)
ARG SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0
ENV SETUPTOOLS_SCM_PRETEND_VERSION=${SETUPTOOLS_SCM_PRETEND_VERSION}
RUN pip install --no-cache-dir .

# Default environment variables
ENV GOLEM_RHINO_HOST=127.0.0.1
ENV GOLEM_RHINO_PORT=9876
ENV GOLEM_GH_PORT=9877
ENV GOLEM_TIMEOUT=30

# Expose the MCP server via stdio transport
# The server reads from stdin and writes to stdout (MCP stdio protocol)
ENTRYPOINT ["python", "-m", "golem_3dmcp.server"]
