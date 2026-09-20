"""Figures for the simulation results, from results/ablation_summary.csv.

    python scripts/make_figures.py

Static PNGs for the README and paper. Marks and chrome follow one set of specs:
thin bars, 2px lines, >= 8px markers with a surface ring, hairline solid gridlines,
text in ink tokens (never the series color), selective direct labels, and a legend
whenever there are two or more series. Categorical hues are assigned in a fixed,
validated order and never cycled.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

RESULTS = Path(__file__).resolve().parent.parent / "results"
FIG = RESULTS / "figures"

# Reference palette, light surface. Slots 1-4 in validated order.
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]
SURFACE, INK, INK2, MUTED, GRID, BASELINE = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
DESIGNS = ["D0", "D1", "D2", "D3", "D4", "D5", "D6"]

plt.rcParams.update({
    "font.family": ["Segoe UI", "DejaVu Sans", "sans-serif"],
    "font.size": 10,
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "text.color": INK, "axes.labelcolor": INK2, "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.edgecolor": BASELINE, "axes.linewidth": 1,
    "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 1, "grid.linestyle": "-", "axes.axisbelow": True,
    "xtick.major.size": 0, "ytick.major.size": 0,
    "axes.titlesize": 10.5, "axes.titleweight": "semibold", "axes.titlelocation": "left",
    "legend.frameon": False, "legend.fontsize": 9,
})


def _style(ax) -> None:
    ax.grid(axis="x", visible=False)
    ax.tick_params(axis="both", labelsize=9)


def _pct(ax) -> None:
    ax.set_ylim(0, 1.04)
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"])


def _headline(fig, title: str, standfirst: str) -> None:
    fig.text(0.01, 0.975, title, fontsize=12.5, fontweight="semibold", color=INK, va="top")
    fig.text(0.01, 0.925, standfirst, fontsize=9, color=INK2, va="top", wrap=True)


def _save(fig, name: str) -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG / name, dpi=160)
    plt.close(fig)
    print(f"wrote {FIG / name}")


# ------------------------------------------------------------------ figure 1


def fig1(s: pd.DataFrame) -> None:
    a = s[(s.grid == "A") & (s.effect == "none")]
    drifts = [("none", "No drift"), ("slow", "Slow drift, +2% per sweep"),
              ("fast", "Fast drift, +5% per sweep"), ("step", "Step of +15% mid-sweep")]
    fig, axes = plt.subplots(1, 4, figsize=(12.5, 3.9), sharey=True)
    for ax, (d, title) in zip(axes, drifts):
        sub = a[a.drift == d].set_index("design").reindex(DESIGNS)
        fpr = sub.false_positive_rate.fillna(0.0)
        x = np.arange(len(DESIGNS))
        ax.bar(x, fpr.values, width=0.5, color=SERIES[0], linewidth=0)
        abstained = [i for i, dn in enumerate(DESIGNS) if sub.abstain_rate[dn] >= 0.99]
        if abstained:
            names = "–".join(DESIGNS[i] for i in (abstained[0], abstained[-1])) if len(abstained) > 1 else DESIGNS[abstained[0]]
            ax.text(np.mean(abstained), 0.04, f"{names} abstain\n(G4 fails)", ha="center", va="bottom",
                    fontsize=8, color=MUTED)
        if fpr.max() > 0:
            i = int(np.argmax(fpr.values))
            ax.text(i, fpr.values[i] + 0.02, f"{fpr.values[i]:.0%}", ha="center", va="bottom", fontsize=9, color=INK2)
        ax.set_xticks(x)
        ax.set_xticklabels(DESIGNS)
        ax.set_title(title)
        _style(ax)
        _pct(ax)
    axes[0].set_ylabel("False-positive rate")
    _headline(fig, "Single-observation designs read price drift as discrimination",
              "No effect injected. Share of analysed cohorts with at least one persona flagged. "
              "Two-sided designs (D2–D4) are more exposed to a mid-sweep step than one-sided D1; "
              "D5–D6 abstain on it because the control moved.")
    fig.tight_layout(rect=(0, 0, 1, 0.86))
    _save(fig, "fig1_false_positives_by_drift.png")


# ------------------------------------------------------------------ figure 2


def fig2(s: pd.DataFrame) -> None:
    b = s[(s.grid == "B") & (s.design == "D6")]
    truths = [("none", False, "No variation"), ("premium", False, "Attribute effect"),
              ("none", True, "Random buckets (A/B)"), ("premium", True, "Mixed")]
    fig, ax = plt.subplots(figsize=(7.5, 4.3))
    ends: list[tuple[float, str, str]] = []
    for i, (e, ab, label) in enumerate(truths):
        sub = b[(b.effect == e) & (b.ab_test == ab)].sort_values("k")
        ax.plot(sub.k, sub.mechanism_accuracy, color=SERIES[i], linewidth=2,
                solid_joinstyle="round", solid_capstyle="round", label=label,
                marker="o", markersize=8, markeredgecolor=SURFACE, markeredgewidth=2, zorder=3)
        ends.append((float(sub.mechanism_accuracy.iloc[-1]), label, SERIES[i]))
    # Direct end-labels only where they do not collide; the legend carries the rest.
    placed: list[float] = []
    for y, label, _ in sorted(ends, reverse=True):
        if all(abs(y - p) > 0.06 for p in placed):
            ax.text(8.25, y, label, va="center", fontsize=9, color=INK2)
            placed.append(y)
    ax.set_xticks([1, 2, 3, 5, 8])
    ax.set_xlim(0.6, 10.2)
    ax.set_xlabel("Replicates per cell, k")
    ax.set_ylabel("Mechanism classification accuracy")
    _pct(ax)
    _style(ax)
    ax.legend(loc="lower right", bbox_to_anchor=(0.995, 0.03))
    _headline(fig, "Separating A/B buckets from an attribute effect needs replicates",
              "D6 per-cohort classification against the true mechanism, by replicate count. k = 1 cannot classify. "
              "No variation and Attribute effect coincide at 100% from k = 2; the two random-bucket cases are the story.")
    fig.tight_layout(rect=(0, 0, 1, 0.86))
    _save(fig, "fig2_mechanism_accuracy_by_k.png")


# ------------------------------------------------------------------ figure 3


def fig3(s: pd.DataFrame) -> None:
    c = s[(s.grid == "C") & (s.effect == "premium")]
    blocks = [("none", "No blocking"), ("uniform", "Uniform blocking, 20%"),
              ("differential", "Differential blocking, target 50%")]
    rows = [("power_any", "Power (target flagged)"), ("abstain_rate", "Abstain rate")]
    fig, axes = plt.subplots(2, 3, figsize=(12.5, 6.6), sharey="row")
    x = np.arange(len(DESIGNS))
    w = 0.34
    for j, (bk, title) in enumerate(blocks):
        for r, (metric, ylabel) in enumerate(rows):
            ax = axes[r, j]
            for i, corr in enumerate((0.0, 0.1)):
                sub = c[(c.blocking == bk) & (c.parse_corruption == corr)].set_index("design").reindex(DESIGNS)
                ax.bar(x + (i - 0.5) * (w + 0.05), sub[metric].fillna(0.0).values, width=w,
                       color=SERIES[i], linewidth=0, label=f"parse corruption {corr:.0%}")
            ax.set_xticks(x)
            ax.set_xticklabels(DESIGNS)
            _pct(ax)
            _style(ax)
            if r == 0:
                ax.set_title(title)
            if j == 0:
                ax.set_ylabel(ylabel)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper right", bbox_to_anchor=(0.995, 0.905), ncol=2)
    _headline(fig, "Blocking and parse corruption: silent loss versus visible abstention",
              "10% premium on the target persona. D0–D4 lose a blocked target silently (power falls, abstain stays 0); "
              "D5–D6 report the cohort incomplete instead. Only D6 refuses corrupt parses.")
    fig.tight_layout(rect=(0, 0, 1, 0.87))
    _save(fig, "fig3_blocking_and_parsing.png")


# ------------------------------------------------------------------ figure 4


def fig4(s: pd.DataFrame) -> None:
    d = s[(s.grid == "D") & (s.design == "D6")].sort_values("effect_size")
    fig, ax = plt.subplots(figsize=(6.5, 3.9))
    ax.plot(d.effect_size, d.power_strict, color=SERIES[0], linewidth=2, marker="o",
            markersize=8, markeredgecolor=SURFACE, markeredgewidth=2, zorder=3)
    ax.axvline(0.05, color=BASELINE, linewidth=1, zorder=1)
    ax.text(0.0515, 0.04, "flag threshold, 5%", rotation=90, va="bottom", fontsize=8, color=MUTED)
    ax.set_xticks(d.effect_size.values)
    ax.set_xticklabels([f"{e:.0%}" for e in d.effect_size])
    ax.set_xlabel("Injected effect on the target persona")
    ax.set_ylabel("Power (target only)")
    _pct(ax)
    _style(ax)
    _headline(fig, "Power is a step function of the flag threshold at this noise level",
              "D6, k = 3, no drift, 0.5% multiplicative noise. Effects below the 5% threshold are invisible by construction; "
              "the threshold is a pre-registered constant, not a tuned one.")
    fig.tight_layout(rect=(0, 0, 1, 0.84))
    _save(fig, "fig4_power_by_effect_size.png")


def main() -> int:
    path = RESULTS / "ablation_summary.csv"
    if not path.exists():
        print(f"missing {path}; run scripts/run_ablation.py first", file=sys.stderr)
        return 1
    s = pd.read_csv(path)
    fig1(s)
    fig2(s)
    fig3(s)
    fig4(s)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
