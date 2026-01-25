@echo off
TITLE Library Attendance System Server
ECHO ======================================================
ECHO      STARTING UCC LIBRARY ATTENDANCE SYSTEM
ECHO ======================================================
ECHO Please do not close this window while the system is in use.
ECHO.

:: 1. Navigate to project folder
cd /d "C:\Users\Vincent\PycharmProjects\library_project"

:: 2. Activate Virtual Environment (Using .venv based on your logs)
call .venv\Scripts\activate

:: 3. Run the production server
python run_production.py

pause