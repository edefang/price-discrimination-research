from __future__ import annotations

import random

import pytest

from pdd.collect import HttpFetcher, SweepPlan, Target, _HostThrottle, build_visit_order, run_sweep
from pdd.mock_store import MockStore, Scenario
from pdd.personas import one_factor_at_a_time
from pdd.storage import connect


def plan_for(store, replicates=3, seed=7, personas=None):
    personas = personas or one_factor_at_a_time()
    return SweepPlan(
        sweep_id="s1",
        retailer_id="mock",
        targets=[Target("mock", pid, store.url_for(pid)) for pid in store.products],
        personas=personas,
        replicates=replicates,
        seed=seed,
    )


class TestVisitOrder:
    def test_every_cell_and_replicate_appears_exactly_once(self):
        store = MockStore(Scenario.NONE)
        plan = plan_for(store)
        order = build_visit_order(plan)
        keys = [(v.target.product_id, v.persona.persona_id, v.replicate_idx) for v in order]
        assert len(keys) == len(set(keys)) == 3 * 7 * 3

    def test_control_replicates_are_spread_first_to_last(self):
        """G4 reads temporal drift off the control; it must be sampled across the sweep."""
        order = build_visit_order(plan_for(MockStore(Scenario.NONE)))
        assert order[0].persona.is_control and order[-1].persona.is_control
        positions = [i for i, v in enumerate(order) if v.persona.is_control]
        gaps = [b - a for a, b in zip(positions, positions[1:])]
        assert max(gaps) - min(gaps) <= 2, gaps

    def test_order_is_deterministic_in_the_seed(self):
        store = MockStore(Scenario.NONE)
        a = build_visit_order(plan_for(store, seed=1))
        b = build_visit_order(plan_for(store, seed=1))
        c = build_visit_order(plan_for(store, seed=2))
        key = lambda o: [(v.persona.persona_id, v.target.product_id, v.replicate_idx) for v in o]
        assert key(a) == key(b) and key(a) != key(c)

    def test_no_control_persona_is_tolerated(self):
        personas = [p for p in one_factor_at_a_time() if not p.is_control]
        order = build_visit_order(plan_for(MockStore(Scenario.NONE), personas=personas))
        assert len(order) == 3 * 6 * 3


class TestHttpFetcher:
    def test_primed_persona_makes_two_requests_cold_makes_one(self):
        personas = {p.persona_id: p for p in one_factor_at_a_time()}
        with MockStore(Scenario.NONE) as store, HttpFetcher() as f:
            f.fetch(store.url_for("sku-001"), personas["control"])
            assert store.request_count == 1
            f.fetch(store.url_for("sku-001"), personas["hist=primed"])
            assert store.request_count == 3

    def test_http_error_is_captured_not_raised(self):
        with MockStore(Scenario.NONE) as store, HttpFetcher() as f:
            cap = f.fetch(store.url_for("missing"), one_factor_at_a_time()[0])
        assert cap.status == 404 and cap.error == "http 404"

    def test_connection_failure_is_captured(self):
        with HttpFetcher(timeout=0.5) as f:
            cap = f.fetch("http://127.0.0.1:9/nothing", one_factor_at_a_time()[0])
        assert cap.html is None and cap.error


class TestThrottle:
    def test_sleeps_between_requests_to_the_same_host_only(self):
        slept = []
        t = _HostThrottle(delay=0.5, jitter=0.0, rng=random.Random(0), sleep=slept.append)
        t.wait("http://a.example/x")
        t.wait("http://b.example/y")     # different host: no sleep
        t.wait("http://a.example/z")     # same host: sleeps
        assert len(slept) == 1 and 0 < slept[0] <= 0.5

    def test_zero_delay_never_sleeps(self):
        slept = []
        t = _HostThrottle(delay=0.0, jitter=0.0, rng=random.Random(0), sleep=slept.append)
        for _ in range(3):
            t.wait("http://a.example/x")
        assert slept == []


class TestRunSweep:
    def test_records_every_visit_and_marks_the_sweep(self):
        with MockStore(Scenario.NONE) as store, HttpFetcher() as f:
            conn = connect(":memory:")
            plan = plan_for(store, replicates=2)
            summary = run_sweep(conn, plan, f)
        assert summary.visits == summary.usable == 3 * 7 * 2
        assert summary.bot_pages == summary.parse_failures == summary.fetch_errors == 0
        n = conn.execute("SELECT COUNT(*) FROM observations WHERE sweep_id='s1'").fetchone()[0]
        assert n == summary.visits
        sweep = conn.execute("SELECT ended_at, window_seconds FROM sweeps WHERE sweep_id='s1'").fetchone()
        assert sweep["ended_at"] and sweep["window_seconds"] >= 0

    def test_bot_pages_are_recorded_with_reason(self):
        with MockStore(Scenario.BOT_PAGE) as store, HttpFetcher() as f:
            conn = connect(":memory:")
            summary = run_sweep(conn, plan_for(store, replicates=1), f)
        assert summary.bot_pages == 3      # one mobile persona x three products
        rows = conn.execute(
            "SELECT persona_id, error, parse_status FROM observations WHERE canary_status='bot_page'"
        ).fetchall()
        assert {r["persona_id"] for r in rows} == {"dev=mobile"}
        assert all(r["error"] == "canary: bot_page" and r["parse_status"] == "not_attempted" for r in rows)

    def test_captures_are_written_when_a_dir_is_given(self, tmp_path):
        with MockStore(Scenario.NONE) as store, HttpFetcher() as f:
            conn = connect(":memory:")
            plan = plan_for(store, replicates=1)
            plan.capture_dir = tmp_path
            run_sweep(conn, plan, f)
        files = list((tmp_path / "s1").glob("*.html"))
        assert len(files) == 3 * 7
        ref = conn.execute("SELECT capture_ref FROM observations LIMIT 1").fetchone()[0]
        assert ref and ref.endswith(".html")
