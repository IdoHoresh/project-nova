from pathlib import Path

from dotenv import find_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Walk up from cwd to locate the first `.env` (worktree root, repo root, etc.).
# Falls back to a literal ".env" so unit tests that monkeypatch env vars without
# a file on disk still work. Without this, `nova` invoked from the `nova-agent/`
# subdir would never find the repo-root `.env`.
_ENV_FILE = find_dotenv(usecwd=True) or ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Required secrets — TWO providers
    google_api_key: str = Field(..., alias="GOOGLE_API_KEY")
    anthropic_api_key: str = Field(..., alias="ANTHROPIC_API_KEY")

    # Per-task model selection (see spec §6 tech stack table)
    decision_model: str = Field("gemini-2.5-flash", alias="NOVA_DECISION_MODEL")
    deliberation_model: str = Field("gemini-2.5-pro", alias="NOVA_DELIBERATION_MODEL")
    cheap_vision_model: str = Field("gemini-2.5-flash-lite", alias="NOVA_CHEAP_VISION_MODEL")
    reflection_model: str = Field("claude-sonnet-4-6", alias="NOVA_REFLECTION_MODEL")
    demo_model: str = Field("claude-opus-4-7", alias="NOVA_DEMO_MODEL")

    # Storage paths
    sqlite_path: Path = Field(Path("./data/nova.db"), alias="NOVA_SQLITE_PATH")
    lancedb_path: Path = Field(Path("./data/lancedb"), alias="NOVA_LANCEDB_PATH")

    # ADB / emulator
    adb_path: str = Field("adb", alias="ADB_PATH")
    adb_device_id: str | None = Field(None, alias="ADB_DEVICE_ID")

    # WebSocket
    ws_host: str = Field("127.0.0.1", alias="NOVA_WS_HOST")
    ws_port: int = Field(8765, alias="NOVA_WS_PORT")

    # Logging
    log_level: str = Field("INFO", alias="NOVA_LOG_LEVEL")

    # Cost guardrail (USD); 0 means no limit
    daily_budget_usd: float = Field(20.0, alias="NOVA_DAILY_BUDGET_USD")


_settings: Settings | None = None


def get_settings() -> Settings:
    """Lazy singleton. Call this at runtime, not at import."""
    global _settings
    if _settings is None:
        _settings = Settings()
        _settings.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        _settings.lancedb_path.mkdir(parents=True, exist_ok=True)
    return _settings
