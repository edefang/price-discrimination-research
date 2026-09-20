"""Collection: fetchers and the sweep runner (requirements R6, R8, R9, R10).

Two fetchers implement one protocol. `HttpFetcher` is plain `urllib` and is what the
mock-storefront validation runs on, so the full pipeline is exercised without a
browser. `PlaywrightFetcher` is the real thing: one browser process, a fresh context
per observation, explicit wait for the price element.

The sweep runner owns the visit order. Two properties of that order carry weight:

  * it is randomly permuted per sweep from a recorded seed, so persona is not
    confounded with position (the v0 loop visited personas in a fixed order);
  * the control persona's replicates are placed at evenly spaced positions across
    the sweep rather than shuffled in with the rest. G4 asks whether the control
    price moved *during* the sweep, and it can only answer that if the control was
    sampled throughout.
"""

from __future__ import annotations

import http.cookiejar
import random
import re
import sqlite3
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol
from urllib.parse import urlparse

from . import canary as canary_mod
from .canary import CanaryRule, CanaryStatus
from .extract import extract_price
from .personas import Persona
from .storage import open_sweep, record


@dataclass(frozen=True)
class Capture:
    html: str | None
    status: int | None
    load_ms: int
    error: str | None = None


class Fetcher(Protocol):
    def fetch(self, url: str, persona: Persona) -> Capture: ...


# ------------------------------------------------------------------- HTTP fetcher


class HttpFetcher:
    """Stdlib fetch with a fresh cookie jar per observation.

    A `primed` persona visits the page once before the measured visit, keeping the
    cookies it was handed — which is what "has been here before" means to a server.
    """

    def __init__(self, timeout: float = 10.0) -> None:
        self.timeout = timeout

    def __enter__(self) -> HttpFetcher:
        return self

    def __exit__(self, *_exc) -> None:
        pass

    def fetch(self, url: str, persona: Persona) -> Capture:
        jar = http.cookiejar.CookieJar()
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
        headers = persona.http_headers()

        def get() -> tuple[str, int]:
            req = urllib.request.Request(url, headers=headers)
            with opener.open(req, timeout=self.timeout) as resp:
                return resp.read().decode("utf-8", "replace"), resp.status

        t0 = time.perf_counter()
        try:
            if persona.hist == "primed":
                get()
            html, status = get()
            return Capture(html, status, int((time.perf_counter() - t0) * 1000))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace") if e.fp else None
            return Capture(body, e.code, int((time.perf_counter() - t0) * 1000), f"http {e.code}")
        except Exception as e:  # network errors, timeouts
            return Capture(None, None, int((time.perf_counter() - t0) * 1000), f"{type(e).__name__}: {e}")


# ------------------------------------------------------------- Playwright fetcher


class PlaywrightFetcher:
    """One Chromium process for the whole sweep; a new context per observation.

    Contexts are the isolation boundary — separate cookies, storage, and cache — which
    is what a persona needs. The v0 prototype launched and closed an entire browser
    per (persona x product); at study scale that is tens of minutes of overhead per
    sweep for no isolation gain.
    """

    def __init__(
        self,
        wait_selector: str = '[data-test="price"]',
        timeout_ms: int = 15_000,
        headless: bool = True,
    ) -> None:
        self.wait_selector = wait_selector
        self.timeout_ms = timeout_ms
        self.headless = headless
        self._pw = None
        self._browser = None

    def __enter__(self) -> PlaywrightFetcher:
        from playwright.sync_api import sync_playwright

        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(headless=self.headless)
        return self

    def __exit__(self, *_exc) -> None:
        if self._browser:
            self._browser.close()
        if self._pw:
            self._pw.stop()

    def fetch(self, url: str, persona: Persona) -> Capture:
        from playwright.sync_api import TimeoutError as PWTimeout

        assert self._browser is not None, "use as a context manager"
        context = self._browser.new_context(**persona.context_options())
        t0 = time.perf_counter()
        status: int | None = None
        error: str | None = None
        try:
            page = context.new_page()
            if persona.hist == "primed":
                page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
            resp = page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
            status = resp.status if resp else None
            try:
                # Explicit wait for the price element, not for network idle: on
                # client-rendered storefronts the price node is often absent at
                # network idle, which produced spurious failures in v0.
                page.wait_for_selector(self.wait_selector, timeout=self.timeout_ms)
            except PWTimeout:
                error = "wait_for_selector timeout"   # capture anyway; the canary decides
            html = page.content()
            return Capture(html, status, int((time.perf_counter() - t0) * 1000), error)
        except Exception as e:
            return Capture(None, status, int((time.perf_counter() - t0) * 1000), f"{type(e).__name__}: {e}")
        finally:
            context.close()


# -------------------------------------------------------------------- planning


@dataclass(frozen=True)
class Target:
    retailer_id: str
    product_id: str
    url: str
    canary_rule: CanaryRule = canary_mod.DEFAULT_RULE


@dataclass(frozen=True)
class Visit:
    target: Target
    persona: Persona
    replicate_idx: int


@dataclass
class SweepPlan:
    sweep_id: str
    retailer_id: str
    targets: list[Target]
    personas: list[Persona]
    replicates: int
    seed: int
    delay_seconds: float = 0.0
    jitter_seconds: float = 0.0
    capture_dir: Path | None = None
    extra: dict = field(default_factory=dict)


def build_visit_order(plan: SweepPlan) -> list[Visit]:
    rng = random.Random(plan.seed)
    controls = [
        Visit(t, p, r)
        for t in plan.targets
        for p in plan.personas
        if p.is_control
        for r in range(plan.replicates)
    ]
    others = [
        Visit(t, p, r)
        for t in plan.targets
        for p in plan.personas
        if not p.is_control
        for r in range(plan.replicates)
    ]
    rng.shuffle(others)
    rng.shuffle(controls)

    total = len(controls) + len(others)
    n_c = len(controls)
    if n_c == 0:
        return others
    slots = {0} if n_c == 1 else {round(i * (total - 1) / (n_c - 1)) for i in range(n_c)}

    order: list[Visit] = []
    ci = oi = 0
    for pos in range(total):
        if ci < n_c and pos in slots:
            order.append(controls[ci])
            ci += 1
        elif oi < len(others):
            order.append(others[oi])
            oi += 1
        else:
            order.append(controls[ci])
            ci += 1
    order.extend(controls[ci:])   # only if slots collided
    return order


# --------------------------------------------------------------------- running


@dataclass
class SweepSummary:
    sweep_id: str
    visits: int
    usable: int
    bot_pages: int
    parse_failures: int
    fetch_errors: int
    duration_s: float


class _HostThrottle:
    def __init__(self, delay: float, jitter: float, rng: random.Random, sleep) -> None:
        self.delay, self.jitter, self.rng, self.sleep = delay, jitter, rng, sleep
        self.last: dict[str, float] = {}

    def wait(self, url: str) -> None:
        host = urlparse(url).netloc
        if host in self.last and self.delay > 0:
            due = self.last[host] + self.delay + self.rng.uniform(0, self.jitter)
            remaining = due - time.monotonic()
            if remaining > 0:
                self.sleep(remaining)
        self.last[host] = time.monotonic()


def run_sweep(
    conn: sqlite3.Connection,
    plan: SweepPlan,
    fetcher: Fetcher,
    *,
    sleep=time.sleep,
) -> SweepSummary:
    started = datetime.now(timezone.utc)
    open_sweep(conn, plan.sweep_id, plan.retailer_id, started.isoformat(), plan.seed)
    throttle = _HostThrottle(plan.delay_seconds, plan.jitter_seconds, random.Random(plan.seed ^ 0xC0FFEE), sleep)
    if plan.capture_dir:
        (plan.capture_dir / plan.sweep_id).mkdir(parents=True, exist_ok=True)

    order = build_visit_order(plan)
    counts = dict(usable=0, bot=0, parse=0, fetch=0)

    for i, v in enumerate(order):
        throttle.wait(v.target.url)
        cap = fetcher.fetch(v.target.url, v.persona)
        observed_at = datetime.now(timezone.utc).isoformat()

        capture_ref = None
        if plan.capture_dir and cap.html is not None:
            safe = re.sub(r"[^A-Za-z0-9=._-]+", "_", v.persona.persona_id)   # "tz=Europe/Berlin"
            path = plan.capture_dir / plan.sweep_id / f"{i:05d}_{safe}_{v.target.product_id}_r{v.replicate_idx}.html"
            path.write_text(cap.html, encoding="utf-8")
            capture_ref = str(path)

        row = dict(
            sweep_id=plan.sweep_id,
            replicate_idx=v.replicate_idx,
            retailer_id=v.target.retailer_id,
            product_id=v.target.product_id,
            persona_id=v.persona.persona_id,
            is_control=int(v.persona.is_control),
            factor_geo=v.persona.geo,
            factor_dev=v.persona.dev,
            factor_loc=v.persona.loc,
            factor_tz=v.persona.tz,
            factor_hist=v.persona.hist,
            observed_at=observed_at,
            http_status=cap.status,
            load_ms=cap.load_ms,
            capture_ref=capture_ref,
        )

        if cap.html is None:
            counts["fetch"] += 1
            record(conn, parse_status="not_attempted", canary_status="unknown", error=cap.error or "no capture", **row)
            continue

        status = canary_mod.check(cap.html, v.target.canary_rule)
        if status is CanaryStatus.BOT_PAGE:
            counts["bot"] += 1
            record(conn, parse_status="not_attempted", canary_status=status.value, error="canary: bot_page", **row)
            continue

        ex = extract_price(cap.html, v.persona.loc)
        if ex.ok:
            counts["usable"] += 1
            record(
                conn,
                price_minor_units=ex.money.minor_units,
                currency=ex.money.currency,
                price_kind=ex.price_kind,
                raw_price_text=ex.raw_text,
                parse_status="ok",
                canary_status=status.value,
                error=cap.error,
                **row,
            )
        else:
            counts["parse"] += 1
            record(
                conn,
                raw_price_text=ex.raw_text,
                parse_status=ex.parse_status,
                parse_detail=ex.detail,
                canary_status=status.value,
                error=cap.error or ex.detail,
                **row,
            )

    ended = datetime.now(timezone.utc)
    conn.execute(
        "UPDATE sweeps SET ended_at = ?, window_seconds = ? WHERE sweep_id = ?",
        (ended.isoformat(), int((ended - started).total_seconds()), plan.sweep_id),
    )
    conn.commit()
    return SweepSummary(
        plan.sweep_id, len(order), counts["usable"], counts["bot"], counts["parse"], counts["fetch"],
        (ended - started).total_seconds(),
    )
