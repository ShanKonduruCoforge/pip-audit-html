@echo off
if not exist .\.venv\Scripts\python.exe (
  echo ERROR: .venv not found. Run 001_env.bat first.
  exit /b 1
)
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
