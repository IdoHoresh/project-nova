from pathlib import Path
from typing import Literal

from dotenv import find_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from nova_agent.llm.tiers import TierName

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
        # Process env takes precedence over .env by default. If a parent shell
        # exports an alias as an empty string (common for ANTHROPIC_API_KEY in
        # CI / template shell rcs), it shadows the populated .env value and
        # produces confusing "auth header not set" errors at API call time.
        # Treat empty exports as "unset" so the .env wins.
        env_ignore_empty=True,
    )

    # Required secrets — TWO providers
    google_api_key: str = Field(..., alias="GOOGLE_API_KEY")
    anthropic_api_key: str = Field(..., alias="ANTHROPIC_API_KEY")

    # Per-task model selection (see spec §6 tech stack table). When the
    # `tier` field is set, those values override the per-task defaults
    # below — see ADR-0006 for the cost-discipline rationale and the four
    # tiers (plumbing / dev / production / demo).
    decision_model: str = Field("gemini-2.5-flash", alias="NOVA_DECISION_MODEL")
    deliberation_model: str = Field("gemini-2.5-pro", alias="NOVA_DELIBERATION_MODEL")
    cheap_vision_model: str = Field("gemini-2.5-flash-lite", alias="NOVA_CHEAP_VISION_MODEL")
    reflection_model: str = Field("claude-sonnet-4-6", alias="NOVA_REFLECTION_MODEL")
    demo_model: str = Field("claude-opus-4-7", alias="NOVA_DEMO_MODEL")

    # Cost-discipline tier (see ADR-0006 + nova_agent.llm.tiers). When set,
    # main.py uses tiers.model_for(role) for decision/tot/reflection
    # routing instead of the per-task fields above. Default None preserves
    # the per-task defaults (the historical shape) for backward
    # compatibility with existing .env files. Validated against the
    # TierName Literal at the chokepoint per .claude/rules/security.md
    # ("validate every external boundary with pydantic").
    tier: TierName | None = Field(None, alias="NOVA_TIER")

    # Storage paths
    sqlite_path: Path = Field(Path("./data/nova.db"), alias="NOVA_SQLITE_PATH")
    lancedb_path: Path = Field(Path("./data/lancedb"), alias="NOVA_LANCEDB_PATH")

    # ADB / emulator
    adb_path: str = Field("adb", alias="ADB_PATH")
    adb_device_id: str | None = Field(None, alias="ADB_DEVICE_ID")

    # WebSocket
    ws_host: str = Field("127.0.0.1", alias="NOVA_WS_HOST")
    ws_port: int = Field(8765, alias="NOVA_WS_PORT")

    # Bus recording (dev-only). When set, every published AgentEvent is
    # appended to this JSONL file in addition to the live broadcast — see
    # nova_agent.bus.recorder. Default None disables recording entirely.
    bus_record_path: Path | None = Field(None, alias="NOVA_BUS_RECORD")

    # GameIO source — flips main._build_io between LiveGameIO (live
    # emulator via OCR + ADB) and SimGameIO (in-process Game2048Sim +
    # brutalist renderer). Default "live" preserves existing behaviour;
    # "sim" is the Phase 0.7 cliff-test path. See ADR-0008.
    io_source: Literal["live", "sim"] = Field("live", alias="NOVA_IO_SOURCE")
    sim_scenario: str = Field("fresh-start", alias="NOVA_SIM_SCENARIO")

    # Logging
    log_level: str = Field("INFO", alias="NOVA_LOG_LEVEL")

    # Cost guardrail (USD); 0 means no limit
    daily_budget_usd: float = Field(20.0, alias="NOVA_DAILY_BUDGET_USD")

    # Phase 0.7a counterfactual ablation flag (spec §2.1 + §4.1). When True,
    # AffectState.update() skips the `0.7 * max(0.0, (3 - empty_cells) / 3)`
    # anxiety term, isolating the contribution of trauma_intensity / RPE-driven
    # anxiety drivers. Default False — production behavior unchanged. Sourced
    # via env var NOVA_NULL_EMPTY_CELLS_ANXIETY_TERM=1.
    null_empty_cells_anxiety_term: bool = Field(False, alias="NOVA_NULL_EMPTY_CELLS_ANXIETY_TERM")


_settings: Settings | None = None


def get_settings() -> Settings:
    """Lazy singleton. Call this at runtime, not at import."""
    global _settings
    if _settings is None:
        _settings = Settings()
        _settings.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        _settings.lancedb_path.mkdir(parents=True, exist_ok=True)
    return _settings
