# nova-agent/tests/test_lab_trauma_golden.py
import json
from pathlib import Path

import pytest

from nova_agent.lab.trauma_ablation import (
    _golden_seed,
    _read_golden_calibration,
    _check_golden_gate_passed,
)


# --- Seed namespace isolation ---


def test_golden_seed_is_separate_namespace() -> None:
    """Golden seeds must not collide with the first 200 surrogate/main seeds."""
    # Surrogate/main use offset-based seeds starting at 0
    surrogate_main_seeds = set(range(200))
    golden_seeds = {_golden_seed(i) for i in range(10)}
    assert golden_seeds.isdisjoint(surrogate_main_seeds), (
        f"Golden seeds {golden_seeds} collide with surrogate/main {surrogate_main_seeds}"
    )


def test_golden_seed_deterministic() -> None:
    """Same seed_idx produces same golden seed."""
    assert _golden_seed(0) == _golden_seed(0)
    assert _golden_seed(0) != _golden_seed(1)


# --- Calibration read ---


def test_read_golden_calibration_parses_thresholds(tmp_path: Path) -> None:
    """Parse golden_calibration.json and extract thresholds."""
    calib = {
        "move_threshold": 5,
        "anxiety_threshold": 0.8,
        "sessions": [],
    }
    calib_path = tmp_path / "golden_calibration.json"
    calib_path.write_text(json.dumps(calib))
    thresholds = _read_golden_calibration(calib_path)
    assert thresholds["move_threshold"] == 5
    assert abs(thresholds["anxiety_threshold"] - 0.8) < 1e-6


def test_read_golden_calibration_raises_on_missing(tmp_path: Path) -> None:
    """Raise FileNotFoundError if golden_calibration.json missing."""
    with pytest.raises(FileNotFoundError):
        _read_golden_calibration(tmp_path / "nonexistent.json")


# --- Surrogate gate-check ---


def test_check_golden_gate_passed_raises_on_missing_result(tmp_path: Path) -> None:
    """_check_golden_gate_passed raises if golden/result.json missing."""
    with pytest.raises((FileNotFoundError, RuntimeError)):
        _check_golden_gate_passed(tmp_path)


def test_check_golden_gate_passed_raises_on_non_pass_status(tmp_path: Path) -> None:
    """_check_golden_gate_passed raises if status != 'pass'."""
    golden_dir = tmp_path / "golden"
    golden_dir.mkdir(parents=True)
    (golden_dir / "result.json").write_text(json.dumps({"status": "fail"}))
    with pytest.raises((ValueError, RuntimeError)):
        _check_golden_gate_passed(tmp_path)


def test_check_golden_gate_passed_succeeds_on_pass_status(tmp_path: Path) -> None:
    """_check_golden_gate_passed succeeds without raising when status='pass'."""
    golden_dir = tmp_path / "golden"
    golden_dir.mkdir(parents=True)
    (golden_dir / "result.json").write_text(json.dumps({"status": "pass"}))
    # Must not raise
    _check_golden_gate_passed(tmp_path)
