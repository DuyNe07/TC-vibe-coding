"""Typed application settings loaded from environment variables / .env (prefix ``APP_``)."""

from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
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
