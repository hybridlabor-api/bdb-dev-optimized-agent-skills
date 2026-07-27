# 🎬 DaVinci Resolve MCP Bridge

### The only MCP server for DaVinci Resolve that works on the **Free version**.

> "Add a marker at 5 seconds." "Transcribe my timeline." "Remove the background from clip 1." "Render to MP4."
>
> Just talk to your AI assistant. It controls Resolve for you.

[![Free + Studio](https://img.shields.io/badge/DaVinci%20Resolve-Free%20%2B%20Studio-00b359.svg)](https://www.blackmagicdesign.com/products/davinciresolve)
[![Tools](https://img.shields.io/badge/MCP%20Tools-162-blue.svg)](#-162-tools-across-every-feature-of-resolve)
[![AI](https://img.shields.io/badge/Local%20AI-Voice%20%7C%20Background%20%7C%20Transcription-purple.svg)](#-built-in-ai-that-replaces-295-studio-features)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## 🤔 What Is This?

This project lets AI assistants like **Cursor**, **Claude**, or **Windsurf** control DaVinci Resolve through natural language. Instead of clicking through menus, you just *tell* the AI what to do — and it does it.

Think of it like giving your AI assistant a pair of hands inside DaVinci Resolve.

---

## ⚡ What Makes This Different?

Every other DaVinci Resolve MCP server requires the **$295 Studio version** because they use "external scripting" — a feature Blackmagic locks behind the paywall.

**This project works around that entirely.**

Instead of calling Resolve from the outside, a small bridge script runs *inside* Resolve (through the Scripts menu, which is available to everyone). That bridge opens a local connection, and the MCP server talks to it. Simple — and it works on the Free version.

```
Your AI Assistant (Cursor, Claude, etc.)
         │
         │  talks MCP
         ▼
  resolve_mcp_bridge.py     ← runs on your machine
         │
         │  talks HTTP (localhost)
         ▼
  CursorBridge.py           ← runs INSIDE Resolve (Workspace > Scripts)
         │
         ▼
  DaVinci Resolve API       ← full read + write access
```

**155 of 162 tools work on Free.** The 7 that don't are Studio's Neural Engine features — and for each one, this project includes a **free, local AI replacement** that runs on your CPU.

---

## 🧠 Built-In AI That Replaces $295 Studio Features

No API keys. No cloud. No subscriptions. These run locally on your machine using open-source models:

| You'd normally need Studio for... | This gives you instead | Powered by |
|---|---|---|
| 🎤 **Voice Isolation** | Separate vocals from music/noise | [Demucs v4](https://github.com/facebookresearch/demucs) by Meta |
| ✂️ **Background Removal** | Remove backgrounds from images & video | [rembg](https://github.com/danielgatis/rembg) + BiRefNet |
| 📝 **Auto Subtitles** | Transcribe audio with word-level timestamps | [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (OpenAI Whisper) |

Models download automatically on first use. Everything runs on CPU — no GPU required.

---

## 🎛️ 162 Tools Across Every Feature of Resolve

This isn't a demo with 5 tools. It covers the **entire** DaVinci Resolve experience:

| Area | What you can do |
|------|----------------|
| **Timeline** | Create, rename, duplicate, switch timelines. Add/remove clips. Insert at specific frames. Delete with ripple. |
| **Clips** | Set color, opacity, zoom, pan, tilt, rotation, crop, flip, composite mode, scaling. Enable/disable. |
| **Markers & Flags** | Add/delete colored markers with notes on timelines and individual clips. Manage flags. |
| **Media Pool** | Import files, browse folders, move/delete/relink clips, auto-sync audio, export metadata. |
| **Color Grading** | Apply LUTs, set CDL values, copy grades between clips, manage color versions and groups, reset grades. |
| **Fusion** | List, add, import, export, delete, load, rename Fusion compositions on any clip. |
| **Rendering** | Configure settings, set format/codec, manage the render queue, start/stop rendering, quick export. |
| **Titles** | Insert Text+, generators, and Fusion compositions directly onto the timeline. |
| **Audio** | Apply Fairlight presets, insert audio at playhead, voice isolation (per-track and per-clip). |
| **Gallery** | Create albums, grab stills, export/import stills, set labels. |
| **Tracks** | Add, delete, rename, lock/unlock, enable/disable video/audio/subtitle tracks. |
| **Project Management** | List, create, load, delete, archive, export, import projects. Switch databases. |
| **AI Tools** | Transcribe audio, isolate vocals, remove backgrounds — all locally, no Studio required. |

---

## 🚀 Getting Started

### What You Need

- **DaVinci Resolve 18+** (Free or Studio — both work)
- **Python 3.9+** on the same machine as Resolve
- **Cursor**, Claude Desktop, or any MCP-compatible AI assistant

### Step 1 — Install the bridge script inside Resolve

Copy `src/CursorBridge.py` to your Resolve scripts folder:

| Platform | Path |
|----------|------|
| **Windows** | `%APPDATA%\Blackmagic Design\DaVinci Resolve\Support\Fusion\Scripts\Utility\` |
| **macOS** | `~/Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Scripts/Utility/` |
| **Linux** | `~/.local/share/DaVinciResolve/Fusion/Scripts/` |

### Step 2 — Set up the MCP server

```bash
git clone https://github.com/hiteshK03/davinci-resolve-mcp.git
cd davinci-resolve-mcp
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Step 3 — Tell your AI assistant about it

Add to your `.cursor/mcp.json` (or equivalent):

```json
{
  "mcpServers": {
    "davinci-resolve": {
      "command": "python",
      "args": ["path/to/davinci-resolve-mcp/src/resolve_mcp_bridge.py"]
    }
  }
}
```

<details>
<summary><strong>Windows + WSL setup</strong> (Cursor in WSL, Resolve on Windows)</summary>

```json
{
  "mcpServers": {
    "davinci-resolve": {
      "command": "cmd.exe",
      "args": ["/c", "C:\\path\\to\\venv\\Scripts\\python.exe", "C:\\path\\to\\src\\resolve_mcp_bridge.py"]
    }
  }
}
```
</details>

### Step 4 — Start using it

1. Open DaVinci Resolve
2. Go to **Workspace → Scripts → CursorBridge**
3. Console shows: `Bridge is running (read + write)`
4. Talk to your AI assistant — it now controls Resolve

---

## 💬 Things You Can Say

```
"What's on my timeline right now?"
"Import these files into the media pool"
"Add a green marker at 5 seconds called 'intro ends'"
"Insert a Text+ title at the playhead"
"Set the first clip on track 2 to 70% opacity"
"Zoom in clip 1 to 120% and shift it left"
"Transcribe my timeline audio"
"Isolate the vocals from my timeline"
"Remove the background from clip 1 on video track 1"
"Apply this LUT to node 1 of the current clip"
"Set up an MP4 H.265 render and start it"
"Export the timeline as FCPXML"
"Grab a still from the current frame"
```

---

## 🔁 Works With the Full Pipeline

This is one piece of a three-server video production setup:

| Server | What it does |
|--------|-------------|
| **This (DaVinci Resolve MCP)** | Controls Resolve — timelines, clips, color, rendering, local AI |
| [**mcp-image-gen**](https://github.com/hiteshK03/mcp-image-gen) | Generates images locally (backgrounds, textures, overlays) — no API keys |
| **Video Editor MCP** | File-based video processing (ffmpeg, overlays, transitions) — no Resolve needed |

The AI assistant orchestrates across all three automatically. Generate an image → import into Resolve → place on timeline → adjust properties — all from a single conversation.

---

## 📋 Free vs Studio Compatibility

| Feature | Studio | Free + This Project |
|---------|--------|-------------------|
| Timeline editing, clips, markers | ✅ | ✅ |
| Color grading, LUTs, CDL | ✅ | ✅ |
| Rendering, export | ✅ | ✅ |
| Media pool, project management | ✅ | ✅ |
| Fusion compositions | ✅ | ✅ |
| Gallery & stills | ✅ | ✅ |
| Voice Isolation | ✅ Neural Engine | ✅ Demucs v4 (local) |
| Background Removal | ✅ Magic Mask | ✅ rembg/BiRefNet (local) |
| Auto Subtitles | ✅ Neural Engine | ✅ faster-whisper (local) |
| Smart Reframe | ✅ | ❌ |
| Stabilization | ✅ | ❌ |

**155/162 tools work on Free. The 5 that don't have local AI replacements. Only 2 have no alternative (Smart Reframe, Stabilization).**

---

## ⚠️ Limitations

- **Keyframe animations** — the scripting API only supports static property values, not animated keyframes
- **Fusion node parameters** — text content and effect values inside compositions need the Fusion page UI
- **Transitions** — must be added manually from the Effects Library
- **Background removal on video** — CPU-bound, can be slow for long clips
- **Gallery stills** — require being on the Color page

---

## 📄 License

MIT — use it however you want.
