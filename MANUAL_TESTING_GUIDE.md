# Manual Testing Guide - ClusterIQ Self-Healing Demo

This guide shows how to manually test and demonstrate the three self-healing scenarios.

---

## Scenario 1: Auto Termination for Idle Clusters

### Current Configuration
- **Idle Timeout**: 10 minutes (configured in `data/self_healing_config.json`)
- **Feature Status**: Enabled (`auto_terminate_idle_clusters: true`)
- **Dry-Run Mode**: Disabled (will actually execute)

### Manual Testing Steps

**Step 1: Check current config**
```powershell
cd backend
python -c "from self_healing_config import get_config; import json; print(json.dumps(get_config().config, indent=2))"
```
Expected output: Should show `"idle_timeout_minutes": 10` and `"auto_terminate_idle_clusters": true`

**Step 2: List all clusters**
```powershell
python -c "from databricks_client import DatabricksClient; from config import get_databricks_credentials; \
creds = get_databricks_credentials(); client = DatabricksClient(creds); \
clusters = client.get_all_clusters(); \
import json; print(json.dumps([{'id': c.get('cluster_id'), 'name': c.get('cluster_name'), 'state': c.get('state')} for c in clusters], indent=2))"
```

**Step 3: Check idle cluster detection**
```powershell
python health_monitor.py
```
Expected output: Will show clusters that are idle (RUNNING state but no recent activity)

**Step 4: Trigger auto termination on a specific idle cluster**
```powershell
python -c "from databricks_client import DatabricksClient; from config import get_databricks_credentials; \
from auto_remediation import AutoRemediation; \
creds = get_databricks_credentials(); client = DatabricksClient(creds); \
remediation = AutoRemediation(client); \
result = remediation.auto_terminate_idle_cluster('CLUSTER_ID_HERE'); \
import json; print(json.dumps(result, indent=2))"
```
Replace `CLUSTER_ID_HERE` with actual cluster ID

**Expected Behavior:**
- Cluster is identified as idle (no spark activity for >10 minutes)
- Cluster is terminated/stopped
- Action is logged in `data/healing_history.json`

---

## Scenario 2: Failed Job Restart to 1 Attempt Only

### Current Configuration (UPDATED ✅)
- **Max Restart Attempts**: 1 ✅ (changed from 3)
- **Location**: `data/self_healing_config.json` - `rules.auto_restart.max_attempts`
- **Behavior**: Only the LAST (most recent) failed job is eligible for restart
- **Restart Window**: 2 hours (120 minutes)

### Manual Testing Steps

**Step 1: Verify max attempts is set to 1**
```powershell
python -c "from self_healing_config import get_config; \
config = get_config(); \
max_attempts = config.get_rule('auto_restart').get('max_attempts'); \
print(f'Current max restart attempts: {max_attempts}')"
```
Expected output: `Current max restart attempts: 1` ✅

**Step 2: Find a recently failed job/cluster**
```powershell
python check_failed_jobs.py
```
Or use the test file:
```powershell
python test_failed_cluster_restart.py --check
```
Expected output: Lists clusters that failed in last 2 hours

**Step 3: Check restart history for a cluster**
```powershell
python -c "from self_healing_config import get_history; \
history = get_history(); \
actions = history.get_actions_for_resource('CLUSTER_ID_HERE'); \
import json; \
restart_actions = [a for a in actions if a.get('action_type') == 'auto_restart']; \
print(f'Restart attempts: {len(restart_actions)}'); \
print(json.dumps(restart_actions, indent=2, default=str))"
```
Replace `CLUSTER_ID_HERE` with cluster that failed

**Step 4: Trigger auto restart**
```powershell
python -c "from databricks_client import DatabricksClient; from config import get_databricks_credentials; \
from auto_remediation import AutoRemediation; \
creds = get_databricks_credentials(); client = DatabricksClient(creds); \
remediation = AutoRemediation(client); \
result = remediation.auto_restart_cluster('CLUSTER_ID_HERE'); \
import json; print(json.dumps(result, indent=2))"
```

**Expected Behavior (AFTER change to 1) ✅:**
- 1st attempt: Cluster restarts ✓
- 2nd attempt: BLOCKED - "Max restart attempts (1) reached. Only the last failed job is eligible for restart."
- Prevents retry storms - only allows ONE single restart per cluster failure cycle

---

## Scenario 3: Long Running Job Stop/Cancel

### Current Configuration
- **Feature Status**: Disabled (`auto_cancel_long_running_jobs: false`)
- **Threshold**: 10 minutes (`LONG_RUNNING_THRESHOLD_MINUTES`)
- **Location**: Main logic in `main.py` - `generate_long_running_job_recommendations()`

### Manual Testing Steps

**Step 1: Enable long-running job cancellation**
```powershell
python -c "from self_healing_config import get_config; \
config = get_config(); \
config.update_config({'features': {'auto_cancel_long_running_jobs': True}}); \
print('Feature enabled')"
```

**Step 2: Check threshold**
```powershell
python -c "print('Current threshold: 10 minutes')"
```

**Step 3: Run the health analysis (will detect long-running jobs)**
```powershell
python -c "from simple_server import perform_full_analysis; \
analysis = perform_full_analysis(); \
import json; \
long_running_recs = [r for r in analysis.get('recommendations', []) if r.get('type') == 'long_running_job']; \
print(f'Found {len(long_running_recs)} long-running job recommendations'); \
print(json.dumps(long_running_recs[:2], indent=2, default=str))"
```

**Step 4: Get active jobs running >10 minutes**
```powershell
python main.py --check-long-running
```
Expected output: Shows jobs running longer than 10 minutes

**Step 5: Cancel a specific long-running job/run**
```powershell
python -c "from databricks_client import DatabricksClient; from config import get_databricks_credentials; \
creds = get_databricks_credentials(); client = DatabricksClient(creds); \
result = client.cancel_job_run(job_id='JOB_ID', run_id='RUN_ID'); \
import json; print(json.dumps(result, indent=2))"
```

**Expected Behavior:**
- Jobs running >10 minutes are detected
- Recommendations are generated with cancel action
- Upon approval/execution, job run is cancelled
- Cost savings calculated and logged

---

## Summary of Changes Needed

### ✅ Change 1: Auto-Restart Attempts (Scenario 2) - COMPLETED
**File**: `data/self_healing_config.json`
```json
"rules": {
  "auto_restart": {
    "enabled": true,
    "conditions": ["FAILED", "ERROR", "TERMINATING"],
    "max_attempts": 1,  ✅ Changed from 3 to 1
    "backoff_minutes": 5
  }
}
```
**Code Updates**: 
- `auto_remediation.py` - Now tracks total restart attempts (not just last hour) and only allows 1 per failure
- `test_failed_cluster_restart.py` - Updated MAX_RESTART_ATTEMPTS constant to 1
- `self_healing_config.py` - Updated default config to max_attempts: 1

### TODO Change 2: Enable Long-Running Job Cancellation (Scenario 3)
**File**: `data/self_healing_config.json`
```json
"features": {
  ...
  "auto_cancel_long_running_jobs": true  // Change from false to true
}
```

---

## Quick Demo Script Template

```powershell
# 1. IDLE CLUSTER TERMINATION
Write-Host "=== SCENARIO 1: Auto Terminate Idle Cluster ===" -ForegroundColor Green
python health_monitor.py
Write-Host "Review idle clusters above. Running auto-termination..." -ForegroundColor Yellow
# [Run termination command]

# 2. FAILED JOB RESTART
Write-Host "`n=== SCENARIO 2: Failed Job Restart ===" -ForegroundColor Green
python test_failed_cluster_restart.py --check
Write-Host "Review failed clusters. Attempting restart..." -ForegroundColor Yellow
# [Run restart command]

# 3. LONG RUNNING JOB CANCEL
Write-Host "`n=== SCENARIO 3: Long Running Job Detection ===" -ForegroundColor Green
python main.py --check-long-running
Write-Host "Review long-running jobs. Cancelling stuck jobs..." -ForegroundColor Yellow
# [Run cancel command]
```

---

## Troubleshooting

**No clusters found?**
- Check Databricks authentication: `python -c "from databricks_client import DatabricksClient; from config import get_databricks_credentials; print(DatabricksClient(get_databricks_credentials()).get_all_clusters())"`

**Dry-run mode preventing changes?**
- Check config: `python -c "from self_healing_config import get_config; print(get_config().is_dry_run())"`
- Disable: `python -c "from self_healing_config import get_config; get_config().update_config({'safety': {'dry_run': False}})"`

**History not updating?**
- Check file permissions: `ls -l data/healing_history.json`
- View history: `python -c "from self_healing_config import get_history; print(get_history().history)"`
