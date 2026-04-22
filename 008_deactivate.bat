@echo off
if "%VIRTUAL_ENV%"=="" (
  echo No active virtual environment detected.
  exit /b 0
)
if exist .\.venv\Scripts\deactivate.bat call .\.venv\Scripts\deactivate.bat
