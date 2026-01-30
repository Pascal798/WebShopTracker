@echo off
setlocal

REM Build script to create a Windows executable for bot.py using PyInstaller
REM Usage: Open PowerShell or cmd as Administrator and run: build_exe.bat

if not defined VIRTUAL_ENV (
  echo Creating virtual environment in .venv...
  python -m venv .venv
)

call .venv\Scripts\activate.bat

echo Upgrading pip...
python -m pip install --upgrade pip

echo Installing requirements and PyInstaller...
pip install -r requirements.txt
pip install pyinstaller

echo Installing Playwright browsers (Chromium)...
python -m playwright install chromium

echo Running PyInstaller (one-directory build)...
pyinstaller --noconfirm --clean --onedir --console bot.py

if exist dist\bot (
  echo Copying config files to dist\bot...
  copy /Y shops_config.json dist\bot\ >nul 2>&1 || echo Could not copy shops_config.json
  copy /Y products.json dist\bot\ >nul 2>&1 || echo Could not copy products.json
  if exist .env copy /Y .env dist\bot\ >nul 2>&1
  echo Build finished. Executable is in dist\bot\bot.exe
) else (
  echo Build failed or dist\bot not found
)

endlocal
pause
