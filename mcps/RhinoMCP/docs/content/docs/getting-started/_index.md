---
title: Getting Started
icon: play
weight: 1
prev: /
next: docs/getting-started/connector
toc: false
author: Callum
editor: SteveF
keywords:
  - getting started
  - installation
  - setup
  - AI assistant
---

<blockquote class="page-alert">
This guide assumes you have <a href="https://www.rhino3d.com/download/">Rhino 3D</a> already installed and licensed.
</blockquote>

In about ten minutes you'll have your AI assistant making geometry in your Rhino and/or Grasshopper window. We'll do it in a couple steps:

## Pick an AI assistant

Any AI assistant that speaks the [Model Context Protocol](https://modelcontextprotocol.io) can drive Rhino & Grasshopper. *Choose one of the AI assistants below to continue.*

{{< cards >}}

  {{< card link="connector" icon="claude" title="Claude Desktop" subtitle="A friendly chat app from Anthropic. *Easiest to install and use.*" >}}

  {{< card link="cc-plugin" icon="claude" title="Claude Code" subtitle="A terminal-based (CLI) assistant that feels more like coding than chat." >}}

  {{< card link="copilot" icon="github" title="GitHub Copilot" subtitle="GitHub's AI assistant inside VS Code. Switch to Agent mode and point it to the Rhino MCP router." >}}

  {{< card link="codex" icon="chatgpt" title="OpenAI Codex" subtitle="OpenAI's terminal-based assistant (CLI). Point its MCP config at the Rhino MCP router and go." >}}

  {{< card link="gemini" icon="gemini" title="Gemini CLI" subtitle="Google's open-source terminal assistant (CLI). Drop the Rhino MCP router into its MCP config." >}}

  {{< card link="lm-studio" icon="lmstudio" title="Local LLM" subtitle="Run an open-weight model on your own machine and drive Rhino & Grasshopper without Internet." >}}

{{< /cards >}}

<blockquote class="page-note">
<strong>Other MCP clients work, too.</strong> <a href="https://cursor.com">Cursor</a> and other MCP-capable assistants can point at the same Rhino MCP router.
</blockquote>
