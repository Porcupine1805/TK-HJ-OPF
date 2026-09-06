#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
rm -rf "$ROOT/target"
mkdir -p "$ROOT/target/classes"
find "$ROOT/src/main/java" -name '*.java' | sort > "$ROOT/target/sources.txt"
javac --release 21 -d "$ROOT/target/classes" @"$ROOT/target/sources.txt"
jar --create --file "$ROOT/target/tk-hj-opf.jar" --main-class org.tkhjopf.app.Main -C "$ROOT/target/classes" .
echo "Built $ROOT/target/tk-hj-opf.jar"
