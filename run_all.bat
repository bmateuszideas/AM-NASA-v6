@echo off
SETLOCAL ENABLEDELAYEDEXPANSION

REM Przejdź do katalogu, w którym leży ten plik
cd /d "%~dp0"

echo [RUN_ALL] Checking virtualenv .venv ...

IF NOT EXIST ".venv\Scripts\python.exe" goto CREATE_VENV
echo [RUN_ALL] Found existing .venv
goto INSTALL

:CREATE_VENV
echo [RUN_ALL] Creating .venv ...
python -m venv .venv
IF ERRORLEVEL 1 (
  echo [ERROR] Failed to create virtualenv. Make sure Python is installed and in PATH.
  goto END
)

echo [RUN_ALL] .venv created successfully

:INSTALL
echo [RUN_ALL] Installing dependencies ...
".venv\Scripts\python.exe" -m pip install -U pip
IF EXIST "requirements.txt" (
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt
) ELSE (
  echo [WARN] requirements.txt not found - skipping dependency install
)

echo [RUN_ALL] Running tests (pytest -v) ...
".venv\Scripts\python.exe" -m pytest -v
IF ERRORLEVEL 1 (
  echo [WARN] Tests failed. Check the logs above.
)

echo [RUN_ALL] Running AMJD pipeline ...
".venv\Scripts\python.exe" -m scripts.amjd_validate_master
".venv\Scripts\python.exe" -m scripts.amjd_raw_to_master_like
".venv\Scripts\python.exe" -m scripts.amjd_volcano_process
".venv\Scripts\python.exe" -m scripts.amjd_portfolio_summary
".venv\Scripts\python.exe" -m scripts.amjd_event_index

echo.
echo [RUN_ALL] Starting API server in a separate window...
start "" ".venv\Scripts\python.exe" -m uvicorn app.main:app --reload

echo.
echo [DONE] AM-NASA v6 pipeline finished and API started.
echo Open http://127.0.0.1:8000/ in your browser.
echo.

:END
ENDLOCAL
pause
