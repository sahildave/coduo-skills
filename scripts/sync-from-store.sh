#!/bin/bash
# Copy every skill already in plugins/coduo/skills from the editor's store
# (~/.agents/skills). The store is where these skills are edited; this repo is
# where they are published. Run after an edit, review the diff, commit, push.
set -euo pipefail
cd "$(dirname "$0")/.."
DEST=plugins/coduo/skills
for d in "$DEST"/*/; do
  n=$(basename "$d")
  src="$HOME/.agents/skills/$n"
  if [ -d "$src" ] && [ ! -L "$src" ]; then
    rm -rf "$d" && cp -R "$src" "$DEST/$n" && echo "synced $n"
  else
    echo "WARN $n: not a folder in the store (skipped)"
  fi
done
find "$DEST" -name .DS_Store -delete
# Personal names and private repos must not reach this public repo.
if grep -r -n -I -i -E 'sahildave|indhuja|\bSahil\b|/Users/[a-z]+/|Coduo Brain' "$DEST"; then
  echo "ERROR: personal reference above; scrub it in the store, then sync again." >&2
  exit 1
fi
