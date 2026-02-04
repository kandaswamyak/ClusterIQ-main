# Azure Deployment Quick Start

## 📋 Deployment Overview

Your ClusterIQ project has been configured for Azure Web App deployment with:
- ✅ Docker containerization (both frontend and backend)
- ✅ GitHub Actions CI/CD pipelines
- ✅ Environment-specific configurations
- ✅ Health checks and monitoring

## 🚀 Quick Start (5 steps)

### Step 1: Run Azure Setup Script

**Windows:**
```cmd
cd scripts
azure-deploy.bat
```

**Linux/Mac:**
```bash
chmod +x scripts/azure-deploy.sh
./scripts/azure-deploy.sh
```

This script will:
- Create Azure resource group
- Create App Service plans
- Create web apps
- Generate publish profiles

### Step 2: Save Publish Profiles

When the script completes, you'll get two XML blocks:
1. **Backend Publish Profile** → Save as GitHub secret `AZURE_BACKEND_PUBLISH_PROFILE`
2. **Frontend Publish Profile** → Save as GitHub secret `AZURE_FRONTEND_PUBLISH_PROFILE`

### Step 3: Add GitHub Secrets

Go to GitHub repository → Settings → Secrets and variables → Actions

Add these 4 secrets:
```
AZURE_BACKEND_APP_NAME = clusteriq-backend-api (from script output)
AZURE_BACKEND_PUBLISH_PROFILE = (XML from script)
AZURE_FRONTEND_APP_NAME = clusteriq-frontend (from script output)
AZURE_FRONTEND_PUBLISH_PROFILE = (XML from script)
```

### Step 4: Configure Azure Environment Variables

In Azure Portal for each app:

**Backend App → Configuration → Application Settings:**
```
DATABRICKS_HOST
DATABRICKS_TOKEN
AZURE_OPENAI_ENDPOINT
AZURE_OPENAI_API_KEY
AZURE_OPENAI_DEPLOYMENT_NAME
CORS_ORIGINS (set to frontend URL)
DELTA_CLUSTER_EVENTS_TABLE
DELTA_CLUSTER_LOGS_TABLE
DELTA_JOB_RUN_LOGS_TABLE
```

**Frontend App → Configuration → Application Settings:**
```
VITE_API_BASE_URL (set to backend URL)
VITE_ENVIRONMENT = production
```

### Step 5: Deploy

Push to main branch:
```bash
git add .
git commit -m "Deploy to Azure"
git push origin main
```

GitHub Actions will automatically:
1. Build Docker images
2. Push to container registry
3. Deploy to Azure Web Apps

## 📁 New Files Created

```
.github/workflows/
├── deploy-backend.yml       # Backend CI/CD pipeline
└── deploy-frontend.yml      # Frontend CI/CD pipeline

backend/
├── Dockerfile               # Backend container config
├── .dockerignore            # Exclude files from container
└── .env.example             # Example environment vars

frontend/
├── Dockerfile               # Frontend container config
├── .dockerignore            # Exclude files from container
└── .env.example             # Example environment vars

scripts/
├── azure-deploy.sh          # Linux/Mac setup script
└── azure-deploy.bat         # Windows setup script

AZURE_DEPLOYMENT.md          # Detailed deployment guide
```

## 🔍 Verify Deployment

Once deployed, test your apps:

```bash
# Test backend health
curl https://clusteriq-backend-api.azurewebsites.net/health

# Test frontend
curl https://clusteriq-frontend.azurewebsites.net
```

## 📊 Monitor Logs

```bash
# View real-time logs
az webapp log tail \
  --name clusteriq-backend-api \
  --resource-group clusteriq-rg

az webapp log tail \
  --name clusteriq-frontend \
  --resource-group clusteriq-rg
```

## 🔐 Security Notes

1. **Never commit .env files** - Use .env.example
2. **Use Azure Key Vault** for secrets (recommended)
3. **Enable HTTPS only** in Web App settings
4. **Review CORS settings** for your domain

## 💰 Cost Estimation

- **App Service Plan B2** (each): ~$55/month
- **Total for both apps**: ~$110/month
- **Storage**: Minimal
- **Data transfer**: Variable

## ❓ Troubleshooting

### Deployment fails in GitHub Actions
1. Check workflow logs in GitHub
2. Verify publish profile is correct
3. Ensure app names match in secrets

### App won't start
1. Check Azure Web App logs
2. Verify environment variables
3. Test Docker image locally:
   ```bash
   docker build -t test-backend backend/
   docker run -p 8000:8000 test-backend
   ```

### Frontend can't reach backend
1. Check CORS_ORIGINS in backend
2. Verify VITE_API_BASE_URL in frontend
3. Ensure both apps are running

## 📚 Additional Resources

- Full guide: See `AZURE_DEPLOYMENT.md`
- Azure CLI docs: https://docs.microsoft.com/cli/azure/
- GitHub Actions docs: https://docs.github.com/actions
- Docker docs: https://docs.docker.com/

## 🎯 Next Steps

1. ✅ Run setup script
2. ✅ Add GitHub secrets
3. ✅ Configure environment variables
4. ✅ Push to main branch
5. ✅ Monitor deployment
6. ✅ Access deployed apps
