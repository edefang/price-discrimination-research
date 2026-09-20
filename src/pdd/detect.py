"""Detection (requirements R2-R5).

This is the layer the audit found most broken. Four defects, all verified by execution,
all of which biased toward reporting a finding:

  A1  pooled across time, so a $100->$115 price change flagged all three personas
  A2  one-sided, so a 17% targeted discount was invisible
  A3  baseline included the observation under test, so with N=3 at most one could flag
  B3  `WHERE price IS NOT NULL` dropped blocked personas — the ones most likely to be
      treated differently — and returned a clean null

Each is addressed structurally here rather than by convention: the cohort is keyed on
sweep, deviation is signed, the reference excludes the observation, and an incomplete
cohort is a distinct outcome that cannot be mistaken for "nothing found".
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from enum import Enum

from .money import CurrencyMismatch, Money


class CohortStatus(str, Enum):
    COMPLETE = "complete"
    INCOMPLETE = "incomplete"          # R5 — reported, never silently analysed
    NO_REFERENCE = "no_reference"
    SINGLE_OBSERVATION = "single_observation"


class Direction(str, Enum):
    PREMIUM = "premium"
    DISCOUNT = "discount"              # R2 — v0 could not represent this at all


@dataclass(frozen=True)
class Observation:
    """One usable price reading. Construction is the analysis-eligibility boundary."""

    sweep_id: str
    product_id: str
    persona_id: str
    price: Money
    replicate_idx: int = 0
    is_control: bool = False


@dataclass(frozen=True)
class MissingCell:
    """A persona that yielded no usable price, and why. Never discarded."""

    persona_id: str
    reason: str


@dataclass(frozen=True)
class Finding:
    sweep_id: str
    product_id: str
    persona_id: str
    price: Money
    reference: Money
    reference_kind: str
    deviation: float                   # signed
    direction: Direction

    @property
    def pct(self) -> float:
        return self.deviation * 100.0


@dataclass(frozen=True)
class CohortResult:
    sweep_id: str
    product_id: str
    currency: str
    status: CohortStatus
    findings: tuple[Finding, ...] = field(default_factory=tuple)
    missing: tuple[MissingCell, ...] = field(default_factory=tuple)
    reference_kind: str | None = None
    detail: str | None = None

    @property
    def analysable(self) -> bool:
        """Whether this cohort may enter the panel.

        An incomplete cohort is not analysable. Reading a null result off one is the
        v0 failure that turned a blocked persona into 'no discrimination found'.
        """
        return self.status is CohortStatus.COMPLETE


def _reference_for(
    obs: list[Observation], target: Observation
) -> tuple[Money | None, str]:
    """Reference price for `target`, excluding `target` itself (R3).

    Control persona first — it is the designed reference and it reads temporal drift.
    Otherwise the leave-one-out median of the remaining personas. The v0 baseline
    included the observation under test, which with three personas meant the middle one
    could never flag and at most one ever could.
    """
    controls = [o for o in obs if o.is_control and o is not target]
    if controls:
        prices = [o.price.minor_units for o in controls]
        return Money(round(statistics.median(prices)), target.price.currency), "control"

    others = [o for o in obs if o is not target]
    if not others:
        return None, "none"
    prices = [o.price.minor_units for o in others]
    return Money(round(statistics.median(prices)), target.price.currency), "leave_one_out_median"


def evaluate_cohort(
    observations: list[Observation],
    *,
    threshold: float,
    expected_personas: set[str] | None = None,
    missing: list[MissingCell] | None = None,
) -> CohortResult:
    """Evaluate one (sweep, product, currency) cohort.

    `threshold` is the absolute proportional deviation at which a persona is flagged.
    It has no default, deliberately: the v0 prototype's 5% was a placeholder with no
    derivation, and the study's minimum detectable effect comes from the pilot variance
    estimate. Requiring the caller to pass it keeps that decision visible.
    """
    if not observations:
        raise ValueError("cohort is empty")

    sweep_ids = {o.sweep_id for o in observations}
    product_ids = {o.product_id for o in observations}
    if len(sweep_ids) != 1:
        raise ValueError(f"cohort spans {len(sweep_ids)} sweeps; comparison unit is one sweep (R1)")
    if len(product_ids) != 1:
        raise ValueError(f"cohort spans {len(product_ids)} products")

    currencies = {o.price.currency for o in observations}
    if len(currencies) != 1:
        raise CurrencyMismatch(
            f"cohort mixes {sorted(currencies)}; group by currency before evaluating (R4)"
        )

    sweep_id, product_id, currency = sweep_ids.pop(), product_ids.pop(), currencies.pop()
    missing = list(missing or [])

    if expected_personas is not None:
        present = {o.persona_id for o in observations}
        for persona in sorted(expected_personas - present):
            if not any(m.persona_id == persona for m in missing):
                missing.append(MissingCell(persona, "absent from cohort"))

    base = dict(
        sweep_id=sweep_id, product_id=product_id, currency=currency, missing=tuple(missing)
    )

    if missing:
        return CohortResult(
            status=CohortStatus.INCOMPLETE,
            detail=(
                f"{len(missing)} persona(s) missing: "
                + ", ".join(f"{m.persona_id} ({m.reason})" for m in missing)
                + " — cohort not analysable (R5)"
            ),
            **base,
        )

    if len({o.persona_id for o in observations}) < 2:
        return CohortResult(
            status=CohortStatus.SINGLE_OBSERVATION,
            detail="a single persona cannot be compared against anything",
            **base,
        )

    findings: list[Finding] = []
    reference_kind: str | None = None
    has_control = any(o.is_control for o in observations)

    for target in observations:
        # A control observation is the reference, not a subject. Evaluating it against
        # the treated personas would report the control as deviating from them, which
        # inverts the comparison — and with several treated personas shifted together,
        # would flag the one persona known to be untreated.
        if has_control and target.is_control:
            continue

        reference, kind = _reference_for(observations, target)
        if reference is None:
            continue
        reference_kind = kind
        if reference.minor_units == 0:
            continue

        deviation = target.price.proportional_deviation_from(reference)
        # R2: two-sided. A persona shown less is a finding.
        if abs(deviation) > threshold:
            findings.append(
                Finding(
                    sweep_id=sweep_id,
                    product_id=product_id,
                    persona_id=target.persona_id,
                    price=target.price,
                    reference=reference,
                    reference_kind=kind,
                    deviation=deviation,
                    direction=Direction.PREMIUM if deviation > 0 else Direction.DISCOUNT,
                )
            )

    return CohortResult(
        status=CohortStatus.COMPLETE,
        findings=tuple(findings),
        reference_kind=reference_kind,
        **base,
    )


def evaluate_panel(
    observations: list[Observation],
    *,
    threshold: float,
    expected_personas: set[str] | None = None,
) -> list[CohortResult]:
    """Split a panel into cohorts and evaluate each.

    Grouping by (sweep_id, product_id, currency) is the correction for A1 and B2. The
    v0 analysis grouped by product alone, so every observation ever recorded went into
    one median and ordinary price drift became signal.
    """
    cohorts: dict[tuple[str, str, str], list[Observation]] = {}
    for o in observations:
        cohorts.setdefault((o.sweep_id, o.product_id, o.price.currency), []).append(o)

    return [
        evaluate_cohort(group, threshold=threshold, expected_personas=expected_personas)
        for _, group in sorted(cohorts.items())
    ]
