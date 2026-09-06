# TK-HJ-OPF Java 21

Clean-room strict-order global top-K miner. This is the **proposed method** of this repository.

```powershell
powershell -File scripts/build.ps1
powershell -File scripts/run_tests.ps1
java -cp target/classes org.tkhjopf.app.Main --input data/example_opf.txt --mode tk --forgetting 0.1 --topK 5 --minLen 2 --maxLen 10
```

Modes: `hjtopk`, `tk`, `tk-no-pdub`, `tk-no-dub`, `tk-no-bounds`.
Do not use threshold modes `baseline`/`hj` in TK-OPF claims (known incomplete generation on at least one forgetting case).

`single-file/TKHJOPF.java` is the manuscript companion: `javac TKHJOPF.java && java TKHJOPF`.
