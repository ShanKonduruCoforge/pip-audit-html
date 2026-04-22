#!/usr/bin/env bash
set -euo pipefail
if [ ! -x ./.venv/bin/python ]; then
  echo "ERROR: .venv not found. Run 001_env.sh and 003_setup.sh first."
  exit 1
fi

echo "Installing build tools..."
./.venv/bin/python -m pip install --upgrade build twine --quiet

echo "Cleaning previous dist/..."
rm -rf dist/

echo "Building sdist and wheel..."
./.venv/bin/python -m build

echo ""
echo "Validating distribution..."
./.venv/bin/python -m twine check dist/*

echo ""
echo "Build complete. Artifacts in dist/"
ls -lh dist/
