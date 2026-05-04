"""Tests for main._build_io factory."""

from __future__ import annotations

from nova_agent.action.live_io import LiveGameIO
from nova_agent.config import Settings
from nova_agent.lab.io import SimGameIO
from nova_agent.main import _build_io


def _settings(**overrides: object) -> Settings:
    """Build a Settings with the env-var fields the test cares about,
    populating the required api-key fields with placeholders.

    Pydantic-settings reads alias keys (the env-var names like
    GOOGLE_API_KEY / NOVA_IO_SOURCE), not field attribute names.
    populate_by_name is not enabled on the model_config, so passing
    kwargs by field name is silently dropped under extra="ignore".
    Use aliases here so the construction actually takes effect.
    """
    base: dict[str, object] = {
        "GOOGLE_API_KEY": "x" * 8,
        "ANTHROPIC_API_KEY": "x" * 8,
    }
    base.update(overrides)
    return Settings(**base)  # type: ignore[arg-type]


def test_build_io_returns_live_game_io_by_default() -> None:
    s = _settings()
    io = _build_io(s)
    assert isinstance(io, LiveGameIO)


def test_build_io_returns_sim_game_io_when_io_source_sim() -> None:
    s = _settings(NOVA_IO_SOURCE="sim", NOVA_SIM_SCENARIO="fresh-start")
    io = _build_io(s)
    assert isinstance(io, SimGameIO)
