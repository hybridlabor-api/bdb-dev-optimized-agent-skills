---
title: Make a Windows-only plugin cross-platform
linkTitle: Windows to cross-platform
weight: 5
author: Callum
editor: SteveF
draft: true
keywords:
  - cross-platform
  - Mac
  - P/Invoke
  - plugin port
---

// https://github.com/mcneel/RhinoVR

If your Rhino plugin currently only runs on Windows, getting it onto Mac is usually a mix of UI work (WPF → Eto) and a long tail of small non-UI Windows-isms: P/Invokes into `user32`/`kernel32`, registry reads, COM interop, `\\`-style paths, `System.Drawing` assumptions, and the like. This page is about the non-UI half; for the UI half see [Convert a WPF UI to Eto](wpf-to-eto).

## The loop

With Rhino MCP loaded, the assistant can:

- Grep the codebase for the usual Windows-only suspects (`DllImport`, `Microsoft.Win32`, `System.Windows.*`, `Marshal`, hard-coded `C:\` paths) and work through them one at a time.
- Replace each with a portable equivalent, usually a RhinoCommon or Eto API, sometimes plain BCL, occasionally a small `RuntimeInformation` switch when there's genuinely no shared path.
- Build, load the `.rhp` into the running Rhino, and run the affected command to confirm the replacement actually works on the target platform.

The "actually run it on Mac" step is what makes this worth doing through the MCP. A lot of Windows-isms compile fine on .NET on Mac and only blow up at runtime when the P/Invoke can't resolve.

## A prompt to start with

{{< prompt >}}
This is a Rhino plugin that only runs on Windows. I want it working on
Mac as well. Find the Windows-specific code (P/Invokes, registry
access, COM interop, `System.Windows.*` references, hard-coded Windows
paths) and replace each with a cross-platform equivalent
(RhinoCommon, Eto, or plain .NET). Work one site at a time, build after
each change, load it into the Rhino I have open and run the affected
command to confirm it still works. Show me the diff before each file
change, and at the end give me a list of anything you couldn't port.
{{< /prompt >}}

If the plugin has a WPF UI, do that port first (or in parallel in a separate session), otherwise the build won't come up on Mac at all and the assistant can't close its loop.

## What to review

- **P/Invoke removals.** A `DllImport` into `user32` usually has a RhinoCommon or Eto equivalent; confirm the replacement has the same behavior, not just the same shape. Things like window activation, cursor position, and clipboard access all have portable APIs but with slightly different semantics.
- **Registry usage.** `Microsoft.Win32.Registry` is Windows-only. Settings should generally move to `PlugIn.Settings` (RhinoCommon) or a file under a portable location like `Rhino.ApplicationSettings`'s data folder. Watch for license/activation state that was stored in the registry. That needs a deliberate decision, not just a reflexive port.
- **File paths.** `Path.Combine` and forward slashes are fine on both platforms; hard-coded `C:\Users\...` or `%APPDATA%` is not. Mac uses `~/Library/Application Support/...` for the equivalent data, and RhinoCommon exposes the right folders directly.
- **`System.Drawing` quirks.** `System.Drawing.Common` works on Mac but some bits (printing, GDI+ specifics) don't. If the plugin does non-trivial image work, prefer Eto's drawing APIs.
- **COM interop.** Office automation, Shell COM objects, anything `Marshal.GetActiveObject`: none of this exists on Mac. These usually need a real redesign, not a port. Flag them and decide per-feature whether to drop, gate, or replace.
- **Conditional compilation.** Some Windows-only features genuinely have no Mac equivalent. `RuntimeInformation.IsOSPlatform(...)` at runtime is usually cleaner than `#if WINDOWS` at compile time, because the same assembly ships to both platforms.
- **The `.csproj`.** Check that nothing pins the build to `win-x64` / `net8.0-windows` unless it has to. The plugin should build as plain `net7.0` / `net8.0` so the same `.rhp` runs on both.

## When the assistant gets stuck

If a feature genuinely has no Mac equivalent (a Windows-only license dongle, an Office automation feature, a driver-level integration), have the assistant gate it behind a runtime platform check and surface it in the "couldn't port" list rather than stubbing silently. A feature that's clearly Windows-only with a polite message is much better than one that appears to work and quietly does nothing.

For anything that compiles on Mac but fails at runtime, ask the assistant to reproduce the failure through the MCP first (running the command, reading the error) before proposing a fix. The MCP is what keeps it honest about which "fixes" actually fix anything.
