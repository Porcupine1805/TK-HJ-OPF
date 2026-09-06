# Validation status

The package was built and tested with Java 21 in the artifact environment.

## Fixed OPF running example

`SelfTest` compares TK-HJ-OPF against the exhaustive brute-force window oracle on
`t=(15,32,29,27,34,33,25,20,28,23)`, `k=0.1`, `K=5`, lengths 2..10.
It checks pattern identities, occurrence endings, and forgetting supports with tolerance `1e-10`.

Expected ordered result:

1. `(2,1)` — `4.275265959680775`
2. `(1,3,2)` — `2.166905349827049`
3. `(3,2,1)` — `2.108360609853726`
4. `(1,2)` — `1.9606970418658145`
5. `(2,1,3)` — `1.511368077748593`

## Randomized property testing

`RandomizedSelfTest` performs 2,400 deterministic exact comparisons against brute force over small tie-free series, varying `n`, `k`, `minLen`, and `K`. The current suite completes without mismatch.

Run both tests with:

```bash
bash scripts/run_tests.sh
```

These tests establish small-instance semantic consistency; they are not a substitute for the locked journal-scale performance campaign.
