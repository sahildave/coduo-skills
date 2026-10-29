#!/usr/bin/env bash
# Render a converted board in headless Chrome at device scale 2 and confirm its
# pixel size matches the Paper export, so a conversion bug shows up as a picture
# before anything is committed.
#
#   render_check.sh <board.html> <out.png> [width=393] [height=852]
#
# Compare <out.png> with Paper's own 2x export of the same artboard by eye (Read
# both); the only expected drift is a font the machine lacks, which vendoring the
# TTFs into fonts/ removes.
set -euo pipefail
html=$1; out=$2; w=${3:-393}; h=${4:-852}
CH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
[ -x "$CH" ] || CH=$(command -v chromium || command -v google-chrome || true)
[ -n "$CH" ] || { echo "no Chrome/Chromium found"; exit 2; }
"$CH" --headless=new --disable-gpu --hide-scrollbars --force-device-scale-factor=2 \
  --window-size="$w,$h" --screenshot="$out" "file://$(cd "$(dirname "$html")" && pwd)/$(basename "$html")" 2>/dev/null
got=$(sips -g pixelWidth -g pixelHeight "$out" | awk '/pixel/{printf "%sx", $2}' | sed 's/x$//')
want="$((w*2))x$((h*2))"
[ "$got" = "$want" ] && echo "OK $got $out" || { echo "SIZE MISMATCH want $want got $got"; exit 1; }
