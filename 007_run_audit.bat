@echo off
if not exist .\.venv\Scripts\python.exe (
  echo ERROR: .venv not found. Run 001_env.bat and 003_setup.bat first.
  exit /b 1
)

echo Installing pip-audit if not already present...
.\.venv\Scripts\python.exe -m pip install pip-audit --quiet

if not exist audit_reports mkdir audit_reports

echo Running pip-audit and generating JSON...
.\.venv\Scripts\python.exe -m pip_audit --format json --output audit_reports\pip-audit-report.json 2>nul
if %errorlevel% neq 0 (
  if not exist audit_reports\pip-audit-report.json (
    echo ERROR: pip-audit failed and produced no output.
    exit /b 1
  )
  echo NOTE: pip-audit reported vulnerabilities. Continuing to generate HTML report.
)

echo Converting JSON report to HTML...
.\.venv\Scripts\pip-audit-html.exe audit_reports\pip-audit-report.json ^
  -o audit_reports\pip-audit-report.html ^
  --title "pip-audit Security Report"

if %errorlevel% neq 0 (
  echo ERROR: HTML conversion failed.
  exit /b 1
)

echo.
echo Done! Open the report:
echo   audit_reports\pip-audit-report.html
