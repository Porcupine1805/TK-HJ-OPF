# Datasets (paper 1)

Bundled: `source-code/data/example_opf.txt` (OPF running example).

## Public (redistributable with attribution)

WDC-SILSO daily total sunspot number v2.0 (CC BY-NC 4.0).
Source: https://www.sidc.be/SILSO/DATA/SN_d_tot_V2.0.csv  
Converted series (SSN < 0 dropped): `source-code/data/public/SILSO_sunspots.txt` (`n=72967`).
Campaign: `source-code/results-campaign/public_silso.csv` (this host, 2026-09-07).

## Official OPF-Miner DB1–DB8 (not redistributed)

Copy the eight `.txt` files locally and check SHA-256:

| File | n | SHA-256 |
|---|---:|---|
| DB1_Amazon.txt | 5842 | `0f826c7af3ef51a9bda6f9d69e66e962c4a776c3ee56fd88db41cd9fbc777b1d` |
| DB2_Russell2000.txt | 8141 | `3035a617532ca8826f17b814d4b064244f3294cfc915acd3777334e5a02e0cbf` |
| DB3_Nasdaq.txt | 12279 | `841367472d7b12e44d99f7562457116e8ce179b67bbb1cce9581d331d181b431` |
| DB4_SP500.txt | 23046 | `42084a62c8840ac4970ae6c36b9482c33b9b3bdac0bc5a5bc028e876d92ef0e8` |
| DB5_NYSE.txt | 60000 | `89aeeb3c4c1a3284600ffc2a6a8592fde4cc529ab124cd7ebd80c43262c3cc66` |
| DB6_CL_US.txt | 10305 | `a6230f32938a65d71d81df129c0caa4af846d38bc9d2716d83594cdc43b4b768` |
| DB7_HPQ_US.txt | 12075 | `e55a9c72d15526abb5f4fd44ee4cd298749c597e29b1c80757c3a07b35202630` |
| DB8_GE_US.txt | 14058 | `068d7e1f9cd716e3e6e0dc23f9a79471bcc30ea72438e6429ee21bdc9e759c50` |
