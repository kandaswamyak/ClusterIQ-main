#!/usr/bin/env python
"""Test the health check code directly"""
import sys
sys.path.insert(0, '.')
from databricks_client import get_databricks_client
from datetime import datetime
import json

try:
    print("Getting databricks client...")
    client = get_databricks_client()
    print("Got client, fetching clusters...")
    clusters = client.get_all_clusters()
    print(f"Got {len(clusters)} clusters")
    
    healthy = len([c for c in clusters if c.get("state") == "RUNNING"])
    unhealthy = len([c for c in clusters if c.get("state") in ["FAILED", "ERROR"]])
    total = len(clusters)
    
    result = {
        "success": True,
        "summary": {
            "total_clusters": total,
            "healthy": healthy,
            "unhealthy": unhealthy,
            "health_percentage": (healthy / total * 100) if total > 0 else 0
        },
        "clusters": [
            {
                "cluster_id": c.get("cluster_id"),
                "cluster_name": c.get("cluster_name"),
                "state": c.get("state"),
                "is_healthy": c.get("state") not in ["FAILED", "ERROR"]
            }
            for c in clusters[:3]  # Just first 3
        ],
        "timestamp": datetime.utcnow().isoformat()
    }
    
    print("Result:")
    print(json.dumps(result, indent=2))
except Exception as e:
    import traceback
    print(f"Error: {e}")
    traceback.print_exc()
