"""The workflow gate must stay in place: hooks installed, and code writes refused while the repo is locked."""

import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HOOKS = ROOT / "scripts" / "hooks"
GUARD = HOOKS / "gate_guard.sh"
UNLOCK_FILE = ROOT / ".gate-unlock"
PROTECTED = ("backend/", "frontend/", "tests/", "scripts/", "conftest.py", "run.ps1", "requirements.txt")


def test_hook_scripts_exist() -> None:
    for name in ("gate_guard.sh", "session_start.sh", "stop_guard.sh"):
        assert (HOOKS / name).is_file(), f"missing hook script {name}"


def test_claude_settings_register_the_gate() -> None:
    hooks = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))["hooks"]
    commands = {
        event: " ".join(h["command"] for group in entries for h in group["hooks"]) for event, entries in hooks.items()
    }
    assert "session_start.sh" in commands["SessionStart"]
    assert "gate_guard.sh" in commands["PreToolUse"]
    assert "stop_guard.sh" in commands["Stop"]
    matchers = [group.get("matcher", "") for group in hooks["PreToolUse"]]
    assert any("Write" in m and "Edit" in m for m in matchers), "the guard must cover Write and Edit"


def test_guard_protects_code_paths() -> None:
    text = GUARD.read_text(encoding="utf-8")
    for path in PROTECTED:
        assert path.rstrip("/") in text, f"gate_guard.sh no longer protects {path}"
    assert "new_feature.py" in text, "scaffolding must be blocked while locked"


def _run_guard(file_path: str) -> int:
    payload = json.dumps({"tool_name": "Write", "tool_input": {"file_path": file_path}})
    result = subprocess.run(
        [shutil.which("bash") or "bash", str(GUARD)], input=payload, capture_output=True, text=True, cwd=ROOT
    )
    return result.returncode


def test_guard_refuses_code_and_allows_documents_when_locked() -> None:
    if shutil.which("bash") is None or UNLOCK_FILE.exists():  # unlocked: Prompt 2 is running
        return
    assert _run_guard("backend/features/demo/models/item.py") == 2
    assert _run_guard(str(ROOT / "frontend" / "features" / "demo" / "pages" / "list_page.py")) == 2
    assert _run_guard("docs/business/demo.md") == 0
    assert _run_guard("docs/business/_sources/demo-discovery.md") == 0
