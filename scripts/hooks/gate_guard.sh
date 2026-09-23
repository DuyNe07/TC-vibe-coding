#!/usr/bin/env bash
# Claude Code "PreToolUse" hook (configured in .claude/settings.json): the workflow gate.
#
# The repository is LOCKED by default: no code may be written until the user pastes
# docs/prompt/02-implement-feature.md, whose first step creates the unlock file `.gate-unlock`
# (deleted again by its last step). Analysis and discovery only write documents, so they are never blocked.
# Exit 2 = the write is refused and the message on stderr is shown to the AI.
set -u
cd "$(dirname "${BASH_SOURCE[0]}")/../.." || exit 0
PAYLOAD="$(cat)"

[ -f ".gate-unlock" ] && exit 0   # implementation phase: Prompt 2 unlocked the repository

# Path of the file the tool wants to write (JSON -> plain path, Windows backslashes included)
RAW="$(printf '%s' "$PAYLOAD" | tr '\n' ' ' | sed -n 's/.*"file_path"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')"
if [ -z "$RAW" ]; then
  # Shell commands: block only the unmistakable start of an implementation
  CMD="$(printf '%s' "$PAYLOAD" | tr '\n' ' ' | sed -n 's/.*"command"[[:space:]]*:[[:space:]]*"\(.*\)".*/\1/p')"
  case "$CMD" in
    *new_feature.py*)
      echo "BLOCKED by the workflow gate: scaffolding a feature (scripts/new_feature.py) is part of the" >&2
      echo "implementation step. Run docs/prompt/02-implement-feature.md first (it unlocks the repository)." >&2
      exit 2
      ;;
  esac
  exit 0
fi

# Make the path relative to the project folder, case-insensitively
# (tools send "D:\repo\x", "D:/repo/x", "/d/repo/x" or already "x")
REL="$(printf '%s' "$RAW" | tr '\\' '/' | sed 's#//*#/#g')"
LOWER="$(printf '%s' "$REL" | tr '[:upper:]' '[:lower:]')"
PROJECT="$(basename "$(pwd)" | tr '[:upper:]' '[:lower:]')"
case "$LOWER" in *"/$PROJECT/"*) LOWER="${LOWER##*"/$PROJECT/"}"; REL="$LOWER" ;; esac

case "$LOWER" in
  backend/* | frontend/* | tests/* | scripts/* | .claude/* | .streamlit/* | \
  conftest.py | run.ps1 | requirements.txt | pyproject.toml | .gitignore | .gitattributes)
    cat >&2 <<EOF
BLOCKED by the workflow gate (scripts/hooks/gate_guard.sh): "$REL" is framework/feature code and this repository is
LOCKED for writing.

The only allowed path is the 3-step flow (see CLAUDE.md):
  1. docs/prompt/00-discovery.md        understand the business with the user (writes only docs/business/_sources/)
  2. docs/prompt/01-business-analysis.md  write docs/business/<key>.md, confirmed by the user
  3. docs/prompt/02-implement-feature.md  THEN code (it creates the .gate-unlock file first)

Do not create .gate-unlock yourself: it is created only when the user has pasted Prompt 2 and the business document
says "Status: Ready for implementation". Tell the user, in Vietnamese, which of the 3 steps to run now.
EOF
    exit 2
    ;;
esac
exit 0
