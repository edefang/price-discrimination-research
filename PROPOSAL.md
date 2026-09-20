# Research Proposal

## Detector Design Determines Findings: A Simulation Study of Price Discrimination Measurement

**Author:** Eyong Defang
**Date:** 2026-09-19
**Status:** Proposal. No data generated, no instrument built.
**Scope basis:** `docs/09-feasibility-assessment.md`, Option 1.

---

## 1. Summary

Studies that measure online price discrimination must separate a real effect — the
retailer showing different prices to different consumers — from at least four things
that imitate one: ordinary price changes over time, randomized A/B price experiments,
differential blocking of unusual visitors, and silent parsing errors.

This study asks how well the detector designs used in this area actually do that. It
generates synthetic price panels under known data-generating processes, runs competing
detector designs against them, and measures how often each reports an effect that is not
there and misses one that is. An ablation identifies which design features are
responsible. The instrument is separately validated over real HTTP against a mock
storefront with injected ground truth.

The contribution is methodological: an error-rate characterization of a class of
measurement designs, and a characterization of how much replication — and of which
kind — is needed to distinguish attribute-based pricing from randomized price
experimentation. (An earlier draft claimed the latter as a first; the literature review
found that duplicated control accounts are established practice, and the claim was
narrowed. See `docs/08-literature.md`, section 3.)

## 2. Motivation

This proposal began as a startup. The product was a scraper that varied browser personas
and flagged price gaps, intended to power a consumer savings tool. An audit of that
prototype (`AUDIT-v0-prototype.md`) found four defects, each verified by execution:

- Prices were pooled **across time** rather than compared within a moment. A $100→$115
  retailer price change, with no discrimination present, produced flags against all
  three personas at +6.98%.
- The test was **one-sided**. A persona shown a 17% targeted discount was not detected.
- Blocked observations were **silently dropped**, removing the unusual personas most
  likely to be treated differently.
- The price parser returned wrong numbers without error — `$1,299.00` parsed as `129.0`.

Every one of those defects biases in the same direction: toward reporting a finding.
That is not misconduct. It is what happens when a detector is built to detect, and it is
a pressure any measurement of this kind is under.

Which raises the question this study exists to answer: **how often does a detector of
that class report price discrimination that is not there?** The audit answers it for one
implementation under one scenario. That is an anecdote. This study turns it into a
measured error rate across a space of realistic conditions.

## 3. Research questions

**RQ1 — Error rates.** Under known data-generating processes, what false-positive and
false-negative rates do commonly-used price-discrimination detector designs produce?

**RQ2 — Attribution.** Which design features — within-sweep comparison, a control arm,
two-sided testing, leave-one-out baselines, replication — account for the differences
between designs?

**RQ3 — Mechanism separation.** Can replicated observation reliably distinguish
attribute-based pricing from randomized A/B price assignment, and at what replicate
count *k* does the separation become dependable?

**RQ4 — Degradation.** How do differential blocking and parse corruption degrade each
design, and does either turn a correct design into a misleading one?

RQ3 is the question with the most external value, and the one the literature review
reshaped. Retailer A/B testing produces price variation that has nothing to do with
consumer attributes, and a single-observation design cannot tell the two apart. Hannak
et al. (2014) addressed this by running one treatment twice — a duplicated control —
and reading the twin's inconsistency as the noise floor; Karan et al. (2023) quantify a
chance-level baseline. Replication for noise control is therefore established, not new.

What neither work characterizes is *how much* replication the separation needs, or
whether a single duplicated arm (k = 2 on one treatment) performs as well as replicating
every cell. Those are statistical properties of the design, and simulation — where the
mechanism is known by construction — is the only setting that can answer them.

## 4. Hypotheses

| ID | Hypothesis | Falsified by |
|---|---|---|
| **H1** | v0-class designs (pooled across time, one-sided, filtered failures) produce a false-positive rate substantially above nominal alpha under realistic temporal drift | FPR at or near nominal despite drift |
| **H2** | Within-sweep comparison with a control arm is the single feature accounting for most of the FPR reduction | Ablation shows another feature dominates, or no single feature dominates |
| **H3** | One-sided testing produces a false-negative rate approaching 100% for targeted-discount effects | Discount effects detected despite one-sided testing |
| **H4** | Replication separates discrimination from A/B testing at modest *k*, with classification accuracy rising steeply then plateauing | No *k* within the feasible range achieves dependable separation |

H4 is the hypothesis most likely to fail in an interesting way. If separation requires a
large *k*, that is itself a useful result: it would mean field studies of this kind need
far more observations per cell than they typically collect.

## 5. Method

### 5.1 Simulation

A generator produces synthetic panels with ground truth known by construction. Factors
crossed:

| Factor | Levels |
|---|---|
| True effect | absent / present-premium / present-discount |
| Effect size | a range spanning below to above plausible detection |
| Temporal drift | none / slow / fast / step change mid-sweep |
| A/B testing | absent / present, varying bucket count |
| Blocking | none / uniform / **differential by persona** |
| Parse corruption | none / at rates observed in the audit |
| Measurement noise | a range of within-cell SD |

Differential blocking is called out because it is the mechanism most likely to produce a
confidently wrong null, and it is the one the audit found was invisible to the v0 design.

### 5.2 Detector designs compared

Not arbitrary variants — an ablation lattice from the v0 design to the corrected one, so
each feature's contribution is isolated:

| Design | Within-sweep | Two-sided | Leave-one-out | Control arm | Replicates + G4 | Robust parser |
|---|---|---|---|---|---|---|
| **D0** — v0 as audited | no | no | no | no | no | no |
| D1 | **yes** | no | no | no | no | no |
| D2 | yes | **yes** | no | no | no | no |
| D3 | yes | yes | **yes** | no | no | no |
| D4 | yes | yes | yes | **yes** | no | no |
| D5 | yes | yes | yes | yes | **yes** | no |
| **D6** — corrected | yes | yes | yes | yes | yes | **yes** |

Adding one feature at a time is what makes RQ2 answerable. Two changes from the first
draft of this table, both made during implementation: leave-one-out now precedes the
control arm, because once a control is the reference the leave-one-out step is vacuous
and its contribution could not be measured; and the parser is a seventh, separate step,
because parse quality is orthogonal to statistical design and folding it into D5 would
have confounded two effects.

"Replicates + G4" bundles three things that only exist together: *k* > 1 observations
per cell, the control-stability gate that needs them, and the rule that an incomplete
cohort is reported rather than analysed. D0–D4 observe each cell once and drop failures
silently, as v0 did.

### 5.3 Outcomes

- FPR and FNR per design per condition (RQ1)
- Marginal contribution of each feature, from the D0→D5 lattice (RQ2)
- Classification accuracy for discrimination versus A/B testing, as a function of *k* (RQ3)
- Degradation curves under blocking and parse corruption (RQ4)

Monte Carlo replication per cell, with the count set so simulation error is small
relative to the differences being estimated.

### 5.4 Instrument validation

Simulation establishes statistical properties; it does not establish that the software
works. In parallel, the real instrument runs over actual HTTP against a **local mock
storefront** serving prices as a known function of persona attributes, with scenarios
for no effect, single-factor effect, interaction, targeted discount, locale currency
change, mid-sweep price change, and a bot fallback page.

Acceptance requires the instrument recover ground truth in every scenario, including
correctly reporting *no* effect where none was injected. The v0 prototype never
completed a single successful run, so none of its logic was ever checked against a known
answer; that is the gap this step closes.

## 6. Deliverables

1. Open-source simulator, with the data-generating processes specified and seeded.
2. Measurement instrument meeting requirements R1–R10 of `docs/03-measurement-protocol.md`.
3. Mock storefront and validation fixture suite.
4. Locale-aware price parser with the fixture suite from the audit's failure table.
5. Analysis code reproducing every reported number from seed.
6. Written report answering RQ1–RQ4.
7. Replication package: everything above, runnable from a clean clone.

## 7. What this study does not claim

- Nothing about whether any retailer discriminates on price. No live retail data is
  collected.
- No prevalence or magnitude estimate for real markets.
- No claim about retailer intent.
- Simulation results depend on whether the generating processes resemble reality. That
  assumption is stated, not proven, and is the study's principal limitation.

## 8. Limitations

**The central one:** a simulation can only be as realistic as its generating processes.
If real retail prices move in ways not modeled, the error rates reported here will not
transfer. Mitigations: ground the drift and noise parameters in whatever published
figures the literature review yields; report results across parameter ranges rather than
at a point estimate; and state plainly where a parameter is a guess.

Secondary limitations:

- The detector lattice covers designs reachable from the v0 prototype, not every design
  in the literature.
- Mock-storefront validation proves the instrument works against a cooperative target,
  not against a defended one.
- No external validity for live anti-bot conditions.

## 9. Ethics

No third-party systems are accessed. No personal data is collected. No accounts are
created. The mock storefront runs locally.

The ethics and legal apparatus in `docs/06-ethics-and-legal.md` applies only to the
field study and is retained for that purpose. Under this proposal, none of it is
triggered — which is a substantial part of why this scope was chosen.

## 10. Plan

Mapped onto `docs/07-project-lifecycle.md`. Phases 2–4 of that document, which require
live collection, are not part of this proposal.

| Stage | Work | Estimate |
|---|---|---|
| 1 | Parser + fixtures; schema with `sweep_id`; core instrument | 2–3 weeks |
| 2 | Mock storefront; instrument validation to acceptance | 1–2 weeks |
| 3 | Simulator; detector lattice D0–D5 | 2–3 weeks |
| 4 | Run simulations; analysis | 1 week |
| 5 | Literature review, verifying the citations in `docs/08-literature.md` | in parallel |
| 6 | Write-up and replication package | 1–2 weeks |

**Total: roughly 6–10 weeks part-time.** These are estimates, not measured, and stage 3
is the one most likely to overrun.

## 11. Extension, not a dependency

If a permission-based live target becomes available — a consenting small retailer, a
public pricing API, a site whose terms permit it — a bounded live validation is appended
(`docs/09-feasibility-assessment.md`, Option 2). It is structured so that its absence
does not affect completion of anything above.

## 12. Open questions

- **Institutional affiliation** — unconfirmed. Does not block this proposal; would
  matter for reviving the field study.
- **Drift and noise parameters** — to be grounded in the literature review; currently
  unknown, and will be reported as ranges rather than invented as point values.
- **Publication venue** — undecided. The work stands as a technical report and
  open-source release regardless.
- ~~**Whether prior work has already tested RQ3**~~ — **resolved 2026-09-19, against the
  original claim.** Hannak et al. 2014 used duplicated control accounts; Karan et al.
  2023 quantify a chance baseline. The contribution was narrowed to replication *amount*
  and *kind* before stage 3, as this item required. Recorded in `docs/08-literature.md`.
