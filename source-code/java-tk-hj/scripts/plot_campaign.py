#!/usr/bin/env python3
"""Figures for the TK-HJ-OPF manuscript from locked campaign CSVs."""
from __future__ import annotations

import argparse
import csv
import math
import statistics
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CSV = ROOT / "source-code" / "results-campaign" / "timing.csv"
DEFAULT_FIG = ROOT / "latex-submit" / "figures"
DEFAULT_PUBLIC = ROOT / "source-code" / "results-campaign" / "full_paper1.csv"
DEFAULT_RSS = ROOT / "source-code" / "results-campaign" / "full_paper1_rss.csv"
DEFAULT_SUBMIT = ROOT / "latex-submit" / "figures"

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
PUBLIC_SHORT = {
    "SILSO_sunspots.txt": "SILSO",
    "NASDAQCOM.txt": "NASDAQCOM",
    "FRED_SP500.txt": "S&P 500 (FRED)",
}
PUBLIC_ORDER = list(PUBLIC_SHORT)
RSS_SHORT = {**SHORT, **PUBLIC_SHORT}
RSS_ORDER = list(SHORT) + list(PUBLIC_SHORT)


def geomean(xs: list[float]) -> float:
    return math.exp(sum(math.log(x) for x in xs) / len(xs))


def load_csv(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            r["runtime_ms"] = float(r["runtime_ms"])
            if "topk" in r:
                r["topk"] = int(r["topk"])
            if "maxlen" in r:
                r["maxlen"] = int(r["maxlen"])
            if "k" in r:
                r["k"] = float(r["k"])
            if "n" in r:
                r["n"] = int(r["n"])
            if "peak_heap_mb" in r:
                r["peak_heap_mb"] = float(r["peak_heap_mb"])
            if "aligned_checks" in r:
                r["aligned_checks"] = int(r["aligned_checks"])
            rows.append(r)
    return rows


def median_map(rows, phase, key=("dataset", "mode")):
    g = defaultdict(list)
    for r in rows:
        if r.get("phase") != phase:
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


def save(fig, name: str, dests: list[Path]) -> None:
    for dest in dests:
        dest.mkdir(parents=True, exist_ok=True)
        fig.savefig(dest / f"{name}.png")
        fig.savefig(dest / f"{name}.pdf")


def fig_runtime(rows, dests):
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
    save(fig, "official_runtime", dests)
    plt.close(fig)


def fig_speedup(rows, dests):
    med = median_map(rows, "central")
    names = [SHORT[d] for d in DS_ORDER]
    sp = [med[(d, "hjtopk")] / med[(d, "tk")] for d in DS_ORDER]
    gm = geomean(sp)
    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    bars = ax.bar(names, sp, color="#1f4e79")
    ax.axhline(gm, color="#c0392b", ls="--", lw=1, label=f"geomean {gm:.2f}×")
    ax.set_ylabel("Speedup HJ / full TK-HJ")
    ax.set_title("Per-dataset speedup at the central configuration")
    ax.legend()
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, rotation=20, ha="right")
    for b, v in zip(bars, sp):
        ax.text(b.get_x() + b.get_width() / 2, v * 1.02, f"{v:.1f}×", ha="center", va="bottom", fontsize=7)
    fig.tight_layout()
    save(fig, "official_speedup", dests)
    plt.close(fig)
    return gm, sp


def fig_k_sens(rows, dests):
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
    save(fig, "official_K_sensitivity", dests)
    plt.close(fig)


def fig_l_sens(rows, dests):
    g = defaultdict(list)
    for r in rows:
        if r["phase"] != "L_sens":
            continue
        g[(r["mode"], r["maxlen"])].append(r["runtime_ms"])
    if not g:
        return
    med = {k: statistics.median(v) for k, v in g.items()}
    Ls = [8, 12, 16]
    fig, ax = plt.subplots(figsize=(6.2, 3.6))
    for mode in ["hjtopk", "tk-no-pdub", "tk"]:
        ys = [med[(mode, L)] for L in Ls]
        ax.plot(Ls, ys, marker="o", label=LABEL[mode])
    ax.set_yscale("log")
    ax.set_xticks(Ls)
    ax.set_xlabel(r"$\ell_{\max}$")
    ax.set_ylabel("Median runtime (ms)")
    ax.set_title(r"Amazon length sensitivity at $K=50$")
    ax.legend(fontsize=8)
    fig.tight_layout()
    save(fig, "official_L_sensitivity", dests)
    plt.close(fig)


def fig_kforget_sens(rows, dests):
    g = defaultdict(list)
    n_of = {}
    for r in rows:
        if r["phase"] != "k_sens":
            continue
        n_of[r["dataset"]] = r["n"]
        factor = round(r["k"] * r["n"], 6)
        g[(r["dataset"], r["mode"], factor)].append(r["runtime_ms"])
    if not g:
        return
    med = {k: statistics.median(v) for k, v in g.items()}
    factors = [0.25, 0.5, 1.0, 2.0, 4.0]
    dss = ["DB1_Amazon.txt", "DB8_GE_US.txt"]
    fig, axes = plt.subplots(1, 2, figsize=(8.4, 3.5), sharey=True)
    for ax, ds in zip(axes, dss):
        for mode in ["hjtopk", "tk-no-pdub", "tk"]:
            ys = []
            for c in factors:
                key = (ds, mode, round(c, 6))
                if key in med:
                    ys.append(med[key])
                else:
                    cands = [kk for (d, m, kk) in med if d == ds and m == mode]
                    nearest = min(cands, key=lambda x: abs(x - c)) if cands else None
                    ys.append(med[(ds, mode, nearest)] if nearest is not None else float("nan"))
            ax.plot(factors, ys, marker="o", label=LABEL[mode])
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xticks(factors, [str(c) for c in factors])
        ax.set_title(SHORT[ds])
        ax.set_xlabel(r"$k\cdot n$")
    axes[0].set_ylabel("Median runtime (ms)")
    axes[1].legend(fontsize=7)
    fig.suptitle(r"Forgetting-factor sensitivity at $K=50$, $\ell_{\max}=12$", y=1.02)
    fig.tight_layout()
    save(fig, "official_forget_sensitivity", dests)
    plt.close(fig)


def fig_heap(rows, dests):
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
    save(fig, "official_heap", dests)
    plt.close(fig)


def fig_search_space(rows, dests):
    g = defaultdict(list)
    for r in rows:
        if r["phase"] != "central":
            continue
        g[(r["dataset"], r["mode"])].append(r["aligned_checks"])
    med = {k: statistics.median(v) for k, v in g.items()}
    x = np.arange(len(DS_ORDER))
    width = 0.35
    fig, ax = plt.subplots(figsize=(8.4, 3.8))
    hj = [med[(d, "hjtopk")] for d in DS_ORDER]
    tk = [med[(d, "tk")] for d in DS_ORDER]
    ax.bar(x - width / 2, hj, width, label="HJ exhaustive")
    ax.bar(x + width / 2, tk, width, label="Full TK-HJ")
    ax.set_yscale("log")
    ax.set_xticks(x)
    ax.set_xticklabels([SHORT[d] for d in DS_ORDER], rotation=20, ha="right")
    ax.set_ylabel("Median aligned occurrence checks")
    ax.set_title(r"Search-space reduction at $K=50$, $\ell_{\max}=12$")
    ax.legend()
    fig.tight_layout()
    save(fig, "official_search_space", dests)
    plt.close(fig)


def fig_graphical_abstract(gm: float, dests):
    fig, ax = plt.subplots(figsize=(13.84, 5.53), dpi=120)
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
            f"Locked Java campaign: geomean {gm:.2f}× vs exhaustive hash-join on OPF DB1–DB8.",
            ha="center", fontsize=8.5, color="#1f4e79")
    fig.tight_layout(pad=0.3)
    save(fig, "graphical_abstract", dests)
    plt.close(fig)


def fig_public(path: Path, dests):
    if not path.exists():
        return
    rows = load_csv(path)
    g = defaultdict(list)
    for r in rows:
        g[(r["dataset"], r["mode"])].append(r["runtime_ms"])
    med = {k: statistics.median(v) for k, v in g.items()}
    x = np.arange(len(PUBLIC_ORDER))
    width = 0.16
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    for i, mode in enumerate(MODE_ORDER):
        ys = [med[(ds, mode)] for ds in PUBLIC_ORDER]
        ax.bar(x + (i - 2) * width, ys, width, label=LABEL[mode])
    ax.set_yscale("log")
    ax.set_xticks(x)
    ax.set_xticklabels([PUBLIC_SHORT[d] for d in PUBLIC_ORDER])
    ax.set_ylabel("Median runtime (ms)")
    ax.set_title(r"Public series at $K=50$, $\ell_{\max}=12$, $k=1/n$")
    ax.legend(ncols=2, fontsize=7)
    fig.tight_layout()
    save(fig, "public_runtime", dests)
    plt.close(fig)


def fig_rss(path: Path, dests):
    if not path.exists():
        return
    by = {}
    with path.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r.get("oneshot_rows") in {"0", ""}:
                continue
            by[(r["dataset"], r["mode"])] = float(r["peak_working_set_mb"])
    if not by:
        return
    order = [d for d in RSS_ORDER if (d, "hjtopk") in by and (d, "tk") in by]
    x = np.arange(len(order))
    width = 0.35
    fig, ax = plt.subplots(figsize=(9.2, 3.8))
    hj = [by[(d, "hjtopk")] for d in order]
    tk = [by[(d, "tk")] for d in order]
    ax.bar(x - width / 2, hj, width, label="HJ exhaustive")
    ax.bar(x + width / 2, tk, width, label="Full TK-HJ")
    ax.set_xticks(x)
    ax.set_xticklabels([RSS_SHORT[d] for d in order], rotation=25, ha="right")
    ax.set_ylabel("Peak Working Set (MB)")
    ax.set_title(r"Fresh-JVM OS Peak WS ($-$Xmx8g, no $-$Xms)")
    ax.legend()
    fig.tight_layout()
    save(fig, "official_rss", dests)
    plt.close(fig)


def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--timing", type=Path, default=DEFAULT_CSV)
    p.add_argument("--public", type=Path, default=DEFAULT_PUBLIC)
    p.add_argument("--rss", type=Path, default=DEFAULT_RSS)
    p.add_argument("--fig-dir", type=Path, action="append", default=None)
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    dests = args.fig_dir if args.fig_dir else [DEFAULT_FIG, DEFAULT_SUBMIT]
    style()
    rows = load_csv(args.timing)
    fig_runtime(rows, dests)
    gm, _sp = fig_speedup(rows, dests)
    fig_k_sens(rows, dests)
    fig_l_sens(rows, dests)
    fig_kforget_sens(rows, dests)
    fig_heap(rows, dests)
    fig_search_space(rows, dests)
    fig_graphical_abstract(gm, dests)
    fig_public(args.public, dests)
    fig_rss(args.rss, dests)
    print("wrote", [str(d) for d in dests], "geomean", f"{gm:.4f}")


if __name__ == "__main__":
    main()
