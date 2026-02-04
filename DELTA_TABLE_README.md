# Delta Table Analysis Feature

## Overview

This feature allows you to read Delta tables from Databricks containing cluster and job logs, and generate AI-powered summaries and insights using OpenAI/Azure OpenAI.

## What's New

✅ **Read Delta Tables**: Query any Delta table from your Databricks workspace  
✅ **Execute SQL Queries**: Run custom SQL queries via API  
✅ **AI Summarization**: Get intelligent summaries of logs with actionable insights  
✅ **Multiple Analysis Modes**: Focus analysis on cost, performance, errors, or usage  
✅ **REST API Endpoints**: Easy integration with any application  
✅ **Interactive Testing**: Python scripts for quick testing  

## Quick Start

### Step 1: Ensure Prerequisites

1. **Databricks Setup**:
   - SQL Warehouse must be running in your Databricks workspace
   - Delta table with cluster/job logs must exist
   - Databricks token must have READ access to the table

2. **Environment Configuration**:
   Your `.env` file should already have these configured:
   ```bash
   # Databricks
   DATABRICKS_HOST=https://your-workspace.azuredatabricks.net/
   DATABRICKS_TOKEN=dapi...
   
   # Azure OpenAI
   AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com
   AZURE_OPENAI_API_KEY=your-key
   AZURE_OPENAI_DEPLOYMENT_NAME=gpt-5.2
   ```

### Step 2: Test with Interactive Script

The easiest way to get started:

```bash
cd backend
python test_delta_table.py
```

The script will guide you through:
1. Entering your Delta table name
2. Selecting a SQL warehouse
3. Choosing analysis focus
4. Viewing AI-generated insights

### Step 3: Use via API

Start the backend server:

```bash
cd backend
python main.py
```

Then use the API (see examples below).

## API Endpoints

### 1. Read Delta Table

**Endpoint**: `POST /api/delta-table/read`

**Request**:
```json
{
  "table_name": "catalog.schema.table_name",
  "limit": 1000,
  "warehouse_id": "optional-warehouse-id"
}
```

**Response**:
```json
{
  "status": "success",
  "table_name": "catalog.schema.table_name",
  "rows": [...],
  "row_count": 150,
  "columns": ["col1", "col2", ...]
}
```

### 2. Read and Summarize Delta Table (AI-Powered)

**Endpoint**: `POST /api/delta-table/summarize`

**Request**:
```json
{
  "table_name": "catalog.schema.table_name",
  "limit": 1000,
  "analysis_focus": "cost",
  "warehouse_id": "optional-warehouse-id"
}
```

**Analysis Focus Options**:
- `general` - Comprehensive overview (default)
- `cost` - Cost optimization and savings
- `performance` - Performance bottlenecks
- `errors` - Error patterns and fixes
- `usage` - Resource utilization patterns

**Response**:
```json
{
  "status": "success",
  "table_name": "...",
  "row_count": 150,
  "summary": "High-level AI summary...",
  "key_findings": [
    "Finding 1",
    "Finding 2"
  ],
  "insights": [
    {
      "category": "cost",
      "severity": "high",
      "title": "Over-provisioned clusters detected",
      "description": "Several clusters running with high idle time",
      "recommendation": "Right-size clusters or implement auto-termination"
    }
  ],
  "statistics": {
    "total_records": 150,
    "key_metrics": {}
  }
}
```

### 3. Execute Custom SQL Query

**Endpoint**: `POST /api/sql/execute`

**Request**:
```json
{
  "query": "SELECT * FROM my_table WHERE date > '2024-01-01' LIMIT 100",
  "warehouse_id": "optional-warehouse-id"
}
```

**Response**:
```json
{
  "status": "success",
  "rows": [...],
  "row_count": 45,
  "columns": ["col1", "col2", ...]
}
```

## Usage Examples

### Python Script (Interactive)

```bash
python test_delta_table.py
```

### Python Code

```python
from databricks_client import DatabricksClient
from ai_agent import ClusterIQAgent

# Initialize
client = DatabricksClient(host="...", token="...")
ai = ClusterIQAgent(azure_endpoint="...", azure_api_key="...", azure_deployment_name="...")

# Read table
data = client.read_delta_table("default.cluster_logs", limit=500)

# Generate summary
summary = ai.summarize_delta_table_data(data, analysis_focus="cost")

print(summary['summary'])
```

### cURL

```bash
# Read table
curl -X POST http://localhost:8000/api/delta-table/read \
  -H "Content-Type: application/json" \
  -d '{"table_name": "default.cluster_logs", "limit": 100}'

# Summarize table
curl -X POST http://localhost:8000/api/delta-table/summarize \
  -H "Content-Type: application/json" \
  -d '{"table_name": "default.cluster_logs", "analysis_focus": "cost"}'
```

### API Usage Example Script

```bash
python example_api_usage.py
```

This demonstrates all three endpoints with sample requests.

## File Changes

### New Files Created:
1. `backend/test_delta_table.py` - Interactive testing script
2. `backend/example_api_usage.py` - API usage examples
3. `DELTA_TABLE_GUIDE.md` - Comprehensive documentation
4. `DELTA_TABLE_README.md` - This file

### Modified Files:
1. `backend/databricks_client.py` - Added:
   - `execute_sql_query()` - Execute SQL via Statement Execution API
   - `read_delta_table()` - Read Delta tables

2. `backend/ai_agent.py` - Added:
   - `summarize_delta_table_data()` - AI-powered analysis of table data

3. `backend/main.py` - Added endpoints:
   - `POST /api/delta-table/read`
   - `POST /api/delta-table/summarize`
   - `POST /api/sql/execute`

## Table Name Format

Your Delta table can be specified in these formats:

```
catalog_name.schema_name.table_name    # Three-level
schema_name.table_name                  # Two-level
table_name                              # Uses default schema
```

Examples:
- `main.default.cluster_logs`
- `default.cluster_logs`
- `cluster_logs`

## Expected Data Schema

For best results, your Delta table should contain cluster/job log data with columns like:

- `cluster_id` - Cluster identifier
- `cluster_name` - Cluster name
- `job_id` - Job identifier
- `job_name` - Job name
- `timestamp` - Event timestamp
- `event_type` - Event type (start, stop, error, etc.)
- `duration` - Duration in seconds
- `cost` - Cost metrics
- `state` - State information
- `error_message` - Error details (if any)

## Troubleshooting

### Error: "No SQL warehouses available"
**Solution**: Create and start a SQL Warehouse in your Databricks workspace

### Error: "Table not found"
**Solutions**:
- Verify table name format
- Check table exists: `SHOW TABLES IN schema_name`
- Ensure token has READ permission

### Error: "Databricks client not configured"
**Solution**: Check `.env` file has valid `DATABRICKS_HOST` and `DATABRICKS_TOKEN`

### Error: "AI agent not configured"
**Solution**: Verify Azure OpenAI credentials in `.env` file

### Error: "Query timeout"
**Solutions**:
- Reduce `limit` parameter
- Ensure SQL warehouse is running
- Use WHERE clause to filter data

## Tips for Best Results

1. **Start Small**: Begin with 500-1000 rows for faster analysis
2. **Choose Focus**: Select the right `analysis_focus` for your needs
3. **Sample First**: Use `read_delta_table` to inspect data before summarizing
4. **Warehouse Size**: Use larger warehouse for complex queries on big tables
5. **Data Quality**: Ensure logs have consistent schema and complete data

## Next Steps

1. **Test the feature**: Run `python test_delta_table.py`
2. **Try the API**: Run `python example_api_usage.py`
3. **Read the guide**: See `DELTA_TABLE_GUIDE.md` for detailed documentation
4. **Integrate**: Add API calls to your frontend application

## Support

- Check backend logs for detailed error messages
- Test Databricks connectivity: `GET /health`
- Verify SQL warehouse in Databricks workspace
- See `DELTA_TABLE_GUIDE.md` for comprehensive troubleshooting

---

**Ready to use!** Start with `python test_delta_table.py` to analyze your Delta tables.
