#!/usr/bin/env python3
"""Check current jobs with full details including recent runs."""
import os
import sys
import json
from dotenv import load_dotenv
from databricks_client import DatabricksClient

load_dotenv()
client = DatabricksClient(host=os.getenv('DATABRICKS_HOST'), token=os.getenv('DATABRICKS_TOKEN'))

try:
    jobs = client.get_all_jobs()
    print(f'\n📊 Total jobs: {len(jobs)}\n')
    
    if not jobs:
        print('❌ No jobs found')
        sys.exit(0)
    
    print('=' * 120)
    for j in jobs:
        job_id = j.get('job_id')
        job_name = j.get('settings', {}).get('name', 'N/A')
        print(f'\n🔹 Job ID: {job_id}')
        print(f'   Name: {job_name}')
        
        # Get recent runs
        try:
            runs = client.get_job_runs(job_id, limit=3)
            if isinstance(runs, dict):
                runs_list = runs.get('runs', [])
            else:
                runs_list = runs or []
            
            if runs_list:
                print(f'   Recent Runs ({len(runs_list)}):')
                for run in runs_list:
                    run_id = run.get('run_id')
                    state = run.get('state', {})
                    result_state = state.get('result_state', 'UNKNOWN')
                    life_cycle_state = state.get('life_cycle_state', 'UNKNOWN')
                    state_msg = state.get('state_message', 'No message')
                    
                    print(f'     - Run {run_id}:')
                    print(f'       Result State: {result_state}')
                    print(f'       Lifecycle: {life_cycle_state}')
                    if state_msg:
                        # Show first 100 chars of error message
                        print(f'       Message: {state_msg[:100]}...')
            else:
                print(f'   No recent runs found')
        except Exception as e:
            print(f'   Error fetching runs: {str(e)[:100]}')
        
        print()
    
    print('=' * 120)
    print(f'\nTotal: {len(jobs)} jobs\n')
    
except Exception as e:
    print(f'❌ Error: {str(e)}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
