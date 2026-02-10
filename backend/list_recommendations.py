#!/usr/bin/env python3
"""List all pending recommendations."""
import os
import sys
sys.path.insert(0, '.')

from approval_store import list_recommendations

try:
    all_recs = list_recommendations()
    pending = [r for r in all_recs if r.get('status') == 'PENDING']
    
    print(f'\n📊 Total Pending Recommendations: {len(pending)}\n')
    
    for rec in pending:
        print(f'📌 {rec.get("title")}')
        print(f'   Type: {rec.get("type")}')
        print(f'   Resource: {rec.get("resource_name")} (ID: {rec.get("resource_id")})')
        print(f'   Severity: {rec.get("severity")}')
        print(f'   Status: {rec.get("status")}')
        print()
    
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
