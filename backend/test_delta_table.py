"""Test script for Delta table reading and summarization."""
import os
from dotenv import load_dotenv
from databricks_client import DatabricksClient
from ai_agent import ClusterIQAgent

# Load environment variables
load_dotenv()

def test_delta_table_read():
    """Test reading a Delta table and generating a summary."""
    
    # Initialize clients
    databricks_client = DatabricksClient(
        host=os.getenv("DATABRICKS_HOST"),
        token=os.getenv("DATABRICKS_TOKEN")
    )
    
    ai_agent = ClusterIQAgent(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        azure_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        azure_deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    )
    
    # Replace with your actual Delta table name
    # Examples: "catalog_name.schema_name.table_name" or "schema_name.table_name"
    table_name = input("Enter your Delta table name (e.g., 'default.cluster_logs'): ").strip()
    
    if not table_name:
        print("Error: Table name is required")
        return
    
    # Optional: Get warehouse ID
    print("\nFetching available SQL warehouses...")
    warehouses = databricks_client.get_sql_warehouses()
    
    if warehouses:
        print("\nAvailable SQL Warehouses:")
        for i, wh in enumerate(warehouses):
            print(f"  {i+1}. {wh.get('name')} (ID: {wh.get('id')}) - State: {wh.get('state')}")
        
        choice = input("\nEnter warehouse number (or press Enter for default): ").strip()
        warehouse_id = warehouses[int(choice)-1].get('id') if choice.isdigit() and int(choice) <= len(warehouses) else None
    else:
        print("No SQL warehouses found. Will use default if available.")
        warehouse_id = None
    
    # Read the Delta table
    print(f"\n{'='*60}")
    print(f"Reading Delta table: {table_name}")
    print(f"{'='*60}\n")
    
    table_data = databricks_client.read_delta_table(
        table_name=table_name,
        limit=1000,
        warehouse_id=warehouse_id
    )
    
    if table_data.get("status") != "success":
        print(f"Error reading table: {table_data.get('error')}")
        return
    
    print(f"✓ Successfully read {table_data.get('row_count')} rows")
    print(f"✓ Columns: {', '.join(table_data.get('columns', []))}")
    
    # Show sample data
    if table_data.get('rows'):
        print(f"\nSample data (first 3 rows):")
        for i, row in enumerate(table_data['rows'][:3], 1):
            print(f"\n  Row {i}:")
            for key, value in row.items():
                print(f"    {key}: {value}")
    
    # Generate AI summary
    print(f"\n{'='*60}")
    print("Generating AI Summary...")
    print(f"{'='*60}\n")
    
    # Ask for analysis focus
    print("Analysis focus options:")
    print("  1. General (comprehensive overview)")
    print("  2. Cost (cost optimization)")
    print("  3. Performance (performance analysis)")
    print("  4. Errors (error patterns)")
    print("  5. Usage (usage patterns)")
    
    focus_choice = input("\nSelect analysis focus (1-5, or press Enter for General): ").strip()
    focus_map = {
        "1": "general",
        "2": "cost",
        "3": "performance",
        "4": "errors",
        "5": "usage"
    }
    analysis_focus = focus_map.get(focus_choice, "general")
    
    summary = ai_agent.summarize_delta_table_data(
        table_data=table_data,
        analysis_focus=analysis_focus
    )
    
    if summary.get("status") != "success":
        print(f"Error generating summary: {summary.get('error')}")
        return
    
    # Display results
    print(f"\n{'='*60}")
    print("AI ANALYSIS SUMMARY")
    print(f"{'='*60}\n")
    
    print(f"Table: {summary.get('table_name')}")
    print(f"Records Analyzed: {summary.get('row_count')}")
    print(f"Analysis Focus: {summary.get('analysis_focus')}")
    print(f"\n{summary.get('summary', 'No summary available')}\n")
    
    if summary.get('key_findings'):
        print(f"\n{'='*60}")
        print("KEY FINDINGS")
        print(f"{'='*60}\n")
        for i, finding in enumerate(summary['key_findings'], 1):
            print(f"{i}. {finding}")
    
    if summary.get('insights'):
        print(f"\n{'='*60}")
        print("DETAILED INSIGHTS")
        print(f"{'='*60}\n")
        for i, insight in enumerate(summary['insights'], 1):
            print(f"\n{i}. [{insight.get('severity', 'N/A').upper()}] {insight.get('title', 'No title')}")
            print(f"   Category: {insight.get('category', 'N/A')}")
            print(f"   Description: {insight.get('description', 'No description')}")
            print(f"   Recommendation: {insight.get('recommendation', 'No recommendation')}")
    
    if summary.get('statistics'):
        print(f"\n{'='*60}")
        print("STATISTICS")
        print(f"{'='*60}\n")
        stats = summary['statistics']
        print(f"Total Records: {stats.get('total_records', 0)}")
        if stats.get('key_metrics'):
            print("\nKey Metrics:")
            for key, value in stats['key_metrics'].items():
                print(f"  {key}: {value}")
    
    print(f"\n{'='*60}")
    print("Analysis Complete!")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════╗
║         Delta Table Analysis with OpenAI                 ║
║         ClusterIQ - Databricks Cost Optimization         ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    try:
        test_delta_table_read()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        print(f"\n\nError: {str(e)}")
        import traceback
        traceback.print_exc()
