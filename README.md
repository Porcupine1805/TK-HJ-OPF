# TK-HJ-OPF

Exact, threshold-free **top-K order-preserving pattern mining** under exponential
forgetting (TK-OPF), via a hash-indexed prefix–suffix join, descendant bounds
(DUB / PDUB), and depth-UB profiles.

This repository is **source code and locked campaign CSVs** (no manuscript PDF).

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

## Modes

| Mode | Meaning |
|---|---|
| `hjtopk` | exhaustive hash-join top-K, no search pruning |
| `tk-no-bounds` | heap + join, neither bound |
| `tk-no-dub` | PDUB only |
| `tk-no-pdub` | DUB only |
| `tk-naive` | PDUB + DUB, breakpoint oracles |
| `tk` | PDUB + DUB, **depth-UB profiles** (default) |

Do not use threshold modes `baseline` / `hj` in TK-OPF claims (forgetting support is not anti-monotone).

## Locked campaign (manuscript)

Host: Intel Core i5-8250U, Windows 11, Temurin 25, `-Xms2g -Xmx8g`.
Central cell `K=50`, `ℓ_max=12`, `k=1/n`.

- Official OPF DB1–DB8: geomean **19.63×** (`hjtopk` / `tk`) — `source-code/results-campaign/timing.csv`
- Depth-UB profile ablation: geomean **1.16×** (naive PDUB / profile) — `profile_ablation.csv`

See `source-code/results-campaign/PROTOCOL.txt` and `source-code/java-tk-hj/docs/REPRODUCE.md`.

Official DB1–DB8 `.txt` files are **not** redistributed. SHA-256: `DATASETS.md`.

## License

GPL-3.0-or-later. Clean-room Java; does not copy OPF-Miner source.
See `NOTICE.md`.
