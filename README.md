# TK-HJ-OPF

Exact, threshold-free **top-K order-preserving pattern mining** under exponential
forgetting, via a hash-indexed prefix–suffix join and descendant bounds
(DUB / PDUB).

This repository contains **source code and campaign CSVs only** (no manuscript).

## Build and test

Requires JDK 21+ (`javac --release 21`).

```powershell
cd source-code/java-tk-hj
powershell -File scripts/build.ps1
powershell -File scripts/run_tests.ps1
java -cp target/classes org.tkhjopf.app.Main --input ..\data\example_opf.txt --mode tk --forgetting 0.1 --topK 5 --minLen 2 --maxLen 10
```

Self-test expected top-5 on the OPF running example
`t = (15,32,29,27,34,33,25,20,28,23)`, `k=0.1`, `K=5`:
`(2,1)`, `(1,3,2)`, `(3,2,1)`, `(1,2)`, `(2,1,3)`.

## Locked campaign (2026-09-06)

Host: Intel Core i5-8250U, Windows 11, Temurin 25, `-Xms2g -Xmx8g`.
Central grid `K=50`, `ℓ_max=12`, `k=1/n`: geometric-mean speedup of full
`tk` over exhaustive `hjtopk` is **19.63×** on official OPF DB1–DB8.
Raw files: `source-code/results-campaign/timing.csv`, `canonical.tsv`.

Do **not** mix these medians with an earlier ARM64 laptop campaign.

Official DB1–DB8 `.txt` files are **not** in this repository (upstream
license unclear). SHA-256: `DATASETS.md`.

## Modes

`hjtopk`, `tk`, `tk-no-pdub`, `tk-no-dub`, `tk-no-bounds`.
Do not use threshold modes `baseline` / `hj` in TK-OPF claims.

## License

GPL-3.0-or-later. Clean-room Java; does not copy OPF-Miner source.
See `NOTICE.md`.
