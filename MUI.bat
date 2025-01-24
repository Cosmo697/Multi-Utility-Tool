@echo off
REM --------------------------------------------
REM Name: run_app.bat
REM Description:
REM  - Creates a Python virtual environment if not present
REM  - Activates the venv
REM  - Installs dependencies from requirements.txt
REM  - Launches the application (app.py)
REM --------------------------------------------

REM 1) Check if Python is available
where python >nul 2>nul
IF %ERRORLEVEL% NEQ 0 (
    echo "Python not found on PATH. Please install or add it to PATH."
    pause
    exit /b 1
)

REM 2) Check if venv folder exists
IF NOT EXIST "venv" (
    echo "No virtual environment found. Creating one..."
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

REM 4) Install dependencies
echo "Installing/Updating dependencies from requirements.txt..."
pip install -r requirements.txt
IF %ERRORLEVEL% NEQ 0 (
    echo "Error installing dependencies."
    pause
    exit /b 1
)

REM 5) Run the app
echo "Launching the application..."
python app.py
echo "App finished with code %ERRORLEVEL%."
pause

REM Optional: Deactivate the environment after use
echo "Application finished. Deactivating virtual environment."
deactivate

pause
