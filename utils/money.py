"""Price text -> amount + currency. Pure, no browser."""
import re
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

_SYMBOLS = {"$": "USD", "€": "EUR", "£": "GBP"}
_PRICE = re.compile(r"([$€£])\s*(\d[\d,]*(?:\.\d+)?)")


class Money(BaseModel):
    model_config = ConfigDict(frozen=True)

    amount: Decimal = Field(ge=0)
    currency: str = Field(pattern=r"^[A-Z]{3}$")

    def __str__(self) -> str:
        return f"{self.amount} {self.currency}"


def parse_money(text: str) -> Money:
    """'Item total: $39.98' -> Money(39.98, USD). Raises ValueError on anything else."""
    match = _PRICE.search(text or "")
    if not match:
        raise ValueError(f"No price with a known currency symbol in {text!r}")
    symbol, number = match.groups()
    return Money(amount=Decimal(number.replace(",", "")), currency=_SYMBOLS[symbol])
