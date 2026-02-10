"""Force detection of Code_Optimise failed job"""
import os
import sys
from dotenv import load_dotenv
from databricks_client import DatabricksClient

load_dotenv()

client = DatabricksClient(
    os.getenv('DATABRICKS_HOST'),
    os.getenv('DATABRICKS_TOKEN')
)

job_id = '130082990215176'
print(f"=== Checking Code_Optimise (Job ID: {job_id}) ===\n")

# Get runs
runs_response = client.get_job_runs(job_id, limit=5)
print(f"Response type: {type(runs_response)}")
print(f"Response: {runs_response}\n")

# Check if it's a dict with status
if isinstance(runs_response, dict):
    status = runs_response.get('status')
    print(f"Status field: {status}")
    if status and status != 'success':
        print("⚠️ Status is not 'success' - this would skip the job!")
        print("This is why the job isn't being detected!\n")
    
    runs = runs_response.get('runs', [])
else:
    runs = runs_response or []

print(f"\nRuns found: {len(runs)}\n")

for run in runs:
    run_id = run.get('run_id')
    state = run.get('state', {})
    result_state = state.get('result_state')
    life_cycle = state.get('life_cycle_state')
    message = state.get('state_message', '')
    
    print(f"Run {run_id}:")
    print(f"  Lifecycle: {life_cycle}")
    print(f"  Result: {result_state}")
    print(f"  Message: {message[:100]}...")
    
    if result_state in ['FAILED', 'TIMEDOUT']:
        print(f"  ✓ This SHOULD create execution_error recommendation!")
    else:
        print(f"  ✗ Not FAILED/TIMEDOUT, won't create recommendation")
    print()
