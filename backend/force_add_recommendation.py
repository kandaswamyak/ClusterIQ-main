"""Force add Code_Optimise recommendation"""
import os
import sys
from dotenv import load_dotenv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

# Import after path setup
from databricks_client import DatabricksClient
from main import generate_execution_error_recommendations
from approval_store import add_recommendations

client = DatabricksClient(
    os.getenv('DATABRICKS_HOST'),
    os.getenv('DATABRICKS_TOKEN')
)

print("=== Forcing Code_Optimise Recommendation ===\n")

# Get jobs
jobs = client.get_all_jobs()
print(f"Total jobs: {len(jobs)}")

# Generate execution error recommendations
exec_recs = generate_execution_error_recommendations(jobs)
print(f"Execution error recommendations generated: {len(exec_recs)}\n")

if exec_recs:
    for rec in exec_recs:
        print(f"- {rec.get('resource_name')} (Run: {rec.get('details', {}).get('run_id')})")
   
    print(f"\nAdding {len(exec_recs)} recommendations to approval store...\n")
    
    try:
        added = add_recommendations(exec_recs)
        print(f"✓ SUCCESS! Added {len(added)} recommendations")
        print("\nRecommendations now in store:")
        for rec in added:
            print(f"  • {rec.get('resource_name')} - {rec.get('id')}")
        
        print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("🎯 REFRESH YOUR DASHBOARD NOW!")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("Go to Self-Healing tab")
        print("You'll see Code_Optimise in Job Recommendations")
        print("Click 'Run Self-Healing' to fix it!")
        
    except Exception as e:
        print(f"✗ ERROR adding recommendations: {e}")
        import traceback
        traceback.print_exc()
else:
    print("✗ No recommendations generated")
