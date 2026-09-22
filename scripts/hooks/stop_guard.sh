#!/usr/bin/env bash
# Claude Code "Stop" hook (configured in .claude/settings.json).
# When code changed, run scripts/check.py; if it fails, block the stop (exit 2) so the AI fixes it.
cd "$(dirname "${BASH_SOURCE[0]}")/../.." || exit 0

if [ -x ".venv/Scripts/python.exe" ]; then PY=".venv/Scripts/python.exe"
elif [ -x ".venv/bin/python" ]; then PY=".venv/bin/python"
else exit 0; fi   # environment not created yet: nothing to check

# Avoid infinite loops: if we already blocked once in this stop cycle, let it stop.
if "$PY" -c "import json,sys; sys.exit(0 if json.load(sys.stdin).get('stop_hook_active') else 1)" 2>/dev/null; then
  exit 0
fi

# Only check when Python code changed.
if [ -z "$(git status --porcelain -- backend frontend scripts tests conftest.py 2>/dev/null)" ]; then
  exit 0
fi

OUTPUT="$("$PY" scripts/check.py 2>&1)"
if [ $? -ne 0 ]; then
  echo "$OUTPUT" | tail -n 60 >&2
  echo "" >&2
  echo "scripts/check.py FAILED. Fix the problems above following docs/rules/ before finishing." >&2
  exit 2
fi
exit 0
