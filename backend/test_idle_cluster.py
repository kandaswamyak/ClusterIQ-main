#!/usr/bin/env python
"""Test idle_cluster recommendation generation and storage."""
import sys
sys.path.insert(0, '.')
import json
from simple_server import perform_basic_analysis
from approval_store import add_recommendations, list_recommendations

# Mock data
mock_jobs = []
mock_clusters = [
    {
        "cluster_id": "cluster-1",
        "cluster_name": "test-cluster-1",
        "state": "RUNNING",
        "num_workers": 2,
        "autotermination_minutes": 15
    },
    {
        "cluster_id": "cluster-2",
        "cluster_name": "test-cluster-2",
        "state": "RUNNING",
        "num_workers": 0,
        "autotermination_minutes": None
    }
]

print("=" * 60)
print("Testing idle_cluster recommendation generation...")
print("=" * 60)

# Generate recommendations
print("\n1. Generating recommendations...")
recs = perform_basic_analysis(mock_jobs, mock_clusters)
print(f"   Generated {len(recs)} recommendations")

# Filter idle_cluster recs
idle_recs = [r for r in recs if r.get("type") == "idle_cluster"]
print(f"   Found {len(idle_recs)} idle_cluster recommendations")

if idle_recs:
    print("\n   Idle cluster recommendations:")
    for rec in idle_recs:
        print(f"   - {rec.get('id')}: {rec.get('title')}")
        print(f"     Type: {rec.get('type')}")
        print(f"     Action: {rec.get('action')}")
        print(f"     Created: {rec.get('created_at')}")
else:
    print("   ⚠️  No idle_cluster recommendations found!")

# Store recommendations
print("\n2. Storing recommendations...")
try:
    add_recommendations(recs)
    print("   ✓ Recommendations stored")
except Exception as e:
    print(f"   ✗ Error storing: {e}")

# Retrieve from store
print("\n3. Retrieving from approval store...")
all_stored = list_recommendations(status=None)
print(f"   Total stored: {len(all_stored)}")

stored_idle = [r for r in all_stored if r.get("type") == "idle_cluster"]
print(f"   Idle cluster stored: {len(stored_idle)}")

if stored_idle:
    print("\n   Stored idle cluster recommendations:")
    for rec in stored_idle:
        print(f"   - {rec.get('id')}: {rec.get('title')}")
        print(f"     Status: {rec.get('status')}")
        print(f"     Created: {rec.get('created_at')}")

# Retrieve PENDING recommendations
print("\n4. Retrieving PENDING recommendations...")
pending = list_recommendations(status="PENDING")
print(f"   Total PENDING: {len(pending)}")

pending_idle = [r for r in pending if r.get("type") == "idle_cluster"]
print(f"   Idle cluster PENDING: {len(pending_idle)}")

if not pending_idle:
    print("   ⚠️  No idle_cluster in PENDING status!")

print("\n" + "=" * 60)
