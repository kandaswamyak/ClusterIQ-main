# Delta Table Analysis Guide

This guide explains how to read Delta tables from Databricks and generate AI-powered summaries using OpenAI.

## Features Added

1. **Read Delta Tables**: Query Delta tables directly from Databricks
2. **AI Summarization**: Generate intelligent summaries of cluster and job logs
3. **Multiple Analysis Modes**: Focus on cost, performance, errors, or general insights
4. **REST API Endpoints**: Easy integration with frontend or other services

## Prerequisites

- Databricks workspace with SQL Warehouse configured
- Delta table containing cluster and job logs
- Azure OpenAI or OpenAI API credentials configured in `.env`

## Usage Methods

### Method 1: Python Script (Recommended for Testing)

Run the test script interactively:

```bash
cd backend
python test_delta_table.py
```

The script will:
1. Prompt for your Delta table name
2. Show available SQL warehouses
3. Read the data from the table
4. Ask for analysis focus (general, cost, performance, errors, usage)
5. Generate and display AI summary with insights

### Method 2: API Endpoints

Start the backend server:

```bash
cd backend
python main.py
```

#### Endpoint 1: Read Delta Table

```bash
POST http://localhost:8000/api/delta-table/read
Content-Type: application/json

{
  "table_name": "catalog_name.schema_name.table_name",
  "limit": 1000,
  "warehouse_id": "optional_warehouse_id"
}
```

Response:
```json
{
  "status": "success",
  "table_name": "catalog_name.schema_name.table_name",
  "rows": [...],
  "row_count": 150,
  "columns": ["column1", "column2", ...]
}
```

#### Endpoint 2: Read and Summarize Delta Table

```bash
POST http://localhost:8000/api/delta-table/summarize
Content-Type: application/json

{
  "table_name": "catalog_name.schema_name.table_name",
  "limit": 1000,
  "warehouse_id": "optional_warehouse_id",
  "analysis_focus": "cost"
}
```

Parameters:
- `table_name` (required): Full table name (catalog.schema.table or schema.table)
- `limit` (optional, default: 1000): Max rows to analyze
- `warehouse_id` (optional): SQL warehouse ID (auto-selects if not provided)
- `analysis_focus` (optional, default: "general"): One of:
  - `general`: Comprehensive overview
  - `cost`: Cost optimization focus
  - `performance`: Performance analysis
  - `errors`: Error pattern detection
  - `usage`: Usage pattern analysis

Response:
```json
{
  "status": "success",
  "table_name": "...",
  "row_count": 150,
  "column_count": 10,
  "columns": ["..."],
  "analysis_focus": "cost",
  "summary": "High-level summary...",
  "key_findings": [
    "Finding 1",
    "Finding 2"
  ],
  "insights": [
    {
      "category": "cost",
      "severity": "high",
      "title": "...",
      "description": "...",
      "recommendation": "..."
    }
  ],
  "statistics": {
    "total_records": 150,
    "key_metrics": {}
  }
}
```

#### Endpoint 3: Execute Custom SQL Query

```bash
POST http://localhost:8000/api/sql/execute
Content-Type: application/json

{
  "query": "SELECT * FROM my_table WHERE date > '2024-01-01' LIMIT 100",
  "warehouse_id": "optional_warehouse_id"
}
```

## Example Table Names

Your Delta table name should follow one of these formats:

1. **Three-level namespace**: `catalog_name.schema_name.table_name`
   - Example: `main.default.cluster_logs`

2. **Two-level namespace**: `schema_name.table_name`
   - Example: `default.cluster_logs`

3. **Single name** (uses default schema): `table_name`
   - Example: `cluster_logs`

## Expected Data Format

For optimal analysis, your Delta table should contain cluster and job log data with columns such as:

- `cluster_id`: Cluster identifier
- `cluster_name`: Cluster name
- `job_id`: Job identifier
- `job_name`: Job name
- `timestamp`: Log timestamp
- `event_type`: Type of event (start, stop, error, etc.)
- `duration`: Execution duration
- `cost`: Cost metrics
- `state`: Cluster/job state
- `error_message`: Error details (if applicable)
- Any other relevant metrics

## Analysis Focus Options

### General (Default)
- Comprehensive overview of all data
- Identifies key patterns and trends
- Suitable for initial exploration

### Cost
- Focus on cost optimization
- Identifies resource wastage
- Provides cost-saving recommendations

### Performance
- Analyzes execution times
- Identifies bottlenecks
- Performance optimization suggestions

### Errors
- Pattern recognition in failures
- Root cause analysis
- Error prevention recommendations

### Usage
- Cluster utilization patterns
- Job execution frequency
- Resource allocation insights

## Example Python Code

```python
from databricks_client import DatabricksClient
from ai_agent import ClusterIQAgent

# Initialize clients
client = DatabricksClient(host="...", token="...")
ai = ClusterIQAgent(azure_endpoint="...", azure_api_key="...", azure_deployment_name="...")

# Read Delta table
data = client.read_delta_table(
    table_name="main.default.cluster_logs",
    limit=500
)

# Generate summary
summary = ai.summarize_delta_table_data(
    table_data=data,
    analysis_focus="cost"
)

print(summary['summary'])
for insight in summary['insights']:
    print(f"{insight['title']}: {insight['recommendation']}")
```

## Example cURL Commands

### Read table:
```bash
curl -X POST http://localhost:8000/api/delta-table/read \
  -H "Content-Type: application/json" \
  -d '{"table_name": "default.cluster_logs", "limit": 100}'
```

### Summarize table:
```bash
curl -X POST http://localhost:8000/api/delta-table/summarize \
  -H "Content-Type: application/json" \
  -d '{
    "table_name": "default.cluster_logs",
    "limit": 500,
    "analysis_focus": "cost"
  }'
```

## Troubleshooting

### "No SQL warehouses available"
- Ensure you have at least one SQL warehouse running in your Databricks workspace
- Check your Databricks token has permission to access SQL warehouses

### "Table not found"
- Verify the table name format (catalog.schema.table)
- Check if the table exists: Run `SHOW TABLES IN schema_name` in Databricks SQL
- Ensure your token has READ permission on the table

### "AI agent not configured"
- Verify `.env` file has valid OpenAI/Azure OpenAI credentials
- Check the backend logs for initialization errors

### "Query timeout"
- Reduce the `limit` parameter to fetch fewer rows
- Ensure your SQL warehouse is running (not in stopped state)
- Check if the table is very large - consider adding WHERE clause

## Tips for Best Results

1. **Limit Data Volume**: Start with 500-1000 rows for faster analysis
2. **Use Specific Focus**: Choose analysis_focus based on your goal
3. **Review Sample Data**: Check the data sample before full analysis
4. **SQL Warehouse**: Use a larger warehouse for complex queries
5. **Table Format**: Ensure logs are well-structured with consistent columns

## Integration with Frontend

To integrate with the ClusterIQ frontend, add API calls in [frontend/src/services/api.js](../frontend/src/services/api.js):

```javascript
export const analyzeDeltaTable = async (tableName, focus = 'general') => {
  const response = await fetch(`${API_BASE_URL}/api/delta-table/summarize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      table_name: tableName,
      analysis_focus: focus,
      limit: 1000
    })
  });
  return response.json();
};
```

## Support

For issues or questions:
1. Check backend logs for detailed error messages
2. Verify Databricks connectivity using `/api/debug/clusters`
3. Test SQL warehouse access in Databricks SQL editor first
