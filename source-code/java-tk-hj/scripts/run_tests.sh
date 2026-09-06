#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
bash scripts/build.sh
java -cp target/classes org.tkhjopf.app.SelfTest
java -cp target/classes org.tkhjopf.app.RandomizedSelfTest
