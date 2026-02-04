"""Test script to verify Databricks API connection."""
import os
from dotenv import load_dotenv
import requests

load_dotenv()

def test_databricks_api():
    """Test Databricks API connection."""
    host = os.getenv("DATABRICKS_HOST", "").rstrip('/')
    token = os.getenv("DATABRICKS_TOKEN", "")
    
    if not host or not token:
        print("ERROR: DATABRICKS_HOST and DATABRICKS_TOKEN must be set in .env")
        return
    
    print(f"Testing connection to: {host}")
    print(f"Token: {'*' * 20}...{token[-4:] if len(token) > 4 else '****'}")
    print()
    
    # Test Jobs API
    try:
        url = f"{host}/api/2.1/jobs/list"
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        print(f"Calling: {url}")
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            job_count = len(data.get("jobs", []))
            print(f"✓ Jobs API: SUCCESS")
            print(f"  Found {job_count} jobs")
        else:
            print(f"✗ Jobs API: FAILED")
            print(f"  Status Code: {response.status_code}")
            print(f"  Response: {response.text[:200]}")
    
    except Exception as e:
        print(f"✗ Jobs API: ERROR")
        print(f"  {str(e)}")
    
    print()
    
    # Test Clusters API
    try:
        url = f"{host}/api/2.1/clusters/list"
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        print(f"Calling: {url}")
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            cluster_count = len(data.get("clusters", []))
            print(f"✓ Clusters API: SUCCESS")
            print(f"  Found {cluster_count} clusters")
        else:
            print(f"✗ Clusters API: FAILED")
            print(f"  Status Code: {response.status_code}")
            print(f"  Response: {response.text[:200]}")
    
    except Exception as e:
        print(f"✗ Clusters API: ERROR")
        print(f"  {str(e)}")

if __name__ == "__main__":
    test_databricks_api()

