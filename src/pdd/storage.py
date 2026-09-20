"""SQLite storage for the observation panel.

Thin by design. The schema carries the invariants (see `schema.py`); this module only
opens connections with the settings that make those invariants real — SQLite does not
enforce foreign keys unless asked — and loads analysis-eligible cohorts back out.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from pathlib import Path

from .detect import MissingCell, Observation
from .money import Money
from .schema import DDL, SCHEMA_VERSION


def connect(db_path: str | Path) -> sqlite3.Connection:
    path = Path(db_path)
    if path.name != ":memory:":
        path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    # Off by default in SQLite; without it the sweep_id reference is decorative.
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(DDL)
    conn.execute(
        "INSERT OR REPLACE INTO schema_meta (key, value) VALUES ('version', ?)",
        (str(SCHEMA_VERSION),),
    )
    conn.commit()
    return conn


def open_sweep(
    conn: sqlite3.Connection, sweep_id: str, retailer_id: str, started_at: str, seed: int
) -> None:
    conn.execute(
        "INSERT INTO sweeps (sweep_id, retailer_id, started_at, seed) VALUES (?,?,?,?)",
        (sweep_id, retailer_id, started_at, seed),
    )
    conn.commit()


def record(conn: sqlite3.Connection, **fields) -> int:
    """Insert one observation. Unknown columns raise rather than being dropped."""
    cols = ", ".join(fields)
    placeholders = ", ".join("?" for _ in fields)
    cur = conn.execute(
        f"INSERT INTO observations ({cols}) VALUES ({placeholders})", tuple(fields.values())
    )
    conn.commit()
    return int(cur.lastrowid or 0)


def load_cohort(
    conn: sqlite3.Connection, sweep_id: str, product_id: str, currency: str
) -> tuple[list[Observation], list[MissingCell]]:
    """Load one cohort, returning usable observations *and* the cells that failed.

    Returning both is the point. The v0 analysis issued `WHERE price IS NOT NULL` and
    never read the `error` column, so blocked personas vanished and the caller could not
    tell an incomplete cohort from a clean one (defect B3). Here the failures come back
    alongside the prices and the caller cannot avoid seeing them.
    """
    rows = conn.execute(
        """
        SELECT persona_id, replicate_idx, is_control, price_minor_units, currency,
               parse_status, canary_status, error
        FROM observations
        WHERE sweep_id = ? AND product_id = ?
          AND (currency = ? OR currency IS NULL)
        ORDER BY persona_id, replicate_idx
        """,
        (sweep_id, product_id, currency),
    ).fetchall()

    usable: list[Observation] = []
    missing: list[MissingCell] = []

    for r in rows:
        if r["canary_status"] == "bot_page":
            missing.append(MissingCell(r["persona_id"], "canary: bot_page"))
        elif r["parse_status"] != "ok" or r["price_minor_units"] is None:
            reason = r["error"] or f"parse_status: {r['parse_status']}"
            missing.append(MissingCell(r["persona_id"], reason))
        else:
            usable.append(
                Observation(
                    sweep_id=sweep_id,
                    product_id=product_id,
                    persona_id=r["persona_id"],
                    price=Money(r["price_minor_units"], r["currency"]),
                    replicate_idx=r["replicate_idx"],
                    is_control=bool(r["is_control"]),
                )
            )

    return usable, missing


def cohort_keys(conn: sqlite3.Connection) -> Iterator[tuple[str, str, str]]:
    """Every (sweep, product, currency) triple present in the panel."""
    yield from (
        (r["sweep_id"], r["product_id"], r["currency"])
        for r in conn.execute(
            """
            SELECT DISTINCT sweep_id, product_id, currency FROM observations
            WHERE currency IS NOT NULL ORDER BY sweep_id, product_id, currency
            """
        )
    )
