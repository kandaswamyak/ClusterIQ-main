#!/usr/bin/env python3
"""Check current jobs in Databricks."""
import os
import sys
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
    
    print('Job Details:')
    print('-' * 100)
    for j in jobs:
        job_id = j.get('job_id')
        job_name = j.get('settings', {}).get('name', 'N/A')
        print(f'  ID: {job_id:20} | Name: {job_name}')
    
    print('-' * 100)
    print(f'\nTotal: {len(jobs)} jobs\n')
    
except Exception as e:
    print(f'❌ Error: {str(e)}')
    sys.exit(1)
