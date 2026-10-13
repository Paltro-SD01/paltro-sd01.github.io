@echo off
title Paltro-SD01 Git & LabVIEW Telemetry Launcher
color 0A

echo ====================================================================
echo   Paltro-SD01 | LabVIEW & Git Telemetry Control Launcher
echo ====================================================================
echo.
echo   [1] Open Live Web Dashboard in Browser (https://paltro-sd01.github.io)
echo   [2] Launch Local Fast HTTP Server (http://localhost:8000)
echo   [3] Rescan All 6 Rig Repositories and Push Updates to GitHub Pages
echo   [4] Launch LabVIEW Work Order Automator (Drawer Interface)
echo   [5] Exit
echo.
echo ====================================================================
set /p choice="Select an option (1-5): "

if "%choice%"=="1" goto live
if "%choice%"=="2" goto local
if "%choice%"=="3" goto sync
if "%choice%"=="4" goto automator
if "%choice%"=="5" goto exit

:live
echo Opening Live Dashboard...
start https://paltro-sd01.github.io
goto end

:local
echo Launching Local HTTP Server...
cd /d "D:\Projects\paltro-sd01.github.io"
start python serve.py
goto end

:sync
echo.
echo ====================================================================
echo   Scanning all 6 LabVIEW Test Rig Repositories...
echo ====================================================================
cd /d "D:\Projects\paltro-sd01.github.io"
python refresh_data.py
git add data.js
git commit -m "chore: sync latest repo commits and work orders"
git push origin main
git push origin main:gh-pages --force
echo.
echo [SUCCESS] Telemetry synchronized and published to GitHub Pages!
pause
goto end

:automator
echo Opening Automator in Browser...
start https://paltro-sd01.github.io#suite
goto end

:end
exit

:exit
exit
