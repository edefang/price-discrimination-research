"""Detector regression tests.

`TestAuditScenarios` is the four scenarios run against the v0 prototype during the audit,
with the outcomes it produced recorded in each docstring. Every one of them must now come
out the other way.
"""

from __future__ import annotations

import pytest

from pdd.detect import (
    CohortStatus,
    Direction,
    MissingCell,
    Observation,
    evaluate_cohort,
    evaluate_panel,
)
from pdd.money import CurrencyMismatch, Money

THRESHOLD = 0.05  # the v0 value, used here only to reproduce its scenarios


def usd(amount: str) -> Money:
    whole, _, frac = amount.partition(".")
    return Money(int(whole) * 100 + int((frac or "0").ljust(2, "0")), "USD")


def obs(sweep, persona, price, product="sku1", control=False, replicate=0):
    return Observation(
        sweep_id=sweep,
        product_id=product,
        persona_id=persona,
        price=price if isinstance(price, Money) else usd(str(price)),
        is_control=control,
        replicate_idx=replicate,
    )


class TestAuditScenarios:
    def test_temporal_price_change_is_not_discrimination(self):
        """v0: flagged all three personas at +6.98%. Defect A1, threat T1.

        The retailer moved $100 -> $115 between runs. No persona was treated
        differently. v0 pooled both runs into one median of 107.5 and reported three
        findings.
        """
        panel = [
            *(obs("sweep-1", p, "100.00") for p in ("us_east", "us_west", "mobile")),
            *(obs("sweep-2", p, "115.00") for p in ("us_east", "us_west", "mobile")),
        ]
        results = evaluate_panel(panel, threshold=THRESHOLD)

        assert len(results) == 2, "one cohort per sweep — never pooled across time"
        assert all(r.status is CohortStatus.COMPLETE for r in results)
        assert all(r.findings == () for r in results)

    def test_targeted_discount_is_detected(self):
        """v0: flagged nothing. Defect A2.

        Mobile is shown 100.00 against a cohort at 120.00 — a 16.7% discount. v0's
        one-sided test could not represent this outcome.
        """
        cohort = [
            obs("sweep-1", "us_east", "120.00"),
            obs("sweep-1", "us_west", "120.00"),
            obs("sweep-1", "mobile", "100.00"),
        ]
        result = evaluate_cohort(cohort, threshold=THRESHOLD)

        assert result.status is CohortStatus.COMPLETE
        flagged = {f.persona_id: f for f in result.findings}
        assert "mobile" in flagged
        assert flagged["mobile"].direction is Direction.DISCOUNT
        assert flagged["mobile"].pct == pytest.approx(-16.67, abs=0.01)

    def test_cross_currency_is_refused_not_compared(self):
        """Defect B2, threat T5. v0 compared raw floats across locales."""
        mixed = [
            obs("sweep-1", "us_east", Money(11000, "USD")),
            obs("sweep-1", "uk", Money(8900, "GBP")),
        ]
        with pytest.raises(CurrencyMismatch):
            evaluate_cohort(mixed, threshold=THRESHOLD)

        # Through the panel entry point they are separate cohorts, never related.
        results = evaluate_panel(mixed, threshold=THRESHOLD)
        assert {r.currency for r in results} == {"USD", "GBP"}
        assert all(r.status is CohortStatus.SINGLE_OBSERVATION for r in results)

    def test_blocked_persona_yields_incomplete_not_a_clean_null(self):
        """v0: printed 'nothing flagged'. Defect B3, threat T4 — bias aimed at the signal."""
        result = evaluate_cohort(
            [obs("sweep-1", "us_east", "100.00"), obs("sweep-1", "us_west", "100.00")],
            threshold=THRESHOLD,
            expected_personas={"us_east", "us_west", "mobile"},
            missing=[MissingCell("mobile", "canary: bot_page")],
        )

        assert result.status is CohortStatus.INCOMPLETE
        assert not result.analysable, "an incomplete cohort must not enter the panel"
        assert result.findings == ()
        assert [m.persona_id for m in result.missing] == ["mobile"]
        assert "bot_page" in result.detail


class TestBaselineExcludesTheObservationUnderTest:
    """Defect A3."""

    def test_two_high_personas_do_not_hide_the_low_one(self):
        """v0: median of (100,120,120) is 120, so nothing flagged in either direction."""
        result = evaluate_cohort(
            [
                obs("s1", "a", "100.00"),
                obs("s1", "b", "120.00"),
                obs("s1", "c", "120.00"),
            ],
            threshold=THRESHOLD,
        )
        flagged = {f.persona_id for f in result.findings}
        assert "a" in flagged

    def test_uniform_cohort_flags_nothing(self):
        result = evaluate_cohort(
            [obs("s1", p, "100.00") for p in ("a", "b", "c")], threshold=THRESHOLD
        )
        assert result.findings == ()


class TestControlArm:
    def test_control_is_the_reference_when_present(self):
        result = evaluate_cohort(
            [
                obs("s1", "control", "100.00", control=True),
                obs("s1", "treat_a", "100.00"),
                obs("s1", "treat_b", "112.00"),
            ],
            threshold=THRESHOLD,
        )
        assert result.reference_kind == "control"
        flagged = {f.persona_id: f for f in result.findings}
        assert set(flagged) == {"treat_b"}
        assert flagged["treat_b"].pct == pytest.approx(12.0)

    def test_control_arm_survives_a_majority_shifted_cohort(self):
        """Where a median baseline would be dragged along, the control holds."""
        result = evaluate_cohort(
            [
                obs("s1", "control", "100.00", control=True),
                obs("s1", "a", "130.00"),
                obs("s1", "b", "130.00"),
                obs("s1", "c", "130.00"),
            ],
            threshold=THRESHOLD,
        )
        assert {f.persona_id for f in result.findings} == {"a", "b", "c"}


class TestStructuralGuards:
    def test_cohort_spanning_sweeps_is_rejected(self):
        with pytest.raises(ValueError, match="spans 2 sweeps"):
            evaluate_cohort(
                [obs("s1", "a", "100.00"), obs("s2", "a", "115.00")], threshold=THRESHOLD
            )

    def test_threshold_is_required(self):
        with pytest.raises(TypeError):
            evaluate_cohort([obs("s1", "a", "100.00")])  # type: ignore[call-arg]

    def test_deviation_is_signed_both_ways(self):
        result = evaluate_cohort(
            [
                obs("s1", "control", "100.00", control=True),
                obs("s1", "high", "110.00"),
                obs("s1", "low", "90.00"),
            ],
            threshold=THRESHOLD,
        )
        by_persona = {f.persona_id: f for f in result.findings}
        assert by_persona["high"].direction is Direction.PREMIUM
        assert by_persona["low"].direction is Direction.DISCOUNT
        assert by_persona["high"].deviation > 0 > by_persona["low"].deviation
