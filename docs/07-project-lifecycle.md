# Project Lifecycle

Eight phases. Each has entry criteria, deliverables, and exit criteria. **A phase does
not begin until the previous phase's exit criteria are met.** That ordering is the
document's purpose, not a formality — the v0 prototype's failure was building the
detector before defining the unit of comparison, which is Phase 4 work attempted at
Phase 1.

**Current position: Phase 0 and Phase 1 complete; the simulation study (PROPOSAL.md stages 3–4) is run and reported.** (2026-09-19)

---

## Phase 0 — Audit and reframe

**Objective.** Establish what the prior prototype actually does, and decide the frame.

**Entry.** An existing prototype and a question about whether it works.

**Deliverables**
- [x] Audit of the v0 prototype with empirically verified defects (`../AUDIT-v0-prototype.md`)
- [x] Decision to reframe from product to study (`00-from-startup-to-research.md`)
- [x] Research proposal: questions, hypotheses, estimand, scope (`01-research-proposal.md`)
- [x] Study design (`02-study-design.md`)
- [x] Measurement protocol with instrument requirements (`03-measurement-protocol.md`)
- [x] Draft analysis plan (`04-analysis-plan.md`)
- [x] Threats to validity (`05-threats-to-validity.md`)
- [x] Ethics and legal posture (`06-ethics-and-legal.md`)

**Exit criteria.** Every defect in the audit traces to a requirement or threat that
addresses it. *(Met — see the summary table in `05-threats-to-validity.md`.)*

**Status: COMPLETE.**

---

## Phase 1 — Instrument build and validation

**Objective.** A measurement instrument that recovers known ground truth.

**Entry.** Phase 0 complete.

**Deliverables**
- [x] Mock storefront serving prices as a known function of persona attributes — `../src/pdd/mock_store.py`, eleven scenarios
- [x] Instrument implementing R1–R10 from `03-measurement-protocol.md` — collection layer in `../src/pdd/collect.py`, canary in `canary.py`, QC in `qc.py`
- [x] Schema per section 2 of that document, with `sweep_id` and integer minor units — `../src/pdd/schema.py`
- [x] Price parser with the fixture suite, passing all nine audit formats plus locale variants — `../src/pdd/parsing.py`
- [x] Analysis code: two-sided, leave-one-out, currency-grouped — `../src/pdd/detect.py` *(variance decomposition awaits the simulator)*
- [x] Test suite covering both pure layers — 52 tests passing
- [x] v0-vs-corrected comparison harness — `../scripts/compare_v0.py`

**Exit criteria** *(all met 2026-09-19; `tests/test_e2e_mock.py`, `scripts/validate_mock.py`)*
1. [x] The instrument recovers the injected ground truth in **every** mock scenario,
   including correctly reporting *no effect* where none was injected. *(11/11)*
2. [x] The mid-sweep price-change scenario is caught by G4 rather than reported as
   discrimination. **This is the direct regression test for the v0 fatal flaw.**
3. [x] The targeted-discount scenario is detected. *(v0 could not.)*
4. [x] The bot-page scenario is flagged, not silently analyzed. *(v0 could not.)*
5. [x] A fresh clone runs the full mock validation with one command.
   *(`python scripts/validate_mock.py`; also over a real Chromium with `--playwright`)*

**Status: COMPLETE.**

**Risk.** Building against the mock only proves the logic, not live feasibility. That is
Phase 2's job and the phases must not be merged.

---

## Phase 2 — Pilot study

**Objective.** Find out whether the design survives contact with a live retailer, and
measure the variance needed for power.

**Entry.** Phase 1 exit criteria met.

**Deliverables**
- [ ] One or two retailers, small product set, short collection window
- [ ] Feasible sweep window *W* measured under polite request rates
- [ ] `sigma_within` estimated — the number Phase 3's power calculation needs
- [ ] G4 control-stability pass rate per retailer
- [ ] Bot-detection rate per persona type
- [ ] Selector stability observed over the window
- [ ] Feasibility report with a go / no-go recommendation

**Exit criteria**
1. *W* is short enough that G4 passes at a pre-declared rate, **or** the study is
   declared infeasible against that retailer and the retailer set is revised.
2. `sigma_within` is estimated with enough precision to power Phase 3.
3. Bot-detection rate is low enough that the panel will not be dominated by exclusions.

**This is the phase most likely to kill the study**, and that is a feature. Finding out
here costs weeks; finding out in Phase 5 costs the project. Pilot data is **not** used
to test hypotheses, and is excluded from the main panel.

---

## Phase 3 — Power, pre-registration, ethics gate

**Objective.** Freeze everything that could otherwise be tuned after seeing results.

**Entry.** Phase 2 go recommendation.

**Deliverables**
- [ ] Power simulation using pilot variance; final *k*, N_products, N_sweeps
- [ ] Minimum detectable effect, derived rather than inherited
- [ ] Fractional factorial fraction and generator chosen and documented
- [ ] Retailer and product samples fixed, with selection criteria stated
- [ ] Analysis plan frozen and timestamped
- [ ] Every row in `06-ethics-and-legal.md` section 8 signed off
- [ ] Pre-registration filed with a public registry

**Exit criteria**
1. The analysis plan is registered and immutable; later changes are amendments with
   reasons.
2. Ethics sign-off is complete, including the proxy sourcing decision.
3. No open decision from `01-research-proposal.md` section 8 remains open.

**This phase has no data in it.** Its entire value is that it happens *before* Phase 4.

---

## Phase 4 — Main collection

**Objective.** Execute the registered design.

**Entry.** Phase 3 complete.

**Deliverables**
- [ ] The panel, collected per protocol
- [ ] Per-sweep QC results, including every failure
- [ ] Collection log: incidents, blocks, selector breaks, deviations
- [ ] Instrument health monitoring throughout

**Exit criteria**
1. The registered N is reached, or collection is stopped for a documented reason.
2. QC pass rates are within the bounds Phase 2 predicted.
3. No analysis has been run on the outcome. Operational monitoring only.

**Standing rule: do not look.** Running the analysis mid-collection and continuing until
the result looks right is the failure mode pre-registration exists to prevent. QC
monitoring is permitted; outcome analysis is not.

---

## Phase 5 — Analysis

**Objective.** Execute the frozen plan.

**Entry.** Phase 4 complete.

**Deliverables**
- [ ] Primary analysis (RQ1, RQ2)
- [ ] Secondary mixed-effects model (RQ3)
- [ ] Variance decomposition separating discrimination from A/B testing (RQ4)
- [ ] Exploratory heterogeneity analysis, labeled as such
- [ ] Full exclusion accounting
- [ ] Amendment log, if the plan deviated

**Exit criteria**
1. Every pre-registered analysis is run and reported, including those that found nothing.
2. Exploratory analyses are separated from confirmatory ones in the output.
3. Results are reproducible from the panel by a second execution.

---

## Phase 6 — Write-up and dissemination

**Objective.** Report what was found, including if that is nothing.

**Entry.** Phase 5 complete.

**Deliverables**
- [ ] Paper or report, with the null-reporting standard from `04-analysis-plan.md` section 6
- [ ] Responsible disclosure to named retailers, with response window
- [ ] Limitations section drawn from `05-threats-to-validity.md`, not softened
- [ ] Explicit statement of what was not tested

**Exit criteria**
1. Findings are stated with uncertainty and scope limits.
2. Disclosure window has closed and any responses are incorporated.
3. No claim exceeds what the design can support — in particular, no claim about intent.

---

## Phase 7 — Replication package

**Objective.** Let someone else check the work.

**Entry.** Phase 6 complete.

**Deliverables**
- [ ] Instrument source, with the mock storefront and fixtures
- [ ] Anonymized observation panel
- [ ] Analysis code reproducing every reported number
- [ ] Pre-registration, amendment log, and collection log
- [ ] Documentation sufficient for independent re-collection

**Exit criteria**
1. A third party reproduces the reported numbers from the released panel.
2. The instrument passes mock validation on a clean machine.

---

## Simulation study (PROPOSAL.md stages 3–4) — COMPLETE

Not a lifecycle phase of the field study; the active proposal's substitute for
Phases 2–5. Recorded here so the position is unambiguous.

- [x] Simulator with known data-generating processes — `../src/pdd/simulate.py`
- [x] Detector lattice D0–D6, one feature per step
- [x] Grids A–D run at 200 panels per condition — `../scripts/run_ablation.py`
- [x] Results and figures — `../results/`
- [x] Vectorized D6 checked against the production detector on the same cohorts — `../tests/test_simulate.py`
- [x] Write-up — `../PAPER.md`

---

## Where the v0 prototype sat

Useful as a calibration. The prototype had a scraper, a database, and a detector — the
Phase 1 artifacts. But it had no defined unit of comparison, no validation against
ground truth, no power analysis, no pre-registration, and no ethics review. It was never
successfully run even once.

In lifecycle terms it was a **partial, unvalidated Phase 1 deliverable** that was
positioned as ready to produce findings. The gap between those two things is what the
remaining phases are for.
