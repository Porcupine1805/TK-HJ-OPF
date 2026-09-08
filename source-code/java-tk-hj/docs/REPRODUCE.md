# Reproduce the TK-HJ-OPF campaign

Requires JDK 21+ (`javac --release 21`) and, for figures, Python 3 with `numpy` and `matplotlib`.

## Build and tests

```powershell
cd source-code/java-tk-hj
powershell -File scripts/build.ps1
powershell -File scripts/run_tests.ps1
```

`run_tests` runs `SelfTest`, `RandomizedSelfTest` (2400 brute-force comparisons, plus profile vs naive), and `ProfileExactnessTest`.

Single-file companion (same semantics, 1-based endpoints):

```powershell
cd single-file
javac TKHJOPF.java
java TKHJOPF
```

## Official OPF DB1–DB8

Those eight files are **not** redistributed. Copy them to `source-code/data/official/` (or set `TKHJ_OFFICIAL_DIR`) and check SHA-256 in `DATASETS.md`.

```powershell
$env:TKHJ_OFFICIAL_DIR = "C:\path\to\official"
java -Xms2g -Xmx8g -cp target/classes org.tkhjopf.app.CampaignRunner $env:TKHJ_OFFICIAL_DIR ..\results-campaign 5 10
```

## Public series

Converted files are in `source-code/data/public/`. Rebuild from FRED CSVs with `scripts/prepare_public.py` if needed.

```powershell
java -Xms2g -Xmx8g -cp target/classes org.tkhjopf.app.Paper1SeriesRunner ..\results-campaign `
  ..\data\public\SILSO_sunspots.txt ..\data\public\NASDAQCOM.txt ..\data\public\FRED_SP500.txt
```

## Profile ablation

```powershell
java -Xms2g -Xmx8g -cp target/classes org.tkhjopf.app.ProfileAblationRunner `
  $env:TKHJ_OFFICIAL_DIR ..\data\public ..\results-campaign
```

## Locked CSVs

The manuscript numbers come from the files named in `source-code/results-campaign/PROTOCOL.txt`. Do not mix hosts.
