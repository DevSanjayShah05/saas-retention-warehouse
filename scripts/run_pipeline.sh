#!/usr/bin/env bash
# Cohort & Ledger — full ELT pipeline: incremental raw load -> dbt build (run + test).
# Used locally and by .github/workflows/nightly_elt.yml.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "== 1/2: incremental raw load =="
python scripts/load_raw_incremental.py

echo
echo "== 2/2: dbt build (staging -> marts -> analytics, with tests) =="
cd warehouse
export DBT_PROFILES_DIR="$ROOT_DIR/warehouse"
dbt build

echo
echo "Pipeline complete."
