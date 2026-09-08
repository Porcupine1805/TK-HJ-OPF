#!/usr/bin/env python3
"""Run the locked Paper-1 campaign and write tables/figures.

Official DB1–DB8 (SHA-256 checked) + public SILSO/FRED:
  self-tests, CampaignRunner, CanonicalDump, Paper1SeriesRunner, RSS,
  aggregate_paper1.py, plot_campaign.py.

Does not overwrite the previously locked results-campaign/timing.csv;
writes a dated run directory instead.
"""
from __future__ import annotations

import hashlib
import os
import platform
import shutil
import subprocess
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

JAVA_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = JAVA_ROOT.parent
PAPER_ROOT = SRC_ROOT.parent
SCRIPTS = Path(__file__).resolve().parent

OFFICIAL_DIR = Path(os.environ.get("TKHJ_OFFICIAL_DIR", str(SRC_ROOT / "data" / "official")))
PUBLIC_DIR = SRC_ROOT / "data" / "public"
RUN_ID = datetime.now().strftime("%Y%m%d")
OUT = SRC_ROOT / "results-campaign" / f"run-{RUN_ID}"
STATUS = OUT / "STATUS.txt"
LOG = OUT / "campaign.log"

OFFICIAL_NAMES = [
    "DB1_Amazon.txt", "DB2_Russell2000.txt", "DB3_Nasdaq.txt", "DB4_SP500.txt",
    "DB5_NYSE.txt", "DB6_CL_US.txt", "DB7_HPQ_US.txt", "DB8_GE_US.txt",
]
PUBLIC_NAMES = ["SILSO_sunspots.txt", "NASDAQCOM.txt", "FRED_SP500.txt"]
EXPECTED_SHA = {
    "DB1_Amazon.txt": "0f826c7af3ef51a9bda6f9d69e66e962c4a776c3ee56fd88db41cd9fbc777b1d",
    "DB2_Russell2000.txt": "3035a617532ca8826f17b814d4b064244f3294cfc915acd3777334e5a02e0cbf",
    "DB3_Nasdaq.txt": "841367472d7b12e44d99f7562457116e8ce179b67bbb1cce9581d331d181b431",
    "DB4_SP500.txt": "42084a62c8840ac4970ae6c36b9482c33b9b3bdac0bc5a5bc028e876d92ef0e8",
    "DB5_NYSE.txt": "89aeeb3c4c1a3284600ffc2a6a8592fde4cc529ab124cd7ebd80c43262c3cc66",
    "DB6_CL_US.txt": "a6230f32938a65d71d81df129c0caa4af846d38bc9d2716d83594cdc43b4b768",
    "DB7_HPQ_US.txt": "e55a9c72d15526abb5f4fd44ee4cd298749c597e29b1c80757c3a07b35202630",
    "DB8_GE_US.txt": "068d7e1f9cd716e3e6e0dc23f9a79471bcc30ea72438e6429ee21bdc9e759c50",
    "NASDAQCOM.txt": "09a5b4be3b66d53ebe0b459bffca01d47b4bf9e5565aa35b87580edb4a97149e",
    "FRED_SP500.txt": "32b519d225f275a33d213f56a6b6f8a969815e15e73cb9ffdee278f6a4811644",
}
JVM_TIMING = ["-Xms2g", "-Xmx8g"]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_status(state: str, step: str = "", msg: str = "") -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    lines = [
        f"STATUS={state}",
        f"PID={os.getpid()}",
        f"STEP={step}",
        f"MSG={msg}",
        f"UPDATED={datetime.now(timezone.utc).isoformat()}",
        f"OUT={OUT}",
    ]
    STATUS.write_text("\n".join(lines) + "\n", encoding="utf-8")


def log(msg: str) -> None:
    line = f"[{datetime.now().isoformat(timespec='seconds')}] {msg}"
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8", errors="replace") as f:
        f.write(line + "\n")


def run(step: str, cmd: list[str], cwd: Path) -> None:
    write_status("RUNNING", step)
    log(f"$ {' '.join(cmd)}  (cwd={cwd})")
    with LOG.open("a", encoding="utf-8", errors="replace") as f:
        f.write(f"--- {step} ---\n")
        f.flush()
        proc = subprocess.run(
            cmd,
            cwd=str(cwd),
            stdout=f,
            stderr=subprocess.STDOUT,
            check=False,
        )
    if proc.returncode != 0:
        raise RuntimeError(f"{step} exit={proc.returncode}")
    log(f"ok {step}")


def host_bits() -> dict[str, str]:
    info = {
        "hostname": platform.node(),
        "os": f"{platform.system()} {platform.release()} {platform.version()}",
        "arch": platform.machine(),
        "python": sys.version.split()[0],
        "processors": str(os.cpu_count() or ""),
    }
    try:
        ps = subprocess.run(
            [
                "powershell", "-NoProfile", "-Command",
                "(Get-CimInstance Win32_Processor).Name; "
                "[math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory/1GB,0)",
            ],
            capture_output=True, text=True, check=False,
        )
        lines = [ln.strip() for ln in ps.stdout.splitlines() if ln.strip()]
        if lines:
            info["cpu"] = lines[0]
        if len(lines) > 1:
            info["ram_gb"] = lines[1]
    except OSError:
        pass
    try:
        git = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(PAPER_ROOT), capture_output=True, text=True, check=False,
        )
        if git.returncode == 0:
            info["git"] = git.stdout.strip()
    except OSError:
        pass
    return info


def write_environment(extra: dict[str, str]) -> None:
    env_path = OUT / "host_environment.txt"
    lines = [f"{k}={v}" for k, v in extra.items()]
    java = subprocess.run(["java", "-version"], capture_output=True, text=True, check=False)
    javac = subprocess.run(["javac", "-version"], capture_output=True, text=True, check=False)
    lines.append("java_version_raw=" + (java.stderr or java.stdout).replace("\n", " | ").strip())
    lines.append("javac_version_raw=" + (javac.stdout or javac.stderr).replace("\n", " | ").strip())
    lines.append("jvm_timing=" + " ".join(JVM_TIMING))
    lines.append("rss_flags=-Xmx8g (no -Xms)")
    lines.append("central=5 warmup + 10 measured")
    lines.append("sensitivity=3 warmup + 5 measured")
    lines.append("rss=3 warmup + 5 measured, fresh JVM per (series, mode)")
    lines.append("K=50")
    lines.append("minLen=2")
    lines.append("maxLen=12")
    lines.append("k=1/n")
    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def verify_datasets() -> None:
    missing = []
    bad = []
    recorded = []
    for name in OFFICIAL_NAMES:
        path = OFFICIAL_DIR / name
        if not path.exists():
            missing.append(str(path))
            continue
        digest = sha256(path)
        recorded.append(f"{name} n_bytes={path.stat().st_size} sha256={digest}")
        expected = EXPECTED_SHA.get(name)
        if expected and digest != expected:
            bad.append(f"{name} got={digest} expected={expected}")
    for name in PUBLIC_NAMES:
        path = PUBLIC_DIR / name
        if not path.exists():
            missing.append(str(path))
            continue
        digest = sha256(path)
        recorded.append(f"{name} n_bytes={path.stat().st_size} sha256={digest}")
        expected = EXPECTED_SHA.get(name)
        if expected and digest != expected:
            bad.append(f"{name} got={digest} expected={expected}")
    (OUT / "DATASETS.sha256").write_text("\n".join(recorded) + "\n", encoding="utf-8")
    if missing:
        raise FileNotFoundError("missing datasets: " + "; ".join(missing))
    if bad:
        raise ValueError("SHA-256 mismatch: " + "; ".join(bad))


def public_series() -> list[str]:
    return [str(PUBLIC_DIR / n) for n in PUBLIC_NAMES]


def promote_to_results_root() -> None:
    """Copy this run to results-campaign/, after archiving the previous locked files once."""
    root = SRC_ROOT / "results-campaign"
    archive = root / "archive-20260906"
    archive.mkdir(exist_ok=True)
    for name in ["timing.csv", "canonical.tsv", "environment.txt", "PROTOCOL.txt", "SUMMARY.md"]:
        src = root / name
        dst = archive / name
        if src.exists() and not dst.exists():
            shutil.copy2(src, dst)
    for name in [
        "timing.csv", "canonical.tsv", "canonical.csv", "environment.txt",
        "host_environment.txt", "full_paper1.csv", "full_paper1_canonical.tsv",
        "full_paper1_rss.csv", "full_paper1_oneshot.csv", "full_paper1_SUMMARY.md",
        "full_paper1_tables.tex", "tables_manuscript.tex", "numbers.json",
        "PROTOCOL.txt", "DATASETS.sha256", "campaign.log",
    ]:
        src = OUT / name
        if src.exists():
            shutil.copy2(src, root / name)
    log(f"promoted artifacts to {root}")


def write_protocol() -> None:
    text = f"""Paper-1 campaign — {datetime.now().date().isoformat()}
Host: {platform.node()}
Out: {OUT}
Java flags (timing): {' '.join(JVM_TIMING)}
RSS flags: -Xmx8g, no -Xms
Timer: System.nanoTime around mine() only
Official: CampaignRunner 5 warmup + 10 measured (central); 3+5 for K/L/k sweeps
Canonical official: CanonicalDump TSV (untimed, separate process after timing)
Public: Paper1SeriesRunner, same central cell, 5 warmup + 10 measured
RSS: run_rss.py, fresh JVM per (series, mode), 3 warmup + 5 measured
Datasets: official OPF DB1–DB8 SHA-256 as DATASETS.sha256; public SILSO + FRED
Do not mix this folder with results-campaign/timing.csv from another host or date.
"""
    (OUT / "PROTOCOL.txt").write_text(text, encoding="utf-8")


def main() -> int:
    os.environ.setdefault("MPLBACKEND", "Agg")
    os.environ.setdefault("PYTHONUNBUFFERED", "1")
    t0 = time.time()
    OUT.mkdir(parents=True, exist_ok=True)
    if LOG.exists():
        LOG.unlink()
    write_status("RUNNING", "start")
    log(f"campaign start out={OUT} pid={os.getpid()}")
    try:
        write_environment(host_bits())
        write_protocol()
        run("prepare_public", [sys.executable, str(SCRIPTS / "prepare_public.py")], JAVA_ROOT)
        verify_datasets()
        log("dataset SHA-256 ok")
        run(
            "build",
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(SCRIPTS / "build.ps1")],
            JAVA_ROOT,
        )
        run("SelfTest", ["java", "-cp", "target/classes", "org.tkhjopf.app.SelfTest"], JAVA_ROOT)
        run("RandomizedSelfTest", ["java", "-cp", "target/classes", "org.tkhjopf.app.RandomizedSelfTest"], JAVA_ROOT)
        run(
            "CampaignRunner",
            ["java", *JVM_TIMING, "-cp", "target/classes", "org.tkhjopf.app.CampaignRunner",
             str(OFFICIAL_DIR), str(OUT), "5", "10"],
            JAVA_ROOT,
        )
        run(
            "CanonicalDump",
            ["java", *JVM_TIMING, "-cp", "target/classes", "org.tkhjopf.app.CanonicalDump",
             str(OFFICIAL_DIR), str(OUT / "canonical.tsv")],
            JAVA_ROOT,
        )
        run(
            "Paper1SeriesRunner",
            ["java", *JVM_TIMING, "-cp", "target/classes", "org.tkhjopf.app.Paper1SeriesRunner",
             str(OUT), *public_series()],
            JAVA_ROOT,
        )
        run(
            "RSS",
            [sys.executable, str(SCRIPTS / "run_rss.py"),
             "--out-dir", str(OUT),
             "--official-dir", str(OFFICIAL_DIR),
             "--public-dir", str(PUBLIC_DIR),
             "--cwd", str(JAVA_ROOT)],
            JAVA_ROOT,
        )
        run(
            "aggregate",
            [sys.executable, str(SCRIPTS / "aggregate_paper1.py"), "--res-dir", str(OUT)],
            JAVA_ROOT,
        )
        fig_run = OUT / "figures"
        fig_ms = PAPER_ROOT / "manuscript" / "figures"
        fig_sub = PAPER_ROOT / "submit" / "figures"
        run(
            "plot",
            [sys.executable, str(SCRIPTS / "plot_campaign.py"),
             "--timing", str(OUT / "timing.csv"),
             "--public", str(OUT / "full_paper1.csv"),
             "--rss", str(OUT / "full_paper1_rss.csv"),
             "--fig-dir", str(fig_run),
             "--fig-dir", str(fig_ms),
             "--fig-dir", str(fig_sub)],
            JAVA_ROOT,
        )
        promote_to_results_root()
        elapsed = time.time() - t0
        log(f"campaign done in {elapsed/60:.1f} min")
        write_status("DONE", "done", f"elapsed_s={elapsed:.0f}")
        return 0
    except Exception as exc:
        log("FAILED: " + str(exc))
        log(traceback.format_exc())
        write_status("FAILED", "error", str(exc).replace("\n", " ")[:500])
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
