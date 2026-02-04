# Azure Deployment Checklist

## Pre-Deployment ✓

- [ ] Azure subscription active and accessible
- [ ] GitHub repository set up with main branch
- [ ] GitHub Actions enabled in repository settings
- [ ] Azure CLI installed on your machine
- [ ] Docker installed (for local testing)

## Step 1: Run Setup Script ✓

- [ ] Navigate to `scripts/` directory
- [ ] Run `azure-deploy.sh` (Linux/Mac) or `azure-deploy.bat` (Windows)
- [ ] Complete all prompts (resource group, location, app prefix)
- [ ] Resource group created: _______________
- [ ] Backend app name: _______________
- [ ] Frontend app name: _______________

## Step 2: Save Publish Profiles ✓

- [ ] Copy **Backend Publish Profile** (full XML)
- [ ] Copy **Frontend Publish Profile** (full XML)
- [ ] Save both profiles securely

## Step 3: Add GitHub Secrets ✓

Go to: GitHub → Repository → Settings → Secrets and variables → Actions

Add these secrets:

- [ ] `AZURE_BACKEND_APP_NAME`
  - Value: `clusteriq-backend-api` (or your custom name)

- [ ] `AZURE_BACKEND_PUBLISH_PROFILE`
  - Value: (Full XML from script)

- [ ] `AZURE_FRONTEND_APP_NAME`
  - Value: `clusteriq-frontend` (or your custom name)

- [ ] `AZURE_FRONTEND_PUBLISH_PROFILE`
  - Value: (Full XML from script)

## Step 4: Configure Backend Environment Variables ✓

Go to: Azure Portal → Backend Web App → Configuration → Application settings

Add these settings:

- [ ] `DATABRICKS_HOST`
  - Value: `https://your-workspace.azuredatabricks.net`

- [ ] `DATABRICKS_TOKEN`
  - Value: (Your Databricks token)

- [ ] `AZURE_OPENAI_ENDPOINT`
  - Value: `https://your-resource.openai.azure.com`

- [ ] `AZURE_OPENAI_API_KEY`
  - Value: (Your API key)

- [ ] `AZURE_OPENAI_DEPLOYMENT_NAME`
  - Value: (Your deployment name, e.g., ClusterIQGPT)

- [ ] `CORS_ORIGINS`
  - Value: `https://your-frontend-app.azurewebsites.net,http://localhost:3000`

- [ ] `DELTA_CLUSTER_EVENTS_TABLE`
  - Value: `default.cluster_events`

- [ ] `DELTA_CLUSTER_LOGS_TABLE`
  - Value: `default.cluster_logs`

- [ ] `DELTA_JOB_RUN_LOGS_TABLE`
  - Value: `default.job_run_logs`

- [ ] `BACKEND_PORT`
  - Value: `8000`

- [ ] `ENVIRONMENT`
  - Value: `production`

- [ ] `LOG_LEVEL`
  - Value: `INFO`

After adding all settings, click **Save**

## Step 5: Configure Frontend Environment Variables ✓

Go to: Azure Portal → Frontend Web App → Configuration → Application settings

Add these settings:

- [ ] `VITE_API_BASE_URL`
  - Value: `https://your-backend-app.azurewebsites.net/api`

- [ ] `VITE_ENVIRONMENT`
  - Value: `production`

After adding settings, click **Save**

## Step 6: Verify Local Build ✓

Test Docker images locally before deploying:

```bash
# Test backend
cd backend
docker build -t clusteriq-backend .
docker run -p 8000:8000 -e DATABRICKS_HOST="..." clusteriq-backend

# Test frontend
cd frontend
docker build -t clusteriq-frontend .
docker run -p 3000:3000 clusteriq-frontend
```

- [ ] Backend builds successfully
- [ ] Frontend builds successfully
- [ ] Both containers run without errors

## Step 7: Deploy ✓

1. Commit your changes:
   ```bash
   git add .
   git commit -m "Configure Azure deployment"
   git push origin main
   ```

2. GitHub Actions automatically starts:
   - [ ] Backend workflow triggered
   - [ ] Frontend workflow triggered

3. Monitor deployments:
   - [ ] Go to GitHub → Actions
   - [ ] Watch workflow progress
   - [ ] Both workflows complete successfully

## Step 8: Verify Deployment ✓

After deployment completes:

- [ ] Backend health check:
  ```bash
  curl https://your-backend-app.azurewebsites.net/health
  ```

- [ ] Frontend loads:
  ```bash
  curl https://your-frontend-app.azurewebsites.net
  ```

- [ ] Check Azure Web App logs:
  ```bash
  az webapp log tail --name your-backend-app --resource-group your-rg
  az webapp log tail --name your-frontend-app --resource-group your-rg
  ```

- [ ] Test in browser: `https://your-frontend-app.azurewebsites.net`

## Step 9: Monitor & Maintain ✓

- [ ] Set up log monitoring (Azure Portal or CLI)
- [ ] Enable Application Insights for monitoring
- [ ] Configure alerts for errors
- [ ] Schedule regular backups
- [ ] Review costs monthly
- [ ] Test failover scenarios
- [ ] Document any custom configurations

## Troubleshooting ✓

If deployment fails, check:

- [ ] GitHub Actions logs for error messages
- [ ] Azure Web App logs: `az webapp log tail`
- [ ] Publish profiles are valid XML
- [ ] Environment variables are correct
- [ ] CORS settings allow frontend URL
- [ ] Images can be pulled from GitHub Container Registry

### Common Issues:

**"Unable to connect to remote server"**
- [ ] Verify publish profile
- [ ] Check GitHub secret values

**"Application failed to start"**
- [ ] Check environment variables
- [ ] Review application logs
- [ ] Test Docker image locally

**"CORS error in frontend"**
- [ ] Update CORS_ORIGINS to include frontend URL
- [ ] Restart backend app after changing settings

**"Can't pull container image"**
- [ ] Verify GitHub token has package permissions
- [ ] Check image name matches workflow configuration

## Post-Deployment Tasks ✓

- [ ] Document deployment URLs
- [ ] Set up monitoring and alerts
- [ ] Configure auto-scaling if needed
- [ ] Enable HTTPS redirect
- [ ] Review security settings
- [ ] Test all application features
- [ ] Inform team of deployment
- [ ] Create incident response plan

## Emergency Procedures ✓

- [ ] Know how to rollback: redeploy previous git tag
- [ ] Have backup of environment variables
- [ ] Know Azure support contacts
- [ ] Have disaster recovery plan
- [ ] Test restore procedures

---

**Deployment Date:** _______________
**Deployed By:** _______________
**Notes:** 

