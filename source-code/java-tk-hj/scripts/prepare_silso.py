#!/usr/bin/env python3
"""Convert SILSO daily SSN v2.0 CSV to a space-separated series (skip missing -1)."""
from pathlib import Path

src = Path(__file__).resolve().parents[2] / "data" / "public" / "SN_d_tot_V2.0.csv"
dst = Path(__file__).resolve().parents[2] / "data" / "public" / "SILSO_sunspots.txt"
vals = []
for line in src.read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if not line or line.startswith("#"):
        continue
    parts = [p.strip() for p in line.replace(",", ";").split(";")]
    if len(parts) < 5:
        continue
    ssn = float(parts[4])
    if ssn < 0:
        continue
    vals.append(ssn)
dst.write_text(" ".join(f"{v:.4g}" for v in vals), encoding="ascii")
print(f"n={len(vals)} -> {dst}")
