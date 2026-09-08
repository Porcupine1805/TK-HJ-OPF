#!/usr/bin/env python3
"""Bar chart for naive PDUB vs depth-UB profile vs DUB-only."""
from __future__ import annotations

import csv
import statistics
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
CSV = ROOT / "source-code" / "results-campaign" / "run-20260908-profile" / "profile_ablation.csv"
DESTS = [
    ROOT / "latex-submit" / "figures",
]
SHORT = {
    "DB1_Amazon.txt": "Amazon",
    "DB2_Russell2000.txt": "Russell",
    "DB3_Nasdaq.txt": "Nasdaq",
    "DB4_SP500.txt": "S&P 500",
    "DB5_NYSE.txt": "NYSE",
    "DB6_CL_US.txt": "CL.US",
    "DB7_HPQ_US.txt": "HPQ.US",
    "DB8_GE_US.txt": "GE.US",
    "SILSO_sunspots.txt": "SILSO",
    "NASDAQCOM.txt": "NASDAQ",
    "FRED_SP500.txt": "FRED S&P",
}
MODE_LABEL = {
    "tk-no-pdub": "DUB-only",
    "tk-naive": "Naive PDUB",
    "tk": "Profile PDUB",
}
MODE_ORDER = ["tk-no-pdub", "tk-naive", "tk"]


def main() -> None:
    g = defaultdict(list)
    order: list[str] = []
    with CSV.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["dataset"] not in order:
                order.append(r["dataset"])
            g[(r["dataset"], r["mode"])].append(float(r["runtime_ms"]))
    med = {k: statistics.median(v) for k, v in g.items()}
    x = np.arange(len(order))
    width = 0.25
    plt.rcParams.update({"font.size": 9, "figure.dpi": 160, "savefig.dpi": 200, "axes.grid": True, "grid.alpha": 0.35})
    fig, ax = plt.subplots(figsize=(9.2, 3.8))
    for i, mode in enumerate(MODE_ORDER):
        ys = [med[(ds, mode)] for ds in order]
        ax.bar(x + (i - 1) * width, ys, width, label=MODE_LABEL[mode])
    ax.set_yscale("log")
    ax.set_xticks(x)
    ax.set_xticklabels([SHORT[d] for d in order], rotation=25, ha="right")
    ax.set_ylabel("Median runtime (ms)")
    ax.set_title(r"PDUB evaluation: DUB-only vs naive vs depth-UB profile")
    ax.legend(ncols=3, fontsize=8)
    fig.tight_layout()
    for dest in DESTS:
        dest.mkdir(parents=True, exist_ok=True)
        fig.savefig(dest / "profile_ablation.png")
        fig.savefig(dest / "profile_ablation.pdf")
    plt.close(fig)
    print("wrote profile_ablation")


if __name__ == "__main__":
    main()
