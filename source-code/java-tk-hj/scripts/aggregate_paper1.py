#!/usr/bin/env python3
"""Medians, IQR, bootstrap 95% CI, Wilcoxon, Markdown/LaTeX, and numbers.json for Paper 1."""
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from collections import defaultdict
from itertools import product
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_RES = ROOT / "source-code" / "results-campaign"

MODE_LABEL = {
    "hjtopk": "HJ",
    "tk-no-bounds": "No bounds",
    "tk-no-dub": "PDUB only",
    "tk-no-pdub": "DUB only",
    "tk": "Full TK",
}
MD_SHORT = {
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
TEX_SHORT = {
    "DB1_Amazon.txt": "Amazon",
    "DB2_Russell2000.txt": "Russell 2000",
    "DB3_Nasdaq.txt": "Nasdaq",
    "DB4_SP500.txt": r"S\&P 500",
    "DB5_NYSE.txt": "NYSE",
    "DB6_CL_US.txt": "CL.US",
    "DB7_HPQ_US.txt": "HPQ.US",
    "DB8_GE_US.txt": "GE.US",
    "SILSO_sunspots.txt": "SILSO",
    "NASDAQCOM.txt": "NASDAQCOM",
    "FRED_SP500.txt": r"S\&P 500 (FRED)",
}
OFFICIAL_ORDER = [
    "DB1_Amazon.txt", "DB2_Russell2000.txt", "DB3_Nasdaq.txt", "DB4_SP500.txt",
    "DB5_NYSE.txt", "DB6_CL_US.txt", "DB7_HPQ_US.txt", "DB8_GE_US.txt",
]
PUBLIC_ORDER = ["SILSO_sunspots.txt", "NASDAQCOM.txt", "FRED_SP500.txt"]
RSS_ORDER = OFFICIAL_ORDER + PUBLIC_ORDER
MODE_ORDER = list(MODE_LABEL)


def load_timing(path: Path, phase: str | None = None) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    with path.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if phase and r["phase"] != phase:
                continue
            r["runtime_ms"] = float(r["runtime_ms"])
            r["n"] = int(r["n"])
            r["topk"] = int(r["topk"])
            r["maxlen"] = int(r["maxlen"])
            r["k"] = float(r["k"])
            r["pair_attempts"] = int(r["pair_attempts"])
            r["compatible_pairs"] = int(r["compatible_pairs"])
            r["pdub_prunes"] = int(r["pdub_prunes"])
            r["dub_prunes"] = int(r["dub_prunes"])
            r["aligned_checks"] = int(r["aligned_checks"])
            r["peak_heap_mb"] = float(r["peak_heap_mb"])
            rows.append(r)
    return rows


def group_runtimes(rows: list[dict], extra: tuple[str, ...] = ()) -> dict[tuple, list[float]]:
    g: dict[tuple, list[float]] = defaultdict(list)
    for r in rows:
        key = (r["dataset"], r["mode"]) + tuple(r[x] for x in extra)
        g[key].append(r["runtime_ms"])
    return g


def bootstrap_median_ci(xs: list[float], n_boot: int = 10000, seed: int = 20260907) -> tuple[float, float, float]:
    a = np.asarray(xs, dtype=float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(a), size=(n_boot, len(a)))
    meds = np.median(a[idx], axis=1)
    lo, hi = np.percentile(meds, [2.5, 97.5])
    return float(np.median(a)), float(lo), float(hi)


def iqr(xs: list[float]) -> tuple[float, float]:
    s = sorted(xs)
    q = statistics.quantiles(s, n=4, method="inclusive")
    return q[0], q[2]


def geomean(xs: list[float]) -> float:
    return math.exp(sum(math.log(x) for x in xs) / len(xs))


def wilcoxon_signed_n8(diffs: list[float]) -> tuple[float, float]:
    """Exact Wilcoxon signed-rank two-sided p-value for n<=8 (no zeros expected)."""
    abs_d = [(abs(d), d) for d in diffs if d != 0]
    abs_d.sort()
    ranks = []
    i = 0
    while i < len(abs_d):
        j = i
        while j < len(abs_d) and abs_d[j][0] == abs_d[i][0]:
            j += 1
        avg = (i + 1 + j) / 2.0
        for _k in range(i, j):
            ranks.append((avg, abs_d[_k][1]))
        i = j
    w_pos = sum(r for r, d in ranks if d > 0)
    signed = [r if d > 0 else -r for r, d in ranks]
    m = len(signed)
    extreme = 0
    count = 0
    nullmean = sum(abs(s) for s in signed) / 2.0
    obs = abs(w_pos - nullmean)
    for bits in product([-1, 1], repeat=m):
        wp = sum(abs(s) for s, b in zip(signed, bits) if b > 0)
        count += 1
        if abs(wp - nullmean) + 1e-12 >= obs:
            extreme += 1
    p = extreme / count if count else float("nan")
    return float(w_pos), float(p)


def fmt_ms(x: float) -> str:
    return f"{x:.3f}"


def median_field(rows: list[dict], dataset: str, mode: str, field: str) -> float:
    xs = [r[field] for r in rows if r["dataset"] == dataset and r["mode"] == mode]
    return statistics.median(xs) if xs else float("nan")


def stats_block(rows: list[dict], order: list[str]) -> dict:
    g = group_runtimes(rows)
    n_of = {}
    for r in rows:
        n_of[r["dataset"]] = r["n"]
    out = {"datasets": [], "geomean_hj_tk": None, "geomean_hj_dub": None}
    sp_tk, sp_dub = [], []
    for ds in order:
        if (ds, "hjtopk") not in g or (ds, "tk") not in g:
            continue
        rec = {"dataset": ds, "n": n_of.get(ds, 0), "modes": {}}
        for mode in MODE_ORDER:
            xs = g.get((ds, mode), [])
            if not xs:
                continue
            m, lo, hi = bootstrap_median_ci(xs)
            q1, q3 = iqr(xs)
            rec["modes"][mode] = {
                "median": m, "ci_lo": lo, "ci_hi": hi, "iqr_lo": q1, "iqr_hi": q3, "n_runs": len(xs),
            }
        rec["speedup_hj_tk"] = rec["modes"]["hjtopk"]["median"] / rec["modes"]["tk"]["median"]
        if "tk-no-pdub" in rec["modes"]:
            rec["speedup_hj_dub"] = rec["modes"]["hjtopk"]["median"] / rec["modes"]["tk-no-pdub"]["median"]
            sp_dub.append(rec["speedup_hj_dub"])
        sp_tk.append(rec["speedup_hj_tk"])
        out["datasets"].append(rec)
    if sp_tk:
        out["geomean_hj_tk"] = geomean(sp_tk)
    if sp_dub:
        out["geomean_hj_dub"] = geomean(sp_dub)
    return out


def md_runtime_table(block: dict, title: str) -> str:
    lines = [f"## {title}", ""]
    lines.append("| dataset | n | HJ | No bounds | PDUB only | DUB only | Full TK | HJ/TK | HJ/DUB | HJ median [CI] | TK median [CI] |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |")
    for rec in block["datasets"]:
        ds = rec["dataset"]
        modes = rec["modes"]

        def cell(mode: str) -> str:
            if mode not in modes:
                return "—"
            return fmt_ms(modes[mode]["median"])

        s_tk = rec["speedup_hj_tk"]
        s_dub = rec.get("speedup_hj_dub", float("nan"))
        lines.append(
            f"| {MD_SHORT.get(ds, ds)} | {rec['n']} | {cell('hjtopk')} | {cell('tk-no-bounds')} | "
            f"{cell('tk-no-dub')} | {cell('tk-no-pdub')} | {cell('tk')} | {s_tk:.2f}x | {s_dub:.2f}x | "
            f"{modes['hjtopk']['median']:.3f} [{modes['hjtopk']['ci_lo']:.3f},{modes['hjtopk']['ci_hi']:.3f}] | "
            f"{modes['tk']['median']:.3f} [{modes['tk']['ci_lo']:.3f},{modes['tk']['ci_hi']:.3f}] |"
        )
        hq1, hq3 = modes["hjtopk"]["iqr_lo"], modes["hjtopk"]["iqr_hi"]
        q1, q3 = modes["tk"]["iqr_lo"], modes["tk"]["iqr_hi"]
        lines.append(
            f"|  IQR {MD_SHORT.get(ds, ds)} |  | [{hq1:.3f},{hq3:.3f}] |  |  |  | [{q1:.3f},{q3:.3f}] |  |  |  |  |"
        )
    gm_tk = block.get("geomean_hj_tk") or float("nan")
    gm_dub = block.get("geomean_hj_dub") or float("nan")
    lines.append(f"| geomean |  |  |  |  |  |  | {gm_tk:.2f}x | {gm_dub:.2f}x |  |  |")
    lines.append("")
    lines.append(f"geomean HJ/TK = {gm_tk:.4f}x, HJ/DUB-only = {gm_dub:.4f}x, N_datasets={len(block['datasets'])}")
    lines.append("")
    return "\n".join(lines)


def tex_runtime_table(block: dict, caption: str, label: str, title_comment: str) -> str:
    rows = [
        f"% {title_comment}",
        r"\begin{table}[t]",
        r"\caption{" + caption + "}",
        r"\label{" + label + "}",
        r"\centering",
        r"\small",
        r"\setlength{\tabcolsep}{4pt}",
        r"\resizebox{\textwidth}{!}{%",
        r"\begin{tabular}{@{}lrrrrrr@{}}",
        r"\toprule",
        r"Dataset & $n$ & HJ & DUB-only & Full TK & HJ/TK & HJ/DUB \\",
        r"\midrule",
    ]
    for rec in block["datasets"]:
        ds = rec["dataset"]
        modes = rec["modes"]
        dub = modes["tk-no-pdub"]["median"]
        tk = modes["tk"]["median"]
        dub_s, tk_s = fmt_ms(dub), fmt_ms(tk)
        if dub <= tk:
            dub_s = r"\textbf{" + dub_s + "}"
        else:
            tk_s = r"\textbf{" + tk_s + "}"
        rows.append(
            f"{TEX_SHORT.get(ds, ds)} & {rec['n']} & {fmt_ms(modes['hjtopk']['median'])} & "
            f"{dub_s} & {tk_s} & {rec['speedup_hj_tk']:.2f}$\\times$ & "
            f"{rec['speedup_hj_dub']:.2f}$\\times$ \\\\"
        )
    gm_tk = block.get("geomean_hj_tk") or float("nan")
    gm_dub = block.get("geomean_hj_dub") or float("nan")
    rows += [
        r"\midrule",
        f"Geomean & & & & & {gm_tk:.2f}$\\times$ & {gm_dub:.2f}$\\times$ \\\\",
        r"\bottomrule",
        r"\end{tabular}%",
        r"}",
        r"\end{table}",
        "",
    ]
    return "\n".join(rows)


def pair_block(rows: list[dict]) -> tuple[str, str, list[dict]]:
    recs = []
    md = ["## Search-space counters (central, median over measured runs)", ""]
    md.append("| dataset | HJ pairs | HJ aligned | TK pairs | TK aligned | PDUB prunes | DUB prunes |")
    md.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: |")
    tex = [
        r"\begin{table}[t]",
        r"\caption{Median search-space counters at $K=50$, $\ell_{\max}=12$, $k=1/n$. Pair attempts and compatible pairs are hash-join events; aligned checks are occurrence-list comparisons.}",
        r"\label{tab:pairs}",
        r"\centering",
        r"\footnotesize",
        r"\setlength{\tabcolsep}{3.5pt}",
        r"\resizebox{\textwidth}{!}{%",
        r"\begin{tabular}{@{}lrrrrrr@{}}",
        r"\toprule",
        r"Dataset & HJ pairs & HJ aligned & TK pairs & TK aligned & PDUB prunes & DUB prunes \\",
        r"\midrule",
    ]
    for ds in OFFICIAL_ORDER:
        hj_pairs = median_field(rows, ds, "hjtopk", "pair_attempts")
        hj_al = median_field(rows, ds, "hjtopk", "aligned_checks")
        tk_pairs = median_field(rows, ds, "tk", "pair_attempts")
        tk_al = median_field(rows, ds, "tk", "aligned_checks")
        pdub = median_field(rows, ds, "tk", "pdub_prunes")
        dub = median_field(rows, ds, "tk", "dub_prunes")
        if math.isnan(hj_pairs):
            continue
        recs.append({
            "dataset": ds,
            "hj_pairs": int(hj_pairs), "hj_aligned": int(hj_al),
            "tk_pairs": int(tk_pairs), "tk_aligned": int(tk_al),
            "pdub_prunes": int(pdub), "dub_prunes": int(dub),
        })
        md.append(
            f"| {MD_SHORT[ds]} | {int(hj_pairs)} | {int(hj_al)} | {int(tk_pairs)} | "
            f"{int(tk_al)} | {int(pdub)} | {int(dub)} |"
        )
        tex.append(
            f"{TEX_SHORT[ds]} & {int(hj_pairs)} & {int(hj_al)} & {int(tk_pairs)} & "
            f"{int(tk_al)} & {int(pdub)} & {int(dub)} \\\\"
        )
    md.append("")
    tex += [r"\bottomrule", r"\end{tabular}%", r"}", r"\end{table}", ""]
    return "\n".join(md), "\n".join(tex), recs


def sensitivity_md(all_rows: list[dict]) -> tuple[str, dict]:
    numbers: dict = {"K_sens": {}, "L_sens": {}, "k_sens": {}}
    lines = ["## Sensitivity (same JVM after central; 3 warmup + 5 measured)", ""]
    k_rows = [r for r in all_rows if r["phase"] == "K_sens"]
    g = group_runtimes(k_rows, extra=("topk",))
    lines.append("### K-sensitivity")
    lines.append("| dataset | K | HJ | DUB-only | Full TK | HJ/TK |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: |")
    for ds in ["DB1_Amazon.txt", "DB2_Russell2000.txt", "DB3_Nasdaq.txt"]:
        numbers["K_sens"][ds] = {}
        for K in [10, 50, 100, 500]:
            hj = statistics.median(g[(ds, "hjtopk", K)]) if (ds, "hjtopk", K) in g else float("nan")
            dub = statistics.median(g[(ds, "tk-no-pdub", K)]) if (ds, "tk-no-pdub", K) in g else float("nan")
            tk = statistics.median(g[(ds, "tk", K)]) if (ds, "tk", K) in g else float("nan")
            sp = hj / tk if tk else float("nan")
            numbers["K_sens"][ds][str(K)] = {"hj": hj, "dub": dub, "tk": tk, "hj_tk": sp}
            lines.append(f"| {MD_SHORT[ds]} | {K} | {hj:.3f} | {dub:.3f} | {tk:.3f} | {sp:.1f}x |")
    lines.append("")

    l_rows = [r for r in all_rows if r["phase"] == "L_sens"]
    gl = group_runtimes(l_rows, extra=("maxlen",))
    lines.append("### L-sensitivity (Amazon, K=50)")
    lines.append("| L | HJ | DUB-only | Full TK | HJ/TK |")
    lines.append("| ---: | ---: | ---: | ---: | ---: |")
    ds = "DB1_Amazon.txt"
    for L in [8, 12, 16]:
        hj = statistics.median(gl[(ds, "hjtopk", L)]) if (ds, "hjtopk", L) in gl else float("nan")
        dub = statistics.median(gl[(ds, "tk-no-pdub", L)]) if (ds, "tk-no-pdub", L) in gl else float("nan")
        tk = statistics.median(gl[(ds, "tk", L)]) if (ds, "tk", L) in gl else float("nan")
        sp = hj / tk if tk else float("nan")
        numbers["L_sens"][str(L)] = {"hj": hj, "dub": dub, "tk": tk, "hj_tk": sp}
        lines.append(f"| {L} | {hj:.3f} | {dub:.3f} | {tk:.3f} | {sp:.1f}x |")
    lines.append("")

    ks_rows = [r for r in all_rows if r["phase"] == "k_sens"]
    lines.append("### Forgetting-factor sensitivity (K=50, L=12)")
    lines.append("| dataset | k·n | HJ | Full TK | HJ/TK |")
    lines.append("| --- | ---: | ---: | ---: | ---: |")
    by = defaultdict(list)
    n_of = {}
    for r in ks_rows:
        n_of[r["dataset"]] = r["n"]
        by[(r["dataset"], r["mode"], round(r["k"] * r["n"], 6))].append(r["runtime_ms"])
    for ds in ["DB1_Amazon.txt", "DB8_GE_US.txt"]:
        numbers["k_sens"][ds] = {}
        n = n_of.get(ds, 1)
        for c in [0.25, 0.5, 1.0, 2.0, 4.0]:
            key_c = round(c, 6)
            hj = statistics.median(by[(ds, "hjtopk", key_c)]) if (ds, "hjtopk", key_c) in by else float("nan")
            tk = statistics.median(by[(ds, "tk", key_c)]) if (ds, "tk", key_c) in by else float("nan")
            # k stored as c/n; float may not match round(c). Fall back to nearest.
            if math.isnan(hj):
                candidates = [kk for (d, m, kk) in by if d == ds and m == "hjtopk"]
                if candidates:
                    nearest = min(candidates, key=lambda x: abs(x - c))
                    hj = statistics.median(by[(ds, "hjtopk", nearest)])
                    tk = statistics.median(by[(ds, "tk", nearest)])
            sp = hj / tk if tk else float("nan")
            numbers["k_sens"][ds][str(c)] = {"hj": hj, "tk": tk, "hj_tk": sp, "n": n}
            lines.append(f"| {MD_SHORT[ds]} | {c:g} | {hj:.3f} | {tk:.3f} | {sp:.1f}x |")
    lines.append("")
    return "\n".join(lines), numbers


def canonical_agree(path: Path, title: str) -> str:
    if not path.exists():
        return f"## {title}\n\n(no canonical TSV)\n"
    shas: dict[str, set[str]] = defaultdict(set)
    npat: dict[str, int] = defaultdict(int)
    with path.open(encoding="utf-8") as f:
        _header = f.readline()
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 10:
                continue
            ds, mode, sha = parts[0], parts[2], parts[9]
            shas[ds].add(sha)
            npat[ds] += 1
    lines = [f"## {title}", ""]
    for ds, s in shas.items():
        flag = "IDENTICAL" if len(s) == 1 else "MISMATCH " + ",".join(sorted(x[:12] for x in s))
        lines.append(f"- {ds}: unique_sha={len(s)} rows={npat[ds]} {flag}")
    lines.append("")
    return "\n".join(lines)


def rss_block(path: Path) -> tuple[str, str, list[dict]]:
    if not path.exists():
        return "## RSS\n\n(no RSS csv)\n", "", []
    by = {}
    with path.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            by[(r["dataset"], r["mode"])] = r
    recs = []
    md = ["## Per-mode OS Working Set (fresh JVM, -Xmx8g, no -Xms)", ""]
    md.append("| dataset | HJ | No bounds | PDUB only | DUB only | Full TK |")
    md.append("| --- | ---: | ---: | ---: | ---: | ---: |")
    tex = [
        r"\begin{table}[t]",
        r"\caption{Fresh-JVM OS Peak Working Set (MB) at $K=50$, $\ell_{\max}=12$, $k=1/n$. Flags: \texttt{-Xmx8g}, no \texttt{-Xms}.}",
        r"\label{tab:rss}",
        r"\centering",
        r"\footnotesize",
        r"\setlength{\tabcolsep}{3.5pt}",
        r"\resizebox{\textwidth}{!}{%",
        r"\begin{tabular}{@{}lrrrr@{}}",
        r"\toprule",
        r"Dataset & HJ & No bounds & DUB-only & Full TK \\",
        r"\midrule",
    ]
    for ds in RSS_ORDER:
        def mb(mode: str) -> str:
            r = by.get((ds, mode))
            return r["peak_working_set_mb"] if r else "—"

        if (ds, "tk") not in by:
            continue
        recs.append({
            "dataset": ds,
            "hjtopk": float(by[(ds, "hjtopk")]["peak_working_set_mb"]),
            "tk-no-bounds": float(by[(ds, "tk-no-bounds")]["peak_working_set_mb"]),
            "tk-no-dub": float(by[(ds, "tk-no-dub")]["peak_working_set_mb"]),
            "tk-no-pdub": float(by[(ds, "tk-no-pdub")]["peak_working_set_mb"]),
            "tk": float(by[(ds, "tk")]["peak_working_set_mb"]),
            "n": int(by[(ds, "tk")]["n"] or 0),
        })
        md.append(
            f"| {MD_SHORT.get(ds, ds)} | {mb('hjtopk')} | {mb('tk-no-bounds')} | "
            f"{mb('tk-no-dub')} | {mb('tk-no-pdub')} | {mb('tk')} |"
        )
        tex_label = TEX_SHORT.get(ds, ds)
        if ds == "DB4_SP500.txt":
            tex_label = r"S\&P 500 (OPF)"
        tex.append(
            f"{tex_label} & {mb('hjtopk')} & {mb('tk-no-bounds')} & {mb('tk-no-pdub')} & {mb('tk')} \\\\"
        )
    md += [
        "",
        "Values are peak Windows WorkingSet64 of a dedicated JVM (3 warmup + 5 measured).",
        "Timing campaign uses `-Xms2g -Xmx8g`; RSS uses `-Xmx8g` only so the committed 2 GB heap does not mask the algorithm.",
        "",
    ]
    tex += [r"\bottomrule", r"\end{tabular}%", r"}", r"\end{table}", ""]
    return "\n".join(md), "\n".join(tex), recs


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--res-dir", type=Path, default=DEFAULT_RES)
    p.add_argument("--official-csv", type=Path, default=None)
    p.add_argument("--public-csv", type=Path, default=None)
    p.add_argument("--rss-csv", type=Path, default=None)
    p.add_argument("--canon-official", type=Path, default=None)
    p.add_argument("--canon-public", type=Path, default=None)
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    res: Path = args.res_dir
    official_csv = args.official_csv or (res / "timing.csv")
    public_csv = args.public_csv or (res / "full_paper1.csv")
    rss_csv = args.rss_csv or (res / "full_paper1_rss.csv")
    canon_off = args.canon_official or (res / "canonical.tsv")
    canon_pub = args.canon_public or (res / "full_paper1_canonical.tsv")
    out_md = res / "full_paper1_SUMMARY.md"
    out_tex = res / "full_paper1_tables.tex"
    out_ms = res / "tables_manuscript.tex"
    out_json = res / "numbers.json"

    off_all = load_timing(official_csv)
    off = [r for r in off_all if r["phase"] == "central"]
    pub = load_timing(public_csv, "public")
    parts = ["# Paper 1 full-experiment summary", ""]
    tex_parts = ["% auto-generated by aggregate_paper1.py — do not edit by hand", ""]
    ms_parts = ["% auto-generated manuscript table environments", ""]
    payload: dict = {}

    if off:
        block = stats_block(off, OFFICIAL_ORDER)
        payload["official_central"] = block
        parts.append(md_runtime_table(block, "Official DB1–DB8 central (timing.csv)"))
        tex_parts.append(tex_runtime_table(block, "", "tab:central-raw", "Official DB1–DB8 central"))
        ms_parts.append(tex_runtime_table(
            block,
            r"Central campaign, $K=50$, $\ell_{\max}=12$, $k=1/n$. Median ms, ten measured runs after five warmups.",
            "tab:central",
            "Official DB1–DB8 central",
        ))
        diffs_tk, diffs_dub = [], []
        for rec in block["datasets"]:
            diffs_tk.append(rec["modes"]["hjtopk"]["median"] - rec["modes"]["tk"]["median"])
            diffs_dub.append(rec["modes"]["hjtopk"]["median"] - rec["modes"]["tk-no-pdub"]["median"])
        w, p = wilcoxon_signed_n8(diffs_tk)
        w2, p2 = wilcoxon_signed_n8(diffs_dub)
        payload["wilcoxon_hj_tk"] = {"W_plus": w, "p": p}
        payload["wilcoxon_hj_dub"] = {"W_plus": w2, "p": p2}
        parts.append(f"Wilcoxon signed-rank on {len(diffs_tk)} paired medians HJ−TK: W+={w:.1f}, two-sided p={p:.5f}")
        parts.append(f"Wilcoxon signed-rank on {len(diffs_dub)} paired medians HJ−DUB-only: W+={w2:.1f}, two-sided p={p2:.5f}")
        parts.append("")
        parts.append("Bootstrap is percentile 95% CI of the median, 10000 resamples, seed 20260907.")
        parts.append("")
        pmd, ptex, prec = pair_block(off)
        payload["pairs"] = prec
        parts.append(pmd)
        tex_parts.append(ptex)
        ms_parts.append(ptex)
        smd, snum = sensitivity_md(off_all)
        payload["sensitivity"] = snum
        parts.append(smd)

    if pub:
        block = stats_block(pub, PUBLIC_ORDER)
        payload["public"] = block
        parts.append(md_runtime_table(block, "Public series (5-mode)"))
        tex_parts.append(tex_runtime_table(block, "", "tab:public-raw", "Public series"))
        ms_parts.append(tex_runtime_table(
            block,
            r"Public series, same central cell as Table~\ref{tab:central}. Median ms, ten measured runs. Bold: fastest exact variant.",
            "tab:public",
            "Public series",
        ))

    parts.append(canonical_agree(canon_off, "Canonical SHA agreement (official 5-mode)"))
    parts.append(canonical_agree(canon_pub, "Canonical SHA agreement (public 5-mode)"))
    rmd, rtex, rrec = rss_block(rss_csv)
    payload["rss"] = rrec
    parts.append(rmd)
    if rtex:
        tex_parts.append(rtex)
        ms_parts.append(rtex)

    out_md.write_text("\n".join(parts), encoding="utf-8")
    out_tex.write_text("\n".join(tex_parts), encoding="utf-8")
    out_ms.write_text("\n".join(ms_parts), encoding="utf-8")

    def default(o):
        if isinstance(o, float):
            return o
        raise TypeError(o)

    out_json.write_text(json.dumps(payload, indent=2, default=default), encoding="utf-8")
    print(f"WROTE {out_md}")
    print(f"WROTE {out_tex}")
    print(f"WROTE {out_ms}")
    print(f"WROTE {out_json}")
    print(out_md.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
