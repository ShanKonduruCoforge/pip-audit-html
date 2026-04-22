#!/usr/bin/env bash
set -uo pipefail

if [ ! -x ./.venv/bin/python ]; then
  echo "ERROR: .venv not found. Run 001_env.sh and 003_setup.sh first."
  exit 1
fi

echo "Installing pip-audit if not already present..."
./.venv/bin/python -m pip install pip-audit --quiet

mkdir -p audit_reports

echo "Running pip-audit and generating JSON..."
./.venv/bin/python -m pip_audit --format json --output audit_reports/pip-audit-report.json 2>/dev/null || {
  if [ ! -f audit_reports/pip-audit-report.json ]; then
    echo "ERROR: pip-audit failed and produced no output."
    exit 1
  fi
  echo "NOTE: pip-audit reported vulnerabilities. Continuing to generate HTML report."
}

echo "Converting JSON report to HTML..."
./.venv/bin/pip-audit-html audit_reports/pip-audit-report.json \
  -o audit_reports/pip-audit-report.html \
  --title "pip-audit Security Report"

echo ""
echo "Done! Open the report:"
echo "  audit_reports/pip-audit-report.html"
