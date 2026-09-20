"""Mock-storefront validation (measurement protocol, section 6; lifecycle Phase 1).

Runs the *entire* pipeline — sweep planning, fetching, canary, extraction, storage,
QC gates, cohort evaluation, mechanism classification — against a storefront whose
ground truth is known by construction, and compares what the instrument reports
with what it should.

The comparison is symmetric. A scenario with no injected effect must produce no
finding, and that is asserted as hard as a scenario with an effect must produce one.
The v0 prototype was never checked against a known answer in either direction.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .collect import Fetcher, HttpFetcher, SweepPlan, Target, run_sweep
from .detect import CohortResult, CohortStatus, MissingCell, evaluate_cohort
from .mechanism import Mechanism, decompose
from .mock_store import Expectation, MockStore, Scenario
from .personas import Persona, one_factor_at_a_time
from .qc import SweepQC, run_gates
from .storage import connect, load_cohort, usable_personas_by_currency


@dataclass(frozen=True)
class Check:
    name: str
    passed: bool
    detail: str


@dataclass
class ScenarioOutcome:
    scenario: Scenario
    expectation: Expectation
    qc: SweepQC
    cohorts: list[CohortResult]
    mechanisms: dict[str, Mechanism]
    checks: list[Check]

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.checks)

    def failures(self) -> list[Check]:
        return [c for c in self.checks if not c.passed]


def _persona_level_missing(usable, missing) -> list[MissingCell]:
    """A persona is missing from a cohort only if *none* of its replicates yielded a
    price. Partial replicate loss is recorded by G1; it does not void the cohort."""
    present = {o.persona_id for o in usable}
    seen: dict[str, MissingCell] = {}
    for m in missing:
        if m.persona_id not in present and m.persona_id not in seen:
            seen[m.persona_id] = m
    return list(seen.values())


def validate_scenario(
    scenario: Scenario | str,
    fetcher_factory: Callable[[], Fetcher] = HttpFetcher,
    *,
    personas: list[Persona] | None = None,
    replicates: int = 5,
    seed: int = 20260919,
    threshold: float = 0.05,
    tol: float = 0.01,
) -> ScenarioOutcome:
    scenario = Scenario(scenario)
    personas = personas or one_factor_at_a_time()
    expected_ids = {p.persona_id for p in personas}

    with MockStore(scenario) as store:
        targets = [Target("mock", pid, store.url_for(pid)) for pid in store.products]
        total = len(targets) * len(personas) * replicates
        store.step_after = total // 2
        plan = SweepPlan(
            sweep_id=f"validate-{scenario.value}",
            retailer_id="mock",
            targets=targets,
            personas=personas,
            replicates=replicates,
            seed=seed,
        )
        conn = connect(":memory:")
        with fetcher_factory() as fetcher:
            run_sweep(conn, plan, fetcher)
        exp = store.expected(personas)
        products = set(store.products)

    qc = run_gates(conn, plan.sweep_id, products=products, personas=expected_ids)

    cohorts: list[CohortResult] = []
    mechanisms: dict[str, Mechanism] = {}
    control_currency = "USD"

    for pid in sorted(products):
        by_currency = usable_personas_by_currency(conn, plan.sweep_id, pid)
        seen = set().union(*by_currency.values()) if by_currency else set()
        truly_missing = expected_ids - seen
        control_currency = next((c for c, ps in by_currency.items() if "control" in ps), "USD")
        currencies = set(by_currency) | ({control_currency} if truly_missing else set())

        for currency in sorted(currencies):
            usable, missing = load_cohort(conn, plan.sweep_id, pid, currency)
            present = by_currency.get(currency, set())
            expect_here = present | (truly_missing if currency == control_currency else set())
            missing = [m for m in _persona_level_missing(usable, missing) if m.persona_id in expect_here]
            result = evaluate_cohort(
                usable, threshold=threshold, expected_personas=expect_here, missing=missing
            )
            cohorts.append(result)
            if currency == control_currency and result.status is CohortStatus.COMPLETE:
                mechanisms[pid] = decompose(usable, tol=tol).mechanism

    conn.close()
    checks = _compare(exp, qc, cohorts, mechanisms, control_currency)
    return ScenarioOutcome(scenario, exp, qc, cohorts, mechanisms, checks)


def _compare(
    exp: Expectation,
    qc: SweepQC,
    cohorts: list[CohortResult],
    mechanisms: dict[str, Mechanism],
    control_currency: str,
) -> list[Check]:
    checks: list[Check] = []
    main = [c for c in cohorts if c.currency == control_currency]

    got_currencies = {c.currency for c in cohorts}
    checks.append(Check("currencies", got_currencies == set(exp.currencies),
                        f"expected {sorted(exp.currencies)}, got {sorted(got_currencies)}"))

    want_pass = exp.sweep_qc == "pass"
    checks.append(Check("sweep_qc", qc.passed == want_pass,
                        f"expected {exp.sweep_qc}, gates: {qc.summary()}"))
    failed_gates = {g.gate for g in qc.gates if not g.passed}
    checks.append(Check("failing_gates", failed_gates == set(exp.failing_gates),
                        f"expected {sorted(exp.failing_gates)}, got {sorted(failed_gates)}"))

    statuses = {c.status.value for c in main}
    checks.append(Check("cohort_status", statuses == {exp.cohort_status},
                        f"expected {exp.cohort_status}, got {sorted(statuses)}"))

    if exp.cohort_status == "incomplete":
        got_missing = {m.persona_id for c in main for m in c.missing}
        checks.append(Check("missing_personas", got_missing == set(exp.missing),
                            f"expected {sorted(exp.missing)}, got {sorted(got_missing)}"))

    if want_pass and exp.cohort_status == "complete":
        got_flagged = {f.persona_id for c in main for f in c.findings}
        checks.append(Check("flagged_personas", got_flagged == set(exp.flagged),
                            f"expected {sorted(exp.flagged)}, got {sorted(got_flagged)}"))
        if exp.direction and exp.flagged:
            dirs = {f.direction.value for c in main for f in c.findings}
            checks.append(Check("direction", dirs == {exp.direction},
                                f"expected {exp.direction}, got {sorted(dirs)}"))

    if exp.mechanism:
        got = {m.value for m in mechanisms.values()}
        checks.append(Check("mechanism", got == {exp.mechanism},
                            f"expected {exp.mechanism}, got {sorted(got)}"))
    elif want_pass and exp.cohort_status == "complete":
        wanted = Mechanism.ATTRIBUTE_CORRELATED if exp.flagged else Mechanism.NO_VARIATION
        got = {m.value for m in mechanisms.values()}
        checks.append(Check("mechanism", got == {wanted.value},
                            f"expected {wanted.value}, got {sorted(got)}"))

    return checks


def validate_all(
    fetcher_factory: Callable[[], Fetcher] = HttpFetcher,
    scenarios: list[Scenario] | None = None,
    **kwargs,
) -> list[ScenarioOutcome]:
    return [validate_scenario(s, fetcher_factory, **kwargs) for s in (scenarios or list(Scenario))]
