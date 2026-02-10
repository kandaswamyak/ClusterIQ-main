#!/usr/bin/env python3
"""Create recommendations for the test jobs."""
import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv

sys.path.insert(0, '.')
from approval_store import add_recommendations

# Recommendations for the test jobs
recommendations = [
    {
        "type": "execution_error",
        "resource_type": "job",
        "resource_id": "132309342588491",
        "resource_name": "Code Optimization Job",
        "title": "Code optimization job failed - Quota exceeded",
        "description": "The code_optimization task failed because the cluster was terminated due to Azure quota limits. The job needs optimization to reduce resource requirements OR Azure quota needs to be increased.",
        "severity": "high",
        "confidence_score": 0.95,
        "details": {
            "error": "AZURE_QUOTA_EXCEEDED_EXCEPTION",
            "task": "code_optimization",
            "reason": "VM size not available, insufficient cores quota",
            "action": "AI code analysis and optimization"
        }
    },
    {
        "type": "execution_error",
        "resource_type": "job",
        "resource_id": "338496054916121",
        "resource_name": "ClusterIQ Metrics Loader",
        "title": "Job failed - Can be restarted once quota is available",
        "description": "The ClusterIQ_Metrics_Loader_4Hours job failed due to Azure quota exceeded. The job will succeed once quota is restored. Auto-restart is recommended.",
        "severity": "high",
        "confidence_score": 0.95,
        "details": {
            "error": "AZURE_QUOTA_EXCEEDED_EXCEPTION",
            "task": "ClusterIQ_Metrics_Loader_4Hours",
            "reason": "Cluster terminated - quota limit exceeded",
            "action": "Auto-restart when quota is available"
        }
    }
]

try:
    # Add recommendations
    for rec in recommendations:
        add_recommendations([rec])
        print(f"✅ Created recommendation for {rec['resource_name']}")
        print(f"   Type: {rec['type']}")
        print(f"   Severity: {rec['severity']}")
        print()
    
    print("=" * 100)
    print(f"✅ All recommendations created successfully")
    print("=" * 100)
    
except Exception as e:
    print(f"❌ Error creating recommendations: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
