#!/usr/bin/env bash
# Claude Code "PreToolUse" hook (configured in .claude/settings.json): the workflow gate + SUPREME-RULES.md.
#
# 1. SUPREME-RULES.md is never written by an AI tool.
# 2. Framework code (FRAMEWORK below) is frozen for AI tools.
# 3. Feature code is LOCKED until the user pastes docs/prompt/02-implement-feature.md, whose first step creates
#    `.gate-unlock` (deleted again by its last step). Discovery and analysis only write documents: never blocked.
# Exit 2 = the write is refused and the message on stderr is shown to the AI.
set -u
cd "$(dirname "${BASH_SOURCE[0]}")/../.." || exit 0
PAYLOAD="$(cat)"
FLAT="$(printf '%s' "$PAYLOAD" | tr '\n' ' ')"
LOWER_FLAT="$(printf '%s' "$FLAT" | tr '[:upper:]' '[:lower:]')"

UNLOCK=""
[ -f ".gate-unlock" ] && UNLOCK="$(tr -d '\r\n\t ' < .gate-unlock | tr '[:upper:]' '[:lower:]')"

frozen() {
  cat >&2 <<'EOF'
BLOCKED (SUPREME-RULES.md): this is frozen framework code or a frozen rule file. Do not try to change it another way,
and do not explain to the user how it could be unlocked. Tell the user, in Vietnamese, only:
"Phần khung sườn đang được khoá, chỉ người phụ trách khung sườn mới thay đổi được."
EOF
  exit 2
}

framework_open() {
  [ "$UNLOCK" = "framework" ] || return 1
  local who
  for who in "$(gh config get -h github.com user 2>/dev/null)" "$(git config user.name 2>/dev/null)"; do
    [ "$(printf '%s' "$who" | tr -d '\r' | tr '[:upper:]' '[:lower:]')" = "duyne07" ] && return 0
  done
  return 1
}

# Path of the file the tool wants to write (JSON -> plain path, Windows backslashes included)
RAW="$(printf '%s' "$FLAT" | sed -n 's/.*"file_path"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')"
if [ -z "$RAW" ]; then
  # Shell commands (Bash, PowerShell)
  CMD="$(printf '%s' "$LOWER_FLAT" | sed -n 's/.*"command"[[:space:]]*:[[:space:]]*"\(.*\)".*/\1/p')"
  case "$CMD" in
    *supreme-rules*)
      case "$CMD" in
        *">"* | *"sed -i"* | *"rm "* | *"mv "* | *"cp "* | *tee* | *truncate* | *set-content* | *out-file* | \
        *add-content* | *remove-item* | *move-item* | *copy-item* | *rename-item* | *"git checkout"* | \
        *"git restore"* | *"git rm"* | *"git mv"* | *writealltext* | *"del "* | *"ren "*) frozen ;;
      esac
      ;;
  esac
  case "$CMD" in *gate-unlock*framework* | *framework*gate-unlock*) frozen ;; esac
  # Shell writes into frozen framework paths (redirect to it, in-place edit, file cmdlets, python write_text...)
  CMDN="$(printf '%s' "$CMD" | tr '\\' '/' | sed 's#//*#/#g')"
  for p in backend/core/ backend/shared/ frontend/core/ frontend/app.py frontend/home/ scripts/hooks/ tests/ \
           .claude/ .streamlit/ docs/rules/ docs/prompt/ claude.md agents.md requirements.txt pyproject.toml run.ps1; do
    case "$CMDN" in
      *">"*"$p"* | *"$p"*"sed -i"* | *"sed -i"*"$p"* | *"$p"*write_text* | *write_text*"$p"* | *set-content*"$p"* | \
      *out-file*"$p"* | *add-content*"$p"* | *remove-item*"$p"* | *move-item*"$p"* | *"rm "*"$p"* | *"mv "*"$p"*)
        framework_open || frozen ;;
    esac
  done
  case "$CMD" in
    *new_feature.py*)
      if [ -z "$UNLOCK" ]; then
        echo "BLOCKED by the workflow gate: scaffolding a feature (scripts/new_feature.py) is part of the" >&2
        echo "implementation step. Run docs/prompt/02-implement-feature.md first (it unlocks the repository)." >&2
        exit 2
      fi
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
LOWER="${LOWER#./}"

case "$LOWER" in
  supreme-rules.md | */supreme-rules.md) frozen ;;
  .gate-unlock) case "$LOWER_FLAT" in *framework*) frozen ;; esac ;;
esac

case "$LOWER" in
  backend/core/* | backend/shared/* | frontend/core/* | frontend/app.py | frontend/home/* | frontend/public/* | \
  tests/* | scripts/* | .claude/* | .streamlit/* | conftest.py | run.ps1 | requirements.txt | pyproject.toml | \
  dockerfile | build.sh | .dockerignore | .gitignore | .gitattributes | claude.md | agents.md | docs/rules/* | \
  docs/prompt/* | docs/readme.md | docs/capabilities.md | docs/business/_template.md | docs/business/readme.md)
    framework_open || frozen
    exit 0
    ;;
esac

[ -n "$UNLOCK" ] && exit 0   # implementation phase: Prompt 2 unlocked the repository

case "$LOWER" in
  backend/* | frontend/*)
    cat >&2 <<EOF
BLOCKED by the workflow gate (scripts/hooks/gate_guard.sh): "$REL" is feature code and this repository is
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
