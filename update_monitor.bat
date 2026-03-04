@echo off
set TIMESTAMP=%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%

echo [%TIMESTAMP%] Starting monitor update >> monitor_log.txt

cd /d C:\integrator\enrollment-system

python enrollment_monitor.py --output-dir . >> monitor_log.txt 2>&1
python deploy_monitor.py update >> monitor_log.txt 2>&1

echo [%TIMESTAMP%] Monitor update complete >> monitor_log.txt