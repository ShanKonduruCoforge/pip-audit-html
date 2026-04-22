@echo off
echo ============================================================
echo  Publish to PyPI (PRODUCTION)
echo  https://pypi.org/project/pip-audit-html/
echo ============================================================
echo.
echo  WARNING: This will publish to the LIVE PyPI registry.
echo           Ensure the version in pyproject.toml is correct
echo           and 009_build.bat has been run.
echo.
set /p CONFIRM="Type YES to continue: "
if /i not "%CONFIRM%"=="YES" (
  echo Aborted.
  exit /b 0
)

if not exist .\.venv\Scripts\python.exe (
  echo ERROR: .venv not found. Run 001_env.bat and 003_setup.bat first.
  exit /b 1
)

if not exist dist\ (
  echo ERROR: dist\ not found. Run 009_build.bat first.
  exit /b 1
)

if "%TWINE_PASSWORD%"=="" (
  echo NOTE: TWINE_PASSWORD env variable not set.
  echo       You will be prompted for your PyPI API token.
  echo       Get one at: https://pypi.org/manage/account/token/
  echo.
)

.\.venv\Scripts\python.exe -m twine upload ^
  --username __token__ ^
  dist\*

echo.
echo Published to PyPI!
echo   pip install pip-audit-html
