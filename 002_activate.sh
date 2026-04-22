#!/usr/bin/env bash
if [ ! -f ./.venv/bin/activate ]; then
  echo "ERROR: .venv not found. Run 001_env.sh first."
  return 1 2>/dev/null || exit 1
fi
source ./.venv/bin/activate
