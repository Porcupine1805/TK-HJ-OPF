#!/usr/bin/env python3
"""Build latex-submit/ (Elsevier) and code-github/ (public repo snapshot)."""
from __future__ import annotations

import csv
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
JAVA = ROOT / "source-code" / "java-tk-hj"
SRC = ROOT / "source-code"
MS = ROOT / "manuscript"
ARCHIVE = SRC / "results-campaign" / "archive-20260906"
PROFILE = SRC / "results-campaign" / "run-20260908-profile"
LATEX = ROOT / "latex-submit"
CODE = ROOT / "code-github"
SCRIPTS = JAVA / "scripts"

FIG_USED = [
    "official_runtime.png",
    "official_speedup.png",
    "official_K_sensitivity.png",
    "profile_ablation.png",
    "public_runtime.png",
    "official_rss.png",
    "graphical_abstract.png",
]

# Manuscript Table public / RSS (locked 6 Sept 2026 medians).
PUBLIC_MED = {
    "SILSO_sunspots.txt": {
        "n": 72967,
        "hjtopk": 248.145, "tk-no-bounds": 227.976, "tk-no-dub": 17.998,
        "tk-no-pdub": 16.738, "tk": 17.241,
    },
    "NASDAQCOM.txt": {
        "n": 14014,
        "hjtopk": 140.672, "tk-no-bounds": 139.080, "tk-no-dub": 5.413,
        "tk-no-pdub": 4.743, "tk": 5.198,
    },
    "FRED_SP500.txt": {
        "n": 2514,
        "hjtopk": 28.428, "tk-no-bounds": 30.035, "tk-no-dub": 1.280,
        "tk-no-pdub": 1.008, "tk": 1.078,
    },
}
RSS_MED = {
    "DB1_Amazon.txt": {"hjtopk": 298.7, "tk": 75.4},
    "DB2_Russell2000.txt": {"hjtopk": 275.0, "tk": 80.9},
    "DB3_Nasdaq.txt": {"hjtopk": 345.8, "tk": 80.2},
    "DB4_SP500.txt": {"hjtopk": 376.6, "tk": 102.8},
    "DB5_NYSE.txt": {"hjtopk": 363.4, "tk": 121.7},
    "DB6_CL_US.txt": {"hjtopk": 290.1, "tk": 74.6},
    "DB7_HPQ_US.txt": {"hjtopk": 301.6, "tk": 72.5},
    "DB8_GE_US.txt": {"hjtopk": 268.7, "tk": 79.7},
    "SILSO_sunspots.txt": {"hjtopk": 376.3, "tk": 109.7},
    "NASDAQCOM.txt": {"hjtopk": 373.7, "tk": 85.6},
    "FRED_SP500.txt": {"hjtopk": 177.6, "tk": 64.6},
}


def reset_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)


def write_median_csv(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = "phase,dataset,n,mode,k,topk,minlen,maxlen,rep,runtime_ms,patterns,pair_attempts,compatible_pairs,pdub_prunes,dub_prunes,aligned_checks,peak_heap_mb"
    with path.open("w", encoding="utf-8", newline="") as f:
        f.write(fields + "\n")
        for ds, rec in PUBLIC_MED.items():
            for mode, ms in rec.items():
                if mode == "n":
                    continue
                for rep in range(10):
                    f.write(
                        f"public,{ds},{rec['n']},{mode},0.0,50,2,12,{rep},{ms:.6f},50,0,0,0,0,0,0\n"
                    )


def write_rss_csv(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["dataset", "mode", "n", "peak_working_set_mb", "rss_flags", "exit", "oneshot_rows"])
        for ds, rec in RSS_MED.items():
            for mode, mb in rec.items():
                w.writerow([ds, mode, 0, mb, "-Xmx8g", 0, 5])


def restore_lock_csvs() -> None:
    dest = SRC / "results-campaign"
    for name in ["timing.csv", "canonical.tsv", "environment.txt", "SUMMARY.md"]:
        src = ARCHIVE / name
        if src.exists():
            shutil.copy2(src, dest / name)
    for name in [
        "profile_ablation.csv",
        "profile_ablation_canonical.tsv",
        "profile_ablation_SUMMARY.md",
        "profile_ablation_tables.tex",
    ]:
        src = PROFILE / name
        if src.exists():
            shutil.copy2(src, dest / name)


def restore_figures() -> None:
    tmp = ROOT / ".figlock"
    tmp.mkdir(exist_ok=True)
    pub = tmp / "public.csv"
    rss = tmp / "rss.csv"
    write_median_csv(pub)
    write_rss_csv(rss)
    fig_ms = MS / "figures"
    fig_lx = LATEX / "figures"
    fig_ms.mkdir(parents=True, exist_ok=True)
    fig_lx.mkdir(parents=True, exist_ok=True)
    subprocess.check_call(
        [
            sys.executable, str(SCRIPTS / "plot_campaign.py"),
            "--timing", str(ARCHIVE / "timing.csv"),
            "--public", str(pub),
            "--rss", str(rss),
            "--fig-dir", str(fig_ms),
            "--fig-dir", str(fig_lx),
        ],
        cwd=str(JAVA),
    )
    subprocess.check_call([sys.executable, str(SCRIPTS / "plot_ablation.py")], cwd=str(JAVA))
    shutil.copy2(fig_ms / "profile_ablation.png", fig_lx / "profile_ablation.png")
    shutil.copy2(fig_ms / "profile_ablation.pdf", fig_lx / "profile_ablation.pdf")
    shutil.rmtree(tmp, ignore_errors=True)


def pack_latex() -> None:
    LATEX.mkdir(parents=True, exist_ok=True)
    (LATEX / "figures").mkdir(exist_ok=True)
    shutil.copy2(MS / "main.tex", LATEX / "main.tex")
    shutil.copy2(MS / "references.bib", LATEX / "references.bib")
    shutil.copy2(MS / "elsarticle-num.bst", LATEX / "elsarticle-num.bst")
    shutil.copy2(MS / "highlights.txt", LATEX / "highlights.txt")
    shutil.copy2(MS / "compile.ps1", LATEX / "compile.ps1")
    shutil.copy2(ROOT / "submit" / "cover_letter.txt", LATEX / "cover_letter.txt")
    ga = MS / "figures" / "graphical_abstract.png"
    if ga.exists():
        shutil.copy2(ga, LATEX / "graphical_abstract.png")
        shutil.copy2(ga, LATEX / "figures" / "graphical_abstract.png")
    for name in FIG_USED:
        src = MS / "figures" / name
        if src.exists():
            shutil.copy2(src, LATEX / "figures" / name)
    (LATEX / "README.txt").write_text(
        """Information Sciences (Elsevier) — LaTeX submission package
==========================================================

Compiler: pdfLaTeX. Main document: main.tex
  powershell -File compile.ps1

Upload to Overleaf or Editorial Manager:

  main.tex
  references.bib
  elsarticle-num.bst
  figures/official_runtime.png
  figures/official_speedup.png
  figures/official_K_sensitivity.png
  figures/profile_ablation.png
  figures/public_runtime.png
  figures/official_rss.png

Editorial Manager extras (not inside the PDF):
  highlights.txt              5 bullets, each <= 85 characters
  graphical_abstract.png      landscape PNG (upload as Graphical Abstract)
  cover_letter.txt            cover letter
  main.pdf                    compiled manuscript (after compile.ps1)

Do not upload official OPF-Miner DB1-DB8 series.
Code: https://github.com/Porcupine1805/TK-HJ-OPF
""",
        encoding="utf-8",
    )


def compile_latex() -> None:
    subprocess.check_call(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(LATEX / "compile.ps1")],
        cwd=str(LATEX),
    )


def pack_code() -> None:
    reset_dir(CODE)
    for name in ["LICENSE", "NOTICE.md", "DATASETS.md", "README.md", ".gitignore"]:
        shutil.copy2(ROOT / name, CODE / name)
    # source tree
    skip_scripts = {"watch_campaign.py", "pack_release.py"}
    dest_java = CODE / "source-code" / "java-tk-hj"
    shutil.copytree(
        JAVA / "src", dest_java / "src",
        ignore=shutil.ignore_patterns("*.class"),
    )
    shutil.copytree(JAVA / "single-file", dest_java / "single-file")
    shutil.copytree(JAVA / "docs", dest_java / "docs")
    (dest_java / "scripts").mkdir(parents=True)
    for p in (JAVA / "scripts").iterdir():
        if p.suffix in {".ps1", ".sh", ".py"} and p.name not in skip_scripts:
            shutil.copy2(p, dest_java / "scripts" / p.name)
    shutil.copy2(JAVA / "README.md", dest_java / "README.md")
    shutil.copy2(JAVA / "LICENSE_NOTE.md", dest_java / "LICENSE_NOTE.md")
    (dest_java / "data").mkdir(exist_ok=True)
    shutil.copy2(JAVA / "data" / "example_opf.txt", dest_java / "data" / "example_opf.txt")

    dest_data = CODE / "source-code" / "data"
    dest_data.mkdir(parents=True)
    shutil.copy2(SRC / "data" / "example_opf.txt", dest_data / "example_opf.txt")
    shutil.copy2(SRC / "data" / "legacy_example.txt", dest_data / "legacy_example.txt")
    pub = dest_data / "public"
    pub.mkdir()
    shutil.copy2(SRC / "data" / "public" / "README.md", pub / "README.md")
    for name in ["SILSO_sunspots.txt", "NASDAQCOM.txt", "FRED_SP500.txt"]:
        src = SRC / "data" / "public" / name
        if src.exists():
            shutil.copy2(src, pub / name)
    (dest_data / "official").mkdir()
    shutil.copy2(SRC / "data" / "official" / "README.md", dest_data / "official" / "README.md")
    shutil.copy2(SRC / "README.md", CODE / "source-code" / "README.md")

    dest_res = CODE / "source-code" / "results-campaign"
    dest_res.mkdir()
    for name in [
        "PROTOCOL.txt", "environment.txt", "timing.csv", "canonical.tsv", "SUMMARY.md",
        "profile_ablation.csv", "profile_ablation_canonical.tsv", "profile_ablation_SUMMARY.md",
    ]:
        src = SRC / "results-campaign" / name
        if src.exists():
            shutil.copy2(src, dest_res / name)
    dest_small = CODE / "source-code" / "results-small"
    dest_small.mkdir()
    for p in (SRC / "results-small").iterdir():
        if p.is_file():
            shutil.copy2(p, dest_small / p.name)


def main() -> None:
    restore_lock_csvs()
    restore_figures()
    pack_latex()
    compile_latex()
    pack_code()
    print("LATEX", LATEX)
    print("CODE", CODE)
    print("latex files", sorted(p.name for p in LATEX.iterdir()))
    print("code top", sorted(p.name for p in CODE.iterdir()))


if __name__ == "__main__":
    main()
