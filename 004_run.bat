@echo off
if not exist .\.venv\Scripts\python.exe (
  echo ERROR: .venv not found. Run 001_env.bat and 003_setup.bat first.
  exit /b 1
)
.\.venv\Scripts\pip-audit-html.exe --help
