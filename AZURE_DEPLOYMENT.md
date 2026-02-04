# Azure Web App Deployment Guide

## Overview
This project deploys a React frontend and Flask backend as separate Azure Web App services using Docker containers and GitHub Actions.

## Prerequisites

1. **Azure Subscription** - Active Azure account
2. **GitHub Account** - Repository with GitHub Actions enabled
3. **Azure CLI** - Install from https://docs.microsoft.com/cli/azure/install-azure-cli
4. **Docker** (for local testing) - https://www.docker.com/products/docker-desktop

## Architecture

```
GitHub Repository
    ├── Frontend (React + Vite)
    │   └── Deployed to Azure Web App (Linux)
    └── Backend (Python Flask)
        └── Deployed to Azure Web App (Linux)
```

## Step 1: Create Azure Resources

### 1.1 Create Resource Group
```bash
az group create --name clusteriq-rg --location eastus
```

### 1.2 Create App Service Plans (Linux)
```bash
# Backend App Service Plan
az appservice plan create \
  --name clusteriq-backend-plan \
  --resource-group clusteriq-rg \
  --sku B2 \
  --is-linux

# Frontend App Service Plan
az appservice plan create \
  --name clusteriq-frontend-plan \
  --resource-group clusteriq-rg \
  --sku B2 \
  --is-linux
```

### 1.3 Create Web Apps
```bash
# Backend Web App
az webapp create \
  --resource-group clusteriq-rg \
  --plan clusteriq-backend-plan \
  --name clusteriq-backend-api \
  --deployment-container-image-name-user clusteriq-backend

# Frontend Web App
az webapp create \
  --resource-group clusteriq-rg \
  --plan clusteriq-frontend-plan \
  --name clusteriq-frontend \
  --deployment-container-image-name-user clusteriq-frontend
```

## Step 2: Configure GitHub Secrets

Add these secrets to your GitHub repository (Settings > Secrets and Variables > Actions):

### Backend Secrets
```
AZURE_BACKEND_APP_NAME: clusteriq-backend-api
AZURE_BACKEND_PUBLISH_PROFILE: <download from Azure Portal>
```

### Frontend Secrets
```
AZURE_FRONTEND_APP_NAME: clusteriq-frontend
AZURE_FRONTEND_PUBLISH_PROFILE: <download from Azure Portal>
```

### How to get Publish Profile:
1. Go to Azure Portal > Web App > Download publish profile
2. Copy the entire XML content
3. Add as GitHub secret

## Step 3: Configure Environment Variables in Azure

### Backend Environment Variables (in Azure Portal)

Go to **Web App > Configuration > Application Settings** and add:

```
DATABRICKS_HOST: https://your-workspace.azuredatabricks.net
DATABRICKS_TOKEN: your-token
AZURE_OPENAI_ENDPOINT: https://your-resource.openai.azure.com
AZURE_OPENAI_API_KEY: your-api-key
AZURE_OPENAI_DEPLOYMENT_NAME: your-deployment
BACKEND_PORT: 8000
CORS_ORIGINS: https://clusteriq-frontend.azurewebsites.net
DELTA_CLUSTER_EVENTS_TABLE: default.cluster_events
DELTA_CLUSTER_LOGS_TABLE: default.cluster_logs
DELTA_JOB_RUN_LOGS_TABLE: default.job_run_logs
ENVIRONMENT: production
LOG_LEVEL: INFO
```

### Frontend Environment Variables (in Azure Portal)

Go to **Web App > Configuration > Application Settings** and add:

```
VITE_API_BASE_URL: https://clusteriq-backend-api.azurewebsites.net/api
VITE_ENVIRONMENT: production
```

## Step 4: Configure CORS on Backend

Update `backend/main.py` CORS configuration:

```python
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "https://clusteriq-frontend.azurewebsites.net",
            "http://localhost:3000",  # Local development
            "http://localhost:5173"   # Local Vite dev
        ],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})
```

## Step 5: Deploy

### Automatic Deployment (GitHub Actions)
1. Push code to `main` branch
2. GitHub Actions workflows automatically trigger
3. Docker images are built and pushed to GitHub Container Registry
4. Deployed to Azure Web Apps

### Manual Deployment (if needed)
```bash
# Build and push Docker images
docker build -t clusteriq-backend backend/
docker build -t clusteriq-frontend frontend/

# Deploy using Azure CLI
az webapp up --name clusteriq-backend-api --resource-group clusteriq-rg
az webapp up --name clusteriq-frontend --resource-group clusteriq-rg
```

## Step 6: Verify Deployment

### Test Backend
```bash
curl https://clusteriq-backend-api.azurewebsites.net/health
```

### Test Frontend
```bash
curl https://clusteriq-frontend.azurewebsites.net
```

## Monitoring & Logs

### View Logs
```bash
# Backend logs
az webapp log tail --name clusteriq-backend-api --resource-group clusteriq-rg

# Frontend logs
az webapp log tail --name clusteriq-frontend --resource-group clusteriq-rg
```

### Enable Application Insights
```bash
az monitor app-insights component create \
  --app clusteriq-insights \
  --location eastus \
  --resource-group clusteriq-rg
```

## Troubleshooting

### 1. Deployment Fails
- Check GitHub Actions workflow logs
- Verify Azure credentials in secrets
- Ensure Docker images build successfully locally

### 2. Application Won't Start
- Check Azure Web App logs: `az webapp log tail`
- Verify environment variables are set correctly
- Check CORS configuration

### 3. Frontend Can't Connect to Backend
- Verify CORS_ORIGINS in backend settings
- Check VITE_API_BASE_URL in frontend settings
- Ensure both apps are running

### 4. Container Registry Issues
- Verify GitHub token permissions
- Check container image names match configuration
- Ensure registry is accessible

## Security Best Practices

1. **Never commit .env files** - Use .env.example instead
2. **Use Azure Key Vault** for secrets:
   ```bash
   az keyvault create --name clusteriq-kv --resource-group clusteriq-rg
   ```

3. **Enable HTTPS only** - Go to Web App > TLS/SSL settings
4. **Configure firewall** - Restrict access if needed
5. **Use Managed Identity** - Reduces credential management

## Scaling

### Increase App Service Tier
```bash
az appservice plan update --name clusteriq-backend-plan \
  --resource-group clusteriq-rg \
  --sku S1
```

### Enable Auto-Scale
Configure in Azure Portal > Web App > Scale up/out settings

## Costs

Estimate costs:
- **App Service Plan B2**: ~$55/month per app
- **Storage**: Minimal (Docker images in registry)
- **Data Transfer**: Variable based on usage

Total estimated: ~$110/month for both apps

## Support

For issues:
1. Check GitHub Actions logs
2. Review Azure Web App logs
3. Verify environment variables
4. Test locally with Docker
