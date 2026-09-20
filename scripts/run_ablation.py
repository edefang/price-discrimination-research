"""Run the simulation grids from PROPOSAL.md section 5 and write results/.

    python scripts/run_ablation.py            # full run
    python scripts/run_ablation.py --quick    # fewer panels, for a smoke test

Outputs (all under results/):
    ablation_rows.csv     one row per (grid, condition, design, panel)
    ablation_summary.csv  means and 95% CI half-widths per (grid, condition, design)
    summary.md            the headline tables, ready to paste into the paper

Every number is reproducible from the seed recorded in each row.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from pdd.simulate import LATTICE, Condition, run_condition  # noqa: E402

RESULTS = Path(__file__).resolve().parent.parent / "results"
SEED = 20260919


def grid_a() -> list[tuple[str, Condition, int]]:
    """RQ1/RQ2: effect x drift, all designs, k=3."""
    out = []
    for effect in ("none", "premium", "discount"):
        for drift, rate in (("none", 0.0), ("slow", 0.02), ("fast", 0.05), ("step", 0.15)):
            out.append(("A", Condition(effect=effect, drift=drift, drift_rate=rate), 3))
    return out


def grid_b() -> list[tuple[str, Condition, int]]:
    """RQ3: mechanism separation as a function of k."""
    out = []
    for effect in ("none", "premium"):
        for ab in (False, True):
            for k in (1, 2, 3, 5, 8):
                out.append(("B", Condition(effect=effect, ab_test=ab), k))
    return out


def grid_c() -> list[tuple[str, Condition, int]]:
    """RQ4: blocking and parse corruption."""
    out = []
    for effect in ("none", "premium"):
        for blocking, rate in (("none", 0.0), ("uniform", 0.2), ("differential", 0.5)):
            for corruption in (0.0, 0.1):
                out.append(("C", Condition(effect=effect, blocking=blocking, block_rate=rate,
                                           parse_corruption=corruption), 3))
    return out


def grid_d() -> list[tuple[str, Condition, int]]:
    """Power curve: effect size, D6 only reported but all designs run."""
    return [("D", Condition(effect="premium", effect_size=e), 3)
            for e in (0.02, 0.04, 0.06, 0.08, 0.10, 0.15)]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--panels", type=int, default=None)
    args = ap.parse_args()
    n_panels = args.panels or (20 if args.quick else 200)

    RESULTS.mkdir(exist_ok=True)
    specs = grid_a() + grid_b() + grid_c() + grid_d()
    rows: list[dict] = []
    t0 = time.perf_counter()
    for i, (grid, cond, k) in enumerate(specs, 1):
        designs = [d for d in LATTICE if d.replicates] if grid == "B" else LATTICE
        for r in run_condition(cond, designs, n_panels=n_panels, seed=SEED + i, k=k):
            r["grid"] = grid
            rows.append(r)
        print(f"[{i:>2}/{len(specs)}] grid {grid} {cond.effect:<8} drift={cond.drift:<5} "
              f"ab={int(cond.ab_test)} block={cond.blocking:<12} corrupt={cond.parse_corruption} "
              f"k={k}  ({time.perf_counter() - t0:.0f}s)")

    df = pd.DataFrame(rows)
    df.to_csv(RESULTS / "ablation_rows.csv", index=False)

    keys = ["grid", "effect", "effect_size", "drift", "drift_rate", "ab_test", "ab_size",
            "blocking", "block_rate", "parse_corruption", "noise_sd", "k", "design"]
    metrics = ["false_positive_rate", "power_strict", "power_any", "misattribution_rate",
               "abstain_rate", "mechanism_accuracy", "mechanism_classifiable_rate"]
    g = df.groupby(keys)[metrics]
    summary = g.mean().join(g.sem().mul(1.96).add_suffix("_ci95"))
    summary["n_panels"] = g.size()
    summary = summary.reset_index()
    summary.to_csv(RESULTS / "ablation_summary.csv", index=False)

    write_summary_md(summary, n_panels)
    print(f"\nwrote {RESULTS / 'ablation_rows.csv'} ({len(df)} rows) and summary in {time.perf_counter() - t0:.0f}s")
    return 0


def _pct(x: float) -> str:
    return "—" if pd.isna(x) else f"{100 * x:.1f}%"


def write_summary_md(s: pd.DataFrame, n_panels: int) -> None:
    lines = [f"# Simulation summary\n", f"{n_panels} panels per condition; 20 products x 5 sweeps per panel; "
             f"threshold 5%; seed {SEED}. Rates are over analysed cohorts; abstain is over all cohorts.\n"]

    a = s[s.grid == "A"]
    lines.append("\n## Grid A — false positives under temporal drift (no effect injected)\n")
    lines.append("| drift | " + " | ".join(d.name for d in LATTICE) + " |")
    lines.append("|---|" + "---|" * len(LATTICE))
    for drift in ("none", "slow", "fast", "step"):
        sub = a[(a.effect == "none") & (a.drift == drift)].set_index("design")
        lines.append(f"| {drift} | " + " | ".join(_pct(sub.loc[d.name, "false_positive_rate"]) for d in LATTICE) + " |")
    lines.append("\nAbstain rate (cohorts excluded by QC), same conditions:\n")
    lines.append("| drift | " + " | ".join(d.name for d in LATTICE) + " |")
    lines.append("|---|" + "---|" * len(LATTICE))
    for drift in ("none", "slow", "fast", "step"):
        sub = a[(a.effect == "none") & (a.drift == drift)].set_index("design")
        lines.append(f"| {drift} | " + " | ".join(_pct(sub.loc[d.name, "abstain_rate"]) for d in LATTICE) + " |")

    lines.append("\n## Grid A — power (10% effect, no drift)\n")
    lines.append("| effect | metric | " + " | ".join(d.name for d in LATTICE) + " |")
    lines.append("|---|---|" + "---|" * len(LATTICE))
    for effect in ("premium", "discount"):
        sub = a[(a.effect == effect) & (a.drift == "none")].set_index("design")
        for m, label in (("power_strict", "target only"), ("power_any", "target flagged"), ("misattribution_rate", "non-target flagged")):
            lines.append(f"| {effect} | {label} | " + " | ".join(_pct(sub.loc[d.name, m]) for d in LATTICE) + " |")

    b = s[s.grid == "B"]
    lines.append("\n## Grid B — mechanism classification accuracy by replicate count (D6)\n")
    lines.append("| truth | k=1 | k=2 | k=3 | k=5 | k=8 |")
    lines.append("|---|---|---|---|---|---|")
    for effect, ab, label in (("none", False, "none"), ("premium", False, "attribute"), ("none", True, "random (A/B)"), ("premium", True, "mixed")):
        sub = b[(b.effect == effect) & (b.ab_test == ab) & (b.design == "D6")].set_index("k")
        lines.append(f"| {label} | " + " | ".join(_pct(sub.loc[k, "mechanism_accuracy"]) if k in sub.index else "—" for k in (1, 2, 3, 5, 8)) + " |")

    c = s[s.grid == "C"]
    lines.append("\n## Grid C — degradation (10% premium effect)\n")
    lines.append("| blocking | parse corruption | metric | " + " | ".join(d.name for d in LATTICE) + " |")
    lines.append("|---|---|---|" + "---|" * len(LATTICE))
    for blocking in ("none", "uniform", "differential"):
        for corr in (0.0, 0.1):
            sub = c[(c.effect == "premium") & (c.blocking == blocking) & (c.parse_corruption == corr)].set_index("design")
            for m, label in (("power_any", "power"), ("abstain_rate", "abstain")):
                lines.append(f"| {blocking} | {corr} | {label} | " + " | ".join(_pct(sub.loc[d.name, m]) for d in LATTICE) + " |")
    lines.append("\nFalse positives under parse corruption, no effect:\n")
    lines.append("| blocking | parse corruption | " + " | ".join(d.name for d in LATTICE) + " |")
    lines.append("|---|---|" + "---|" * len(LATTICE))
    for blocking in ("none", "uniform", "differential"):
        for corr in (0.0, 0.1):
            sub = c[(c.effect == "none") & (c.blocking == blocking) & (c.parse_corruption == corr)].set_index("design")
            lines.append(f"| {blocking} | {corr} | " + " | ".join(_pct(sub.loc[d.name, "false_positive_rate"]) for d in LATTICE) + " |")

    d_ = s[(s.grid == "D") & (s.design == "D6")].set_index("effect_size")
    lines.append("\n## Grid D — D6 power by effect size (premium, no drift, k=3, threshold 5%)\n")
    lines.append("| effect size | " + " | ".join(f"{e:.0%}" for e in d_.index) + " |")
    lines.append("|---|" + "---|" * len(d_.index))
    lines.append("| power (target only) | " + " | ".join(_pct(v) for v in d_["power_strict"]) + " |")

    (RESULTS / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
