#!/usr/bin/env python3
"""Get full error details for all jobs."""
import os
import sys
import json
from dotenv import load_dotenv
from databricks_client import DatabricksClient

load_dotenv()
client = DatabricksClient(host=os.getenv('DATABRICKS_HOST'), token=os.getenv('DATABRICKS_TOKEN'))

try:
    jobs = client.get_all_jobs()
    
    for j in jobs:
        job_id = j.get('job_id')
        print(f'\n{"=" * 120}')
        print(f'JOB ID: {job_id}')
        print(f'{"=" * 120}')
        
        # Get recent runs
        try:
            runs = client.get_job_runs(job_id, limit=5)
            if isinstance(runs, dict):
                runs_list = runs.get('runs', [])
            else:
                runs_list = runs or []
            
            for idx, run in enumerate(runs_list, 1):
                run_id = run.get('run_id')
                state = run.get('state', {})
                result_state = state.get('result_state', 'UNKNOWN')
                state_msg = state.get('state_message', 'No message')
                start_time = run.get('start_time')
                end_time = run.get('end_time')
                
                # Convert timestamps to readable format
                from datetime import datetime
                start = datetime.fromtimestamp(start_time/1000) if start_time else 'N/A'
                end = datetime.fromtimestamp(end_time/1000) if end_time else 'N/A'
                
                print(f'\n  Run #{idx}: {run_id}')
                print(f'  Result State: {result_state}')
                print(f'  Start Time: {start}')
                print(f'  End Time: {end}')
                print(f'  Error Message:')
                print(f'  {"-" * 116}')
                print(f'  {state_msg}')
                print(f'  {"-" * 116}')
        except Exception as e:
            print(f'  Error fetching runs: {str(e)}')
    
    print(f'\n{"=" * 120}\n')
    
except Exception as e:
    print(f'❌ Error: {str(e)}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
