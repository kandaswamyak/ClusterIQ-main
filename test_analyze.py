#!/usr/bin/env python3
import requests
import sys

try:
    print("Testing /api/analyze endpoint...")
    r = requests.post('http://localhost:8000/api/analyze', timeout=65)
    print(f'Status: {r.status_code}')
    data = r.json()
    recs = data['summary']['recommendations_count']
    atype = data['summary']['analysis_type']
    print(f'Recommendations: {recs}')
    print(f'Analysis Type: {atype}')
    print("✓ Analyze endpoint working!")
    sys.exit(0)
except Exception as e:
    print(f'✗ Error: {str(e)}')
    sys.exit(1)
