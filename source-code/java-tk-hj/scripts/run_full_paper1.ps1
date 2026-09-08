# Full remaining Paper-1 experiments on this host.
# 1) Self-tests
# 2) Public series (SILSO + FRED): 5-mode canonical + 5 warmup / 10 measured, one JVM, -Xms2g -Xmx8g
# 3) Fresh-JVM Working-Set per (series, mode): -Xmx8g and NO large -Xms, so committed heap
#    does not mask per-algorithm RSS. Timing campaign still uses -Xms2g -Xmx8g.
$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

$OutDir = Join-Path (Split-Path -Parent $Root) "results-campaign"
New-Item -ItemType Directory -Force $OutDir | Out-Null
$Log = Join-Path $OutDir "full_paper1.log"
"=== $(Get-Date -Format o) start ===" | Set-Content $Log
java -version 2>> $Log
Write-Host "ROOT=$Root OUT=$OutDir"

& "$Root\scripts\build.ps1"
if ($LASTEXITCODE -ne 0) { throw "build failed" }
"build ok" | Add-Content $Log

Write-Host "=== SelfTest ==="
java -cp target/classes org.tkhjopf.app.SelfTest 2>> $Log
if ($LASTEXITCODE -ne 0) { throw "SelfTest failed" }
Write-Host "=== RandomizedSelfTest ==="
java -cp target/classes org.tkhjopf.app.RandomizedSelfTest 2>> $Log
if ($LASTEXITCODE -ne 0) { throw "RandomizedSelfTest failed" }

Write-Host "=== convert FRED ==="
python "$Root\scripts\prepare_public.py" 2>> $Log
if ($LASTEXITCODE -ne 0) { throw "prepare_public failed" }

$official = if ($env:TKHJ_OFFICIAL_DIR) { $env:TKHJ_OFFICIAL_DIR } else { Join-Path (Split-Path -Parent $Root) "data\official" }
$public = Join-Path (Split-Path -Parent $Root) "data\public"

$publicSeries = @()
foreach ($n in @("SILSO_sunspots.txt", "NASDAQCOM.txt", "FRED_SP500.txt")) {
  $p = Join-Path $public $n
  if (Test-Path $p) { $publicSeries += $p } else { Write-Host "MISSING public $p" }
}

$allSeries = @()
if (Test-Path $official) {
  foreach ($n in @("DB1_Amazon.txt","DB2_Russell2000.txt","DB3_Nasdaq.txt","DB4_SP500.txt","DB5_NYSE.txt","DB6_CL_US.txt","DB7_HPQ_US.txt","DB8_GE_US.txt")) {
    $p = Join-Path $official $n
    if (Test-Path $p) { $allSeries += $p }
  }
}
$allSeries += $publicSeries
Write-Host "PUBLIC=$($publicSeries.Count) ALL=$($allSeries.Count)"
"PUBLIC=$($publicSeries.Count) ALL=$($allSeries.Count)" | Add-Content $Log

# --- 5-mode timing+canonical for public series (locked timing flags) ---
Write-Host "=== Paper1SeriesRunner public ==="
$runnerArgs = @("-Xms2g", "-Xmx8g", "-cp", "target/classes", "org.tkhjopf.app.Paper1SeriesRunner", $OutDir) + $publicSeries
& java @runnerArgs 2>> $Log
Write-Host "SERIES_RUNNER_EXIT=$LASTEXITCODE"
"SERIES_RUNNER_EXIT=$LASTEXITCODE" | Add-Content $Log
if ($LASTEXITCODE -ne 0) { throw "Paper1SeriesRunner failed" }

# --- RSS: Python subprocess + GetProcessMemoryInfo (argv list, no path splitting) ---
Write-Host "=== RSS (run_rss.py) ==="
python "$Root\scripts\run_rss.py" 2>> $Log
if ($LASTEXITCODE -ne 0) { throw "run_rss.py failed" }

Write-Host "=== aggregate ==="
python "$Root\scripts\aggregate_paper1.py" 2>> $Log
Write-Host "DONE rss=$RssCsv"
"=== $(Get-Date -Format o) done ===" | Add-Content $Log
