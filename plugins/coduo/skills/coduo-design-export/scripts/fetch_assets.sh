#!/usr/bin/env bash
# Vendor every Paper file-asset the JSX references into <boards-dir>/assets/.
#
#   fetch_assets.sh <jsx-dir> <boards-dir>
#
# Paper serves file-assets publicly (no session needed), so a plain curl works.
# Prints the URL prefix to pass to jsx2html.py --assets-url-prefix.
set -euo pipefail
jsx_dir=$1; boards=$2
mkdir -p "$boards/assets"
urls=$(grep -rhoE 'https://app\.paper\.design/file-assets/[A-Z0-9]+/[A-Z0-9]+\.[a-z0-9]+' "$jsx_dir" | sort -u || true)
[ -z "$urls" ] && { echo "no file-assets referenced"; exit 0; }
for u in $urls; do
  f=${u##*/}
  [ -f "$boards/assets/$f" ] || curl -sSf -o "$boards/assets/$f" "$u"
  printf '%s  %s\n' "$(file -b "$boards/assets/$f" | cut -c1-40)" "$f"
done
echo "prefix: $(echo "$urls" | head -1 | sed -E 's|/[A-Z0-9]+\.[a-z0-9]+$|/|')"
