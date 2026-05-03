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
