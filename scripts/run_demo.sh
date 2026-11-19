#!/usr/bin/env bash
# Runs the tests and the full pipeline, then copies the main outputs to evidence/.
set -euo pipefail
cd "$(dirname "$0")/.."

python3 -m unittest discover -s tests -v 2>&1 | tee /tmp/aab_tests.txt
python3 -m aab.run

mkdir -p evidence/gold
cp out/lake/gold/kpi_*.csv evidence/gold/
cp out/lake/quality_report.json out/lake/catalog.json evidence/
cp out/business-case.md out/value-streams.md out/portfolio.md out/policy_digest.md evidence/
cp out/rapid_response_queue.json out/adoption_dashboard.html evidence/
cp /tmp/aab_tests.txt evidence/tests.txt
echo "Evidence updated in evidence/"
