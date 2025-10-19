@echo off
REM Set fixed parameters
set YEAR=2024
set MONTH=12
set DAY=1
set START_MINUTE=0
set START_SECOND=0
set DURATION=3600
set STEP=60
set OUTPUT_DIR=data\flights\

REM Loop through each hour of the day
for /L %%H in (0,1,23) do (
    echo Running for hour %%H
    python download_adsb.py ^
        --year %YEAR% ^
        --month %MONTH% ^
        --day %DAY% ^
        --start-hour %%H ^
        --start-minute %START_MINUTE% ^
        --start-second %START_SECOND% ^
        --duration %DURATION% ^
        --step %STEP% ^
        --output-dir %OUTPUT_DIR%
)
pause
