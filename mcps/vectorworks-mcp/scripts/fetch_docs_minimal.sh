#!/usr/bin/env bash
set -euo pipefail

# Minimal, ingestion-ready docs fetcher (md/html only)

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DATA_DIR="${ROOT}/data"
mkdir -p "${DATA_DIR}"

echo "==> Clone: Vectorworks developer-scripting (GitHub)"
# Official scripting landing/how-to content (markdown/html)
# https://github.com/Vectorworks/developer-scripting
if [ ! -d "${DATA_DIR}/vw-dev-scripting" ]; then
  git clone --depth=1 https://github.com/Vectorworks/developer-scripting "${DATA_DIR}/vw-dev-scripting"
else
  git -C "${DATA_DIR}/vw-dev-scripting" pull --ff-only
fi

echo "==> Fetch: App Help (core scripting pages 2022/2023/2024)"
APP_HELP="${DATA_DIR}/vw-app-help"
mkdir -p "${APP_HELP}"

UA_DEFAULT="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0 Safari/537.36"
UA="${UA:-$UA_DEFAULT}"

fetch() {
  local url="$1"
  local out="$2"
  echo "fetch ${url} -> ${out}"
  curl -fsSL -H "User-Agent: ${UA}" "$url" -o "$out"
}

fetch_optional() {
  local url="$1"
  local out="$2"
  echo "fetch(optional) ${url} -> ${out}"
  if ! curl -fsSL -H "User-Agent: ${UA}" "$url" -o "$out"; then
    echo "WARN: Failed to fetch optional resource: ${url} (skipped)" >&2
  fi
}

# 2022 Scripting top
fetch "https://app-help.vectorworks.net/2022/eng/VW2022_Guide/Scripts/Scripting.htm" \
  "${APP_HELP}/VW2022_Scripting.htm"

# 2022 Script Editor / palettes
fetch "https://app-help.vectorworks.net/2022/eng/VW2022_Guide/Scripts/Creating_and_editing_script_palettes_and_scripts.htm" \
  "${APP_HELP}/VW2022_ScriptEditor.htm"

# 2022 plug-in script specification
fetch "https://app-help.vectorworks.net/2022/eng/VW2022_Guide/Scripts/Specifying_the_plug-in_script.htm" \
  "${APP_HELP}/VW2022_PluginScript.htm"

# 2023 Creating scripted plug-ins (explicit practical page)
fetch "https://app-help.vectorworks.net/2023/eng/VW2023_Guide/Scripts/Creating_scripted%20plug-ins.htm?agt=index" \
  "${APP_HELP}/VW2023_CreatingScriptedPlugins.htm"

# 2024 Running scripts (how to run)
fetch "https://app-help.vectorworks.net/2024/eng/VW2024_Guide/Scripts/Running_scripts.htm" \
  "${APP_HELP}/VW2024_RunningScripts.htm"

echo "==> Fetch: VectorScript reference (JP index + example page)"
JP_REF="${DATA_DIR}/vw-jp-ref"
mkdir -p "${JP_REF}"

# Function index (Japanese)
fetch "https://www.vectorworks.co.jp/develop/ScriptReference/ScriptFunctionReference.html" \
  "${JP_REF}/ScriptFunctionReference.html"

# Example: Objects/Symbols API page
fetch "https://www.vectorworks.co.jp/develop/ScriptReference/Pages/ObjectsSymbols.html" \
  "${JP_REF}/ObjectsSymbols.html"

echo "==> Fetch: Developer Wiki category page (EN)"
DEVWIKI="${DATA_DIR}/vw-devwiki"
mkdir -p "${DEVWIKI}"

# Category index sample page (HTML). Note: PDF not fetched (not ingested).
# Some endpoints may return 403 to generic clients; treat as optional.
fetch_optional "https://developer.vectorworks.net/index.php?pagefrom=SetDocDrpShadwByCls%0AVS%3ASetDocDrpShadwByCls&subcatfrom=VS+Function+Reference%3ADimensions&title=Category%3AVS_Function_Reference&until=VS+Function+Reference%3ADimensions" \
  "${DEVWIKI}/VS_Function_Reference_category.html"

echo "==> Done. Saved under: ${DATA_DIR}"
echo "Files ready for ingestion: .md/.html under ${DATA_DIR}"
