from datetime import date


class BudgetExceeded(RuntimeError):
    """Raised when an LLM call would exceed the configured daily cap."""


class BudgetGuard:
    def __init__(self, daily_cap_usd: float):
        self.daily_cap_usd = daily_cap_usd
        self._day = date.today()
        self.spent_today = 0.0

    def _roll_day(self) -> None:
        today = date.today()
        if today != self._day:
            self._day = today
            self.spent_today = 0.0

    def charge(self, amount_usd: float) -> None:
        self._roll_day()
        if self.daily_cap_usd > 0 and self.spent_today + amount_usd > self.daily_cap_usd:
            raise BudgetExceeded(
                f"Charge of ${amount_usd:.4f} would exceed daily cap "
                f"${self.daily_cap_usd:.2f} (already spent ${self.spent_today:.4f})."
            )
        self.spent_today += amount_usd


class RunBudget:
    """Per-run cap (§6.6 lever L5). Default $0.50; envvar NOVA_PER_RUN_CAP_USD."""

    def __init__(self, cap_usd: float = 0.50):
        self.cap_usd = cap_usd
        self.spent = 0.0

    def charge(self, amount_usd: float) -> None:
        if self.cap_usd > 0 and self.spent + amount_usd > self.cap_usd:
            raise BudgetExceeded(
                f"Per-run charge of ${amount_usd:.4f} would exceed run cap "
                f"${self.cap_usd:.2f} (already spent ${self.spent:.4f})."
            )
        self.spent += amount_usd


class SessionBudget:
    """M-07 Cost-Abort Gate: tracks total spend across all LLM calls in a run.

    Shared across all BudgetedLLM wrappers so decision, tot, reflection, and
    bot spend aggregate into one session cap. Pre-charges a pessimistic
    estimate before each call so that concurrent asyncio coroutines cannot
    both pass the cap check on the same stale ``spent`` value.

    asyncio contract: all mutations are synchronous (no ``await``), so they
    run atomically on the single-threaded event loop — no lock needed.
    """

    def __init__(self, cap_usd: float) -> None:
        self.cap_usd = cap_usd
        self.spent = 0.0

    def pre_charge(self, estimate_usd: float) -> None:
        """Check + increment ``spent`` before the call.

        Raises BudgetExceeded if the estimate would push spend past cap.
        Increments ``spent`` on success so a concurrent call sees the updated
        value and cannot also pass the same cap check.
        """
        if self.cap_usd > 0 and self.spent + estimate_usd > self.cap_usd:
            raise BudgetExceeded(
                f"Pre-call estimate ${estimate_usd:.4f} would push session spend "
                f"${self.spent:.4f} past cap ${self.cap_usd:.2f}."
            )
        self.spent += estimate_usd

    def true_up(self, estimate_usd: float, actual_usd: float) -> None:
        """Post-call: replace the pre-charged estimate with the actual cost.

        Actual is always ≤ estimate (conservative estimate), so ``spent``
        can only decrease or stay the same. Clamp to 0 for float precision.
        """
        self.spent = max(0.0, self.spent - estimate_usd) + actual_usd

    def refund(self, estimate_usd: float) -> None:
        """Refund a pre-charged estimate when the LLM call raises."""
        self.spent = max(0.0, self.spent - estimate_usd)
