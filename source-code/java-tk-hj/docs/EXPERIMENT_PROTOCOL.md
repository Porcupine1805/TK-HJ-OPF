# Experiment protocol for the journal manuscript

## Planned testbed

Record the exact final machine before generating publishable values. The current manuscript template contains the intended environment fields (CPU, cores, RAM, OS, Java distribution/build, JVM heap, GC). Do not mix results from different machines in one timing table.

## Required algorithms

A. Original OPF-Miner release (external, unchanged).
B. Same-code nested join baseline (`baseline`) for causal isolation.
C. HJ-OPF only (`hj`).
D. Exhaustive HJ top-k semantic baseline (`hjtopk`): HJ enumeration with no top-k search pruning.
E. Full TK-HJ-OPF (`tk`).
F. Exact ablations: `tk-no-pdub`, `tk-no-dub`, and `tk-no-bounds`. Keep immediate-child PUB only as a diagnostic bound; it is not a safe whole-pair pruning rule by itself.
G. Brute force only for small correctness instances.

## Research questions

RQ1 Exactness: canonical pattern-support equality against brute force on small series and against OPF-Miner for thresholded cells.
RQ2 Pair discovery: pair attempts, compatible pairs J, and hash join reduction.
RQ3 Top-k effectiveness: runtime versus K and the exhaustive HJ baseline.
RQ4 Pruning: PDUB whole-pair prune ratio, DUB branch prune ratio, expanded patterns, aligned-occurrence comparisons.
RQ5 Scalability: increasing n and decreasing threshold-equivalent density.
RQ6 Sensitivity: K and forgetting factor k.
RQ7 Memory: peak JVM heap and OS RSS using the same sampling method for every algorithm.
RQ8 Ablation: exhaustive HJ top-k; HJ+PDUB; HJ+DUB; full TK-HJ-OPF.

## Datasets

Use the OPF-Miner DB1--DB8 suite for comparability. Add the UCI ElectricityLoadDiagrams20112014 length ladder only as a controlled scalability study, and add at least one independent large public time-series family (e.g., UCR datasets selected before timing) to reduce suite-specific bias.

## Timing protocol

- Java 21 LTS or one frozen JDK build across all methods.
- Fixed JVM flags and garbage collector.
- At least 3 discarded warmups, then 10 measured runs for ordinary cells; increase to 20--30 for sub-50-ms cells or use batching.
- Report median, IQR, bootstrap 95% CI, and geometric-mean speedup across heterogeneous cells.
- Use paired Wilcoxon tests only on genuinely paired experimental units; apply Holm correction when testing multiple variants.
- Put correctness dumps outside timed regions.
- Record timeout and OOM as censored outcomes, never silently drop cells.

## Reproducibility bundle

Freeze dataset SHA-256 checksums, command lines, JVM flags, raw per-run CSV, aggregation script, canonical outputs, and the exact source commit used for each reported table/figure.
