"""Test script to debug cluster fetching."""
import os
import sys
from dotenv import load_dotenv
from databricks_client import DatabricksClient
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

def test_clusters():
    """Test cluster fetching."""
    host = os.getenv("DATABRICKS_HOST")
    token = os.getenv("DATABRICKS_TOKEN")
    
    if not host or not token:
        print("ERROR: DATABRICKS_HOST and DATABRICKS_TOKEN must be set in .env")
        return
    
    print(f"Connecting to: {host}")
    
    try:
        client = DatabricksClient(host=host, token=token)
        print("✓ Client initialized")
        
        # Test listing clusters
        print("\nTesting clusters.list()...")
        cluster_list = list(client.client.clusters.list())
        print(f"Found {len(cluster_list)} clusters in list")
        
        if cluster_list:
            print("\nFirst few clusters:")
            for i, cluster in enumerate(cluster_list[:3]):
                print(f"  {i+1}. ID: {cluster.cluster_id}, Name: {getattr(cluster, 'cluster_name', 'N/A')}, State: {cluster.state.value if hasattr(cluster, 'state') and cluster.state else 'N/A'}")
        
        # Test our method
        print("\nTesting get_all_clusters()...")
        clusters = client.get_all_clusters()
        print(f"Processed {len(clusters)} clusters")
        
        if clusters:
            print("\nProcessed clusters:")
            for i, cluster in enumerate(clusters[:3]):
                print(f"  {i+1}. {cluster}")
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_clusters()

