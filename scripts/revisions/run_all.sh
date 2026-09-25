#!/usr/bin/env bash
# Run every revision analysis. Execute from the repository root:
#   bash scripts/revisions/run_all.sh
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="reviews/outputs"

echo "== sanity check =="
python "$HERE/_sanity_check.py" | tee "$OUT/_sanity_check.txt" 2>/dev/null || true

echo "== R3: stocks-only (refilter) =="
python "$HERE/r3_stocks_only.py" --mode refilter --metrics hcm,pozzi

echo "== R3: stocks-only (rebuild) =="
# Uncomment once scikit-learn is available in the active environment.
# python "$HERE/r3_stocks_only.py" --mode rebuild --metrics hcm

echo "== R2: size double-sort + BAB spanning =="
python "$HERE/r2_spanning.py"

echo "== R8: sub-period + multiplicity + decile sensitivity =="
python "$HERE/r8_multiple_testing.py" --metric hcm

echo "== S1: costs + capacity =="
python "$HERE/s1_costs_capacity.py" --metric hcm

echo "== done -> $OUT =="
