"""Tests for the pure helpers in nova_agent.lab.cliff_test."""

from __future__ import annotations

import pytest

from nova_agent.lab.cliff_test import (
    _BudgetState,
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


class TestBudgetState:
    def test_initial_state_under_caps(self) -> None:
        bs = _BudgetState()
        assert bs.soft_cap_hit("snake-collapse-128", "carla") is False
        assert bs.hard_cap_hit("snake-collapse-128", "carla") is False

    def test_soft_cap_exact(self) -> None:
        """Spend exactly $5 → soft cap hit (>= comparison)."""
        bs = _BudgetState()
        bs.add("snake-collapse-128", "carla", 5.00)
        assert bs.soft_cap_hit("snake-collapse-128", "carla") is True
        assert bs.hard_cap_hit("snake-collapse-128", "carla") is False

    def test_soft_cap_just_under(self) -> None:
        """$4.99 → soft cap NOT hit."""
        bs = _BudgetState()
        bs.add("snake-collapse-128", "carla", 4.99)
        assert bs.soft_cap_hit("snake-collapse-128", "carla") is False

    def test_hard_cap(self) -> None:
        """$6.50 → hard cap hit (5 * 1.3)."""
        bs = _BudgetState()
        bs.add("snake-collapse-128", "carla", 6.50)
        assert bs.soft_cap_hit("snake-collapse-128", "carla") is True
        assert bs.hard_cap_hit("snake-collapse-128", "carla") is True

    def test_separate_arms(self) -> None:
        """$5 on Carla — Bot still under cap."""
        bs = _BudgetState()
        bs.add("snake-collapse-128", "carla", 5.00)
        assert bs.soft_cap_hit("snake-collapse-128", "bot") is False

    def test_separate_scenarios(self) -> None:
        """$5 on scenario A — scenario B still under cap."""
        bs = _BudgetState()
        bs.add("snake-collapse-128", "carla", 5.00)
        assert bs.soft_cap_hit("512-wall", "carla") is False

    def test_add_accumulates(self) -> None:
        bs = _BudgetState()
        bs.add("snake-collapse-128", "carla", 1.00)
        bs.add("snake-collapse-128", "carla", 2.00)
        assert bs.spent("snake-collapse-128", "carla") == pytest.approx(3.00)

    def test_concurrent_adds_thread_safety(self) -> None:
        """asyncio.gather may race; _BudgetState.add is called from coroutine,
        not from a thread, but the running totals must remain monotonic.
        We don't need a Lock for asyncio coroutines (single-threaded event
        loop), but we do need the implementation to be a single += per call.
        """
        bs = _BudgetState()
        for _ in range(100):
            bs.add("snake-collapse-128", "carla", 0.01)
        assert bs.spent("snake-collapse-128", "carla") == pytest.approx(1.00)
