@echo off
echo ========================================
echo    Consolidador Excel - Build Script
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo.

REM Install/update dependencies
echo Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt
echo.

REM Clean previous builds
echo Cleaning previous builds...
if exist "dist\" rmdir /s /q dist
if exist "build\" rmdir /s /q build
echo.

REM Build executable
echo Building executable...
pyinstaller app.spec
echo.

REM Check if build was successful
if exist "dist\ConsolidadorExcel.exe" (
    echo ========================================
    echo    BUILD SUCCESSFUL!
    echo ========================================
    echo.
    echo Executable created: dist\ConsolidadorExcel.exe
    echo.
    echo To run the application:
    echo   1. Navigate to the 'dist' folder
    echo   2. Double-click 'ConsolidadorExcel.exe'
    echo   3. The app will open in your default browser
    echo.
) else (
    echo ========================================
    echo    BUILD FAILED!
    echo ========================================
    echo Please check the error messages above.
)

echo.
echo Press any key to exit...
pause >nul