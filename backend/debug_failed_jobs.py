#!/usr/bin/env python3
"""Debug why failed jobs aren't being restarted."""
import os
import sys
import time
from dotenv import load_dotenv

sys.path.insert(0, '.')
from databricks_client import DatabricksClient

load_dotenv()
client = DatabricksClient(host=os.getenv('DATABRICKS_HOST'), token=os.getenv('DATABRICKS_TOKEN'))

print("\n" + "=" * 120)
print("DEBUG: FAILED JOB DETECTION")
print("=" * 120)

try:
    jobs = client.get_all_jobs()
    print(f"\nTotal jobs: {len(jobs)}\n")
    
    failed_jobs_found = 0
    
    for job in jobs:
        job_id = job.get("job_id")
        job_name = job.get("settings", {}).get("name") or job.get("job_name", "Unknown")
        
        print(f"\nJob {job_id}: {job_name}")
        
        try:
            # Get recent runs
            runs_response = client.get_job_runs(job_id, limit=5)
            
            if isinstance(runs_response, dict):
                if runs_response.get("status") != "success":
                    print(f"   ERROR: Failed to get runs: {runs_response.get('error', 'Unknown')}")
                    continue
                runs = runs_response.get("runs", [])
            else:
                runs = runs_response or []
            
            if not runs:
                print(f"   No runs found for this job")
                continue
            
            print(f"   Found {len(runs)} recent runs:")
            
            for run in runs:
                run_id = run.get("run_id")
                state = run.get("state", {})
                result_state = state.get("result_state", "")
                life_cycle = state.get("life_cycle_state", "")
                end_time = run.get("end_time")
                
                print(f"\n      Run {run_id}")
                print(f"        Result State: {result_state or 'EMPTY'}")
                print(f"        Lifecycle: {life_cycle or 'EMPTY'}")
                
                # Check if it matches restart criteria
                is_failed = result_state in ["FAILED", "TIMEDOUT"]
                is_internal_error = result_state == "" and life_cycle == "INTERNAL_ERROR"
                
                if is_failed or is_internal_error:
                    print(f"        MATCHES RESTART CRITERIA")
                    
                    # Check age
                    if end_time:
                        failure_age_minutes = (int(time.time() * 1000) - end_time) / 1000 / 60
                        days_ago = failure_age_minutes / 60 / 24
                        print(f"        Failed {failure_age_minutes:.1f} minutes ago ({days_ago:.1f} days ago)")
                        
                        if failure_age_minutes > 10080:  # 7 days
                            print(f"        TOO OLD FOR RESTART (> 7 days)")
                        else:
                            print(f"        WITHIN RESTART WINDOW (< 7 days)")
                            failed_jobs_found += 1
                    else:
                        print(f"        No end_time available")
                else:
                    print(f"        Does not match restart criteria")
        
        except Exception as e:
            print(f"   ERROR: {str(e)}")
    
    print(f"\n" + "=" * 120)
    print(f"RESULT: Found {failed_jobs_found} jobs eligible for restart")
    print("=" * 120 + "\n")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

