"""Quality-control gates (measurement protocol, section 5).

A sweep enters the analysis panel only if it passes all four. Each gate reports what
it found, not just whether it passed, because the exclusion accounting is part of the
result: a null produced by heavy exclusion is a different claim from a null on a
complete panel.

G4 is the one to understand. It checks that the control persona's price was identical
across all of its replicates within the sweep. If it moved, the retailer's own price
changed during the window, and within-sweep comparison is invalid for that sweep. This
is the direct guard against the v0 prototype's fatal defect — reading an ordinary
price change as discrimination — and it only works because the sweep runner spreads
the control replicates across the visit order.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass


@dataclass(frozen=True)
class GateResult:
    gate: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class SweepQC:
    sweep_id: str
    gates: tuple[GateResult, ...]

    @property
    def passed(self) -> bool:
        return all(g.passed for g in self.gates)

    def gate(self, name: str) -> GateResult:
        return next(g for g in self.gates if g.gate == name)

    def summary(self) -> str:
        return "; ".join(f"{g.gate}:{'pass' if g.passed else 'FAIL'}" for g in self.gates)


_USABLE = "parse_status = 'ok' AND canary_status = 'real_page' AND price_minor_units IS NOT NULL"


def g1_completeness(
    conn: sqlite3.Connection, sweep_id: str, products: set[str], personas: set[str]
) -> GateResult:
    """Every (product, persona) cell has at least one usable observation."""
    rows = conn.execute(
        f"SELECT DISTINCT product_id, persona_id FROM observations "
        f"WHERE sweep_id = ? AND {_USABLE}",
        (sweep_id,),
    ).fetchall()
    present = {(r["product_id"], r["persona_id"]) for r in rows}
    missing = sorted(
        (p, q) for p in products for q in personas if (p, q) not in present
    )
    if not missing:
        return GateResult("G1", True, f"{len(present)} cells complete")
    return GateResult(
        "G1", False,
        f"{len(missing)} cell(s) without a usable price: "
        + ", ".join(f"{p}/{q}" for p, q in missing[:8])
        + (" ..." if len(missing) > 8 else ""),
    )


def g2_canary(conn: sqlite3.Connection, sweep_id: str) -> GateResult:
    """No observation was a bot or challenge page."""
    rows = conn.execute(
        "SELECT persona_id, COUNT(*) AS n FROM observations "
        "WHERE sweep_id = ? AND canary_status = 'bot_page' GROUP BY persona_id",
        (sweep_id,),
    ).fetchall()
    if not rows:
        return GateResult("G2", True, "no bot pages")
    return GateResult(
        "G2", False,
        "bot page served to: " + ", ".join(f"{r['persona_id']} x{r['n']}" for r in rows),
    )


def g3_parse_confidence(conn: sqlite3.Connection, sweep_id: str) -> GateResult:
    """No observation carries an unresolved parse."""
    rows = conn.execute(
        "SELECT parse_status, COUNT(*) AS n FROM observations "
        "WHERE sweep_id = ? AND parse_status IN ('ambiguous','multiple_candidates') "
        "GROUP BY parse_status",
        (sweep_id,),
    ).fetchall()
    if not rows:
        return GateResult("G3", True, "all parses unambiguous")
    return GateResult(
        "G3", False, ", ".join(f"{r['parse_status']} x{r['n']}" for r in rows)
    )


def g4_control_stability(conn: sqlite3.Connection, sweep_id: str) -> GateResult:
    """The control persona's price is identical across its replicates, per product."""
    rows = conn.execute(
        f"SELECT product_id, currency, COUNT(DISTINCT price_minor_units) AS k, "
        f"MIN(price_minor_units) AS lo, MAX(price_minor_units) AS hi, COUNT(*) AS n "
        f"FROM observations WHERE sweep_id = ? AND is_control = 1 AND {_USABLE} "
        f"GROUP BY product_id, currency",
        (sweep_id,),
    ).fetchall()
    if not rows:
        return GateResult("G4", False, "no usable control observations")
    unstable = [r for r in rows if r["k"] > 1]
    if not unstable:
        return GateResult(
            "G4", True, f"control stable across {sum(r['n'] for r in rows)} replicate(s)"
        )
    return GateResult(
        "G4", False,
        "control moved within the sweep: "
        + ", ".join(
            f"{r['product_id']} {r['lo']}->{r['hi']} {r['currency']} ({r['k']} distinct)"
            for r in unstable
        ),
    )


def run_gates(
    conn: sqlite3.Connection, sweep_id: str, *, products: set[str], personas: set[str]
) -> SweepQC:
    qc = SweepQC(
        sweep_id,
        (
            g1_completeness(conn, sweep_id, products, personas),
            g2_canary(conn, sweep_id),
            g3_parse_confidence(conn, sweep_id),
            g4_control_stability(conn, sweep_id),
        ),
    )
    conn.execute(
        "UPDATE sweeps SET qc_status = ?, qc_detail = ? WHERE sweep_id = ?",
        ("pass" if qc.passed else "fail", qc.summary(), sweep_id),
    )
    conn.commit()
    return qc
