# Feasibility Assessment — What Can Actually Be Done

**Date:** 2026-09-19
**Purpose:** Evaluate the design in `02-study-design.md` against real constraints and
recommend a version that can be finished.

The design documents describe the study one would run with a lab, a budget, counsel, and
a year. This document asks a narrower question: **what can one person, working
part-time, with no budget and no legal cover, actually complete?**

The answer is more than it might appear — but not the part everyone assumes.

---

## 1. Constraints

| Constraint | Status | Consequence |
|---|---|---|
| Personnel | One person, part-time | No coverage for a long-running collection; anything requiring daily attention for months will lapse |
| Budget | Assumed near zero | Residential proxies out (also ruled out on ethics); a few cheap regional VPS instances are affordable if needed |
| Institutional affiliation | **Open variable** — not confirmed | Determines IRB access, library access, and whether the work carries institutional cover |
| Legal counsel | None available | The highest-consequence gap. Live scraping of named commercial retailers without counsel puts personal exposure on one individual |
| Infrastructure | One Windows laptop; Google Drive | No always-on host; scheduled sweeps would run only when the machine is awake, which biases sampling by time-of-day |
| Time horizon | Months, part-time, alongside a job search | Multi-month daily panels are not realistic |
| Target environment | Major retailers are heavily defended | A solo scraper gets blocked. Threat T3 dominates everything downstream |

**On affiliation:** this is worth resolving because it moves several rows. If there is a
current institutional affiliation, IRB consultation and library access become available
and the ethics gate in `06-ethics-and-legal.md` gets much easier to close. The
recommendation below is deliberately chosen to work either way, so this does not block
starting.

---

## 2. Component-by-component evaluation

Every element of the full design, assessed independently.

| Component | Cost | Feasible solo? | Notes |
|---|---|---|---|
| Sweep discipline, `sweep_id`, within-sweep comparison | Free | **Yes** | Pure software |
| Control arm / control persona | Free | **Yes** | Pure software |
| Two-sided test, leave-one-out baseline | Free | **Yes** | Pure software |
| Replicates (*k* per cell) | Free | **Yes** | More requests, but only matters against live targets |
| Locale-aware price parser + fixtures | Free | **Yes** | Bounded, testable, a weekend of work |
| DEV factor (desktop / mobile) | Free | **Yes** | Browser context setting |
| LOC factor (locale) | Free | **Yes** | Browser context setting |
| TZ factor (timezone) | Free | **Yes** | Browser context setting |
| HIST factor (cold / primed) | Free | **Yes** | Context reuse |
| Bot-page canary | Free | **Yes** | Pure software |
| Mock storefront + injected ground truth | Free | **Yes** | The highest-value item on this list |
| **GEO factor (apparent IP location)** | ~$15–40/mo | **Marginal** | Cheap VPS regions are affordable, but datacenter IPs are detectable and carry the T10 reputation confound; ethical residential proxies are unaffordable |
| **Live retail targets** | Free in money | **No** | Anti-bot defeats it, and legal exposure lands on one uninsured individual |
| Pilot variance estimate (`sigma_within`) | — | **Blocked** | Requires live collection |
| Power analysis | — | **Blocked** | Requires pilot variance |
| Pre-registration of a field study | — | **Blocked** | Requires power analysis |
| IRB determination | — | **Unknown** | Depends on affiliation |
| Legal review | — | **No** | Not obtainable |

**The pattern is the finding of this assessment.** Every blocker is concentrated in one
place: pointing the instrument at real commercial retailers. Everything else — the entire
methodological apparatus, the instrument, the validation, the statistics — is free and
fully within reach.

That suggests the study should be built around what is reachable rather than around the
one component that is not.

---

## 3. Options

### Option 1 — Methods and simulation study

**Claim:** detector *design* determines what a price-discrimination study finds, and
commonly-built designs manufacture findings under ordinary conditions.

**Method:** a simulator generating synthetic price panels under known data-generating
processes — no effect, attribute effect, A/B testing, temporal drift, differential
blocking, parse corruption. Competing detector designs, including the v0-class design
and the corrected design, are run against them, and false-positive and false-negative
rates are measured. An ablation isolates which design features account for the
differences. Separately, the real instrument is validated against a mock storefront over
actual HTTP with injected ground truth.

| | |
|---|---|
| Cost | $0 |
| Legal exposure | None |
| Ethics exposure | None — no third-party systems touched |
| Completable solo | **Yes** |
| Estimated effort | 6–10 weeks part-time *(estimate, not measured)* |
| Blocked by anything | No |
| Produces a real contribution | Yes — see below |

**Why this is not a consolation prize.** The audit already demonstrated, on one concrete
implementation, that a v0-class detector reports three false positives from an ordinary
$100→$115 price change and misses a 17% targeted discount entirely. That is a single
anecdote. Turning it into a characterized error rate across a space of realistic
conditions is a genuine methodological result, and it bears directly on how existing
measurement findings in this area should be read. The A/B-versus-discrimination
separation (RQ4 in `01-research-proposal.md`) has never been tested here at all, and
simulation is the only setting where its ground truth is knowable.

**What it cannot claim:** anything about actual retailer behavior. It is a study of
measurement, not of prices.

### Option 2 — Option 1 plus bounded live validation

Option 1, plus a small live component against targets chosen for permissibility rather
than interest:

- sites whose `robots.txt` and terms permit automated access;
- retailers exposing a public pricing API, where terms allow;
- **a small e-commerce operator who consents** — the strongest version, because the
  operator can state whether they personalize, giving real-world ground truth that no
  amount of scraping can provide. Hard to obtain, disproportionately valuable if obtained.

| | |
|---|---|
| Added cost | $0–40 |
| Added exposure | Low, if and only if targets are permission-based |
| Completable solo | Yes, but the live part may fail to materialize |
| Added effort | +3–5 weeks *(estimate)* |

**Structure this so the live part cannot sink the project.** It is a stretch goal
appended to a finished Option 1, never a dependency.

### Option 3 — The full field study

The design as written in `02-study-design.md`.

**Not feasible under current constraints.** Requires: sustained infrastructure for a
multi-month panel; a proxy solution that is both ethical and affordable, which currently
does not exist at this budget; counsel; and an ethics determination. Documented here so
the decision is recorded rather than quietly abandoned, and so it can be revived if
affiliation or funding appear.

---

## 4. Recommendation

**Commit to Option 1. Treat Option 2's live component as a stretch goal that does not
gate completion.**

Reasoning:

1. **It is the only track that can definitely be finished.** Everything it needs is
   already available. Nothing in it is blocked on money, permission, or another person.
2. **Its contribution is real and currently unserved.** Characterizing the error rates
   of detector designs — and testing whether replicates separate A/B testing from
   discrimination — is a question simulation is uniquely suited to answer, because
   ground truth is only knowable when you generate it.
3. **The expensive part is already done.** The audit is the motivating section. The
   design documents are the method. What remains is the simulator, the instrument, and
   the analysis.
4. **It preserves the field study rather than abandoning it.** Option 1 produces exactly
   the validated instrument Option 3 would need. If affiliation or funding appear, the
   field study starts from a working, characterized measurement tool instead of from
   nothing.
5. **It fits the secondary purpose.** A simulation design, an ablation study, a clean
   instrument, and reproducible results are strong evidence of applied statistical
   judgment — which matters given the concurrent job search.

## 5. What is given up, stated plainly

- No claim about whether retailers actually discriminate. That question stays open.
- No prevalence or magnitude estimate. RQ1 and RQ2 of the original proposal go unanswered.
- H2 (geography dominates) is untestable and is dropped rather than weakly tested.
- The findings speak to *measurement practice*, and anyone wanting a consumer-facing
  answer will find that unsatisfying.

These are real losses. They are preferable to a field study that stalls at the pilot,
or one that produces a number nobody should believe.

## 6. Decision log

| Question | Position | Status |
|---|---|---|
| Which option | Option 1, with Option 2 as non-blocking stretch | **Recommended — awaiting confirmation** |
| Institutional affiliation | Unknown; recommendation robust either way | **Open** |
| Whether to revisit Option 3 | Only if affiliation or funding changes | Deferred |
| Budget ceiling | Assumed ~$0 | **Unconfirmed** |

The scoped proposal for Option 1 is in `../PROPOSAL.md`.
