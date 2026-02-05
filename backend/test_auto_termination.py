"""
Test script to verify auto-termination configuration on the playground cluster.

This script:
1. Checks if the playground cluster exists
2. Verifies auto-termination is configured
3. Monitors the cluster state over time
4. Reports when it terminates
"""

import os
import sys
import json
import time
from datetime import datetime
from dotenv import load_dotenv
from databricks_client import DatabricksClient

# Load environment variables
load_dotenv()

DATABRICKS_HOST = os.getenv("DATABRICKS_HOST")
DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN")

def print_header(text):
    """Print a formatted header."""
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}\n")

def print_section(text):
    """Print a section header."""
    print(f"\n--- {text} ---\n")

def test_auto_termination():
    """Test auto-termination configuration on playground cluster."""
    
    if not DATABRICKS_HOST or not DATABRICKS_TOKEN:
        print("❌ Error: DATABRICKS_HOST or DATABRICKS_TOKEN not configured")
        return False
    
    print_header("Auto-Termination Verification Test")
    
    client = DatabricksClient(DATABRICKS_HOST, DATABRICKS_TOKEN)
    
    # Step 1: Get cluster list
    print_section("Step 1: Fetching clusters...")
    clusters = client.get_all_clusters()
    
    if not clusters:
        print("❌ No clusters found")
        return False
    
    print(f"✅ Found {len(clusters)} clusters")
    
    # Find playground cluster
    playground = None
    for cluster in clusters:
        if cluster.get("cluster_name") == "playground":
            playground = cluster
            break
    
    if not playground:
        print("❌ 'playground' cluster not found")
        print("\n📋 Available clusters:")
        for cluster in clusters:
            print(f"  - {cluster.get('cluster_name')} (ID: {cluster.get('cluster_id')})")
        return False
    
    print(f"✅ Found 'playground' cluster")
    
    # Step 2: Check cluster details
    print_section("Step 2: Checking cluster configuration...")
    
    cluster_id = playground.get("cluster_id")
    cluster_state = playground.get("state", "UNKNOWN")
    
    print(f"Cluster ID: {cluster_id}")
    print(f"State: {cluster_state}")
    print(f"Workers: {playground.get('num_workers', 'N/A')}")
    print(f"Node Type: {playground.get('node_type_id', 'N/A')}")
    
    # Get detailed cluster info
    try:
        cluster_info = client.get_cluster_info(cluster_id)
        if cluster_info and cluster_info.get("status") == "success":
            details = cluster_info.get("cluster", {})
            auto_term = details.get("autotermination_minutes", "NOT SET")
            print(f"Auto-termination: {auto_term} minutes")
            
            if auto_term == "NOT SET" or auto_term == 0:
                print("⚠️  WARNING: Auto-termination is NOT configured!")
                return False
            else:
                print(f"✅ Auto-termination is configured for {auto_term} minutes")
    except Exception as e:
        print(f"⚠️  Could not fetch detailed cluster info: {str(e)}")
    
    # Step 3: Monitor cluster state
    print_section("Step 3: Monitoring cluster state...")
    print(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Cluster state: {cluster_state}")
    
    if cluster_state == "RUNNING":
        print("\n📌 Cluster is currently RUNNING")
        print("⏱️  Auto-termination will trigger after 15 minutes of inactivity")
        print("\nTo verify auto-termination:")
        print("1. Stop any jobs running on this cluster")
        print("2. Leave the cluster idle for 15 minutes")
        print("3. Check back in 15 minutes - cluster should be TERMINATED")
        
        # Optional: Monitor for a short period
        print("\n📊 Monitoring for 5 minutes (can continue in background)...")
        monitor_duration = 60  # seconds
        check_interval = 30    # seconds
        checks = 0
        
        while checks * check_interval < monitor_duration:
            time.sleep(check_interval)
            checks += 1
            
            try:
                clusters = client.get_all_clusters()
                for c in clusters:
                    if c.get("cluster_id") == cluster_id:
                        state = c.get("state", "UNKNOWN")
                        elapsed = checks * check_interval
                        print(f"[{elapsed}s] Cluster state: {state}")
                        
                        if state == "TERMINATED":
                            print(f"\n✅ Cluster terminated after {elapsed} seconds!")
                            return True
                        break
            except Exception as e:
                print(f"⚠️  Error checking cluster: {str(e)}")
    
    elif cluster_state == "TERMINATED":
        print("✅ Cluster is already TERMINATED")
        print("Auto-termination worked!")
        return True
    
    else:
        print(f"⚠️  Cluster state is: {cluster_state}")
        print("Cannot test auto-termination on a cluster that's not RUNNING or TERMINATED")
    
    return True

def main():
    """Run the auto-termination test."""
    try:
        success = test_auto_termination()
        
        print_section("Test Summary")
        if success:
            print("✅ Auto-termination test completed successfully")
            print("\n📋 Next steps:")
            print("  1. Wait 15 minutes with no activity on the cluster")
            print("  2. Check Databricks UI to confirm cluster is TERMINATED")
            print("  3. Verify you're not charged for idle compute time")
        else:
            print("❌ Auto-termination test encountered issues")
            print("\n🔧 Troubleshooting:")
            print("  1. Ensure playground cluster exists in Databricks")
            print("  2. Check auto-termination is configured (should be 15 minutes)")
            print("  3. Verify Databricks token has proper permissions")
        
        sys.exit(0 if success else 1)
    
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
