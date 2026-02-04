"""Quick example script to demonstrate Delta table analysis."""
import requests
import json

# Configuration
API_BASE_URL = "http://localhost:8000"

def example_usage():
    """Example showing how to use the Delta table endpoints."""
    
    print("="*70)
    print("Delta Table Analysis - API Example")
    print("="*70)
    
    # Example 1: Read Delta table
    print("\n1. Reading Delta Table...")
    print("-" * 70)
    
    read_payload = {
        "table_name": "default.cluster_logs",  # Replace with your table name
        "limit": 100
    }
    
    print(f"Request: POST {API_BASE_URL}/api/delta-table/read")
    print(f"Payload: {json.dumps(read_payload, indent=2)}")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/delta-table/read",
            json=read_payload
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✓ Success! Read {data.get('row_count', 0)} rows")
            print(f"  Columns: {', '.join(data.get('columns', []))}")
            
            if data.get('rows'):
                print(f"\n  Sample row:")
                print(f"  {json.dumps(data['rows'][0], indent=4)}")
        else:
            print(f"\n✗ Error: {response.status_code}")
            print(f"  {response.text}")
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
    
    # Example 2: Summarize Delta table with AI
    print("\n\n2. Generating AI Summary...")
    print("-" * 70)
    
    summarize_payload = {
        "table_name": "default.cluster_logs",  # Replace with your table name
        "limit": 500,
        "analysis_focus": "cost"  # Options: general, cost, performance, errors, usage
    }
    
    print(f"Request: POST {API_BASE_URL}/api/delta-table/summarize")
    print(f"Payload: {json.dumps(summarize_payload, indent=2)}")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/delta-table/summarize",
            json=summarize_payload
        )
        
        if response.status_code == 200:
            summary = response.json()
            print(f"\n✓ Success!")
            print(f"\n{'='*70}")
            print("SUMMARY")
            print(f"{'='*70}")
            print(f"\n{summary.get('summary', 'No summary available')}")
            
            if summary.get('key_findings'):
                print(f"\n{'='*70}")
                print("KEY FINDINGS")
                print(f"{'='*70}")
                for i, finding in enumerate(summary['key_findings'], 1):
                    print(f"\n{i}. {finding}")
            
            if summary.get('insights'):
                print(f"\n{'='*70}")
                print("INSIGHTS")
                print(f"{'='*70}")
                for insight in summary['insights'][:3]:  # Show first 3
                    print(f"\n[{insight.get('severity', 'N/A').upper()}] {insight.get('title', 'No title')}")
                    print(f"  {insight.get('description', 'No description')}")
                    print(f"  → {insight.get('recommendation', 'No recommendation')}")
        else:
            print(f"\n✗ Error: {response.status_code}")
            print(f"  {response.text}")
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
    
    # Example 3: Execute custom SQL query
    print("\n\n3. Executing Custom SQL Query...")
    print("-" * 70)
    
    sql_payload = {
        "query": "SELECT cluster_id, COUNT(*) as event_count FROM default.cluster_logs GROUP BY cluster_id LIMIT 10"
    }
    
    print(f"Request: POST {API_BASE_URL}/api/sql/execute")
    print(f"Payload: {json.dumps(sql_payload, indent=2)}")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/sql/execute",
            json=sql_payload
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✓ Success! Query returned {result.get('row_count', 0)} rows")
            
            if result.get('rows'):
                print(f"\n  Results:")
                for row in result['rows'][:5]:  # Show first 5
                    print(f"  {row}")
        else:
            print(f"\n✗ Error: {response.status_code}")
            print(f"  {response.text}")
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
    
    print("\n" + "="*70)
    print("Examples Complete!")
    print("="*70)
    print("\nNote: Replace 'default.cluster_logs' with your actual table name.")
    print("Make sure the backend server is running: python main.py")
    print("="*70 + "\n")


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════╗
║     Delta Table Analysis - API Usage Examples                   ║
║     Make sure backend is running on http://localhost:8000        ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    # Check if server is running
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=2)
        if response.status_code == 200:
            print("✓ Backend server is running!\n")
            example_usage()
        else:
            print("✗ Backend server returned error. Please check the server.")
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to backend server.")
        print("  Please start the server first: python main.py")
    except Exception as e:
        print(f"✗ Error: {str(e)}")
