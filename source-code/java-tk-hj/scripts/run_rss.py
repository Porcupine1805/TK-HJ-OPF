#!/usr/bin/env python3
"""Fresh-JVM Windows Peak Working Set via GetProcessMemoryInfo.

Uses subprocess argv lists (no PowerShell splitting on spaces).
RSS flags: -Xmx8g only (no -Xms). Timing campaign stays -Xms2g -Xmx8g.
"""
from __future__ import annotations

import argparse
import csv
import ctypes
import os
import subprocess
import sys
import time
from ctypes import wintypes
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT.parent / "results-campaign"
DEFAULT_OFFICIAL = Path(os.environ["TKHJ_OFFICIAL_DIR"]) if os.environ.get("TKHJ_OFFICIAL_DIR") else (ROOT.parent / "data" / "official")
DEFAULT_PUBLIC = ROOT.parent / "data" / "public"
MODES = ["hjtopk", "tk-no-bounds", "tk-no-dub", "tk-no-pdub", "tk"]
OFFICIAL_NAMES = [
    "DB1_Amazon.txt", "DB2_Russell2000.txt", "DB3_Nasdaq.txt", "DB4_SP500.txt",
    "DB5_NYSE.txt", "DB6_CL_US.txt", "DB7_HPQ_US.txt", "DB8_GE_US.txt",
]
PUBLIC_NAMES = ["SILSO_sunspots.txt", "NASDAQCOM.txt", "FRED_SP500.txt"]


class PROCESS_MEMORY_COUNTERS_EX(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("PageFaultCount", wintypes.DWORD),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
        ("PrivateUsage", ctypes.c_size_t),
    ]


psapi = ctypes.WinDLL("psapi")
psapi.GetProcessMemoryInfo.argtypes = [
    wintypes.HANDLE,
    ctypes.POINTER(PROCESS_MEMORY_COUNTERS_EX),
    wintypes.DWORD,
]
psapi.GetProcessMemoryInfo.restype = wintypes.BOOL


def peak_working_set(handle: int) -> int:
    counters = PROCESS_MEMORY_COUNTERS_EX()
    counters.cb = ctypes.sizeof(counters)
    ok = psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb)
    if not ok:
        raise OSError(f"GetProcessMemoryInfo failed, GetLastError={ctypes.GetLastError()}")
    return int(counters.PeakWorkingSetSize)


def run_one(series: Path, mode: str, cwd: Path, cp: str) -> tuple[int, str, float, list[str], str]:
    cmd = [
        "java", "-Xmx8g", "-cp", cp,
        "org.tkhjopf.app.OneShot", str(series), mode, "3", "5", "50", "12",
    ]
    proc = subprocess.Popen(
        cmd,
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    handle = int(proc._handle)  # Windows process handle; valid after wait
    sampled = 0
    while proc.poll() is None:
        try:
            sampled = max(sampled, peak_working_set(handle))
        except OSError:
            pass
        time.sleep(0.02)
    stdout, stderr = proc.communicate(timeout=30)
    try:
        sampled = max(sampled, peak_working_set(handle))
    except OSError:
        pass
    lines = [ln for ln in stdout.splitlines() if ln.strip()]
    data = [ln for ln in lines if not ln.startswith("phase,")]
    n = data[0].split(",")[2] if data else ""
    mb = round(sampled / (1024 * 1024), 1)
    return proc.returncode, n, mb, data, stderr


def series_list(official: Path, public: Path) -> list[Path]:
    out: list[Path] = []
    for name in OFFICIAL_NAMES:
        p = official / name
        if p.exists():
            out.append(p)
    for name in PUBLIC_NAMES:
        p = public / name
        if p.exists():
            out.append(p)
    return out


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    p.add_argument("--official-dir", type=Path, default=DEFAULT_OFFICIAL)
    p.add_argument("--public-dir", type=Path, default=DEFAULT_PUBLIC)
    p.add_argument("--cwd", type=Path, default=ROOT)
    p.add_argument("--cp", default="target/classes")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    out_dir: Path = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    rss_path = out_dir / "full_paper1_rss.csv"
    oneshot_path = out_dir / "full_paper1_oneshot.csv"
    series = series_list(args.official_dir, args.public_dir)
    if len(series) < 11:
        print(f"WARNING series count={len(series)}", file=sys.stderr)
    with rss_path.open("w", encoding="utf-8", newline="") as rf, oneshot_path.open(
        "w", encoding="utf-8", newline=""
    ) as of:
        rss_w = csv.writer(rf)
        rss_w.writerow(["dataset", "mode", "n", "peak_working_set_mb", "rss_flags", "exit", "oneshot_rows"])
        of.write(
            "phase,dataset,n,mode,k,topk,minlen,maxlen,rep,runtime_ms,patterns,"
            "pair_attempts,compatible_pairs,pdub_prunes,dub_prunes,aligned_checks,peak_heap_mb\n"
        )
        failures = 0
        for s in series:
            for mode in MODES:
                print(f"RSS start {s.name} {mode}", flush=True)
                code, n, mb, data, err = run_one(s, mode, args.cwd, args.cp)
                rss_w.writerow([s.name, mode, n, mb, "-Xmx8g", code, len(data)])
                rf.flush()
                for ln in data:
                    of.write(ln + "\n")
                of.flush()
                print(
                    f"RSS {s.name} {mode} n={n} WS={mb} MB exit={code} rows={len(data)}",
                    flush=True,
                )
                if code != 0 or len(data) != 5:
                    failures += 1
                    sys.stderr.write(err[:2000] + "\n")
    if failures:
        raise SystemExit(f"RSS failures={failures}")
    print(f"WROTE {rss_path}", flush=True)


if __name__ == "__main__":
    main()
