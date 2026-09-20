# Price Discrimination in Online Retail — A Measurement Study

**Status:** Phase 0 complete (prototype audited, study reframed, scope decided). Phase 1 not started.
**Last updated:** 2026-09-19
**Type:** Independent measurement study. Not a product, not a startup.

---

## What this is

**A study of how well price discrimination can be measured** — not, currently, a study
of whether it occurs.

The original aim was to measure whether online retailers display different prices to
different consumer profiles. `docs/09-feasibility-assessment.md` evaluated that against
real constraints and found the blockers concentrated entirely in one component: pointing
the instrument at live commercial retailers. Everything else — the instrument, the
statistics, the validation — is within reach.

So the scope moved to the reachable question, which turned out to be the more
interesting one. Detector designs in this area are under systematic pressure to report
findings, and the audit of this project's own prototype demonstrated that concretely: it
reported three false positives from an ordinary price change and missed a 17% targeted
discount entirely. **`PROPOSAL.md`** turns that anecdote into a measured error rate
across a space of realistic conditions, and tests whether replicated observation can
separate real discrimination from retailer A/B testing.

The field study is not abandoned — `docs/01-research-proposal.md` retains its design,
and the active proposal is built to produce the validated instrument it would need.

The method is a **randomized field experiment run against live retail websites**. The
experimenter controls the assignment of consumer profiles ("personas") to page requests,
varying geography, locale, device class, browser, timezone, and visit history on a
factorial grid, then measures the price each profile is shown for an identical SKU at
the same moment.

Because profile assignment is randomized by the experimenter rather than observed after
the fact, this is an experiment rather than an observational study. That distinction
does most of the methodological work — see `docs/02-study-design.md`.

## What this was

This project began as a startup prototype: a Playwright scraper that varied browser
personas and flagged price gaps, intended as the cold-start engine for a consumer
savings product. That prototype lives at `G:\My Drive\Start Up\` and is audited in
`AUDIT-v0-prototype.md`.

The audit found the prototype's measurement layer unsound in ways that biased it
*toward producing findings* — it pooled observations across time rather than comparing
within a moment, tested only one direction, and silently dropped the observations most
likely to carry signal. Those are tolerable bugs in a product that iterates toward
usefulness. They are disqualifying in an instrument meant to produce a number someone
believes.

`docs/00-from-startup-to-research.md` covers what the reframe changes and why.

## Repository map

| Path | What it holds |
|---|---|
| `docs/00-from-startup-to-research.md` | The pivot: what changes under a research frame, and why |
| **`PROPOSAL.md`** | **The active proposal — the scoped study being pursued** |
| `docs/01-research-proposal.md` | Reference design: the unconstrained field study, retained for revival |
| `docs/02-study-design.md` | Factorial design, units of observation, randomization, power |
| `docs/03-measurement-protocol.md` | Instrument requirements, sweep discipline, QC gates |
| `docs/04-analysis-plan.md` | Pre-registered analysis; frozen before collection |
| `docs/05-threats-to-validity.md` | Confounds, how each is detected and mitigated |
| `docs/06-ethics-and-legal.md` | Scraping ethics, IRB posture, proxy sourcing, disclosure |
| `docs/07-project-lifecycle.md` | Phase 0–7 plan with entry and exit criteria |
| `docs/08-literature.md` | Prior work threads; citations to be verified before use |
| `docs/09-feasibility-assessment.md` | What is actually doable under real constraints, and why |
| `AUDIT-v0-prototype.md` | Audit of the startup prototype this study replaces |
| `src/pdd/` | The instrument: `money`, `parsing`, `schema`, `storage`, `detect` |
| `tests/` | 52 tests; the audit's failures are regression tests |
| `scripts/compare_v0.py` | v0 against the corrected detector, side by side |

## Lifecycle at a glance

| Phase | Objective | State |
|---|---|---|
| 0 | Audit prototype, reframe as a study | **Complete** |
| 1 | Build and validate the instrument against a mock storefront | **In progress** — parser, schema, detector done (52 tests); mock storefront next |
| 2 | Pilot study — small N, live targets, estimate variance | Out of scope (field study only) |
| 3 | Power analysis, pre-registration, ethics sign-off | Out of scope (field study only) |
| 4 | Main data collection | Out of scope (field study only) |
| 5 | Analysis per the frozen plan | Not started — simulation analysis under `PROPOSAL.md` |
| 6 | Write-up and dissemination | Not started |
| 7 | Replication package release | Not started |

Full criteria in `docs/07-project-lifecycle.md`. Phases do not start until the prior
phase's exit criteria are met; that ordering is the point of the document.

## The one thing to understand before reading further

Under the startup frame, finding no price discrimination killed the product. Under the
research frame, **a rigorous null result is a finding.** That inversion changes the
incentive from "detect something" to "measure correctly," which is the correction the
audit says this work needs.

## Running it

```
python -m pytest -q          # 52 tests
python scripts/compare_v0.py # v0 vs corrected, on the audit scenarios
```

## Current state

The pure layers of the instrument exist and are tested: the price parser, the schema,
storage, and the detector. Every defect the audit found is covered by a regression test
that reproduces the v0 outcome and asserts the corrected one.

**No data has been collected and nothing has touched a live retailer.** The collection
layer (browser contexts, the bot canary, rate limiting) and the mock storefront are not
built. No document here should be read as reporting a result about any retailer.
