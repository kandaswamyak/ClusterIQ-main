"""Test execution error detection directly"""
import os
import sys
from dotenv import load_dotenv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup
load_dotenv()
from databricks_client import DatabricksClient

client = DatabricksClient(
   os.getenv('DATABRICKS_HOST'),
    os.getenv('DATABRICKS_TOKEN')
)

print("=== Testing Execution Error Detection ===\n")

# Get jobs
jobs = client.get_all_jobs()
print(f"Total jobs: {len(jobs)}\n")

# Find Code_Optimise
code_job = None
for job in jobs:
    if job.get('job_id') == 130082990215176 or job.get('job_name') == 'Code_Optimise':
        code_job = job
        break

if not code_job:
    print("✗ Code_Optimise not found in jobs list!")
    sys.exit(1)

print(f"✓ Found Code_Optimise: {code_job.get('job_name')}")
print(f"  Job ID: {code_job.get('job_id')}\n")

# Get runs
job_id = code_job.get('job_id')
runs_response = client.get_job_runs(job_id, limit=5)

print(f"Runs response type: {type(runs_response)}")

if isinstance(runs_response, dict):
    status = runs_response.get('status')
    print(f"Status field: {status}")
    if status and status != 'success':
        print("⚠️ THIS IS THE PROBLEM - status != 'success' would skip the job!")
    runs = runs_response.get('runs', [])
else:
    runs = runs_response or []
    print(f"✓ Response is list, will use directly")

print(f"\nRuns found: {len(runs)}\n")

# Check each run
for run in runs:
    run_id = run.get('run_id')
    state = run.get('state', {})
    result_state = state.get('result_state')
    life_cycle = state.get('life_cycle_state')
    message = state.get('state_message', '')
    cluster_instance = run.get('cluster_instance')
    
    print(f"Run {run_id}:")
    print(f"  Lifecycle: {life_cycle}")
    print(f"  Result: {result_state}")
    print(f"  Cluster Instance: {cluster_instance}")
    
    if result_state in ['FAILED', 'TIMEDOUT']:
        print(f"  ✓✓✓ SHOULD CREATE RECOMMENDATION! ✓✓✓")
        
        # Test the fix
        cluster_inst_fixed = cluster_instance or {}
        cluster_id = cluster_inst_fixed.get('cluster_id', 'unknown')
        print(f"  Cluster ID (fixed): {cluster_id}")
        print(f"  This WILL work with the fix!")
    else:
        print(f"  ✗ Not failed")
    print()

print("\n=== Importing and testing the actual function ===\n")

# Now test the actual function
from main import generate_execution_error_recommendations

recommendations = generate_execution_error_recommendations(jobs)

print(f"\nRecommendations generated: {len(recommendations)}")

if recommendations:
    print("\n✓✓✓ SUCCESS! ✓✓✓\n")
    for rec in recommendations:
        print(f"ID: {rec.get('id')}")
        print(f"Job: {rec.get('resource_name')}")
        print(f"Type: {rec.get('type')}")
        print(f"Run ID: {rec.get('details', {}).get('run_id')}")
        print()
else:
    print("\n✗ NO RECOMMENDATIONS - something is still wrong!")
