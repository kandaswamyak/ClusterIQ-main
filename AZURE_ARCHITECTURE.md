# Azure Deployment Architecture

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      GitHub Repository                          │
│                     (ClusterIQ-main)                            │
│                                                                 │
│  ┌────────────────────┐         ┌────────────────────┐         │
│  │  Backend Code      │         │  Frontend Code     │         │
│  │  - Python          │         │  - React/Vite      │         │
│  │  - Flask           │         │  - Node.js         │         │
│  │  - Requirements    │         │  - Package.json    │         │
│  └────────────────────┘         └────────────────────┘         │
│           │                              │                     │
│  ┌────────▼────────┐         ┌──────────▼───────┐            │
│  │  Dockerfile     │         │  Dockerfile      │            │
│  │  - Python 3.11  │         │  - Node.js 18    │            │
│  │  - Alpine       │         │  - Alpine        │            │
│  │  - Slim         │         │  - Multi-stage   │            │
│  └─────────────────┘         └──────────────────┘            │
│           │                              │                     │
│           └──────────┬──────────────────┘                      │
│                      │                                         │
│          GitHub Actions (Workflows)                           │
│       (deploy-backend.yml)                                    │
│       (deploy-frontend.yml)                                   │
│                      │                                         │
└──────────────────────┼─────────────────────────────────────────┘
                       │
           ┌───────────┴──────────┐
           │                      │
    ┌──────▼──────┐       ┌───────▼─────┐
    │  Push to    │       │   Build     │
    │  Container  │       │   Docker    │
    │  Registry   │       │   Image     │
    │             │       │             │
    │ GHCR.IO     │       │ Multi-stage │
    └──────┬──────┘       └───────┬─────┘
           │                      │
           └──────────┬───────────┘
                      │
         ┌────────────┴─────────────┐
         │                          │
    ┌────▼─────┐           ┌────────▼────┐
    │  Backend │           │  Frontend    │
    │  Deploy  │           │  Deploy      │
    └────┬─────┘           └────────┬─────┘
         │                          │
    ┌────▼──────────────────────────▼────┐
    │     Azure Web Apps (Linux)          │
    │                                      │
    │  ┌──────────────┐  ┌─────────────┐  │
    │  │   Backend    │  │  Frontend   │  │
    │  │   App Svc    │  │  App Svc    │  │
    │  │              │  │             │  │
    │  │ :8000        │  │ :3000       │  │
    │  └──────────────┘  └─────────────┘  │
    │                                      │
    │  App Service Plans (B2 SKU)         │
    │  - Auto-scaling capable             │
    │  - Load balancing included          │
    │  - Health checks enabled            │
    │  - Monitoring enabled               │
    │                                      │
    └────┬──────────────────────────┬─────┘
         │                          │
    ┌────▼─────────────┐   ┌───────▼──────┐
    │ Databricks API   │   │  Azure OpenAI│
    │  - Clusters      │   │  - GPT Model │
    │  - Jobs          │   │  - Analysis  │
    │  - Delta Tables  │   │  - Insights  │
    └──────────────────┘   └──────────────┘
```

## Deployment Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                    Git Push to Main Branch                      │
└────────────────────┬────────────────────────────────────────────┘
                     │
        ┌────────────┴─────────────┐
        │                          │
    ┌───▼─────────┐           ┌───▼──────────┐
    │   Backend   │           │   Frontend   │
    │   Workflow  │           │   Workflow   │
    └───┬─────────┘           └───┬──────────┘
        │                         │
    ┌───▼─────────────────────────▼────────┐
    │    Build Docker Images                │
    │  - Run tests                          │
    │  - Build layers                       │
    │  - Optimize sizes                     │
    └────────┬─────────────────────────────┘
             │
    ┌────────▼──────────────────────┐
    │  Push to GitHub Container      │
    │  Registry (GHCR.IO)            │
    │  - ghcr.io/owner/backend:xxx   │
    │  - ghcr.io/owner/frontend:xxx  │
    └────────┬──────────────────────┘
             │
    ┌────────▼──────────────────────┐
    │  Deploy to Azure Web Apps      │
    │  - Pull image from GHCR        │
    │  - Create container            │
    │  - Configure environment       │
    │  - Start health checks         │
    │  - Route traffic               │
    └────────┬──────────────────────┘
             │
    ┌────────▼──────────────────────┐
    │   Deployment Complete!         │
    │   ✓ Backend running at :8000  │
    │   ✓ Frontend running at :3000 │
    └───────────────────────────────┘
```

## Environment Variables Flow

```
┌──────────────────────────────────────────────┐
│          Local Development (.env)            │
│  - DATABRICKS_HOST                           │
│  - DATABRICKS_TOKEN                          │
│  - AZURE_OPENAI_*                            │
└───────────────┬────────────────────────────┘
                │ (for local testing only)
                │
┌───────────────▼────────────────────────────┐
│    Git Push (DO NOT COMMIT .env file)       │
│    Use .env.example as template             │
└───────────────┬────────────────────────────┘
                │
┌───────────────▼────────────────────────────┐
│      GitHub Actions Workflow                │
│   - Read secrets from GitHub Secrets        │
│   - Build Docker image                      │
│   - Push to registry                        │
└───────────────┬────────────────────────────┘
                │
┌───────────────▼────────────────────────────┐
│    Azure Web App Configuration              │
│   Application Settings:                     │
│   - DATABRICKS_HOST                         │
│   - DATABRICKS_TOKEN                        │
│   - AZURE_OPENAI_ENDPOINT                   │
│   - AZURE_OPENAI_API_KEY                    │
│   - etc...                                  │
└────────────────────────────────────────────┘
                │
        ┌───────▼─────────┐
        │  Injected into  │
        │  Container at   │
        │  Runtime        │
        └─────────────────┘
```

## Networking

```
┌──────────────────────────────────────────────────────────┐
│                  Internet                                 │
└──────────────┬──────────────────────────────────────────┘
               │ (HTTPS only)
               │
    ┌──────────┴────────────┐
    │                       │
┌───▼────────────┐   ┌─────▼────────────┐
│  Frontend App  │   │  Backend App     │
│   (Port 3000)  │   │   (Port 8000)    │
│ - Serves HTML  │   │ - API endpoints  │
│ - Serves JS    │   │ - Data processing│
│ - Serves CSS   │   │ - DB connections │
└────────┬───────┘   └────────┬─────────┘
         │                    │
         │   User Request:    │
         │ /api/stats         │
         └──────────┬─────────┘
                    │
            ┌───────▼──────────┐
            │  CORS Headers    │
            │  Check & Validate│
            └───────┬──────────┘
                    │
            ┌───────▼──────────┐
            │  Process Request │
            │  - Verify auth   │
            │  - Call Databricks
            │  - Return data   │
            └────────┬─────────┘
                     │
            ┌────────▼──────────┐
            │  Response to      │
            │  Frontend (JSON)  │
            └───────────────────┘
```

## Data Flow

```
Frontend (React)
    │
    ├─→ User clicks action
    │
    ├─→ API call: fetch('/api/stats')
    │
    ├─→ Backend receives request
    │
    ├─→ Backend calls Databricks API
    │   ├─ /api/2.1/clusters/list
    │   ├─ /api/2.1/jobs/list
    │   ├─ /api/2.0/sql/warehouses
    │   └─ ... other endpoints
    │
    ├─→ Backend processes data
    │   ├─ Counts resources
    │   ├─ Formats response
    │   └─ Returns JSON
    │
    ├─→ Frontend receives JSON
    │
    ├─→ React updates state
    │
    └─→ UI re-renders with data
```

## Scaling Strategy

```
Single App Service
    │
    ├─→ Vertical Scaling (increase SKU)
    │   ├─ B2 → S1 → S2 → P1 (more CPU/RAM)
    │   └─ Reduces cost per unit
    │
    └─→ Horizontal Scaling (auto-scale)
        ├─ Add more instances (replicas)
        ├─ Load balancer distributes traffic
        └─ Auto-scale rules:
           ├─ CPU > 80% → Add instance
           └─ CPU < 20% → Remove instance
```

## Backup & Recovery

```
Production Deployment
    │
    ├─→ Automated backups
    │   └─ Git repository = complete recovery
    │
    ├─→ Rollback capability
    │   ├─ Revert to previous commit
    │   ├─ GitHub Actions re-deploys
    │   └─ Full recovery in ~5 minutes
    │
    └─→ Application insights logging
        ├─ All errors logged
        ├─ Performance metrics
        └─ User activity tracked
```

## Security Layers

```
┌────────────────────────────────────┐
│      HTTPS/TLS Encryption          │
│   (Azure managed certificate)       │
└──────────┬─────────────────────────┘
           │
┌──────────▼─────────────────────────┐
│       CORS Protection              │
│   (Origin validation)              │
└──────────┬─────────────────────────┘
           │
┌──────────▼─────────────────────────┐
│     Web App Firewall (optional)    │
│   (DDoS protection, WAF rules)     │
└──────────┬─────────────────────────┘
           │
┌──────────▼─────────────────────────┐
│    Docker Container Isolation      │
│   (Namespace/cgroup isolation)     │
└──────────┬─────────────────────────┘
           │
┌──────────▼─────────────────────────┐
│     Non-root User (appuser)        │
│   (UID 1000, limited privileges)   │
└──────────┬─────────────────────────┘
           │
┌──────────▼─────────────────────────┐
│    Application-level Security      │
│   - Input validation               │
│   - Authentication checks          │
│   - Authorization controls         │
└────────────────────────────────────┘
```

## Monitoring & Observability

```
Azure Web Apps
    │
    ├─→ Application Insights
    │   ├─ Error tracking
    │   ├─ Performance metrics
    │   ├─ Dependency tracking
    │   └─ Custom events
    │
    ├─→ Log Analytics
    │   ├─ Centralized logging
    │   ├─ Query logs with KQL
    │   └─ Create dashboards
    │
    ├─→ Alerts & Notifications
    │   ├─ Alert on errors
    │   ├─ Alert on performance
    │   ├─ Email/SMS notifications
    │   └─ Slack integration (optional)
    │
    └─→ GitHub Actions Logs
        ├─ Deployment status
        ├─ Build logs
        ├─ Push status
        └─ Complete audit trail
```

---

This architecture provides:
✅ High availability
✅ Easy scaling
✅ Automated deployments
✅ Complete monitoring
✅ Security best practices
✅ Cost optimization
