# ClusterIQ Knowledge Base - How To Guide

## Table of Contents
1. [Getting Started](#getting-started)
2. [Understanding the Dashboard](#understanding-the-dashboard)
3. [Running Analysis](#running-analysis)
4. [Working with Recommendations](#working-with-recommendations)
5. [Approval Workflow](#approval-workflow)
6. [Self-Healing Configuration](#self-healing-configuration)
7. [Monitoring Cluster Health](#monitoring-cluster-health)
8. [Best Practices](#best-practices)
9. [Frequently Asked Questions (FAQ)](#frequently-asked-questions-faq)
10. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Prerequisites

Before using ClusterIQ, ensure you have:

1. **Databricks Account Access**
   - Valid Databricks workspace
   - Admin or cluster management permissions
   - Personal access token

2. **Environment Variables Configured**
   ```
   DATABRICKS_HOST=https://your-workspace.azuredatabricks.net
   DATABRICKS_TOKEN=dapi...
   AZURE_OPENAI_ENDPOINT=https://your-endpoint.cognitiveservices.azure.com
   AZURE_OPENAI_API_KEY=your-key
   AZURE_OPENAI_DEPLOYMENT_NAME=ClusterIQGPT
   ```

3. **Delta Tables Created** (Optional but recommended)
   ```sql
   CREATE TABLE IF NOT EXISTS default.cluster_events (
     event_id STRING,
     cluster_id STRING,
     event_type STRING,
     timestamp TIMESTAMP,
     metadata STRING
   )
   
   CREATE TABLE IF NOT EXISTS default.cluster_logs (
     cluster_id STRING,
     timestamp TIMESTAMP,
     cpu_usage FLOAT,
     memory_usage FLOAT,
     disk_usage FLOAT
   )
   
   CREATE TABLE IF NOT EXISTS default.job_run_logs (
     job_id STRING,
     run_id STRING,
     duration INT,
     status STRING,
     cost FLOAT,
     timestamp TIMESTAMP
   )
   ```

### Starting ClusterIQ

#### 1. Start Backend Server
```bash
cd backend
python main.py
```
Backend runs on `http://localhost:8000`

#### 2. Start Frontend Server
```bash
cd frontend
npm run dev
```
Frontend runs on `http://localhost:3000`

#### 3. Access the Application
Open your browser to: **http://localhost:3000**

---

## Understanding the Dashboard

### Dashboard Components

#### 1. **Cluster Statistics Card**
Shows at-a-glance cluster metrics:
- Total clusters in workspace
- Running clusters
- Terminated clusters
- Estimated monthly cost

**💡 Tip:** Click the card to see breakdown by cluster state

#### 2. **Recent Recommendations Section**
Displays latest AI-generated optimization suggestions:
- Cluster name
- Recommendation type (Right-size, Terminate, etc.)
- Estimated monthly savings (e.g., "$250/month")
- Confidence score (0-100%)

**💡 Tip:** Higher confidence = more reliable recommendation

#### 3. **Jobs Overview**
Summary of Databricks jobs:
- Total jobs
- Active jobs
- Failed jobs (last 24 hours)
- Average job duration

#### 4. **Self-Healing Status** (if enabled)
Shows:
- Health monitoring: Active/Inactive
- Last health check time
- Recent auto-remediation actions
- Auto-healing rules active

---

## Running Analysis

### What Analysis Does

ClusterIQ Analysis:
1. ✅ Fetches current cluster data from Databricks API
2. ✅ Retrieves job execution history
3. ✅ Reads performance metrics from Delta tables (if configured)
4. ✅ Sends data to Azure OpenAI for intelligent analysis
5. ✅ Generates cost optimization recommendations
6. ✅ Stores recommendations for approval

### How to Run Analysis

#### Step 1: Click "Run Analysis" Button
Located on the Dashboard or in navigation

#### Step 2: Wait for Completion
Processing time: 30-120 seconds depending on:
- Number of clusters (typically 20-100)
- Number of jobs (typically 10-500)
- Delta table size (if reading logs)
- OpenAI API response time

#### Step 3: View Results
Once complete:
1. Dashboard updates with new recommendations
2. Recommendations page shows detailed suggestions
3. Estimated savings calculated
4. Confidence scores assigned

### Interpreting Analysis Results

#### Confidence Score
```
90-100%: Highly reliable (safe to auto-apply)
75-89%:  Moderately reliable (review before applying)
60-74%:  Less certain (recommend manual review)
<60%:    Low confidence (verify manually)
```

#### Estimated Savings
```
Calculation: (Current Cost) - (New Cost) per month

Examples:
- Right-size cluster: $500 - $250 = $250/month savings
- Terminate idle cluster: $1000 - $0 = $1000/month savings
- Scale down workers: $800 - $600 = $200/month savings
```

#### Recommendation Types
```
1. Right-Size: Reduce instance size (underutilized)
2. Consolidate: Merge multiple small clusters
3. Terminate: Kill unused/idle clusters
4. Change Instance: Switch to cost-effective type
5. Auto-Scale: Adjust worker count dynamically
```

---

## Working with Recommendations

### Recommendations Page

#### Viewing All Recommendations

1. Click **"Recommendations"** in sidebar
2. See all generated recommendations in card format
3. Each card shows:
   - Cluster name and ID
   - Recommendation action
   - Current cost vs. new cost
   - Estimated monthly savings (in dollars)
   - Confidence score (%)
   - Priority level (High/Medium/Low)

#### Expanding Recommendation Details

Click on any recommendation card to expand and see:
- Detailed analysis explanation
- Cluster current metrics (CPU, memory, uptime)
- Rationale for recommendation
- Implementation steps
- Potential risks

#### Filtering Recommendations

```
By Status:
- Pending (not yet approved)
- Approved (ready to implement)
- Applied (already implemented)
- Rejected (user declined)

By Priority:
- High impact (>$500/month savings)
- Medium impact ($100-500/month)
- Low impact (<$100/month)

By Type:
- Right-sizing
- Consolidation
- Termination
- Instance type change
- Scaling
```

#### Sorting Options
- By savings (highest to lowest)
- By confidence (most to least certain)
- By cluster name (A-Z)
- By date created (newest first)

---

## Approval Workflow

### Complete Approval Flow

```
Recommendations Generated
        ↓
User Reviews in UI
        ↓
User Clicks "Approve"
        ↓
Moves to "Approvals" Page
        ↓
Final Review Option
        ↓
User Clicks "Apply"
        ↓
Action Executes on Cluster
        ↓
Status Updated
        ↓
Logged in History
```

### Step-by-Step Approval Process

#### 1. Review Recommendation
- Go to **Recommendations** page
- Read description and analysis
- Check confidence score
- Review estimated savings

#### 2. Approve Recommendation
- Click **"Approve"** button on card
- Optional: Add approval note/comment
- Recommendation moves to Approvals page

#### 3. Final Review (Optional)
- Go to **Approvals** page
- See all approved-but-not-yet-applied recommendations
- Review once more before execution
- Option to reject if needed

#### 4. Apply/Execute Action
- Click **"Apply Now"** button
- Action executes immediately on Databricks cluster
- Status updates to "Executing"
- Wait for completion (typically seconds to minutes)

#### 5. Verify Results
- Check status in Approvals or History
- Verify cluster state in Databricks
- Monitor for issues

### Rejecting Recommendations

If you don't want to apply a recommendation:

1. **On Recommendations page:** Click "Reject" button
   - Recommendation moves to "Rejected" status
   - Won't show in Approvals page
   - Can be re-approved later if needed

2. **On Approvals page:** Click "Remove" or "Reject"
   - Removes from approvals
   - Returns to Recommendations as "Rejected"

### Viewing Approval History

1. Click **"History"** or **"Activity Log"**
2. See all past approvals with:
   - Who approved (if tracked)
   - When approved
   - When applied
   - Current status
   - Actual savings achieved

---

## Self-Healing Configuration

### What is Self-Healing?

Automated cluster remediation that:
- ✅ Detects cluster issues continuously
- ✅ Executes fixes without waiting for approval
- ✅ Minimizes downtime
- ✅ Reduces manual intervention
- ✅ Maintains audit trail

### When to Use Self-Healing

**Use Self-Healing FOR:**
- 🟢 Dev/test environments (low risk)
- 🟢 Idle cluster termination (safe, reversible)
- 🟢 Routine auto-scaling adjustments
- 🟢 Failed cluster restart (minimize downtime)

**DON'T Use Self-Healing FOR:**
- 🔴 Production clusters (until fully validated)
- 🔴 Critical workloads
- 🔴 Cost-significant changes
- 🔴 Compliance-sensitive operations

### Accessing Self-Healing Settings

1. Click **"Self-Healing"** in navigation
2. See current status and configuration
3. View recent automated actions
4. Access settings panel

### Configuring Self-Healing

#### Step 1: Enable Self-Healing
```
Toggle: Self-Healing [OFF] → [ON]
```

#### Step 2: Configure Features
```
Feature Controls:
☐ Auto-Restart Failed Clusters
☐ Auto-Terminate Idle Clusters
☐ Auto-Scale Resources
☐ Auto-Apply Cost Optimizations
```

#### Step 3: Set Safety Parameters
```
Max Restart Attempts: 3 (prevent infinite loops)
Idle Timeout: 60 minutes (before terminating)
Max Actions Per Hour: 10 (rate limiting)
Dry-Run Mode: ON (test first)
```

#### Step 4: Exclude Critical Clusters
```
Excluded Clusters:
- prod-*
- critical-*
- etl-nightly-*
- ml-training-*
```

#### Step 5: Enable Notifications (Recommended)
```
Send Alert When:
☑ Action executed
☑ Action failed
☑ Restart limit exceeded
☑ Cost threshold exceeded
```

### Dry-Run Mode (Recommended First Step)

Before enabling actual self-healing:

1. **Enable Dry-Run:** Toggle `DRY_RUN: ON`
2. **Let it run for 1 week:**
   - Observe what actions would be taken
   - Review in "Dry-Run Activity Log"
   - Verify no false positives
3. **Check recommendations:**
   - Are clusters correctly identified as idle?
   - Are restart attempts appropriate?
   - Any wrong clusters in exclusion list?
4. **Adjust configuration if needed**
5. **Disable Dry-Run:** `DRY_RUN: OFF`
6. **Enable actual execution**

### Monitoring Self-Healing Actions

#### Recent Actions List
Shows last 20 auto-remediation actions:
- Timestamp
- Cluster affected
- Action taken
- Status (success/failed)
- Impact (cost saved, downtime avoided)

#### Activity Statistics
```
Today:
- Actions taken: 3
- Success rate: 100%
- Clusters healed: 2
- Cost saved: $150

This Week:
- Actions taken: 15
- Success rate: 93%
- Clusters healed: 8
- Cost saved: $850
```

---

## Monitoring Cluster Health

### Health Check Overview

ClusterIQ monitors cluster health for:
- ✅ Failed clusters (immediate attention)
- ✅ Idle clusters (cost optimization)
- ✅ Under-provisioned clusters (performance)
- ✅ Over-provisioned clusters (cost)
- ✅ Unhealthy worker nodes
- ✅ Job failure rates

### Health Status Indicators

```
🟢 HEALTHY
- Running clusters with good metrics
- Normal CPU/memory usage
- Jobs completing successfully

🟡 WARNING
- Slightly elevated issues
- Minor performance degradation
- Potential problems emerging

🔴 CRITICAL
- Failed clusters
- 100% CPU/memory
- High job failure rate
- Requires immediate action
```

### Health Percentage Score

```
90-100%: Excellent health
75-89%:  Good, minor issues
60-74%:  Fair, needs attention
<60%:    Poor, urgent action needed
```

### Manual Health Check

To manually trigger a health check:

1. Click **"Self-Healing"** → **"Check Health Now"** button
2. Wait for health monitor to run (30-60 seconds)
3. View results:
   - Total clusters scanned
   - Healthy clusters
   - Clusters with issues
   - Clusters with auto-healable problems

### Health History

View health checks over time:
1. **Self-Healing** → **"Health History"**
2. See trend graphs:
   - Health score over time
   - Issue count trend
   - Auto-healing action frequency

---

## Best Practices

### 1. Start Conservative

```
Week 1: Review dashboard only
         ↓
Week 2: Approve some low-risk recommendations
         ↓
Week 3: Enable self-healing in dry-run mode
         ↓
Week 4: Enable self-healing for dev/test only
         ↓
Month 2: Gradually expand to production
```

### 2. Validate Recommendations Before Applying

**Always check:**
- ✅ Confidence score >75% for critical changes
- ✅ Estimated savings make sense
- ✅ No dependent clusters/jobs
- ✅ Safe time to make change (off-peak)
- ✅ Rollback plan if something fails

### 3. Use Hybrid Approach

```
Manual Approval FOR:
- Production clusters
- >$500/month cost impact
- Critical workloads

Self-Healing FOR:
- Dev/test clusters
- Routine idle cleanup
- Small auto-scaling
```

### 4. Monitor Regularly

**Daily:**
- Check dashboard for new recommendations
- Review any alerts

**Weekly:**
- Review approval history
- Check if recommended savings were realized
- Validate cluster health metrics

**Monthly:**
- Analyze trends in recommendations
- Adjust self-healing configuration if needed
- Review cost savings achieved

### 5. Set Up Notifications

Configure alerts for:
- New high-confidence recommendations
- Self-healing action failures
- Clusters entering critical health
- Cost threshold exceeded

### 6. Exclude Sensitive Clusters

Always protect:
- Production clusters (until confident)
- Long-running ML training jobs
- Scheduled ETL pipelines
- Critical batch processes

### 7. Test Before Production

For any new recommendation type:
1. Test on dev cluster first
2. Verify no side effects
3. Monitor for 1 week
4. Then apply to production

### 8. Document Your Decisions

For each significant action:
- Record why you approved/rejected
- Note any issues that occurred
- Update exclusion list if needed
- Share learnings with team

---

## Troubleshooting

### Common Issues and Solutions

#### Issue 1: "Backend Connection Error"

**Symptoms:** Can't connect to http://localhost:8000

**Solutions:**
1. Check backend is running:
   ```bash
   cd backend
   python main.py
   ```
2. Verify port 8000 is available:
   ```bash
   netstat -ano | findstr :8000
   ```
3. Check environment variables are set:
   ```bash
   echo %DATABRICKS_TOKEN%
   ```

#### Issue 2: "No Recommendations Generated"

**Symptoms:** Run Analysis but get no results

**Solutions:**
1. Verify Databricks credentials are valid
2. Check that workspace has clusters/jobs
3. Review backend logs for errors:
   ```
   Look for ERROR messages in console
   ```
4. Ensure Delta tables exist (if configured):
   ```sql
   SHOW TABLES IN default LIKE 'cluster%'
   ```

#### Issue 3: "Confidence Scores Too Low"

**Symptoms:** All recommendations show <60% confidence

**Solutions:**
1. This is normal for new/changing workloads
2. Run analysis again after 1-2 weeks
3. Check if Delta table logs are populated
4. Verify cluster metrics are being tracked

#### Issue 4: "Self-Healing Actions Keep Failing"

**Symptoms:** Auto-restart or termination fails repeatedly

**Solutions:**
1. Enable dry-run mode to debug
2. Check exclusion list - is cluster excluded?
3. Verify Databricks token has cluster management permissions
4. Check cluster logs in Databricks for root cause
5. Reduce `max_restart_attempts` if stuck in loop

#### Issue 5: "Analysis Takes Too Long"

**Symptoms:** Analysis runs for >5 minutes

**Solutions:**
1. Check network connection to Databricks
2. Verify Azure OpenAI is responding:
   - Test: `curl $AZURE_OPENAI_ENDPOINT`
3. If >100 clusters, analysis may take longer (normal)
4. Check backend logs for slow API calls
5. Consider running analysis during off-peak hours

#### Issue 6: "Estimated Savings Seem Wrong"

**Symptoms:** Savings calculations don't match expectations

**Solutions:**
1. Verify cost data in Databricks (check pricing)
2. Check cluster configuration (instance type, worker count)
3. Ensure Delta cost tables are populated
4. Review AI prompt in `backend/ai_agent.py`
5. Contact support with specific example

#### Issue 7: "Dashboard Shows No Clusters"

**Symptoms:** Cluster Statistics shows 0 clusters

**Solutions:**
1. Verify Databricks workspace is accessible
2. Check token has cluster list permissions:
   ```
   Required: clusters.list, clusters.get
   ```
3. Test API directly:
   ```bash
   curl -H "Authorization: Bearer $TOKEN" \
     $DATABRICKS_HOST/api/2.0/clusters/list
   ```
4. Ensure workspace actually has clusters

### Getting Help

**If issues persist:**

1. **Check logs:**
   - Backend: Console output from `python main.py`
   - Frontend: Browser developer tools (F12)
   
2. **Enable debug mode:**
   ```bash
   # In backend/.env
   DEBUG=True
   ```

3. **Check QA.md:**
   - Reference Q&A for architecture details
   
4. **Review configuration:**
   - Verify `.env` file is correct
   - Check Delta table schemas
   - Validate Databricks token permissions

---

## Advanced Tips

### Custom Prompts

Modify AI prompts in `backend/ai_agent.py` to:
- Focus on specific optimization areas
- Add business-specific constraints
- Adjust confidence thresholds
- Include custom cost models

### Extending Self-Healing

Add custom remediation actions in `backend/auto_remediation.py`:
- Custom health checks
- Additional remediation strategies
- Integration with incident management
- Custom notifications

### Performance Tuning

Optimize analysis speed:
1. Reduce cluster list query frequency
2. Cache job data between runs
3. Batch Delta table queries
4. Use parallel processing for large workspaces

### Integration with External Systems

Connect ClusterIQ to:
- Slack for notifications
- JIRA for ticket creation
- PagerDuty for incident management
- Custom monitoring tools

---

## Frequently Asked Questions (FAQ)

### 1. Does ClusterIQ read from Databricks Delta tables?

**Q:** How does ClusterIQ access cluster and performance data?

**A:** Yes, ClusterIQ reads from Databricks Delta tables to access historical metrics and event data:

- **cluster_events** - Records cluster state changes, start/stop events, autoscale actions
- **cluster_logs** - Contains timestamped performance metrics (CPU, memory, disk usage)
- **job_run_logs** - Stores job execution history with duration, status, and cost data

**How It Works:**
1. Delta tables store time-series data from your Databricks clusters
2. ClusterIQ queries these tables to build historical context
3. Trends are analyzed to identify patterns and optimization opportunities
4. Data is combined with real-time Databricks API data for complete picture

**Example Delta Query:**
```sql
SELECT cluster_id, timestamp, cpu_usage, memory_usage 
FROM cluster_logs 
WHERE timestamp > NOW() - INTERVAL 7 DAYS
ORDER BY timestamp DESC
```

**Benefits:**
- ✅ Access to historical performance trends (days/weeks)
- ✅ Identify recurring patterns and anomalies
- ✅ Calculate cost trends over time
- ✅ Correlate events with performance changes

---

### 2. Does ClusterIQ show clusters and jobs using API?

**Q:** How does ClusterIQ display real-time cluster and job information?

**A:** Yes, ClusterIQ uses Databricks REST APIs to fetch real-time data:

**Cluster Information (API Endpoints Used):**
- `GET /api/2.0/clusters/list` - Lists all clusters with current state
- `GET /api/2.0/clusters/get` - Gets detailed cluster configuration
- `GET /api/2.0/clusters/spark-versions` - Available Spark versions

**Job Information (API Endpoints Used):**
- `GET /api/2.0/jobs/list` - Lists all jobs in workspace
- `GET /api/2.0/jobs/get` - Gets specific job details
- `GET /api/2.0/jobs/runs/list` - Lists recent job runs

**What's Displayed:**
- Cluster state (running, terminated, pending, restarting)
- Number of nodes and node type
- Current CPU/memory utilization
- Estimated hourly cost
- Last activity timestamp
- Job execution history and status

**Real-Time vs Historical:**
```
Real-Time (API) + Historical (Delta Tables) = Complete Picture
├─ Current state (running/stopped)
├─ Configuration details
├─ Recent activity (last 24h)
└─ Historical trends (days/weeks)
```

**Code Pattern:**
```python
# Backend fetches via API
clusters = databricks_client.get_all_clusters()  # Real-time API call
# Then enriches with Delta data
historical_data = delta_client.query_cluster_logs(cluster_id)
# Combines both for analysis
```

---

### 3. Does ClusterIQ use GenAI to read metrics from Delta tables?

**Q:** How does ClusterIQ interpret and analyze cluster data?

**A:** Yes, ClusterIQ uses Azure OpenAI (ClusterIQGPT) to analyze metrics and generate insights:

**How It Works:**

1. **Data Collection Phase**
   - Fetches real-time data from Databricks API
   - Queries historical data from Delta tables
   - Calculates derived metrics (cost, utilization, efficiency)

2. **AI Analysis Phase**
   - Sends structured data to Azure OpenAI (GPT-4)
   - LangChain framework handles prompt engineering
   - AI analyzes patterns and anomalies
   - Generates human-readable insights

3. **Recommendation Generation**
   - AI identifies optimization opportunities
   - Assigns confidence scores (0-100%)
   - Estimates cost savings potential
   - Creates actionable recommendations

**Example Analysis Flow:**
```
Raw Data (CPU %, Memory %, Job Duration)
          ↓
        [AI Analysis]
          ↓
Insight: "Cluster X has 15% avg CPU, but runs 24/7"
Recommendation: "Auto-scale or terminate idle periods = $500/month savings"
```

**AI Capabilities:**
- ✅ Identify underutilized clusters
- ✅ Detect cost optimization opportunities
- ✅ Find performance bottlenecks
- ✅ Suggest right-sizing actions
- ✅ Estimate accuracy of recommendations
- ✅ Provide business impact analysis

**Configuration:**
```python
# backend/config.py
AZURE_OPENAI_ENDPOINT = "https://your-resource.openai.azure.com/"
AZURE_OPENAI_DEPLOYMENT_NAME = "ClusterIQGPT"  # Usually GPT-4
```

---

### 4. Are all recommendations coming from certain prompt?

**Q:** How does ClusterIQ generate recommendations? Is it rule-based or AI-based?

**A:** All recommendations are generated from carefully engineered prompts sent to Azure OpenAI:

**Recommendation Generation Process:**

1. **Data Preparation**
   ```python
   analysis_context = {
       "clusters": [...],  # Real-time data
       "metrics": {...},   # Historical aggregates
       "anomalies": [...], # Detected issues
       "cost_analysis": {...}  # Cost calculations
   }
   ```

2. **Prompt Engineering**
   ```
   The prompt includes:
   - Cluster statistics and performance data
   - Cost breakdown by cluster
   - Utilization patterns
   - Failure/restart history
   - Job execution efficiency
   
   The prompt asks AI to:
   - Identify which clusters are inefficient
   - Suggest specific actions (resize, terminate, auto-scale)
   - Estimate cost savings
   - Assess confidence in recommendation
   - Explain reasoning to user
   ```

3. **AI Processing**
   - Azure OpenAI (ClusterIQGPT) analyzes the prompt
   - Generates recommendations based on:
     * Industry best practices
     * Databricks optimization patterns
     * Cost optimization strategies
     * Your specific cluster data

4. **Recommendation Output**
   ```json
   {
     "recommendation": "Reduce instance size from i3en.24xlarge to i3en.3xlarge",
     "cluster_id": "1201-205507-test123",
     "reason": "Cluster maintains 18% avg CPU - smaller instance would save $1200/month",
     "estimated_savings": 1200,
     "confidence": 85,
     "action": "resize_cluster"
   }
   ```

**Key Points:**
- ✅ Prompts are data-driven (not hardcoded rules)
- ✅ AI learns from your cluster patterns
- ✅ Recommendations include confidence scores
- ✅ Savings are estimated from actual usage
- ✅ Each recommendation has explainability

**Customization:**
You can modify prompts in `backend/ai_agent.py` to:
- Focus on specific optimization areas
- Add business constraints
- Adjust confidence thresholds
- Include custom metrics

---

### 5. How is it different when self-healing vs manual approval?

**Q:** What's the difference between self-healing (automatic) and manual approval workflows?

**A:** Here's a detailed comparison:

| Aspect | Manual Approval | Self-Healing |
|--------|-----------------|--------------|
| **Approval** | Human reviews & approves | Automatic (no human) |
| **Speed** | Delayed (hours/days) | Immediate (seconds) |
| **Action Timing** | After human approves | When trigger condition met |
| **Risk** | Lower (human oversight) | Higher (automatic) |
| **Scale** | Works for few clusters | Works for many clusters |
| **Compliance** | Easier to audit | Harder to track |
| **Customization** | Per-action decisions | Pre-configured rules |
| **Labor** | High (human reviews) | Low (fully automated) |
| **Learning** | Humans make decisions | Fixed rules applied |

**Manual Approval Workflow:**
```
1. Analysis runs (scheduled daily)
2. AI generates recommendations
3. Notification sent to DevOps team
4. Human reviews recommendation
   - Checks if it makes sense
   - Verifies cluster importance
   - Reviews business impact
5. Human clicks "Approve"
6. Action executed (restart, resize, terminate)
7. Monitoring for side effects
```

**Self-Healing Workflow:**
```
1. Health check runs (every 5 minutes)
2. Condition detected (e.g., OOM error)
3. Automatic action triggered (e.g., restart)
4. Action executed immediately
5. Status logged to approval store
6. Alert sent to team (for info only)
```

**Example Scenario - Restarting Failed Cluster:**

**Manual Approach:**
```
09:00 - Cluster crashes
09:05 - Alert sent to on-call engineer
09:15 - Engineer investigates
09:20 - Engineer approves restart
09:21 - Cluster restart begins
09:30 - Cluster back online (30 min downtime)
```

**Self-Healing Approach:**
```
09:00 - Cluster crashes
09:01 - Health check detects failure
09:02 - Auto-restart triggered
09:12 - Cluster back online (12 min downtime)
```

**When to Use Each:**

**Manual Approval is Better For:**
- Critical production clusters
- High-risk actions (data-destructive)
- Environments requiring audit trails
- Teams preferring human oversight
- Learning/training phases

**Self-Healing is Better For:**
- Dev/test environments
- Non-critical clusters
- Common, low-risk issues
- 24/7 operations (no on-call)
- Cost optimization actions

**Hybrid Approach (Recommended):**
```
├─ Self-Healing Enabled
│  ├─ Restart failed clusters
│  ├─ Scale down underutilized
│  └─ Terminate idle (after 4h)
│
└─ Manual Approval Required
   ├─ Terminate cluster (irreversible)
   ├─ Resize to smaller instance
   └─ Change security settings
```

---

### 6. How risky is it to use self-healing without human in loop?

**Q:** What are the risks of automatic self-healing and how can we mitigate them?

**A:** Self-healing is powerful but carries risks. Here's the complete risk assessment:

**Risk Categories:**

**1. Data Loss Risks** ⚠️ HIGH
- **Risk:** Cluster termination = data loss if not persisted
- **Example:** Temp data on cluster storage lost
- **Mitigation:**
  - Always use Delta Lake for persistent storage
  - Never rely on cluster storage for important data
  - Implement job status checks before termination
  - Configure approval gates for termination actions

**2. Job Failure Risks** ⚠️ MEDIUM-HIGH
- **Risk:** Restart/terminate during job execution kills the job
- **Example:** Long-running ETL job terminated mid-process
- **Mitigation:**
  - Check active jobs before restarting
  - Use job dependency tracking
  - Implement gradual shutdown (graceful termination)
  - Monitor job health metrics
  - Set minimum job duration thresholds

**3. Cascade Failures** ⚠️ MEDIUM
- **Risk:** Automatic actions trigger additional failures
- **Example:** Restart cluster → auto-scale up → out of quota → failure
- **Mitigation:**
  - Implement safety checks (quota, limits)
  - Add action delays between retries
  - Track recent action history
  - Implement circuit breaker pattern
  - Set max retry limits

**4. Compliance & Audit Risks** ⚠️ MEDIUM
- **Risk:** Automatic actions hard to audit and explain
- **Example:** Terminated cluster breaks compliance requirements
- **Mitigation:**
  - Log all actions with timestamps
  - Maintain detailed audit trail
  - Store before/after cluster state
  - Require approval for certain actions
  - Regular compliance reviews

**5. Configuration Errors** ⚠️ MEDIUM
- **Risk:** Self-healing rules configured incorrectly
- **Example:** All clusters terminated due to overly broad rule
- **Mitigation:**
  - Test rules in dry-run mode first
  - Use cluster tags for exemptions
  - Implement allowlist of clusters
  - Gradually expand self-healing scope
  - Monitor action side effects

**Risk Mitigation Strategy:**

**Phase 1: Start Conservative** (Week 1-2)
```
✅ SAFE ACTIONS (Enable First)
├─ Restart failed clusters (low-risk)
├─ Scale down overprovisioned (easy to reverse)
└─ Restart after scheduled maintenance

❌ RISKY ACTIONS (Enable Later)
├─ Terminate clusters (data loss)
├─ Resize to smaller instances (capacity changes)
└─ Auto-terminate idle (jobs might be pending)
```

**Phase 2: Validate & Monitor** (Week 3-4)
```
1. Monitor self-healing actions for 2 weeks
2. Verify job success rates unchanged
3. Check data integrity
4. Review audit logs
5. Get team approval before expanding
```

**Phase 3: Gradual Expansion** (Week 5+)
```
1. Enable riskier actions one at a time
2. Implement approval gates for dangerous actions
3. Use cluster tags to control scope
4. Maintain manual override capability
5. Continue monitoring metrics
```

**Configuration for Risk Mitigation:**

```yaml
# backend/config.py - Self-Healing Rules

SELF_HEALING_CONFIG = {
    "enabled": True,
    
    # Low-risk actions (always enabled)
    "restart_failed": {
        "enabled": True,
        "max_retries": 2,
        "retry_delay_minutes": 5,
        "approval_required": False,
        "notify_team": True
    },
    
    # Medium-risk actions (require monitoring)
    "scale_down": {
        "enabled": True,
        "approval_required": True,  # ← Human approval
        "exempted_clusters": ["prod-cluster-1"],
        "min_scale_down_percentage": 30,
        "notify_team": True
    },
    
    # High-risk actions (rarely auto-execute)
    "terminate_cluster": {
        "enabled": False,  # ← Disabled by default
        "approval_required": True,
        "exempted_clusters": ["*"],  # ← Exempt everything
        "notify_team": True,
        "safety_checks": [
            "no_active_jobs",
            "no_data_in_ephemeral_storage"
        ]
    }
}
```

**Best Practices for Safe Self-Healing:**

1. **Start Small**
   - Enable for non-critical clusters first
   - Test thoroughly before production
   - Use dry-run mode initially

2. **Implement Safety Checks**
   ```python
   def safe_restart_cluster(cluster_id):
       # Check no long-running jobs
       if has_active_jobs(cluster_id):
           return False
       
       # Check quota available
       if not has_sufficient_quota():
           return False
       
       # Check recent restart count
       if recent_restarts_too_high():
           return False
       
       # Safe to proceed
       restart_cluster(cluster_id)
   ```

3. **Monitor & Alert**
   - Track all actions in real-time
   - Alert team to unusual patterns
   - Daily review of self-healing actions
   - Weekly analysis of impact

4. **Maintain Manual Override**
   - Always allow stopping self-healing
   - Provide quick rollback capability
   - Keep human-in-loop for critical actions
   - Test manual recovery procedures

5. **Regular Audits**
   - Review self-healing decisions
   - Validate business impact
   - Check compliance requirements
   - Adjust rules based on learnings

**Risk Score Matrix:**

```
RISK LEVEL    | ACTION TYPE           | APPROVAL | AUTO-ENABLED
Low (1-2)     | Restart failed        | Optional | Yes
Medium (3-5)  | Scale down            | Required | Yes (monitored)
Medium (3-5)  | Auto-scale             | Required | Yes (limited)
High (6-8)    | Terminate cluster     | Required | No
High (6-8)    | Resize (smaller)      | Required | No
Critical (9+) | Datastore modification| Manual   | No
```

**Incident Response Plan:**

If something goes wrong:
```
1. Immediately disable self-healing
2. Assess impact (data loss, failed jobs)
3. Recover from backups if needed
4. Root cause analysis
5. Update configuration based on learnings
6. Get team sign-off before re-enabling
```

**Recommended Setup for Most Teams:**

```
Phase 1: Only auto-restart failed clusters
Phase 2: Add auto-scale down (with approval gate)
Phase 3: Add other low-risk actions
Phase 4: Revisit high-risk actions annually

Avoid self-healing for:
- Production-critical clusters
- Clusters with real-time job processing
- Compliance-sensitive environments
- Until team is fully confident
```

---

## Summary

**ClusterIQ Workflow:**
```
Run Analysis
     ↓
Review Recommendations (AI-generated)
     ↓
Approve/Reject
     ↓
Apply Actions (Manual or Self-Heal)
     ↓
Monitor Results
     ↓
Achieve Cost Savings + Performance Improvements
```

**Key Principle:** Start conservative, validate, then expand automation gradually.

**Success Metrics:**
- ✅ Cost savings 30-50%
- ✅ Reduced manual cluster management
- ✅ Improved cluster health
- ✅ Faster response to issues
- ✅ Data-driven decisions

---

**Last Updated:** February 8, 2026  
**ClusterIQ Version:** 1.0.0  
**For additional details, see QA.md**
