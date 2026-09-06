# Novelty-search log (Paper 1: TK-HJ-OPF)

Date: 6–7 September 2026  
Scope: exact *global* top-K order-preserving pattern mining under OPF exponential forgetting.

## Queries

| Database | Query (examples) |
|---|---|
| IEEE Xplore / TKDE | `OPF-Miner forgetting`; `order-preserving top-k pattern mining`; `order-preserving suffix tree mining` |
| arXiv | `order-preserving pattern mining` (cs.DS / cs.DB, 2024–2026) |
| Publisher sites | COPP-Miner; SOPP-Miner; OIP-Miner; Zhou OPPM review |

## Inclusion / exclusion

Include: OP mining or OP matching with a top-K *or* forgetting objective.  
Exclude: ordinary itemset top-K; unweighted frequent/maximal/closed OP unless it is the complexity competitor.

## Hits (not TK-HJ)

- OPF-Miner (TKDE 2024): minsup OPF, lists top-K OPF as future work.
- COPP-Miner (TKDE 2024): top-K *contrast* OP, different score.
- OPST mining (ICDM 2024 / TKDE 2026): unweighted frequent/maximal/closed after an index.
- SOPP-Miner (TKDE 2026): stability; top-K as downstream selection.
- OIP-Miner (SCIS 2025): forgetting factor, not OP windows.
- Zhou et al. OPPM review (TKDE 2026): matching, not recency-weighted top-K mining.

## Decision

No published algorithm was found whose *primary* objective is exact global top-K under OPF exponential forgetting with fusion + DUB/PDUB. This log is **not** a non-existence proof and does not support a “first ever top-K OP method” claim (COPP already uses top-K).
