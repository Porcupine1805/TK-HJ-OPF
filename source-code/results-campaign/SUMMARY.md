# Campaign summary (this host, not ver1 ARM64 numbers)

Full remaining-experiment write-up: `full_paper1_SUMMARY.md` (public 5-mode, bootstrap CIs, Wilcoxon, RSS).

## Central K=50, L=12, k=1/n  (median ms)

| dataset | n | hjtopk | tk-no-bounds | tk-no-pdub | tk-no-dub | tk | speedup_hj_over_tk | speedup_hj_over_dub |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DB1_Amazon | 5842 | 69.941 | 45.781 | 1.859 | 1.994 | 1.961 | 35.66x | 37.62x |
| DB2_Russell2000 | 8141 | 64.229 | 63.216 | 2.542 | 2.602 | 2.669 | 24.07x | 25.27x |
| DB6_CL_US | 10305 | 49.993 | 42.595 | 2.318 | 2.650 | 2.399 | 20.84x | 21.56x |
| DB7_HPQ_US | 12075 | 53.981 | 48.721 | 2.801 | 3.161 | 2.895 | 18.64x | 19.27x |
| DB3_Nasdaq | 12279 | 89.371 | 90.814 | 3.349 | 3.734 | 3.508 | 25.48x | 26.68x |
| DB8_GE_US | 14058 | 50.950 | 49.464 | 3.199 | 3.433 | 3.219 | 15.83x | 15.93x |
| DB4_SP500 | 23046 | 146.488 | 142.610 | 5.622 | 6.420 | 6.135 | 23.88x | 26.05x |
| DB5_NYSE | 60000 | 96.432 | 107.440 | 14.676 | 14.791 | 14.026 | 6.88x | 6.57x |

geomean speedup HJ/tk = 19.63x
geomean speedup HJ/DUB-only = 20.29x

## Canonical SHA agreement at central config

| dataset | unique SHAs among 5 modes | note |
| --- | --- | --- |
| DB1_Amazon.txt | 1 | identical |
| DB2_Russell2000.txt | 1 | identical |
| DB6_CL_US.txt | 1 | identical |
| DB7_HPQ_US.txt | 1 | identical |
| DB3_Nasdaq.txt | 1 | identical |
| DB8_GE_US.txt | 1 | identical |
| DB4_SP500.txt | 1 | identical |
| DB5_NYSE.txt | 1 | identical |
