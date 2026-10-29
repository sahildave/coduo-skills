#!/bin/bash
# Compile macdrag (and droptarget) into the cache dir; prints the bin dir.
# Rebuilds only when a source is newer than its binary. Needs swiftc (Xcode or CLT).
set -euo pipefail
src="$(cd "$(dirname "$0")" && pwd)"
bin="${MACDRAG_CACHE:-$HOME/Library/Caches/coduo-mac-drag}/bin"
mkdir -p "$bin"
for name in macdrag droptarget; do
  if [ ! -x "$bin/$name" ] || [ "$src/$name.swift" -nt "$bin/$name" ]; then
    swiftc -O "$src/$name.swift" -o "$bin/$name" >&2
  fi
done
echo "$bin"
