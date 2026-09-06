#!/usr/bin/env python3
"""Figures for the TK-HJ-OPF manuscript from locked timing.csv."""
from __future__ import annotations

import csv
import statistics
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
CSV = ROOT / "source-code" / "results-campaign" / "timing.csv"
FIG = ROOT / "manuscript" / "figures"
FIG.mkdir(parents=True, exist_ok=True)

LABEL = {
    "hjtopk": "HJ exhaustive",
    "tk-no-bounds": "No bounds",
    "tk-no-dub": "PDUB only",
    "tk-no-pdub": "DUB only",
    "tk": "Full TK-HJ",
}
SHORT = {
    "DB1_Amazon.txt": "Amazon",
    "DB2_Russell2000.txt": "Russell",
    "DB3_Nasdaq.txt": "Nasdaq",
    "DB4_SP500.txt": "S&P 500",
    "DB5_NYSE.txt": "NYSE",
    "DB6_CL_US.txt": "CL.US",
    "DB7_HPQ_US.txt": "HPQ.US",
    "DB8_GE_US.txt": "GE.US",
}
MODE_ORDER = ["hjtopk", "tk-no-bounds", "tk-no-dub", "tk-no-pdub", "tk"]
DS_ORDER = list(SHORT)


def load():
    rows = []
    with CSV.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            r["runtime_ms"] = float(r["runtime_ms"])
            r["topk"] = int(r["topk"])
            r["maxlen"] = int(r["maxlen"])
            r["k"] = float(r["k"])
            r["peak_heap_mb"] = float(r["peak_heap_mb"])
            rows.append(r)
    return rows


def median_map(rows, phase, key=("dataset", "mode")):
    g = defaultdict(list)
    for r in rows:
        if r["phase"] != phase:
            continue
        k = tuple(r[x] for x in key)
        g[k].append(r["runtime_ms"])
    return {k: statistics.median(v) for k, v in g.items()}


def style():
    plt.rcParams.update({
        "font.size": 9,
        "axes.titlesize": 10,
        "figure.dpi": 160,
        "savefig.dpi": 200,
        "axes.grid": True,
        "grid.alpha": 0.35,
    })


def fig_runtime(rows):
    med = median_map(rows, "central")
    x = np.arange(len(DS_ORDER))
    width = 0.16
    fig, ax = plt.subplots(figsize=(8.8, 4.2))
    for i, mode in enumerate(MODE_ORDER):
        ys = [med[(ds, mode)] for ds in DS_ORDER]
        ax.bar(x + (i - 2) * width, ys, width, label=LABEL[mode])
    ax.set_yscale("log")
    ax.set_xticks(x)
    ax.set_xticklabels([SHORT[d] for d in DS_ORDER], rotation=20, ha="right")
    ax.set_ylabel("Median runtime (ms)")
    ax.set_title(r"Official DB1–DB8 at $K=50$, $\ell_{\max}=12$, $k=1/n$")
    ax.legend(ncols=3, fontsize=8)
    fig.tight_layout()
    fig.savefig(FIG / "official_runtime.png")
    fig.savefig(FIG / "official_runtime.pdf")
    plt.close(fig)


def fig_speedup(rows):
    med = median_map(rows, "central")
    names = [SHORT[d] for d in DS_ORDER]
    sp = [med[(d, "hjtopk")] / med[(d, "tk")] for d in DS_ORDER]
    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    bars = ax.bar(names, sp, color="#1f4e79")
    ax.axhline(19.63, color="#c0392b", ls="--", lw=1, label="geomean 19.63×")
    ax.set_ylabel("Speedup HJ / full TK-HJ")
    ax.set_title("Per-dataset speedup at the central configuration")
    ax.legend()
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, rotation=20, ha="right")
    for b, v in zip(bars, sp):
        ax.text(b.get_x() + b.get_width() / 2, v * 1.02, f"{v:.1f}×", ha="center", va="bottom", fontsize=7)
    fig.tight_layout()
    fig.savefig(FIG / "official_speedup.png")
    fig.savefig(FIG / "official_speedup.pdf")
    plt.close(fig)


def fig_k_sens(rows):
    g = defaultdict(list)
    for r in rows:
        if r["phase"] != "K_sens":
            continue
        g[(r["dataset"], r["mode"], r["topk"])].append(r["runtime_ms"])
    med = {k: statistics.median(v) for k, v in g.items()}
    Ks = [10, 50, 100, 500]
    fig, axes = plt.subplots(1, 3, figsize=(9.2, 3.4), sharey=True)
    for ax, ds in zip(axes, ["DB1_Amazon.txt", "DB2_Russell2000.txt", "DB3_Nasdaq.txt"]):
        for mode in ["hjtopk", "tk-no-pdub", "tk"]:
            ys = [med[(ds, mode, K)] for K in Ks]
            ax.plot(Ks, ys, marker="o", label=LABEL[mode])
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xticks(Ks, [str(K) for K in Ks])
        ax.set_title(SHORT[ds])
        ax.set_xlabel(r"$K$")
    axes[0].set_ylabel("Median runtime (ms)")
    axes[2].legend(fontsize=7)
    fig.suptitle(r"$K$-sensitivity at $\ell_{\max}=12$", y=1.02)
    fig.tight_layout()
    fig.savefig(FIG / "official_K_sensitivity.png")
    fig.savefig(FIG / "official_K_sensitivity.pdf")
    plt.close(fig)


def fig_heap(rows):
    g = defaultdict(list)
    for r in rows:
        if r["phase"] != "central":
            continue
        g[(r["dataset"], r["mode"])].append(r["peak_heap_mb"])
    med = {k: statistics.median(v) for k, v in g.items()}
    x = np.arange(len(DS_ORDER))
    width = 0.35
    fig, ax = plt.subplots(figsize=(8.4, 3.8))
    hj = [med[(d, "hjtopk")] for d in DS_ORDER]
    tk = [med[(d, "tk")] for d in DS_ORDER]
    ax.bar(x - width / 2, hj, width, label="HJ exhaustive")
    ax.bar(x + width / 2, tk, width, label="Full TK-HJ")
    ax.set_xticks(x)
    ax.set_xticklabels([SHORT[d] for d in DS_ORDER], rotation=20, ha="right")
    ax.set_ylabel("Median diagnostic JVM heap (MB)")
    ax.set_title("In-process heap (not OS Peak RSS)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG / "official_heap.png")
    fig.savefig(FIG / "official_heap.pdf")
    plt.close(fig)


def fig_graphical_abstract():
    fig, ax = plt.subplots(figsize=(13.84, 5.53), dpi=120)  # ~13.8cm x 5.5cm at 96dpi * ~1.4
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 5.5)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    def box(x, y, w, h, text, fc, ec="#1a1a1a"):
        rec = plt.Rectangle((x, y), w, h, facecolor=fc, edgecolor=ec, lw=1.4, zorder=2)
        ax.add_patch(rec)
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=9, zorder=3, wrap=True)

    def arrow(x1, y1, x2, y2):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="-|>", color="#222", lw=1.5), zorder=1)

    ax.text(7, 5.15, "TK-HJ-OPF: exact top-$K$ OPF under exponential forgetting",
            ha="center", fontsize=13, fontweight="bold")
    ax.text(7, 4.72, r"$w_j=e^{-k(n-j)}$  ·  no minsup  ·  strict rank encoding",
            ha="center", fontsize=9, color="#333")

    box(0.25, 2.55, 2.15, 1.5, "Time series\n$t_1\\ldots t_n$", "#d6eaf8")
    box(2.7, 2.55, 2.25, 1.5, "Length-2\nseeds + heap\n$\\theta$", "#d5f5e3")
    box(5.25, 2.55, 2.35, 1.5, "Hash join\npre / suf\nkeys", "#fdebd0")
    box(7.9, 3.35, 2.35, 1.15, "PDUB prune\npair lineage", "#fadbd8")
    box(7.9, 2.05, 2.35, 1.15, "Fusion\nimmutable Occ", "#f9e79f")
    box(10.55, 2.55, 3.15, 1.5, "DUB prune +\ncapacity-$K$\noutput heap", "#d7bde2")

    arrow(2.4, 3.3, 2.7, 3.3)
    arrow(4.95, 3.3, 5.25, 3.3)
    arrow(7.6, 3.5, 7.9, 3.85)
    arrow(7.6, 3.1, 7.9, 2.65)
    arrow(10.25, 3.9, 10.55, 3.5)
    arrow(10.25, 2.6, 10.55, 3.1)

    ax.text(7, 1.35,
            r"Safe because $w_{j+d}=e^{kd}w_j$. PUB (direct child) cannot prune a lineage.",
            ha="center", fontsize=9)
    ax.text(7, 0.75,
            "Locked Java campaign (2026-09-06): geomean 19.63× vs exhaustive hash-join on OPF DB1–DB8.",
            ha="center", fontsize=8.5, color="#1f4e79")
    fig.tight_layout(pad=0.3)
    out = FIG / "graphical_abstract.png"
    fig.savefig(out, dpi=120)
    fig.savefig(FIG / "graphical_abstract.pdf")
    plt.close(fig)
    print("GA", out, plt.imread(out).shape)


def main():
    style()
    rows = load()
    fig_runtime(rows)
    fig_speedup(rows)
    fig_k_sens(rows)
    fig_heap(rows)
    fig_graphical_abstract()
    print("wrote", FIG)


if __name__ == "__main__":
    main()
