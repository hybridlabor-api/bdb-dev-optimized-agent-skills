#!/usr/bin/env python3
"""
CursorBridge - HTTP bridge between DaVinci Resolve and Cursor MCP.

Launch from: Workspace > Scripts > CursorBridge
Exposes a JSON API on localhost:9876 that an external MCP server can query.
Works with DaVinci Resolve Free (no external scripting required).

GET  endpoints = read-only queries
POST endpoints = write / mutation operations
"""

import json
import sys
import traceback
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

HOST = "127.0.0.1"
PORT = 9876
BRIDGE_VERSION = "2.0.0"

# ---------------------------------------------------------------------------
# Resolve bootstrap — grab the object while Fusion globals are in scope
# ---------------------------------------------------------------------------
resolve_obj = None


def _init_resolve():
    global resolve_obj
    for attempt in (
        lambda: fu.GetResolve(),        # noqa: F821
        lambda: fusion.GetResolve(),     # noqa: F821
        lambda: bmd.scriptapp("Resolve"),  # noqa: F821
    ):
        try:
            resolve_obj = attempt()
            if resolve_obj:
                return
        except Exception:
            pass
    try:
        import DaVinciResolveScript as dvr
        resolve_obj = dvr.scriptapp("Resolve")
    except Exception:
        pass


_init_resolve()

if resolve_obj:
    print("[CursorBridge] Connected to Resolve: %s %s" % (
        resolve_obj.GetProductName(), resolve_obj.GetVersionString()))
else:
    print("[CursorBridge] WARNING: Could not obtain Resolve object.")


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def safe(fn):
    try:
        return fn()
    except Exception:
        return None


def _resolve():
    r = resolve_obj
    if not r:
        return None, {"error": "Not connected to Resolve"}
    return r, None


def _project():
    r, err = _resolve()
    if err:
        return None, None, err
    pm = r.GetProjectManager()
    if not pm:
        return None, None, {"error": "No project manager"}
    proj = pm.GetCurrentProject()
    if not proj:
        return None, None, {"error": "No project open"}
    return r, proj, None


def _timeline():
    r, proj, err = _project()
    if err:
        return None, None, None, err
    tl = proj.GetCurrentTimeline()
    if not tl:
        return None, None, None, {"error": "No timeline open"}
    return r, proj, tl, None


def _clip_at(body):
    """Locate a TimelineItem by trackType / trackIndex / clipIndex."""
    _, _, tl, err = _timeline()
    if err:
        return None, err
    tt = body.get("trackType", "video")
    ti = int(body.get("trackIndex", 1))
    ci = int(body.get("clipIndex", 0))
    items = safe(lambda: tl.GetItemListInTrack(tt, ti))
    if not items:
        return None, {"error": "No clips on %s track %d" % (tt, ti)}
    if ci < 0 or ci >= len(items):
        return None, {"error": "clipIndex %d out of range (0-%d)" % (ci, len(items) - 1)}
    return items[ci], None


def _find_pool_item(pool, name):
    """Recursively search media pool for an item by name."""
    def search(folder):
        clips = folder.GetClipList() or []
        for c in clips:
            if safe(lambda: c.GetName()) == name:
                return c
        for sf in (folder.GetSubFolderList() or []):
            hit = search(sf)
            if hit:
                return hit
        return None
    root = pool.GetRootFolder()
    return search(root) if root else None


def _find_folder_by_path(pool, path):
    """Find a media pool folder by slash-separated path (e.g. 'Footage/Day1')."""
    root = pool.GetRootFolder()
    if not root:
        return None
    if not path or path.lower() in ("root", "/", ""):
        return root
    parts = [p for p in path.split("/") if p and p.lower() not in ("root", "master")]
    current = root
    for part in parts:
        subfolders = current.GetSubFolderList() or []
        found = None
        for sf in subfolders:
            if safe(lambda sf=sf: sf.GetName()) == part:
                found = sf
                break
        if not found:
            return None
        current = found
    return current


def _resolve_clip_refs(tl, clip_refs):
    """Resolve a list of {trackType, trackIndex, clipIndex} dicts to TimelineItem objects."""
    items = []
    for ref in clip_refs:
        tt = ref.get("trackType", "video")
        ti = int(ref.get("trackIndex", 1))
        ci = int(ref.get("clipIndex", 0))
        track_items = safe(lambda tt=tt, ti=ti: tl.GetItemListInTrack(tt, ti))
        if track_items and 0 <= ci < len(track_items):
            items.append(track_items[ci])
    return items


def _get_album(gallery, body):
    """Get a gallery album from body params (albumIndex + albumType), or current album."""
    album_index = int(body.get("albumIndex", 0))
    album_type = body.get("albumType", "still")
    if album_index > 0:
        if album_type == "powergrade":
            albums = safe(lambda: gallery.GetGalleryPowerGradeAlbums()) or []
        else:
            albums = safe(lambda: gallery.GetGalleryStillAlbums()) or []
        if album_index < 1 or album_index > len(albums):
            return None, {"error": "Album index %d out of range (1-%d)" % (album_index, len(albums))}
        return albums[album_index - 1], None
    album = safe(lambda: gallery.GetCurrentStillAlbum())
    if not album:
        return None, {"error": "No album selected"}
    return album, None


# ---------------------------------------------------------------------------
# GET handlers  (read-only)
# ---------------------------------------------------------------------------

def gather_status():
    r, err = _resolve()
    if err:
        return {"connected": False, "bridgeVersion": BRIDGE_VERSION, **err}
    return {
        "connected": True,
        "bridgeVersion": BRIDGE_VERSION,
        "product": safe(lambda: r.GetProductName()),
        "version": safe(lambda: r.GetVersionString()),
    }


def gather_project():
    _, proj, err = _project()
    if err:
        return err
    keys = [
        "timelineResolutionWidth", "timelineResolutionHeight",
        "timelineFrameRate", "timelinePlaybackFrameRate",
        "colorScienceMode", "audioCaptureNumChannels", "superScale",
    ]
    settings = {}
    for k in keys:
        v = safe(lambda k=k: proj.GetSetting(k))
        if v not in (None, ""):
            settings[k] = v
    return {
        "name": safe(lambda: proj.GetName()),
        "timelineCount": safe(lambda: proj.GetTimelineCount()),
        "currentRenderFormatAndCodec": safe(lambda: proj.GetCurrentRenderFormatAndCodec()),
        "settings": settings,
    }


def gather_page():
    r, err = _resolve()
    if err:
        return err
    return {"page": safe(lambda: r.GetCurrentPage())}


def gather_timeline():
    _, proj, tl, err = _timeline()
    if err:
        return err
    vt = safe(lambda: tl.GetTrackCount("video")) or 0
    at = safe(lambda: tl.GetTrackCount("audio")) or 0
    st = safe(lambda: tl.GetTrackCount("subtitle")) or 0
    names = {}
    for i in range(1, vt + 1):
        n = safe(lambda i=i: tl.GetTrackName("video", i))
        if n:
            names["video_%d" % i] = n
    for i in range(1, at + 1):
        n = safe(lambda i=i: tl.GetTrackName("audio", i))
        if n:
            names["audio_%d" % i] = n
    tl_keys = [
        "timelineResolutionWidth", "timelineResolutionHeight",
        "timelineFrameRate", "timelineOutputResolutionWidth",
        "timelineOutputResolutionHeight",
    ]
    settings = {}
    for k in tl_keys:
        v = safe(lambda k=k: tl.GetSetting(k))
        if v not in (None, ""):
            settings[k] = v
    return {
        "name": safe(lambda: tl.GetName()),
        "startFrame": safe(lambda: tl.GetStartFrame()),
        "endFrame": safe(lambda: tl.GetEndFrame()),
        "startTimecode": safe(lambda: tl.GetStartTimecode()),
        "currentTimecode": safe(lambda: tl.GetCurrentTimecode()),
        "trackCount": {"video": vt, "audio": at, "subtitle": st},
        "trackNames": names,
        "markInOut": safe(lambda: tl.GetMarkInOut()),
        "settings": settings,
    }


def gather_clips(track_type, track_index):
    _, _, tl, err = _timeline()
    if err:
        return err
    mx = safe(lambda: tl.GetTrackCount(track_type)) or 0
    if track_index < 1 or track_index > mx:
        return {"error": "Track index %d out of range (1-%d) for %s" % (track_index, mx, track_type)}
    items = safe(lambda: tl.GetItemListInTrack(track_type, track_index))
    if not items:
        return {"trackType": track_type, "trackIndex": track_index, "clips": []}
    clips = []
    for item in items:
        cd = {
            "name": safe(lambda: item.GetName()),
            "duration": safe(lambda: item.GetDuration()),
            "start": safe(lambda: item.GetStart()),
            "end": safe(lambda: item.GetEnd()),
            "enabled": safe(lambda: item.GetClipEnabled()),
            "color": safe(lambda: item.GetClipColor()),
        }
        mp = safe(lambda: item.GetMediaPoolItem())
        if mp:
            props = safe(lambda: mp.GetClipProperty()) or {}
            for key in ("File Path", "Clip Name", "Resolution", "FPS", "Frames", "Duration", "Audio Ch"):
                if key in props:
                    cd[key] = props[key]
        clips.append(cd)
    return {"trackType": track_type, "trackIndex": track_index, "clips": clips}


def gather_markers():
    _, _, tl, err = _timeline()
    if err:
        return err
    raw = safe(lambda: tl.GetMarkers()) or {}
    return {"markers": [{"frameId": fid, **info} for fid, info in raw.items()]}


def gather_render():
    _, proj, err = _project()
    if err:
        return err
    return {
        "formatAndCodec": safe(lambda: proj.GetCurrentRenderFormatAndCodec()),
        "renderMode": safe(lambda: proj.GetCurrentRenderMode()),
        "renderJobList": safe(lambda: proj.GetRenderJobList()),
        "isRendering": safe(lambda: proj.IsRenderingInProgress()),
    }


def gather_media_pool():
    """List clips in current media pool folder."""
    _, proj, err = _project()
    if err:
        return err
    pool = proj.GetMediaPool()
    if not pool:
        return {"error": "No media pool"}
    folder = pool.GetCurrentFolder()
    if not folder:
        return {"error": "No current folder"}
    clips = folder.GetClipList() or []
    result = []
    for c in clips:
        result.append({
            "name": safe(lambda: c.GetName()),
            "clipColor": safe(lambda: c.GetClipColor()),
            "mediaId": safe(lambda: c.GetMediaId()),
        })
    subfolders = [safe(lambda sf=sf: sf.GetName()) for sf in (folder.GetSubFolderList() or [])]
    return {
        "folderName": safe(lambda: folder.GetName()),
        "clips": result,
        "subfolders": subfolders,
    }


def gather_media_pool_structure(qs):
    """Get the media pool folder tree structure."""
    _, proj, err = _project()
    if err:
        return err
    pool = proj.GetMediaPool()
    if not pool:
        return {"error": "No media pool"}
    include_clips = qs.get("include_clips", ["false"])[0].lower() == "true"
    max_depth = int(qs.get("max_depth", ["10"])[0])

    def build_tree(folder, depth=0):
        if depth > max_depth:
            return {"name": safe(lambda: folder.GetName()), "truncated": True}
        clips = folder.GetClipList() or []
        subfolders = folder.GetSubFolderList() or []
        node = {
            "name": safe(lambda: folder.GetName()),
            "clipCount": len(clips),
            "subfolderCount": len(subfolders),
        }
        if include_clips:
            node["clips"] = [{"name": safe(lambda c=c: c.GetName()),
                              "mediaId": safe(lambda c=c: c.GetMediaId())} for c in clips]
        node["subfolders"] = [build_tree(sf, depth + 1) for sf in subfolders]
        return node

    root = pool.GetRootFolder()
    if not root:
        return {"error": "No root folder"}
    current = pool.GetCurrentFolder()
    return {
        "tree": build_tree(root),
        "currentFolder": safe(lambda: current.GetName()) if current else None,
    }


def gather_clip_metadata(qs):
    """Get metadata for a media pool clip by name."""
    _, proj, err = _project()
    if err:
        return err
    pool = proj.GetMediaPool()
    if not pool:
        return {"error": "No media pool"}
    clip_name = qs.get("clip_name", [""])[0]
    if not clip_name:
        return {"error": "clip_name parameter is required"}
    item = _find_pool_item(pool, clip_name)
    if not item:
        return {"error": "Clip '%s' not found in media pool" % clip_name}
    metadata = safe(lambda: item.GetMetadata()) or {}
    third_party = safe(lambda: item.GetThirdPartyMetadata()) or {}
    return {
        "name": safe(lambda: item.GetName()),
        "mediaId": safe(lambda: item.GetMediaId()),
        "metadata": metadata,
        "thirdPartyMetadata": third_party,
    }


def gather_clip_info(qs):
    """Get detailed clip properties for a media pool clip."""
    _, proj, err = _project()
    if err:
        return err
    pool = proj.GetMediaPool()
    if not pool:
        return {"error": "No media pool"}
    clip_name = qs.get("clip_name", [""])[0]
    if not clip_name:
        return {"error": "clip_name parameter is required"}
    item = _find_pool_item(pool, clip_name)
    if not item:
        return {"error": "Clip '%s' not found in media pool" % clip_name}
    props = safe(lambda: item.GetClipProperty()) or {}
    flags = safe(lambda: item.GetFlagList()) or []
    markers = safe(lambda: item.GetMarkers()) or {}
    mark_in_out = safe(lambda: item.GetMarkInOut()) or {}
    return {
        "name": safe(lambda: item.GetName()),
        "mediaId": safe(lambda: item.GetMediaId()),
        "clipColor": safe(lambda: item.GetClipColor()) or "",
        "flags": flags,
        "markers": {str(k): v for k, v in markers.items()},
        "markInOut": mark_in_out,
        "properties": props,
    }


def gather_clip_markers(qs):
    """Get markers on a specific timeline item."""
    _, _, tl, err = _timeline()
    if err:
        return err
    tt = qs.get("track_type", ["video"])[0]
    ti = int(qs.get("track_index", ["1"])[0])
    ci = int(qs.get("clip_index", ["0"])[0])
    items = safe(lambda: tl.GetItemListInTrack(tt, ti))
    if not items:
        return {"error": "No clips on %s track %d" % (tt, ti)}
    if ci < 0 or ci >= len(items):
        return {"error": "clipIndex %d out of range (0-%d)" % (ci, len(items) - 1)}
    item = items[ci]
    markers = safe(lambda: item.GetMarkers()) or {}
    return {
        "clipName": safe(lambda: item.GetName()),
        "markers": [{"frameId": fid, **info} for fid, info in markers.items()],
    }


def gather_clip_flags(qs):
    """Get flags on a specific timeline item."""
    _, _, tl, err = _timeline()
    if err:
        return err
    tt = qs.get("track_type", ["video"])[0]
    ti = int(qs.get("track_index", ["1"])[0])
    ci = int(qs.get("clip_index", ["0"])[0])
    items = safe(lambda: tl.GetItemListInTrack(tt, ti))
    if not items:
        return {"error": "No clips on %s track %d" % (tt, ti)}
    if ci < 0 or ci >= len(items):
        return {"error": "clipIndex %d out of range (0-%d)" % (ci, len(items) - 1)}
    item = items[ci]
    flags = safe(lambda: item.GetFlagList()) or []
    return {"clipName": safe(lambda: item.GetName()), "flags": flags}


def gather_current_video_item(qs):
    """Get the current video item at the playhead."""
    _, _, tl, err = _timeline()
    if err:
        return err
    item = safe(lambda: tl.GetCurrentVideoItem())
    if not item:
        return {"error": "No current video item at playhead"}
    mp = safe(lambda: item.GetMediaPoolItem())
    props = {}
    if mp:
        props = safe(lambda: mp.GetClipProperty()) or {}
    track_info = safe(lambda: item.GetTrackTypeAndIndex()) or []
    return {
        "name": safe(lambda: item.GetName()),
        "duration": safe(lambda: item.GetDuration()),
        "start": safe(lambda: item.GetStart()),
        "end": safe(lambda: item.GetEnd()),
        "enabled": safe(lambda: item.GetClipEnabled()),
        "color": safe(lambda: item.GetClipColor()),
        "trackType": track_info[0] if len(track_info) > 0 else None,
        "trackIndex": track_info[1] if len(track_info) > 1 else None,
        "properties": {k: props[k] for k in ("File Path", "Clip Name", "Resolution", "FPS", "Frames", "Duration") if k in props},
    }


def gather_clip_thumbnail(qs):
    """Get thumbnail for current clip (Color page only)."""
    _, _, tl, err = _timeline()
    if err:
        return err
    data = safe(lambda: tl.GetCurrentClipThumbnailImage())
    if not data:
        return {"error": "Failed to get thumbnail. Make sure you are on the Color page."}
    return data


def gather_gallery_albums(qs):
    """List gallery still albums and PowerGrade albums."""
    _, proj, err = _project()
    if err:
        return err
    gallery = safe(lambda: proj.GetGallery())
    if not gallery:
        return {"error": "Cannot access gallery"}
    still_albums = safe(lambda: gallery.GetGalleryStillAlbums()) or []
    pg_albums = safe(lambda: gallery.GetGalleryPowerGradeAlbums()) or []
    current = safe(lambda: gallery.GetCurrentStillAlbum())
    current_name = safe(lambda: gallery.GetAlbumName(current)) if current else None
    result = {"currentAlbum": current_name, "stillAlbums": [], "powerGradeAlbums": []}
    for i, album in enumerate(still_albums):
        name = safe(lambda a=album: gallery.GetAlbumName(a))
        stills = safe(lambda a=album: a.GetStills()) or []
        result["stillAlbums"].append({"index": i + 1, "name": name, "stillCount": len(stills)})
    for i, album in enumerate(pg_albums):
        name = safe(lambda a=album: gallery.GetAlbumName(a))
        stills = safe(lambda a=album: a.GetStills()) or []
        result["powerGradeAlbums"].append({"index": i + 1, "name": name, "stillCount": len(stills)})
    return result


def gather_album_stills(qs):
    """List stills in a gallery album."""
    _, proj, err = _project()
    if err:
        return err
    gallery = safe(lambda: proj.GetGallery())
    if not gallery:
        return {"error": "Cannot access gallery"}
    album_index = int(qs.get("album_index", ["0"])[0])
    album_type = qs.get("album_type", ["still"])[0]
    if album_index > 0:
        if album_type == "powergrade":
            albums = safe(lambda: gallery.GetGalleryPowerGradeAlbums()) or []
        else:
            albums = safe(lambda: gallery.GetGalleryStillAlbums()) or []
        if album_index < 1 or album_index > len(albums):
            return {"error": "Album index %d out of range (1-%d)" % (album_index, len(albums))}
        album = albums[album_index - 1]
    else:
        album = safe(lambda: gallery.GetCurrentStillAlbum())
    if not album:
        return {"error": "No album selected"}
    album_name = safe(lambda: gallery.GetAlbumName(album))
    stills = safe(lambda: album.GetStills()) or []
    result = []
    for i, still in enumerate(stills):
        label = safe(lambda s=still: album.GetLabel(s))
        result.append({"index": i + 1, "label": label or ""})
    return {"albumName": album_name, "stills": result}


# ---------------------------------------------------------------------------
# POST handlers  (write / mutate)
# ---------------------------------------------------------------------------

VALID_PAGES = ("media", "cut", "edit", "fusion", "color", "fairlight", "deliver")


def action_open_page(body):
    r, err = _resolve()
    if err:
        return err
    page = body.get("page", "")
    if page not in VALID_PAGES:
        return {"error": "Invalid page. Must be one of: %s" % ", ".join(VALID_PAGES)}
    return {"success": bool(r.OpenPage(page)), "page": page}


def action_set_timecode(body):
    _, _, tl, err = _timeline()
    if err:
        return err
    tc = body.get("timecode", "")
    if not tc:
        return {"error": "timecode is required (e.g. '01:00:05:00')"}
    return {"success": bool(tl.SetCurrentTimecode(tc)), "timecode": tc}


# -- Markers ---------------------------------------------------------------

def action_add_marker(body):
    _, _, tl, err = _timeline()
    if err:
        return err
    frame_id = body.get("frameId")
    if frame_id is None:
        return {"error": "frameId is required"}
    color = body.get("color", "Blue")
    name = body.get("name", "")
    note = body.get("note", "")
    duration = body.get("duration", 1)
    custom = body.get("customData", "")
    ok = tl.AddMarker(int(frame_id), color, name, note, int(duration), custom)
    return {"success": bool(ok), "frameId": frame_id, "color": color}


def action_delete_marker(body):
    _, _, tl, err = _timeline()
    if err:
        return err
    frame = body.get("frameId")
    color = body.get("color")
    if frame is not None:
        return {"success": bool(tl.DeleteMarkerAtFrame(int(frame))), "frameId": frame}
    if color:
        return {"success": bool(tl.DeleteMarkersByColor(color)), "color": color}
    return {"error": "Provide frameId or color (use 'All' to delete all)"}


# -- Timeline management ---------------------------------------------------

def action_switch_timeline(body):
    _, proj, err = _project()
    if err:
        return err
    idx = body.get("index")
    if idx is None:
        return {"error": "index is required (1-based)"}
    idx = int(idx)
    total = proj.GetTimelineCount() or 0
    if idx < 1 or idx > total:
        return {"error": "index %d out of range (1-%d)" % (idx, total)}
    tl = proj.GetTimelineByIndex(idx)
    if not tl:
        return {"error": "Could not get timeline at index %d" % idx}
    ok = proj.SetCurrentTimeline(tl)
    return {"success": bool(ok), "timeline": safe(lambda: tl.GetName())}


def action_create_timeline(body):
    _, proj, err = _project()
    if err:
        return err
    name = body.get("name", "")
    if not name:
        return {"error": "name is required"}
    pool = proj.GetMediaPool()
    if not pool:
        return {"error": "No media pool"}
    tl = pool.CreateEmptyTimeline(name)
    if not tl:
        return {"error": "Failed to create timeline '%s'" % name}
    return {"success": True, "timeline": name}


def action_rename_timeline(body):
    _, _, tl, err = _timeline()
    if err:
        return err
    name = body.get("name", "")
    if not name:
        return {"error": "name is required"}
    return {"success": bool(tl.SetName(name)), "name": name}


def action_duplicate_timeline(body):
    _, _, tl, err = _timeline()
    if err:
        return err
    name = body.get("name", "")
    new_tl = tl.DuplicateTimeline(name) if name else tl.DuplicateTimeline()
    if not new_tl:
        return {"error": "Failed to duplicate timeline"}
    return {"success": True, "timeline": safe(lambda: new_tl.GetName())}


# -- Track management ------------------------------------------------------

def action_add_track(body):
    _, _, tl, err = _timeline()
    if err:
        return err
    tt = body.get("trackType", "video")
    sub = body.get("subTrackType", "")
    if sub:
        ok = tl.AddTrack(tt, sub)
    else:
        ok = tl.AddTrack(tt)
    return {"success": bool(ok), "trackType": tt}


def action_delete_track(body):
    _, _, tl, err = _timeline()
    if err:
        return err
    tt = body.get("trackType", "video")
    ti = int(body.get("trackIndex", 0))
    if ti < 1:
        return {"error": "trackIndex must be >= 1"}
    return {"success": bool(tl.DeleteTrack(tt, ti)), "trackType": tt, "trackIndex": ti}


def action_set_track_enable(body):
    _, _, tl, err = _timeline()
    if err:
        return err
    tt = body.get("trackType", "video")
    ti = int(body.get("trackIndex", 1))
    en = bool(body.get("enabled", True))
    return {"success": bool(tl.SetTrackEnable(tt, ti, en)), "enabled": en}


def action_set_track_lock(body):
    _, _, tl, err = _timeline()
    if err:
        return err
    tt = body.get("trackType", "video")
    ti = int(body.get("trackIndex", 1))
    locked = bool(body.get("locked", True))
    return {"success": bool(tl.SetTrackLock(tt, ti, locked)), "locked": locked}


def action_set_track_name(body):
    _, _, tl, err = _timeline()
    if err:
        return err
    tt = body.get("trackType", "video")
    ti = int(body.get("trackIndex", 1))
    name = body.get("name", "")
    if not name:
        return {"error": "name is required"}
    return {"success": bool(tl.SetTrackName(tt, ti, name)), "name": name}


# -- Media management ------------------------------------------------------

def action_import_media(body):
    _, proj, err = _project()
    if err:
        return err
    paths = body.get("filePaths", [])
    if not paths:
        return {"error": "filePaths array is required"}
    pool = proj.GetMediaPool()
    if not pool:
        return {"error": "No media pool"}
    items = pool.ImportMedia(paths)
    if not items:
        return {"error": "Import failed — check file paths are valid Windows paths accessible from Resolve"}
    return {
        "success": True,
        "imported": [safe(lambda i=i: i.GetName()) for i in items],
    }


def action_import_media_from_storage(body):
    r, proj, err = _project()
    if err:
        return err
    paths = body.get("filePaths", [])
    if not paths:
        return {"error": "filePaths array is required"}
    ms = r.GetMediaStorage()
    if not ms:
        return {"error": "No media storage"}
    items = ms.AddItemListToMediaPool(paths)
    if not items:
        return {"error": "Import from storage failed"}
    return {
        "success": True,
        "imported": [safe(lambda i=i: i.GetName()) for i in items],
    }


def action_append_to_timeline(body):
    _, proj, err = _project()
    if err:
        return err
    pool = proj.GetMediaPool()
    if not pool:
        return {"error": "No media pool"}
    clip_name = body.get("clipName", "")
    if not clip_name:
        return {"error": "clipName is required"}
    item = _find_pool_item(pool, clip_name)
    if not item:
        return {"error": "Clip '%s' not found in media pool" % clip_name}
    tl_items = pool.AppendToTimeline([item])
    if not tl_items:
        return {"error": "Failed to append clip to timeline"}
    return {"success": True, "appended": clip_name}


# -- Clip operations -------------------------------------------------------

def action_set_clip_color(body):
    item, err = _clip_at(body)
    if err:
        return err
    color = body.get("color", "")
    if not color:
        ok = item.ClearClipColor()
        return {"success": bool(ok), "action": "cleared"}
    return {"success": bool(item.SetClipColor(color)), "color": color}


def action_set_clip_enabled(body):
    item, err = _clip_at(body)
    if err:
        return err
    en = bool(body.get("enabled", True))
    return {"success": bool(item.SetClipEnabled(en)), "enabled": en}


def action_set_clip_properties(body):
    item, err = _clip_at(body)
    if err:
        return err
    props = body.get("properties", {})
    if not props:
        return {"error": "properties dict is required (e.g. {\"Pan\": 0, \"Opacity\": 80})"}
    results = {}
    for k, v in props.items():
        results[k] = bool(item.SetProperty(k, v))
    return {"success": all(results.values()), "results": results}


def action_add_clip_marker(body):
    item, err = _clip_at(body)
    if err:
        return err
    fid = body.get("frameId")
    if fid is None:
        return {"error": "frameId is required"}
    ok = item.AddMarker(
        int(fid),
        body.get("color", "Blue"),
        body.get("name", ""),
        body.get("note", ""),
        int(body.get("duration", 1)),
        body.get("customData", ""),
    )
    return {"success": bool(ok)}


# -- Titles / Generators ---------------------------------------------------

def action_insert_title(body):
    _, _, tl, err = _timeline()
    if err:
        return err
    name = body.get("titleName", "")
    if not name:
        return {"error": "titleName is required (e.g. 'Text+', 'Scroll')"}
    fusion_title = body.get("fusionTitle", False)
    if fusion_title:
        item = tl.InsertFusionTitleIntoTimeline(name)
    else:
        item = tl.InsertTitleIntoTimeline(name)
    if not item:
        return {"error": "Failed to insert title '%s'" % name}
    return {"success": True, "title": name, "clipName": safe(lambda: item.GetName())}


def action_insert_generator(body):
    _, _, tl, err = _timeline()
    if err:
        return err
    name = body.get("generatorName", "")
    if not name:
        return {"error": "generatorName is required (e.g. 'Solid Color', '10 Step')"}
    fusion_gen = body.get("fusionGenerator", False)
    if fusion_gen:
        item = tl.InsertFusionGeneratorIntoTimeline(name)
    else:
        item = tl.InsertGeneratorIntoTimeline(name)
    if not item:
        return {"error": "Failed to insert generator '%s'" % name}
    return {"success": True, "generator": name, "clipName": safe(lambda: item.GetName())}


def action_insert_fusion_comp(body):
    _, _, tl, err = _timeline()
    if err:
        return err
    item = tl.InsertFusionCompositionIntoTimeline()
    if not item:
        return {"error": "Failed to insert Fusion composition"}
    return {"success": True, "clipName": safe(lambda: item.GetName())}


# -- Render -----------------------------------------------------------------

def action_set_render_settings(body):
    _, proj, err = _project()
    if err:
        return err
    settings = body.get("settings", {})
    if not settings:
        return {"error": "settings dict is required"}
    return {"success": bool(proj.SetRenderSettings(settings))}


def action_set_render_format(body):
    _, proj, err = _project()
    if err:
        return err
    fmt = body.get("format", "")
    codec = body.get("codec", "")
    if not fmt or not codec:
        return {"error": "format and codec are required"}
    return {"success": bool(proj.SetCurrentRenderFormatAndCodec(fmt, codec))}


def action_add_render_job(body):
    _, proj, err = _project()
    if err:
        return err
    job_id = proj.AddRenderJob()
    if not job_id:
        return {"error": "Failed to add render job — check render settings are complete"}
    return {"success": True, "jobId": job_id}


def action_start_rendering(body):
    _, proj, err = _project()
    if err:
        return err
    job_ids = body.get("jobIds", [])
    if job_ids:
        ok = proj.StartRendering(job_ids)
    else:
        ok = proj.StartRendering()
    return {"success": bool(ok)}


def action_stop_rendering(body):
    _, proj, err = _project()
    if err:
        return err
    proj.StopRendering()
    return {"success": True}


def action_delete_render_job(body):
    _, proj, err = _project()
    if err:
        return err
    job_id = body.get("jobId", "")
    if job_id:
        return {"success": bool(proj.DeleteRenderJob(job_id))}
    if body.get("all", False):
        return {"success": bool(proj.DeleteAllRenderJobs())}
    return {"error": "Provide jobId or set all=true"}


def action_get_render_formats(body):
    _, proj, err = _project()
    if err:
        return err
    formats = safe(lambda: proj.GetRenderFormats()) or {}
    fmt = body.get("format", "")
    if fmt:
        codecs = safe(lambda: proj.GetRenderCodecs(fmt)) or {}
        return {"format": fmt, "codecs": codecs}
    return {"formats": formats}


# -- Project ----------------------------------------------------------------

def action_save_project(body):
    _, proj, err = _project()
    if err:
        return err
    return {"success": bool(proj.GetName() and resolve_obj.GetProjectManager().SaveProject())}


def action_set_project_setting(body):
    _, proj, err = _project()
    if err:
        return err
    key = body.get("key", "")
    value = body.get("value", "")
    if not key:
        return {"error": "key is required"}
    return {"success": bool(proj.SetSetting(key, str(value))), "key": key, "value": value}


def action_set_timeline_setting(body):
    _, _, tl, err = _timeline()
    if err:
        return err
    key = body.get("key", "")
    value = body.get("value", "")
    if not key:
        return {"error": "key is required"}
    return {"success": bool(tl.SetSetting(key, str(value))), "key": key, "value": value}


def action_export_frame(body):
    _, proj, err = _project()
    if err:
        return err
    path = body.get("filePath", "")
    if not path:
        return {"error": "filePath is required (e.g. 'C:\\\\output\\\\frame.png')"}
    return {"success": bool(proj.ExportCurrentFrameAsStill(path)), "filePath": path}


def action_create_subtitles(body):
    _, _, tl, err = _timeline()
    if err:
        return err
    ok = tl.CreateSubtitlesFromAudio(body.get("settings", {}))
    return {"success": bool(ok)}


def action_detect_scene_cuts(body):
    _, _, tl, err = _timeline()
    if err:
        return err
    return {"success": bool(tl.DetectSceneCuts())}


# -- Media Pool Deep Access -------------------------------------------------

def action_navigate_media_pool(body):
    _, proj, err = _project()
    if err:
        return err
    pool = proj.GetMediaPool()
    if not pool:
        return {"error": "No media pool"}
    path = body.get("path", "")
    if not path or path.lower() in ("root", "/"):
        folder = pool.GetRootFolder()
    else:
        folder = _find_folder_by_path(pool, path)
    if not folder:
        return {"error": "Folder not found: '%s'" % path}
    ok = pool.SetCurrentFolder(folder)
    return {"success": bool(ok), "folder": safe(lambda: folder.GetName())}


def action_create_media_pool_folder(body):
    _, proj, err = _project()
    if err:
        return err
    pool = proj.GetMediaPool()
    if not pool:
        return {"error": "No media pool"}
    name = body.get("name", "")
    if not name:
        return {"error": "name is required"}
    parent_path = body.get("parentPath", "")
    if parent_path:
        parent = _find_folder_by_path(pool, parent_path)
        if not parent:
            return {"error": "Parent folder not found: '%s'" % parent_path}
    else:
        parent = pool.GetCurrentFolder()
    if not parent:
        return {"error": "No parent folder"}
    new_folder = pool.AddSubFolder(parent, name)
    if not new_folder:
        return {"error": "Failed to create folder '%s'" % name}
    return {"success": True, "folder": name}


def action_set_clip_metadata(body):
    _, proj, err = _project()
    if err:
        return err
    pool = proj.GetMediaPool()
    if not pool:
        return {"error": "No media pool"}
    clip_name = body.get("clipName", "")
    if not clip_name:
        return {"error": "clipName is required"}
    item = _find_pool_item(pool, clip_name)
    if not item:
        return {"error": "Clip '%s' not found in media pool" % clip_name}
    metadata = body.get("metadata", {})
    if not metadata:
        return {"error": "metadata dict is required"}
    ok = item.SetMetadata(metadata)
    return {"success": bool(ok)}


def action_set_pool_clip_property(body):
    _, proj, err = _project()
    if err:
        return err
    pool = proj.GetMediaPool()
    if not pool:
        return {"error": "No media pool"}
    clip_name = body.get("clipName", "")
    if not clip_name:
        return {"error": "clipName is required"}
    item = _find_pool_item(pool, clip_name)
    if not item:
        return {"error": "Clip '%s' not found in media pool" % clip_name}
    prop_name = body.get("propertyName", "")
    prop_value = body.get("propertyValue", "")
    if not prop_name:
        return {"error": "propertyName is required"}
    ok = item.SetClipProperty(prop_name, prop_value)
    return {"success": bool(ok), "property": prop_name}


def action_delete_media_pool_clips(body):
    _, proj, err = _project()
    if err:
        return err
    pool = proj.GetMediaPool()
    if not pool:
        return {"error": "No media pool"}
    clip_names = body.get("clipNames", [])
    if not clip_names:
        return {"error": "clipNames array is required"}
    items, not_found = [], []
    for name in clip_names:
        item = _find_pool_item(pool, name)
        if item:
            items.append(item)
        else:
            not_found.append(name)
    if not items:
        return {"error": "No matching clips found", "notFound": not_found}
    ok = pool.DeleteClips(items)
    return {"success": bool(ok), "deleted": len(items), "notFound": not_found}


def action_move_media_pool_clips(body):
    _, proj, err = _project()
    if err:
        return err
    pool = proj.GetMediaPool()
    if not pool:
        return {"error": "No media pool"}
    clip_names = body.get("clipNames", [])
    target_path = body.get("targetFolder", "")
    if not clip_names:
        return {"error": "clipNames array is required"}
    if not target_path:
        return {"error": "targetFolder path is required"}
    target = _find_folder_by_path(pool, target_path)
    if not target:
        return {"error": "Target folder not found: '%s'" % target_path}
    items = [i for name in clip_names for i in [_find_pool_item(pool, name)] if i]
    if not items:
        return {"error": "No matching clips found"}
    ok = pool.MoveClips(items, target)
    return {"success": bool(ok), "moved": len(items)}


def action_relink_media_pool_clips(body):
    _, proj, err = _project()
    if err:
        return err
    pool = proj.GetMediaPool()
    if not pool:
        return {"error": "No media pool"}
    clip_names = body.get("clipNames", [])
    folder_path = body.get("folderPath", "")
    if not clip_names:
        return {"error": "clipNames array is required"}
    if not folder_path:
        return {"error": "folderPath is required (filesystem path)"}
    items = [i for name in clip_names for i in [_find_pool_item(pool, name)] if i]
    if not items:
        return {"error": "No matching clips found"}
    ok = pool.RelinkClips(items, folder_path)
    return {"success": bool(ok), "relinked": len(items)}


def action_unlink_media_pool_clips(body):
    _, proj, err = _project()
    if err:
        return err
    pool = proj.GetMediaPool()
    if not pool:
        return {"error": "No media pool"}
    clip_names = body.get("clipNames", [])
    if not clip_names:
        return {"error": "clipNames array is required"}
    items = [i for name in clip_names for i in [_find_pool_item(pool, name)] if i]
    if not items:
        return {"error": "No matching clips found"}
    ok = pool.UnlinkClips(items)
    return {"success": bool(ok), "unlinked": len(items)}


def action_auto_sync_audio(body):
    _, proj, err = _project()
    if err:
        return err
    pool = proj.GetMediaPool()
    if not pool:
        return {"error": "No media pool"}
    clip_names = body.get("clipNames", [])
    if len(clip_names) < 2:
        return {"error": "At least 2 clipNames required (video + audio)"}
    items = [i for name in clip_names for i in [_find_pool_item(pool, name)] if i]
    if len(items) < 2:
        return {"error": "Need at least 2 matching clips"}
    settings = body.get("settings", {})
    ok = pool.AutoSyncAudio(items, settings)
    return {"success": bool(ok)}


def action_import_timeline_from_file(body):
    _, proj, err = _project()
    if err:
        return err
    pool = proj.GetMediaPool()
    if not pool:
        return {"error": "No media pool"}
    file_path = body.get("filePath", "")
    if not file_path:
        return {"error": "filePath is required"}
    options = body.get("importOptions", {})
    tl = pool.ImportTimelineFromFile(file_path, options) if options else pool.ImportTimelineFromFile(file_path)
    if not tl:
        return {"error": "Failed to import timeline from '%s'" % file_path}
    return {"success": True, "timeline": safe(lambda: tl.GetName())}


def action_export_metadata(body):
    _, proj, err = _project()
    if err:
        return err
    pool = proj.GetMediaPool()
    if not pool:
        return {"error": "No media pool"}
    file_name = body.get("fileName", "")
    if not file_name:
        return {"error": "fileName is required (CSV path)"}
    clip_names = body.get("clipNames", [])
    items = [i for name in clip_names for i in [_find_pool_item(pool, name)] if i] if clip_names else []
    ok = pool.ExportMetadata(file_name, items) if items else pool.ExportMetadata(file_name)
    return {"success": bool(ok), "fileName": file_name}


def action_insert_to_timeline(body):
    """Insert a media pool clip at a specific track and record frame position."""
    _, proj, err = _project()
    if err:
        return err
    pool = proj.GetMediaPool()
    if not pool:
        return {"error": "No media pool"}
    clip_name = body.get("clipName", "")
    if not clip_name:
        return {"error": "clipName is required"}
    item = _find_pool_item(pool, clip_name)
    if not item:
        return {"error": "Clip '%s' not found in media pool" % clip_name}
    clip_info = {"mediaPoolItem": item}
    for key, body_key in [("trackIndex", "trackIndex"), ("recordFrame", "recordFrame"),
                          ("startFrame", "startFrame"), ("endFrame", "endFrame"),
                          ("mediaType", "mediaType")]:
        val = body.get(body_key)
        if val is not None:
            clip_info[key] = int(val)
    tl_items = pool.AppendToTimeline([clip_info])
    if not tl_items:
        return {"error": "Failed to insert clip to timeline"}
    return {"success": True, "inserted": clip_name, "count": len(tl_items)}


# -- Per-Clip Markers & Flags ----------------------------------------------

def action_delete_clip_marker(body):
    item, err = _clip_at(body)
    if err:
        return err
    frame = body.get("frameId")
    color = body.get("color")
    custom_data = body.get("customData")
    if frame is not None:
        return {"success": bool(item.DeleteMarkerAtFrame(int(frame)))}
    if color:
        return {"success": bool(item.DeleteMarkersByColor(color))}
    if custom_data:
        return {"success": bool(item.DeleteMarkerByCustomData(custom_data))}
    return {"error": "Provide frameId, color (use 'All' for all), or customData"}


def action_add_clip_flag(body):
    item, err = _clip_at(body)
    if err:
        return err
    color = body.get("color", "")
    if not color:
        return {"error": "color is required"}
    return {"success": bool(item.AddFlag(color)), "color": color}


def action_clear_clip_flags(body):
    item, err = _clip_at(body)
    if err:
        return err
    color = body.get("color", "All")
    return {"success": bool(item.ClearFlags(color)), "color": color}


# -- Timeline Clip Manipulation ---------------------------------------------

def action_delete_timeline_clips(body):
    _, _, tl, err = _timeline()
    if err:
        return err
    clip_refs = body.get("clips", [])
    ripple = body.get("ripple", False)
    if not clip_refs:
        return {"error": "clips array is required (each: {trackType, trackIndex, clipIndex})"}
    items = _resolve_clip_refs(tl, clip_refs)
    if not items:
        return {"error": "No matching clips found"}
    ok = tl.DeleteClips(items, ripple)
    return {"success": bool(ok), "deleted": len(items), "ripple": ripple}


def action_link_timeline_clips(body):
    _, _, tl, err = _timeline()
    if err:
        return err
    clip_refs = body.get("clips", [])
    linked = body.get("linked", True)
    if len(clip_refs) < 2:
        return {"error": "At least 2 clip references required"}
    items = _resolve_clip_refs(tl, clip_refs)
    if len(items) < 2:
        return {"error": "Need at least 2 matching clips"}
    ok = tl.SetClipsLinked(items, linked)
    return {"success": bool(ok), "linked": linked, "count": len(items)}


def action_create_compound_clip(body):
    _, _, tl, err = _timeline()
    if err:
        return err
    clip_refs = body.get("clips", [])
    if not clip_refs:
        return {"error": "clips array is required"}
    items = _resolve_clip_refs(tl, clip_refs)
    if not items:
        return {"error": "No matching clips found"}
    clip_info = {}
    if body.get("name"):
        clip_info["name"] = body["name"]
    if body.get("startTimecode"):
        clip_info["startTimecode"] = body["startTimecode"]
    result = tl.CreateCompoundClip(items, clip_info) if clip_info else tl.CreateCompoundClip(items)
    if not result:
        return {"error": "Failed to create compound clip"}
    return {"success": True, "name": safe(lambda: result.GetName())}


def action_create_fusion_clip(body):
    _, _, tl, err = _timeline()
    if err:
        return err
    clip_refs = body.get("clips", [])
    if not clip_refs:
        return {"error": "clips array is required"}
    items = _resolve_clip_refs(tl, clip_refs)
    if not items:
        return {"error": "No matching clips found"}
    result = tl.CreateFusionClip(items)
    if not result:
        return {"error": "Failed to create Fusion clip"}
    return {"success": True, "name": safe(lambda: result.GetName())}


def action_export_timeline(body):
    """Export timeline to AAF/EDL/FCPXML/OTIO etc."""
    r, _, tl, err = _timeline()
    if err:
        return err
    file_name = body.get("fileName", "")
    export_type = body.get("exportType", "")
    export_subtype = body.get("exportSubtype", "EXPORT_NONE")
    if not file_name:
        return {"error": "fileName is required"}
    if not export_type:
        return {"error": "exportType is required"}
    type_map = {
        "AAF": "EXPORT_AAF", "DRT": "EXPORT_DRT", "EDL": "EXPORT_EDL",
        "FCP_7_XML": "EXPORT_FCP_7_XML",
        "FCPXML_1_8": "EXPORT_FCPXML_1_8", "FCPXML_1_9": "EXPORT_FCPXML_1_9",
        "FCPXML_1_10": "EXPORT_FCPXML_1_10",
        "HDR_10_PROFILE_A": "EXPORT_HDR_10_PROFILE_A",
        "HDR_10_PROFILE_B": "EXPORT_HDR_10_PROFILE_B",
        "TEXT_CSV": "EXPORT_TEXT_CSV", "TEXT_TAB": "EXPORT_TEXT_TAB",
        "DOLBY_VISION_VER_2_9": "EXPORT_DOLBY_VISION_VER_2_9",
        "DOLBY_VISION_VER_4_0": "EXPORT_DOLBY_VISION_VER_4_0",
        "DOLBY_VISION_VER_5_1": "EXPORT_DOLBY_VISION_VER_5_1",
        "OTIO": "EXPORT_OTIO", "ALE": "EXPORT_ALE", "ALE_CDL": "EXPORT_ALE_CDL",
    }
    subtype_map = {
        "EXPORT_NONE": "EXPORT_NONE", "EXPORT_AAF_NEW": "EXPORT_AAF_NEW",
        "EXPORT_AAF_EXISTING": "EXPORT_AAF_EXISTING",
        "EXPORT_CDL": "EXPORT_CDL", "EXPORT_SDL": "EXPORT_SDL",
        "EXPORT_MISSING_CLIPS": "EXPORT_MISSING_CLIPS",
    }
    et_attr = type_map.get(export_type)
    if not et_attr:
        return {"error": "Unknown exportType '%s'. Valid: %s" % (export_type, ", ".join(type_map.keys()))}
    es_attr = subtype_map.get(export_subtype, "EXPORT_NONE")
    et = safe(lambda: getattr(r, et_attr))
    es = safe(lambda: getattr(r, es_attr))
    if et is None:
        return {"error": "Resolve does not support export constant '%s'" % et_attr}
    ok = tl.Export(file_name, et, es)
    return {"success": bool(ok), "fileName": file_name, "exportType": export_type}


# -- Gallery / Stills -------------------------------------------------------

def action_set_current_album(body):
    _, proj, err = _project()
    if err:
        return err
    gallery = safe(lambda: proj.GetGallery())
    if not gallery:
        return {"error": "Cannot access gallery"}
    album, aerr = _get_album(gallery, body)
    if aerr:
        return aerr
    ok = gallery.SetCurrentStillAlbum(album)
    name = safe(lambda: gallery.GetAlbumName(album))
    return {"success": bool(ok), "albumName": name}


def action_create_gallery_album(body):
    _, proj, err = _project()
    if err:
        return err
    gallery = safe(lambda: proj.GetGallery())
    if not gallery:
        return {"error": "Cannot access gallery"}
    album_type = body.get("albumType", "still")
    if album_type == "powergrade":
        album = gallery.CreateGalleryPowerGradeAlbum()
    else:
        album = gallery.CreateGalleryStillAlbum()
    if not album:
        return {"error": "Failed to create %s album" % album_type}
    name = body.get("name", "")
    if name:
        gallery.SetAlbumName(album, name)
    final_name = safe(lambda: gallery.GetAlbumName(album))
    return {"success": True, "albumName": final_name, "albumType": album_type}


def action_grab_still(body):
    _, _, tl, err = _timeline()
    if err:
        return err
    still = tl.GrabStill()
    if not still:
        return {"error": "Failed to grab still. Make sure you are on the Color page."}
    return {"success": True}


def action_grab_all_stills(body):
    _, _, tl, err = _timeline()
    if err:
        return err
    source = int(body.get("stillFrameSource", 2))
    stills = tl.GrabAllStills(source)
    if not stills:
        return {"error": "Failed to grab stills"}
    return {"success": True, "count": len(stills)}


def action_export_stills(body):
    _, proj, err = _project()
    if err:
        return err
    gallery = safe(lambda: proj.GetGallery())
    if not gallery:
        return {"error": "Cannot access gallery"}
    album, aerr = _get_album(gallery, body)
    if aerr:
        return aerr
    folder_path = body.get("folderPath", "")
    file_prefix = body.get("filePrefix", "still")
    fmt = body.get("format", "png")
    if not folder_path:
        return {"error": "folderPath is required"}
    stills = safe(lambda: album.GetStills()) or []
    still_indices = body.get("stillIndices", [])
    if still_indices:
        selected = [stills[i - 1] for i in still_indices if 1 <= i <= len(stills)]
    else:
        selected = stills
    if not selected:
        return {"error": "No stills to export"}
    ok = album.ExportStills(selected, folder_path, file_prefix, fmt)
    return {"success": bool(ok), "exported": len(selected), "folderPath": folder_path}


def action_import_stills(body):
    _, proj, err = _project()
    if err:
        return err
    gallery = safe(lambda: proj.GetGallery())
    if not gallery:
        return {"error": "Cannot access gallery"}
    album = safe(lambda: gallery.GetCurrentStillAlbum())
    if not album:
        return {"error": "No album selected"}
    file_paths = body.get("filePaths", [])
    if not file_paths:
        return {"error": "filePaths array is required"}
    ok = album.ImportStills(file_paths)
    return {"success": bool(ok)}


def action_delete_stills(body):
    _, proj, err = _project()
    if err:
        return err
    gallery = safe(lambda: proj.GetGallery())
    if not gallery:
        return {"error": "Cannot access gallery"}
    album, aerr = _get_album(gallery, body)
    if aerr:
        return aerr
    stills = safe(lambda: album.GetStills()) or []
    still_indices = body.get("stillIndices", [])
    if not still_indices:
        return {"error": "stillIndices array is required"}
    selected = [stills[i - 1] for i in still_indices if 1 <= i <= len(stills)]
    if not selected:
        return {"error": "No stills found at given indices"}
    ok = album.DeleteStills(selected)
    return {"success": bool(ok), "deleted": len(selected)}


def action_set_still_label(body):
    _, proj, err = _project()
    if err:
        return err
    gallery = safe(lambda: proj.GetGallery())
    if not gallery:
        return {"error": "Cannot access gallery"}
    album = safe(lambda: gallery.GetCurrentStillAlbum())
    if not album:
        return {"error": "No album selected"}
    still_index = int(body.get("stillIndex", 0))
    label = body.get("label", "")
    stills = safe(lambda: album.GetStills()) or []
    if still_index < 1 or still_index > len(stills):
        return {"error": "stillIndex %d out of range (1-%d)" % (still_index, len(stills))}
    ok = album.SetLabel(stills[still_index - 1], label)
    return {"success": bool(ok), "label": label}


# -- Color Grading / Node Graph / LUT / CDL --------------------------------

def gather_node_graph(qs):
    """Get the color node graph for a timeline item or the timeline itself."""
    scope = qs.get("scope", ["clip"])[0]
    if scope == "timeline":
        _, _, tl, err = _timeline()
        if err:
            return err
        graph = safe(lambda: tl.GetNodeGraph())
        if not graph:
            return {"error": "Cannot get timeline node graph"}
    else:
        item, err = _clip_at({
            "trackType": qs.get("track_type", ["video"])[0],
            "trackIndex": int(qs.get("track_index", ["1"])[0]),
            "clipIndex": int(qs.get("clip_index", ["0"])[0]),
        })
        if err:
            return err
        layer = int(qs.get("layer_index", ["1"])[0])
        graph = safe(lambda: item.GetNodeGraph(layer))
        if not graph:
            return {"error": "Cannot get clip node graph"}
    num = safe(lambda: graph.GetNumNodes()) or 0
    nodes = []
    for i in range(1, num + 1):
        nodes.append({
            "index": i,
            "label": safe(lambda i=i: graph.GetNodeLabel(i)) or "",
            "lut": safe(lambda i=i: graph.GetLUT(i)) or "",
            "tools": safe(lambda i=i: graph.GetToolsInNode(i)) or [],
            "cacheMode": safe(lambda i=i: graph.GetNodeCacheMode(i)),
        })
    return {"nodeCount": num, "nodes": nodes}


def action_set_lut(body):
    item, err = _clip_at(body)
    if err:
        return err
    layer = int(body.get("layerIndex", 1))
    graph = safe(lambda: item.GetNodeGraph(layer))
    if not graph:
        return {"error": "Cannot get node graph"}
    node_index = int(body.get("nodeIndex", 1))
    lut_path = body.get("lutPath", "")
    if not lut_path:
        return {"error": "lutPath is required"}
    ok = graph.SetLUT(node_index, lut_path)
    return {"success": bool(ok), "nodeIndex": node_index, "lutPath": lut_path}


def action_get_lut(body):
    item, err = _clip_at(body)
    if err:
        return err
    layer = int(body.get("layerIndex", 1))
    graph = safe(lambda: item.GetNodeGraph(layer))
    if not graph:
        return {"error": "Cannot get node graph"}
    node_index = int(body.get("nodeIndex", 1))
    lut = safe(lambda: graph.GetLUT(node_index))
    return {"nodeIndex": node_index, "lutPath": lut or ""}


def action_set_node_enabled(body):
    item, err = _clip_at(body)
    if err:
        return err
    layer = int(body.get("layerIndex", 1))
    graph = safe(lambda: item.GetNodeGraph(layer))
    if not graph:
        return {"error": "Cannot get node graph"}
    node_index = int(body.get("nodeIndex", 1))
    enabled = bool(body.get("enabled", True))
    ok = graph.SetNodeEnabled(node_index, enabled)
    return {"success": bool(ok), "nodeIndex": node_index, "enabled": enabled}


def action_apply_grade_from_drx(body):
    item, err = _clip_at(body)
    if err:
        return err
    layer = int(body.get("layerIndex", 1))
    graph = safe(lambda: item.GetNodeGraph(layer))
    if not graph:
        return {"error": "Cannot get node graph"}
    path = body.get("drxPath", "")
    grade_mode = int(body.get("gradeMode", 0))
    if not path:
        return {"error": "drxPath is required"}
    ok = graph.ApplyGradeFromDRX(path, grade_mode)
    return {"success": bool(ok), "drxPath": path, "gradeMode": grade_mode}


def action_reset_all_grades(body):
    item, err = _clip_at(body)
    if err:
        return err
    layer = int(body.get("layerIndex", 1))
    graph = safe(lambda: item.GetNodeGraph(layer))
    if not graph:
        return {"error": "Cannot get node graph"}
    ok = graph.ResetAllGrades()
    return {"success": bool(ok)}


def action_apply_arri_cdl_lut(body):
    item, err = _clip_at(body)
    if err:
        return err
    layer = int(body.get("layerIndex", 1))
    graph = safe(lambda: item.GetNodeGraph(layer))
    if not graph:
        return {"error": "Cannot get node graph"}
    ok = graph.ApplyArriCdlLut()
    return {"success": bool(ok)}


def action_set_cdl(body):
    item, err = _clip_at(body)
    if err:
        return err
    cdl_map = body.get("cdl", {})
    if not cdl_map:
        return {"error": "cdl dict is required with keys: NodeIndex, Slope, Offset, Power, Saturation"}
    ok = item.SetCDL(cdl_map)
    return {"success": bool(ok)}


def action_export_lut(body):
    r, _ = _resolve()
    item, err = _clip_at(body)
    if err:
        return err
    export_type_str = body.get("exportType", "33PTCUBE")
    path = body.get("path", "")
    if not path:
        return {"error": "path is required"}
    type_map = {
        "17PTCUBE": "EXPORT_LUT_17PTCUBE",
        "33PTCUBE": "EXPORT_LUT_33PTCUBE",
        "65PTCUBE": "EXPORT_LUT_65PTCUBE",
        "PANASONICVLUT": "EXPORT_LUT_PANASONICVLUT",
    }
    attr = type_map.get(export_type_str)
    if not attr:
        return {"error": "Unknown exportType. Valid: %s" % ", ".join(type_map.keys())}
    et = safe(lambda: getattr(r, attr))
    if et is None:
        return {"error": "Resolve does not support %s" % attr}
    ok = item.ExportLUT(et, path)
    return {"success": bool(ok), "path": path}


def action_copy_grades(body):
    _, _, tl, err = _timeline()
    if err:
        return err
    source_ref = body.get("source", {})
    target_refs = body.get("targets", [])
    if not source_ref or not target_refs:
        return {"error": "source and targets are required"}
    source_item, serr = _clip_at(source_ref)
    if serr:
        return serr
    target_items = _resolve_clip_refs(tl, target_refs)
    if not target_items:
        return {"error": "No matching target clips found"}
    ok = source_item.CopyGrades(target_items)
    return {"success": bool(ok), "copiedTo": len(target_items)}


def action_reset_node_colors(body):
    item, err = _clip_at(body)
    if err:
        return err
    ok = item.ResetAllNodeColors()
    return {"success": bool(ok)}


# -- Color Versions ---------------------------------------------------------

def gather_color_versions(qs):
    item, err = _clip_at({
        "trackType": qs.get("track_type", ["video"])[0],
        "trackIndex": int(qs.get("track_index", ["1"])[0]),
        "clipIndex": int(qs.get("clip_index", ["0"])[0]),
    })
    if err:
        return err
    current = safe(lambda: item.GetCurrentVersion()) or {}
    local_versions = safe(lambda: item.GetVersionNameList(0)) or []
    remote_versions = safe(lambda: item.GetVersionNameList(1)) or []
    return {
        "clipName": safe(lambda: item.GetName()),
        "currentVersion": current,
        "localVersions": local_versions,
        "remoteVersions": remote_versions,
    }


def action_add_color_version(body):
    item, err = _clip_at(body)
    if err:
        return err
    name = body.get("versionName", "")
    vtype = int(body.get("versionType", 0))
    if not name:
        return {"error": "versionName is required"}
    ok = item.AddVersion(name, vtype)
    return {"success": bool(ok), "versionName": name, "versionType": vtype}


def action_load_color_version(body):
    item, err = _clip_at(body)
    if err:
        return err
    name = body.get("versionName", "")
    vtype = int(body.get("versionType", 0))
    if not name:
        return {"error": "versionName is required"}
    ok = item.LoadVersionByName(name, vtype)
    return {"success": bool(ok), "versionName": name}


def action_delete_color_version(body):
    item, err = _clip_at(body)
    if err:
        return err
    name = body.get("versionName", "")
    vtype = int(body.get("versionType", 0))
    if not name:
        return {"error": "versionName is required"}
    ok = item.DeleteVersionByName(name, vtype)
    return {"success": bool(ok), "versionName": name}


def action_rename_color_version(body):
    item, err = _clip_at(body)
    if err:
        return err
    old_name = body.get("oldName", "")
    new_name = body.get("newName", "")
    vtype = int(body.get("versionType", 0))
    if not old_name or not new_name:
        return {"error": "oldName and newName are required"}
    ok = item.RenameVersionByName(old_name, new_name, vtype)
    return {"success": bool(ok)}


# -- Color Groups -----------------------------------------------------------

def gather_color_groups(qs):
    _, proj, err = _project()
    if err:
        return err
    groups = safe(lambda: proj.GetColorGroupsList()) or []
    result = []
    for i, g in enumerate(groups):
        name = safe(lambda g=g: g.GetName())
        result.append({"index": i + 1, "name": name})
    return {"colorGroups": result}


def action_add_color_group(body):
    _, proj, err = _project()
    if err:
        return err
    name = body.get("groupName", "")
    if not name:
        return {"error": "groupName is required"}
    group = proj.AddColorGroup(name)
    if not group:
        return {"error": "Failed to create color group '%s'" % name}
    return {"success": True, "groupName": name}


def action_delete_color_group(body):
    _, proj, err = _project()
    if err:
        return err
    name = body.get("groupName", "")
    if not name:
        return {"error": "groupName is required"}
    groups = safe(lambda: proj.GetColorGroupsList()) or []
    target = None
    for g in groups:
        if safe(lambda g=g: g.GetName()) == name:
            target = g
            break
    if not target:
        return {"error": "Color group '%s' not found" % name}
    ok = proj.DeleteColorGroup(target)
    return {"success": bool(ok)}


def action_assign_to_color_group(body):
    _, proj, err = _project()
    if err:
        return err
    item, ierr = _clip_at(body)
    if ierr:
        return ierr
    group_name = body.get("groupName", "")
    if not group_name:
        return {"error": "groupName is required"}
    groups = safe(lambda: proj.GetColorGroupsList()) or []
    target = None
    for g in groups:
        if safe(lambda g=g: g.GetName()) == group_name:
            target = g
            break
    if not target:
        return {"error": "Color group '%s' not found" % group_name}
    ok = item.AssignToColorGroup(target)
    return {"success": bool(ok), "groupName": group_name}


def action_remove_from_color_group(body):
    item, err = _clip_at(body)
    if err:
        return err
    ok = item.RemoveFromColorGroup()
    return {"success": bool(ok)}


# -- Fusion Composition Management ------------------------------------------

def gather_fusion_comps(qs):
    item, err = _clip_at({
        "trackType": qs.get("track_type", ["video"])[0],
        "trackIndex": int(qs.get("track_index", ["1"])[0]),
        "clipIndex": int(qs.get("clip_index", ["0"])[0]),
    })
    if err:
        return err
    count = safe(lambda: item.GetFusionCompCount()) or 0
    names = safe(lambda: item.GetFusionCompNameList()) or []
    return {"clipName": safe(lambda: item.GetName()), "fusionCompCount": count, "fusionCompNames": names}


def action_add_fusion_comp(body):
    item, err = _clip_at(body)
    if err:
        return err
    comp = item.AddFusionComp()
    if not comp:
        return {"error": "Failed to add Fusion composition"}
    return {"success": True}


def action_import_fusion_comp(body):
    item, err = _clip_at(body)
    if err:
        return err
    path = body.get("path", "")
    if not path:
        return {"error": "path is required (.comp file)"}
    comp = item.ImportFusionComp(path)
    if not comp:
        return {"error": "Failed to import Fusion composition from '%s'" % path}
    return {"success": True, "path": path}


def action_export_fusion_comp(body):
    item, err = _clip_at(body)
    if err:
        return err
    path = body.get("path", "")
    comp_index = int(body.get("compIndex", 1))
    if not path:
        return {"error": "path is required"}
    ok = item.ExportFusionComp(path, comp_index)
    return {"success": bool(ok), "path": path, "compIndex": comp_index}


def action_delete_fusion_comp(body):
    item, err = _clip_at(body)
    if err:
        return err
    comp_name = body.get("compName", "")
    if not comp_name:
        return {"error": "compName is required"}
    ok = item.DeleteFusionCompByName(comp_name)
    return {"success": bool(ok), "compName": comp_name}


def action_load_fusion_comp(body):
    item, err = _clip_at(body)
    if err:
        return err
    comp_name = body.get("compName", "")
    if not comp_name:
        return {"error": "compName is required"}
    comp = item.LoadFusionCompByName(comp_name)
    if not comp:
        return {"error": "Failed to load Fusion composition '%s'" % comp_name}
    return {"success": True, "compName": comp_name}


def action_rename_fusion_comp(body):
    item, err = _clip_at(body)
    if err:
        return err
    old_name = body.get("oldName", "")
    new_name = body.get("newName", "")
    if not old_name or not new_name:
        return {"error": "oldName and newName are required"}
    ok = item.RenameFusionCompByName(old_name, new_name)
    return {"success": bool(ok)}


# -- Smart Features (Studio) ------------------------------------------------

def action_create_magic_mask(body):
    item, err = _clip_at(body)
    if err:
        return err
    mode = body.get("mode", "F")
    ok = item.CreateMagicMask(mode)
    return {"success": bool(ok), "mode": mode}


def action_regenerate_magic_mask(body):
    item, err = _clip_at(body)
    if err:
        return err
    ok = item.RegenerateMagicMask()
    return {"success": bool(ok)}


def action_stabilize(body):
    item, err = _clip_at(body)
    if err:
        return err
    ok = item.Stabilize()
    return {"success": bool(ok)}


def action_smart_reframe(body):
    item, err = _clip_at(body)
    if err:
        return err
    ok = item.SmartReframe()
    return {"success": bool(ok)}


# -- Audio / Fairlight -------------------------------------------------------

def gather_fairlight_presets(qs):
    r, err = _resolve()
    if err:
        return err
    presets = safe(lambda: r.GetFairlightPresets()) or []
    return {"presets": presets}


def action_apply_fairlight_preset(body):
    _, proj, err = _project()
    if err:
        return err
    name = body.get("presetName", "")
    if not name:
        return {"error": "presetName is required"}
    ok = proj.ApplyFairlightPresetToCurrentTimeline(name)
    return {"success": bool(ok), "presetName": name}


def action_insert_audio_at_playhead(body):
    _, proj, err = _project()
    if err:
        return err
    media_path = body.get("mediaPath", "")
    start_offset = int(body.get("startOffsetInSamples", 0))
    duration = int(body.get("durationInSamples", 0))
    if not media_path:
        return {"error": "mediaPath is required"}
    ok = proj.InsertAudioToCurrentTrackAtPlayhead(media_path, start_offset, duration)
    return {"success": bool(ok)}


def gather_voice_isolation_state(qs):
    scope = qs.get("scope", ["clip"])[0]
    if scope == "track":
        _, _, tl, err = _timeline()
        if err:
            return err
        ti = int(qs.get("track_index", ["1"])[0])
        state = safe(lambda: tl.GetVoiceIsolationState(ti))
        return {"scope": "track", "trackIndex": ti, "state": state or {}}
    else:
        item, err = _clip_at({
            "trackType": qs.get("track_type", ["video"])[0],
            "trackIndex": int(qs.get("track_index", ["1"])[0]),
            "clipIndex": int(qs.get("clip_index", ["0"])[0]),
        })
        if err:
            return err
        state = safe(lambda: item.GetVoiceIsolationState())
        return {"scope": "clip", "clipName": safe(lambda: item.GetName()), "state": state or {}}


def action_set_voice_isolation_state(body):
    scope = body.get("scope", "clip")
    state = body.get("state", {})
    if not state:
        return {"error": "state dict required: {isEnabled: bool, amount: int (0-100)}"}
    if scope == "track":
        _, _, tl, err = _timeline()
        if err:
            return err
        ti = int(body.get("trackIndex", 1))
        ok = tl.SetVoiceIsolationState(ti, state)
        return {"success": bool(ok), "scope": "track", "trackIndex": ti}
    else:
        item, err = _clip_at(body)
        if err:
            return err
        ok = item.SetVoiceIsolationState(state)
        return {"success": bool(ok), "scope": "clip"}


# -- Take Selector -----------------------------------------------------------

def gather_takes(qs):
    item, err = _clip_at({
        "trackType": qs.get("track_type", ["video"])[0],
        "trackIndex": int(qs.get("track_index", ["1"])[0]),
        "clipIndex": int(qs.get("clip_index", ["0"])[0]),
    })
    if err:
        return err
    count = safe(lambda: item.GetTakesCount()) or 0
    selected = safe(lambda: item.GetSelectedTakeIndex()) or 0
    takes = []
    for i in range(1, count + 1):
        info = safe(lambda i=i: item.GetTakeByIndex(i)) or {}
        takes.append({"index": i, "startFrame": info.get("startFrame"), "endFrame": info.get("endFrame")})
    return {"clipName": safe(lambda: item.GetName()), "takesCount": count, "selectedTakeIndex": selected, "takes": takes}


def action_add_take(body):
    _, proj, err = _project()
    if err:
        return err
    pool = proj.GetMediaPool()
    if not pool:
        return {"error": "No media pool"}
    item, ierr = _clip_at(body)
    if ierr:
        return ierr
    mp_clip_name = body.get("mediaPoolClipName", "")
    if not mp_clip_name:
        return {"error": "mediaPoolClipName is required"}
    mp_item = _find_pool_item(pool, mp_clip_name)
    if not mp_item:
        return {"error": "Clip '%s' not found in media pool" % mp_clip_name}
    start = body.get("startFrame")
    end = body.get("endFrame")
    if start is not None and end is not None:
        ok = item.AddTake(mp_item, int(start), int(end))
    else:
        ok = item.AddTake(mp_item)
    return {"success": bool(ok)}


def action_select_take(body):
    item, err = _clip_at(body)
    if err:
        return err
    idx = int(body.get("takeIndex", 1))
    ok = item.SelectTakeByIndex(idx)
    return {"success": bool(ok), "takeIndex": idx}


def action_delete_take(body):
    item, err = _clip_at(body)
    if err:
        return err
    idx = int(body.get("takeIndex", 1))
    ok = item.DeleteTakeByIndex(idx)
    return {"success": bool(ok), "takeIndex": idx}


def action_finalize_take(body):
    item, err = _clip_at(body)
    if err:
        return err
    ok = item.FinalizeTake()
    return {"success": bool(ok)}


# -- Proxy / Cache / Misc Clip Ops ------------------------------------------

def action_link_proxy_media(body):
    _, proj, err = _project()
    if err:
        return err
    pool = proj.GetMediaPool()
    if not pool:
        return {"error": "No media pool"}
    clip_name = body.get("clipName", "")
    proxy_path = body.get("proxyMediaFilePath", "")
    if not clip_name or not proxy_path:
        return {"error": "clipName and proxyMediaFilePath are required"}
    item = _find_pool_item(pool, clip_name)
    if not item:
        return {"error": "Clip '%s' not found" % clip_name}
    ok = item.LinkProxyMedia(proxy_path)
    return {"success": bool(ok)}


def action_unlink_proxy_media(body):
    _, proj, err = _project()
    if err:
        return err
    pool = proj.GetMediaPool()
    if not pool:
        return {"error": "No media pool"}
    clip_name = body.get("clipName", "")
    if not clip_name:
        return {"error": "clipName is required"}
    item = _find_pool_item(pool, clip_name)
    if not item:
        return {"error": "Clip '%s' not found" % clip_name}
    ok = item.UnlinkProxyMedia()
    return {"success": bool(ok)}


def action_replace_clip(body):
    _, proj, err = _project()
    if err:
        return err
    pool = proj.GetMediaPool()
    if not pool:
        return {"error": "No media pool"}
    clip_name = body.get("clipName", "")
    file_path = body.get("filePath", "")
    if not clip_name or not file_path:
        return {"error": "clipName and filePath are required"}
    item = _find_pool_item(pool, clip_name)
    if not item:
        return {"error": "Clip '%s' not found" % clip_name}
    ok = item.ReplaceClip(file_path)
    return {"success": bool(ok)}


def action_set_clip_cache(body):
    item, err = _clip_at(body)
    if err:
        return err
    cache_type = body.get("cacheType", "color")
    cache_value = int(body.get("cacheValue", 1))
    if cache_type == "fusion":
        ok = item.SetFusionOutputCache(cache_value)
    else:
        ok = item.SetColorOutputCache(cache_value)
    return {"success": bool(ok), "cacheType": cache_type, "cacheValue": cache_value}


def action_update_sidecar(body):
    item, err = _clip_at(body)
    if err:
        return err
    ok = item.UpdateSidecar()
    return {"success": bool(ok)}


def gather_linked_items(qs):
    item, err = _clip_at({
        "trackType": qs.get("track_type", ["video"])[0],
        "trackIndex": int(qs.get("track_index", ["1"])[0]),
        "clipIndex": int(qs.get("clip_index", ["0"])[0]),
    })
    if err:
        return err
    linked = safe(lambda: item.GetLinkedItems()) or []
    result = []
    for li in linked:
        ti = safe(lambda li=li: li.GetTrackTypeAndIndex()) or []
        result.append({
            "name": safe(lambda li=li: li.GetName()),
            "trackType": ti[0] if len(ti) > 0 else None,
            "trackIndex": ti[1] if len(ti) > 1 else None,
        })
    return {"clipName": safe(lambda: item.GetName()), "linkedItems": result}


def action_set_timeline_mark_in_out(body):
    _, _, tl, err = _timeline()
    if err:
        return err
    mark_in = body.get("markIn")
    mark_out = body.get("markOut")
    mark_type = body.get("type", "all")
    if mark_in is not None and mark_out is not None:
        ok = tl.SetMarkInOut(int(mark_in), int(mark_out), mark_type)
        return {"success": bool(ok)}
    return {"error": "markIn and markOut are required"}


def action_clear_timeline_mark_in_out(body):
    _, _, tl, err = _timeline()
    if err:
        return err
    mark_type = body.get("type", "all")
    ok = tl.ClearMarkInOut(mark_type)
    return {"success": bool(ok)}


# -- Project Manager ---------------------------------------------------------

def gather_project_list(qs):
    r, err = _resolve()
    if err:
        return err
    pm = r.GetProjectManager()
    if not pm:
        return {"error": "No project manager"}
    projects = safe(lambda: pm.GetProjectListInCurrentFolder()) or []
    folders = safe(lambda: pm.GetFolderListInCurrentFolder()) or []
    current_folder = safe(lambda: pm.GetCurrentFolder()) or ""
    current_db = safe(lambda: pm.GetCurrentDatabase()) or {}
    return {
        "currentFolder": current_folder,
        "currentDatabase": current_db,
        "projects": projects,
        "folders": folders,
    }


def gather_database_list(qs):
    r, err = _resolve()
    if err:
        return err
    pm = r.GetProjectManager()
    if not pm:
        return {"error": "No project manager"}
    dbs = safe(lambda: pm.GetDatabaseList()) or []
    current = safe(lambda: pm.GetCurrentDatabase()) or {}
    return {"currentDatabase": current, "databases": dbs}


def action_load_project(body):
    r, err = _resolve()
    if err:
        return err
    pm = r.GetProjectManager()
    if not pm:
        return {"error": "No project manager"}
    name = body.get("projectName", "")
    if not name:
        return {"error": "projectName is required"}
    proj = pm.LoadProject(name)
    if not proj:
        return {"error": "Failed to load project '%s'" % name}
    return {"success": True, "projectName": safe(lambda: proj.GetName())}


def action_create_project(body):
    r, err = _resolve()
    if err:
        return err
    pm = r.GetProjectManager()
    if not pm:
        return {"error": "No project manager"}
    name = body.get("projectName", "")
    if not name:
        return {"error": "projectName is required"}
    proj = pm.CreateProject(name)
    if not proj:
        return {"error": "Failed to create project '%s' (name may already exist)" % name}
    return {"success": True, "projectName": safe(lambda: proj.GetName())}


def action_delete_project(body):
    r, err = _resolve()
    if err:
        return err
    pm = r.GetProjectManager()
    name = body.get("projectName", "")
    if not name:
        return {"error": "projectName is required"}
    ok = pm.DeleteProject(name)
    return {"success": bool(ok)}


def action_archive_project(body):
    r, err = _resolve()
    if err:
        return err
    pm = r.GetProjectManager()
    name = body.get("projectName", "")
    file_path = body.get("filePath", "")
    if not name or not file_path:
        return {"error": "projectName and filePath are required"}
    src_media = body.get("archiveSrcMedia", True)
    render_cache = body.get("archiveRenderCache", True)
    proxy_media = body.get("archiveProxyMedia", False)
    ok = pm.ArchiveProject(name, file_path, src_media, render_cache, proxy_media)
    return {"success": bool(ok)}


def action_export_project(body):
    r, err = _resolve()
    if err:
        return err
    pm = r.GetProjectManager()
    name = body.get("projectName", "")
    file_path = body.get("filePath", "")
    if not name or not file_path:
        return {"error": "projectName and filePath are required"}
    with_stills = body.get("withStillsAndLUTs", True)
    ok = pm.ExportProject(name, file_path, with_stills)
    return {"success": bool(ok)}


def action_import_project(body):
    r, err = _resolve()
    if err:
        return err
    pm = r.GetProjectManager()
    file_path = body.get("filePath", "")
    if not file_path:
        return {"error": "filePath is required"}
    project_name = body.get("projectName")
    ok = pm.ImportProject(file_path, project_name) if project_name else pm.ImportProject(file_path)
    return {"success": bool(ok)}


def action_navigate_project_folder(body):
    r, err = _resolve()
    if err:
        return err
    pm = r.GetProjectManager()
    action = body.get("action", "")
    folder_name = body.get("folderName", "")
    if action == "root":
        ok = pm.GotoRootFolder()
    elif action == "parent":
        ok = pm.GotoParentFolder()
    elif action == "open" and folder_name:
        ok = pm.OpenFolder(folder_name)
    elif action == "create" and folder_name:
        ok = pm.CreateFolder(folder_name)
    elif action == "delete" and folder_name:
        ok = pm.DeleteFolder(folder_name)
    else:
        return {"error": "action required: 'root', 'parent', 'open', 'create', or 'delete'"}
    return {"success": bool(ok), "action": action}


def action_set_database(body):
    r, err = _resolve()
    if err:
        return err
    pm = r.GetProjectManager()
    db_info = body.get("dbInfo", {})
    if not db_info:
        return {"error": "dbInfo dict required with keys DbType, DbName, optional IpAddress"}
    ok = pm.SetCurrentDatabase(db_info)
    return {"success": bool(ok)}


# -- Resolve-level / Presets / MediaStorage ----------------------------------

def action_layout_preset(body):
    r, err = _resolve()
    if err:
        return err
    action = body.get("action", "")
    name = body.get("presetName", "")
    path = body.get("presetFilePath", "")
    if action == "load" and name:
        return {"success": bool(r.LoadLayoutPreset(name))}
    elif action == "save" and name:
        return {"success": bool(r.SaveLayoutPreset(name))}
    elif action == "update" and name:
        return {"success": bool(r.UpdateLayoutPreset(name))}
    elif action == "delete" and name:
        return {"success": bool(r.DeleteLayoutPreset(name))}
    elif action == "export" and name and path:
        return {"success": bool(r.ExportLayoutPreset(name, path))}
    elif action == "import" and path:
        return {"success": bool(r.ImportLayoutPreset(path, name))}
    return {"error": "action required: 'load', 'save', 'update', 'delete', 'export', 'import'"}


def action_render_preset(body):
    r, err = _resolve()
    if err:
        return err
    _, proj, perr = _project()
    if perr:
        return perr
    action = body.get("action", "")
    name = body.get("presetName", "")
    path = body.get("presetPath", "")
    if action == "import" and path:
        return {"success": bool(r.ImportRenderPreset(path))}
    elif action == "export" and name and path:
        return {"success": bool(r.ExportRenderPreset(name, path))}
    elif action == "load" and name:
        return {"success": bool(proj.LoadRenderPreset(name))}
    elif action == "saveAs" and name:
        return {"success": bool(proj.SaveAsNewRenderPreset(name))}
    elif action == "delete" and name:
        return {"success": bool(proj.DeleteRenderPreset(name))}
    elif action == "list":
        return {"presets": safe(lambda: proj.GetRenderPresetList()) or []}
    return {"error": "action required: 'load', 'saveAs', 'delete', 'list', 'import', 'export'"}


def action_burnin_preset(body):
    r, err = _resolve()
    if err:
        return err
    action = body.get("action", "")
    name = body.get("presetName", "")
    path = body.get("presetPath", "")
    if action == "import" and path:
        return {"success": bool(r.ImportBurnInPreset(path))}
    elif action == "export" and name and path:
        return {"success": bool(r.ExportBurnInPreset(name, path))}
    elif action == "load" and name:
        _, proj, perr = _project()
        if perr:
            return perr
        return {"success": bool(proj.LoadBurnInPreset(name))}
    return {"error": "action required: 'load', 'import', 'export'"}


def action_set_keyframe_mode(body):
    r, err = _resolve()
    if err:
        return err
    mode = int(body.get("mode", 0))
    ok = r.SetKeyframeMode(mode)
    return {"success": bool(ok), "mode": mode}


def gather_keyframe_mode(qs):
    r, err = _resolve()
    if err:
        return err
    mode = safe(lambda: r.GetKeyframeMode())
    labels = {0: "All", 1: "Color", 2: "Sizing"}
    return {"keyframeMode": mode, "label": labels.get(mode, "Unknown")}


def action_quick_export(body):
    _, proj, err = _project()
    if err:
        return err
    preset_name = body.get("presetName", "")
    if not preset_name:
        presets = safe(lambda: proj.GetQuickExportRenderPresets()) or []
        return {"error": "presetName is required", "availablePresets": presets}
    params = body.get("params", {})
    result = proj.RenderWithQuickExport(preset_name, params)
    return {"result": result}


def gather_quick_export_presets(qs):
    _, proj, err = _project()
    if err:
        return err
    presets = safe(lambda: proj.GetQuickExportRenderPresets()) or []
    return {"presets": presets}


def action_set_render_mode(body):
    _, proj, err = _project()
    if err:
        return err
    mode = int(body.get("renderMode", 0))
    ok = proj.SetCurrentRenderMode(mode)
    return {"success": bool(ok), "renderMode": mode}


def action_get_render_job_status(body):
    _, proj, err = _project()
    if err:
        return err
    job_id = body.get("jobId", "")
    if not job_id:
        return {"error": "jobId is required"}
    status = safe(lambda: proj.GetRenderJobStatus(job_id))
    return {"jobId": job_id, "status": status or {}}


def action_refresh_lut_list(body):
    _, proj, err = _project()
    if err:
        return err
    ok = proj.RefreshLUTList()
    return {"success": bool(ok)}


def gather_render_resolutions(qs):
    _, proj, err = _project()
    if err:
        return err
    fmt = qs.get("format", [""])[0]
    codec = qs.get("codec", [""])[0]
    if fmt and codec:
        res = safe(lambda: proj.GetRenderResolutions(fmt, codec)) or []
    else:
        res = safe(lambda: proj.GetRenderResolutions()) or []
    return {"resolutions": res}


def gather_media_storage(qs):
    r, err = _resolve()
    if err:
        return err
    ms = r.GetMediaStorage()
    if not ms:
        return {"error": "No media storage"}
    volumes = safe(lambda: ms.GetMountedVolumeList()) or []
    folder_path = qs.get("folder_path", [""])[0]
    result = {"volumes": volumes}
    if folder_path:
        subfolders = safe(lambda: ms.GetSubFolderList(folder_path)) or []
        files = safe(lambda: ms.GetFileList(folder_path)) or []
        result["subfolders"] = subfolders
        result["files"] = files
    return result


def action_reveal_in_storage(body):
    r, err = _resolve()
    if err:
        return err
    ms = r.GetMediaStorage()
    if not ms:
        return {"error": "No media storage"}
    path = body.get("path", "")
    if not path:
        return {"error": "path is required"}
    ok = ms.RevealInStorage(path)
    return {"success": bool(ok)}


# ---------------------------------------------------------------------------
# Route tables
# ---------------------------------------------------------------------------

GET_ROUTES = {
    "/status":                  lambda qs: gather_status(),
    "/project":                 lambda qs: gather_project(),
    "/page":                    lambda qs: gather_page(),
    "/timeline":                lambda qs: gather_timeline(),
    "/timeline/clips":          lambda qs: gather_clips(
                                    qs.get("track_type", ["video"])[0],
                                    int(qs.get("track_index", ["1"])[0])),
    "/timeline/markers":        lambda qs: gather_markers(),
    "/timeline/current-item":   lambda qs: gather_current_video_item(qs),
    "/timeline/thumbnail":      lambda qs: gather_clip_thumbnail(qs),
    "/render":                  lambda qs: gather_render(),
    "/render/resolutions":      gather_render_resolutions,
    "/render/quick-export-presets": gather_quick_export_presets,
    "/mediapool":               lambda qs: gather_media_pool(),
    "/mediapool/structure":     gather_media_pool_structure,
    "/mediapool/clip/metadata": gather_clip_metadata,
    "/mediapool/clip/info":     gather_clip_info,
    "/clip/markers":            gather_clip_markers,
    "/clip/flags":              gather_clip_flags,
    "/clip/node-graph":         gather_node_graph,
    "/clip/color-versions":     gather_color_versions,
    "/clip/fusion-comps":       gather_fusion_comps,
    "/clip/takes":              gather_takes,
    "/clip/linked-items":       gather_linked_items,
    "/color/groups":            gather_color_groups,
    "/audio/voice-isolation":   gather_voice_isolation_state,
    "/fairlight/presets":       gather_fairlight_presets,
    "/gallery/albums":          gather_gallery_albums,
    "/gallery/stills":          gather_album_stills,
    "/keyframe-mode":           gather_keyframe_mode,
    "/projects":                gather_project_list,
    "/databases":               gather_database_list,
    "/media-storage":           gather_media_storage,
}

def action_shutdown(body):
    """Gracefully stop the HTTP server (used for hot-reload)."""
    import threading
    threading.Thread(target=lambda: server.shutdown(), daemon=True).start()
    return {"success": True, "message": "Shutting down"}


POST_ROUTES = {
    "/bridge/shutdown":             action_shutdown,
    "/page":                        action_open_page,
    "/playhead":                    action_set_timecode,
    # markers
    "/marker/add":                  action_add_marker,
    "/marker/delete":               action_delete_marker,
    # timeline
    "/timeline/switch":             action_switch_timeline,
    "/timeline/create":             action_create_timeline,
    "/timeline/rename":             action_rename_timeline,
    "/timeline/duplicate":          action_duplicate_timeline,
    "/timeline/export":             action_export_timeline,
    "/timeline/mark-in-out":        action_set_timeline_mark_in_out,
    "/timeline/clear-mark-in-out":  action_clear_timeline_mark_in_out,
    # timeline clip manipulation
    "/timeline/clips/delete":       action_delete_timeline_clips,
    "/timeline/clips/link":         action_link_timeline_clips,
    "/timeline/compound-clip":      action_create_compound_clip,
    "/timeline/fusion-clip":        action_create_fusion_clip,
    # tracks
    "/track/add":                   action_add_track,
    "/track/delete":                action_delete_track,
    "/track/enable":                action_set_track_enable,
    "/track/lock":                  action_set_track_lock,
    "/track/rename":                action_set_track_name,
    # media
    "/media/import":                action_import_media,
    "/media/import-storage":        action_import_media_from_storage,
    "/media/append":                action_append_to_timeline,
    "/media/insert":                action_insert_to_timeline,
    # media pool deep access
    "/mediapool/navigate":          action_navigate_media_pool,
    "/mediapool/folder/create":     action_create_media_pool_folder,
    "/mediapool/clip/metadata":     action_set_clip_metadata,
    "/mediapool/clip/property":     action_set_pool_clip_property,
    "/mediapool/clips/delete":      action_delete_media_pool_clips,
    "/mediapool/clips/move":        action_move_media_pool_clips,
    "/mediapool/clips/relink":      action_relink_media_pool_clips,
    "/mediapool/clips/unlink":      action_unlink_media_pool_clips,
    "/mediapool/audio-sync":        action_auto_sync_audio,
    "/mediapool/timeline/import":   action_import_timeline_from_file,
    "/mediapool/metadata/export":   action_export_metadata,
    # clip operations
    "/clip/color":                  action_set_clip_color,
    "/clip/enabled":                action_set_clip_enabled,
    "/clip/properties":             action_set_clip_properties,
    "/clip/marker/add":             action_add_clip_marker,
    "/clip/marker/delete":          action_delete_clip_marker,
    "/clip/flag/add":               action_add_clip_flag,
    "/clip/flag/clear":             action_clear_clip_flags,
    "/clip/cache":                  action_set_clip_cache,
    "/clip/sidecar":                action_update_sidecar,
    # color grading / LUT / CDL
    "/color/set-lut":               action_set_lut,
    "/color/get-lut":               action_get_lut,
    "/color/set-node-enabled":      action_set_node_enabled,
    "/color/apply-drx":             action_apply_grade_from_drx,
    "/color/reset-grades":          action_reset_all_grades,
    "/color/apply-arri-cdl":        action_apply_arri_cdl_lut,
    "/color/set-cdl":               action_set_cdl,
    "/color/export-lut":            action_export_lut,
    "/color/copy-grades":           action_copy_grades,
    "/color/reset-node-colors":     action_reset_node_colors,
    # color versions
    "/color/version/add":           action_add_color_version,
    "/color/version/load":          action_load_color_version,
    "/color/version/delete":        action_delete_color_version,
    "/color/version/rename":        action_rename_color_version,
    # color groups
    "/color/group/add":             action_add_color_group,
    "/color/group/delete":          action_delete_color_group,
    "/color/group/assign":          action_assign_to_color_group,
    "/color/group/remove":          action_remove_from_color_group,
    # fusion comps per-clip
    "/clip/fusion/add":             action_add_fusion_comp,
    "/clip/fusion/import":          action_import_fusion_comp,
    "/clip/fusion/export":          action_export_fusion_comp,
    "/clip/fusion/delete":          action_delete_fusion_comp,
    "/clip/fusion/load":            action_load_fusion_comp,
    "/clip/fusion/rename":          action_rename_fusion_comp,
    # smart features
    "/clip/magic-mask":             action_create_magic_mask,
    "/clip/magic-mask/regenerate":  action_regenerate_magic_mask,
    "/clip/stabilize":              action_stabilize,
    "/clip/smart-reframe":          action_smart_reframe,
    # audio / fairlight
    "/audio/fairlight-preset":      action_apply_fairlight_preset,
    "/audio/insert-at-playhead":    action_insert_audio_at_playhead,
    "/audio/voice-isolation":       action_set_voice_isolation_state,
    # take selector
    "/clip/take/add":               action_add_take,
    "/clip/take/select":            action_select_take,
    "/clip/take/delete":            action_delete_take,
    "/clip/take/finalize":          action_finalize_take,
    # proxy
    "/mediapool/proxy/link":        action_link_proxy_media,
    "/mediapool/proxy/unlink":      action_unlink_proxy_media,
    "/mediapool/clip/replace":      action_replace_clip,
    # titles & generators
    "/title/insert":                action_insert_title,
    "/generator/insert":            action_insert_generator,
    "/fusion/insert":               action_insert_fusion_comp,
    # render
    "/render/settings":             action_set_render_settings,
    "/render/format":               action_set_render_format,
    "/render/formats":              action_get_render_formats,
    "/render/job/add":              action_add_render_job,
    "/render/job/status":           action_get_render_job_status,
    "/render/start":                action_start_rendering,
    "/render/stop":                 action_stop_rendering,
    "/render/job/delete":           action_delete_render_job,
    "/render/mode":                 action_set_render_mode,
    "/render/quick-export":         action_quick_export,
    "/render/refresh-luts":         action_refresh_lut_list,
    "/render/preset":               action_render_preset,
    # project
    "/project/save":                action_save_project,
    "/project/setting":             action_set_project_setting,
    "/timeline/setting":            action_set_timeline_setting,
    "/project/export-frame":        action_export_frame,
    "/timeline/subtitles":          action_create_subtitles,
    "/timeline/scene-cuts":         action_detect_scene_cuts,
    # project manager
    "/projects/load":               action_load_project,
    "/projects/create":             action_create_project,
    "/projects/delete":             action_delete_project,
    "/projects/archive":            action_archive_project,
    "/projects/export":             action_export_project,
    "/projects/import":             action_import_project,
    "/projects/folder":             action_navigate_project_folder,
    "/projects/database":           action_set_database,
    # resolve-level presets
    "/resolve/layout-preset":       action_layout_preset,
    "/resolve/burnin-preset":       action_burnin_preset,
    "/resolve/keyframe-mode":       action_set_keyframe_mode,
    # media storage
    "/media-storage/reveal":        action_reveal_in_storage,
    # gallery / stills
    "/gallery/album/set":           action_set_current_album,
    "/gallery/album/create":        action_create_gallery_album,
    "/gallery/grab":                action_grab_still,
    "/gallery/grab-all":            action_grab_all_stills,
    "/gallery/stills/export":       action_export_stills,
    "/gallery/stills/import":       action_import_stills,
    "/gallery/stills/delete":       action_delete_stills,
    "/gallery/stills/label":        action_set_still_label,
}


# ---------------------------------------------------------------------------
# HTTP handler
# ---------------------------------------------------------------------------

class BridgeHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def _respond(self, data):
        body = json.dumps(data, default=str).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _error(self, code, msg):
        body = json.dumps({"error": msg}).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        qs = parse_qs(parsed.query)
        handler = GET_ROUTES.get(path)
        if handler:
            try:
                self._respond(handler(qs))
            except Exception:
                self._error(500, traceback.format_exc())
        else:
            self._error(404, "Unknown GET endpoint: %s" % path)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        content_len = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(content_len) if content_len else b"{}"
        try:
            body = json.loads(raw)
        except Exception:
            self._error(400, "Invalid JSON body")
            return
        handler = POST_ROUTES.get(path)
        if handler:
            try:
                self._respond(handler(body))
            except Exception:
                self._error(500, traceback.format_exc())
        else:
            self._error(404, "Unknown POST endpoint: %s" % path)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


# ---------------------------------------------------------------------------
# Start server (with hot-reload: shut down any previous instance first)
# ---------------------------------------------------------------------------
import time
try:
    import urllib.request
    req = urllib.request.Request(
        "http://%s:%d/bridge/shutdown" % (HOST, PORT),
        data=b"{}",
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    urllib.request.urlopen(req, timeout=2)
    print("[CursorBridge] Sent shutdown to previous instance, waiting...")
    time.sleep(1.5)
except Exception:
    pass

print("[CursorBridge] Starting HTTP server on http://%s:%d ..." % (HOST, PORT))
server = None
try:
    server = HTTPServer((HOST, PORT), BridgeHandler)
    print("[CursorBridge] Bridge is running (read + write).  %d GET routes, %d POST routes." % (
        len(GET_ROUTES), len(POST_ROUTES)))
    print("[CursorBridge] To stop: close DaVinci Resolve or re-run this script.")
    server.serve_forever()
except OSError as e:
    if "Address already in use" in str(e) or "Only one usage" in str(e) or getattr(e, "errno", 0) == 10048:
        print("[CursorBridge] Port %d already in use — could not replace old bridge." % PORT)
        print("[CursorBridge] Restart DaVinci Resolve and try again.")
    else:
        print("[CursorBridge] ERROR: %s" % e)
except KeyboardInterrupt:
    print("[CursorBridge] Shutting down.")
except Exception as e:
    print("[CursorBridge] ERROR: %s" % e)
