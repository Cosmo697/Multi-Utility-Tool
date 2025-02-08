@echo off
REM --------------------------------------------
REM Name: run_app.bat
REM Description:
REM  - Creates a Python virtual environment if not present
REM  - Activates the venv
REM  - Installs dependencies from requirements.txt
REM  - Launches the application (app.py)
REM --------------------------------------------

REM 1) Check for Python installation
python --version
IF %ERRORLEVEL% NEQ 0 (
    echo "Python is not installed or not added to PATH."
    pause
    exit /b 1
)

REM 2) Create virtual environment if it doesn't exist
IF NOT EXIST "venv" (
    python -m venv venv
    IF %ERRORLEVEL% NEQ 0 (
        echo "Error creating virtual environment."
        pause
        exit /b 1
    )
)

REM 3) Activate the virtual environment
CALL ".\venv\Scripts\activate.bat"
IF %ERRORLEVEL% NEQ 0 (
    echo "Error activating virtual environment."
    pause
    exit /b 1
)

REM 4) Check if requirements.txt exists
IF NOT EXIST "requirements.txt" (
    echo "requirements.txt not found."
    pause
    exit /b 1
)

REM 5) Install dependencies
echo "Installing/Updating dependencies from requirements.txt..."
pip install -r requirements.txt
IF %ERRORLEVEL% NEQ 0 (
    echo "Error installing dependencies."
    pause
    exit /b 1
)

REM 6) Run the app
echo "Launching the application..."
python app.py
IF %ERRORLEVEL% NEQ 0 (
    echo "Application encountered an error."
    pause
    exit /b 1
)
echo "App finished with code %ERRORLEVEL%."
pause

REM 7) Deactivate the virtual environment
IF DEFINED VIRTUAL_ENV (
    echo "Deactivating virtual environment."
    deactivate
)

pause
