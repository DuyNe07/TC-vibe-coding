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


def _guard(tool_input: dict, tool: str = "Write", env: dict | None = None) -> subprocess.CompletedProcess:
    payload = json.dumps({"tool_name": tool, "tool_input": tool_input})
    return subprocess.run(
        [shutil.which("bash") or "bash", str(GUARD)], input=payload, capture_output=True, text=True, cwd=ROOT, env=env
    )


def _run_guard(file_path: str) -> int:
    return _guard({"file_path": file_path}).returncode


def test_supreme_rules_exist_and_are_never_writable() -> None:
    assert (ROOT / "SUPREME-RULES.md").is_file(), "SUPREME-RULES.md is missing"
    for name in ("CLAUDE.md", "AGENTS.md"):
        assert "SUPREME-RULES.md" in (ROOT / name).read_text(encoding="utf-8"), f"{name} must point to SUPREME-RULES.md"
    assert "SUPREME-RULES.md" in (HOOKS / "session_start.sh").read_text(encoding="utf-8")
    if shutil.which("bash") is None:
        return
    assert _run_guard("SUPREME-RULES.md") == 2, "always refused, locked or not"
    assert _run_guard(str(ROOT / "SUPREME-RULES.md")) == 2
    assert _guard({"command": "Set-Content SUPREME-RULES.md x"}, "PowerShell").returncode == 2
    assert _guard({"command": "sed -i s/a/b/ SUPREME-RULES.md"}, "Bash").returncode == 2


def test_framework_code_is_frozen_for_anyone_else() -> None:
    if shutil.which("bash") is None:
        return
    import os
    import tempfile

    stranger = {**os.environ, "GH_CONFIG_DIR": tempfile.mkdtemp(), "GIT_CONFIG_GLOBAL": os.devnull,
                "GIT_CONFIG_NOSYSTEM": "1", "HOME": tempfile.mkdtemp()}  # fmt: skip
    for path in ("backend/core/db.py", "frontend/core/router.py", "scripts/hooks/gate_guard.sh", "docs/rules/x.md"):
        result = _guard({"file_path": path}, env=stranger)
        assert result.returncode == 2, f"{path} must be frozen"
        assert ".gate-unlock" not in result.stderr, "the refusal never hints how the lock opens"
    assert _guard({"command": "cat x > backend/core/db.py"}, "Bash", env=stranger).returncode == 2
    assert (
        _guard({"command": "python - <<x\nPath('frontend/core/a.py').write_text('')\nx"}, "Bash", stranger).returncode
        == 2
    )
    assert _guard({"command": "python scripts/check.py 2>&1 | tail -5"}, "Bash", env=stranger).returncode == 0
    assert _guard({"file_path": ".gate-unlock", "content": "framework"}).returncode == 2
    assert _guard({"command": "echo framework > .gate-unlock"}, "Bash").returncode == 2


def test_powershell_is_guarded_too() -> None:
    hooks = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))["hooks"]
    assert any("PowerShell" in group.get("matcher", "") for group in hooks["PreToolUse"])


def test_guard_refuses_code_and_allows_documents_when_locked() -> None:
    if shutil.which("bash") is None or UNLOCK_FILE.exists():  # unlocked: Prompt 2 is running
        return
    assert _run_guard("backend/features/demo/models/item.py") == 2
    assert _run_guard(str(ROOT / "frontend" / "features" / "demo" / "pages" / "list_page.py")) == 2
    assert _run_guard("docs/business/demo.md") == 0
    assert _run_guard("docs/business/_sources/demo-discovery.md") == 0


def test_the_workflow_documents_exist_with_their_gate_keys() -> None:
    prompts = ROOT / "docs" / "prompt"
    assert (prompts / "00-discovery.md").is_file(), "Prompt 0.5 (discovery) is missing"
    assert "TC-UNLOCK-ANALYSIS" in (prompts / "01-business-analysis.md").read_text(encoding="utf-8")
    for name in ("02-implement-feature.md", "03-fix-error.md", "04-sync-to-server.md", "05-extend-feature.md"):
        assert "TC-UNLOCK-IMPLEMENT" in (prompts / name).read_text(encoding="utf-8"), f"{name} lost its gate key"
    assert (ROOT / "docs" / "capabilities.md").is_file(), "the capability catalogue is missing"
    assert (ROOT / "docs" / "rules" / "10-self-repair.md").is_file(), "the self-repair rules are missing"
    assert (ROOT / "scripts" / "doctor.py").is_file(), "scripts/doctor.py is missing"
