#!/usr/bin/env python3
"""
DaVinci Resolve MCP Bridge Server

Connects to the CursorBridge HTTP server running inside DaVinci Resolve.
The bridge script must be started first: Workspace > Scripts > CursorBridge.

Exposes read AND write tools so Cursor can both query and manipulate Resolve.
"""

import json
import logging
import os
import shutil
import subprocess
import sys
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional


def _find_ffmpeg() -> Optional[str]:
    """Locate ffmpeg binary, checking PATH and common install locations."""
    found = shutil.which("ffmpeg")
    if found:
        return found
    candidates = [
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "AutoSubs", "ffmpeg.exe"),
        os.path.join(os.environ.get("PROGRAMFILES", ""), "ffmpeg", "bin", "ffmpeg.exe"),
        os.path.join(os.environ.get("USERPROFILE", ""), "ffmpeg", "bin", "ffmpeg.exe"),
    ]
    for c in candidates:
        if c and os.path.isfile(c):
            return c
    return None


FFMPEG_BIN = _find_ffmpeg()

log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(os.path.join(log_dir, "bridge_mcp.log"))],
)
logger = logging.getLogger("resolve-bridge-mcp")

from mcp.server.fastmcp import FastMCP

BRIDGE_URL = "http://127.0.0.1:9876"

CONN_ERROR = (
    "Cannot reach the CursorBridge inside DaVinci Resolve. "
    "Make sure DaVinci Resolve is open and you have started the bridge "
    "via Workspace > Scripts > CursorBridge."
)

mcp = FastMCP(
    "DaVinciResolveBridge",
    instructions=(
        "DaVinci Resolve MCP Bridge — provides full read AND write access to "
        "DaVinci Resolve via an internal HTTP bridge.\n"
        "Before using these tools, the user must start the CursorBridge script "
        "inside DaVinci Resolve (Workspace > Scripts > CursorBridge).\n"
        "If tools return connection errors, remind the user to start the bridge script.\n\n"
        "WRITE OPERATIONS: This bridge can modify the Resolve project — add markers, "
        "import media, insert titles, change clip properties, start renders, and more. "
        "Always confirm destructive operations with the user before executing."
    ),
)


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _get(endpoint: str, params: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    url = f"{BRIDGE_URL}{endpoint}"
    if params:
        qs = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{qs}"
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read().decode("utf-8"))
            if e.code == 404:
                body["hint"] = "The CursorBridge may be outdated. Restart DaVinci Resolve and re-run CursorBridge."
            return body
        except Exception:
            return {"error": f"Bridge returned HTTP {e.code}"}
    except urllib.error.URLError:
        return {"error": CONN_ERROR}
    except Exception as e:
        return {"error": f"Bridge request failed: {e}"}


def _post(endpoint: str, body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    url = f"{BRIDGE_URL}{endpoint}"
    data = json.dumps(body or {}).encode("utf-8")
    try:
        req = urllib.request.Request(
            url, data=data,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read().decode("utf-8"))
            if e.code in (404, 501):
                body["hint"] = "The CursorBridge may be outdated. Restart DaVinci Resolve and re-run CursorBridge."
            return body
        except Exception:
            return {"error": f"Bridge returned HTTP {e.code}"}
    except urllib.error.URLError:
        return {"error": CONN_ERROR}
    except Exception as e:
        return {"error": f"Bridge request failed: {e}"}


# ═══════════════════════════════════════════════════════════════════════════
# READ TOOLS
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool()
def get_resolve_status() -> Dict[str, Any]:
    """Check whether the CursorBridge is running and DaVinci Resolve is connected.
    Call this first to verify the bridge is active before using other tools."""
    return _get("/status")


@mcp.tool()
def get_project_info() -> Dict[str, Any]:
    """Get information about the currently open DaVinci Resolve project.
    Returns the project name, resolution, frame rate, color science, and timeline count."""
    return _get("/project")


@mcp.tool()
def get_current_page() -> Dict[str, Any]:
    """Get which page the user is currently viewing in DaVinci Resolve.
    Returns one of: media, cut, edit, fusion, color, fairlight, deliver."""
    return _get("/page")


@mcp.tool()
def get_timeline_info() -> Dict[str, Any]:
    """Get detailed information about the current timeline.
    Returns the timeline name, duration, frame rate, track counts,
    current playhead timecode, track names, and in/out mark positions."""
    return _get("/timeline")


@mcp.tool()
def get_timeline_clips(track_type: str = "video", track_index: int = 1) -> Dict[str, Any]:
    """Get the list of clips on a specific track in the current timeline.
    Args:
        track_type: 'video', 'audio', or 'subtitle'. Defaults to 'video'.
        track_index: 1-based track index. Defaults to 1.
    Returns clip names, durations, positions, file paths, colors, and enabled state."""
    return _get("/timeline/clips", {"track_type": track_type, "track_index": str(track_index)})


@mcp.tool()
def get_timeline_markers() -> Dict[str, Any]:
    """Get all markers on the current timeline.
    Returns marker positions, colors, names, notes, and durations."""
    return _get("/timeline/markers")


@mcp.tool()
def get_render_settings() -> Dict[str, Any]:
    """Get the current render configuration for the project.
    Returns render format, codec, render mode, job list, and rendering status."""
    return _get("/render")


@mcp.tool()
def get_media_pool() -> Dict[str, Any]:
    """List clips and subfolders in the current media pool folder.
    Returns clip names, colors, and media IDs."""
    return _get("/mediapool")


@mcp.tool()
def get_clip_properties(
    track_type: str = "video", track_index: int = 1, clip_index: int = 0
) -> Dict[str, Any]:
    """Get the inspector/transform properties of a timeline clip (zoom, pan, tilt, opacity, crop, etc.).
    Args:
        track_type: 'video', 'audio', or 'subtitle'.
        track_index: 1-based track index.
        clip_index: 0-based clip position on that track."""
    return _get(f"/clip/properties?track_type={track_type}&track_index={track_index}&clip_index={clip_index}")


# ═══════════════════════════════════════════════════════════════════════════
# WRITE TOOLS — Navigation
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool()
def open_page(page: str) -> Dict[str, Any]:
    """Switch DaVinci Resolve to a different page.
    Args:
        page: One of 'media', 'cut', 'edit', 'fusion', 'color', 'fairlight', 'deliver'."""
    return _post("/page", {"page": page})


@mcp.tool()
def set_playhead(timecode: str) -> Dict[str, Any]:
    """Move the playhead to a specific timecode in the current timeline.
    Args:
        timecode: Timecode string, e.g. '01:00:05:00' or '00:00:30:00'."""
    return _post("/playhead", {"timecode": timecode})


# ═══════════════════════════════════════════════════════════════════════════
# WRITE TOOLS — Timeline Markers
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool()
def add_marker(
    frameId: int,
    color: str = "Blue",
    name: str = "",
    note: str = "",
    duration: int = 1,
    customData: str = "",
) -> Dict[str, Any]:
    """Add a marker to the current timeline.
    Args:
        frameId: Frame number (relative to timeline start) where the marker is placed.
        color: Marker color — 'Blue', 'Cyan', 'Green', 'Yellow', 'Red', 'Pink',
               'Purple', 'Fuchsia', 'Rose', 'Lavender', 'Sky', 'Mint', 'Lemon',
               'Sand', 'Cocoa', 'Cream'.
        name: Marker name/title.
        note: Marker note/description.
        duration: Duration in frames (default 1).
        customData: Optional custom data string for scripting use."""
    return _post("/marker/add", {
        "frameId": frameId, "color": color, "name": name,
        "note": note, "duration": duration, "customData": customData,
    })


@mcp.tool()
def delete_markers(frameId: Optional[int] = None, color: Optional[str] = None) -> Dict[str, Any]:
    """Delete timeline markers by frame position or by color.
    Args:
        frameId: Delete the specific marker at this frame number.
        color: Delete all markers of this color. Use 'All' to delete every marker."""
    body: Dict[str, Any] = {}
    if frameId is not None:
        body["frameId"] = frameId
    if color is not None:
        body["color"] = color
    return _post("/marker/delete", body)


# ═══════════════════════════════════════════════════════════════════════════
# WRITE TOOLS — Timeline Management
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool()
def switch_timeline(index: int) -> Dict[str, Any]:
    """Switch to a different timeline in the project.
    Args:
        index: 1-based timeline index. Use get_project_info() to see timelineCount."""
    return _post("/timeline/switch", {"index": index})


@mcp.tool()
def create_timeline(name: str) -> Dict[str, Any]:
    """Create a new empty timeline in the media pool.
    Args:
        name: Name for the new timeline."""
    return _post("/timeline/create", {"name": name})


@mcp.tool()
def rename_timeline(name: str) -> Dict[str, Any]:
    """Rename the current timeline.
    Args:
        name: New name for the timeline."""
    return _post("/timeline/rename", {"name": name})


@mcp.tool()
def duplicate_timeline(name: str = "") -> Dict[str, Any]:
    """Duplicate the current timeline.
    Args:
        name: Optional name for the duplicated timeline."""
    return _post("/timeline/duplicate", {"name": name})


# ═══════════════════════════════════════════════════════════════════════════
# WRITE TOOLS — Track Management
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool()
def add_track(track_type: str, sub_track_type: str = "") -> Dict[str, Any]:
    """Add a new track to the current timeline.
    Args:
        track_type: 'video', 'audio', or 'subtitle'.
        sub_track_type: For audio tracks: 'mono', 'stereo', '5.1', '7.1', etc. Defaults to 'mono'."""
    return _post("/track/add", {"trackType": track_type, "subTrackType": sub_track_type})


@mcp.tool()
def delete_track(track_type: str, track_index: int) -> Dict[str, Any]:
    """Delete a track from the current timeline.
    Args:
        track_type: 'video', 'audio', or 'subtitle'.
        track_index: 1-based index of the track to delete."""
    return _post("/track/delete", {"trackType": track_type, "trackIndex": track_index})


@mcp.tool()
def set_track_enable(track_type: str, track_index: int, enabled: bool) -> Dict[str, Any]:
    """Enable or disable a track in the current timeline.
    Args:
        track_type: 'video', 'audio', or 'subtitle'.
        track_index: 1-based track index.
        enabled: True to enable, False to disable."""
    return _post("/track/enable", {"trackType": track_type, "trackIndex": track_index, "enabled": enabled})


@mcp.tool()
def set_track_lock(track_type: str, track_index: int, locked: bool) -> Dict[str, Any]:
    """Lock or unlock a track in the current timeline.
    Args:
        track_type: 'video', 'audio', or 'subtitle'.
        track_index: 1-based track index.
        locked: True to lock, False to unlock."""
    return _post("/track/lock", {"trackType": track_type, "trackIndex": track_index, "locked": locked})


@mcp.tool()
def set_track_name(track_type: str, track_index: int, name: str) -> Dict[str, Any]:
    """Rename a track in the current timeline.
    Args:
        track_type: 'video', 'audio', or 'subtitle'.
        track_index: 1-based track index.
        name: New name for the track."""
    return _post("/track/rename", {"trackType": track_type, "trackIndex": track_index, "name": name})


# ═══════════════════════════════════════════════════════════════════════════
# WRITE TOOLS — Media Management
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool()
def import_media(file_paths: List[str]) -> Dict[str, Any]:
    """Import media files into the current media pool folder.
    Args:
        file_paths: List of absolute file paths (Windows paths as seen by Resolve,
                    e.g. ['C:\\\\Users\\\\user\\\\Videos\\\\clip.mp4'])."""
    return _post("/media/import", {"filePaths": file_paths})


@mcp.tool()
def append_to_timeline(clip_name: str) -> Dict[str, Any]:
    """Append a media pool clip to the end of the current timeline.
    Args:
        clip_name: Name of the clip in the media pool (as returned by get_media_pool)."""
    return _post("/media/append", {"clipName": clip_name})


@mcp.tool()
def insert_to_timeline(
    clip_name: str,
    track_index: int = 1,
    record_frame: int = 0,
    start_frame: int = -1,
    end_frame: int = -1,
) -> Dict[str, Any]:
    """Insert a media pool clip at a specific track and timeline position.
    Args:
        clip_name: Name of the clip in the media pool.
        track_index: 1-based video track index to place the clip on.
        record_frame: Timeline frame position where the clip should start.
        start_frame: Source clip in-point frame (-1 = from beginning).
        end_frame: Source clip out-point frame (-1 = to end)."""
    payload: Dict[str, Any] = {
        "clipName": clip_name,
        "trackIndex": track_index,
        "recordFrame": record_frame,
    }
    if start_frame >= 0:
        payload["startFrame"] = start_frame
    if end_frame >= 0:
        payload["endFrame"] = end_frame
    return _post("/media/insert", payload)


# ═══════════════════════════════════════════════════════════════════════════
# WRITE TOOLS — Clip Operations
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool()
def set_clip_color(
    track_type: str, track_index: int, clip_index: int, color: str = ""
) -> Dict[str, Any]:
    """Set the color label of a clip on the timeline.
    Args:
        track_type: 'video', 'audio', or 'subtitle'.
        track_index: 1-based track index.
        clip_index: 0-based clip position on that track.
        color: Color name (e.g. 'Orange', 'Teal', 'Lime'). Empty string clears the color."""
    return _post("/clip/color", {
        "trackType": track_type, "trackIndex": track_index,
        "clipIndex": clip_index, "color": color,
    })


@mcp.tool()
def set_clip_enabled(
    track_type: str, track_index: int, clip_index: int, enabled: bool
) -> Dict[str, Any]:
    """Enable or disable a clip on the timeline.
    Args:
        track_type: 'video', 'audio', or 'subtitle'.
        track_index: 1-based track index.
        clip_index: 0-based clip position on that track.
        enabled: True to enable, False to disable."""
    return _post("/clip/enabled", {
        "trackType": track_type, "trackIndex": track_index,
        "clipIndex": clip_index, "enabled": enabled,
    })


@mcp.tool()
def set_clip_properties(
    track_type: str, track_index: int, clip_index: int,
    properties: Dict[str, Any] = {},
) -> Dict[str, Any]:
    """Set transform and compositing properties on a timeline clip.
    Args:
        track_type: 'video', 'audio', or 'subtitle'.
        track_index: 1-based track index.
        clip_index: 0-based clip position on that track.
        properties: Dict of property key-value pairs. Supported keys include:
            'Pan', 'Tilt' (float), 'ZoomX', 'ZoomY' (0-100),
            'RotationAngle' (-360 to 360), 'Opacity' (0-100),
            'CropLeft', 'CropRight', 'CropTop', 'CropBottom' (float),
            'FlipX', 'FlipY' (bool), 'Distortion' (-1 to 1),
            'AnchorPointX', 'AnchorPointY' (float),
            'CompositeMode' (int: 0=Normal, 4=Multiply, 5=Screen, 6=Overlay, etc.),
            'Scaling' (int: 0=Project, 1=Crop, 2=Fit, 3=Fill, 4=Stretch).
    Example: {'ZoomX': 50, 'ZoomY': 50, 'Pan': -200, 'Opacity': 80}"""
    return _post("/clip/properties", {
        "trackType": track_type, "trackIndex": track_index,
        "clipIndex": clip_index, "properties": properties,
    })


# ═══════════════════════════════════════════════════════════════════════════
# WRITE TOOLS — Titles & Generators
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool()
def insert_title(title_name: str, fusion_title: bool = False) -> Dict[str, Any]:
    """Insert a title at the playhead in the current timeline.
    Args:
        title_name: Name of the title template (e.g. 'Text+', 'Scroll', 'Lower Third').
        fusion_title: If True, inserts a Fusion title instead of a standard title."""
    return _post("/title/insert", {"titleName": title_name, "fusionTitle": fusion_title})


@mcp.tool()
def insert_generator(generator_name: str, fusion_generator: bool = False) -> Dict[str, Any]:
    """Insert a generator at the playhead in the current timeline.
    Args:
        generator_name: Name of the generator (e.g. 'Solid Color', '10 Step', 'Grey Scale').
        fusion_generator: If True, inserts a Fusion generator instead of a standard one."""
    return _post("/generator/insert", {"generatorName": generator_name, "fusionGenerator": fusion_generator})


@mcp.tool()
def insert_fusion_composition() -> Dict[str, Any]:
    """Insert an empty Fusion composition at the playhead in the current timeline.
    Opens a blank Fusion comp that can be edited in the Fusion page."""
    return _post("/fusion/insert", {})


# ═══════════════════════════════════════════════════════════════════════════
# WRITE TOOLS — Rendering
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool()
def set_render_settings(settings: Dict[str, Any]) -> Dict[str, Any]:
    """Configure render settings for the project.
    Args:
        settings: Dict of render settings. Supported keys include:
            'TargetDir' (str), 'CustomName' (str), 'SelectAllFrames' (bool),
            'MarkIn' (int), 'MarkOut' (int), 'ExportVideo' (bool),
            'ExportAudio' (bool), 'FormatWidth' (int), 'FormatHeight' (int),
            'FrameRate' (float), 'VideoQuality' (int or str like 'Best'),
            'AudioCodec' (str), 'AudioBitDepth' (int), 'AudioSampleRate' (int),
            'ExportAlpha' (bool), 'NetworkOptimization' (bool).
    Example: {'TargetDir': 'C:\\\\output', 'CustomName': 'final', 'SelectAllFrames': True}"""
    return _post("/render/settings", {"settings": settings})


@mcp.tool()
def set_render_format(format: str, codec: str) -> Dict[str, Any]:
    """Set the render output format and codec.
    Args:
        format: Render format (e.g. 'mp4', 'mov', 'mxf'). Use get_render_formats() to see options.
        codec: Codec name (e.g. 'H264', 'H265'). Use get_render_formats(format) to see codecs."""
    return _post("/render/format", {"format": format, "codec": codec})


@mcp.tool()
def get_render_formats(format: str = "") -> Dict[str, Any]:
    """List available render formats, or codecs for a specific format.
    Args:
        format: If provided, returns available codecs for this format. Otherwise lists all formats."""
    return _post("/render/formats", {"format": format})


@mcp.tool()
def add_render_job() -> Dict[str, Any]:
    """Add a render job to the queue based on current render settings.
    Returns the job ID if successful. Configure settings first with set_render_settings()."""
    return _post("/render/job/add", {})


@mcp.tool()
def start_rendering(job_ids: List[str] = []) -> Dict[str, Any]:
    """Start rendering queued jobs.
    Args:
        job_ids: Optional list of specific job IDs to render. Empty = render all queued jobs."""
    return _post("/render/start", {"jobIds": job_ids})


@mcp.tool()
def stop_rendering() -> Dict[str, Any]:
    """Stop any currently active render process."""
    return _post("/render/stop", {})


@mcp.tool()
def delete_render_job(job_id: str = "", all: bool = False) -> Dict[str, Any]:
    """Delete render job(s) from the queue.
    Args:
        job_id: ID of a specific job to delete.
        all: If True, deletes all render jobs in the queue."""
    return _post("/render/job/delete", {"jobId": job_id, "all": all})


# ═══════════════════════════════════════════════════════════════════════════
# WRITE TOOLS — Project & Settings
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool()
def save_project() -> Dict[str, Any]:
    """Save the currently open DaVinci Resolve project."""
    return _post("/project/save", {})


@mcp.tool()
def set_project_setting(key: str, value: str) -> Dict[str, Any]:
    """Set a project-level setting.
    Args:
        key: Setting name (e.g. 'timelineResolutionWidth', 'timelineFrameRate', 'superScale').
        value: Setting value as string."""
    return _post("/project/setting", {"key": key, "value": value})


@mcp.tool()
def set_timeline_setting(key: str, value: str) -> Dict[str, Any]:
    """Set a timeline-level setting on the current timeline.
    Args:
        key: Setting name (e.g. 'timelineResolutionWidth', 'timelineResolutionHeight', 'timelineFrameRate').
        value: Setting value as string."""
    return _post("/timeline/setting", {"key": key, "value": value})


@mcp.tool()
def export_current_frame(file_path: str) -> Dict[str, Any]:
    """Export the current frame (at playhead) as a still image.
    Args:
        file_path: Absolute Windows path with extension (e.g. 'C:\\\\output\\\\frame.png').
                   Supported formats: .dpx, .cin, .tif, .jpg, .png, .ppm, .bmp, .xpm."""
    return _post("/project/export-frame", {"filePath": file_path})


@mcp.tool()
def create_subtitles_from_audio() -> Dict[str, Any]:
    """[STUDIO ONLY] Auto-generate subtitles from the audio in the current timeline using DaVinci Resolve's built-in speech-to-text (Neural Engine).
    Not available in DaVinci Resolve Free. For transcription on Free, use the local AI tool transcribe_timeline instead."""
    return _post("/timeline/subtitles", {})


@mcp.tool()
def detect_scene_cuts() -> Dict[str, Any]:
    """Automatically detect and create scene cuts along the current timeline."""
    return _post("/timeline/scene-cuts", {})


# ═══════════════════════════════════════════════════════════════════════════
# MEDIA POOL — Deep Access
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool()
def get_media_pool_structure(include_clips: bool = False, max_depth: int = 10) -> Dict[str, Any]:
    """Get the full media pool folder tree structure.
    Args:
        include_clips: If True, includes clip names in each folder. False by default to keep output small.
        max_depth: Maximum folder depth to traverse (default 10).
    Returns the folder hierarchy with clip counts, and the name of the currently selected folder."""
    return _get("/mediapool/structure", {
        "include_clips": str(include_clips).lower(),
        "max_depth": str(max_depth),
    })


@mcp.tool()
def navigate_media_pool(path: str) -> Dict[str, Any]:
    """Navigate to a specific folder in the media pool.
    Args:
        path: Folder path using slash separators, e.g. 'Footage/Day1/A-Cam'.
              Use 'root' or '/' to navigate to the root folder.
    Sets the current media pool folder so subsequent operations target it."""
    return _post("/mediapool/navigate", {"path": path})


@mcp.tool()
def create_media_pool_folder(name: str, parent_path: str = "") -> Dict[str, Any]:
    """Create a new subfolder in the media pool.
    Args:
        name: Name for the new folder.
        parent_path: Path to the parent folder (e.g. 'Footage/Day1'). Empty = current folder."""
    return _post("/mediapool/folder/create", {"name": name, "parentPath": parent_path})


@mcp.tool()
def get_clip_metadata(clip_name: str) -> Dict[str, Any]:
    """Get all metadata for a media pool clip.
    Args:
        clip_name: Name of the clip in the media pool.
    Returns standard metadata (Description, Comments, Shot, Scene, Take, etc.)
    and any third-party metadata attached to the clip."""
    return _get("/mediapool/clip/metadata", {"clip_name": clip_name})


@mcp.tool()
def set_clip_metadata(clip_name: str, metadata: Dict[str, str]) -> Dict[str, Any]:
    """Set metadata on a media pool clip.
    Args:
        clip_name: Name of the clip in the media pool.
        metadata: Dict of metadata key-value pairs to set, e.g.
                  {'Description': 'Wide shot', 'Comments': 'Best take', 'Shot': 'A001'}.
    Common metadata keys: Description, Comments, Keywords, Shot, Scene, Take, Good Take, Angle."""
    return _post("/mediapool/clip/metadata", {"clipName": clip_name, "metadata": metadata})


@mcp.tool()
def get_clip_info(clip_name: str) -> Dict[str, Any]:
    """Get detailed properties for a media pool clip including flags, markers, and all clip attributes.
    Args:
        clip_name: Name of the clip in the media pool.
    Returns clip color, flags, markers, mark in/out points, and all clip properties
    (File Path, Resolution, FPS, Duration, Codec, Audio channels, etc.)."""
    return _get("/mediapool/clip/info", {"clip_name": clip_name})


@mcp.tool()
def set_pool_clip_property(clip_name: str, property_name: str, property_value: str) -> Dict[str, Any]:
    """Set a property on a media pool clip.
    Args:
        clip_name: Name of the clip in the media pool.
        property_name: Property key, e.g. 'Super Scale', 'Clip Name'.
        property_value: Value to set (as string)."""
    return _post("/mediapool/clip/property", {
        "clipName": clip_name, "propertyName": property_name, "propertyValue": property_value,
    })


@mcp.tool()
def delete_media_pool_clips(clip_names: List[str]) -> Dict[str, Any]:
    """Delete clips from the media pool.
    Args:
        clip_names: List of clip names to delete.
    Returns the count of deleted clips and any names not found."""
    return _post("/mediapool/clips/delete", {"clipNames": clip_names})


@mcp.tool()
def move_media_pool_clips(clip_names: List[str], target_folder: str) -> Dict[str, Any]:
    """Move clips to a different folder in the media pool.
    Args:
        clip_names: List of clip names to move.
        target_folder: Destination folder path, e.g. 'Footage/Selects'."""
    return _post("/mediapool/clips/move", {"clipNames": clip_names, "targetFolder": target_folder})


@mcp.tool()
def relink_media_pool_clips(clip_names: List[str], folder_path: str) -> Dict[str, Any]:
    """Relink media pool clips to a new filesystem folder.
    Args:
        clip_names: List of clip names to relink.
        folder_path: Absolute filesystem path to the new media location."""
    return _post("/mediapool/clips/relink", {"clipNames": clip_names, "folderPath": folder_path})


@mcp.tool()
def unlink_media_pool_clips(clip_names: List[str]) -> Dict[str, Any]:
    """Unlink media pool clips from their source files.
    Args:
        clip_names: List of clip names to unlink."""
    return _post("/mediapool/clips/unlink", {"clipNames": clip_names})


@mcp.tool()
def auto_sync_audio(clip_names: List[str], settings: Dict[str, Any] = {}) -> Dict[str, Any]:
    """Auto-sync audio to video clips in the media pool.
    Requires at least one video clip and one audio clip.
    Args:
        clip_names: List of at least 2 clip names (video + audio clips to sync).
        settings: Optional sync settings dict. Keys:
                  'mode' ('waveform' or 'timecode', default 'timecode'),
                  'channelNumber' (int, for waveform mode),
                  'retainEmbeddedAudio' (bool), 'retainVideoMetadata' (bool)."""
    return _post("/mediapool/audio-sync", {"clipNames": clip_names, "settings": settings})


@mcp.tool()
def import_timeline_from_file(file_path: str, import_options: Dict[str, Any] = {}) -> Dict[str, Any]:
    """Import a timeline from an AAF, EDL, XML, FCPXML, DRT, ADL, or OTIO file.
    Args:
        file_path: Absolute path to the timeline file.
        import_options: Optional dict with keys:
                        'timelineName' (str), 'importSourceClips' (bool, default True),
                        'sourceClipsPath' (str, fallback path for missing media),
                        'interlaceProcessing' (bool, AAF only)."""
    return _post("/mediapool/timeline/import", {"filePath": file_path, "importOptions": import_options})


@mcp.tool()
def export_metadata(file_name: str, clip_names: List[str] = []) -> Dict[str, Any]:
    """Export clip metadata from the media pool to a CSV file.
    Args:
        file_name: Absolute path for the output CSV file.
        clip_names: Optional list of specific clip names. Empty = export all clips."""
    return _post("/mediapool/metadata/export", {"fileName": file_name, "clipNames": clip_names})


@mcp.tool()
def import_media_from_storage(file_paths: List[str]) -> Dict[str, Any]:
    """Import media files from Resolve's Media Storage into the current media pool folder.
    Uses Media Storage paths (volumes mounted in Resolve) rather than direct filesystem paths.
    Args:
        file_paths: List of absolute file paths as seen in Resolve's Media Storage."""
    return _post("/media/import-storage", {"filePaths": file_paths})


# ═══════════════════════════════════════════════════════════════════════════
# PER-CLIP MARKERS & FLAGS
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool()
def add_clip_marker(
    track_type: str, track_index: int, clip_index: int,
    frameId: int, color: str = "Blue", name: str = "",
    note: str = "", duration: int = 1, customData: str = "",
) -> Dict[str, Any]:
    """Add a marker to a specific clip on the timeline (not a timeline marker).
    Args:
        track_type: 'video', 'audio', or 'subtitle'.
        track_index: 1-based track index.
        clip_index: 0-based clip position on the track.
        frameId: Frame position relative to clip start.
        color: Marker color (Blue, Green, Red, Yellow, etc.).
        name: Marker name/title.
        note: Marker note/description.
        duration: Duration in frames (default 1).
        customData: Optional custom data string."""
    return _post("/clip/marker/add", {
        "trackType": track_type, "trackIndex": track_index, "clipIndex": clip_index,
        "frameId": frameId, "color": color, "name": name,
        "note": note, "duration": duration, "customData": customData,
    })


@mcp.tool()
def get_clip_markers(track_type: str = "video", track_index: int = 1, clip_index: int = 0) -> Dict[str, Any]:
    """Get all markers on a specific timeline clip.
    Args:
        track_type: 'video', 'audio', or 'subtitle'.
        track_index: 1-based track index.
        clip_index: 0-based clip position on the track.
    Returns the clip name and list of markers with frame positions, colors, names, and notes."""
    return _get("/clip/markers", {
        "track_type": track_type, "track_index": str(track_index), "clip_index": str(clip_index),
    })


@mcp.tool()
def delete_clip_markers(
    track_type: str, track_index: int, clip_index: int,
    frameId: Optional[int] = None, color: Optional[str] = None, customData: Optional[str] = None,
) -> Dict[str, Any]:
    """Delete markers from a specific timeline clip.
    Args:
        track_type: 'video', 'audio', or 'subtitle'.
        track_index: 1-based track index.
        clip_index: 0-based clip position on the track.
        frameId: Delete the marker at this specific frame.
        color: Delete all markers of this color. Use 'All' to delete every marker.
        customData: Delete the first marker matching this custom data string.
    Provide one of frameId, color, or customData."""
    body: Dict[str, Any] = {"trackType": track_type, "trackIndex": track_index, "clipIndex": clip_index}
    if frameId is not None:
        body["frameId"] = frameId
    if color is not None:
        body["color"] = color
    if customData is not None:
        body["customData"] = customData
    return _post("/clip/marker/delete", body)


@mcp.tool()
def add_clip_flag(track_type: str, track_index: int, clip_index: int, color: str) -> Dict[str, Any]:
    """Add a flag to a timeline clip. Flags are colored labels visible in the timeline.
    Args:
        track_type: 'video', 'audio', or 'subtitle'.
        track_index: 1-based track index.
        clip_index: 0-based clip position on the track.
        color: Flag color (e.g. 'Blue', 'Green', 'Red', 'Yellow', 'Cyan', 'Pink', 'Purple')."""
    return _post("/clip/flag/add", {
        "trackType": track_type, "trackIndex": track_index, "clipIndex": clip_index, "color": color,
    })


@mcp.tool()
def get_clip_flags(track_type: str = "video", track_index: int = 1, clip_index: int = 0) -> Dict[str, Any]:
    """Get all flags on a specific timeline clip.
    Args:
        track_type: 'video', 'audio', or 'subtitle'.
        track_index: 1-based track index.
        clip_index: 0-based clip position on the track.
    Returns the clip name and list of flag colors."""
    return _get("/clip/flags", {
        "track_type": track_type, "track_index": str(track_index), "clip_index": str(clip_index),
    })


@mcp.tool()
def clear_clip_flags(
    track_type: str, track_index: int, clip_index: int, color: str = "All",
) -> Dict[str, Any]:
    """Clear flags from a timeline clip.
    Args:
        track_type: 'video', 'audio', or 'subtitle'.
        track_index: 1-based track index.
        clip_index: 0-based clip position on the track.
        color: Color of flags to clear, or 'All' to clear every flag."""
    return _post("/clip/flag/clear", {
        "trackType": track_type, "trackIndex": track_index, "clipIndex": clip_index, "color": color,
    })


# ═══════════════════════════════════════════════════════════════════════════
# TIMELINE CLIP MANIPULATION
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool()
def delete_timeline_clips(clips: List[Dict[str, Any]], ripple: bool = False) -> Dict[str, Any]:
    """Delete clips from the timeline.
    Args:
        clips: List of clip references, each a dict with keys:
               'trackType' ('video'/'audio'/'subtitle'), 'trackIndex' (1-based), 'clipIndex' (0-based).
               Example: [{'trackType': 'video', 'trackIndex': 1, 'clipIndex': 0}]
        ripple: If True, performs ripple delete (closes gaps). Default False."""
    return _post("/timeline/clips/delete", {"clips": clips, "ripple": ripple})


@mcp.tool()
def link_timeline_clips(clips: List[Dict[str, Any]], linked: bool = True) -> Dict[str, Any]:
    """Link or unlink timeline clips. Linked clips move together when dragged.
    Args:
        clips: List of at least 2 clip references (same format as delete_timeline_clips).
        linked: True to link, False to unlink."""
    return _post("/timeline/clips/link", {"clips": clips, "linked": linked})


@mcp.tool()
def create_compound_clip(
    clips: List[Dict[str, Any]], name: str = "", start_timecode: str = "",
) -> Dict[str, Any]:
    """Create a compound clip from selected timeline items.
    A compound clip nests multiple clips into a single item on the timeline.
    Args:
        clips: List of clip references to merge.
        name: Optional name for the compound clip.
        start_timecode: Optional start timecode (e.g. '00:00:00:00')."""
    body: Dict[str, Any] = {"clips": clips}
    if name:
        body["name"] = name
    if start_timecode:
        body["startTimecode"] = start_timecode
    return _post("/timeline/compound-clip", body)


@mcp.tool()
def create_fusion_clip(clips: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create a Fusion clip from selected timeline items.
    A Fusion clip allows complex compositing of multiple source clips in the Fusion page.
    Args:
        clips: List of clip references to merge into a Fusion clip."""
    return _post("/timeline/fusion-clip", {"clips": clips})


@mcp.tool()
def get_current_video_item() -> Dict[str, Any]:
    """Get information about the clip currently under the playhead.
    Returns the clip name, duration, start/end frames, enabled state, color,
    track position, and source file properties.
    Useful for identifying what the user is looking at before performing operations."""
    return _get("/timeline/current-item")


@mcp.tool()
def get_clip_thumbnail() -> Dict[str, Any]:
    """Get a thumbnail image of the current clip at the playhead position.
    Only works when on the Color page.
    Returns width, height, format, and base64-encoded RGB image data."""
    return _get("/timeline/thumbnail")


@mcp.tool()
def export_timeline(
    file_name: str, export_type: str, export_subtype: str = "EXPORT_NONE",
) -> Dict[str, Any]:
    """Export the current timeline to a file (AAF, EDL, FCPXML, OTIO, etc.).
    Args:
        file_name: Absolute output file path.
        export_type: One of: 'AAF', 'DRT', 'EDL', 'FCP_7_XML', 'FCPXML_1_8',
                     'FCPXML_1_9', 'FCPXML_1_10', 'HDR_10_PROFILE_A', 'HDR_10_PROFILE_B',
                     'TEXT_CSV', 'TEXT_TAB', 'DOLBY_VISION_VER_2_9', 'DOLBY_VISION_VER_4_0',
                     'DOLBY_VISION_VER_5_1', 'OTIO', 'ALE', 'ALE_CDL'.
        export_subtype: Required for AAF ('EXPORT_AAF_NEW' or 'EXPORT_AAF_EXISTING')
                        and EDL ('EXPORT_CDL', 'EXPORT_SDL', 'EXPORT_MISSING_CLIPS', or 'EXPORT_NONE').
                        For other formats, leave as default 'EXPORT_NONE'."""
    return _post("/timeline/export", {
        "fileName": file_name, "exportType": export_type, "exportSubtype": export_subtype,
    })


# ═══════════════════════════════════════════════════════════════════════════
# GALLERY & STILLS
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool()
def get_gallery_albums() -> Dict[str, Any]:
    """List all gallery still albums and PowerGrade albums.
    Returns the currently selected album name, and lists of still albums
    and PowerGrade albums with their names, indices, and still counts."""
    return _get("/gallery/albums")


@mcp.tool()
def get_album_stills(album_index: int = 0, album_type: str = "still") -> Dict[str, Any]:
    """List stills in a gallery album.
    Args:
        album_index: 1-based album index (from get_gallery_albums). 0 = current album.
        album_type: 'still' or 'powergrade'.
    Returns the album name and list of stills with their indices and labels."""
    return _get("/gallery/stills", {"album_index": str(album_index), "album_type": album_type})


@mcp.tool()
def set_current_album(album_index: int, album_type: str = "still") -> Dict[str, Any]:
    """Set the active gallery album. Stills will be grabbed into this album.
    Args:
        album_index: 1-based album index (from get_gallery_albums).
        album_type: 'still' or 'powergrade'."""
    return _post("/gallery/album/set", {"albumIndex": album_index, "albumType": album_type})


@mcp.tool()
def create_gallery_album(album_type: str = "still", name: str = "") -> Dict[str, Any]:
    """Create a new gallery album.
    Args:
        album_type: 'still' for a Still album, 'powergrade' for a PowerGrade album.
        name: Optional name for the new album."""
    body: Dict[str, Any] = {"albumType": album_type}
    if name:
        body["name"] = name
    return _post("/gallery/album/create", body)


@mcp.tool()
def grab_still() -> Dict[str, Any]:
    """Grab a still from the current clip at the playhead position.
    The still is saved into the currently active gallery album.
    Must be on the Color page for this to work."""
    return _post("/gallery/grab", {})


@mcp.tool()
def grab_all_stills(still_frame_source: int = 2) -> Dict[str, Any]:
    """Grab stills from all clips on the timeline.
    Args:
        still_frame_source: 1 = first frame of each clip, 2 = middle frame (default).
    Must be on the Color page. Returns the count of stills grabbed."""
    return _post("/gallery/grab-all", {"stillFrameSource": still_frame_source})


@mcp.tool()
def export_stills(
    folder_path: str, file_prefix: str = "still", format: str = "png",
    album_index: int = 0, album_type: str = "still", still_indices: List[int] = [],
) -> Dict[str, Any]:
    """Export stills from a gallery album to disk.
    Args:
        folder_path: Absolute path to the output directory.
        file_prefix: Filename prefix for exported stills (default 'still').
        format: Export format: 'dpx', 'cin', 'tif', 'jpg', 'png' (default), 'ppm', 'bmp', 'xpm', 'drx'.
        album_index: 1-based album index. 0 = current album.
        album_type: 'still' or 'powergrade'.
        still_indices: Optional list of 1-based still indices to export. Empty = export all."""
    return _post("/gallery/stills/export", {
        "folderPath": folder_path, "filePrefix": file_prefix, "format": format,
        "albumIndex": album_index, "albumType": album_type, "stillIndices": still_indices,
    })


@mcp.tool()
def import_stills(file_paths: List[str]) -> Dict[str, Any]:
    """Import stills (grade references) into the current gallery album.
    Args:
        file_paths: List of absolute file paths to import (DPX, TIFF, JPG, PNG, DRX, etc.)."""
    return _post("/gallery/stills/import", {"filePaths": file_paths})


@mcp.tool()
def delete_stills(
    still_indices: List[int], album_index: int = 0, album_type: str = "still",
) -> Dict[str, Any]:
    """Delete stills from a gallery album.
    Args:
        still_indices: List of 1-based still indices to delete (from get_album_stills).
        album_index: 1-based album index. 0 = current album.
        album_type: 'still' or 'powergrade'."""
    return _post("/gallery/stills/delete", {
        "stillIndices": still_indices, "albumIndex": album_index, "albumType": album_type,
    })


@mcp.tool()
def set_still_label(still_index: int, label: str) -> Dict[str, Any]:
    """Set the label on a gallery still in the current album.
    Args:
        still_index: 1-based still index (from get_album_stills).
        label: Label text to set on the still."""
    return _post("/gallery/stills/label", {"stillIndex": still_index, "label": label})


# ═══════════════════════════════════════════════════════════════════════════
# COLOR GRADING / NODE GRAPH / LUT / CDL
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool()
def get_node_graph(
    track_type: str = "video", track_index: int = 1, clip_index: int = 0,
    scope: str = "clip", layer_index: int = 1,
) -> Dict[str, Any]:
    """Get the color node graph for a clip or the timeline.
    Args:
        track_type: 'video', 'audio', or 'subtitle' (ignored if scope='timeline').
        track_index: 1-based track index.
        clip_index: 0-based clip position.
        scope: 'clip' to get a clip's node graph, 'timeline' for the timeline's graph.
        layer_index: Node stack layer (1-based, default 1).
    Returns list of nodes with index, label, LUT path, tools, and cache mode."""
    params = {"scope": scope, "track_type": track_type, "track_index": str(track_index),
              "clip_index": str(clip_index), "layer_index": str(layer_index)}
    return _get("/clip/node-graph", params)


@mcp.tool()
def set_lut(
    track_type: str, track_index: int, clip_index: int,
    node_index: int, lut_path: str, layer_index: int = 1,
) -> Dict[str, Any]:
    """Apply a LUT to a specific node in a clip's color graph.
    Args:
        track_type: 'video', 'audio', or 'subtitle'.
        track_index: 1-based track index.
        clip_index: 0-based clip position.
        node_index: 1-based node index in the graph.
        lut_path: Absolute or relative path to the LUT file (.cube, etc.).
                  Resolve must have discovered the LUT (use refresh_lut_list if needed).
        layer_index: Node stack layer (default 1)."""
    return _post("/color/set-lut", {
        "trackType": track_type, "trackIndex": track_index, "clipIndex": clip_index,
        "nodeIndex": node_index, "lutPath": lut_path, "layerIndex": layer_index,
    })


@mcp.tool()
def get_lut(
    track_type: str, track_index: int, clip_index: int,
    node_index: int, layer_index: int = 1,
) -> Dict[str, Any]:
    """Get the LUT applied to a specific node.
    Args:
        track_type: 'video', 'audio', or 'subtitle'.
        track_index: 1-based track index.
        clip_index: 0-based clip position.
        node_index: 1-based node index.
        layer_index: Node stack layer (default 1)."""
    return _post("/color/get-lut", {
        "trackType": track_type, "trackIndex": track_index, "clipIndex": clip_index,
        "nodeIndex": node_index, "layerIndex": layer_index,
    })


@mcp.tool()
def set_node_enabled(
    track_type: str, track_index: int, clip_index: int,
    node_index: int, enabled: bool, layer_index: int = 1,
) -> Dict[str, Any]:
    """Enable or disable a node in the color graph.
    Args:
        track_type: 'video', 'audio', or 'subtitle'.
        track_index: 1-based track index.
        clip_index: 0-based clip position.
        node_index: 1-based node index.
        enabled: True to enable, False to disable.
        layer_index: Node stack layer (default 1)."""
    return _post("/color/set-node-enabled", {
        "trackType": track_type, "trackIndex": track_index, "clipIndex": clip_index,
        "nodeIndex": node_index, "enabled": enabled, "layerIndex": layer_index,
    })


@mcp.tool()
def apply_grade_from_drx(
    track_type: str, track_index: int, clip_index: int,
    drx_path: str, grade_mode: int = 0, layer_index: int = 1,
) -> Dict[str, Any]:
    """Apply a color grade from a DRX still file to a clip.
    Args:
        track_type: 'video', 'audio', or 'subtitle'.
        track_index: 1-based track index.
        clip_index: 0-based clip position.
        drx_path: Absolute path to the .drx still file.
        grade_mode: 0 = No keyframes, 1 = Source Timecode aligned, 2 = Start Frames aligned.
        layer_index: Node stack layer (default 1)."""
    return _post("/color/apply-drx", {
        "trackType": track_type, "trackIndex": track_index, "clipIndex": clip_index,
        "drxPath": drx_path, "gradeMode": grade_mode, "layerIndex": layer_index,
    })


@mcp.tool()
def reset_all_grades(
    track_type: str, track_index: int, clip_index: int, layer_index: int = 1,
) -> Dict[str, Any]:
    """Reset all color grades on a clip's node graph back to default.
    Args:
        track_type: 'video', 'audio', or 'subtitle'.
        track_index: 1-based track index.
        clip_index: 0-based clip position.
        layer_index: Node stack layer (default 1)."""
    return _post("/color/reset-grades", {
        "trackType": track_type, "trackIndex": track_index, "clipIndex": clip_index,
        "layerIndex": layer_index,
    })


@mcp.tool()
def apply_arri_cdl_lut(
    track_type: str, track_index: int, clip_index: int, layer_index: int = 1,
) -> Dict[str, Any]:
    """Apply ARRI CDL and LUT to a clip.
    Args:
        track_type: 'video', 'audio', or 'subtitle'.
        track_index: 1-based track index.
        clip_index: 0-based clip position.
        layer_index: Node stack layer (default 1)."""
    return _post("/color/apply-arri-cdl", {
        "trackType": track_type, "trackIndex": track_index, "clipIndex": clip_index,
        "layerIndex": layer_index,
    })


@mcp.tool()
def set_cdl(
    track_type: str, track_index: int, clip_index: int, cdl: Dict[str, str],
) -> Dict[str, Any]:
    """Set CDL (Color Decision List) values on a clip.
    Args:
        track_type: 'video', 'audio', or 'subtitle'.
        track_index: 1-based track index.
        clip_index: 0-based clip position.
        cdl: CDL map with keys 'NodeIndex' (string, 1-based), 'Slope' (e.g. '0.5 0.4 0.2'),
             'Offset' (e.g. '0.4 0.3 0.2'), 'Power' (e.g. '0.6 0.7 0.8'), 'Saturation' (e.g. '0.65').
    Example: {'NodeIndex': '1', 'Slope': '1.0 1.0 1.0', 'Offset': '0 0 0', 'Power': '1 1 1', 'Saturation': '1.0'}"""
    return _post("/color/set-cdl", {
        "trackType": track_type, "trackIndex": track_index, "clipIndex": clip_index, "cdl": cdl,
    })


@mcp.tool()
def export_lut(
    track_type: str, track_index: int, clip_index: int,
    path: str, export_type: str = "33PTCUBE",
) -> Dict[str, Any]:
    """Export a LUT from a clip's color grading.
    Args:
        track_type: 'video', 'audio', or 'subtitle'.
        track_index: 1-based track index.
        clip_index: 0-based clip position.
        path: Output file path (include filename; extension auto-appended if wrong).
        export_type: '17PTCUBE', '33PTCUBE' (default), '65PTCUBE', or 'PANASONICVLUT'."""
    return _post("/color/export-lut", {
        "trackType": track_type, "trackIndex": track_index, "clipIndex": clip_index,
        "path": path, "exportType": export_type,
    })


@mcp.tool()
def copy_grades(source: Dict[str, Any], targets: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Copy color grades from one clip to others.
    Args:
        source: Source clip reference: {trackType, trackIndex, clipIndex}.
        targets: List of target clip references (same format)."""
    return _post("/color/copy-grades", {"source": source, "targets": targets})


@mcp.tool()
def reset_node_colors(track_type: str, track_index: int, clip_index: int) -> Dict[str, Any]:
    """Reset node colors for all nodes in a clip's active color version.
    Args:
        track_type: 'video', 'audio', or 'subtitle'.
        track_index: 1-based track index.
        clip_index: 0-based clip position."""
    return _post("/color/reset-node-colors", {
        "trackType": track_type, "trackIndex": track_index, "clipIndex": clip_index,
    })


# ═══════════════════════════════════════════════════════════════════════════
# COLOR VERSIONS
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool()
def get_color_versions(
    track_type: str = "video", track_index: int = 1, clip_index: int = 0,
) -> Dict[str, Any]:
    """Get all color versions for a clip (local and remote).
    Args:
        track_type: 'video', 'audio', or 'subtitle'.
        track_index: 1-based track index.
        clip_index: 0-based clip position.
    Returns the current version, and lists of local and remote version names."""
    return _get("/clip/color-versions", {
        "track_type": track_type, "track_index": str(track_index), "clip_index": str(clip_index),
    })


@mcp.tool()
def add_color_version(
    track_type: str, track_index: int, clip_index: int,
    version_name: str, version_type: int = 0,
) -> Dict[str, Any]:
    """Add a new color version to a clip.
    Args:
        track_type: 'video', 'audio', or 'subtitle'.
        track_index: 1-based track index.
        clip_index: 0-based clip position.
        version_name: Name for the new version.
        version_type: 0 = local (default), 1 = remote."""
    return _post("/color/version/add", {
        "trackType": track_type, "trackIndex": track_index, "clipIndex": clip_index,
        "versionName": version_name, "versionType": version_type,
    })


@mcp.tool()
def load_color_version(
    track_type: str, track_index: int, clip_index: int,
    version_name: str, version_type: int = 0,
) -> Dict[str, Any]:
    """Load/activate a named color version on a clip.
    Args:
        track_type: 'video', 'audio', or 'subtitle'.
        track_index: 1-based track index.
        clip_index: 0-based clip position.
        version_name: Name of the version to load.
        version_type: 0 = local, 1 = remote."""
    return _post("/color/version/load", {
        "trackType": track_type, "trackIndex": track_index, "clipIndex": clip_index,
        "versionName": version_name, "versionType": version_type,
    })


@mcp.tool()
def delete_color_version(
    track_type: str, track_index: int, clip_index: int,
    version_name: str, version_type: int = 0,
) -> Dict[str, Any]:
    """Delete a color version from a clip.
    Args:
        track_type: 'video', 'audio', or 'subtitle'.
        track_index: 1-based track index.
        clip_index: 0-based clip position.
        version_name: Name of the version to delete.
        version_type: 0 = local, 1 = remote."""
    return _post("/color/version/delete", {
        "trackType": track_type, "trackIndex": track_index, "clipIndex": clip_index,
        "versionName": version_name, "versionType": version_type,
    })


@mcp.tool()
def rename_color_version(
    track_type: str, track_index: int, clip_index: int,
    old_name: str, new_name: str, version_type: int = 0,
) -> Dict[str, Any]:
    """Rename a color version on a clip.
    Args:
        track_type: 'video', 'audio', or 'subtitle'.
        track_index: 1-based track index.
        clip_index: 0-based clip position.
        old_name: Current version name.
        new_name: New version name.
        version_type: 0 = local, 1 = remote."""
    return _post("/color/version/rename", {
        "trackType": track_type, "trackIndex": track_index, "clipIndex": clip_index,
        "oldName": old_name, "newName": new_name, "versionType": version_type,
    })


# ═══════════════════════════════════════════════════════════════════════════
# COLOR GROUPS
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool()
def get_color_groups() -> Dict[str, Any]:
    """List all color groups in the current project."""
    return _get("/color/groups")


@mcp.tool()
def add_color_group(group_name: str) -> Dict[str, Any]:
    """Create a new color group. Group name must be unique.
    Args:
        group_name: Name for the new color group."""
    return _post("/color/group/add", {"groupName": group_name})


@mcp.tool()
def delete_color_group(group_name: str) -> Dict[str, Any]:
    """Delete a color group. Clips in the group become ungrouped.
    Args:
        group_name: Name of the color group to delete."""
    return _post("/color/group/delete", {"groupName": group_name})


@mcp.tool()
def assign_to_color_group(
    track_type: str, track_index: int, clip_index: int, group_name: str,
) -> Dict[str, Any]:
    """Assign a timeline clip to a color group.
    Args:
        track_type: 'video', 'audio', or 'subtitle'.
        track_index: 1-based track index.
        clip_index: 0-based clip position.
        group_name: Name of the existing color group."""
    return _post("/color/group/assign", {
        "trackType": track_type, "trackIndex": track_index, "clipIndex": clip_index,
        "groupName": group_name,
    })


@mcp.tool()
def remove_from_color_group(track_type: str, track_index: int, clip_index: int) -> Dict[str, Any]:
    """Remove a clip from its color group.
    Args:
        track_type: 'video', 'audio', or 'subtitle'.
        track_index: 1-based track index.
        clip_index: 0-based clip position."""
    return _post("/color/group/remove", {
        "trackType": track_type, "trackIndex": track_index, "clipIndex": clip_index,
    })


# ═══════════════════════════════════════════════════════════════════════════
# FUSION COMPOSITION MANAGEMENT (per-clip)
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool()
def get_fusion_comps(
    track_type: str = "video", track_index: int = 1, clip_index: int = 0,
) -> Dict[str, Any]:
    """List Fusion compositions on a timeline clip.
    Args:
        track_type: 'video', 'audio', or 'subtitle'.
        track_index: 1-based track index.
        clip_index: 0-based clip position.
    Returns the count and names of Fusion compositions."""
    return _get("/clip/fusion-comps", {
        "track_type": track_type, "track_index": str(track_index), "clip_index": str(clip_index),
    })


@mcp.tool()
def add_fusion_comp_to_clip(track_type: str, track_index: int, clip_index: int) -> Dict[str, Any]:
    """Add a new blank Fusion composition to a timeline clip.
    Args:
        track_type: 'video', 'audio', or 'subtitle'.
        track_index: 1-based track index.
        clip_index: 0-based clip position."""
    return _post("/clip/fusion/add", {
        "trackType": track_type, "trackIndex": track_index, "clipIndex": clip_index,
    })


@mcp.tool()
def import_fusion_comp_to_clip(
    track_type: str, track_index: int, clip_index: int, path: str,
) -> Dict[str, Any]:
    """Import a Fusion composition from file into a timeline clip.
    Args:
        track_type: 'video', 'audio', or 'subtitle'.
        track_index: 1-based track index.
        clip_index: 0-based clip position.
        path: Absolute path to the .comp file."""
    return _post("/clip/fusion/import", {
        "trackType": track_type, "trackIndex": track_index, "clipIndex": clip_index, "path": path,
    })


@mcp.tool()
def export_fusion_comp_from_clip(
    track_type: str, track_index: int, clip_index: int,
    path: str, comp_index: int = 1,
) -> Dict[str, Any]:
    """Export a Fusion composition from a timeline clip to a file.
    Args:
        track_type: 'video', 'audio', or 'subtitle'.
        track_index: 1-based track index.
        clip_index: 0-based clip position.
        path: Output file path.
        comp_index: 1-based composition index (default 1)."""
    return _post("/clip/fusion/export", {
        "trackType": track_type, "trackIndex": track_index, "clipIndex": clip_index,
        "path": path, "compIndex": comp_index,
    })


@mcp.tool()
def delete_fusion_comp_on_clip(
    track_type: str, track_index: int, clip_index: int, comp_name: str,
) -> Dict[str, Any]:
    """Delete a named Fusion composition from a timeline clip.
    Args:
        track_type: 'video', 'audio', or 'subtitle'.
        track_index: 1-based track index.
        clip_index: 0-based clip position.
        comp_name: Name of the Fusion composition to delete."""
    return _post("/clip/fusion/delete", {
        "trackType": track_type, "trackIndex": track_index, "clipIndex": clip_index,
        "compName": comp_name,
    })


@mcp.tool()
def load_fusion_comp_on_clip(
    track_type: str, track_index: int, clip_index: int, comp_name: str,
) -> Dict[str, Any]:
    """Load a named Fusion composition as the active one on a clip.
    Args:
        track_type: 'video', 'audio', or 'subtitle'.
        track_index: 1-based track index.
        clip_index: 0-based clip position.
        comp_name: Name of the Fusion composition to load."""
    return _post("/clip/fusion/load", {
        "trackType": track_type, "trackIndex": track_index, "clipIndex": clip_index,
        "compName": comp_name,
    })


@mcp.tool()
def rename_fusion_comp_on_clip(
    track_type: str, track_index: int, clip_index: int,
    old_name: str, new_name: str,
) -> Dict[str, Any]:
    """Rename a Fusion composition on a timeline clip.
    Args:
        track_type: 'video', 'audio', or 'subtitle'.
        track_index: 1-based track index.
        clip_index: 0-based clip position.
        old_name: Current composition name.
        new_name: New composition name."""
    return _post("/clip/fusion/rename", {
        "trackType": track_type, "trackIndex": track_index, "clipIndex": clip_index,
        "oldName": old_name, "newName": new_name,
    })


# ═══════════════════════════════════════════════════════════════════════════
# SMART FEATURES (Studio)
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool()
def create_magic_mask(
    track_type: str, track_index: int, clip_index: int, mode: str = "F",
) -> Dict[str, Any]:
    """[STUDIO ONLY] Create a Magic Mask on a timeline clip using DaVinci Neural Engine.
    Not available in DaVinci Resolve Free. For background removal on Free, use the local AI tool remove_background_clip instead.
    Args:
        track_type: 'video', 'audio', or 'subtitle'.
        track_index: 1-based track index.
        clip_index: 0-based clip position.
        mode: 'F' = forward, 'B' = backward, 'BI' = bidirectional."""
    return _post("/clip/magic-mask", {
        "trackType": track_type, "trackIndex": track_index, "clipIndex": clip_index, "mode": mode,
    })


@mcp.tool()
def regenerate_magic_mask(track_type: str, track_index: int, clip_index: int) -> Dict[str, Any]:
    """[STUDIO ONLY] Regenerate an existing Magic Mask on a clip using DaVinci Neural Engine.
    Not available in DaVinci Resolve Free.
    Args:
        track_type: 'video', 'audio', or 'subtitle'.
        track_index: 1-based track index.
        clip_index: 0-based clip position."""
    return _post("/clip/magic-mask/regenerate", {
        "trackType": track_type, "trackIndex": track_index, "clipIndex": clip_index,
    })


@mcp.tool()
def stabilize_clip(track_type: str, track_index: int, clip_index: int) -> Dict[str, Any]:
    """[STUDIO ONLY] Stabilize a timeline clip using DaVinci Neural Engine enhanced stabilization.
    Not available in DaVinci Resolve Free.
    Args:
        track_type: 'video', 'audio', or 'subtitle'.
        track_index: 1-based track index.
        clip_index: 0-based clip position."""
    return _post("/clip/stabilize", {
        "trackType": track_type, "trackIndex": track_index, "clipIndex": clip_index,
    })


@mcp.tool()
def smart_reframe_clip(track_type: str, track_index: int, clip_index: int) -> Dict[str, Any]:
    """[STUDIO ONLY] Apply Smart Reframe to a clip using DaVinci Neural Engine for automatic aspect ratio adjustment.
    Not available in DaVinci Resolve Free.
    Args:
        track_type: 'video', 'audio', or 'subtitle'.
        track_index: 1-based track index.
        clip_index: 0-based clip position."""
    return _post("/clip/smart-reframe", {
        "trackType": track_type, "trackIndex": track_index, "clipIndex": clip_index,
    })


# ═══════════════════════════════════════════════════════════════════════════
# AUDIO / FAIRLIGHT
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool()
def get_fairlight_presets() -> Dict[str, Any]:
    """List available Fairlight audio presets."""
    return _get("/fairlight/presets")


@mcp.tool()
def apply_fairlight_preset(preset_name: str) -> Dict[str, Any]:
    """Apply a Fairlight preset to the current timeline.
    Args:
        preset_name: Name of the Fairlight preset (from get_fairlight_presets)."""
    return _post("/audio/fairlight-preset", {"presetName": preset_name})


@mcp.tool()
def insert_audio_at_playhead(
    media_path: str, start_offset_in_samples: int = 0, duration_in_samples: int = 0,
) -> Dict[str, Any]:
    """Insert audio at the playhead on a selected track in the Fairlight page.
    Args:
        media_path: Absolute path to the audio file.
        start_offset_in_samples: Start offset in audio samples.
        duration_in_samples: Duration in audio samples."""
    return _post("/audio/insert-at-playhead", {
        "mediaPath": media_path, "startOffsetInSamples": start_offset_in_samples,
        "durationInSamples": duration_in_samples,
    })


@mcp.tool()
def get_voice_isolation_state(
    scope: str = "clip", track_type: str = "video", track_index: int = 1, clip_index: int = 0,
) -> Dict[str, Any]:
    """[STUDIO ONLY] Get Resolve's native voice isolation state for a clip or audio track.
    Not available in DaVinci Resolve Free. For voice isolation on Free, use the local AI tool voice_isolate instead.
    Args:
        scope: 'clip' for a timeline item, 'track' for an audio track.
        track_type: 'video'/'audio'/'subtitle' (for scope='clip').
        track_index: 1-based track index.
        clip_index: 0-based clip position (for scope='clip').
    Returns {isEnabled, amount} state."""
    return _get("/audio/voice-isolation", {
        "scope": scope, "track_type": track_type,
        "track_index": str(track_index), "clip_index": str(clip_index),
    })


@mcp.tool()
def set_voice_isolation_state(
    scope: str = "clip", track_type: str = "video", track_index: int = 1, clip_index: int = 0,
    is_enabled: bool = True, amount: int = 100,
) -> Dict[str, Any]:
    """[STUDIO ONLY] Set Resolve's native voice isolation state on a clip or audio track.
    Not available in DaVinci Resolve Free. For voice isolation on Free, use the local AI tool voice_isolate instead.
    Args:
        scope: 'clip' or 'track'.
        track_type: 'video'/'audio'/'subtitle' (for scope='clip').
        track_index: 1-based track/audio track index.
        clip_index: 0-based clip position (for scope='clip').
        is_enabled: Enable/disable voice isolation.
        amount: Isolation amount 0-100."""
    body: Dict[str, Any] = {
        "scope": scope, "trackType": track_type, "trackIndex": track_index,
        "clipIndex": clip_index, "state": {"isEnabled": is_enabled, "amount": amount},
    }
    return _post("/audio/voice-isolation", body)


# ═══════════════════════════════════════════════════════════════════════════
# TAKE SELECTOR
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool()
def get_takes(
    track_type: str = "video", track_index: int = 1, clip_index: int = 0,
) -> Dict[str, Any]:
    """Get all takes for a clip (take selector).
    Args:
        track_type: 'video', 'audio', or 'subtitle'.
        track_index: 1-based track index.
        clip_index: 0-based clip position.
    Returns the count, selected take index, and list of takes with frame ranges."""
    return _get("/clip/takes", {
        "track_type": track_type, "track_index": str(track_index), "clip_index": str(clip_index),
    })


@mcp.tool()
def add_take(
    track_type: str, track_index: int, clip_index: int,
    media_pool_clip_name: str, start_frame: Optional[int] = None, end_frame: Optional[int] = None,
) -> Dict[str, Any]:
    """Add a media pool clip as a new take to a timeline clip.
    Args:
        track_type: 'video', 'audio', or 'subtitle'.
        track_index: 1-based track index.
        clip_index: 0-based clip position.
        media_pool_clip_name: Name of the media pool clip to add as a take.
        start_frame: Optional source start frame.
        end_frame: Optional source end frame."""
    body: Dict[str, Any] = {
        "trackType": track_type, "trackIndex": track_index, "clipIndex": clip_index,
        "mediaPoolClipName": media_pool_clip_name,
    }
    if start_frame is not None:
        body["startFrame"] = start_frame
    if end_frame is not None:
        body["endFrame"] = end_frame
    return _post("/clip/take/add", body)


@mcp.tool()
def select_take(track_type: str, track_index: int, clip_index: int, take_index: int) -> Dict[str, Any]:
    """Select a take by index.
    Args:
        track_type: 'video', 'audio', or 'subtitle'.
        track_index: 1-based track index.
        clip_index: 0-based clip position.
        take_index: 1-based take index."""
    return _post("/clip/take/select", {
        "trackType": track_type, "trackIndex": track_index, "clipIndex": clip_index,
        "takeIndex": take_index,
    })


@mcp.tool()
def delete_take(track_type: str, track_index: int, clip_index: int, take_index: int) -> Dict[str, Any]:
    """Delete a take by index.
    Args:
        track_type: 'video', 'audio', or 'subtitle'.
        track_index: 1-based track index.
        clip_index: 0-based clip position.
        take_index: 1-based take index to delete."""
    return _post("/clip/take/delete", {
        "trackType": track_type, "trackIndex": track_index, "clipIndex": clip_index,
        "takeIndex": take_index,
    })


@mcp.tool()
def finalize_take(track_type: str, track_index: int, clip_index: int) -> Dict[str, Any]:
    """Finalize the take selection on a clip, committing the chosen take.
    Args:
        track_type: 'video', 'audio', or 'subtitle'.
        track_index: 1-based track index.
        clip_index: 0-based clip position."""
    return _post("/clip/take/finalize", {
        "trackType": track_type, "trackIndex": track_index, "clipIndex": clip_index,
    })


# ═══════════════════════════════════════════════════════════════════════════
# PROXY / CACHE / CLIP UTILITIES
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool()
def link_proxy_media(clip_name: str, proxy_media_file_path: str) -> Dict[str, Any]:
    """Link a proxy media file to a media pool clip.
    Args:
        clip_name: Name of the clip in the media pool.
        proxy_media_file_path: Absolute path to the proxy media file."""
    return _post("/mediapool/proxy/link", {"clipName": clip_name, "proxyMediaFilePath": proxy_media_file_path})


@mcp.tool()
def unlink_proxy_media(clip_name: str) -> Dict[str, Any]:
    """Unlink proxy media from a media pool clip.
    Args:
        clip_name: Name of the clip in the media pool."""
    return _post("/mediapool/proxy/unlink", {"clipName": clip_name})


@mcp.tool()
def replace_clip(clip_name: str, file_path: str) -> Dict[str, Any]:
    """Replace a media pool clip's underlying source file.
    Args:
        clip_name: Name of the clip in the media pool.
        file_path: Absolute path to the new source media file."""
    return _post("/mediapool/clip/replace", {"clipName": clip_name, "filePath": file_path})


@mcp.tool()
def set_clip_cache(
    track_type: str, track_index: int, clip_index: int,
    cache_type: str = "color", cache_value: int = 1,
) -> Dict[str, Any]:
    """Set render cache mode for a timeline clip.
    Args:
        track_type: 'video', 'audio', or 'subtitle'.
        track_index: 1-based track index.
        clip_index: 0-based clip position.
        cache_type: 'color' or 'fusion'.
        cache_value: For color: 0=disabled, 1=enabled. For fusion: -1=auto, 0=disabled, 1=enabled."""
    return _post("/clip/cache", {
        "trackType": track_type, "trackIndex": track_index, "clipIndex": clip_index,
        "cacheType": cache_type, "cacheValue": cache_value,
    })


@mcp.tool()
def update_sidecar(track_type: str, track_index: int, clip_index: int) -> Dict[str, Any]:
    """Update sidecar file for BRAW clips or RMD file for R3D clips.
    Args:
        track_type: 'video', 'audio', or 'subtitle'.
        track_index: 1-based track index.
        clip_index: 0-based clip position."""
    return _post("/clip/sidecar", {
        "trackType": track_type, "trackIndex": track_index, "clipIndex": clip_index,
    })


@mcp.tool()
def get_linked_items(
    track_type: str = "video", track_index: int = 1, clip_index: int = 0,
) -> Dict[str, Any]:
    """Get items linked to a timeline clip (e.g. audio linked to video).
    Args:
        track_type: 'video', 'audio', or 'subtitle'.
        track_index: 1-based track index.
        clip_index: 0-based clip position.
    Returns the clip name and list of linked items with their names and track positions."""
    return _get("/clip/linked-items", {
        "track_type": track_type, "track_index": str(track_index), "clip_index": str(clip_index),
    })


@mcp.tool()
def set_timeline_mark_in_out(mark_in: int, mark_out: int, type: str = "all") -> Dict[str, Any]:
    """Set mark in/out points on the current timeline.
    Args:
        mark_in: Frame number for the in point.
        mark_out: Frame number for the out point.
        type: 'video', 'audio', or 'all' (default)."""
    return _post("/timeline/mark-in-out", {"markIn": mark_in, "markOut": mark_out, "type": type})


@mcp.tool()
def clear_timeline_mark_in_out(type: str = "all") -> Dict[str, Any]:
    """Clear mark in/out points on the current timeline.
    Args:
        type: 'video', 'audio', or 'all' (default)."""
    return _post("/timeline/clear-mark-in-out", {"type": type})


# ═══════════════════════════════════════════════════════════════════════════
# PROJECT MANAGER
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool()
def get_project_list() -> Dict[str, Any]:
    """List projects and folders in the current database folder.
    Returns the current folder name, current database info, project names, and subfolder names."""
    return _get("/projects")


@mcp.tool()
def get_database_list() -> Dict[str, Any]:
    """List all databases configured in Resolve (Disk and PostgreSQL).
    Returns the current database and list of all databases."""
    return _get("/databases")


@mcp.tool()
def load_project(project_name: str) -> Dict[str, Any]:
    """Load/open a project by name.
    Args:
        project_name: Name of the project to open."""
    return _post("/projects/load", {"projectName": project_name})


@mcp.tool()
def create_project(project_name: str) -> Dict[str, Any]:
    """Create a new project.
    Args:
        project_name: Name for the new project (must be unique)."""
    return _post("/projects/create", {"projectName": project_name})


@mcp.tool()
def delete_project(project_name: str) -> Dict[str, Any]:
    """Delete a project (cannot be the currently loaded project).
    Args:
        project_name: Name of the project to delete."""
    return _post("/projects/delete", {"projectName": project_name})


@mcp.tool()
def archive_project(
    project_name: str, file_path: str,
    archive_src_media: bool = True, archive_render_cache: bool = True,
    archive_proxy_media: bool = False,
) -> Dict[str, Any]:
    """Archive a project to a file.
    Args:
        project_name: Name of the project to archive.
        file_path: Output archive file path.
        archive_src_media: Include source media (default True).
        archive_render_cache: Include render cache (default True).
        archive_proxy_media: Include proxy media (default False)."""
    return _post("/projects/archive", {
        "projectName": project_name, "filePath": file_path,
        "archiveSrcMedia": archive_src_media, "archiveRenderCache": archive_render_cache,
        "archiveProxyMedia": archive_proxy_media,
    })


@mcp.tool()
def export_project(
    project_name: str, file_path: str, with_stills_and_luts: bool = True,
) -> Dict[str, Any]:
    """Export a project to a .drp file.
    Args:
        project_name: Name of the project to export.
        file_path: Output file path.
        with_stills_and_luts: Include stills and LUTs (default True)."""
    return _post("/projects/export", {
        "projectName": project_name, "filePath": file_path, "withStillsAndLUTs": with_stills_and_luts,
    })


@mcp.tool()
def import_project(file_path: str, project_name: str = "") -> Dict[str, Any]:
    """Import a project from a .drp file.
    Args:
        file_path: Path to the .drp file.
        project_name: Optional name for the imported project."""
    body: Dict[str, Any] = {"filePath": file_path}
    if project_name:
        body["projectName"] = project_name
    return _post("/projects/import", body)


@mcp.tool()
def navigate_project_folder(action: str, folder_name: str = "") -> Dict[str, Any]:
    """Navigate the project folder hierarchy.
    Args:
        action: 'root' (go to root), 'parent' (go up), 'open' (enter folder),
                'create' (create folder), 'delete' (delete folder).
        folder_name: Required for 'open', 'create', and 'delete' actions."""
    return _post("/projects/folder", {"action": action, "folderName": folder_name})


@mcp.tool()
def set_database(db_type: str, db_name: str, ip_address: str = "127.0.0.1") -> Dict[str, Any]:
    """Switch to a different database.
    Args:
        db_type: 'Disk' or 'PostgreSQL'.
        db_name: Database name.
        ip_address: PostgreSQL server IP (default '127.0.0.1', ignored for Disk)."""
    db_info: Dict[str, str] = {"DbType": db_type, "DbName": db_name}
    if db_type == "PostgreSQL":
        db_info["IpAddress"] = ip_address
    return _post("/projects/database", {"dbInfo": db_info})


# ═══════════════════════════════════════════════════════════════════════════
# RESOLVE-LEVEL / PRESETS / RENDER MONITORING
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool()
def layout_preset(action: str, preset_name: str = "", preset_file_path: str = "") -> Dict[str, Any]:
    """Manage UI layout presets.
    Args:
        action: 'load', 'save', 'update', 'delete', 'export', or 'import'.
        preset_name: Preset name (required for all except 'import').
        preset_file_path: File path (required for 'export' and 'import')."""
    return _post("/resolve/layout-preset", {
        "action": action, "presetName": preset_name, "presetFilePath": preset_file_path,
    })


@mcp.tool()
def render_preset(
    action: str, preset_name: str = "", preset_path: str = "",
) -> Dict[str, Any]:
    """Manage render presets.
    Args:
        action: 'load', 'saveAs', 'delete', 'list', 'import', or 'export'.
        preset_name: Preset name (for load/saveAs/delete/export).
        preset_path: File path (for import/export)."""
    return _post("/render/preset", {"action": action, "presetName": preset_name, "presetPath": preset_path})


@mcp.tool()
def burnin_preset(action: str, preset_name: str = "", preset_path: str = "") -> Dict[str, Any]:
    """Manage data burn-in presets.
    Args:
        action: 'load', 'import', or 'export'.
        preset_name: Preset name (for load/export).
        preset_path: File path (for import/export)."""
    return _post("/resolve/burnin-preset", {
        "action": action, "presetName": preset_name, "presetPath": preset_path,
    })


@mcp.tool()
def get_keyframe_mode() -> Dict[str, Any]:
    """Get the current keyframe mode (All, Color, or Sizing)."""
    return _get("/keyframe-mode")


@mcp.tool()
def set_keyframe_mode(mode: int) -> Dict[str, Any]:
    """Set the keyframe mode.
    Args:
        mode: 0 = All, 1 = Color, 2 = Sizing."""
    return _post("/resolve/keyframe-mode", {"mode": mode})


@mcp.tool()
def get_render_job_status(job_id: str) -> Dict[str, Any]:
    """Get the status and progress of a specific render job.
    Args:
        job_id: Job ID string (from add_render_job)."""
    return _post("/render/job/status", {"jobId": job_id})


@mcp.tool()
def get_render_resolutions(format: str = "", codec: str = "") -> Dict[str, Any]:
    """Get available render resolutions, optionally filtered by format and codec.
    Args:
        format: Render format (optional).
        codec: Render codec (optional)."""
    params: Dict[str, str] = {}
    if format:
        params["format"] = format
    if codec:
        params["codec"] = codec
    return _get("/render/resolutions", params)


@mcp.tool()
def get_quick_export_presets() -> Dict[str, Any]:
    """List available Quick Export render presets (YouTube, Vimeo, etc.)."""
    return _get("/render/quick-export-presets")


@mcp.tool()
def quick_export(preset_name: str, params: Dict[str, Any] = {}) -> Dict[str, Any]:
    """Quick Export the current timeline using a preset.
    Args:
        preset_name: Preset name (from get_quick_export_presets).
        params: Optional dict with 'TargetDir', 'CustomName', 'VideoQuality', 'EnableUpload' keys."""
    return _post("/render/quick-export", {"presetName": preset_name, "params": params})


@mcp.tool()
def set_render_mode(render_mode: int) -> Dict[str, Any]:
    """Set the render mode.
    Args:
        render_mode: 0 = Individual clips, 1 = Single clip."""
    return _post("/render/mode", {"renderMode": render_mode})


@mcp.tool()
def refresh_lut_list() -> Dict[str, Any]:
    """Refresh the LUT list so Resolve discovers newly added LUT files."""
    return _post("/render/refresh-luts", {})


# ═══════════════════════════════════════════════════════════════════════════
# MEDIA STORAGE
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool()
def get_media_storage(folder_path: str = "") -> Dict[str, Any]:
    """Browse Resolve's Media Storage.
    Args:
        folder_path: Absolute path to browse. Empty = just list mounted volumes.
    Returns mounted volumes, and if folder_path is given, its subfolders and files."""
    params: Dict[str, str] = {}
    if folder_path:
        params["folder_path"] = folder_path
    return _get("/media-storage", params)


@mcp.tool()
def reveal_in_storage(path: str) -> Dict[str, Any]:
    """Expand and reveal a file or folder in Resolve's Media Storage panel.
    Args:
        path: Absolute path to reveal."""
    return _post("/media-storage/reveal", {"path": path})


# ═══════════════════════════════════════════════════════════════════════════
# AI: VOICE ISOLATION (local Demucs — replaces Studio Voice Isolation)
# ═══════════════════════════════════════════════════════════════════════════

_demucs_model = None
_demucs_model_name = None


def _load_demucs(model_name: str = "htdemucs"):
    global _demucs_model, _demucs_model_name
    if _demucs_model and _demucs_model_name == model_name:
        return _demucs_model
    try:
        from demucs.pretrained import get_model
    except ImportError:
        return None
    logger.info("Loading Demucs model '%s' (first load downloads ~80MB)...", model_name)
    _demucs_model = get_model(model_name)
    _demucs_model.eval()
    _demucs_model_name = model_name
    logger.info("Demucs model '%s' loaded.", model_name)
    return _demucs_model


def _run_voice_isolation(
    file_path: str,
    model_name: str = "htdemucs",
    two_stems: str = "vocals",
    output_dir: str = "",
) -> Dict[str, Any]:
    try:
        import torch
        import numpy as np
        import soundfile as sf
        from demucs.apply import apply_model
    except ImportError as e:
        return {"error": f"Missing dependency: {e}. Run: pip install demucs soundfile"}

    if not os.path.isfile(file_path):
        return {"error": f"File not found: {file_path}"}

    model = _load_demucs(model_name)
    if model is None:
        return {"error": "demucs is not installed. Run: pip install demucs"}

    if not output_dir:
        output_dir = os.path.join(os.path.dirname(file_path), "davinci-mcp-output", "voice-isolation")
    os.makedirs(output_dir, exist_ok=True)

    logger.info("Voice isolation starting: %s (model=%s, stems=%s)", file_path, model_name, two_stems)

    try:
        wav_np, sr = sf.read(file_path, dtype="float32")
        if wav_np.ndim == 1:
            wav_np = np.stack([wav_np, wav_np], axis=-1)

        wav_tensor = torch.from_numpy(wav_np.T).float()

        target_sr = model.samplerate
        if sr != target_sr:
            import torchaudio.functional as F
            wav_tensor = F.resample(wav_tensor, sr, target_sr)

        ref = wav_tensor.mean(0)
        wav_tensor = (wav_tensor - ref.mean()) / ref.std()
        sources = apply_model(model, wav_tensor[None], device="cpu")[0]
        sources = sources * ref.std() + ref.mean()

        stem_idx = model.sources.index(two_stems) if two_stems in model.sources else 0
        stem_audio = sources[stem_idx].detach().cpu().numpy()

        other_indices = [i for i in range(len(model.sources)) if i != stem_idx]
        nostem_audio = sources[other_indices].sum(0).detach().cpu().numpy()

        basename = os.path.splitext(os.path.basename(file_path))[0]
        stem_dir = os.path.join(output_dir, basename)
        os.makedirs(stem_dir, exist_ok=True)

        stem_path = os.path.join(stem_dir, f"{two_stems}.wav")
        nostem_path = os.path.join(stem_dir, f"no_{two_stems}.wav")

        sf.write(stem_path, stem_audio.T, target_sr)
        sf.write(nostem_path, nostem_audio.T, target_sr)

        logger.info("Voice isolation complete: %s, %s", stem_path, nostem_path)
        return {
            "success": True,
            "model": model_name,
            "stems": {two_stems: stem_path, f"no_{two_stems}": nostem_path},
            "output_dir": stem_dir,
        }
    except Exception as e:
        logger.exception("Voice isolation failed")
        return {"error": f"Demucs separation failed: {e}"}


@mcp.tool()
def voice_isolate(
    file_path: str,
    model: str = "htdemucs",
    stems: str = "vocals",
    output_dir: str = "",
) -> Dict[str, Any]:
    """[FREE + STUDIO · LOCAL AI] Separate vocals from background audio using Demucs (open-source replacement for Studio Voice Isolation).
    Works on DaVinci Resolve Free — no Studio license needed. Downloads the model on first use (~150MB). Runs on CPU (~1.5x real-time).
    Args:
        file_path: Absolute path to audio/video file.
        model: Demucs model — 'htdemucs' (default, best quality), 'htdemucs_ft' (slower, slightly better),
               'mdx_extra' (good alternative). First run downloads the model.
        stems: Which stem to isolate — 'vocals' (default, outputs vocals + no_vocals),
               'drums', or 'bass'.
        output_dir: Optional output directory. Defaults to a folder next to the source file.
    Returns paths to the separated audio stems (e.g. vocals.wav, no_vocals.wav)."""
    return _run_voice_isolation(file_path, model, stems, output_dir)


@mcp.tool()
def voice_isolate_timeline(
    model: str = "htdemucs",
    stems: str = "vocals",
    output_dir: str = "",
) -> Dict[str, Any]:
    """[FREE + STUDIO · LOCAL AI] Isolate vocals from the current timeline's audio track using Demucs.
    Works on DaVinci Resolve Free — no Studio license needed. Automatically detects the audio file from audio track 1.
    Args:
        model: Demucs model — 'htdemucs' (default), 'htdemucs_ft', 'mdx_extra'.
        stems: Which stem to isolate — 'vocals' (default), 'drums', 'bass'.
        output_dir: Optional output directory.
    Returns paths to the separated audio stems."""
    clips = _get("/timeline/clips", {"track_type": "audio", "track_index": "1"})
    if "error" in clips:
        return clips
    clip_list = clips.get("clips", [])
    if not clip_list:
        return {"error": "No audio clips found on audio track 1"}
    file_path = clip_list[0].get("File Path", "")
    if not file_path:
        return {"error": "Could not determine audio file path from the timeline clip"}
    return _run_voice_isolation(file_path, model, stems, output_dir)


# ═══════════════════════════════════════════════════════════════════════════
# AI: BACKGROUND REMOVAL (local rembg — replaces Studio Magic Mask)
# ═══════════════════════════════════════════════════════════════════════════

_rembg_session = None
_rembg_model_name = None


def _load_rembg(model_name: str = "birefnet-general"):
    global _rembg_session, _rembg_model_name
    if _rembg_session and _rembg_model_name == model_name:
        return _rembg_session
    try:
        from rembg import new_session
    except ImportError:
        return None
    logger.info("Loading rembg model '%s' (first load downloads the model)...", model_name)
    _rembg_session = new_session(model_name)
    _rembg_model_name = model_name
    logger.info("rembg model '%s' loaded.", model_name)
    return _rembg_session


def _remove_bg_single(input_path: str, output_path: str, model_name: str, alpha_matte: bool) -> bool:
    session = _load_rembg(model_name)
    if session is None:
        return False
    from rembg import remove
    from PIL import Image

    img = Image.open(input_path)
    result = remove(img, session=session, alpha_matting=alpha_matte)
    result.save(output_path)
    return True


@mcp.tool()
def remove_background(
    file_path: str,
    model: str = "birefnet-general",
    output_path: str = "",
    alpha_matting: bool = False,
) -> Dict[str, Any]:
    """[FREE + STUDIO · LOCAL AI] Remove background from a single image (open-source replacement for Studio Magic Mask).
    Works on DaVinci Resolve Free — no Studio license needed. Downloads the model on first use (~170MB). Runs on CPU.
    Args:
        file_path: Absolute path to the image file.
        model: Segmentation model — 'birefnet-general' (default, best quality),
               'birefnet-general-lite' (faster), 'u2net' (classic), 'u2net_human_seg' (people only),
               'isnet-general-use', 'silueta' (smallest).
        output_path: Where to save the result. Defaults to <input>_nobg.png.
        alpha_matting: If True, applies alpha matting for smoother edges (slower).
    Returns the path to the output image with transparent background."""
    try:
        from rembg import remove
        from PIL import Image
    except ImportError:
        return {"error": "rembg is not installed. Run: pip install 'rembg[cpu]'"}

    if not os.path.isfile(file_path):
        return {"error": f"File not found: {file_path}"}

    if not output_path:
        base, _ = os.path.splitext(file_path)
        output_path = f"{base}_nobg.png"

    session = _load_rembg(model)
    if session is None:
        return {"error": "Failed to load rembg model"}

    logger.info("Removing background: %s", file_path)
    try:
        img = Image.open(file_path)
        result = remove(img, session=session, alpha_matting=alpha_matting)
        result.save(output_path)
        logger.info("Background removed: %s", output_path)
        return {"success": True, "output_path": output_path}
    except Exception as e:
        return {"error": f"Background removal failed: {e}"}


@mcp.tool()
def remove_background_video(
    file_path: str,
    model: str = "birefnet-general",
    output_dir: str = "",
    output_format: str = "png_sequence",
    alpha_matting: bool = False,
) -> Dict[str, Any]:
    """[FREE + STUDIO · LOCAL AI] Remove background from every frame of a video file (open-source replacement for Studio Magic Mask).
    Works on DaVinci Resolve Free — no Studio license needed. Extracts frames with ffmpeg, processes each with AI, reassembles the result.
    Args:
        file_path: Absolute path to the video file.
        model: Segmentation model — 'birefnet-general' (default), 'birefnet-general-lite' (faster),
               'u2net', 'u2net_human_seg'.
        output_dir: Where to save output frames. Defaults to a folder next to the source file.
        output_format: 'png_sequence' (default, PNG frames with alpha) or 'matte_video'
                       (grayscale matte as MP4, white=foreground).
        alpha_matting: If True, applies alpha matting per frame (slower, smoother edges).
    Returns the output directory path and frame count. Processing is ~0.5-2s per frame on CPU."""
    try:
        from rembg import remove
        from PIL import Image
    except ImportError:
        return {"error": "rembg is not installed. Run: pip install 'rembg[cpu]'"}

    if not os.path.isfile(file_path):
        return {"error": f"File not found: {file_path}"}

    basename = os.path.splitext(os.path.basename(file_path))[0]
    if not output_dir:
        output_dir = os.path.join(os.path.dirname(file_path), "davinci-mcp-output", "background-removal", basename)
    os.makedirs(output_dir, exist_ok=True)

    frames_dir = os.path.join(output_dir, "_frames")
    os.makedirs(frames_dir, exist_ok=True)

    ffmpeg = FFMPEG_BIN
    if not ffmpeg:
        return {"error": "ffmpeg not found. Install ffmpeg or place it in your PATH."}

    ffprobe = os.path.join(os.path.dirname(ffmpeg), "ffprobe" + (".exe" if sys.platform == "win32" else ""))
    if not os.path.isfile(ffprobe):
        ffprobe = shutil.which("ffprobe") or "ffprobe"

    logger.info("Extracting frames from: %s (ffmpeg: %s)", file_path, ffmpeg)
    try:
        subprocess.run(
            [ffmpeg, "-y", "-i", file_path, "-qscale:v", "2", os.path.join(frames_dir, "frame_%06d.png")],
            capture_output=True, text=True, check=True,
        )
    except FileNotFoundError:
        return {"error": f"ffmpeg not found at: {ffmpeg}"}
    except subprocess.CalledProcessError as e:
        return {"error": f"ffmpeg frame extraction failed: {e.stderr[:500]}"}

    frame_files = sorted(f for f in os.listdir(frames_dir) if f.endswith(".png"))
    if not frame_files:
        return {"error": "No frames extracted from video"}

    total = len(frame_files)
    logger.info("Processing %d frames with model '%s'...", total, model)

    session = _load_rembg(model)
    if session is None:
        return {"error": "Failed to load rembg model"}

    output_frames_dir = os.path.join(output_dir, "frames")
    os.makedirs(output_frames_dir, exist_ok=True)

    for i, fname in enumerate(frame_files):
        if (i + 1) % 50 == 0 or i == 0:
            logger.info("  Frame %d / %d", i + 1, total)
        try:
            img = Image.open(os.path.join(frames_dir, fname))
            result = remove(img, session=session, alpha_matting=alpha_matting)

            if output_format == "matte_video":
                alpha = result.split()[-1] if result.mode == "RGBA" else result.convert("L")
                alpha.save(os.path.join(output_frames_dir, fname))
            else:
                result.save(os.path.join(output_frames_dir, fname))
        except Exception as e:
            logger.warning("  Frame %d failed: %s", i + 1, e)

    shutil.rmtree(frames_dir, ignore_errors=True)

    response: Dict[str, Any] = {
        "success": True,
        "model": model,
        "total_frames": total,
        "output_dir": output_frames_dir,
        "output_format": output_format,
    }

    if output_format == "matte_video":
        matte_path = os.path.join(output_dir, f"{basename}_matte.mp4")
        try:
            probe = subprocess.run(
                [ffprobe, "-v", "error", "-select_streams", "v:0",
                 "-show_entries", "stream=r_frame_rate", "-of", "csv=p=0", file_path],
                capture_output=True, text=True,
            )
            fps = probe.stdout.strip() or "30"

            subprocess.run(
                [ffmpeg, "-y", "-framerate", fps,
                 "-i", os.path.join(output_frames_dir, "frame_%06d.png"),
                 "-c:v", "libx264", "-pix_fmt", "yuv420p", matte_path],
                capture_output=True, text=True, check=True,
            )
            response["matte_video"] = matte_path
        except Exception as e:
            logger.warning("Matte video assembly failed: %s", e)
            response["matte_video_error"] = str(e)

    logger.info("Background removal complete: %d frames processed", total)
    return response


@mcp.tool()
def remove_background_clip(
    track_type: str = "video",
    track_index: int = 1,
    clip_index: int = 0,
    model: str = "birefnet-general",
    output_format: str = "png_sequence",
) -> Dict[str, Any]:
    """[FREE + STUDIO · LOCAL AI] Remove background from a specific timeline clip's source video (open-source replacement for Studio Magic Mask).
    Works on DaVinci Resolve Free — no Studio license needed. Finds the clip's source file from the timeline, processes it, returns output paths.
    Args:
        track_type: 'video' or 'audio'. Defaults to 'video'.
        track_index: 1-based track index. Defaults to 1.
        clip_index: 0-based clip position on the track. Defaults to 0.
        model: Segmentation model — 'birefnet-general' (default), 'birefnet-general-lite' (faster).
        output_format: 'png_sequence' (PNG with alpha) or 'matte_video' (B/W matte MP4).
    Returns the output directory and frame count."""
    clips = _get("/timeline/clips", {"track_type": track_type, "track_index": str(track_index)})
    if "error" in clips:
        return clips
    clip_list = clips.get("clips", [])
    if not clip_list:
        return {"error": f"No clips on {track_type} track {track_index}"}
    if clip_index < 0 or clip_index >= len(clip_list):
        return {"error": f"clip_index {clip_index} out of range (0-{len(clip_list) - 1})"}
    file_path = clip_list[clip_index].get("File Path", "")
    if not file_path:
        return {"error": "Could not determine file path for this clip"}
    return remove_background_video(file_path, model=model, output_format=output_format)


# ═══════════════════════════════════════════════════════════════════════════
# TRANSCRIPTION (local Whisper via faster-whisper)
# ═══════════════════════════════════════════════════════════════════════════

_whisper_model = None
_whisper_model_size = None


def _load_whisper(model_size: str = "small"):
    global _whisper_model, _whisper_model_size
    if _whisper_model and _whisper_model_size == model_size:
        return _whisper_model
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        return None
    logger.info("Loading Whisper model '%s' (first load downloads ~483MB)...", model_size)
    _whisper_model = WhisperModel(model_size, device="cpu", compute_type="int8", cpu_threads=4)
    _whisper_model_size = model_size
    logger.info("Whisper model '%s' loaded.", model_size)
    return _whisper_model


def _run_transcription(file_path: str, model_size: str = "small", language: Optional[str] = None) -> Dict[str, Any]:
    model = _load_whisper(model_size)
    if model is None:
        return {"error": "faster-whisper is not installed. Run: pip install faster-whisper"}

    try:
        kwargs: Dict[str, Any] = {"beam_size": 5, "word_timestamps": True}
        if language:
            kwargs["language"] = language

        segments_gen, info = model.transcribe(file_path, **kwargs)

        segments = []
        full_text_parts = []
        for seg in segments_gen:
            words = []
            if seg.words:
                words = [{"word": w.word.strip(), "start": round(w.start, 2), "end": round(w.end, 2),
                          "probability": round(w.probability, 2)} for w in seg.words]
            segments.append({
                "start": round(seg.start, 2),
                "end": round(seg.end, 2),
                "text": seg.text.strip(),
                "words": words,
            })
            full_text_parts.append(seg.text.strip())

        return {
            "language": info.language,
            "language_probability": round(info.language_probability, 2),
            "duration": round(info.duration, 2),
            "full_text": " ".join(full_text_parts),
            "segments": segments,
        }
    except Exception as e:
        return {"error": f"Transcription failed: {e}"}


@mcp.tool()
def transcribe_timeline(model_size: str = "small", language: str = "") -> Dict[str, Any]:
    """[FREE + STUDIO · LOCAL AI] Transcribe the audio from the current timeline using local Whisper (open-source replacement for Studio speech-to-text).
    Works on DaVinci Resolve Free — no Studio license needed. Downloads the model on first use (~483MB for 'small'). Runs entirely on CPU.
    Args:
        model_size: Whisper model size - 'tiny', 'base', 'small', 'medium', or 'large-v3'.
                    'small' is the default (good accuracy/speed balance).
        language: Optional language code (e.g. 'en', 'es', 'fr'). Auto-detected if empty.
    Returns segments with timestamps and the full transcript text."""
    clips = _get("/timeline/clips", {"track_type": "audio", "track_index": "1"})
    if "error" in clips:
        return clips
    clip_list = clips.get("clips", [])
    if not clip_list:
        return {"error": "No audio clips found on audio track 1"}
    file_path = clip_list[0].get("File Path", "")
    if not file_path:
        return {"error": "Could not determine audio file path"}
    return _run_transcription(file_path, model_size, language or None)


@mcp.tool()
def transcribe_file(file_path: str, model_size: str = "small", language: str = "") -> Dict[str, Any]:
    """[FREE + STUDIO · LOCAL AI] Transcribe any audio or video file using local Whisper (open-source replacement for Studio speech-to-text).
    Works on DaVinci Resolve Free — no Studio license needed.
    Args:
        file_path: Absolute path to the audio/video file (Windows path).
        model_size: Whisper model size - 'tiny', 'base', 'small', 'medium', or 'large-v3'.
        language: Optional language code. Auto-detected if empty.
    Returns segments with timestamps and the full transcript text."""
    return _run_transcription(file_path, model_size, language or None)


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    logger.info("Starting DaVinci Resolve MCP Bridge Server (read + write + AI tools)")
    mcp.run()
