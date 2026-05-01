import pytest
from nova_agent.budget import BudgetGuard, BudgetExceeded


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
