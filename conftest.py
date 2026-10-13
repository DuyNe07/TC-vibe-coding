"""Global pytest setup: tests never write into the real data/ or logs/ folders, nor into the real database."""

import tempfile
from pathlib import Path

import pytest

from backend.core import db
from backend.core.config import get_settings


def pytest_configure(config: pytest.Config) -> None:
    # Before any logger is created: send test logs to a temporary folder.
    get_settings().log_dir = Path(tempfile.mkdtemp(prefix="tc-test-logs-"))


@pytest.fixture(autouse=True)
def _isolated_data_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(get_settings(), "data_dir", tmp_path / "data")
    # one throw-away SQLite database per test (SqlRepository), never the shared PostgreSQL
    monkeypatch.setattr(get_settings(), "database_url", f"sqlite+aiosqlite:///{(tmp_path / 'test.db').as_posix()}")
    yield
    db.dispose_all()
