$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root
& "$Root\scripts\build.ps1"
java -cp target/classes org.tkhjopf.app.SelfTest
java -cp target/classes org.tkhjopf.app.RandomizedSelfTest
