"""Mechanism classification by variance decomposition (analysis plan, section 4).

Two mechanisms produce price variation across personas, and a single observation per
cell cannot tell them apart:

    discrimination   price is a function of attributes; the same persona sees the
                     same price on repeat measurement, different personas differ
    A/B testing      price is assigned to a random bucket per session; repeat
                     measurement with a fresh context lands in a different bucket

With k independent replicates per cell they separate: A/B bucketing shows up as
variance *within* a persona's replicates, discrimination as variance *between*
persona means with stable replicates.

The rule has a "mixed" cell on purpose. Forcing a binary classification would
manufacture a cleaner answer than the data supports, and bucket assignment that
itself correlates with attributes is a real third possibility.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass
from enum import Enum

from .detect import Observation


class Mechanism(str, Enum):
    NO_VARIATION = "no_variation"
    ATTRIBUTE_CORRELATED = "attribute_correlated"
    REPLICATE_RANDOM = "replicate_random"
    MIXED = "mixed"
    INSUFFICIENT_REPLICATES = "insufficient_replicates"


@dataclass(frozen=True)
class Decomposition:
    n_personas: int
    min_replicates: int
    grand_mean: float
    within_var: float          # mean within-cell variance, proportional units
    between_var: float         # variance of cell means, proportional units
    unstable_cells: int
    instability_rate: float
    mean_range: float          # (max cell mean - min cell mean) / grand mean
    p_between: float | None    # one-way ANOVA p-value, when computable
    mechanism: Mechanism

    @property
    def f_ratio(self) -> float | None:
        return self.between_var / self.within_var if self.within_var > 0 else None


def decompose(
    observations: list[Observation],
    *,
    tol: float,
    alpha: float = 0.05,
    majority: float = 0.5,
) -> Decomposition:
    """Classify a single (sweep, product, currency) cohort with replicates.

    `tol` is the proportional difference below which two prices are treated as the
    same — it absorbs rounding, not effects. `majority` is the share of cells that
    must disagree with their own replicates before variation is called random.
    """
    cells: dict[str, list[int]] = {}
    for o in observations:
        cells.setdefault(o.persona_id, []).append(o.price.minor_units)

    n_personas = len(cells)
    min_reps = min(len(v) for v in cells.values()) if cells else 0
    grand = statistics.fmean(p for v in cells.values() for p in v) if cells else 0.0

    if n_personas < 2 or min_reps < 2 or grand == 0:
        return Decomposition(
            n_personas, min_reps, grand, 0.0, 0.0, 0, 0.0, 0.0, None,
            Mechanism.INSUFFICIENT_REPLICATES,
        )

    prop = {k: [p / grand for p in v] for k, v in cells.items()}
    means = {k: statistics.fmean(v) for k, v in prop.items()}
    within = statistics.fmean(statistics.pvariance(v) for v in prop.values())
    between = statistics.pvariance(list(means.values()))
    unstable = sum(1 for v in prop.values() if (max(v) - min(v)) > tol)
    rate = unstable / n_personas
    mean_range = max(means.values()) - min(means.values())

    p_between: float | None
    if within == 0.0:
        p_between = 0.0 if mean_range > tol else 1.0
    else:
        try:
            from scipy import stats

            p_between = float(stats.f_oneway(*prop.values()).pvalue)
        except Exception:  # scipy absent or degenerate input
            p_between = None

    within_signif = rate > majority
    between_signif = mean_range > tol and (
        p_between is not None and p_between < alpha
        if within > 0.0
        else True
    )
    # Under random bucketing the cell means also spread, but the spread is driven
    # by the within variance. Require between to exceed within before crediting
    # attribute correlation on top of replicate randomness.
    if within_signif and between > 0 and within > 0 and between <= within:
        between_signif = False

    if not within_signif and not between_signif:
        mech = Mechanism.NO_VARIATION
    elif between_signif and not within_signif:
        mech = Mechanism.ATTRIBUTE_CORRELATED
    elif within_signif and not between_signif:
        mech = Mechanism.REPLICATE_RANDOM
    else:
        mech = Mechanism.MIXED

    return Decomposition(
        n_personas, min_reps, grand, within, between, unstable, rate, mean_range, p_between, mech
    )
