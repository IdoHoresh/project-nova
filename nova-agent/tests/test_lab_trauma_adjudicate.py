import math

import pytest

from nova_agent.lab.trauma_ablation import (
    PRIMARY_PASS_D_FLOOR,
    paired_cohens_d,
    paired_d_ci_95,
    primary_pass,
)


def test_d_zero_on_symmetric_deltas() -> None:
    deltas = [0.0, 0.1, -0.1, 0.05, -0.05]
    d = paired_cohens_d(deltas)
    assert abs(d) < 1e-9


def test_d_positive_on_positive_mean() -> None:
    deltas = [0.3, 0.4, 0.5, 0.35, 0.45]
    assert paired_cohens_d(deltas) > 0


def test_d_known_value() -> None:
    # mean=0.3, sd_ddof1 = |0.2| / sqrt(2-1+1/1) ... use [0.4, 0.2]
    # mean = 0.3, deviations = [0.1, -0.1], variance = 0.01/(2-1)=0.01, sd=0.1
    # Wait: stdev([0.4, 0.2]) = sqrt(((0.4-0.3)^2 + (0.2-0.3)^2) / (2-1))
    #                         = sqrt(0.01 + 0.01) = sqrt(0.02) = 0.14142...
    deltas = [0.4, 0.2]
    d = paired_cohens_d(deltas)
    expected = 0.3 / math.sqrt(0.02)
    assert d == pytest.approx(expected, rel=1e-3)


def test_d_raises_on_too_few() -> None:
    with pytest.raises(ValueError, match="at least 2"):
        paired_cohens_d([0.5])


def test_d_raises_on_zero_variance() -> None:
    with pytest.raises(ValueError, match="zero-variance"):
        paired_cohens_d([0.5, 0.5, 0.5, 0.5])


def test_ci_lo_positive_on_strong_signal() -> None:
    deltas = [0.3 + 0.05 * ((-1) ** i) for i in range(70)]
    lo, hi = paired_d_ci_95(deltas, bootstrap_iters=2000, rng_seed=1)
    assert lo > 0
    assert lo < hi


def test_ci_includes_zero_on_null_signal() -> None:
    deltas = [0.05 * ((-1) ** i) for i in range(70)]
    lo, hi = paired_d_ci_95(deltas, bootstrap_iters=2000, rng_seed=1)
    assert lo < 0 < hi


def test_primary_pass_on_clear_signal() -> None:
    deltas = [0.3 + 0.01 * ((-1) ** i) for i in range(70)]
    assert primary_pass(deltas, r_off_mean=0.30, r_on_mean=0.10) is True


def test_primary_pass_fails_on_direction_flip() -> None:
    deltas = [0.4 + 0.01 * ((-1) ** i) for i in range(70)]
    assert primary_pass(deltas, r_off_mean=0.10, r_on_mean=0.30) is False


def test_primary_pass_fails_on_low_d() -> None:
    deltas = [0.01 * ((-1) ** i) for i in range(70)]
    assert primary_pass(deltas, r_off_mean=0.30, r_on_mean=0.25) is False


def test_primary_pass_floor_value() -> None:
    assert PRIMARY_PASS_D_FLOOR == pytest.approx(0.30)
