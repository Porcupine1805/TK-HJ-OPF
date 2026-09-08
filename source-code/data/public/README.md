# Public series (redistributable with attribution)

`SILSO_sunspots.txt`: WDC-SILSO daily total sunspot number v2.0, missing markers
(SSN < 0) dropped, `n=72967`. CC BY-NC 4.0.
Source: https://www.sidc.be/SILSO/DATA/SN_d_tot_V2.0.csv

`NASDAQCOM.txt`: FRED NASDAQ Composite daily, empty observations dropped, `n=14014`.
`FRED_SP500.txt`: FRED S&P 500 daily downloaded window, `n=2514`
(not official OPF `DB4_SP500.txt`).
Sources: https://fred.stlouisfed.org/series/NASDAQCOM
         https://fred.stlouisfed.org/series/SP500

Rebuild FRED conversions with `java-tk-hj/scripts/prepare_public.py`.
SHA-256 of the converted files: repository root `DATASETS.md`.
