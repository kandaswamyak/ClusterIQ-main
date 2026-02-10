#!/usr/bin/env python3
"""Test auto-restart for failed jobs."""
import os
import sys
import json
import requests
from dotenv import load_dotenv

load_dotenv()

print("\n" + "=" * 100)
print("🧪 TESTING AUTO-RESTART FOR FAILED JOBS")
print("=" * 100)

# Call the run-self-healing endpoint
try:
    url = "http://localhost:8000/api/self-healing/run"
    
    print(f"\n📡 Calling: {url}")
    print("   This will trigger:")
    print("   ✓ Failed job detection")
    print("   ✓ AI analysis for code errors")
    print("   ✓ Auto-restart for failed jobs")
    print()
    
    response = requests.post(url, timeout=60)
    response.raise_for_status()
    
    result = response.json()
    
    print(f"\n✅ Response Status: {response.status_code}")
    print(f"\n📊 Results:")
    print(json.dumps(result, indent=2))
    
    # Parse and show summary
    summary = result.get('summary', {})
    print(f"\n📈 SUMMARY:")
    print(f"   Actions Taken: {summary.get('actions_taken', 0)}")
    print(f"   Failed Jobs Restarted: {summary.get('failed_jobs_restarted', 0)}")
    print(f"   Stuck Jobs Cancelled: {summary.get('stuck_jobs_cancelled', 0)}")
    print(f"   Failed Clusters: {summary.get('failed_clusters', 0)}")
    
    # Show actions taken
    actions = result.get('results', [])
    if actions:
        print(f"\n🎯 ACTIONS TAKEN ({len(actions)}):")
        for action in actions:
            print(f"\n   • {action.get('action')}")
            print(f"     Status: {action.get('status')}")
            print(f"     Message: {action.get('message')}")
            if action.get('note'):
                print(f"     Note: {action.get('note')}")
    else:
        print(f"\n⚠️  No actions taken")
    
    print("\n" + "=" * 100 + "\n")
    
except Exception as e:
    print(f"\n❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
