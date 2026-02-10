#!/usr/bin/env python3
"""Test run_self_healing endpoint - detailed output."""
import os
import sys
import json
import requests
from dotenv import load_dotenv

load_dotenv()

print("\nTesting http://localhost:8000/api/self-healing/run\n")

try:
    response = requests.post("http://localhost:8000/api/self-healing/run", timeout=60)
    result = response.json()
    
    print("FULL RESPONSE:")
    print(json.dumps(result, indent=2))
    
except Exception as e:
    print(f"ERROR: {e}")
