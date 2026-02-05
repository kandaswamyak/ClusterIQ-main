# ✅ Azure Deployment - Infrastructure Created

## 🎉 Successfully Created Resources

### App Service Plans
- ✅ **Backend Plan**: `clusteriq-backend-plan` (B2, Linux) - eastus
- ✅ **Frontend Plan**: `clusteriq-frontend-plan` (B2, Linux) - eastus

### Web Apps
- ✅ **Backend API**: `clusteriq-backend-api`
  - URL: https://clusteriq-backend-api.azurewebsites.net
  - Status: Running
  
- ✅ **Frontend**: `clusteriq`
  - URL: https://clusteriq-c5g9ezftdpdsgwf7.eastus-01.azurewebsites.net
  - Status: Running

### Resource Group
- Name: `ClusterIQ_OpenAI`
- Location: `eastus`

---

## 📋 Next Steps

### Step 1: Add GitHub Secrets (REQUIRED)

Go to your GitHub repository: https://github.com/YOUR_USERNAME/ClusterIQ-main

1. Navigate to: **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

2. Add these 4 secrets:

   **Secret 1:**
   - Name: `AZURE_BACKEND_APP_NAME`
   - Value: `clusteriq-backend-api`

   **Secret 2:**
   - Name: `AZURE_BACKEND_PUBLISH_PROFILE`
   - Value: Copy entire content from `scripts/backend-publish-profile.xml`

   **Secret 3:**
   - Name: `AZURE_FRONTEND_APP_NAME`
   - Value: `clusteriq`

   **Secret 4:**
   - Name: `AZURE_FRONTEND_PUBLISH_PROFILE`
   - Value: Copy entire content from `scripts/frontend-publish-profile.xml`

### Step 2: Configure Azure Environment Variables

#### Backend Environment Variables
Go to Azure Portal → Web Apps → `clusteriq-backend-api` → Configuration → Application settings

Add these settings:

```
DATABRICKS_HOST=your_databricks_host
DATABRICKS_TOKEN=your_databricks_token
AZURE_OPENAI_ENDPOINT=your_azure_openai_endpoint
AZURE_OPENAI_API_KEY=your_azure_openai_api_key
AZURE_OPENAI_DEPLOYMENT_NAME=your_deployment_name
CORS_ORIGINS=https://clusteriq-c5g9ezftdpdsgwf7.eastus-01.azurewebsites.net
DELTA_CLUSTER_EVENTS_TABLE=your_cluster_events_table
DELTA_CLUSTER_LOGS_TABLE=your_cluster_logs_table
DELTA_JOB_RUN_LOGS_TABLE=your_job_run_logs_table
BACKEND_PORT=8000
ENVIRONMENT=production
```

Click **Save** after adding all settings.

#### Frontend Environment Variables
Go to Azure Portal → Web Apps → `clusteriq` → Configuration → Application settings

Add these settings:

```
VITE_API_BASE_URL=https://clusteriq-backend-api.azurewebsites.net/api
VITE_ENVIRONMENT=production
```

Click **Save** after adding all settings.

### Step 3: Update GitHub Actions Workflows

The workflows are already created. You need to update the container registry username:

1. Open `.github/workflows/deploy-backend.yml`
2. Replace `yourusername` with your actual GitHub username

3. Open `.github/workflows/deploy-frontend.yml`
4. Replace `yourusername` with your actual GitHub username

### Step 4: Push to GitHub (Triggers Deployment)

```powershell
cd C:\Users\akandaswamy4\Documents\GitHub\ClusterIQ-main
git add .
git commit -m "Add Azure deployment configuration"
git push origin main
```

This will automatically:
- Build Docker images
- Push to GitHub Container Registry
- Deploy to Azure Web Apps

---

## 🔍 Monitoring Deployment

### Check GitHub Actions
- Go to: https://github.com/YOUR_USERNAME/ClusterIQ-main/actions
- You should see two workflows running:
  - "Deploy Backend to Azure"
  - "Deploy Frontend to Azure"

### Check Azure Deployment
- Backend: https://clusteriq-backend-api.azurewebsites.net/health
- Frontend: https://clusteriq-c5g9ezftdpdsgwf7.eastus-01.azurewebsites.net

### View Logs
```powershell
# Backend logs
az webapp log tail --name clusteriq-backend-api --resource-group ClusterIQ_OpenAI

# Frontend logs
az webapp log tail --name clusteriq --resource-group ClusterIQ_OpenAI
```

---

## 📁 Files Location

- Publish Profiles: `scripts/backend-publish-profile.xml`, `scripts/frontend-publish-profile.xml`
- Docker Files: `backend/Dockerfile`, `frontend/Dockerfile`
- GitHub Actions: `.github/workflows/deploy-backend.yml`, `.github/workflows/deploy-frontend.yml`

---

## ⚠️ Important Notes

1. **First Deployment**: May take 5-10 minutes as Docker images are built
2. **Environment Variables**: Backend won't work until you add Databricks and Azure OpenAI credentials
3. **CORS**: Backend CORS_ORIGINS must include frontend URL
4. **Health Check**: Backend has `/health` endpoint for monitoring
5. **Container Registry**: Using GitHub Container Registry (GHCR) - free and integrated

---

## 🆘 Troubleshooting

### If deployment fails:
1. Check GitHub Actions logs for build errors
2. Verify GitHub secrets are added correctly
3. Ensure Azure environment variables are configured
4. Check Azure Web App logs using `az webapp log tail`

### If backend returns errors:
1. Verify Databricks credentials in Azure Portal
2. Check Azure OpenAI credentials
3. Verify Delta table names are correct
4. Check CORS_ORIGINS includes frontend URL

### If frontend can't connect to backend:
1. Verify VITE_API_BASE_URL in frontend settings
2. Check backend CORS_ORIGINS includes frontend URL
3. Test backend health: https://clusteriq-backend-api.azurewebsites.net/health

---

## 📚 Additional Documentation

- [AZURE_QUICK_START.md](AZURE_QUICK_START.md) - 5-step quick start guide
- [AZURE_DEPLOYMENT.md](AZURE_DEPLOYMENT.md) - Complete deployment reference
- [AZURE_ARCHITECTURE.md](AZURE_ARCHITECTURE.md) - Architecture diagrams
- [DEPLOYMENT_README.md](DEPLOYMENT_README.md) - Documentation index

---

## ✅ Checklist

- [ ] Add 4 GitHub secrets
- [ ] Configure backend environment variables (11 settings)
- [ ] Configure frontend environment variables (2 settings)
- [ ] Update GitHub username in workflow files
- [ ] Push code to GitHub
- [ ] Monitor GitHub Actions deployment
- [ ] Test backend health endpoint
- [ ] Test frontend URL
- [ ] Verify backend logs
- [ ] Verify frontend logs

**Ready to deploy! Follow the steps above.** 🚀
