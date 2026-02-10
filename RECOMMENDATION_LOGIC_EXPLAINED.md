# Recommendation Display Logic - Complete Understanding

## Overview
Recommendations are segregated into **3 different panes** based on their type and purpose:

---

## 1. **Recommendations Pane** (Optimization & Configuration)

### Purpose
Shows **optimization and configuration recommendations** - things that improve performance or cost but are NOT urgent failures.

### Sorting Logic (Line 75-91)
```javascript
// Priority 1: Execution errors first
// Priority 2: Then by timestamp (newest first)
orderMap = {
  execution_error: 0,      // Highest priority
  frequent_retries: 1,
  cost_leak: 2,
  idle_cluster: 3,
  optimization: 4,
  other: 5                 // Lowest priority
}
```

### Job Section Filtering (Line 313)
```javascript
// EXCLUDES auto-healable types (those go to SelfHealing)
autoHealableTypes = ['stuck_pending_job', 'long_running_job', 'idle_cluster', 'execution_error']

// Shows: Optimization recommendations like:
// ✅ "Job with no tasks" (configuration issue)
// ✅ "Job timeout too high" (optimization)
// ✅ "Unnecessary retries configured" (optimization)
```

### Cluster Section Filtering (Line 381)
```javascript
// EXCLUDES auto-healable types (those go to SelfHealing)
autoHealableTypes = ['stuck_pending_job', 'long_running_job', 'idle_cluster', 'execution_error']

// Shows: Cluster optimization recommendations like:
// ✅ "Cluster autoscaling not enabled" (optimization)
// ✅ "Wrong instance type" (cost optimization)
// ✅ "Spot instances recommended" (cost optimization)
```

---

## 2. **SelfHealing Pane** (Auto-Remediation Issues)

### Purpose
Shows **ONLY auto-healable issues** - urgent problems that can be automatically fixed.

### Filtering Logic (Line 118-141) ✅ FIXED
```javascript
// Auto-healable types ONLY
autoHealableTypes = [
  'stuck_pending_job',     // Job stuck in PENDING state
  'long_running_job',      // Job running too long
  'idle_cluster',          // Cluster idle and wasting cost
  'execution_error',       // Job execution failure
  'frequent_retries',      // Job failing repeatedly
  'failed_cluster'         // Cluster in failed state
]

// ONLY includes these specific types
// ❌ Does NOT include all job recommendations
// ❌ Does NOT include optimization recommendations
```

### Job Issues Section (Line 477-479)
```javascript
// Filter: resource_type === 'job' AND type !== 'idle_cluster'
// Shows:
// ✅ execution_error - Failed jobs (max 1 restart)
// ✅ stuck_pending_job - Jobs stuck in PENDING
// ✅ long_running_job - Jobs running too long
// ✅ frequent_retries - Jobs failing repeatedly
// ❌ "Job with no tasks" (goes to Recommendations pane)
```

### Cluster Issues Section (Line 590-593)
```javascript
// Filter: resource_type === 'cluster' OR type === 'idle_cluster'
// Shows:
// ✅ idle_cluster - Clusters wasting resources
// ✅ failed_cluster - Clusters in error state
// ❌ Cluster optimization recommendations (go to Recommendations pane)
```

---

## 3. **Approvals Pane** (All Pending Recommendations)

### Purpose
Shows **ALL pending recommendations** regardless of type - central place for approval workflow.

### Logic
```javascript
// Shows everything with status === 'PENDING'
// No filtering by type
// Includes both auto-healable AND optimization recommendations
```

---

## Summary Table

| Recommendation Type | Recommendations Pane | SelfHealing Pane | Approvals Pane |
|---------------------|---------------------|------------------|----------------|
| **Job Execution Error** | ❌ | ✅ Job Issues | ✅ |
| **Job Stuck Pending** | ❌ | ✅ Job Issues | ✅ |
| **Job Long Running** | ❌ | ✅ Job Issues | ✅ |
| **Job Frequent Retries** | ❌ | ✅ Job Issues | ✅ |
| **Job with No Tasks** | ✅ Job Section | ❌ | ✅ |
| **Job Config Issues** | ✅ Job Section | ❌ | ✅ |
| **Idle Cluster** | ❌ | ✅ Cluster Issues | ✅ |
| **Failed Cluster** | ❌ | ✅ Cluster Issues | ✅ |
| **Cluster Optimization** | ✅ Cluster Section | ❌ | ✅ |

---

## Key Fixes Applied

### Before (WRONG ❌)
```javascript
// SelfHealing.jsx Line 139
if (rec.resource_type === 'job') return true  
// ❌ Included ALL job recommendations
// ❌ Showed "Job with no tasks" in Auto-Remediation
```

### After (CORRECT ✅)
```javascript
// SelfHealing.jsx Line 138
if (autoHealableTypes.includes(rec.type)) return true
return false  
// ✅ ONLY includes specific auto-healable types
// ✅ "Job with no tasks" goes to Recommendations pane
```

---

## Testing Scenarios

### Scenario 1: Job Execution Failure
- **Dashboard**: Shows in job recommendation count
- **Recommendations**: ❌ Not shown (auto-healable)
- **SelfHealing**: ✅ Shows in "Job Issues" section with "Max 1 restart per job"
- **Approvals**: ✅ Shows in pending

### Scenario 2: Job with No Tasks
- **Dashboard**: Shows in job recommendation count
- **Recommendations**: ✅ Shows in "Job Optimization" section
- **SelfHealing**: ❌ Not shown (not auto-healable)
- **Approvals**: ✅ Shows in pending

### Scenario 3: Idle Cluster
- **Dashboard**: Shows in cluster recommendation count
- **Recommendations**: ❌ Not shown (auto-healable)
- **SelfHealing**: ✅ Shows in "Cluster Issues" section
- **Approvals**: ✅ Shows in pending

---

## Dynamic Count Behavior

### Dashboard
- **Job Count**: All job recommendations (both auto-healable + optimization)
- **Cluster Count**: All cluster recommendations (both auto-healable + optimization)

### SelfHealing
- **Auto-Healable Count**: Only auto-healable issues (execution errors, stuck jobs, idle clusters, failed clusters)
- **Job Issues Count**: Auto-healable job issues only
- **Cluster Issues Count**: Auto-healable cluster issues only  

### Recommendations
- **Job Section Count**: Optimization recommendations only (excludes auto-healable)
- **Cluster Section Count**: Optimization recommendations only (excludes auto-healable)

---

## Refresh Intervals

- **Dashboard**: 30 seconds
- **Recommendations**: 30 seconds (or custom via dropdown)
- **SelfHealing**: 5 seconds (auto-remediation query)
- **Approvals**: 30 seconds
