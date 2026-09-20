"""End-to-end: the whole pipeline against the mock storefront, every scenario.

These are the Phase 1 exit criteria in `docs/07-project-lifecycle.md`, as tests.
Ground truth is known by construction; the instrument must recover it in both
directions — an effect where one was injected, nothing where none was.
"""

from __future__ import annotations

import pytest

from pdd.mock_store import Scenario
from pdd.validate import validate_scenario


def _fmt(outcome) -> str:
    return "\n".join(f"  {c.name}: {'ok' if c.passed else 'FAIL'} — {c.detail}" for c in outcome.checks)


@pytest.mark.parametrize("scenario", list(Scenario), ids=[s.value for s in Scenario])
def test_instrument_recovers_ground_truth(scenario):
    outcome = validate_scenario(scenario)
    assert outcome.passed, f"{scenario.value}\n{_fmt(outcome)}"


class TestExitCriteria:
    """Named after the lifecycle's Phase 1 exit criteria, so a failure says which one."""

    def test_2_mid_sweep_price_change_is_caught_by_g4_not_reported_as_discrimination(self):
        o = validate_scenario(Scenario.MID_SWEEP_STEP)
        assert not o.qc.gate("G4").passed, o.qc.gate("G4").detail
        assert o.passed, _fmt(o)

    def test_3_targeted_discount_is_detected(self):
        o = validate_scenario(Scenario.TARGETED_DISCOUNT)
        flagged = {f.persona_id: f.direction.value for c in o.cohorts for f in c.findings}
        assert flagged == {"dev=mobile": "discount"}, flagged

    def test_4_bot_page_is_flagged_not_silently_analysed(self):
        o = validate_scenario(Scenario.BOT_PAGE)
        assert not o.qc.gate("G2").passed
        assert all(not c.analysable for c in o.cohorts if c.currency == "USD")

    def test_1_no_effect_reports_nothing(self):
        o = validate_scenario(Scenario.NONE)
        assert o.passed and all(c.findings == () for c in o.cohorts), _fmt(o)


@pytest.mark.slow
def test_playwright_fetcher_end_to_end():
    pytest.importorskip("playwright")
    from pdd.collect import PlaywrightFetcher

    try:
        with PlaywrightFetcher():
            pass
    except Exception as e:  # browser not installed
        pytest.skip(f"chromium unavailable: {e}")

    o = validate_scenario(Scenario.DEVICE_PREMIUM, PlaywrightFetcher, replicates=2)
    assert o.passed, _fmt(o)
