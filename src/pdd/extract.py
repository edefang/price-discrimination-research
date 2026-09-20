"""Extract the price from a captured page (requirements R7, R8).

The parser handles one string. This layer decides *which* string: it walks the
captured HTML for price nodes, parses each one separately with its DOM role, and
applies the pre-registered selection rule. Parsing per node is what makes the
strike-through case tractable — the v0 regex ran `.search()` over the whole
element's text and took whichever price came first, which on most storefronts is
the crossed-out one.

Selection rule, fixed in advance:

    1. a node marked `sale` wins over one marked `list`
    2. a node marked `struck_through` is never taken
    3. an unmarked node is taken only if it is the sole candidate
    4. two eligible nodes of the same rank with different prices -> multiple_candidates
    5. any ambiguous parse on an eligible node -> ambiguous, never "try the next one"

Rule 5 matters. Falling through to another node when the preferred one is unreadable
is a guess dressed as robustness.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from html.parser import HTMLParser

from .money import Money
from .parsing import LOCALES, ParseStatus, parse_price

_HTML_LANG = re.compile(r"<html\b[^>]*\blang\s*=\s*[\"']([A-Za-z]{2,3}(?:[-_][A-Za-z]{2})?)[\"']", re.I)


def page_locale(html: str, fallback: str) -> str:
    """The convention to parse under.

    The persona's locale is what the request *asked for*; the page's declared `lang`
    is what the page *is written in*, and a retailer is free to ignore the request.
    A de-DE persona served a US page must read `$99.00` as USD under en-US rules, not
    reject it as ambiguous under de-DE rules. Parsing under the page's own declaration
    is the only reading that is right in both cases.
    """
    m = _HTML_LANG.search(html)
    if not m:
        return fallback
    lang = m.group(1).replace("_", "-")
    parts = lang.split("-")
    canonical = parts[0].lower() + ("-" + parts[1].upper() if len(parts) > 1 else "")
    return canonical if canonical in LOCALES else fallback

PRICE_ATTR = ("data-test", "price")
ROLE_ATTR = "data-price-kind"

SELECTION_ORDER = ("sale", "list")
NEVER_TAKEN = ("struck_through",)


@dataclass(frozen=True)
class PriceNode:
    text: str
    role: str | None
    tag: str


class _Collector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.nodes: list[PriceNode] = []
        self._depth = 0
        self._tag = ""
        self._role: str | None = None
        self._buf: list[str] = []

    def handle_starttag(self, tag, attrs) -> None:
        a = dict(attrs)
        if self._depth:
            self._depth += 1
            return
        if a.get(PRICE_ATTR[0]) == PRICE_ATTR[1]:
            self._depth, self._tag, self._role, self._buf = 1, tag, a.get(ROLE_ATTR), []

    def handle_endtag(self, tag) -> None:
        if not self._depth:
            return
        self._depth -= 1
        if self._depth == 0:
            self.nodes.append(PriceNode("".join(self._buf).strip(), self._role, self._tag))

    def handle_data(self, data) -> None:
        if self._depth:
            self._buf.append(data)


def find_price_nodes(html: str) -> list[PriceNode]:
    c = _Collector()
    c.feed(html)
    return c.nodes


@dataclass(frozen=True)
class Extraction:
    money: Money | None
    price_kind: str | None
    parse_status: str
    raw_text: str | None
    detail: str | None = None

    @property
    def ok(self) -> bool:
        return self.parse_status == ParseStatus.OK.value


def _rank(role: str | None) -> int:
    return SELECTION_ORDER.index(role) if role in SELECTION_ORDER else len(SELECTION_ORDER)


def extract_price(html: str, locale: str) -> Extraction:
    """`locale` is the persona's, used only when the page declares none."""
    locale = page_locale(html, locale)
    nodes = find_price_nodes(html)
    raw = " | ".join(f"[{n.role or 'unmarked'}] {n.text}" for n in nodes) or None

    if not nodes:
        return Extraction(None, None, ParseStatus.NO_MATCH.value, raw, "no price node in capture")

    eligible = [n for n in nodes if n.role not in NEVER_TAKEN]
    if not eligible:
        return Extraction(
            None, None, ParseStatus.NO_MATCH.value, raw,
            "only a struck-through price is present; the charged price is missing",
        )

    parsed = [(n, parse_price(n.text, locale)) for n in eligible]

    for n, r in parsed:
        if r.status is ParseStatus.AMBIGUOUS:
            return Extraction(None, n.role, r.status.value, raw, f"{n.role or 'unmarked'}: {r.reason}")
        if r.status is ParseStatus.MULTIPLE_CANDIDATES:
            return Extraction(None, n.role, r.status.value, raw, f"{n.role or 'unmarked'}: {r.reason}")

    good = [(n, r) for n, r in parsed if r.status is ParseStatus.OK]
    if not good:
        return Extraction(None, None, ParseStatus.NO_MATCH.value, raw, "no eligible node parsed")

    best_rank = min(_rank(n.role) for n, _ in good)
    top = [(n, r) for n, r in good if _rank(n.role) == best_rank]

    if best_rank == len(SELECTION_ORDER) and len(good) > 1:
        return Extraction(
            None, None, ParseStatus.MULTIPLE_CANDIDATES.value, raw,
            "several unmarked price nodes; an unmarked node is taken only when it is the sole candidate",
        )

    distinct = {(r.money.minor_units, r.money.currency) for _, r in top}
    if len(distinct) > 1:
        return Extraction(
            None, top[0][0].role, ParseStatus.MULTIPLE_CANDIDATES.value, raw,
            f"{len(distinct)} different prices both marked {top[0][0].role or 'unmarked'}",
        )

    node, result = top[0]
    return Extraction(result.money, node.role or "unknown", ParseStatus.OK.value, raw)
