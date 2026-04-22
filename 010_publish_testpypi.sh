#!/usr/bin/env bash
set -euo pipefail

echo "============================================================"
echo " Publish to TestPyPI"
echo " https://test.pypi.org/project/pip-audit-html/"
echo "============================================================"
echo ""

if [ ! -x ./.venv/bin/python ]; then
  echo "ERROR: .venv not found. Run 001_env.sh and 003_setup.sh first."
  exit 1
fi

if [ ! -d dist ]; then
  echo "ERROR: dist/ not found. Run 009_build.sh first."
  exit 1
fi

if [ -z "${TWINE_PASSWORD:-}" ]; then
  echo "NOTE: TWINE_PASSWORD env variable not set."
  echo "      You will be prompted for your TestPyPI API token."
  echo "      Get one at: https://test.pypi.org/manage/account/token/"
  echo ""
fi

./.venv/bin/python -m twine upload \
  --repository-url https://test.pypi.org/legacy/ \
  --username __token__ \
  dist/*

echo ""
echo "Published to TestPyPI. Install and verify with:"
echo "  pip install --index-url https://test.pypi.org/simple/ pip-audit-html"
