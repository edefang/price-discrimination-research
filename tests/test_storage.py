"""Schema and storage tests.

The schema is where several audit defects are made structurally impossible rather than
merely discouraged. These tests confirm the constraints actually reject the bad rows.
"""

from __future__ import annotations

import sqlite3

import pytest

from pdd.detect import CohortStatus, evaluate_cohort
from pdd.storage import connect, cohort_keys, load_cohort, open_sweep, record


@pytest.fixture
def conn():
    c = connect(":memory:")
    open_sweep(c, "sweep-1", "retailer-a", "2026-09-19T12:00:00Z", seed=1234)
    yield c
    c.close()


def base_row(**overrides):
    row = dict(
        sweep_id="sweep-1",
        replicate_idx=0,
        retailer_id="retailer-a",
        product_id="sku1",
        persona_id="control",
        is_control=1,
        observed_at="2026-09-19T12:00:01Z",
        price_minor_units=10000,
        currency="USD",
        parse_status="ok",
        canary_status="real_page",
    )
    row.update(overrides)
    return row


class TestSchemaConstraints:
    def test_observation_requires_a_sweep_id(self, conn):
        """R1. An observation without a sweep has no comparison unit."""
        row = base_row()
        del row["sweep_id"]
        with pytest.raises(sqlite3.IntegrityError):
            record(conn, **row)

    def test_sweep_id_must_reference_a_real_sweep(self, conn):
        with pytest.raises(sqlite3.IntegrityError):
            record(conn, **base_row(sweep_id="never-opened"))

    def test_price_without_currency_is_rejected(self, conn):
        """Defect B2 — v0 stored a price and ignored its currency."""
        with pytest.raises(sqlite3.IntegrityError):
            record(conn, **base_row(currency=None))

    def test_parse_ok_without_a_price_is_rejected(self, conn):
        """A row claiming a successful parse while holding nothing."""
        with pytest.raises(sqlite3.IntegrityError):
            record(conn, **base_row(price_minor_units=None))

    def test_unknown_status_values_are_rejected(self, conn):
        with pytest.raises(sqlite3.IntegrityError):
            record(conn, **base_row(parse_status="probably_fine"))
        with pytest.raises(sqlite3.IntegrityError):
            record(conn, **base_row(canary_status="looked_ok"))

    def test_duplicate_cell_is_rejected(self, conn):
        record(conn, **base_row())
        with pytest.raises(sqlite3.IntegrityError):
            record(conn, **base_row())

    def test_failed_observation_may_omit_the_price(self, conn):
        """Failures must still be recordable — that is how R5 is possible at all."""
        rowid = record(
            conn,
            **base_row(
                persona_id="mobile",
                is_control=0,
                price_minor_units=None,
                currency=None,
                parse_status="no_match",
                canary_status="bot_page",
                error="challenge page served",
            ),
        )
        assert rowid > 0


class TestLoadCohort:
    def test_failures_come_back_alongside_prices(self, conn):
        """Defect B3: v0's query dropped them and the caller never knew."""
        record(conn, **base_row(persona_id="control", is_control=1))
        record(conn, **base_row(persona_id="us_west", is_control=0))
        record(
            conn,
            **base_row(
                persona_id="mobile",
                is_control=0,
                price_minor_units=None,
                currency=None,
                parse_status="no_match",
                canary_status="bot_page",
                error="challenge page served",
            ),
        )

        usable, missing = load_cohort(conn, "sweep-1", "sku1", "USD")

        assert {o.persona_id for o in usable} == {"control", "us_west"}
        assert [(m.persona_id, m.reason) for m in missing] == [("mobile", "canary: bot_page")]

    def test_a_blocked_persona_makes_the_cohort_incomplete_end_to_end(self, conn):
        """The full path: storage -> detection -> not analysable."""
        record(conn, **base_row(persona_id="control", is_control=1))
        record(conn, **base_row(persona_id="us_west", is_control=0))
        record(
            conn,
            **base_row(
                persona_id="mobile",
                is_control=0,
                price_minor_units=None,
                currency=None,
                parse_status="no_match",
                canary_status="bot_page",
                error="challenge page served",
            ),
        )

        usable, missing = load_cohort(conn, "sweep-1", "sku1", "USD")
        result = evaluate_cohort(
            usable,
            threshold=0.05,
            expected_personas={"control", "us_west", "mobile"},
            missing=missing,
        )

        assert result.status is CohortStatus.INCOMPLETE
        assert not result.analysable
        assert result.findings == ()

    def test_ambiguous_parse_is_treated_as_missing_not_as_a_price(self, conn):
        """R7 — an ambiguous parse is not a measurement."""
        record(conn, **base_row(persona_id="control", is_control=1))
        record(
            conn,
            **base_row(
                persona_id="eu",
                is_control=0,
                price_minor_units=None,
                currency=None,
                parse_status="ambiguous",
                error="'1,299': 3 fractional digits, expected 1..2 for EUR",
            ),
        )
        usable, missing = load_cohort(conn, "sweep-1", "sku1", "USD")
        assert [o.persona_id for o in usable] == ["control"]
        assert missing[0].persona_id == "eu"

    def test_cohort_keys_enumerates_the_panel(self, conn):
        record(conn, **base_row(persona_id="control"))
        record(conn, **base_row(persona_id="us_west", is_control=0, product_id="sku2"))
        assert list(cohort_keys(conn)) == [
            ("sweep-1", "sku1", "USD"),
            ("sweep-1", "sku2", "USD"),
        ]
