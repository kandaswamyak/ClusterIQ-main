# 🚀 Azure Deployment Complete - Start Here!

## ✅ Setup Status: COMPLETE

Your ClusterIQ project is fully configured for Azure Web App deployment!

---

## 📚 Documentation Index

**Start with one of these:**

### 🟢 **Quickest Path (30 minutes)**
→ **[AZURE_QUICK_START.md](AZURE_QUICK_START.md)** - 5-step deployment guide

### 🟡 **Detailed Checklist**
→ **[AZURE_DEPLOYMENT_CHECKLIST.md](AZURE_DEPLOYMENT_CHECKLIST.md)** - Step-by-step with checkboxes

### 🔵 **Complete Reference**
→ **[AZURE_DEPLOYMENT.md](AZURE_DEPLOYMENT.md)** - Full technical documentation

### 🟣 **Architecture Overview**
→ **[AZURE_ARCHITECTURE.md](AZURE_ARCHITECTURE.md)** - System diagrams and flows

### 🟠 **Setup Summary**
→ **[AZURE_SETUP_COMPLETE.md](AZURE_SETUP_COMPLETE.md)** - What was configured

---

## 📋 What You Need to Do Now

### 1️⃣ **Run the Setup Script** (5 min)
Creates Azure resources automatically:

```bash
# Windows
cd scripts && azure-deploy.bat

# Linux/Mac  
chmod +x scripts/azure-deploy.sh && ./scripts/azure-deploy.sh
```

**Output:** Publish profiles (save these!)

### 2️⃣ **Add GitHub Secrets** (5 min)
Go to: GitHub → Settings → Secrets and variables → Actions

```
AZURE_BACKEND_APP_NAME
AZURE_BACKEND_PUBLISH_PROFILE
AZURE_FRONTEND_APP_NAME
AZURE_FRONTEND_PUBLISH_PROFILE
```

### 3️⃣ **Configure Azure Environment Variables** (10 min)
In Azure Portal for each app:

**Backend settings:**
- DATABRICKS_HOST, TOKEN
- AZURE_OPENAI_*, API_KEY
- CORS_ORIGINS
- Delta table names

**Frontend settings:**
- VITE_API_BASE_URL
- VITE_ENVIRONMENT

### 4️⃣ **Deploy** (Automatic - 5 min)
```bash
git push origin main
```

GitHub Actions runs automatically → App deployed!

### 5️⃣ **Verify** (2 min)
```bash
curl https://your-backend-app.azurewebsites.net/health
```
Open: `https://your-frontend-app.azurewebsites.net`

---

## 📂 New Files Added

```
✅ Dockerfiles
  ├── backend/Dockerfile
  ├── backend/.dockerignore
  └── frontend/Dockerfile
  └── frontend/.dockerignore

✅ GitHub Actions
  └── .github/workflows/
      ├── deploy-backend.yml
      └── deploy-frontend.yml

✅ Scripts
  └── scripts/
      ├── azure-deploy.sh (Linux/Mac)
      └── azure-deploy.bat (Windows)

✅ Configuration Templates
  ├── backend/.env.example
  └── frontend/.env.example

✅ Documentation
  ├── AZURE_SETUP_COMPLETE.md (this folder)
  ├── AZURE_QUICK_START.md
  ├── AZURE_DEPLOYMENT.md
  ├── AZURE_ARCHITECTURE.md
  ├── AZURE_DEPLOYMENT_CHECKLIST.md
  └── DEPLOYMENT_README.md (this file)
```

---

## 🎯 Recommended Reading Order

```
1. This file (overview)
   ↓
2. AZURE_QUICK_START.md (execute steps)
   ↓
3. AZURE_DEPLOYMENT_CHECKLIST.md (follow checklist)
   ↓
4. AZURE_ARCHITECTURE.md (understand system)
   ↓
5. AZURE_DEPLOYMENT.md (reference when needed)
```

---

## ⚡ Quick Commands

```bash
# View Azure logs in real-time
az webapp log tail --name clusteriq-backend-api --resource-group clusteriq-rg

# Get app status
az webapp show --name clusteriq-backend-api --resource-group clusteriq-rg

# List deployed apps
az webapp list --resource-group clusteriq-rg

# Test locally before deploying
docker build -t test-backend backend/
docker run -p 8000:8000 test-backend
```

---

## 🔑 Key Files for Deployment

| File | Purpose | Action |
|------|---------|--------|
| `.github/workflows/deploy-backend.yml` | CI/CD pipeline for backend | Auto-runs on push |
| `.github/workflows/deploy-frontend.yml` | CI/CD pipeline for frontend | Auto-runs on push |
| `backend/Dockerfile` | Container config for backend | Builds image automatically |
| `frontend/Dockerfile` | Container config for frontend | Builds image automatically |
| `scripts/azure-deploy.sh` | Setup automation (Linux/Mac) | Run once to create resources |
| `scripts/azure-deploy.bat` | Setup automation (Windows) | Run once to create resources |

---

## 💡 Tips & Tricks

**1. Don't commit .env files**
```bash
# Instead, use .env.example as template
git add backend/.env.example frontend/.env.example
git add -u backend/.env  # Remove if committed
```

**2. Test Docker locally first**
```bash
cd backend
docker build -t clusteriq-backend .
docker run -p 8000:8000 \
  -e DATABRICKS_HOST="..." \
  -e DATABRICKS_TOKEN="..." \
  clusteriq-backend
```

**3. Monitor deployments**
- GitHub Actions: Push → Workflow runs → Deploy (3-5 min)
- Azure Portal: Web App → Activity log → See deployment progress

**4. View logs**
```bash
# Real-time backend logs
az webapp log tail --name clusteriq-backend-api -g clusteriq-rg

# Real-time frontend logs  
az webapp log tail --name clusteriq-frontend -g clusteriq-rg
```

**5. Rollback to previous version**
```bash
# In GitHub, revert commit
git revert <commit-hash>
git push origin main
# Deploys previous version automatically
```

---

## ⚠️ Important Reminders

1. **Never commit secrets** to GitHub
   - Use `.env.example` as template
   - Store secrets in Azure Portal

2. **Set correct CORS origins**
   - Must match your frontend URL
   - Don't leave localhost in production

3. **Test before deploying**
   - Build Docker images locally
   - Run containers and test APIs
   - Verify environment variables

4. **Monitor costs**
   - B2 plan ≈ $55/month per app
   - Total ≈ $110/month
   - Set Azure budget alerts

5. **Backup credentials**
   - Save publish profiles securely
   - Backup Databricks token
   - Store in password manager

---

## 🆘 Troubleshooting Quick Links

| Issue | Solution |
|-------|----------|
| Workflow fails | → Check GitHub Actions logs → See AZURE_DEPLOYMENT.md |
| App won't start | → Check Azure logs → Verify env variables |
| Can't reach backend | → Check CORS settings → Verify URL |
| Docker build fails | → Test locally → Check Dockerfile → See AZURE_DEPLOYMENT.md |
| Deployment is slow | → First deployment slower (pulls layers) → Subsequent faster |

---

## 📞 Support Resources

- **Azure Documentation:** https://docs.microsoft.com/azure/
- **GitHub Actions Docs:** https://docs.github.com/actions
- **Docker Reference:** https://docs.docker.com/reference/
- **Flask Docs:** https://flask.palletsprojects.com/
- **React Docs:** https://react.dev/

---

## ✨ You're Ready!

Everything is set up. Just follow **[AZURE_QUICK_START.md](AZURE_QUICK_START.md)** for the 5 deployment steps.

**Estimated time:** 30 minutes from start to deployed app

---

**Next Step:** Open [AZURE_QUICK_START.md](AZURE_QUICK_START.md) →
