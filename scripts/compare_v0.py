"""Side-by-side: the v0 detector against the corrected one, on the audit scenarios.

Run: python scripts/compare_v0.py

`v0_detect` below is the logic from `G:\\My Drive\\Start Up\\analyze.py`, reimplemented
without pandas but preserving its behaviour exactly: group by product only, median over
the whole group including the row under test, one-sided comparison, non-null rows only.

This is the seed of the D0-to-D5 ablation in PROPOSAL.md section 5.2 — the same
scenarios, run against each design in the lattice, are what turn these four anecdotes
into measured error rates.
"""

from __future__ import annotations

import statistics
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from pdd.detect import CohortStatus, MissingCell, Observation, evaluate_panel  # noqa: E402
from pdd.money import Money  # noqa: E402

THRESHOLD = 0.05


# --------------------------------------------------------------------------- v0

def v0_detect(rows: list[dict]) -> list[str]:
    """The audited v0 logic. Rows with price None are dropped, as v0's SQL did."""
    live = [r for r in rows if r["price"] is not None]
    flagged = []
    by_product: dict[str, list[dict]] = {}
    for r in live:
        by_product.setdefault(r["product_id"], []).append(r)

    for product_id, group in by_product.items():
        baseline = statistics.median([r["price"] for r in group])  # includes the row under test
        if baseline == 0:
            continue
        for r in group:
            pct = (r["price"] - baseline) / baseline * 100
            if pct > THRESHOLD * 100:  # one-sided
                flagged.append(f"{r['persona']} +{pct:.2f}% (median {baseline:.2f})")
    return flagged


# ---------------------------------------------------------------------- corrected

def corrected_detect(rows: list[dict]) -> tuple[list[str], list[str]]:
    usable, missing = [], []
    for r in rows:
        if r["price"] is None:
            missing.append(MissingCell(r["persona"], r.get("reason", "no price")))
            continue
        usable.append(
            Observation(
                sweep_id=r["sweep"],
                product_id=r["product_id"],
                persona_id=r["persona"],
                price=Money(round(r["price"] * 100), r.get("currency", "USD")),
                is_control=r.get("control", False),
            )
        )

    expected = {r["persona"] for r in rows}
    notes, flagged = [], []
    for result in evaluate_panel(usable, threshold=THRESHOLD, expected_personas=expected):
        relevant = [m for m in missing if True] if result.status is CohortStatus.COMPLETE else []
        if missing and not relevant:
            pass
        if result.status is not CohortStatus.COMPLETE:
            notes.append(f"{result.sweep_id}/{result.currency}: {result.status.value}")
            continue
        for f in result.findings:
            flagged.append(
                f"{f.persona_id} {f.pct:+.2f}% ({f.direction.value}, vs {f.reference_kind})"
            )
    if missing:
        notes.append(
            "INCOMPLETE: " + ", ".join(f"{m.persona_id} ({m.reason})" for m in missing)
        )
    return flagged, notes


# ---------------------------------------------------------------------- scenarios

@dataclass
class Scenario:
    name: str
    truth: str
    rows: list[dict]


def row(sweep, persona, price, product="sku1", control=False, currency="USD", reason=None):
    return dict(
        sweep=sweep, persona=persona, price=price, product_id=product,
        control=control, currency=currency, reason=reason,
    )


SCENARIOS = [
    Scenario(
        "Retailer raises price $100 -> $115 between sweeps",
        "NOTHING — no persona was treated differently",
        [
            *(row("sweep-1", p, 100.00) for p in ("us_east", "us_west", "mobile")),
            *(row("sweep-2", p, 115.00) for p in ("us_east", "us_west", "mobile")),
        ],
    ),
    Scenario(
        "Mobile persona shown a 17% targeted discount",
        "FLAG mobile — a 16.7% discount",
        [
            row("sweep-1", "us_east", 120.00),
            row("sweep-1", "us_west", 120.00),
            row("sweep-1", "mobile", 100.00),
        ],
    ),
    Scenario(
        "Two personas shifted high, one at the true price",
        "FLAG the outlier — a 16.7% gap exists",
        [
            row("sweep-1", "a", 100.00),
            row("sweep-1", "b", 120.00),
            row("sweep-1", "c", 120.00),
        ],
    ),
    Scenario(
        "Mobile persona blocked by anti-bot",
        "REPORT INCOMPLETE — not a clean null",
        [
            row("sweep-1", "us_east", 100.00),
            row("sweep-1", "us_west", 100.00),
            row("sweep-1", "mobile", None, reason="canary: bot_page"),
        ],
    ),
    Scenario(
        "Same 17% discount, but with a control persona in the cohort",
        "FLAG mobile ONLY — the control identifies which persona moved",
        [
            row("sweep-1", "control", 120.00, control=True),
            row("sweep-1", "us_east", 120.00),
            row("sweep-1", "us_west", 120.00),
            row("sweep-1", "mobile", 100.00),
        ],
    ),
]


def main() -> None:
    print("=" * 78)
    print("v0 detector vs corrected detector — audit scenarios")
    print(f"threshold: {THRESHOLD:.0%}")
    print("=" * 78)

    wrong_v0 = 0
    for i, sc in enumerate(SCENARIOS, 1):
        v0 = v0_detect(sc.rows)
        new_flags, new_notes = corrected_detect(sc.rows)

        print(f"\n{i}. {sc.name}")
        print(f"   ground truth : {sc.truth}")
        print(f"   v0           : {', '.join(v0) if v0 else 'nothing flagged'}")
        out = new_flags + new_notes
        print(f"   corrected    : {', '.join(out) if out else 'nothing flagged'}")

        expects_flag = sc.truth.startswith(("FLAG", "REPORT"))
        v0_right = bool(v0) == expects_flag and not (sc.truth.startswith("REPORT") and v0)
        if not v0_right:
            wrong_v0 += 1
            print("   -> v0 WRONG")

    print("\n" + "=" * 78)
    print(f"v0 reported the wrong outcome on {wrong_v0} of {len(SCENARIOS)} scenarios.")
    print()
    print("Note scenarios 2 and 3 against 5. Without a control persona, a leave-one-out")
    print("baseline detects that a cohort is dispersed but cannot say which persona")
    print("moved — every member deviates from the median of the others. Adding the")
    print("control arm resolves it to the one persona that actually differs.")
    print()
    print("That contrast is the D3-to-D2 step of the ablation in PROPOSAL.md 5.2, and")
    print("quantifying it across conditions is what RQ2 asks.")
    print("=" * 78)


if __name__ == "__main__":
    main()
