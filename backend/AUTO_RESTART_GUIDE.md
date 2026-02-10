# Auto Restart - Failed Cluster Recovery

## Overview

The Auto Restart feature monitors Databricks clusters for failures and automatically restarts them within a configurable time window. This ensures minimal downtime for critical workloads.

## Key Features

✅ **2-Hour Failure Window**: Only restarts clusters that failed in the last 2 hours  
✅ **Max 3 Restart Attempts**: Prevents infinite restart loops for persistently failing clusters  
✅ **Automatic Detection**: Monitors ERROR and FAILED cluster states  
✅ **History Tracking**: Records all restart attempts and outcomes  
✅ **Configurable Thresholds**: Easily adjust window duration and max attempts  

---

## How It Works

### 1. Detection Phase
```
Every 10 seconds:
  └─ Check all clusters in workspace
     ├─ Identify clusters in FAILED or ERROR state
     ├─ Extract failure timestamp from cluster metadata
     ├─ Check if failure is within 2-hour window
     └─ Count previous restart attempts
```

### 2. Eligibility Check
```
For each failed cluster:
  ├─ ✅ Passed: Failed < 2 hours ago AND restart_attempts < 3
  │   └─ → AUTO-RESTART INITIATED
  │
  └─ ❌ Failed: Failed > 2 hours ago OR restart_attempts >= 3
      ├─ Reason: Outside window (manual intervention needed)
      └─ Reason: Max attempts reached (manual intervention needed)
```

### 3. Restart Phase
```
When auto-restart is triggered:
  ├─ Call Databricks API /clusters/start
  ├─ Log action to history
  ├─ Update cluster state to PENDING
  ├─ Wait for cluster to transition to RUNNING
  └─ Trigger recovery scripts if configured
```

---

## Configuration

### File Location
```
backend/data/self_healing_config.json
```

### Configuration Section
```json
{
  "features": {
    "auto_restart_failed_clusters": true
  },
  "thresholds": {
    "failed_restart_window_minutes": 120,
    "max_restart_attempts": 3
  },
  "rules": {
    "auto_restart": {
      "enabled": true,
      "conditions": ["FAILED", "ERROR", "TERMINATING"],
      "max_attempts": 3,
      "backoff_minutes": 5
    }
  }
}
```

### Configuration Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `auto_restart_failed_clusters` | `true` | Enable/disable auto-restart feature |
| `failed_restart_window_minutes` | `120` | Time window to detect failures (2 hours) |
| `max_restart_attempts` | `3` | Max restarts per cluster before manual intervention |
| `conditions` | `FAILED, ERROR` | Cluster states to monitor |
| `backoff_minutes` | `5` | Wait time between restart attempts |

---

## Failure Scenarios

### Scenario 1: Recent Failure (Within 2 Hours)
```
Cluster: test-cluster
State: ERROR
Failed: 45 minutes ago
Restart Attempts: 0/3

Status: ✅ AUTO-RESTART ENABLED
Action: System will attempt to restart cluster
```

### Scenario 2: Old Failure (> 2 Hours)
```
Cluster: legacy-cluster
State: ERROR
Failed: 3 hours ago
Restart Attempts: 0/3

Status: ⚠️ OUTSIDE WINDOW
Reason: Failure older than 2 hours threshold
Action: REQUIRES MANUAL INTERVENTION
```

### Scenario 3: Max Attempts Exceeded
```
Cluster: flaky-cluster
State: ERROR
Failed: 30 minutes ago
Restart Attempts: 3/3

Status: ⚠️ MAX ATTEMPTS REACHED
Reason: Cluster has been restarted 3 times already
Action: REQUIRES MANUAL INVESTIGATION
```

### Scenario 4: Healthy Cluster (No Restart Needed)
```
Cluster: prod-cluster
State: RUNNING
Last Activity: 2 minutes ago

Status: ✅ HEALTHY
Action: No action needed
```

---

## Usage

### Test Script
```bash
# Check for failed clusters in the last 2 hours
python backend/test_failed_cluster_restart.py --check

# View test scenarios and configuration
python backend/test_failed_cluster_restart.py --test-scenario

# Generate detailed report
python backend/test_failed_cluster_restart.py --report

# Restart a specific cluster
python backend/test_failed_cluster_restart.py --restart-id <cluster_id>

# Attempt to restart all restartable failed clusters
python backend/test_failed_cluster_restart.py --restart-all
```

### API Endpoints

#### Check Self-Healing Status
```
GET /api/self-healing/stats
Response:
{
  "enabled": true,
  "health_summary": {
    "total_clusters": 20,
    "unhealthy": 0,
    "healthy": 20,
    "issues_by_type": {
      "failed_restart_window": 0,
      "max_attempts_exceeded": 0
    }
  },
  "healing_stats": {
    "total_actions": 5,
    "successful": 5,
    "failed": 0,
    "actions_by_type": {
      "auto_restart": 5
    }
  }
}
```

#### Trigger Self-Healing Run
```
POST /api/self-healing/run
Response:
{
  "success": true,
  "summary": {
    "scanned_clusters": 20,
    "actions_taken": 2,
    "failed_clusters": 0
  },
  "results": [
    {
      "action": "restart",
      "cluster_id": "0204-144158-test",
      "cluster_name": "test-cluster",
      "status": "success",
      "message": "Successfully restarted test-cluster"
    }
  ]
}
```

---

## Failure Detection Details

### Cluster Failure Indicators

The system identifies cluster failures by checking the cluster state:

```python
FAILED_STATES = {"FAILED", "ERROR"}
CHECK_STATES = {"FAILED", "ERROR", "TERMINATED", "TERMINATING"}
```

### Timestamp Extraction

The system tries multiple timestamp fields to identify when the failure occurred:

```
Priority Order:
1. cluster.terminated_time       (when cluster was terminated)
2. cluster.last_state_loss_time  (when cluster lost connectivity)
3. cluster.start_time            (cluster start time as fallback)
```

### Time Window Calculation

```
Current Time: 2026-02-08 20:50:00
Failure Window: 2 hours (120 minutes)
Cutoff Time: 2026-02-08 18:50:00

Example:
  Failed at 2026-02-08 19:00:00 → 110 minutes ago → ✅ ELIGIBLE
  Failed at 2026-02-08 17:30:00 → 200 minutes ago → ❌ OUTSIDE WINDOW
```

---

## Monitoring and History

### View Restart History
```python
from self_healing_config import get_history

history = get_history()
actions = history.get_actions()

# Filter for restart actions
restart_actions = [
    a for a in actions 
    if a['action_type'] == 'auto_restart'
]

for action in restart_actions:
    print(f"Cluster: {action['resource_id']}")
    print(f"Status: {action['status']}")
    print(f"Timestamp: {action['timestamp']}")
```

### Dashboard Metrics

The Self Healing dashboard shows:

- **Health Score**: Percentage of healthy clusters
- **Restart Attempts**: Total auto-restart actions taken
- **Success Rate**: % of successful restarts
- **Recent Actions**: Timeline of all healing actions

---

## Best Practices

### ✅ DO
- ✅ Set `failed_restart_window_minutes` to 120 (2 hours) for most use cases
- ✅ Start with `max_restart_attempts: 3` to allow retries
- ✅ Monitor the Self Healing dashboard regularly
- ✅ Review failed restart actions to identify root causes
- ✅ Adjust `backoff_minutes` if clusters require more startup time

### ❌ DON'T
- ❌ Don't set window too long (> 4 hours) → causes resource waste
- ❌ Don't set window too short (< 30 minutes) → may not allow cluster startup
- ❌ Don't disable auto-restart without monitoring
- ❌ Don't ignore clusters that hit max restart attempts
- ❌ Don't ignore repeated failures in the history

---

## Troubleshooting

### Issue: Auto-Restart Not Working
**Symptoms**: Clusters stay in FAILED state, no restarts happening

**Checklist**:
```
1. Is auto_restart_failed_clusters enabled in config?
   └─ Check: backend/data/self_healing_config.json
   
2. Is the failure within 2 hours?
   └─ Check: cluster.terminated_time or cluster.last_state_loss_time
   
3. Have max restart attempts (3) been exceeded?
   └─ Check: self-healing history
   
4. Are the cluster states being detected correctly?
   └─ Check: GET /api/clusters (look for state field)
   
5. Does the Databricks token have cluster restart permissions?
   └─ Check: backend/.env (DATABRICKS_TOKEN)
```

### Issue: Clusters Restarting Too Frequently
**Symptoms**: Clusters in infinite restart loop

**Solutions**:
```
1. Increase max_restart_attempts limit
   └─ Set to higher value (e.g., 5)
   
2. Extend the failure window
   └─ Increase failed_restart_window_minutes
   
3. Add cluster to exclusion list
   └─ Add cluster_id to config.safety.exclude_clusters
```

### Issue: Restart Attempts Fail
**Symptoms**: Clusters are restarted but fail to come back online

**Investigation**:
```
1. Check cluster logs in Databricks UI
2. Review node type and resource availability
3. Check for cluster configuration issues
4. Verify Spark version compatibility
5. Review auto-termination settings
```

---

## Related Features

- **Auto-Terminate Idle Clusters**: Automatically stops idle clusters to save costs
- **Self-Healing Status**: Real-time health monitoring and metrics
- **Healing History**: Complete audit trail of all auto-remediation actions
- **Recommendations**: Proactive suggestions for cluster optimization

---

## Testing and Validation

### Run Complete Health Check
```bash
# Check all clusters and their states
python backend/test_failed_cluster_restart.py --check

# Output:
# Found 2 failed cluster(s) in the last 2 hours:
# 
# ID: 0204-144158-test
# Name: test-cluster
# State: ERROR
# Failed: 45 minutes ago (0.8 hours)
# Restart Attempts: 0/3
# Status: ✅ Can Restart: YES
# ─────────────────────────────────
```

### Simulate and Test
```bash
# View configuration and scenarios
python backend/test_failed_cluster_restart.py --test-scenario

# This shows:
# - Configuration details
# - Example failure scenarios
# - How timestamps are parsed
# - Restart eligibility rules
```

---

## Summary

**Auto Restart** is a critical component of ClusterIQ's self-healing system that:

1. **Detects** cluster failures in real-time
2. **Validates** failures are recent (within 2 hours)
3. **Restarts** clusters automatically (up to 3 attempts)
4. **Tracks** all actions in the healing history
5. **Reports** status via dashboards and APIs

This ensures high availability while preventing resource waste from persisting issues.

**Files Involved**:
- `backend/test_failed_cluster_restart.py` - Test suite and CLI tool
- `backend/main.py` - `/api/self-healing/run` endpoint
- `backend/data/self_healing_config.json` - Configuration
- `backend/self_healing_config.py` - Config management

**Next Steps**:
1. Review the test_failed_cluster_restart.py script
2. Run with `--test-scenario` to understand flow
3. Check for failed clusters with `--check`
4. Monitor the Self Healing dashboard
