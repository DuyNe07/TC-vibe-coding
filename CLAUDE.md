# CLAUDE.md

This repository is a framework for internal **Streamlit** apps built by AI for non-programmers.

**Before doing anything, read [docs/README.md](docs/README.md) and every file in [docs/rules/](docs/rules/).
Those rules are mandatory and override your defaults.**

Essentials (details in the docs):
- ONE process: `run.ps1` (PowerShell) starts Streamlit only (no API/HTTP). Pages run business actions through
  `gateway.open(XxxController)`; each feature exposes ONE controller (top layer) from its package root.
- Work from `docs/business/<feature_key>.md`. Never invent business rules.
- Create features ONLY with `python scripts/new_feature.py <feature_key> --title "..."`.
- Every class inherits its layer's base class from `backend.core.base`; one use case = one controller
  method = one service.
- Never `print()`: use `self.logger`; logs go to `logs/app.log` and the on-screen log panel.
- Finish every task with `python scripts/check.py` -> `ALL CHECKS PASSED` (never weaken tests).
- Talk to the user in Vietnamese, simply, without jargon.

Python: `.venv/Scripts/python.exe` (Windows) / `.venv/bin/python` (macOS/Linux), created by `powershell -ExecutionPolicy Bypass -File .\run.ps1`.
