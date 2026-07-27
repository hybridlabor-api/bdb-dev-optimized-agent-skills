"""Live Resolve smoke test for v2.5.0 fuse_plugin authoring.

Installs a curated subset of generated Fuses to the real Fuses directory while
Resolve is closed, launches Resolve, builds a disposable project with a
Fusion-composition timeline item, attempts to instantiate each Fuse class via
comp.AddTool, and reports pass/fail per template.

Cleans up regardless of pass/fail. Quits Resolve afterward unless --keep-open.
"""

import argparse
import os
import subprocess
import sys
import time

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT)

from src.utils.platform import get_resolve_paths, get_resolve_plugin_paths

paths = get_resolve_paths()
os.environ["RESOLVE_SCRIPT_API"] = paths["api_path"]
os.environ["RESOLVE_SCRIPT_LIB"] = paths["lib_path"]
sys.path.insert(0, paths["modules_path"])

import DaVinciResolveScript as dvr_script  # noqa: E402
from src.utils import fuse_templates  # noqa: E402


# Curated subset spanning the highest-risk surfaces.
TEST_TEMPLATES = [
    ("color_matrix",     {"ops": ["brightness", "contrast"]}),
    ("text_overlay",     None),
    ("source_generator", {"kind": "gradient"}),
    ("transform",        None),
    ("modifier",         {"kind": "sine"}),
]


def _quit_resolve():
    try:
        h = dvr_script.scriptapp("Resolve")
        if h is not None:
            h.Quit()
    except Exception:
        pass


def _add_tool(comp, tool_type):
    """Locked AddTool — mirrors src/server.py fusion_comp.add_tool."""
    comp.Lock()
    try:
        return comp.AddTool(tool_type, -1, -1)
    finally:
        comp.Unlock()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--keep-open", action="store_true",
                        help="Leave Resolve open with the disposable project after test.")
    args = parser.parse_args()

    candidate = dvr_script.scriptapp("Resolve")
    if candidate is not None:
        try:
            if candidate.GetVersion():
                print("ABORT: Resolve is already running. Quit it first.")
                sys.exit(1)
        except Exception:
            pass

    fuses_dir = get_resolve_plugin_paths()["fuses_dir"]
    os.makedirs(fuses_dir, exist_ok=True)

    print(f"=== Installing {len(TEST_TEMPLATES)} templates ===")
    installed = []
    for kind, options in TEST_TEMPLATES:
        name = "McpLive" + kind.replace("_", "").title()
        try:
            source = fuse_templates.TEMPLATES[kind](name, options)
        except Exception as exc:
            print(f"  [GEN FAIL] {kind:18s}: {exc}")
            continue
        path = os.path.join(fuses_dir, f"{name}.fuse")
        with open(path, "w", encoding="utf-8") as f:
            f.write(source)
        installed.append((kind, name, path))
        print(f"  [OK]       {kind:18s}: {name}.fuse")

    if not installed:
        print("ABORT: nothing installed.")
        sys.exit(1)

    results = []
    project_created = False
    pm = None

    try:
        print("\n=== Launching Resolve ===")
        if sys.platform != "darwin":
            print("This harness only supports macOS launch.")
            sys.exit(1)
        subprocess.Popen(["open", "/Applications/DaVinci Resolve/DaVinci Resolve.app"])

        handle = None
        for i in range(60):
            time.sleep(2)
            cand = dvr_script.scriptapp("Resolve")
            if cand is not None:
                try:
                    if cand.GetVersion():
                        handle = cand
                        print(f"  Connected after {(i+1)*2}s: "
                              f"{handle.GetProductName()} {handle.GetVersionString()}")
                        break
                except Exception:
                    continue
        if handle is None:
            print("ABORT: Resolve did not respond within 120s")
            sys.exit(1)

        # Build a disposable project + timeline + Fusion-composition clip.
        # A Fusion-composition timeline item has a real per-clip comp that
        # accepts AddTool. No source media is required.
        print("\n=== Setting up disposable project ===")
        pm = handle.GetProjectManager()
        project_name = "McpLiveSmoke_v25"
        # Delete any leftover project from a prior failed run
        try:
            pm.DeleteProject(project_name)
        except Exception:
            pass
        project = pm.CreateProject(project_name)
        if project is None:
            print("ABORT: CreateProject returned None")
            sys.exit(1)
        project_created = True
        print(f"  Project: {project.GetName()}")

        mp = project.GetMediaPool()
        timeline = mp.CreateEmptyTimeline("McpSmokeTimeline")
        if timeline is None:
            print("ABORT: CreateEmptyTimeline returned None")
            sys.exit(1)
        print(f"  Timeline: {timeline.GetName()}")

        # Insert a Fusion composition (gives us a timeline item with a
        # real per-clip comp).
        print("  Inserting Fusion composition into timeline...")
        item = timeline.InsertFusionCompositionIntoTimeline()
        if item is None:
            print("  WARN: InsertFusionCompositionIntoTimeline returned None — "
                  "will fall back to GetCurrentComp")

        # Switch to Fusion page so the per-clip comp activates.
        handle.OpenPage("fusion")
        time.sleep(1)

        fusion = handle.Fusion()
        if fusion is None:
            print("ABORT: handle.Fusion() returned None")
            sys.exit(1)
        comp = fusion.GetCurrentComp()
        if comp is None:
            print("ABORT: GetCurrentComp returned None")
            sys.exit(1)

        comp_attrs = comp.GetAttrs() or {}
        print(f"  Comp: {comp_attrs.get('COMPS_Name', '?')}")

        # Allow Fusion's tool registry a moment to finish indexing Fuses
        time.sleep(2)

        # Test 1: built-in baseline. If this fails, we have a context issue.
        print("\n=== Built-in baseline ===")
        bg = _add_tool(comp, "Background")
        if bg is None:
            print("  [FAIL] AddTool('Background') returned None — context issue")
            print("         Aborting Fuse tests; comp does not accept tools.")
            return
        print(f"  [OK]   Background -> {bg.GetAttrs().get('TOOLS_RegID', '?')}")
        bg.Delete()

        # Test 2: each generated Fuse
        print("\n=== Instantiating generated Fuses ===")
        for kind, name, _ in installed:
            if kind == "modifier":
                results.append((kind, name, "SKIP",
                                "Modifier — flow AddTool doesn't apply"))
                continue
            try:
                t = _add_tool(comp, name)
                if t is None:
                    results.append((kind, name, "FAIL",
                                    "AddTool returned None — class not registered"))
                else:
                    attrs = t.GetAttrs() or {}
                    results.append((kind, name, "OK",
                                    f"created {attrs.get('TOOLS_RegID', '?')}"))
                    try:
                        t.Delete()
                    except Exception:
                        pass
            except Exception as e:
                results.append((kind, name, "ERR", str(e)))

        print()
        for kind, name, status, msg in results:
            print(f"  [{status:4s}] {kind:18s} {name:30s} {msg}")

    finally:
        # Cleanup installed Fuses
        print("\n=== Cleanup ===")
        for kind, name, path in installed:
            try:
                os.unlink(path)
                print(f"  removed: {os.path.basename(path)}")
            except OSError:
                pass

        # Cleanup disposable project
        if project_created and pm is not None and not args.keep_open:
            try:
                pm.CloseProject(pm.GetCurrentProject())
                pm.DeleteProject("McpLiveSmoke_v25")
                print("  removed: disposable project")
            except Exception:
                pass

        if not args.keep_open:
            print("  Quitting Resolve...")
            _quit_resolve()

    failed = [r for r in results if r[2] in ("FAIL", "ERR")]
    if failed:
        print(f"\n=== {len(failed)} FAILURE(S) ===")
        sys.exit(1)
    elif results:
        passed = sum(1 for r in results if r[2] == "OK")
        skipped = sum(1 for r in results if r[2] == "SKIP")
        print(f"\n=== PASS: {passed} OK, {skipped} SKIP ===")
    else:
        print("\n=== ABORTED before any Fuse was tested ===")
        sys.exit(1)


if __name__ == "__main__":
    main()
