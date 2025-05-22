@echo off
ECHO ====================================
ECHO Demographic Simulation Tool Launcher
ECHO ====================================
ECHO.

:: Check Python installation
python --version > NUL 2>&1
IF %ERRORLEVEL% NEQ 0 (
    ECHO Python is not installed or not in PATH.
    ECHO Please install Python 3.8 or higher from https://www.python.org/downloads/
    ECHO Make sure to check "Add Python to PATH" during installation.
    ECHO.
    PAUSE
    EXIT /B 1
)

:: Create virtual environment if it doesn't exist
IF NOT EXIST venv (
    ECHO Creating virtual environment...
    python -m venv venv
)

:: Activate virtual environment
CALL venv\Scripts\activate.bat

:: Install or update dependencies
ECHO Installing required packages...
pip install -r requirements.txt

:: Check launch option
ECHO.
ECHO Please select which application to launch:
ECHO 1. Standard Web Interface
ECHO 2. Interactive Dashboard (Recommended)
ECHO 3. Download External Data
ECHO.
SET /P LAUNCH_OPTION="Enter your choice (1-3): "

IF "%LAUNCH_OPTION%"=="1" (
    ECHO.
    ECHO Launching standard web interface...
    cd web
    python -m streamlit run app.py
) ELSE IF "%LAUNCH_OPTION%"=="2" (
    ECHO.
    ECHO Launching interactive dashboard...
    cd web
    python -m streamlit run interactive_app.py
) ELSE IF "%LAUNCH_OPTION%"=="3" (
    ECHO.
    ECHO ====================================
    ECHO External Data Download
    ECHO ====================================
    ECHO.
    SET /P COUNTRY="Enter country code (default: PL): "
    IF "%COUNTRY%"=="" SET COUNTRY=PL
    
    SET /P YEAR="Enter year (default: 2022): "
    IF "%YEAR%"=="" SET YEAR=2022
    
    SET /P OUTPUT="Enter output filename (default: External_Input.xlsx): "
    IF "%OUTPUT%"=="" SET OUTPUT=External_Input.xlsx
    
    ECHO.
    ECHO Downloading data for country=%COUNTRY%, year=%YEAR%...
    python external_data_integration.py --country %COUNTRY% --year %YEAR% --output %OUTPUT%
    
    ECHO.
    ECHO Press any key to return to the main menu...
    PAUSE > NUL
    %0
) ELSE (
    ECHO Invalid option selected.
    ECHO.
    ECHO Press any key to try again...
    PAUSE > NUL
    %0
)

:: Deactivate virtual environment when app closes
CALL venv\Scripts\deactivate.bat
