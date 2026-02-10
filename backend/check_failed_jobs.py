"""Quick script to check for failed job runs"""
import os
import sys
from dotenv import load_dotenv
from databricks_client import DatabricksClient

load_dotenv()

client = DatabricksClient(
    os.getenv('DATABRICKS_HOST'),
    os.getenv('DATABRICKS_TOKEN')
)

print("Fetching jobs...")
jobs = client.get_all_jobs()
print(f"Total jobs: {len(jobs)}\n")

failed_found = False
for i, job in enumerate(jobs[:10]):  # Check first 10 jobs
    job_id = job.get('job_id')
    job_name = job.get('job_name', 'Unknown')
    print(f"{i+1}. Job {job_id}: {job_name}")
    
    try:
        runs_response = client.get_job_runs(job_id, limit=5)
        runs = runs_response if isinstance(runs_response, list) else runs_response.get('runs', [])
        
        if runs:
            for run in runs:
                state = run.get('state', {})
                life_cycle = state.get('life_cycle_state', '')
                result = state.get('result_state', '')
                message = state.get('state_message', '')
                run_id = run.get('run_id')
                
                if result in ['FAILED', 'TIMEDOUT', 'CANCELED']:
                    failed_found = True
                    print(f"   ⚠️  Run {run_id}: {life_cycle} / {result}")
                    print(f"      Message: {message[:100]}...")
                    print(f"      End time: {run.get('end_time')}")
                elif result == 'SUCCESS':
                    print(f"   ✓ Run {run_id}: {result}")
                else:
                    print(f"   • Run {run_id}: {life_cycle} / {result or 'N/A'}")
        else:
            print("   No runs found")
    except Exception as e:
        print(f"   Error: {e}")
    print()

if not failed_found:
    print("\n❌ No failed jobs found in recent runs")
else:
    print("\n✅ Found failed jobs - they should appear in recommendations")
