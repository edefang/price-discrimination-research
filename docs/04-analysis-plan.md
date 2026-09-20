# Analysis Plan

**Status: DRAFT — not yet frozen.**

This plan is pre-registered at the end of Phase 3, before any main-study data is
collected. Once frozen, every deviation is logged in a dated amendment section with its
reason, and analyses not specified here are reported as exploratory.

The reason for the freeze is specific to this project's history. The v0 prototype's 5%
flag threshold had no derivation; it was a number chosen because it produced plausible
output. Under a product frame that is a tuning decision. Under a research frame it is
the mechanism by which a study finds whatever it went looking for.

---

## 1. Data preparation

Fixed before analysis, applied mechanically.

**Inclusions.** Observations from sweeps passing all four QC gates in
`03-measurement-protocol.md`.

**Pre-specified exclusions.** Each is recorded with a count in the results:

| Rule | Reason |
|---|---|
| `canary_status = bot_page` | Not a real price |
| `parse_status != ok` | Ambiguous parse is not a measurement |
| Currency differs from the sweep's control currency | Not comparable (R4) |
| Sweep failed G4 control stability | Within-sweep comparison invalid |
| Product delisted or out of stock mid-sweep | The good changed |

**No other exclusions.** In particular, outlying prices are **not** trimmed. A large
price gap is the phenomenon under study, and trimming it is discarding the finding.
Outliers are reported and inspected, never removed.

**Transformation.** Price is expressed as proportional deviation from the sweep's
control price:

```
y = (price - control_price) / control_price
```

so effects are comparable across products at different price levels, and the temporal
drift the control absorbs does not enter.

## 2. Primary analysis — RQ1, RQ2

**Estimator.** For each factor *a* and level *l*, the mean of `y` over all observations
at that level, with all other factors at control.

**Inference.** Cluster-robust standard errors clustered at the **product** level.
Observations within a product across sweeps are not independent — the same SKU carries
the same pricing logic — and treating them as independent would overstate precision,
which is the most common way a study of this shape produces a spuriously confident
result.

**Test.** Two-sided, alpha = 0.05, against the null of zero deviation. Two-sided is a
design requirement (R2), not a preference: a targeted discount is a finding.

**Multiplicity.** Benjamini-Hochberg FDR control at q = 0.05 across the family of all
factor-level contrasts. The family is enumerated and fixed at pre-registration, so it
cannot be narrowed after seeing results.

**RQ1 statistic.** The share of (retailer, product) pairs with at least one factor-level
contrast significant after FDR correction, reported with a confidence interval.

**RQ2 statistic.** Conditional on significance, the distribution of |y| — median,
IQR, and max — reported per factor.

## 3. Secondary analysis — RQ3

Mixed-effects model over all observations:

```
y ~ geo + dev + loc + tz + hist + (1 | product) + (1 | sweep)
```

Random intercepts for product and sweep absorb the two nuisance dimensions: products
differ in baseline pricing logic, and sweeps differ in market conditions. Fixed effects
are the factor main effects.

Two-factor interactions are added only for pairs the fractional design can identify
without aliasing, and are labeled exploratory regardless.

## 4. RQ4 — separating discrimination from A/B testing

The question the single-observation designs cannot answer. Decided by variance
decomposition, per (product, sweep):

- `V_within` = variance across the *k* replicates of the same persona
- `V_between` = variance across persona means

**Decision rule, pre-specified:**

| Condition | Classification |
|---|---|
| `V_between` significant, `V_within` not | **Attribute-correlated: discrimination** |
| `V_within` significant, `V_between` not | **Random across replicates: A/B testing** |
| Both significant | **Mixed** — reported as such, not forced into one bin |
| Neither | **No variation** |

Significance by F-test on the variance ratio, with the same FDR correction.

The "mixed" cell exists deliberately. Forcing a binary classification here would
manufacture a cleaner result than the data supports, and bucket assignment can itself
correlate with attributes, which is a real and interesting third possibility.

## 5. Heterogeneous effects — exploratory

Where a main effect is established, causal ML (`econml`) estimates how the effect varies
by product category, price stratum, and retailer.

**This is the only legitimate role for causal ML in this study.** Identification comes
from randomization (`02-study-design.md`, section 4); these methods are used for effect
*heterogeneity*, not to recover the effect itself. All output here is exploratory and
hypothesis-generating for a follow-up study.

## 6. Reporting the null

If no factor-level contrast survives FDR correction, the study reports a null result
with:

- the minimum detectable effect actually achieved, from realized variance and N;
- the share of sweeps excluded by each QC gate, since a null produced by heavy exclusion
  is a different claim from a null on a complete panel;
- per-retailer breakdown, since a pooled null can hide a single-retailer effect;
- an explicit statement of what was *not* tested: logged-in states, non-fixed-SKU
  verticals, geographies outside the sourceable proxy set.

**A null is written up and disseminated on the same schedule as a positive finding.**
Committing to that in advance is what keeps the earlier analysis honest.

## 7. What this plan forbids

Stated so violations are visible:

- Changing the flag threshold after seeing the data.
- Adding or dropping retailers or products after collection begins.
- Reporting a subgroup discovered during analysis as if pre-specified.
- Dropping "noisy" sweeps by any criterion other than the QC gates above.
- Converting currencies to enlarge the comparison set.
- Re-running collection on a retailer that produced a null.

## 8. Amendments

None. Amendments are appended here with date and reason once the plan is frozen.
