#!/usr/bin/env python3
"""Convert FRED CSVs to space-separated series (skip missing). SILSO converter is prepare_silso.py."""
from __future__ import annotations

import hashlib
from pathlib import Path

PUBLIC = Path(__file__).resolve().parents[2] / "data" / "public"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def convert_fred(src: Path, dst: Path, value_col: int = 1) -> int:
    vals: list[float] = []
    for i, line in enumerate(src.read_text(encoding="utf-8").splitlines()):
        line = line.strip()
        if not line:
            continue
        parts = line.split(",")
        if i == 0 and not parts[0][:1].isdigit():
            continue
        if len(parts) <= value_col:
            continue
        raw = parts[value_col].strip()
        if not raw or raw.upper() in {".", "ND", "NA", "NAN", "NULL"}:
            continue
        vals.append(float(raw))
    dst.write_text(" ".join(f"{v:.10g}" for v in vals), encoding="ascii")
    print(f"{dst.name} n={len(vals)} sha256={sha256(dst)} from {src.name}")
    return len(vals)


def main() -> None:
    PUBLIC.mkdir(parents=True, exist_ok=True)
    n_nd = convert_fred(PUBLIC / "NASDAQCOM.csv", PUBLIC / "NASDAQCOM.txt")
    n_sp = convert_fred(PUBLIC / "SP500.csv", PUBLIC / "FRED_SP500.txt")
    silso = PUBLIC / "SILSO_sunspots.txt"
    if silso.exists():
        n = len(silso.read_text(encoding="ascii").split())
        print(f"{silso.name} n={n} sha256={sha256(silso)}")
    if n_nd < 100 or n_sp < 100:
        raise SystemExit("FRED conversion produced too few points")


if __name__ == "__main__":
    main()
