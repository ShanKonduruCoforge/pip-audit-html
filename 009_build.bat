@echo off
if not exist .\.venv\Scripts\python.exe (
  echo ERROR: .venv not found. Run 001_env.bat and 003_setup.bat first.
  exit /b 1
)

echo Installing build tools...
.\.venv\Scripts\python.exe -m pip install --upgrade build twine --quiet

if exist dist (
  echo Cleaning previous dist\...
  rmdir /s /q dist
)

echo Building sdist and wheel...
.\.venv\Scripts\python.exe -m build

echo.
echo Validating distribution...
.\.venv\Scripts\python.exe -m twine check dist\*

echo.
echo Build complete. Artifacts in dist\
dir dist\
