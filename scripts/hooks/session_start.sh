#!/usr/bin/env bash
# Claude Code "SessionStart" hook (configured in .claude/settings.json).
# Whatever it prints is added to the AI's context at the start of every session: the workflow gate,
# the 3-step flow and the state of every business document. Keep it short and factual.
set -u
cd "$(dirname "${BASH_SOURCE[0]}")/../.." || exit 0

echo "[TC-VIBE-CODING] Framework for internal Streamlit apps built for non-programmers (Vietnamese users)."
echo "MANDATORY: read CLAUDE.md, docs/README.md, docs/rules/*.md and docs/capabilities.md before your first answer,"
echo "and never promise a capability that docs/capabilities.md does not list."
echo "The 3-step flow (the ONLY allowed path; each prompt file is pasted by the user):"
echo "  1. docs/prompt/00-discovery.md         talk with the user about the business (writes only docs/business/_sources/)"
echo "  2. docs/prompt/01-business-analysis.md write docs/business/<key>.md and get it confirmed"
echo "  3. docs/prompt/02-implement-feature.md implement backend + UI (the only step that may write code)"

if [ -f ".gate-unlock" ]; then
  echo "GATE: UNLOCKED for implementation -> $(tr -d '\r\n' < .gate-unlock)"
else
  echo "GATE: LOCKED. Writing code, tests, scripts or scaffolding a feature is FORBIDDEN in this session until the user"
  echo "      pastes docs/prompt/02-implement-feature.md (key TC-UNLOCK-IMPLEMENT) for a document whose Status is"
  echo "      'Ready for implementation'. A PreToolUse hook refuses such writes. Discovery and analysis are allowed."
fi

echo "Business documents:"
found=0
for file in docs/business/*.md; do
  case "$file" in *_TEMPLATE.md | *README.md) continue ;; esac
  [ -f "$file" ] || continue
  found=1
  key="$(basename "$file" .md)"
  status="$(grep -m1 '^| Status' "$file" | sed -E 's/^\|[^|]*\|[[:space:]]*(.*[^[:space:]])[[:space:]]*\|.*/\1/' | cut -c1-60)"
  if [ -d "backend/features/$key" ]; then code="code: yes"; else code="code: no"; fi
  echo "  - $key | Status: ${status:-?} | $code"
done
if [ "$found" = "0" ]; then echo "  (none yet - start with docs/prompt/00-discovery.md)"; fi
exit 0
