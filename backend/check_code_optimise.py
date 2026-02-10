"""Check Code_Optimise job runs"""
import os
from dotenv import load_dotenv
from databricks_client import DatabricksClient

load_dotenv()

client = DatabricksClient(
    os.getenv('DATABRICKS_HOST'),
    os.getenv('DATABRICKS_TOKEN')
)

job_id = '130082990215176'
print(f"Checking runs for Code_Optimise (Job ID: {job_id})\n")

try:
    response = client.get_job_runs(job_id, limit=10)
    runs = response if isinstance(response, list) else response.get('runs', [])
    
    print(f"Total runs found: {len(runs)}\n")
    
    failed_runs = []
    for i, run in enumerate(runs):
        run_id = run.get('run_id')
        state = run.get('state', {})
        life_cycle = state.get('life_cycle_state', 'UNKNOWN')
        result = state.get('result_state', 'N/A')
        message = state.get('state_message', '')
        start_time = run.get('start_time')
        end_time = run.get('end_time', 'Still running')
        
        status_icon = "✓" if result == "SUCCESS" else ("⚠️" if result == "FAILED" else "•")
        print(f"{status_icon} Run {i+1}: ID {run_id}")
        print(f"   State: {life_cycle} / {result}")
        print(f"   Start: {start_time}, End: {end_time}")
        
        if result == "FAILED":
            failed_runs.append(run)
            print(f"   ❌ FAILED! Message: {message[:150]}...")
        elif message:
            print(f"   Message: {message[:100]}...")
        print()
    
    if failed_runs:
        print(f"\n✓ Found {len(failed_runs)} failed run(s) that AI can heal!")
        print("\nAI Auto-Healing will:")
        print("1. Detect these failures")
        print("2. Analyze the error")
        print("3. Generate and apply fix")
        print("4. Restart the job")
    else:
        print("\nNo FAILED runs found yet.")
        print("If screenshot shows FAILED status, wait for Databricks to finish updating.")
        
except Exception as e:
    print(f"Error: {e}")
