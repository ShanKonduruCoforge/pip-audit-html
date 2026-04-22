@echo off
if not exist .\.venv\Scripts\activate.bat (
  echo ERROR: .venv not found. Run 001_env.bat first.
  exit /b 1
)
call .\.venv\Scripts\activate.bat
