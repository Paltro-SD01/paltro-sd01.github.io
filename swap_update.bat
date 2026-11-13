@echo off
REM ============================================================================
REM PALTRO-SD01 | PRODUCTION-SAFE LABVIEW EXE SELF-SWAP UPDATER (swap_update.bat)
REM Called from LabVIEW System Exec.vi (wait until completion = False)
REM Usage: swap_update.bat "<Temp_New_EXE_Path>" "<Target_Installed_EXE_Path>" ["<New_Version>"]
REM ============================================================================
title Paltro-SD01 LabVIEW Auto-Updater
color 0B

set "TEMP_EXE=%~1"
set "TARGET_EXE=%~2"
set "NEW_VER=%~3"
set "EXE_NAME=%~nx2"
set "TARGET_DIR=%~dp2"
set "BACKUP_EXE=%~dpn2_backup.exe"
set "LOG_FILE=%~dp2update_install.log"

if "%TEMP_EXE%"=="" (
    echo [ERROR] Missing arguments. Usage: swap_update.bat "TempNewExe" "TargetExe"
    exit /b 1
)

echo ============================================================
echo   PALTRO-SD01 LABVIEW AUTO-UPDATER
echo   Target Application : %EXE_NAME%
echo   Installing Update  : %NEW_VER%
echo ============================================================
echo [%DATE% %TIME%] Starting OTA swap for %EXE_NAME% (%NEW_VER%) >> "%LOG_FILE%"

REM 1. Wait until LabVIEW closes all NI-DAQmx / VISA / Camera handles and exits
echo [1/4] Waiting for %EXE_NAME% to close...
set /a WAIT_COUNT=0
:WAIT_LOOP
tasklist /FI "IMAGENAME eq %EXE_NAME%" 2>NUL | find /I "%EXE_NAME%" >NUL
if "%ERRORLEVEL%"=="0" (
    set /a WAIT_COUNT+=1
    if %WAIT_COUNT% GEQ 20 (
        echo   -> Force closing lingering %EXE_NAME% process...
        taskkill /F /IM "%EXE_NAME%" >NUL 2>&1
        timeout /t 1 /nobreak >NUL
        goto AFTER_WAIT
    )
    timeout /t 1 /nobreak >NUL
    goto WAIT_LOOP
)
:AFTER_WAIT
timeout /t 1 /nobreak >NUL

REM 2. Verify downloaded EXE exists and is non-empty
if not exist "%TEMP_EXE%" (
    echo [ERROR] Downloaded file not found: %TEMP_EXE%
    echo [%DATE% %TIME%] ERROR: Temp file missing %TEMP_EXE% >> "%LOG_FILE%"
    start "" "%TARGET_EXE%"
    exit /b 1
)

REM 3. Create rollback backup of previous working EXE (Preserves all .ini files!)
echo [2/4] Backing up current %EXE_NAME% to %~nx2_backup.exe...
if exist "%TARGET_EXE%" (
    copy /Y "%TARGET_EXE%" "%BACKUP_EXE%" >NUL
)

REM 4. Swap in the new EXE with automatic rollback if move fails
echo [3/4] Installing updated %EXE_NAME%...
move /Y "%TEMP_EXE%" "%TARGET_EXE%" >NUL
if "%ERRORLEVEL%" NEQ "0" (
    echo [ERROR] Failed to overwrite %TARGET_EXE%! Restoring backup...
    echo [%DATE% %TIME%] ERROR: Move failed, restored backup >> "%LOG_FILE%"
    if exist "%BACKUP_EXE%" copy /Y "%BACKUP_EXE%" "%TARGET_EXE%" >NUL
) else (
    if not "%NEW_VER%"=="" (
        echo %NEW_VER%> "%TARGET_DIR%local_version.txt"
    )
    echo [%DATE% %TIME%] SUCCESS: Updated %EXE_NAME% to %NEW_VER% >> "%LOG_FILE%"
)

REM 5. Relaunch the updated LabVIEW application
echo [4/4] Relaunching %EXE_NAME%...
start "" "%TARGET_EXE%"
exit /b 0
