#!/usr/bin/env bash
set -euo pipefail

echo "============================================================"
echo " Publish to PyPI (PRODUCTION)"
echo " https://pypi.org/project/pip-audit-html/"
echo "============================================================"
echo ""
echo " WARNING: This will publish to the LIVE PyPI registry."
echo "          Ensure the version in pyproject.toml is correct"
echo "          and 009_build.sh has been run."
echo ""
read -r -p "Type YES to continue: " CONFIRM
if [ "$CONFIRM" != "YES" ]; then
  echo "Aborted."
  exit 0
fi

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
  echo "      You will be prompted for your PyPI API token."
  echo "      Get one at: https://pypi.org/manage/account/token/"
  echo ""
fi

./.venv/bin/python -m twine upload \
  --username __token__ \
  dist/*

echo ""
echo "Published to PyPI!"
echo "  pip install pip-audit-html"
