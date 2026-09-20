# Research Proposal

**Working title:** Consumer-Attribute Price Variation in Online Retail: A Randomized
Measurement Study

**Status:** Reference design, not the active proposal.

> This document describes the **unconstrained** field study — the version one would run
> with a lab, a budget, counsel, and a year. `docs/09-feasibility-assessment.md` evaluates
> it against real constraints and finds the live-retail component out of reach; the scoped
> proposal actually being pursued is `../PROPOSAL.md`.
>
> Keep this file. It is what the field study returns to if affiliation or funding appear,
> and `PROPOSAL.md` is designed to produce the validated instrument it would need.

---

## 1. Motivation

Retailers can, in principle, vary a displayed price by anything the browser reveals:
where the request appears to come from, what device made it, what language it prefers,
whether the visitor has been seen before. Whether they *do*, at what scale, and on which
attributes, is an empirical question with a thin and aging evidence base relative to how
often the practice is asserted in public debate.

The question matters for three audiences: consumers deciding whether to trust displayed
prices, regulators weighing disclosure rules, and researchers who need a current baseline
measurement rather than a decade-old one.

## 2. Research questions

**RQ1 — Prevalence.** For what fraction of observed (retailer, product) pairs does the
displayed price vary with consumer profile, beyond what temporal drift and measurement
noise explain?

**RQ2 — Magnitude.** Conditional on variation being present, how large is it in percent
of the control price, and how is that magnitude distributed?

**RQ3 — Determinants.** Which profile attributes — geography, device class, locale,
timezone, visit history — account for the variation, and do they interact?

**RQ4 — Mechanism discrimination.** Where price variation exists, can it be distinguished
from retailer A/B testing, which varies price randomly rather than by consumer attribute?

RQ4 is the question the prior literature most often leaves open, and the design in
`02-study-design.md` is built specifically to answer it via replicate structure.

## 3. Hypotheses

Stated with direction. These are the claims the study can falsify.

| ID | Hypothesis | Falsified by |
|---|---|---|
| **H1** | A non-trivial share of (retailer, product) pairs display consumer-attribute price variation exceeding measurement noise | Variation indistinguishable from control-persona drift |
| **H2** | Geography (apparent IP location) produces larger price effects than any other single attribute | Another factor's main effect dominates, or geography's is null |
| **H3** | Device class produces a directional effect, with mobile profiles shown different prices than desktop | Mobile main effect is null or non-directional |
| **H4** | Where price variation is present, it is attribute-correlated rather than random across replicates — i.e. discrimination rather than A/B testing | Variation is uncorrelated with attributes and varies across replicates of the same persona |

H2 is stated because apparent geography is the attribute most frequently implicated in
documented cases; it is the hypothesis most likely to be wrong for a mundane reason (tax
and shipping leaking into displayed price), which is why the protocol measures item price
rather than cart total.

**Pre-specified null outcome.** If H1 is not supported, the study reports a null: that
under this design, at this sample size, with this power, consumer-attribute price
variation was not detected above noise in this retailer sample. That is a complete
result and will be written up as one.

## 4. Estimand

For product *p*, persona attribute *a*, and sweep *s*, the quantity of interest is the
average effect of setting attribute *a* to level *l* versus the control level, on the
displayed item price, holding all other attributes at their control levels:

```
τ(a, l) = E[ P(p, s | A_a = l, A_-a = control) − P(p, s | A = control) ]
```

expressed as a proportion of the control price so that effects are comparable across
products with different price levels.

Because persona assignment is randomized by the experimenter, τ is identified by
randomization alone. No assumption of unconfoundedness with respect to unobserved
consumer characteristics is required, because there are no consumers — the profiles are
constructed. This is the central methodological advantage of an experimental design over
the observational panels that much prior work relies on.

The threat to identification is not selection; it is **interference and detection** —
the retailer may respond to the measurement itself. `05-threats-to-validity.md` treats
this at length.

## 5. Scope

Deliberately narrow. Each restriction removes a confound rather than a convenience.

| Dimension | In scope | Excluded, and why |
|---|---|---|
| Product type | Fixed SKUs — identical good across all observations | Flights, hotels, rideshare: the good itself varies by fare class, room, and booking moment, so a price difference is not unambiguous |
| Price measured | Item price as displayed on the product page | Cart total: contaminated by tax and shipping, which vary by geography for lawful reasons |
| Session state | Logged out only | Logged-in states require account creation, which the ethics protocol forbids |
| Market | A bounded, pre-registered retailer set | Whole-web crawls: unmaintainable selectors, no depth, no replicates |
| Geography | Simulated via proxy exit location | Physical travel: not feasible at any useful N |
| Currency | Observations compared only within currency | Cross-currency comparison: an FX difference is not a price difference |

## 6. Contribution

1. A **current** prevalence and magnitude estimate for a defined retail sample, with
   stated power and uncertainty, rather than an existence proof.
2. A **design that separates discrimination from A/B testing** — the confound that
   makes most existing single-observation findings ambiguous.
3. An **open replication package**: instrument, mock-storefront validation fixtures,
   pre-registered analysis plan, and the anonymized observation panel.
4. A documented **negative-result path**, so the study is informative whichever way it
   resolves.

## 7. Out of scope

- Any claim about retailer intent. The study measures displayed prices, not motives.
- Legal conclusions about whether observed behavior is lawful.
- Normative argument about whether personalized pricing is desirable.
- Any consumer-facing tool. That was the startup; this is not it.

## 8. Open decisions

These are unresolved and must close before Phase 3 pre-registration. They are listed
rather than guessed.

- **Retailer sample.** Which retailers, how many, selected by what criterion.
- **Product sample.** How many SKUs per retailer, and how selected — price strata?
  category spread? random from catalog?
- **Naming.** Whether published results name individual retailers or report anonymized.
- **Proxy provider.** Constrained hard by the sourcing-consent problem in
  `06-ethics-and-legal.md`; may bound the geography factor to what can be obtained
  ethically.
- **Effect size of interest.** The smallest price difference worth detecting. The v0
  prototype used 5% as a flag threshold with no justification; a real minimum detectable
  effect must come from the Phase 2 pilot variance estimate, not from inheritance.
