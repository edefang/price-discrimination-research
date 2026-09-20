# From Startup Idea to Research Study

**Date of decision:** 2026-09-19

## Why the frame changed

The original project was a venture: detect personalized pricing, use the detection to
power a consumer product that saves people money. The audit of the v0 prototype
(`../AUDIT-v0-prototype.md`) found four defects that all pointed the same direction —
the instrument was biased toward producing findings:

- it compared prices **across time** rather than within a moment, so an ordinary price
  change registered as discrimination against every persona at once;
- it tested **one direction only**, flagging prices above the cohort median, so
  targeted *discounts* — a common form of personalized pricing — were invisible;
- it **silently dropped** personas that were blocked or whose prices failed to parse,
  which removes exactly the unusual profiles most likely to be treated differently;
- it computed the baseline from a pool **including** the observation under test, so with
  three personas at most one could ever be flagged.

None of those are exotic bugs. They are the ordinary consequence of building a detector
whose purpose is to detect. A product that finds nothing has no reason to exist, so the
pressure runs toward sensitivity. A study that finds nothing has published a result.

That is the whole argument for the reframe. The subject matter is interesting, the
measurement is hard, and the honest version of this work is a measurement study rather
than a detection service.

## What changes concretely

| | Startup frame | Research frame |
|---|---|---|
| **Goal** | Detect gaps users can act on | Estimate prevalence, magnitude, determinants |
| **Success** | Users, retention, savings delivered | A defensible estimate with stated uncertainty |
| **Null result** | Kills the product | Is the finding |
| **Incentive** | Sensitivity — find something | Validity — measure correctly |
| **Unit of work** | Ship a feature, iterate | Freeze a design, collect, analyze once |
| **Scope** | As many retailers as possible | A small defensible sample, deeply measured |
| **Instrument** | Good enough to ship | Validated before it touches live data |
| **Causal claim** | Implicit, unexamined | Explicit estimand, identified by randomization |
| **Audience** | Consumers | Anyone who needs a number they can cite |
| **Failure mode** | Users churn | Confident wrong number enters the record |

## Six practical consequences

**1. Pre-registration replaces iteration.** The analysis plan
(`04-analysis-plan.md`) is frozen before data collection begins. Under the product
frame you would tune the threshold until the flags looked right; that is p-hacking with
extra steps. The threshold, the estimator, and the exclusion rules are now decided in
advance, and deviations are logged rather than absorbed.

**2. The instrument gets validated, not just written.** Phase 1 builds a mock storefront
that serves known, deliberately persona-varied prices, so the instrument can be tested
against ground truth before any live target is touched. The v0 prototype was never run
successfully even once — no `data/` directory was ever created — which means none of its
logic was ever exercised against a known answer.

**3. Randomization replaces observational causal inference.** The v0 roadmap planned to
reach for `dowhy` / `econml` to establish causality. That was the wrong tool for this
design. Because the experimenter *assigns* personas, the treatment is randomized and the
main effect is identified without any selection-on-observables assumption. Causal ML
becomes useful for heterogeneous effects — which products, which retailers — not for
identification. See `02-study-design.md`.

**4. A control persona enters every sweep.** A reference profile held constant across
all sweeps measures the retailer's temporal price drift independently of any persona
effect. This is what separates "the price changed" from "the price changed for me," and
its absence was the v0 prototype's fatal flaw.

**5. Ethics becomes a gate rather than a footnote.** Phase 3 does not complete without
an ethics review, including the proxy-sourcing question that the startup frame never
raised: residential proxy networks frequently obtain their exit IPs from people who did
not meaningfully consent, which is a problem a study must resolve before collection and
a product would likely have ignored. See `06-ethics-and-legal.md`.

**6. Scope narrows deliberately.** The product wanted coverage. The study wants a sample
it can defend: fixed-SKU e-commerce, logged-out, item price rather than cart total, a
bounded retailer set. Narrow and valid beats broad and confounded.

## What is retained from the startup work

The reframe discards the product thesis, not the thinking. Three things carry over:

- **The persona-context primitive.** Varying locale, timezone, geolocation, and device
  per browser context is the right measurement mechanism and remains the core of the
  instrument.
- **The fixed-SKU decision.** The v0 README argued for fixed-SKU e-commerce over
  flights and hotels, because a SKU is unambiguously the same good while a seat or a
  room has legitimate confounds. That reasoning is sound and is adopted as study scope.
- **The documented limitations.** The v0 README was candid about the missing IP
  dimension, selector brittleness, and the naivety of the flagging rule. Those
  admissions became the starting list for `05-threats-to-validity.md`.

## What this is not

This is not a claim that price discrimination is occurring. No data has been collected.
The study is designed to be able to measure it, including to measure its absence.
