# AI-Powered Auto-Healing Guide

## Overview
ClusterIQ now includes intelligent AI-powered auto-healing that can automatically detect, analyze, fix code errors, and restart failed jobs without manual intervention.

## How It Works

### 1. Error Detection
The system continuously monitors all Databricks jobs for execution errors:
- Failed job runs (FAILED, TIMEDOUT states)
- Execution errors (Python/PySpark errors)
- Resource-related failures

### 2. AI Code Analysis
When a code-related error is detected, the AI agent:
- Analyzes the error message
- Reads the current job code
- Identifies the root cause
- Generates a fixed version of the code

### 3. Automatic Code Fix
The system automatically:
- Creates a backup of the original code
- Applies the AI-generated fix to the local code file
- Logs all changes for audit purposes

### 4. Job Restart
After applying the fix (if applicable):
- Submits a new job run automatically
- Tracks the new run ID
- Monitors the result

## Supported Error Types

### Code Errors (AI Fix Applied)
- `ZeroDivisionError` - Division by zero
- `TypeError` - Type mismatches
- `ValueError` - Invalid values
- `NameError` - Undefined variables
- `AttributeError` - Missing attributes
- `KeyError` - Missing dictionary keys
- `IndexError` - List index out of range
- `SyntaxError` - Code syntax issues
- `IndentationError` - Indentation problems

### Other Errors (Simple Restart)
- Resource constraints
- Cluster issues
- Timeout errors
- Network errors

## File Structure

```
backend/
├── jobs/
│   ├── Code_Optimization.py        # Your job files
│   ├── Test_Error_Job.py           # Test job with errors
│   ├── Test_Error_Job_Fixed.py     # Example fixed version
│   └── *.py.backup_*               # Auto-generated backups
├── ai_agent.py                     # AI analysis engine
└── main.py                         # Auto-healing orchestration
```

## Testing the Flow

### Step 1: Create a Job with Errors
```python
# backend/jobs/Test_Error_Job.py
def process_data(data):
    result = 0
    for item in data:
        result += 100 / item  # Will fail when item = 0
    return result

test_data = [10, 5, 0, 2]  # Contains zero
result = process_data(test_data)
```

### Step 2: Run the Job in Databricks
1. Upload the file to Databricks workspace
2. Create a job pointing to this notebook
3. Run the job - it will fail with `ZeroDivisionError`

### Step 3: Auto-Healing Activates
1. System detects the failed run
2. Creates execution_error recommendation
3. AI analyzes the error
4. Generates fixed code:
```python
def process_data(data):
    result = 0
    for item in data:
        if item != 0:  # FIX: Check for zero
            result += 100 / item
        else:
            print("Warning: Skipping zero value")
    return result
```
5. Applies fix to local file
6. Restarts the job
7. New run succeeds

## Monitoring Auto-Healing

### Dashboard
- View execution error recommendations
- See AI fix confidence scores
- Track auto-healing success rate

### Logs
```
[AI AUTO-FIX] Starting auto-fix for job Test_Error_Job
[AI AUTO-FIX] Detected code error, attempting AI fix...
[AI AUTO-FIX] Found job code file: jobs/Test_Error_Job.py
[AI AUTO-FIX] ✓ Successfully applied AI fix
[AI AUTO-FIX] Root cause: Division by zero in process_data
[AI AUTO-FIX] Confidence: 0.92
[AI AUTO-FIX] ✓ Successfully submitted new run 12345
[AI AUTO-FIX] ✓ Job restarted with AI-generated code fix
```

### History
Check [SelfHealing.jsx](file:///c:/Users/akandaswamy4/Documents/clusteriq_selfheal/ClusterIQ-main/frontend/src/components/SelfHealing.jsx) tab:
- View all auto-healing actions
- See which jobs were fixed
- Review AI fix details and confidence scores

## Configuration

### Enable Self-Healing
```json
{
  "enabled": true,
  "dry_run": false,
  "auto_approve": true,
  "features": {
    "restart_failed_jobs": true,
    "ai_code_fixes": true
  }
}
```

### AI Configuration
- Uses Azure OpenAI or OpenAI
- Model: GPT-4 Turbo
- Minimum confidence threshold: 0.6 (60%)

## Best Practices

### 1. Job Naming Convention
Name your job files consistently:
- Use underscores: `Code_Optimization.py`
- Match job name in Databricks
- Store in `backend/jobs/` folder

### 2. Code Structure
- Use clear function names
- Add error handling
- Include comments
- Keep functions small and testable

### 3. Monitoring
- Check logs regularly
- Review AI fix confidence scores
- Validate fixed code before production
- Keep backups of original code

### 4. Testing
- Test with intentional errors
- Verify AI fixes work correctly
- Monitor job success rates
- Review auto-healing history

## Safety Features

### Automatic Backups
Every time AI applies a fix, it creates a backup:
```
jobs/Test_Error_Job.py.backup_20260210_143022
```

### Confidence Threshold
AI fixes are only applied if confidence > 0.6 (60%)

### Audit Trail
All auto-healing actions are logged with:
- Timestamp
- Job details
- Error message
- Fix applied
- Confidence score
- New run ID

## Troubleshooting

### AI Fix Not Applied
**Problem**: Job restarted but no AI fix applied
**Possible Causes**:
1. Error not code-related (e.g., resource issue)
2. Job code file not found locally
3. AI confidence too low
4. AI agent not configured

**Solution**:
- Check logs for `[AI AUTO-FIX]` messages
- Verify job file exists in `backend/jobs/`
- Ensure AI credentials configured

### Job Still Failing
**Problem**: Job fails again after AI fix
**Possible Causes**:
1. Complex error requiring manual fix
2. Multiple errors in code
3. Configuration issue

**Solution**:
- Review the backup file
- Check AI fix explanation
- Manually review and fix code
- Adjust job configuration

### Low Confidence Scores
**Problem**: AI reports low confidence (< 0.6)
**Possible Causes**:
1. Error message unclear
2. Complex code structure
3. Multiple possible fixes

**Solution**:
- Review error manually
- Simplify code structure
- Add better error messages to code

## Example Workflow

```
1. Job "Code_Optimization" fails
   ↓
2. System detects: ZeroDivisionError
   ↓
3. Creates recommendation: execution_error
   ↓
4. Self-healing triggers (if enabled)
   ↓
5. AI analyzes: "Division by zero at line 5"
   ↓
6. AI generates fix: Add zero check
   ↓
7. System applies fix to Code_Optimization.py
   ↓
8. Creates backup: Code_Optimization.py.backup_*
   ↓
9. Submits new job run
   ↓
10. Job succeeds ✓
```

## API Integration

### Recommendations Endpoint
```bash
GET /api/recommendations/real-time
```
Returns execution_error recommendations with AI fix details.

### Apply Endpoint
```bash
POST /api/approvals/{rec_id}/apply
```
Triggers auto-healing including AI fix and job restart.

### Self-Healing Status
```bash
GET /api/self-healing/config
```
Check if AI auto-fixing is enabled.

## Next Steps

1. ✅ Create test error file
2. ✅ Set up AI agent
3. ✅ Enable auto-healing
4. 🔄 Test the complete flow
5. 📊 Monitor results
6. 🎯 Refine based on success rate

## Support

For issues or questions:
1. Check logs in terminal
2. Review healing history in dashboard
3. Examine backup files
4. Verify AI configuration

---

**Note**: AI auto-fixing works best for common code errors. Complex issues may require manual intervention. Always review AI-generated fixes before deploying to production.
