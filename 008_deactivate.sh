#!/usr/bin/env bash
if command -v deactivate >/dev/null 2>&1; then
  deactivate
else
  echo "No active virtual environment detected."
fi
