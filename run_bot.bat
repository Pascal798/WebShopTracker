@echo off
REM Runs the compiled bot executable from the dist folder
REM Usage: run_bot.bat [path_to_dist_folder]

set DIST_DIR=%~1
if "%DIST_DIR%"=="" set DIST_DIR=dist\bot

if exist "%DIST_DIR%\bot.exe" (
  echo Starting bot from %DIST_DIR%...
  pushd "%DIST_DIR%"
  start "" "%DIST_DIR%\bot.exe"
  popd
) else (
  echo Executable not found in %DIST_DIR%.
  echo Use build_exe.bat to build the executable first.
)
