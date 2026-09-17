#!/usr/bin/env bash
# Pull app sandbox data via adb root.
# Usage: pull_app_data.sh <package> <dest_dir>
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "usage: $0 <package> <dest_dir>" >&2
  exit 1
fi

PKG="$1"
DEST="$2"
mkdir -p "$DEST"

if ! adb shell id | grep -q uid=0; then
  adb root >/dev/null || true
  sleep 1
fi

if ! adb shell id | grep -q uid=0; then
  echo "error: adb not root; cannot read /data/data/$PKG" >&2
  exit 2
fi

REMOTE="/data/local/tmp/${PKG}-pull"
adb shell "rm -rf '$REMOTE' && mkdir -p '$REMOTE' && \
  cp -a /data/data/$PKG/shared_prefs '$REMOTE/' 2>/dev/null; \
  cp -a /data/data/$PKG/files '$REMOTE/' 2>/dev/null; \
  cp -a /data/data/$PKG/databases '$REMOTE/' 2>/dev/null; \
  cp -a /data/data/$PKG/app_webview '$REMOTE/' 2>/dev/null; \
  chmod -R 644 '$REMOTE' 2>/dev/null; chmod -R a+X '$REMOTE'"

adb pull "$REMOTE" "$DEST/" >/dev/null
# flatten one extra dir level if adb created it
if [[ -d "$DEST/${PKG}-pull" ]]; then
  mv "$DEST/${PKG}-pull"/* "$DEST/" 2>/dev/null || true
  rmdir "$DEST/${PKG}-pull" 2>/dev/null || true
fi

echo "pulled -> $DEST"
ls -la "$DEST" || true
