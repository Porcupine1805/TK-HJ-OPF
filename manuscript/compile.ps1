# Local pdfLaTeX + BibTeX build (Overleaf uses latexmk with the same sequence).
Set-Location $PSScriptRoot
$ErrorActionPreference = "Continue"

Write-Host "=== pdflatex (1/3) ==="
pdflatex -interaction=nonstopmode -file-line-error main.tex
if ($LASTEXITCODE -ne 0) { throw "pdflatex 1 failed: $LASTEXITCODE" }

Write-Host "=== bibtex ==="
bibtex main
if ($LASTEXITCODE -ne 0) { throw "bibtex failed: $LASTEXITCODE" }

Write-Host "=== pdflatex (2/3) ==="
pdflatex -interaction=nonstopmode -file-line-error main.tex
if ($LASTEXITCODE -ne 0) { throw "pdflatex 2 failed: $LASTEXITCODE" }

Write-Host "=== pdflatex (3/3) ==="
pdflatex -interaction=nonstopmode -file-line-error main.tex
if ($LASTEXITCODE -ne 0) { throw "pdflatex 3 failed: $LASTEXITCODE" }

if (-not (Test-Path ".\main.pdf")) { throw "main.pdf was not produced" }
Get-Item ".\main.pdf" | Select-Object FullName, Length, LastWriteTime
