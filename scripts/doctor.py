"""End-to-end self-check: quality gate + the app really starts + errors found in the log.

Used by the AI repair loop (docs/rules/10-self-repair.md) and by anybody who wants one command that answers
"is the app healthy?".

Usage:
    python scripts/doctor.py                # checks + start the app + health check + log errors
    python scripts/doctor.py --skip-checks  # skip scripts/check.py (faster while debugging the UI)
    python scripts/doctor.py --port 8610    # first port to try (the next free one is used if busy)
"""

import argparse
import contextlib
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG_FILE = ROOT / "logs" / "app.log"
HEALTH_TIMEOUT_SECONDS = 90


def _free_port(first: int) -> int:
    for port in range(first, first + 20):
        with socket.socket() as probe:
            if probe.connect_ex(("127.0.0.1", port)) != 0:
                return port
    return first


def _wait_for_health(port: int, process: subprocess.Popen[bytes]) -> bool:
    deadline = time.monotonic() + HEALTH_TIMEOUT_SECONDS
    url = f"http://127.0.0.1:{port}/_stcore/health"
    while time.monotonic() < deadline:
        if process.poll() is not None:
            return False
        try:
            with urllib.request.urlopen(url, timeout=3) as response:  # noqa: S310 - localhost only
                if response.read().strip() == b"ok":
                    return True
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError):
            time.sleep(1.5)
    return False


def _log_problems(since_size: int) -> list[str]:
    if not LOG_FILE.exists():
        return []
    with LOG_FILE.open("r", encoding="utf-8", errors="replace") as handle:
        handle.seek(since_size)
        new_lines = handle.readlines()
    return [line.rstrip() for line in new_lines if " ERROR " in line or " WARNING " in line][-30:]


def run_feature_check() -> tuple[bool, list[str]]:
    """Load every feature manifest and page class, exactly as the Home page does."""
    sys.path.insert(0, str(ROOT))
    from frontend.core.registry import FeatureRegistry

    print("\n=== Features load (manifest + pages) ===", flush=True)
    registry = FeatureRegistry.discover()
    problems = [f"feature '{error.feature_key}' does not load: {error.message}" for error in registry.errors]
    names = ", ".join(manifest.key for manifest in registry.features) or "(none)"
    print(f"--> {'OK' if not problems else 'FAILED'} - loaded: {names}", flush=True)
    return not problems, problems


def run_app_check(port: int) -> tuple[bool, list[str]]:
    """Start the app, wait for its health endpoint, stop it. Returns (ok, problems)."""
    log_size = LOG_FILE.stat().st_size if LOG_FILE.exists() else 0
    handle, output_name = tempfile.mkstemp(prefix="tc-doctor-", suffix=".log")
    os.close(handle)  # Windows: keep no extra handle on the file
    output = Path(output_name)
    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "frontend/app.py",
        "--server.port",
        str(port),
        "--server.headless",
        "true",
    ]
    print(f"\n=== App check (port {port}) ===", flush=True)
    with output.open("wb") as sink:
        process = subprocess.Popen(  # noqa: S603 - fixed command
            command,
            cwd=ROOT,
            stdout=sink,
            stderr=subprocess.STDOUT,
            env={**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"},
        )
        try:
            healthy = _wait_for_health(port, process)
        finally:
            process.terminate()
            try:
                process.wait(timeout=20)
            except subprocess.TimeoutExpired:
                process.kill()
    problems = _log_problems(log_size)
    if not healthy:
        tail = output.read_text(encoding="utf-8", errors="replace").splitlines()[-25:]
        problems = [*tail, *problems]
    with contextlib.suppress(OSError):  # Windows may still hold the file: leaving it behind is harmless
        output.unlink(missing_ok=True)
    print(f"--> {'OK - the app answered /_stcore/health' if healthy else 'FAILED - the app did not start'}", flush=True)
    return healthy, problems


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-checks", action="store_true", help="do not run scripts/check.py")
    parser.add_argument("--port", type=int, default=8599, help="first port to try (default 8599)")
    args = parser.parse_args()

    checks_ok = True
    if not args.skip_checks:
        result = subprocess.run(  # noqa: S603 - fixed command
            [sys.executable, "scripts/check.py"],
            cwd=ROOT,
            env={**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"},
        )
        checks_ok = result.returncode == 0

    features_ok, problems = run_feature_check()
    app_ok, app_problems = run_app_check(_free_port(args.port))
    problems += app_problems

    if problems:
        print("\n=== Errors / warnings to fix ===")
        for line in problems:
            print(f"  {line}")
    if checks_ok and features_ok and app_ok and not problems:
        print("\nAPP IS HEALTHY")
        return 0
    print("\nAPP IS NOT HEALTHY - fix the causes above (docs/rules/10-self-repair.md), then run this again")
    return 1


if __name__ == "__main__":
    sys.exit(main())
