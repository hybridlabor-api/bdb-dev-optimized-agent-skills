"""Probe which Fuses install directory Resolve actually scans.

Stages Blackmagic's known-working Example1 Fuse in BOTH candidate paths,
launches Resolve, and reports which class names register.
"""

import os
import subprocess
import sys
import time

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT)

from src.utils.platform import get_resolve_paths

paths = get_resolve_paths()
os.environ["RESOLVE_SCRIPT_API"] = paths["api_path"]
os.environ["RESOLVE_SCRIPT_LIB"] = paths["lib_path"]
sys.path.insert(0, paths["modules_path"])

import DaVinciResolveScript as dvr_script  # noqa: E402


def _add(comp, name):
    comp.Lock()
    try:
        return comp.AddTool(name, -1, -1)
    finally:
        comp.Unlock()


def main():
    cand = dvr_script.scriptapp("Resolve")
    if cand is not None:
        try:
            if cand.GetVersion():
                print("ABORT: Resolve already running")
                sys.exit(1)
        except Exception:
            pass

    subprocess.Popen(["open", "/Applications/DaVinci Resolve/DaVinci Resolve.app"])
    handle = None
    for i in range(60):
        time.sleep(2)
        cand = dvr_script.scriptapp("Resolve")
        if cand is not None:
            try:
                if cand.GetVersion():
                    handle = cand
                    break
            except Exception:
                pass
    if handle is None:
        print("ABORT: connect timeout")
        sys.exit(1)
    print(f"Connected: {handle.GetVersionString()}")

    pm = handle.GetProjectManager()
    try:
        pm.DeleteProject("McpPathProbe")
    except Exception:
        pass
    project = pm.CreateProject("McpPathProbe")
    mp = project.GetMediaPool()
    timeline = mp.CreateEmptyTimeline("PathProbe")
    timeline.InsertFusionCompositionIntoTimeline()
    handle.OpenPage("fusion")
    time.sleep(2)

    fusion = handle.Fusion()
    comp = fusion.GetCurrentComp()
    print(f"Comp: {comp.GetAttrs().get('COMPS_Name', '?')}")

    # The class registered by Example1 is "ExampleBrightContrast" per the
    # FuRegisterClass first arg. We staged copies under TWO file names but
    # both register the SAME class — Resolve will silently dedup or take
    # whichever loads first. So we can only test if EITHER path was scanned.
    print("\n=== Testing class 'ExampleBrightContrast' ===")
    try:
        t = _add(comp, "ExampleBrightContrast")
        if t is None:
            print("  [FAIL] Even Blackmagic's own example does not register.")
            print("  → Neither candidate Fuses directory is being scanned.")
        else:
            attrs = t.GetAttrs() or {}
            print(f"  [OK]   Registered as {attrs.get('TOOLS_RegID', '?')}")
            print("  → At least one of the candidate paths IS scanned.")
            t.Delete()
    except Exception as e:
        print(f"  [ERR] {e}")

    # Cleanup
    print("\n=== Cleanup ===")
    home = os.path.expanduser("~")
    for p in [
        os.path.join(home, "Library/Application Support/Blackmagic Design/"
                            "DaVinci Resolve/Fusion/Fuses/Example1.fuse"),
        os.path.join(home, "Library/Application Support/Blackmagic Design/"
                            "DaVinci Resolve/Support/Fusion/Fuses/Example1WithSupport.fuse"),
    ]:
        try:
            os.unlink(p)
            print(f"  removed: {os.path.basename(p)}")
        except OSError:
            pass

    try:
        pm.CloseProject(pm.GetCurrentProject())
        pm.DeleteProject("McpPathProbe")
    except Exception:
        pass

    handle.Quit()


if __name__ == "__main__":
    main()
