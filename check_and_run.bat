@echo off
echo ========================================
echo Multi-Node Parallel File Server
echo ========================================
echo.

REM Check for Python
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    where py >nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Python is not installed or not in PATH
        echo.
        echo Please install Python 3.7+ from: https://www.python.org/downloads/
        echo Make sure to check "Add Python to PATH" during installation
        echo.
        echo Alternatively, you can use the Python server by running:
        echo   python server/server.py
        echo.
        pause
        exit /b 1
    ) else (
        set PYTHON_CMD=py
    )
) else (
    set PYTHON_CMD=python
)

echo [OK] Python found
echo.

REM Check for PyQt5
%PYTHON_CMD% -c "import PyQt5" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] PyQt5 not found. Installing...
    %PYTHON_CMD% -m pip install PyQt5
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to install PyQt5
        pause
        exit /b 1
    )
)

echo [OK] PyQt5 installed
echo.
echo ========================================
echo Starting Server...
echo ========================================
echo.
echo Server will run on port 8080
echo Press Ctrl+C to stop the server
echo.
echo In another terminal, run: python client/gui_client.py
echo.
%PYTHON_CMD% server/server.py 8080 server_files

