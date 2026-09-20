"""Money as integer minor units.

The v0 prototype stored price as SQLite REAL. Float money accumulates representation
error and invites comparing 89.0 to 110.0 without noticing they are different
currencies. Both problems are structural, so the type forbids them.
"""

from __future__ import annotations

from dataclasses import dataclass

# Currencies whose minor unit is not 1/100. Extend as the retailer sample grows.
_EXPONENT_OVERRIDES = {
    "JPY": 0,
    "KRW": 0,
    "CLP": 0,
    "ISK": 0,
    "VND": 0,
    "BHD": 3,
    "KWD": 3,
    "OMR": 3,
    "TND": 3,
}

DEFAULT_EXPONENT = 2


def minor_unit_exponent(currency: str) -> int:
    """Decimal digits in this currency's minor unit."""
    return _EXPONENT_OVERRIDES.get(currency.upper(), DEFAULT_EXPONENT)


class CurrencyMismatch(ValueError):
    """Raised on any attempt to relate amounts in different currencies.

    Threat T5. The v0 analysis compared raw floats across personas that varied by
    locale, so a localized currency would have been reported as a price gap.
    """


@dataclass(frozen=True, order=False)
class Money:
    """An exact amount in a single currency, held as integer minor units."""

    minor_units: int
    currency: str

    def __post_init__(self) -> None:
        if not isinstance(self.minor_units, int) or isinstance(self.minor_units, bool):
            raise TypeError(f"minor_units must be int, got {type(self.minor_units).__name__}")
        if not (isinstance(self.currency, str) and len(self.currency) == 3):
            raise ValueError(f"currency must be a 3-letter code, got {self.currency!r}")
        object.__setattr__(self, "currency", self.currency.upper())

    @classmethod
    def from_decimal_string(cls, integer_part: str, fraction_part: str, currency: str) -> Money:
        """Build from already-separated digit strings.

        Takes the parts rather than a formatted string on purpose: deciding which
        separator was decimal and which was grouping is the parser's job, under a known
        locale. Guessing it from the string is the v0 bug that read `$1,299.00` as 129.0.
        """
        exponent = minor_unit_exponent(currency)
        digits = (fraction_part or "").ljust(exponent, "0")
        if len(digits) > exponent:
            raise ValueError(
                f"{len(digits)} fractional digits exceeds {exponent} for {currency}"
            )
        sign = -1 if integer_part.startswith("-") else 1
        whole = abs(int(integer_part or "0"))
        return cls(sign * (whole * 10**exponent + int(digits or "0")), currency)

    def _check(self, other: Money) -> None:
        if not isinstance(other, Money):
            raise TypeError(f"expected Money, got {type(other).__name__}")
        if self.currency != other.currency:
            raise CurrencyMismatch(
                f"cannot relate {self.currency} and {other.currency}; "
                "cross-currency comparison is forbidden (R4)"
            )

    def __lt__(self, other: Money) -> bool:
        self._check(other)
        return self.minor_units < other.minor_units

    def __le__(self, other: Money) -> bool:
        self._check(other)
        return self.minor_units <= other.minor_units

    def __gt__(self, other: Money) -> bool:
        self._check(other)
        return self.minor_units > other.minor_units

    def __ge__(self, other: Money) -> bool:
        self._check(other)
        return self.minor_units >= other.minor_units

    def __sub__(self, other: Money) -> Money:
        self._check(other)
        return Money(self.minor_units - other.minor_units, self.currency)

    def proportional_deviation_from(self, reference: Money) -> float:
        """(self - reference) / reference, signed.

        Signed because detection is two-sided (R2): a persona shown a lower price is as
        much a finding as one shown a higher price. The v0 test was one-sided and could
        not see targeted discounts at all.
        """
        self._check(reference)
        if reference.minor_units == 0:
            raise ZeroDivisionError("reference price is zero")
        return (self.minor_units - reference.minor_units) / reference.minor_units

    def as_decimal_str(self) -> str:
        exponent = minor_unit_exponent(self.currency)
        sign = "-" if self.minor_units < 0 else ""
        whole, frac = divmod(abs(self.minor_units), 10**exponent)
        if exponent == 0:
            return f"{sign}{whole}"
        return f"{sign}{whole}.{frac:0{exponent}d}"

    def __repr__(self) -> str:
        return f"Money({self.as_decimal_str()} {self.currency})"
