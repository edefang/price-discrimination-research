"""Locale-aware price parsing (requirement R7).

The v0 parser was a single regex, `[\\$£€]\\s?(\\d+(?:[.,]\\d{2})?)`, and it was wrong on
seven of nine common price formats. It read `$1,299.00` as 129.0 and `$24,999.00` as
2499.0 — greedy `\\d+` took one digit, the optional tail ate the thousands separator —
and it returned nothing at all for `49,99 EUR` or `USD 49.99`, which are exactly the
formats non-US locale personas produce. Because the analysis filtered on non-null
prices, those personas silently vanished from the cohort.

Three rules follow from that, and they are the whole design here:

1. **Separators are resolved by locale, never guessed from the string.** `1,299` is
   1299 in en-US and ambiguous in de-DE, and no amount of inspecting the text settles it.
2. **Every candidate on the page is returned.** `.search()` taking the first match meant
   the struck-through original price won over the sale price, systematically.
3. **Ambiguity produces a status, never a number.** A wrong price is worse than a
   missing one, because a missing one is visible.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from enum import Enum

from .money import Money, minor_unit_exponent


class ParseStatus(str, Enum):
    OK = "ok"
    NO_MATCH = "no_match"
    AMBIGUOUS = "ambiguous"
    MULTIPLE_CANDIDATES = "multiple_candidates"


@dataclass(frozen=True)
class LocaleConvention:
    group_sep: str
    decimal_sep: str
    currency: str


# Extend as the retailer sample grows. Adding a locale without knowing its convention
# is not permitted — an unknown locale raises rather than falling back to en-US.
LOCALES: dict[str, LocaleConvention] = {
    "en-US": LocaleConvention(",", ".", "USD"),
    "en-CA": LocaleConvention(",", ".", "CAD"),
    "en-GB": LocaleConvention(",", ".", "GBP"),
    "en-AU": LocaleConvention(",", ".", "AUD"),
    "en-IN": LocaleConvention(",", ".", "INR"),
    "de-DE": LocaleConvention(".", ",", "EUR"),
    "es-ES": LocaleConvention(".", ",", "EUR"),
    "it-IT": LocaleConvention(".", ",", "EUR"),
    "nl-NL": LocaleConvention(".", ",", "EUR"),
    "pt-BR": LocaleConvention(".", ",", "BRL"),
    "fr-FR": LocaleConvention(" ", ",", "EUR"),
    "de-CH": LocaleConvention("'", ".", "CHF"),
    "ja-JP": LocaleConvention(",", ".", "JPY"),
}

_SYMBOL_TO_CODES: dict[str, tuple[str, ...]] = {
    "$": ("USD", "CAD", "AUD"),
    "£": ("GBP",),
    "€": ("EUR",),
    "¥": ("JPY",),
    "₹": ("INR",),
    "R$": ("BRL",),
    "CHF": ("CHF",),
}

_ISO_CODES = {
    "USD", "EUR", "GBP", "CAD", "AUD", "JPY", "INR", "BRL", "CHF", "SEK", "NOK", "DKK",
    "PLN", "MXN", "NZD", "SGD", "HKD", "ZAR", "KRW",
}

# A run of digits and separator characters. Deliberately permissive: the token is
# validated strictly afterwards, under the locale. Matching loosely and then rejecting
# is what lets the parser distinguish "no price here" from "a price I refuse to guess at".
_NUMERIC_TOKEN = re.compile(r"\d[\d.,'   ]*\d|\d")

_CURRENCY_MARKER = re.compile(
    r"R\$|CHF|[$£€¥₹]|\b(?:" + "|".join(sorted(_ISO_CODES)) + r")\b"
)

# How far a currency marker may sit from its number, in characters.
_MAX_MARKER_DISTANCE = 3


@dataclass(frozen=True)
class Candidate:
    """One price-like token found in the text."""

    money: Money
    raw: str
    start: int
    end: int
    dom_role: str | None = None


@dataclass(frozen=True)
class ParseResult:
    status: ParseStatus
    money: Money | None = None
    candidates: tuple[Candidate, ...] = field(default_factory=tuple)
    reason: str | None = None

    @property
    def ok(self) -> bool:
        return self.status is ParseStatus.OK


class UnknownLocale(KeyError):
    """Raised for a locale with no recorded convention. Never falls back silently."""


def _normalize(text: str) -> str:
    """Fold the space-like characters retailers use inside numbers into plain spaces."""
    text = unicodedata.normalize("NFKC", text)
    return text.replace(" ", " ").replace(" ", " ").replace(" ", " ")


def _resolve_currency(marker: str, conv: LocaleConvention) -> str | None:
    """Map a currency marker to an ISO code, using the locale to disambiguate.

    `$` alone is not a currency: it is USD, CAD, or AUD. The persona's locale decides.
    If it cannot, the caller gets an ambiguous status rather than a guess.
    """
    marker = marker.strip()
    if marker.upper() in _ISO_CODES:
        return marker.upper()
    codes = _SYMBOL_TO_CODES.get(marker)
    if not codes:
        return None
    if len(codes) == 1:
        return codes[0]
    return conv.currency if conv.currency in codes else None


def _role_for(start: int, end: int, dom_roles: dict[int, str] | None) -> str | None:
    """Find the DOM role whose offset lands on this candidate.

    Accepts a key inside the amount, or just before it (pointing at the currency
    marker). Ties go to the nearest key.
    """
    if not dom_roles:
        return None
    hits = [
        (abs(offset - start), role)
        for offset, role in dom_roles.items()
        if start <= offset < end or 0 <= start - offset <= _MAX_MARKER_DISTANCE
    ]
    return min(hits)[1] if hits else None


def _parse_number(token: str, conv: LocaleConvention, currency: str) -> tuple[str, str]:
    """Split a numeric token into (integer_digits, fraction_digits) under `conv`.

    Raises ValueError with a specific reason on anything ambiguous. This function is
    where the v0 bug lived and where it is now impossible: the separators are supplied,
    not inferred.
    """
    token = token.strip()
    exponent = minor_unit_exponent(currency)
    group, dec = conv.group_sep, conv.decimal_sep

    stray = set(re.findall(r"[^\d]", token)) - {group, dec}
    if stray:
        raise ValueError(
            f"separator {''.join(sorted(stray))!r} is neither the group ({group!r}) "
            f"nor decimal ({dec!r}) separator for this locale"
        )

    if token.count(dec) > 1:
        raise ValueError(f"multiple decimal separators ({dec!r})")

    if dec in token:
        int_part, frac_part = token.split(dec)
        if group in frac_part:
            raise ValueError("group separator appears after the decimal separator")
        if not frac_part.isdigit():
            raise ValueError("non-digit in fractional part")
        if exponent == 0:
            raise ValueError(f"{currency} has no minor unit but a decimal part is present")
        if not 1 <= len(frac_part) <= exponent:
            raise ValueError(
                f"{len(frac_part)} fractional digits, expected 1..{exponent} for {currency}"
            )
    else:
        int_part, frac_part = token, ""

    if group and group in int_part:
        groups = int_part.split(group)
        if not all(g.isdigit() for g in groups):
            raise ValueError("non-digit in integer part")
        if not 1 <= len(groups[0]) <= 3 or any(len(g) != 3 for g in groups[1:]):
            raise ValueError(
                f"malformed grouping {int_part!r}: groups after the first must be 3 digits"
            )
        int_part = "".join(groups)

    if not int_part.isdigit():
        raise ValueError("non-digit in integer part")

    return int_part, frac_part


def parse_price(
    raw_text: str | None,
    locale: str,
    *,
    dom_roles: dict[int, str] | None = None,
) -> ParseResult:
    """Extract every price in `raw_text`, interpreting separators under `locale`.

    `dom_roles` optionally maps a character offset to a DOM role (for example
    `"struck_through"`), so the caller can resolve a multi-candidate result by structure
    rather than by position. Which candidate counts is a pre-registered decision, never
    an accident of regex ordering.

    Offsets are matched tolerantly: a key may point at the currency marker or anywhere
    inside the amount, since a caller should not have to know where the digits start.
    In live use the extraction layer parses one DOM node at a time and carries the role
    directly; the offset map is for text that arrives as a single blob.
    """
    if locale not in LOCALES:
        raise UnknownLocale(
            f"no recorded convention for locale {locale!r}; add it to LOCALES rather "
            "than defaulting, since guessing separators is the defect this module exists to fix"
        )
    conv = LOCALES[locale]

    if not raw_text or not raw_text.strip():
        return ParseResult(ParseStatus.NO_MATCH, reason="empty text")

    text = _normalize(raw_text)
    markers = [(m.start(), m.end(), m.group()) for m in _CURRENCY_MARKER.finditer(text)]
    if not markers:
        return ParseResult(
            ParseStatus.NO_MATCH,
            reason="no currency marker found; an amount without a currency is not comparable (R4)",
        )

    candidates: list[Candidate] = []
    problems: list[str] = []
    claimed: set[tuple[int, int]] = set()

    for m in _NUMERIC_TOKEN.finditer(text):
        token, t_start, t_end = m.group(), m.start(), m.end()

        # Attach the nearest currency marker on either side, within a short distance.
        marker = next(
            (
                mk
                for (s, e, mk) in markers
                if 0 <= t_start - e <= _MAX_MARKER_DISTANCE
                or 0 <= s - t_end <= _MAX_MARKER_DISTANCE
            ),
            None,
        )
        if marker is None:
            continue

        currency = _resolve_currency(marker, conv)
        if currency is None:
            problems.append(
                f"currency marker {marker!r} is ambiguous under locale {locale} "
                f"(could be {', '.join(_SYMBOL_TO_CODES.get(marker.strip(), ()))})"
            )
            continue

        try:
            int_part, frac_part = _parse_number(token, conv, currency)
        except ValueError as exc:
            problems.append(f"{token!r}: {exc}")
            continue

        if (t_start, t_end) in claimed:
            continue
        claimed.add((t_start, t_end))
        candidates.append(
            Candidate(
                money=Money.from_decimal_string(int_part, frac_part, currency),
                raw=token,
                start=t_start,
                end=t_end,
                dom_role=_role_for(t_start, t_end, dom_roles),
            )
        )

    if not candidates:
        return ParseResult(
            ParseStatus.AMBIGUOUS if problems else ParseStatus.NO_MATCH,
            reason="; ".join(problems) if problems else "no price-like token near a currency marker",
        )

    if problems:
        return ParseResult(
            ParseStatus.AMBIGUOUS,
            candidates=tuple(candidates),
            reason="; ".join(problems),
        )

    distinct = {(c.money.minor_units, c.money.currency) for c in candidates}
    if len(distinct) > 1:
        return ParseResult(
            ParseStatus.MULTIPLE_CANDIDATES,
            candidates=tuple(candidates),
            reason=(
                f"{len(distinct)} distinct prices in one element "
                f"({', '.join(sorted(c.raw for c in candidates))}); "
                "the caller must select by DOM role, not by position"
            ),
        )

    return ParseResult(ParseStatus.OK, money=candidates[0].money, candidates=tuple(candidates))
