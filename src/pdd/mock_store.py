"""Mock storefront (measurement protocol, section 6).

A local HTTP server that prices products as a *known* function of the request's
persona signals. Each scenario injects one condition the instrument must recover —
or, for the no-effect scenario, must correctly report as nothing.

The v0 prototype was never run against anything with a known answer; it was pointed
at `example.com` and never completed a sweep. This module is what makes "the
instrument recovers ground truth" a testable claim rather than a hope.

Signals the store reads, and what stands in for what:

    device    User-Agent                  as a live site would
    locale    Accept-Language             as a live site would
    history   cookie `pdd_visited`        as a live site would (set on every visit)
    geography header `X-Persona-Geo`      a stand-in — a live site keys on the IP

Only product-page requests count toward `request_count`, which drives the mid-sweep
and A/B scenarios deterministically.
"""

from __future__ import annotations

import random
import threading
from dataclasses import dataclass, replace
from enum import Enum
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from .parsing import LOCALES


class Scenario(str, Enum):
    NONE = "none"
    DEVICE_PREMIUM = "device_premium"
    GEO_PREMIUM = "geo_premium"
    HIST_PREMIUM = "hist_premium"
    TARGETED_DISCOUNT = "targeted_discount"
    INTERACTION = "interaction"
    LOCALE_CURRENCY = "locale_currency"
    STRIKETHROUGH = "strikethrough"
    MID_SWEEP_STEP = "mid_sweep_step"
    BOT_PAGE = "bot_page"
    AB_TEST = "ab_test"


@dataclass(frozen=True)
class Signals:
    dev: str
    loc: str
    geo: str
    hist: str


def signals_from_headers(headers) -> Signals:
    ua = headers.get("User-Agent", "") or ""
    dev = "mobile" if any(t in ua for t in ("Mobile", "iPhone", "Android")) else "desktop"
    accept = headers.get("Accept-Language", "") or "en-US"
    loc = accept.split(",")[0].split(";")[0].strip() or "en-US"
    geo = headers.get("X-Persona-Geo", "") or "us-east"
    cookie = headers.get("Cookie", "") or ""
    hist = "primed" if "pdd_visited=1" in cookie else "cold"
    return Signals(dev=dev, loc=loc, geo=geo, hist=hist)


@dataclass(frozen=True)
class Quote:
    minor_units: int
    currency: str
    locale: str
    kind: str = "sale"
    struck_minor_units: int | None = None
    is_bot_page: bool = False


@dataclass(frozen=True)
class Expectation:
    """Ground truth for one scenario against one persona set."""

    flagged: frozenset[str]
    direction: str | None
    sweep_qc: str                     # "pass" | "fail"
    cohort_status: str                # "complete" | "incomplete"
    missing: frozenset[str]
    currencies: frozenset[str]
    mechanism: str | None
    note: str
    failing_gates: frozenset[str] = frozenset()   # exactly which gates must fail


DEFAULT_PRODUCTS: dict[str, int] = {
    "sku-001": 9_900,        # $99.00
    "sku-002": 129_900,      # $1,299.00  — the four-figure case v0 read as 129.0
    "sku-003": 2_499_900,    # $24,999.00
}

_SYMBOL = {"USD": "$", "EUR": "€", "GBP": "£"}


def format_price(minor_units: int, currency: str, locale: str) -> str:
    """Render the way a storefront in that locale would, so the parser is exercised
    on real conventions rather than on a canonical form."""
    conv = LOCALES[locale]
    whole, frac = divmod(minor_units, 100)
    grouped = f"{whole:,}".replace(",", "\x00").replace("\x00", conv.group_sep)
    number = f"{grouped}{conv.decimal_sep}{frac:02d}"
    symbol = _SYMBOL[currency]
    return f"{symbol}{number}" if locale.startswith("en") else f"{number} {symbol}"


_PAGE = """<!doctype html>
<html lang="{lang}">
<head><meta charset="utf-8"><title>Mock Store - {pid}</title></head>
<body data-store="pdd-mock">
<main id="product" data-product-id="{pid}">
  <h1 data-test="product-title">Product {pid}</h1>
  <div data-test="price-block">
{struck}    <span data-test="price" data-price-kind="{kind}">{price}</span>
  </div>
  <p data-test="availability">In stock</p>
</main>
</body>
</html>
"""

_STRUCK_LINE = '    <s data-test="price" data-price-kind="struck_through">{struck}</s>\n'

# Served with HTTP 200 on purpose. Real challenge pages frequently are, which is why
# the canary must look at structure and cannot lean on the status code.
_CHALLENGE = """<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>Just a moment...</title></head>
<body>
<div id="challenge">
  <h1>Verify you are human</h1>
  <p>Checking your browser before accessing the store.</p>
</div>
</body>
</html>
"""


class MockStore:
    def __init__(
        self,
        scenario: Scenario | str,
        products: dict[str, int] | None = None,
        *,
        step_after: int = 6,
        host: str = "127.0.0.1",
        port: int = 0,
    ) -> None:
        self.scenario = Scenario(scenario)
        self.products = dict(products or DEFAULT_PRODUCTS)
        self.step_after = step_after
        self._host, self._port = host, port
        self._lock = threading.Lock()
        self.request_count = 0
        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    # ------------------------------------------------------------------ lifecycle

    @property
    def base_url(self) -> str:
        return f"http://{self._host}:{self._port}"

    def url_for(self, product_id: str) -> str:
        return f"{self.base_url}/product/{product_id}"

    def start(self) -> str:
        store = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args) -> None:  # keep test output quiet
                pass

            def do_GET(self) -> None:
                path = urlparse(self.path).path
                if path == "/health":
                    return self._send(200, "ok", "text/plain")
                parts = path.strip("/").split("/")
                if len(parts) != 2 or parts[0] != "product" or parts[1] not in store.products:
                    return self._send(404, "not found", "text/plain")
                quote = store.quote(parts[1], signals_from_headers(self.headers))
                body = _CHALLENGE if quote.is_bot_page else store.render(parts[1], quote)
                self._send(200, body, "text/html; charset=utf-8", set_cookie="pdd_visited=1; Path=/")

            def _send(self, status: int, body: str, ctype: str, set_cookie: str | None = None) -> None:
                data = body.encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(data)))
                if set_cookie:
                    self.send_header("Set-Cookie", set_cookie)
                self.end_headers()
                self.wfile.write(data)

        self._server = ThreadingHTTPServer((self._host, self._port), Handler)
        self._port = self._server.server_address[1]
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        return self.base_url

    def stop(self) -> None:
        if self._server:
            self._server.shutdown()
            self._server.server_close()
            self._server = None

    def __enter__(self) -> MockStore:
        self.start()
        return self

    def __exit__(self, *_exc) -> None:
        self.stop()

    # --------------------------------------------------------------------- pricing

    def quote(self, product_id: str, signals: Signals) -> Quote:
        base = self.products[product_id]
        with self._lock:
            self.request_count += 1
            n = self.request_count

        s = self.scenario
        mult, currency, locale = 1.0, "USD", "en-US"

        if s is Scenario.BOT_PAGE and signals.dev == "mobile":
            return Quote(0, "USD", "en-US", kind="unknown", is_bot_page=True)
        if s is Scenario.DEVICE_PREMIUM and signals.dev == "mobile":
            mult = 1.12
        elif s is Scenario.GEO_PREMIUM and signals.geo == "eu-west":
            mult = 1.10
        elif s is Scenario.HIST_PREMIUM and signals.hist == "primed":
            mult = 1.08
        elif s is Scenario.TARGETED_DISCOUNT and signals.dev == "mobile":
            mult = 0.85
        elif s is Scenario.INTERACTION and signals.dev == "mobile" and signals.geo == "us-west":
            mult = 1.15
        elif s is Scenario.LOCALE_CURRENCY and signals.loc == "de-DE":
            currency, locale, mult = "EUR", "de-DE", 0.92
        elif s is Scenario.MID_SWEEP_STEP and n > self.step_after:
            mult = 1.15
        elif s is Scenario.AB_TEST:
            mult = 1.10 if n % 2 == 0 else 1.0     # alternating buckets, no RNG

        if s is Scenario.STRIKETHROUGH:
            return Quote(base, currency, locale, struck_minor_units=round(base * 1.25))
        return Quote(round(base * mult), currency, locale)

    def render(self, product_id: str, quote: Quote) -> str:
        struck = (
            _STRUCK_LINE.format(
                struck=format_price(quote.struck_minor_units, quote.currency, quote.locale)
            )
            if quote.struck_minor_units is not None
            else ""
        )
        return _PAGE.format(
            lang=quote.locale,
            pid=product_id,
            struck=struck,
            kind=quote.kind,
            price=format_price(quote.minor_units, quote.currency, quote.locale),
        )

    # ---------------------------------------------------------------- ground truth

    def expected(self, personas) -> Expectation:
        """What a correct instrument reports for this scenario and this persona set."""

        def ids(pred) -> frozenset[str]:
            return frozenset(p.persona_id for p in personas if not p.is_control and pred(p))

        base = Expectation(
            flagged=frozenset(),
            direction=None,
            sweep_qc="pass",
            cohort_status="complete",
            missing=frozenset(),
            currencies=frozenset({"USD"}),
            mechanism=None,
            note="",
        )
        s = self.scenario
        if s is Scenario.NONE:
            return replace(base, note="no effect injected; the correct report is nothing")
        if s is Scenario.DEVICE_PREMIUM:
            return replace(base, flagged=ids(lambda p: p.dev == "mobile"), direction="premium")
        if s is Scenario.GEO_PREMIUM:
            return replace(base, flagged=ids(lambda p: p.geo == "eu-west"), direction="premium")
        if s is Scenario.HIST_PREMIUM:
            return replace(base, flagged=ids(lambda p: p.hist == "primed"), direction="premium")
        if s is Scenario.TARGETED_DISCOUNT:
            return replace(base, flagged=ids(lambda p: p.dev == "mobile"), direction="discount")
        if s is Scenario.INTERACTION:
            return replace(
                base,
                flagged=ids(lambda p: p.dev == "mobile" and p.geo == "us-west"),
                direction="premium",
                note=(
                    "a two-factor interaction; invisible to a one-factor-at-a-time set, "
                    "where the correct report is nothing"
                ),
            )
        if s is Scenario.LOCALE_CURRENCY:
            return replace(
                base,
                currencies=frozenset({"USD", "EUR"}),
                note="de-DE persona is quoted in EUR; it forms its own cohort and is never compared",
            )
        if s is Scenario.STRIKETHROUGH:
            return replace(
                base, note="every persona sees the same sale price; the struck-through list price must not be taken"
            )
        if s is Scenario.MID_SWEEP_STEP:
            return replace(
                base,
                sweep_qc="fail",
                failing_gates=frozenset({"G4"}),
                note="price steps mid-sweep; G4 must fail rather than the step being read as discrimination",
            )
        if s is Scenario.BOT_PAGE:
            return replace(
                base,
                sweep_qc="fail",
                failing_gates=frozenset({"G1", "G2"}),
                cohort_status="incomplete",
                missing=ids(lambda p: p.dev == "mobile"),
                note="mobile personas are served a challenge page with HTTP 200; the canary must catch it",
            )
        if s is Scenario.AB_TEST:
            return replace(
                base,
                sweep_qc="fail",
                failing_gates=frozenset({"G4"}),
                mechanism="replicate_random",
                note="price is bucketed per request; replicates of the same persona disagree",
            )
        raise AssertionError(f"no expectation defined for {s}")
