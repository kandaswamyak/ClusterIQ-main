#!/bin/bash

# Azure Deployment Setup Script
# This script automates the setup of Azure resources for ClusterIQ

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}╔═══════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     ClusterIQ - Azure Deployment Setup           ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════╝${NC}"

# Check Azure CLI
if ! command -v az &> /dev/null; then
    echo -e "${RED}❌ Azure CLI not found. Please install from https://aka.ms/azure-cli${NC}"
    exit 1
fi

echo -e "${YELLOW}📋 Step 1: Login to Azure${NC}"
az login

# Get subscription
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
echo -e "${GREEN}✓ Using subscription: $SUBSCRIPTION_ID${NC}"

# Prompt for resource configuration
read -p "Enter Resource Group name (default: clusteriq-rg): " RG_NAME
RG_NAME=${RG_NAME:-clusteriq-rg}

read -p "Enter Location (default: eastus): " LOCATION
LOCATION=${LOCATION:-eastus}

read -p "Enter App Prefix (default: clusteriq): " APP_PREFIX
APP_PREFIX=${APP_PREFIX:-clusteriq}

BACKEND_APP_NAME="${APP_PREFIX}-backend-api"
FRONTEND_APP_NAME="${APP_PREFIX}-frontend"
BACKEND_PLAN="${APP_PREFIX}-backend-plan"
FRONTEND_PLAN="${APP_PREFIX}-frontend-plan"

echo -e "${YELLOW}📦 Creating Resource Group: $RG_NAME in $LOCATION${NC}"
az group create \
  --name "$RG_NAME" \
  --location "$LOCATION"
echo -e "${GREEN}✓ Resource Group created${NC}"

echo -e "${YELLOW}📦 Creating App Service Plan for Backend${NC}"
az appservice plan create \
  --name "$BACKEND_PLAN" \
  --resource-group "$RG_NAME" \
  --sku B2 \
  --is-linux
echo -e "${GREEN}✓ Backend App Service Plan created${NC}"

echo -e "${YELLOW}📦 Creating App Service Plan for Frontend${NC}"
az appservice plan create \
  --name "$FRONTEND_PLAN" \
  --resource-group "$RG_NAME" \
  --sku B2 \
  --is-linux
echo -e "${GREEN}✓ Frontend App Service Plan created${NC}"

echo -e "${YELLOW}📦 Creating Backend Web App${NC}"
az webapp create \
  --resource-group "$RG_NAME" \
  --plan "$BACKEND_PLAN" \
  --name "$BACKEND_APP_NAME" \
  --deployment-container-image-name-user clusteriq-backend
echo -e "${GREEN}✓ Backend Web App created${NC}"

echo -e "${YELLOW}📦 Creating Frontend Web App${NC}"
az webapp create \
  --resource-group "$RG_NAME" \
  --plan "$FRONTEND_PLAN" \
  --name "$FRONTEND_APP_NAME" \
  --deployment-container-image-name-user clusteriq-frontend
echo -e "${GREEN}✓ Frontend Web App created${NC}"

echo -e "${YELLOW}🔧 Configuring Backend Environment Variables${NC}"
echo "Please provide the following values:"

read -p "Databricks Host (https://...azuredatabricks.net): " DB_HOST
read -p "Databricks Token: " -s DB_TOKEN
echo

read -p "Azure OpenAI Endpoint: " AOI_ENDPOINT
read -p "Azure OpenAI API Key: " -s AOI_KEY
echo

read -p "Azure OpenAI Deployment Name: " AOI_DEPLOYMENT

az webapp config appsettings set \
  --resource-group "$RG_NAME" \
  --name "$BACKEND_APP_NAME" \
  --settings \
    DATABRICKS_HOST="$DB_HOST" \
    DATABRICKS_TOKEN="$DB_TOKEN" \
    AZURE_OPENAI_ENDPOINT="$AOI_ENDPOINT" \
    AZURE_OPENAI_API_KEY="$AOI_KEY" \
    AZURE_OPENAI_DEPLOYMENT_NAME="$AOI_DEPLOYMENT" \
    CORS_ORIGINS="https://${FRONTEND_APP_NAME}.azurewebsites.net,http://localhost:3000" \
    BACKEND_PORT="8000" \
    ENVIRONMENT="production" \
    LOG_LEVEL="INFO"

echo -e "${GREEN}✓ Backend environment variables configured${NC}"

echo -e "${YELLOW}🔧 Configuring Frontend Environment Variables${NC}"
az webapp config appsettings set \
  --resource-group "$RG_NAME" \
  --name "$FRONTEND_APP_NAME" \
  --settings \
    VITE_API_BASE_URL="https://${BACKEND_APP_NAME}.azurewebsites.net/api" \
    VITE_ENVIRONMENT="production"

echo -e "${GREEN}✓ Frontend environment variables configured${NC}"

echo -e "${YELLOW}🔐 Getting Publish Profiles${NC}"
echo ""
echo -e "${YELLOW}Backend Publish Profile (save as AZURE_BACKEND_PUBLISH_PROFILE):${NC}"
az webapp deployment publish-profile \
  --resource-group "$RG_NAME" \
  --name "$BACKEND_APP_NAME" \
  --xml

echo ""
echo -e "${YELLOW}Frontend Publish Profile (save as AZURE_FRONTEND_PUBLISH_PROFILE):${NC}"
az webapp deployment publish-profile \
  --resource-group "$RG_NAME" \
  --name "$FRONTEND_APP_NAME" \
  --xml

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║          ✓ Setup Complete!                        ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════╝${NC}"

echo ""
echo -e "${YELLOW}📝 Next Steps:${NC}"
echo "1. Add GitHub Secrets:"
echo "   - AZURE_BACKEND_APP_NAME: $BACKEND_APP_NAME"
echo "   - AZURE_BACKEND_PUBLISH_PROFILE: <paste profile above>"
echo "   - AZURE_FRONTEND_APP_NAME: $FRONTEND_APP_NAME"
echo "   - AZURE_FRONTEND_PUBLISH_PROFILE: <paste profile above>"
echo ""
echo "2. Push to main branch to trigger deployments"
echo ""
echo "3. Monitor deployments in GitHub Actions"
echo ""
echo -e "${YELLOW}🌐 After deployment, access your apps at:${NC}"
echo "   Backend: https://${BACKEND_APP_NAME}.azurewebsites.net"
echo "   Frontend: https://${FRONTEND_APP_NAME}.azurewebsites.net"
