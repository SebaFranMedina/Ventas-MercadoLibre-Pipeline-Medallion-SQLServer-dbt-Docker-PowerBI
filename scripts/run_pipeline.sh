#!/usr/bin/env bash
set -euo pipefail
INPUT_FILE="${INPUT_FILE:-data/sample/sample_sales.xlsx}"

if [ -d "$INPUT_FILE" ]; then
  shopt -s nullglob
  files=("$INPUT_FILE"/*.xlsx)
  [ ${#files[@]} -gt 0 ] || { echo "No .xlsx files in $INPUT_FILE"; exit 2; }
else
  files=("$INPUT_FILE")
fi

echo ">> 1/4 Ingest to bronze (${#files[@]} file(s))"
for f in "${files[@]}"; do
  echo "   - $f"
  python -m ml_pipeline.ingest "$f"
done
echo ">> 2/4 dbt seed"
dbt seed --project-dir dbt --profiles-dir dbt
echo ">> 3/4 dbt build (silver + gold + tests)"
dbt build --project-dir dbt --profiles-dir dbt
echo ">> 4/4 Grants for Power BI"
python -m ml_pipeline.grants
echo "Done."
