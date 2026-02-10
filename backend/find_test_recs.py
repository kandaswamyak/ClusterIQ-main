#!/usr/bin/env python3
"""List recommendations for test jobs."""
import sys
sys.path.insert(0, '.')
from approval_store import list_recommendations

all_recs = list_recommendations()
test_job_ids = ['132309342588491', '338496054916121', 132309342588491, 338496054916121]

print("\n🔍 Looking for recommendations for test jobs...")
print(f"   Job IDs: {test_job_ids}\n")

matching = []
for rec in all_recs:
    job_id = rec.get('resource_id')
    if job_id in test_job_ids and rec.get('status') == 'PENDING':
        matching.append(rec)
        print(f"✅ Found: {rec.get('title')}")
        print(f"   Type: {rec.get('type')}")
        print(f"   Resource ID: {job_id}")
        print(f"   Description: {rec.get('description')}")
        print()

print(f"\nTotal matching: {len(matching)}")
