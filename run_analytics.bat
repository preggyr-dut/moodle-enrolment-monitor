@echo off
echo ========================================
echo Moodle Daily Enrollment Analytics
echo ========================================
echo.

echo Installing/updating dependencies...
pip install -r requirements.txt
echo.

echo Running enrollment analytics...
python enrollment_analytics.py
echo.

echo Press any key to continue...
pause > nul