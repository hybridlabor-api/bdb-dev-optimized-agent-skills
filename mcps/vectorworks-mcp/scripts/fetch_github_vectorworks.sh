#!/usr/bin/env bash
set -euo pipefail

# Clone/update selected Vectorworks repos into:
#   ${DATA_DIR:-data}/github/vectorworks/<repo>
#
# Optional env:
#   DATA_DIR  Base data dir (default: data)
#   REPOS     Space- or comma-separated owner/repo list
#             Default:
#               Vectorworks/developer-scripting \
#               Vectorworks/developer-sdk \
#               Vectorworks/developer-worksheets

DATA_DIR=${DATA_DIR:-data}
BASE_DIR="$DATA_DIR/github/vectorworks"
mkdir -p "$BASE_DIR"

DEFAULT_REPOS=(
  "Vectorworks/developer-scripting"
  "Vectorworks/developer-sdk"
  "Vectorworks/developer-worksheets"
)

if [[ -n "${REPOS:-}" ]]; then
  # allow comma or space separated
  IFS=' ' read -r -a REPOS_LIST <<< "$(echo "$REPOS" | tr ',' ' ')"
else
  REPOS_LIST=("${DEFAULT_REPOS[@]}")
fi

echo "[info] Syncing ${#REPOS_LIST[@]} repositories"
for full in "${REPOS_LIST[@]}"; do
  owner="${full%%/*}"
  repo="${full##*/}"
  url="https://github.com/$full.git"
  dest="$BASE_DIR/$repo"

  if [[ -d "$dest" && ! -d "$dest/.git" ]]; then
    echo "[warn] $dest exists but is not a git repo. Skipped." >&2
    continue
  fi

  if [[ -d "$dest/.git" ]]; then
    echo "[update] $full"
    default_branch=$(git -C "$dest" remote show origin | awk '/HEAD branch/ {print $NF}')
    # Ensure we are on the default branch
    current_branch=$(git -C "$dest" rev-parse --abbrev-ref HEAD || echo "")
    if [[ -n "$default_branch" && "$current_branch" != "$default_branch" ]]; then
      git -C "$dest" checkout -B "$default_branch" --track "origin/$default_branch" 2>/dev/null || \
      git -C "$dest" checkout "$default_branch" 2>/dev/null || true
    fi

    if [[ "${UPDATE_MODE:-pull}" == "pull" ]]; then
      # Prefer fast-forward pull with shallow fetch for speed
      if [[ -n "$default_branch" ]]; then
        git -C "$dest" pull --ff-only --depth=1 --prune origin "$default_branch" || {
          echo "[warn] pull failed; falling back to fetch+reset" >&2
          git -C "$dest" fetch --force --depth=1 origin "$default_branch"
          git -C "$dest" reset --hard "origin/$default_branch"
        }
      else
        git -C "$dest" pull --ff-only --depth=1 --prune origin || {
          echo "[warn] pull failed; falling back to fetch+reset (HEAD)" >&2
          git -C "$dest" fetch --force --depth=1 origin
          git -C "$dest" reset --hard "origin/HEAD"
        }
      fi
    else
      # Clean, deterministic sync (discard local changes)
      if [[ -n "$default_branch" ]]; then
        git -C "$dest" fetch --force --depth=1 origin "$default_branch"
        git -C "$dest" reset --hard "origin/$default_branch"
      else
        git -C "$dest" fetch --force --depth=1 origin
        git -C "$dest" reset --hard "origin/HEAD"
      fi
    fi
  else
    echo "[clone] $full -> $dest"
    git clone --depth=1 "$url" "$dest"
  fi
done

echo "[done] Repositories synced under: $BASE_DIR"
