@echo off
REM Quick start script for Delta Table Analysis

echo ========================================
echo Delta Table Analysis - Quick Start
echo ========================================
echo.

REM Check if we're in the right directory
if not exist "backend\test_delta_table.py" (
    echo Error: Please run this script from the ClusterIQ root directory
    echo Current directory: %CD%
    pause
    exit /b 1
)

echo Starting interactive Delta Table analysis tool...
echo.
echo This will help you:
echo   1. Read your Delta table from Databricks
echo   2. Generate AI-powered insights
echo   3. Get cost optimization recommendations
echo.

cd backend
python test_delta_table.py

cd ..
echo.
echo ========================================
pause
