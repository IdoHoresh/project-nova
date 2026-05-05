"""Tests for the cliff-test runner orchestrator + CLI."""

from __future__ import annotations

import os
import subprocess
import sys


def _run_cli(
    *args: str, env_overrides: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    """Invoke the cliff-test CLI as a subprocess and return the result."""
    env = os.environ.copy()
    # Strip API keys to make sure tier-guard tests don't accidentally hit a real provider.
    for var in ("ANTHROPIC_API_KEY", "GOOGLE_API_KEY"):
        env.pop(var, None)
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run(
        [sys.executable, "-m", "nova_agent.lab.cliff_test", *args],
        capture_output=True,
        text=True,
        env=env,
    )


def test_cli_help_runs_clean() -> None:
    """`cliff-test --help` exits 0 and prints usage."""
    result = _run_cli("--help")
    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert "cliff-test" in result.stdout.lower() or "usage" in result.stdout.lower()


def test_cli_rejects_dev_tier() -> None:
    """Runner refuses NOVA_TIER=dev (per spec §6.1 + ADR-0006)."""
    result = _run_cli(
        "--scenario",
        "snake-collapse-128",
        "--n",
        "1",
        env_overrides={"NOVA_TIER": "dev"},
    )
    assert result.returncode != 0
    combined = (result.stdout + result.stderr).lower()
    assert "tier" in combined


def test_cli_rejects_plumbing_tier() -> None:
    """Runner refuses NOVA_TIER=plumbing (cognitive-judgment models downgraded)."""
    result = _run_cli(
        "--scenario",
        "snake-collapse-128",
        "--n",
        "1",
        env_overrides={"NOVA_TIER": "plumbing"},
    )
    assert result.returncode != 0
    combined = (result.stdout + result.stderr).lower()
    assert "tier" in combined
