#!/usr/bin/env bash
set -euo pipefail
if [ ! -x ./.venv/bin/python ]; then
  echo "ERROR: .venv not found. Run 001_env.sh first."
  exit 1
fi
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install -r requirements.txt
