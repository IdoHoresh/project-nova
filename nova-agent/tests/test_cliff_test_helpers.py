"""Tests for the pure helpers in nova_agent.lab.cliff_test."""

from __future__ import annotations

from nova_agent.lab.cliff_test import (
    _check_anxiety_threshold,
    _first_threshold_index,
)


class TestCheckAnxietyThreshold:
    def test_no_breach(self) -> None:
        """Trajectory all 0.4 → False, no threshold index."""
        traj = [0.4] * 10
        assert _check_anxiety_threshold(traj) is False
        assert _first_threshold_index(traj) is None

    def test_single_spike_no_pair(self) -> None:
        """One spike above without a pair → False (need ≥ 2 consecutive)."""
        traj = [0.4, 0.4, 0.7, 0.4, 0.4]
        assert _check_anxiety_threshold(traj) is False
        assert _first_threshold_index(traj) is None

    def test_pair_at_index_1(self) -> None:
        """Two consecutive above → True, t_predicts at first move of the pair."""
        traj = [0.4, 0.7, 0.65, 0.4]
        assert _check_anxiety_threshold(traj) is True
        assert _first_threshold_index(traj) == 1

    def test_late_pair(self) -> None:
        """Pair late in trajectory → True, t_predicts at first move of the late pair."""
        traj = [0.4, 0.4, 0.4, 0.7, 0.7]
        assert _check_anxiety_threshold(traj) is True
        assert _first_threshold_index(traj) == 3

    def test_three_consecutive_returns_first(self) -> None:
        """Three consecutive — t_predicts is the first of the three."""
        traj = [0.3, 0.7, 0.7, 0.7, 0.4]
        assert _first_threshold_index(traj) == 1

    def test_boundary_value_is_strict_greater(self) -> None:
        """Threshold is > 0.6 (strict), per spec §2.7. Exactly 0.6 doesn't count."""
        traj = [0.6, 0.6, 0.6]
        assert _check_anxiety_threshold(traj) is False
        assert _first_threshold_index(traj) is None

    def test_empty_trajectory(self) -> None:
        """Empty trajectory → False, no index."""
        assert _check_anxiety_threshold([]) is False
        assert _first_threshold_index([]) is None
