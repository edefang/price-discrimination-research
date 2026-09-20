# Study Design

**Design type:** Randomized factorial field experiment, repeated measures, with a
constant control arm.

---

## 1. Units

Getting these right is the correction the v0 audit demanded. The prototype had no
concept of a sweep at all, which is why it compared prices across days and reported
ordinary price changes as discrimination.

| Term | Definition |
|---|---|
| **Observation** | One price reading: (product, persona, replicate, sweep) to price, currency, QC flags |
| **Cell** | One (product, persona) pair within one sweep |
| **Replicate** | One of *k* independent readings of the same cell in the same sweep, each with a fresh browser context |
| **Sweep** | All products x all personas x all replicates, collected within a bounded window *W*. **The sweep is the unit of comparison.** |
| **Panel** | All sweeps for a retailer over the collection period |

**No price is ever compared to a price from a different sweep.** Cross-sweep variation
is temporal drift and is modeled separately, via the control persona. This single rule
eliminates the v0 prototype's dominant failure mode.

*W* must be short enough that the retailer's own price is stable within it, and long
enough to complete the sweep without a request rate that trips rate limiting. Pilot
(Phase 2) estimates the feasible *W*; it is a pre-registered constant thereafter.

## 2. Factors

Persona attributes are crossed on a grid. The v0 prototype's three hand-written personas
each varied four attributes simultaneously, so no effect was attributable to any single
cause — the design was unidentified before a single observation was collected.

| Factor | Levels (provisional) | Rationale |
|---|---|---|
| **GEO** | Apparent IP location: 3-4 regions | Most frequently implicated attribute; tests H2 |
| **DEV** | desktop / mobile | Tests H3; also the axis a retailer can act on most cheaply |
| **LOC** | Browser locale: 2 levels | Separable from GEO only if crossed with it |
| **TZ** | Timezone: aligned / misaligned with GEO | Misalignment is the interesting cell — it isolates TZ from GEO |
| **HIST** | cold / primed (prior visit to the same SKU) | Tests whether repeat interest moves price |

**Control level.** Every factor has a designated control level. The **control persona**
sets all factors to control and appears in every sweep, for every product, at every
replicate count. It is the reference against which effects are measured and the meter
that reads temporal drift.

**Full factorial size.** With the provisional levels above: 4 x 2 x 2 x 2 x 2 = 64
personas per product per sweep. Times *k* replicates times *N* products, that is a
request volume that will not survive politeness constraints at any useful *N*.

**Resolution.** Use a **fractional factorial of resolution IV** for the main study, so
main effects are unconfounded with two-factor interactions, accepting that two-factor
interactions are aliased with each other. Main effects answer RQ3; interactions are
exploratory and flagged as such. If the pilot shows a large interaction, escalate that
pair to a full crossing in a targeted follow-up rather than inflating the main design.

The exact fraction and generator are chosen in Phase 3 from the pilot's variance
estimate and the feasible request budget, and are pre-registered.

## 3. Randomization

Randomized at three levels. All three matter; the v0 prototype randomized nothing.

1. **Order within a sweep.** The sequence of (product, persona, replicate) visits is
   randomly permuted per sweep. Without this, position in the loop is confounded with
   persona: the prototype iterated product-outer, persona-inner, so persona order was
   identical every run and any within-sweep time trend loaded entirely onto the
   last-visited persona.
2. **Proxy exit assignment.** Within a GEO level, the specific exit IP is drawn at
   random per observation, so a single bad IP's reputation does not become that
   region's effect.
3. **Sweep start time.** Sweep start is jittered within its scheduled block, so the
   panel does not sample the same minute of every day.

Randomization seeds are recorded per sweep so the assignment is reproducible.

## 4. Why this is an experiment, and what that buys

The v0 roadmap planned to reach for `dowhy` / `econml` to establish causality. That was
a category error worth naming, because it changes the whole analysis.

Those tools address **observational** causal inference: you observe treated and
untreated units, you fear the assignment was confounded with the outcome, and you
attempt to recover a causal effect under an assumption like unconfoundedness. That is
the right machinery when you cannot control assignment.

Here, assignment *is* controlled. The experimenter decides which persona visits which
product at which moment, and decides it at random. There is no selection process to
adjust for, because there are no self-selecting consumers — the profiles are constructed
objects. The main effect is identified by the randomization itself.

**Consequences:**

- The primary estimator is a simple contrast, not a doubly-robust learner. Complexity
  here would be decoration.
- The assumptions that need defending are **not** unconfoundedness. They are: the
  retailer's price is stable within *W* (checked by the control persona); the
  measurement does not alter the treatment (the detection problem, see
  `05-threats-to-validity.md`); and replicates are independent (checked by fresh
  contexts and IP rotation).
- Causal ML re-enters legitimately at **heterogeneous** treatment effects — which
  product categories, price strata, or retailers show larger effects. That is a
  Phase 5 secondary analysis, not the identification strategy.

## 5. Replicates and the A/B testing problem

Replicates are the design feature that answers RQ4, and they are the reason *k* > 1.

Two mechanisms produce price variation across personas:

- **Discrimination:** price is a function of consumer attributes. The same persona sees
  the same price on repeat measurement; different personas differ systematically.
- **A/B testing:** price is randomly assigned to a bucket. Repeat measurement with a
  fresh context lands in a *different* bucket; variation is uncorrelated with attributes.

With one observation per cell — the v0 design — these are indistinguishable. With *k*
independent replicates per cell, they separate cleanly:

| Within-cell variance | Between-persona variance | Reading |
|---|---|---|
| Low | Low | No variation |
| Low | **High** | **Discrimination** |
| **High** | Low-moderate | **A/B testing** |
| High | High | Both, or bucket assignment correlates with attributes |

The variance-ratio test formalizing this is specified in `04-analysis-plan.md`.

*k* = 3 is the provisional minimum. The pilot sets the final value from the observed
within-cell variance.

## 6. Power

The minimum detectable effect is a function of within-cell price variance, replicate
count, and the number of products. It cannot be computed before the pilot, because the
variance is unknown — and inventing it would be exactly the kind of unjustified constant
the audit criticized in the v0 prototype's 5% threshold.

**Structure of the calculation, to be executed in Phase 3:**

```
MDE = (z_{1-alpha/2} + z_{1-beta}) * sigma_within * sqrt( 2 / (k * N_products * N_sweeps) )
```

with:

| Input | Source | Status |
|---|---|---|
| `sigma_within` — within-cell SD of price, as % of control | Phase 2 pilot | **Unknown — must be measured** |
| `k` — replicates per cell | Chosen to satisfy MDE target | Provisional 3 |
| `N_products`, `N_sweeps` | Request budget under rate limits | Pilot-constrained |
| `alpha` | Pre-registered, with multiplicity correction | 0.05, two-sided |
| `1 - beta` | Pre-registered | 0.80 |

The clustering structure — observations nested in cells nested in sweeps — inflates the
required N above the independent-samples formula above. The Phase 3 calculation uses a
mixed-model power simulation rather than the closed form, which is written here only to
name the inputs.

**No effect-size threshold is inherited from the prototype.** The 5% figure in the v0
code was a placeholder with no derivation behind it and is not carried forward.

## 7. What would make this design fail

Stated plainly, so the pilot can look for it:

- Sweep window *W* cannot be made short enough to hold price constant while staying
  within polite request rates, so the whole within-sweep comparison collapses. **This is
  the primary feasibility risk and the pilot's main job is to resolve it.**
- Bot detection is severe enough that a meaningful share of observations are fallback
  pages, so the panel is unusable regardless of design.
- Ethically sourceable proxies do not cover enough distinct geographies, so GEO drops to
  two levels or out of the design entirely, and H2 becomes untestable.
