$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
if (-not (Test-Path "$Root\target\tk-hj-opf.jar")) { & "$Root\scripts\build.ps1" }
java -cp "$Root\target\classes" org.tkhjopf.app.SelfTest
java -jar "$Root\target\tk-hj-opf.jar" --mode tk --input "$Root\data\example_opf.txt" --forgetting 0.1 --topK 5 --maxLen 10
