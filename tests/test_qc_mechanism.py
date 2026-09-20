from __future__ import annotations

import pytest

from pdd.detect import Observation
from pdd.mechanism import Mechanism, decompose
from pdd.money import Money
from pdd.qc import run_gates
from pdd.storage import connect, open_sweep, record

PERSONAS = {"control", "a", "b"}
PRODUCTS = {"p1"}


@pytest.fixture
def conn():
    c = connect(":memory:")
    open_sweep(c, "s1", "r", "2026-09-19T00:00:00Z", seed=1)
    yield c
    c.close()


def row(persona, price, *, replicate=0, control=False, **over):
    base = dict(
        sweep_id="s1", replicate_idx=replicate, retailer_id="r", product_id="p1",
        persona_id=persona, is_control=int(control), observed_at="2026-09-19T00:00:01Z",
        price_minor_units=price, currency="USD" if price is not None else None,
        parse_status="ok" if price is not None else "no_match", canary_status="real_page",
    )
    base.update(over)
    return base


def clean(conn, k=2):
    for r in range(k):
        record(conn, **row("control", 10000, replicate=r, control=True))
        record(conn, **row("a", 10000, replicate=r))
        record(conn, **row("b", 11000, replicate=r))


class TestGates:
    def test_all_pass_on_a_clean_sweep(self, conn):
        clean(conn)
        qc = run_gates(conn, "s1", products=PRODUCTS, personas=PERSONAS)
        assert qc.passed, qc.summary()
        assert conn.execute("SELECT qc_status FROM sweeps").fetchone()[0] == "pass"

    def test_g1_fails_on_a_missing_cell(self, conn):
        record(conn, **row("control", 10000, control=True))
        record(conn, **row("a", 10000))
        qc = run_gates(conn, "s1", products=PRODUCTS, personas=PERSONAS)
        assert not qc.gate("G1").passed and "p1/b" in qc.gate("G1").detail

    def test_g2_fails_on_a_bot_page(self, conn):
        clean(conn)
        record(conn, **row("b", None, replicate=5, canary_status="bot_page", parse_status="not_attempted"))
        qc = run_gates(conn, "s1", products=PRODUCTS, personas=PERSONAS)
        assert not qc.gate("G2").passed and "b x1" in qc.gate("G2").detail

    def test_g3_fails_on_an_ambiguous_parse(self, conn):
        clean(conn)
        record(conn, **row("a", None, replicate=5, parse_status="ambiguous"))
        qc = run_gates(conn, "s1", products=PRODUCTS, personas=PERSONAS)
        assert not qc.gate("G3").passed

    def test_g4_fails_when_the_control_moved(self, conn):
        record(conn, **row("control", 10000, replicate=0, control=True))
        record(conn, **row("control", 11500, replicate=1, control=True))
        record(conn, **row("a", 10000)); record(conn, **row("b", 10000))
        qc = run_gates(conn, "s1", products=PRODUCTS, personas=PERSONAS)
        assert not qc.gate("G4").passed and "10000->11500" in qc.gate("G4").detail
        assert conn.execute("SELECT qc_status FROM sweeps").fetchone()[0] == "fail"

    def test_g4_fails_when_there_is_no_control(self, conn):
        record(conn, **row("a", 10000)); record(conn, **row("b", 10000))
        assert not run_gates(conn, "s1", products=PRODUCTS, personas={"a", "b"}).gate("G4").passed


def obs(persona, prices):
    return [Observation("s1", "p1", persona, Money(p, "USD"), replicate_idx=i) for i, p in enumerate(prices)]


class TestMechanism:
    def test_stable_replicates_with_a_persona_effect(self):
        d = decompose(obs("control", [100, 100, 100]) + obs("a", [100, 100, 100]) + obs("b", [112, 112, 112]), tol=0.01)
        assert d.mechanism is Mechanism.ATTRIBUTE_CORRELATED and d.within_var == 0.0

    def test_random_buckets_across_replicates(self):
        d = decompose(obs("control", [100, 110, 100, 110]) + obs("a", [110, 100, 110, 100]) + obs("b", [100, 110, 110, 100]), tol=0.01)
        assert d.mechanism is Mechanism.REPLICATE_RANDOM and d.instability_rate == 1.0

    def test_no_variation(self):
        d = decompose(obs("control", [100, 100]) + obs("a", [100, 100]) + obs("b", [100, 100]), tol=0.01)
        assert d.mechanism is Mechanism.NO_VARIATION

    def test_single_replicate_cannot_classify(self):
        d = decompose(obs("control", [100]) + obs("a", [112]), tol=0.01)
        assert d.mechanism is Mechanism.INSUFFICIENT_REPLICATES

    def test_rounding_noise_below_tol_is_not_instability(self):
        d = decompose(obs("control", [10000, 10001, 10000]) + obs("a", [10000, 10000, 10001]), tol=0.01)
        assert d.unstable_cells == 0 and d.mechanism is Mechanism.NO_VARIATION
