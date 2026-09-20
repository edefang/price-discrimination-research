"""Simulation study: data-generating processes and the detector lattice.

PROPOSAL.md section 5. Synthetic panels are generated under conditions whose ground
truth is known by construction, and each design in the lattice D0..D6 is run against
them. The designs are implemented here in vectorized form for speed; `tests/
test_simulate.py` checks that D6 agrees with the production detector on the same data,
so the fast path cannot drift from the real one.

Panel shape is (S, P, J, K): sweeps, products, personas, replicates. NaN is a missing
observation. Persona 0 is the control; persona `TARGET` carries any injected effect.

Numbers to know before reading results:

  * Designs D0-D4 observe each cell once (they use replicate 0 only). That is not a
    simplification — it is what those designs are.
  * D0 pools every sweep into one baseline per product, as the v0 prototype did.
  * Parse corruption models the v0 parser: a price of $1,000 or more is read at one
    tenth of its value, silently. D6 refuses those parses instead.
"""

from __future__ import annotations

import warnings
from dataclasses import asdict, dataclass

import numpy as np

PERSONAS = [
    "control", "geo=us-west", "geo=eu-west", "dev=mobile",
    "loc=de-DE", "tz=Europe/Berlin", "hist=primed",
]
CONTROL = 0
TARGET = 3   # dev=mobile

MECH_NONE, MECH_ATTRIBUTE, MECH_RANDOM, MECH_MIXED, MECH_INSUFFICIENT = 0, 1, 2, 3, -1
MECH_NAMES = {0: "none", 1: "attribute", 2: "random", 3: "mixed", -1: "insufficient"}


@dataclass(frozen=True)
class Condition:
    effect: str = "none"            # none | premium | discount   (applied to TARGET)
    effect_size: float = 0.10
    drift: str = "none"             # none | slow | fast | step
    drift_rate: float = 0.0         # per sweep for slow/fast; step height for step
    ab_test: bool = False           # random bucket per observation
    ab_size: float = 0.10
    blocking: str = "none"          # none | uniform | differential (TARGET only)
    block_rate: float = 0.0
    parse_corruption: float = 0.0   # P(a >= $1,000 price is read at 1/10)
    noise_sd: float = 0.005         # proportional, multiplicative

    def truth_mechanism(self) -> int:
        has_effect = self.effect != "none"
        if has_effect and self.ab_test:
            return MECH_MIXED
        if has_effect:
            return MECH_ATTRIBUTE
        if self.ab_test:
            return MECH_RANDOM
        return MECH_NONE


@dataclass(frozen=True)
class Design:
    name: str
    within_sweep: bool
    two_sided: bool
    leave_one_out: bool
    control_ref: bool
    replicates: bool       # k > 1, G4 gate, incomplete cohorts abstain, mechanism
    robust_parser: bool


LATTICE: list[Design] = [
    Design("D0", False, False, False, False, False, False),
    Design("D1", True, False, False, False, False, False),
    Design("D2", True, True, False, False, False, False),
    Design("D3", True, True, True, False, False, False),
    Design("D4", True, True, True, True, False, False),
    Design("D5", True, True, True, True, True, False),
    Design("D6", True, True, True, True, True, True),
]
DESIGNS = {d.name: d for d in LATTICE}


@dataclass
class Panel:
    true_price: np.ndarray       # (S,P,J,K) displayed price, minor units, NaN if blocked
    observed_v0: np.ndarray      # what a v0-class parser records
    observed_robust: np.ndarray  # what a refusing parser records (corrupt -> NaN)
    position: np.ndarray         # (S,P,J,K) visit position within the cohort


# ------------------------------------------------------------------ generation


def _positions(J: int, K: int, rng: np.random.Generator) -> np.ndarray:
    """Visit positions for one cohort: control replicates evenly spaced, others random.
    Mirrors `collect.build_visit_order`."""
    total = J * K
    pos = np.empty((J, K), int)
    if K > 1:
        ctrl_slots = np.unique(np.round(np.arange(K) * (total - 1) / (K - 1)).astype(int))
    else:
        ctrl_slots = np.array([rng.integers(total)])
    while len(ctrl_slots) < K:   # collisions only when K is close to total
        extra = rng.choice(np.setdiff1d(np.arange(total), ctrl_slots), 1)
        ctrl_slots = np.sort(np.append(ctrl_slots, extra))
    pos[CONTROL] = ctrl_slots[:K]
    rest = np.setdiff1d(np.arange(total), pos[CONTROL])
    rng.shuffle(rest)
    pos[1:] = rest.reshape(J - 1, K)
    return pos


def generate_panel(
    cond: Condition,
    *,
    n_products: int = 20,
    n_sweeps: int = 5,
    k: int = 3,
    rng: np.random.Generator,
) -> Panel:
    S, P, J, K = n_sweeps, n_products, len(PERSONAS), k
    shape = (S, P, J, K)

    # Base prices log-uniform on [$10, $3,000] so a meaningful share are >= $1,000.
    base = np.exp(rng.uniform(np.log(1_000), np.log(300_000), size=P))
    price = np.broadcast_to(base[None, :, None, None], shape).astype(float).copy()

    position = np.empty(shape, int)
    for s in range(S):
        for p in range(P):
            position[s, p] = _positions(J, K, rng)

    if cond.drift in ("slow", "fast"):
        price *= ((1.0 + cond.drift_rate) ** np.arange(S))[:, None, None, None]
    elif cond.drift == "step":
        price *= np.where(position > (J * K) // 2, 1.0 + cond.drift_rate, 1.0)

    if cond.effect == "premium":
        price[:, :, TARGET, :] *= 1.0 + cond.effect_size
    elif cond.effect == "discount":
        price[:, :, TARGET, :] *= 1.0 - cond.effect_size

    if cond.ab_test:
        price *= np.where(rng.random(shape) < 0.5, 1.0 + cond.ab_size, 1.0)

    if cond.noise_sd > 0:
        price *= 1.0 + rng.normal(0.0, cond.noise_sd, shape)
    price = np.round(price)

    if cond.blocking == "uniform":
        price[rng.random(shape) < cond.block_rate] = np.nan
    elif cond.blocking == "differential":
        mask = rng.random((S, P, K)) < cond.block_rate
        price[:, :, TARGET, :][mask] = np.nan

    corrupt = (rng.random(shape) < cond.parse_corruption) & (price >= 100_000)
    observed_v0 = np.where(corrupt, price / 10.0, price)
    observed_robust = np.where(corrupt, np.nan, price)

    return Panel(price, observed_v0, observed_robust, position)


# ------------------------------------------------------------------- detection


def _loo_median(obs: np.ndarray) -> np.ndarray:
    """Median over personas excluding each persona in turn. (S,P,J,1) -> (S,P,J,1)."""
    J = obs.shape[2]
    out = np.empty_like(obs)
    for j in range(J):
        others = np.delete(obs, j, axis=2)
        out[:, :, j, :] = np.nanmedian(others, axis=2)
    return out


@dataclass
class Outcome:
    abstain: np.ndarray            # (S,P) cohort excluded by QC (replicate designs only)
    target_flagged: np.ndarray     # (S,P)
    nontarget_flagged: np.ndarray  # (S,P) any non-target, non-control persona flagged
    mechanism: np.ndarray          # (S,P) int code; MECH_INSUFFICIENT if not classifiable


def run_design(
    panel: Panel,
    design: Design,
    *,
    threshold: float = 0.05,
    g4_tol: float = 0.02,
    mech_tol: float = 0.02,
) -> Outcome:
    obs = panel.observed_robust if design.robust_parser else panel.observed_v0
    if not design.replicates:
        obs = obs[..., :1]
    S, P, J, K = obs.shape
    with np.errstate(all="ignore"):
        if not design.within_sweep:
            ref = np.nanmedian(obs, axis=(0, 2, 3))[None, :, None, None]
        elif design.control_ref:
            ref = np.nanmedian(obs[:, :, CONTROL, :], axis=2)[:, :, None, None]
        elif design.leave_one_out:
            ref = _loo_median(obs)
        else:
            ref = np.nanmedian(obs, axis=2, keepdims=True)

        dev = (obs - ref) / ref
        hit = (np.abs(dev) > threshold) if design.two_sided else (dev > threshold)
        hit &= ~np.isnan(obs) & ~np.isnan(ref)
        if design.control_ref:
            hit[:, :, CONTROL, :] = False
        flagged = np.any(hit, axis=3)                              # (S,P,J)

        abstain = np.zeros((S, P), bool)
        mech = np.full((S, P), MECH_INSUFFICIENT, int)
        if design.replicates:
            ctrl = obs[:, :, CONTROL, :]
            c_med = np.nanmedian(ctrl, axis=2)
            c_range = (np.nanmax(ctrl, axis=2) - np.nanmin(ctrl, axis=2)) / c_med
            g4_fail = np.nan_to_num(c_range, nan=np.inf) > g4_tol if K > 1 else np.zeros((S, P), bool)
            incomplete = np.any(np.all(np.isnan(obs), axis=3), axis=2)
            abstain = g4_fail | incomplete
            if K > 1:
                mech = _classify(obs, threshold=threshold, tol=mech_tol)
            mech[abstain & ~g4_fail] = MECH_INSUFFICIENT

    others = [j for j in range(J) if j not in (CONTROL, TARGET)]
    return Outcome(
        abstain=abstain,
        target_flagged=flagged[:, :, TARGET],
        nontarget_flagged=np.any(flagged[:, :, others], axis=2),
        mechanism=mech,
    )


def _classify(obs: np.ndarray, *, threshold: float, tol: float) -> np.ndarray:
    """Vectorized `mechanism.decompose` rule, per cohort. (S,P,J,K) -> (S,P)."""
    with warnings.catch_warnings():
        # Fully blocked cells are all-NaN; those cohorts are abstained by the caller.
        warnings.simplefilter("ignore", RuntimeWarning)
        return _classify_inner(obs, threshold=threshold, tol=tol)


def _classify_inner(obs: np.ndarray, *, threshold: float, tol: float) -> np.ndarray:
    grand = np.nanmean(obs, axis=(2, 3))[:, :, None, None]
    prop = obs / grand
    cell_range = np.nanmax(prop, axis=3) - np.nanmin(prop, axis=3)       # (S,P,J)
    valid = ~np.isnan(cell_range)
    unstable = (cell_range > tol) & valid
    rate = unstable.sum(axis=2) / np.maximum(valid.sum(axis=2), 1)
    means = np.nanmean(prop, axis=3)                                    # (S,P,J)
    mean_range = np.nanmax(means, axis=2) - np.nanmin(means, axis=2)
    within = np.nanmean(np.nanvar(prop, axis=3), axis=2)
    between = np.nanvar(means, axis=2)

    within_sig = rate > 0.5
    between_sig = mean_range > threshold
    between_sig &= ~(within_sig & (within > 0) & (between <= within))

    out = np.full(obs.shape[:2], MECH_NONE, int)
    out[between_sig & ~within_sig] = MECH_ATTRIBUTE
    out[within_sig & ~between_sig] = MECH_RANDOM
    out[within_sig & between_sig] = MECH_MIXED
    return out


# --------------------------------------------------------------------- metrics


def summarize(outcome: Outcome, cond: Condition) -> dict:
    """Rates over the cohorts of one panel."""
    analysed = ~outcome.abstain
    n = analysed.sum()
    any_flag = outcome.target_flagged | outcome.nontarget_flagged
    has_effect = cond.effect != "none"

    def rate(mask):
        return float(mask[analysed].mean()) if n else float("nan")

    row = dict(
        abstain_rate=float(outcome.abstain.mean()),
        flag_rate=rate(any_flag),
        target_only_rate=rate(outcome.target_flagged & ~outcome.nontarget_flagged),
        target_any_rate=rate(outcome.target_flagged),
        nontarget_rate=rate(outcome.nontarget_flagged),
    )
    row["false_positive_rate"] = row["flag_rate"] if not has_effect else float("nan")
    row["power_strict"] = row["target_only_rate"] if has_effect else float("nan")
    row["power_any"] = row["target_any_rate"] if has_effect else float("nan")
    row["misattribution_rate"] = row["nontarget_rate"] if has_effect else float("nan")

    truth = cond.truth_mechanism()
    classifiable = analysed & (outcome.mechanism != MECH_INSUFFICIENT)
    row["mechanism_accuracy"] = (
        float((outcome.mechanism[analysed] == truth).mean()) if n else float("nan")
    )
    row["mechanism_classifiable_rate"] = float(classifiable.mean())
    return row


def run_condition(
    cond: Condition,
    designs: list[Design],
    *,
    n_panels: int,
    seed: int,
    n_products: int = 20,
    n_sweeps: int = 5,
    k: int = 3,
    threshold: float = 0.05,
) -> list[dict]:
    """Monte Carlo over panels; one row per (design, panel)."""
    rng = np.random.default_rng(seed)
    rows: list[dict] = []
    for i in range(n_panels):
        panel = generate_panel(cond, n_products=n_products, n_sweeps=n_sweeps, k=k, rng=rng)
        for d in designs:
            out = run_design(panel, d, threshold=threshold)
            rows.append(
                dict(**asdict(cond), design=d.name, k=k, panel=i, seed=seed,
                     n_products=n_products, n_sweeps=n_sweeps, threshold=threshold,
                     **summarize(out, cond))
            )
    return rows
