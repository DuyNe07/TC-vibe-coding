"""Global pytest setup: tests never write into the real data/ or logs/ folders."""

import tempfile
from pathlib import Path

import pytest

from backend.core.config import get_settings


def pytest_configure(config: pytest.Config) -> None:
    # Before any logger is created: send test logs to a temporary folder.
    get_settings().log_dir = Path(tempfile.mkdtemp(prefix="tc-test-logs-"))


@pytest.fixture(autouse=True)
def _isolated_data_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(get_settings(), "data_dir", tmp_path / "data")
    yield
