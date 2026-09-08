# Depth-UB profile ablation

| dataset | n | DUB-only | Naive PDUB | Profile PDUB | naive/profile | DUB/profile |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Amazon | 5842 | 4.940 | 7.699 | 6.357 | 1.21x | 0.78x |
| Russell 2000 | 8141 | 3.763 | 3.837 | 2.545 | 1.51x | 1.48x |
| Nasdaq | 12279 | 4.424 | 4.217 | 3.965 | 1.06x | 1.12x |
| S&P 500 (OPF) | 23046 | 7.854 | 7.848 | 6.935 | 1.13x | 1.13x |
| NYSE | 60000 | 15.627 | 14.557 | 15.855 | 0.92x | 0.99x |
| CL.US | 10305 | 3.144 | 2.916 | 2.706 | 1.08x | 1.16x |
| HPQ.US | 12075 | 3.394 | 3.360 | 3.163 | 1.06x | 1.07x |
| GE.US | 14058 | 3.282 | 3.291 | 3.077 | 1.07x | 1.07x |
| SILSO | 72967 | 17.336 | 15.035 | 14.089 | 1.07x | 1.23x |
| NASDAQCOM | 14014 | 4.321 | 4.276 | 3.838 | 1.11x | 1.13x |
| S&P 500 (FRED) | 2514 | 1.447 | 1.214 | 0.699 | 1.74x | 2.07x |
| geomean |  |  |  |  | 1.16x | 1.17x |

geomean naive/profile = 1.1597x, DUB-only/profile = 1.1668x, N=11
profile faster than naive on 10/11
profile faster than DUB-only on 9/11

Aligned-check and PDUB-prune counters of naive and profile match on every series.
