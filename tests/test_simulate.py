"""Simulator tests.

Two kinds: sanity properties each design must have under clean conditions, and a
consistency check that the vectorized D6 agrees with the production detector on the
same cohort — so the fast path used for Monte Carlo cannot quietly diverge from the
code that would analyse real data.
"""

from __future__ import annotations

import numpy as np
import pytest

from pdd.detect import CohortStatus, Observation, evaluate_cohort
from pdd.money import Money
from pdd.simulate import (
    CONTROL,
    DESIGNS,
    LATTICE,
    MECH_ATTRIBUTE,
    MECH_NONE,
    MECH_RANDOM,
    PERSONAS,
    TARGET,
    Condition,
    generate_panel,
    run_design,
    summarize,
)


def sim(cond, design, *, k=3, seed=1, **kw):
    rng = np.random.default_rng(seed)
    panel = generate_panel(cond, n_products=20, n_sweeps=5, k=k, rng=rng)
    return summarize(run_design(panel, DESIGNS[design], **kw), cond)


CLEAN = dict(noise_sd=0.0)


class TestCleanConditions:
    @pytest.mark.parametrize("design", [d.name for d in LATTICE])
    def test_no_effect_no_drift_no_noise_flags_nothing(self, design):
        assert sim(Condition(**CLEAN), design)["false_positive_rate"] == 0.0

    def test_premium_effect_is_found_by_every_design(self):
        for d in LATTICE:
            assert sim(Condition(effect="premium", **CLEAN), d.name)["power_any"] == 1.0, d.name

    def test_discount_is_invisible_to_one_sided_designs_only(self):
        for d in LATTICE:
            p = sim(Condition(effect="discount", **CLEAN), d.name)["power_any"]
            assert p == (0.0 if not d.two_sided else 1.0), (d.name, p)

    def test_leave_one_out_isolates_a_single_shifted_persona_at_n7(self):
        """With seven personas and one shifted, the leave-one-out median is robust and
        D3 attributes correctly. The all-flagged pathology seen in compare_v0.py needs
        a small cohort (three personas) or a majority shift; it is not a property of
        leave-one-out as such. The control arm's value shows under majority shifts."""
        r3 = sim(Condition(effect="premium", **CLEAN), "D3")
        r4 = sim(Condition(effect="premium", **CLEAN), "D4")
        assert r3["misattribution_rate"] == 0.0 and r3["power_strict"] == 1.0
        assert r4["misattribution_rate"] == 0.0 and r4["power_strict"] == 1.0


class TestTemporalDrift:
    def test_between_sweep_drift_only_fools_the_pooled_design(self):
        # Five sweeps at +5% each: the pooled median sits at sweep 3. Sweep 5 is +10.25%
        # and always flags; sweep 4 is +5.00% and sits on the threshold, flagging or not
        # by integer rounding of the price. So D0 lands between 20% and 40%.
        cond = Condition(drift="fast", drift_rate=0.05, **CLEAN)
        fpr = sim(cond, "D0")["false_positive_rate"]
        assert 0.15 <= fpr <= 0.45, fpr
        for name in ("D1", "D2", "D3", "D4", "D5", "D6"):
            assert sim(cond, name)["false_positive_rate"] == 0.0, name

    def test_within_sweep_step_fools_single_observation_designs_and_is_caught_by_g4(self):
        cond = Condition(drift="step", drift_rate=0.15, **CLEAN)
        for name in ("D1", "D2", "D3", "D4"):
            assert sim(cond, name)["false_positive_rate"] > 0.5, name
        r6 = sim(cond, "D6")
        assert r6["abstain_rate"] == 1.0, "control is sampled first and last; the step must fail G4"


class TestBlockingAndParsing:
    def test_differential_blocking_silently_removes_the_target_from_d0_to_d4(self):
        cond = Condition(effect="premium", blocking="differential", block_rate=1.0, **CLEAN)
        for name in ("D0", "D1", "D2", "D3", "D4"):
            r = sim(cond, name)
            assert r["power_any"] == 0.0 and r["abstain_rate"] == 0.0, name
        r6 = sim(cond, "D6")
        assert r6["abstain_rate"] == 1.0

    def test_partial_parse_corruption_creates_false_positives_until_the_parser_refuses(self):
        # Corruption must be partial to bite: if every observation of a product is read
        # at one tenth, the ratios survive and nothing flags. It only touches prices of
        # $1,000 or more (about a fifth of a log-uniform [$10, $3,000] catalog), and at
        # high rates G4 catches much of it — corrupted control replicates look like
        # drift, so D5 abstains rather than false-flags. 10% is the informative level.
        # A single 20-product panel holds only a handful of >= $1,000 products, so the
        # per-panel rate is small and noisy; the claim is D5 > 0 and D6 == 0. The
        # magnitude (about 12% over 200 panels) is Grid C's job, not this test's.
        cond = Condition(parse_corruption=0.1, **CLEAN)
        assert sim(cond, "D5")["false_positive_rate"] > 0.0
        r6 = sim(cond, "D6")
        # D6 refuses the corrupted observation and uses the cell's other replicates;
        # it abstains only when all k are corrupt, which at 10% is rare. Refusal, not
        # abstention, is the mechanism, so the assertion is on the false-positive rate.
        assert r6["false_positive_rate"] == 0.0

    def test_uniform_corruption_preserves_ratios_and_is_invisible(self):
        """A property worth knowing: a parser bug that hits every observation the same
        way is undetectable by any within-cohort design. Only a robust parser helps."""
        assert sim(Condition(parse_corruption=1.0, **CLEAN), "D5")["false_positive_rate"] == 0.0


class TestMechanism:
    def test_attribute_effect_is_classified_with_replicates(self):
        rng = np.random.default_rng(3)
        out = run_design(generate_panel(Condition(effect="premium", **CLEAN), k=3, rng=rng), DESIGNS["D6"])
        assert (out.mechanism == MECH_ATTRIBUTE).all()

    def test_ab_buckets_are_classified_random_at_modest_k(self):
        rng = np.random.default_rng(4)
        out = run_design(generate_panel(Condition(ab_test=True, **CLEAN), k=5, rng=rng), DESIGNS["D6"])
        analysed = ~out.abstain
        assert analysed.any()
        assert (out.mechanism[analysed] == MECH_RANDOM).mean() > 0.9

    def test_single_replicate_cannot_classify(self):
        rng = np.random.default_rng(5)
        out = run_design(generate_panel(Condition(**CLEAN), k=1, rng=rng), DESIGNS["D6"])
        assert (out.mechanism == -1).all()

    def test_clean_cohort_is_none(self):
        rng = np.random.default_rng(6)
        out = run_design(generate_panel(Condition(**CLEAN), k=3, rng=rng), DESIGNS["D6"])
        assert (out.mechanism == MECH_NONE).all()


class TestAgreementWithProductionDetector:
    """The vectorized D6 and `pdd.detect.evaluate_cohort` must flag the same personas."""

    @pytest.mark.parametrize("effect", ["none", "premium", "discount"])
    def test_same_cohort_same_verdict(self, effect):
        rng = np.random.default_rng(11)
        panel = generate_panel(Condition(effect=effect, noise_sd=0.003), n_products=5, n_sweeps=2, k=3, rng=rng)
        out = run_design(panel, DESIGNS["D6"], threshold=0.05)

        for s in range(2):
            for p in range(5):
                obs = [
                    Observation(f"s{s}", f"p{p}", PERSONAS[j], Money(int(panel.observed_robust[s, p, j, r]), "USD"),
                                replicate_idx=r, is_control=(j == CONTROL))
                    for j in range(len(PERSONAS)) for r in range(3)
                    if not np.isnan(panel.observed_robust[s, p, j, r])
                ]
                res = evaluate_cohort(obs, threshold=0.05, expected_personas=set(PERSONAS))
                assert res.status is CohortStatus.COMPLETE
                prod_flagged = {f.persona_id for f in res.findings}
                sim_flagged = set()
                if out.target_flagged[s, p]:
                    sim_flagged.add(PERSONAS[TARGET])
                assert (PERSONAS[TARGET] in prod_flagged) == out.target_flagged[s, p]
                assert bool(prod_flagged - {PERSONAS[TARGET]}) == bool(out.nontarget_flagged[s, p])
