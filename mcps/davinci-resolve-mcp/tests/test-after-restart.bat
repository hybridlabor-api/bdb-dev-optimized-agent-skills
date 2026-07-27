@echo off
:: Restart DaVinci Resolve MCP Server and run tests
:: This script combines server restart with automated testing

echo ========================================================
echo DaVinci Resolve MCP Server - Test After Restart
echo ========================================================

:: Change to the directory where the script is located
cd /d "%~dp0"

:: Check if DaVinci Resolve is running
tasklist | findstr "Resolve" > nul
if %ERRORLEVEL% NEQ 0 (
    echo [33m⚠️ DaVinci Resolve is not running. Please start it before continuing.[0m
    set /p continue_anyway=Start testing anyway? (y/n): 
    if /i not "%continue_anyway%"=="y" (
        echo Aborting test.
        exit /b 1
    )
    echo Continuing with testing despite DaVinci Resolve not running...
)

:: Step 1: Restart the server using the restart script
echo.
echo Step 1: Restarting DaVinci Resolve MCP Server...
if exist restart-server.bat (
    call restart-server.bat
    
    :: Check if restart was successful
    timeout /t 3 /nobreak > nul
    wmic process where "commandline like '%%python%%resolve_mcp_server.py%%'" get processid 2>nul | findstr /r "[0-9]" > nul
    if %ERRORLEVEL% EQU 0 (
        echo [32m✅ Server restart successful[0m
    ) else (
        echo [31m❌ Server restart failed. Please check server logs for errors.[0m
        exit /b 1
    )
) else (
    echo [31m❌ restart-server.bat not found. Cannot restart server.[0m
    exit /b 1
)

:: Step 2: Create test timeline (optional)
echo.
echo Step 2: Create test timeline with media?
set /p create_timeline=Create test timeline? (y/n): 
if /i "%create_timeline%"=="y" (
    echo Creating test timeline...
    if exist create_test_timeline.py (
        python create_test_timeline.py
        if %ERRORLEVEL% NEQ 0 (
            echo [33m⚠️ Test timeline creation had issues, but we'll continue with testing.[0m
        )
    ) else (
        echo [31m❌ create_test_timeline.py not found. Skipping test timeline creation.[0m
    )
) else (
    echo Skipping test timeline creation.
)

:: Step 3: Run automated tests
echo.
echo Step 3: Running automated tests...
if exist test_improvements.py (
    python test_improvements.py
    set TEST_RESULT=%ERRORLEVEL%
    if %TEST_RESULT% EQU 0 (
        echo [32m✅ All tests passed![0m
    ) else (
        echo [33m⚠️ Some tests failed. Check the logs for details.[0m
    )
) else (
    echo [31m❌ test_improvements.py not found. Cannot run tests.[0m
    exit /b 1
)

echo.
echo ========================================================
echo Testing complete. Results logged to mcp_test_results.log
echo ========================================================

exit /b %TEST_RESULT% 