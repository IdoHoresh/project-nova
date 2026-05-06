import pytest
from nova_agent.budget import BudgetExceeded, BudgetGuard, SessionBudget


def test_budget_allows_under_cap():
    g = BudgetGuard(daily_cap_usd=10.00)
    g.charge(2.00)
    g.charge(3.00)
    assert g.spent_today == 5.00


def test_budget_blocks_over_cap():
    g = BudgetGuard(daily_cap_usd=5.00)
    g.charge(3.00)
    with pytest.raises(BudgetExceeded):
        g.charge(2.50)


def test_zero_cap_is_unlimited():
    g = BudgetGuard(daily_cap_usd=0.0)
    g.charge(1_000_000.0)  # no error


def test_session_budget_allows_under_cap() -> None:
    b = SessionBudget(cap_usd=1.0)
    b.pre_charge(0.4)
    b.true_up(0.4, 0.35)
    assert abs(b.spent - 0.35) < 1e-9


def test_session_budget_blocks_at_cap() -> None:
    b = SessionBudget(cap_usd=1.0)
    b.pre_charge(0.6)
    b.true_up(0.6, 0.55)
    with pytest.raises(BudgetExceeded):
        b.pre_charge(0.5)  # 0.55 + 0.5 = 1.05 > 1.0


def test_session_budget_zero_cap_unlimited() -> None:
    b = SessionBudget(cap_usd=0.0)
    b.pre_charge(9999.0)  # no raise


def test_session_budget_refund_restores_spent() -> None:
    b = SessionBudget(cap_usd=1.0)
    b.pre_charge(0.8)
    b.refund(0.8)
    assert b.spent == 0.0


def test_session_budget_second_pre_charge_blocked_when_first_in_flight() -> None:
    """Two concurrent pre-charges that together exceed cap: second must be blocked.

    Simulates two asyncio coroutines both calling pre_charge before either
    calls true_up. The first pre_charge increments spent; the second sees the
    updated value and raises.
    """
    b = SessionBudget(cap_usd=1.0)
    b.pre_charge(0.7)  # spent = 0.7; succeeds
    with pytest.raises(BudgetExceeded):
        b.pre_charge(0.4)  # 0.7 + 0.4 = 1.1 > 1.0
