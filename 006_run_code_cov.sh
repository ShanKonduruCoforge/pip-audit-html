#!/usr/bin/env bash
set -euo pipefail
if [ ! -x ./.venv/bin/python ]; then
  echo "ERROR: .venv not found. Run 001_env.sh and 003_setup.sh first."
  exit 1
fi
./.venv/bin/python -m pytest --cov=. --cov-report=html tests/
