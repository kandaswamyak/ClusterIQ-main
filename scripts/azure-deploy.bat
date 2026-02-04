@echo off
REM Azure Deployment Setup Script (Windows)
REM This script automates the setup of Azure resources for ClusterIQ

setlocal enabledelayedexpansion

echo.
echo ======================================================
echo     ClusterIQ - Azure Deployment Setup
echo ======================================================
echo.

REM Check Azure CLI
az --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Azure CLI not found. Please install from https://aka.ms/azure-cli
    pause
    exit /b 1
)

echo Step 1: Login to Azure
az login
if errorlevel 1 (
    echo ERROR: Azure login failed
    pause
    exit /b 1
)

REM Get subscription
for /f "tokens=*" %%i in ('az account show --query id -o tsv') do set SUBSCRIPTION_ID=%%i
echo Using subscription: !SUBSCRIPTION_ID!
echo.

REM Prompt for resource configuration
set RG_NAME=clusteriq-rg
set /p "RG_NAME=Enter Resource Group name [%RG_NAME%]: "

set LOCATION=eastus
set /p "LOCATION=Enter Location [%LOCATION%]: "

set APP_PREFIX=clusteriq
set /p "APP_PREFIX=Enter App Prefix [%APP_PREFIX%]: "

set BACKEND_APP_NAME=!APP_PREFIX!-backend-api
set FRONTEND_APP_NAME=!APP_PREFIX!-frontend
set BACKEND_PLAN=!APP_PREFIX!-backend-plan
set FRONTEND_PLAN=!APP_PREFIX!-frontend-plan

echo.
echo Creating Resource Group: !RG_NAME! in !LOCATION!
call az group create --name !RG_NAME! --location !LOCATION!
echo.

echo Creating Backend App Service Plan...
call az appservice plan create ^
  --name !BACKEND_PLAN! ^
  --resource-group !RG_NAME! ^
  --sku B2 ^
  --is-linux
echo.

echo Creating Frontend App Service Plan...
call az appservice plan create ^
  --name !FRONTEND_PLAN! ^
  --resource-group !RG_NAME! ^
  --sku B2 ^
  --is-linux
echo.

echo Creating Backend Web App...
call az webapp create ^
  --resource-group !RG_NAME! ^
  --plan !BACKEND_PLAN! ^
  --name !BACKEND_APP_NAME! ^
  --deployment-container-image-name-user clusteriq-backend
echo.

echo Creating Frontend Web App...
call az webapp create ^
  --resource-group !RG_NAME! ^
  --plan !FRONTEND_PLAN! ^
  --name !FRONTEND_APP_NAME! ^
  --deployment-container-image-name-user clusteriq-frontend
echo.

echo.
echo ======================================================
echo          Setup Complete!
echo ======================================================
echo.
echo Next Steps:
echo 1. Add GitHub Secrets:
echo    - AZURE_BACKEND_APP_NAME: !BACKEND_APP_NAME!
echo    - AZURE_BACKEND_PUBLISH_PROFILE: (get from portal)
echo    - AZURE_FRONTEND_APP_NAME: !FRONTEND_APP_NAME!
echo    - AZURE_FRONTEND_PUBLISH_PROFILE: (get from portal)
echo.
echo 2. Run Azure portal to get publish profiles:
echo    Backend: https://portal.azure.com/#resource/subscriptions/!SUBSCRIPTION_ID!/resourceGroups/!RG_NAME!/providers/Microsoft.Web/sites/!BACKEND_APP_NAME!
echo.
echo 3. Configure environment variables in Azure Portal
echo.
echo 4. Push to main branch to trigger deployments
echo.

pause
