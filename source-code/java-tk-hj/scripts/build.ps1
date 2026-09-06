$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Remove-Item -Recurse -Force "$Root\target" -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force "$Root\target\classes" | Out-Null
$Sources = Get-ChildItem -Recurse "$Root\src\main\java\*.java" | ForEach-Object { $_.FullName }
javac --release 21 -d "$Root\target\classes" $Sources
jar --create --file "$Root\target\tk-hj-opf.jar" --main-class org.tkhjopf.app.Main -C "$Root\target\classes" .
Write-Host "Built $Root\target\tk-hj-opf.jar"
