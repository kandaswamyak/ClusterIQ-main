#!/usr/bin/env python3
"""Dashboard: Show current test jobs and their status."""
import os
import sys
from dotenv import load_dotenv
sys.path.insert(0, '.')

from databricks_client import DatabricksClient
from approval_store import list_recommendations

load_dotenv()
client = DatabricksClient(host=os.getenv('DATABRICKS_HOST'), token=os.getenv('DATABRICKS_TOKEN'))

print("\n" + "=" * 120)
print("🚀 CLUSTERIQ SELF-HEALING TEST SETUP - DASHBOARD")
print("=" * 120)

try:
    # Get jobs
    jobs = client.get_all_jobs()
    job_map = {j.get('job_id'): j for j in jobs}
    
    # Get recommendations for our test jobs
    all_recs = list_recommendations()
    test_job_ids = [132309342588491, 338496054916121]
    test_recs = [r for r in all_recs if r.get('resource_id') in test_job_ids and r.get('status') == 'PENDING']
    
    print("\n📋 TEST JOBS SETUP:\n")
    
    for idx, rec in enumerate(test_recs, 1):
        job_id = rec.get('resource_id')
        job = job_map.get(job_id, {})
        
        print(f"{idx}. {rec.get('title')}")
        print(f"   Job ID: {job_id}")
        print(f"   Type: {rec.get('type')} (SEVERITY: {rec.get('severity').upper()})")
        print(f"   Description: {rec.get('description')}")
        
        # Get recent run
        try:
            runs_response = client.get_job_runs(job_id, limit=1)
            if isinstance(runs_response, dict):
                runs = runs_response.get('runs', [])
            else:
                runs = runs_response or []
            
            if runs:
                run = runs[0]
                state = run.get('state', {})
                result = state.get('result_state', 'UNKNOWN')
                error = state.get('state_message', 'No details')
                
                print(f"   Last Run Status: {result}")
                print(f"   Error: {error[:80]}...")
        except:
            pass
        
        if idx == 1:
            print(f"   🤖 Action on Run Self Healing:")
            print(f"      → Analyze error with AI")
            print(f"      → Generate code optimization recommendations")
        else:
            print(f"   🔄 Action on Run Self Healing:")
            print(f"      → Auto-restart failed job")
            print(f"      → Job will succeed once Azure quota is available")
        
        print()
    
    print("\n" + "=" * 120)
    print("✅ WHAT TO DO NEXT:")
    print("=" * 120)
    print("""
1. Open http://localhost:3000 in your browser
2. Go to "Self Healing" tab
3. You should see 2 job issues in the "Job Issues" section:
   - Code optimization job (URGENT) - requires code analysis
   - Metrics Loader job (high priority) - ready for auto-restart

4. Click "Run Healing Now" to:
   ✓ Analyze code optimization job with AI
   ✓ Auto-restart metrics loader job
   ✓ See detailed results with recommendations

Note: Both jobs are currently blocked by Azure quota limits.
Once quota is increased, the metrics loader will auto-restart and succeed.
""")
    print("=" * 120 + "\n")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
