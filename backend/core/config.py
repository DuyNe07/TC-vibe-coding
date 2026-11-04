"""Typed application settings loaded from environment variables / .env (prefix ``APP_``)."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Global settings. Access them ONLY through ``get_settings()``."""

    model_config = SettingsConfigDict(env_file=PROJECT_ROOT / ".env", env_prefix="APP_", extra="ignore")

    name: str = "TC Vibe Coding"
    env: str = "local"
    log_level: str = "INFO"
    data_dir: Path = PROJECT_ROOT / "data"
    log_dir: Path = PROJECT_ROOT / "logs"

    # Built-in master account "u-master" (above every administrator): created at start-up when this is set, with this
    # first password (change it on /admin). Empty: no master, administrators open everything as before.
    master_password: str = ""
    session_hours: int = 12  # a login survives page reloads (F5) for this long
    db_cache_seconds: int = 30  # RAM cache of tables / read-only use cases; changes by OTHER processes show after this
    # true until the schema is frozen ("chốt"): repositories create missing tables on first use.
    # false afterwards: only migrations (python scripts/migrate.py, backend/core/migrate.py) create or change tables.
    db_auto_create: bool = True

    # Volume guards (SUPREME-RULES.md): big data must never freeze the app or the browser.
    db_warn_rows: int = 200_000  # a table read with more rows logs a WARNING (it lives in RAM, filtered in Python)
    excel_max_rows: int = 200_000  # ExcelReader refuses bigger sheets with a clear message
    table_max_rows: int = 200_000  # data_table shows at most this many rows (the rest: filter or export)
    select_max_rows: int = 10_000  # data_table(selection=...) cannot be lazy: every row goes to the browser
    edit_max_rows: int = 5_000  # editable_table: bigger tables are shown read-only, rows returned unchanged
    chart_max_points: int = 5_000  # line / area / scatter charts are thinned to this many points per series
    chart_max_categories: int = 30  # bar / pie charts keep the biggest categories and group the rest as "Khác"

    # Database (backend/core/db.py). APP_DATABASE_URL wins; else PostgreSQL from POSTGRES_*; else data/app.db (SQLite)
    database_url: str = ""
    postgres_ip: str = Field("", validation_alias="POSTGRES_IP")
    postgres_port: int = Field(5432, validation_alias="POSTGRES_PORT")
    postgres_db: str = Field("", validation_alias="POSTGRES_DB")
    postgres_user: str = Field("", validation_alias="POSTGRES_USER")
    postgres_password: str = Field("", validation_alias="POSTGRES_PASSWORD")

    @field_validator("data_dir", "log_dir")
    @classmethod
    def _resolve_relative(cls, value: Path) -> Path:
        return value if value.is_absolute() else PROJECT_ROOT / value

    def feature_data_dir(self, feature_key: str) -> Path:
        """Folder where a feature stores its files: ``data/<feature_key>/`` (created on demand)."""
        path = self.data_dir / feature_key
        path.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache
def get_settings() -> Settings:
    return Settings()
