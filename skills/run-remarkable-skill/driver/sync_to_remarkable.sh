#!/bin/bash
# Upload every .md file in a directory to reMarkable Cloud as PDF, wirelessly.
# Pipeline: pandoc (MD->HTML) -> headless Chrome (HTML->PDF) -> rmapi put.
#
# Usage: sync_to_remarkable.sh <src_dir_with_md_files> <remote_folder> [work_dir]
set -euo pipefail

SRC_DIR="${1:?usage: sync_to_remarkable.sh <src_dir> <remote_folder> [work_dir]}"
RM_FOLDER="${2:?usage: sync_to_remarkable.sh <src_dir> <remote_folder> [work_dir]}"
WORK_DIR="${3:-$(mktemp -d)}"
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NOTES_STYLE="$SCRIPT_DIR/notes-style.html"

mkdir -p "$WORK_DIR"
rmapi mkdir "$RM_FOLDER" >/dev/null 2>&1 || true

count=0
for md in "$SRC_DIR"/*.md; do
  [ -e "$md" ] || continue
  base=$(basename "$md" .md)
  html="$WORK_DIR/$base.html"
  pdf="$WORK_DIR/$base.pdf"

  pandoc "$md" -s -o "$html" --metadata title="$base" --include-in-header="$NOTES_STYLE"
  "$CHROME" --headless --disable-gpu --no-pdf-header-footer \
    --print-to-pdf="$pdf" "file://$html" 2>/dev/null

  echo "uploading $base..."
  rmapi put "$pdf" "$RM_FOLDER"
  count=$((count + 1))
done

echo "done: $count files uploaded to $RM_FOLDER"
