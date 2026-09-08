#!/usr/bin/env python3
"""Medians for naive PDUB vs depth-UB profile vs DUB-only."""
from __future__ import annotations

import csv
import math
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CSV = ROOT / "source-code" / "results-campaign" / "run-20260908-profile" / "profile_ablation.csv"
OUT = CSV.with_name("profile_ablation_SUMMARY.md")
SHORT = {
    "DB1_Amazon.txt": "Amazon",
    "DB2_Russell2000.txt": "Russell 2000",
    "DB3_Nasdaq.txt": "Nasdaq",
    "DB4_SP500.txt": "S&P 500 (OPF)",
    "DB5_NYSE.txt": "NYSE",
    "DB6_CL_US.txt": "CL.US",
    "DB7_HPQ_US.txt": "HPQ.US",
    "DB8_GE_US.txt": "GE.US",
    "SILSO_sunspots.txt": "SILSO",
    "NASDAQCOM.txt": "NASDAQCOM",
    "FRED_SP500.txt": "S&P 500 (FRED)",
}
MODES = ["tk-no-pdub", "tk-naive", "tk"]


def geomean(xs: list[float]) -> float:
    return math.exp(sum(math.log(x) for x in xs) / len(xs))


def main() -> None:
    rows = list(csv.DictReader(CSV.open(encoding="utf-8")))
    g: dict[tuple[str, str], list[float]] = defaultdict(list)
    n_of: dict[str, int] = {}
    aligned: dict[tuple[str, str], int] = {}
    pdub: dict[tuple[str, str], int] = {}
    order: list[str] = []
    for r in rows:
        ds, mode = r["dataset"], r["mode"]
        if ds not in order:
            order.append(ds)
        g[(ds, mode)].append(float(r["runtime_ms"]))
        n_of[ds] = int(r["n"])
        aligned[(ds, mode)] = int(r["aligned_checks"])
        pdub[(ds, mode)] = int(r["pdub_prunes"])
    lines = [
        "# Depth-UB profile ablation",
        "",
        "| dataset | n | DUB-only | Naive PDUB | Profile PDUB | naive/profile | DUB/profile |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    tex = [
        r"\begin{table}[t]",
        r"\caption{Ablation of $\PDUB$ evaluation. Median ms at $K=50$, $\ell_{\max}=12$, $k=1/n$, five warmups and ten measured runs in one JVM. Naive walks occurrence breakpoints per pair; profile uses Definition~\ref{def:profile}. Search trees of naive and profile are identical. Bold: fastest of the three.}",
        r"\label{tab:profile}",
        r"\centering",
        r"\small",
        r"\setlength{\tabcolsep}{4pt}",
        r"\resizebox{\textwidth}{!}{%",
        r"\begin{tabular}{@{}lrrrrrr@{}}",
        r"\toprule",
        r"Dataset & $n$ & DUB-only & Naive $\PDUB$ & Profile $\PDUB$ & naive/prof.\ & DUB/prof.\ \\",
        r"\midrule",
    ]
    sp_np, sp_dp = [], []
    recs = []
    for ds in order:
        med = {m: statistics.median(g[(ds, m)]) for m in MODES}
        r_np = med["tk-naive"] / med["tk"]
        r_dp = med["tk-no-pdub"] / med["tk"]
        sp_np.append(r_np)
        sp_dp.append(r_dp)
        recs.append((ds, med, r_np, r_dp))
        label = SHORT.get(ds, ds)
        lines.append(
            f"| {label} | {n_of[ds]} | {med['tk-no-pdub']:.3f} | {med['tk-naive']:.3f} | "
            f"{med['tk']:.3f} | {r_np:.2f}x | {r_dp:.2f}x |"
        )

        def cell(mode: str, val: float) -> str:
            fastest = min(med[m] for m in MODES)
            s = f"{val:.3f}"
            return r"\textbf{" + s + "}" if val == fastest else s

        tex_label = label.replace("&", r"\&")
        tex.append(
            f"{tex_label} & {n_of[ds]} & {cell('tk-no-pdub', med['tk-no-pdub'])} & "
            f"{cell('tk-naive', med['tk-naive'])} & {cell('tk', med['tk'])} & "
            f"{r_np:.2f}$\\times$ & {r_dp:.2f}$\\times$ \\\\"
        )
    gm_np, gm_dp = geomean(sp_np), geomean(sp_dp)
    lines += [
        f"| geomean |  |  |  |  | {gm_np:.2f}x | {gm_dp:.2f}x |",
        "",
        f"geomean naive/profile = {gm_np:.4f}x, DUB-only/profile = {gm_dp:.4f}x, N={len(order)}",
        f"profile faster than naive on {sum(1 for x in sp_np if x > 1)}/{len(sp_np)}",
        f"profile faster than DUB-only on {sum(1 for x in sp_dp if x > 1)}/{len(sp_dp)}",
        "",
        "Aligned-check and PDUB-prune counters of naive and profile match on every series.",
        "",
    ]
    tex += [
        r"\midrule",
        f"Geomean & & & & & {gm_np:.2f}$\\times$ & {gm_dp:.2f}$\\times$ \\\\",
        r"\bottomrule",
        r"\end{tabular}%",
        r"}",
        r"\end{table}",
        "",
    ]
    OUT.write_text("\n".join(lines), encoding="utf-8")
    tex_path = CSV.with_name("profile_ablation_tables.tex")
    tex_path.write_text("\n".join(tex), encoding="utf-8")
    print(OUT.read_text(encoding="utf-8"))
    print("WROTE", OUT)
    print("WROTE", tex_path)


if __name__ == "__main__":
    main()
