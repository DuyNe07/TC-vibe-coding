# AGENTS.md

Instructions for AI coding agents (Codex, Cursor, Copilot, Gemini...).
They are identical to [CLAUDE.md](CLAUDE.md): read it first, then [docs/README.md](docs/README.md), every file in
[docs/rules/](docs/rules/) and [docs/capabilities.md](docs/capabilities.md), and follow them exactly.

**The workflow gate applies to you too** (full table in CLAUDE.md): this repository is locked for writing by default.
Analysing the code is always allowed; writing code is allowed ONLY after the user pastes
[docs/prompt/02-implement-feature.md](docs/prompt/02-implement-feature.md) for a business document whose `Status` is
`Ready for implementation`. Before that, the only allowed path is
[docs/prompt/00-discovery.md](docs/prompt/00-discovery.md) (talk, write a discovery note) then
[docs/prompt/01-business-analysis.md](docs/prompt/01-business-analysis.md) (write the business document).

Verify every task with `python scripts/check.py` (must print `ALL CHECKS PASSED`).
