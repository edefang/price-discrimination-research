"""Bot-page canary (requirement R6, threat T3).

Every capture is classified before its price is trusted. Without this, "all personas
were served a challenge page" and "no persona was treated differently" produce the
same rows — three identical prices — and the v0 prototype had no way to tell them
apart.

The check is structural, on the captured HTML, and deliberately ignores the HTTP
status: challenge pages are routinely served with 200. Rules are per retailer; the
default matches the mock storefront and the common challenge-page vocabulary.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class CanaryStatus(str, Enum):
    REAL_PAGE = "real_page"
    BOT_PAGE = "bot_page"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class CanaryRule:
    """`real_markers` must *all* be present for a real page; any `bot_marker` is
    decisive on its own. Case-insensitive substring matching — a canary that depends
    on exact markup breaks the first time the retailer reorders an attribute."""

    name: str
    real_markers: tuple[str, ...]
    bot_markers: tuple[str, ...] = field(
        default=(
            'id="challenge"',
            "verify you are human",
            "just a moment",
            "captcha",
            "access denied",
            "unusual traffic",
        )
    )


DEFAULT_RULE = CanaryRule(
    name="mock-store",
    real_markers=('data-store="pdd-mock"', 'data-test="price-block"'),
)


def check(html: str | None, rule: CanaryRule = DEFAULT_RULE) -> CanaryStatus:
    if not html:
        return CanaryStatus.UNKNOWN
    lowered = html.lower()
    if any(m.lower() in lowered for m in rule.bot_markers):
        return CanaryStatus.BOT_PAGE
    if all(m.lower() in lowered for m in rule.real_markers):
        return CanaryStatus.REAL_PAGE
    return CanaryStatus.UNKNOWN
