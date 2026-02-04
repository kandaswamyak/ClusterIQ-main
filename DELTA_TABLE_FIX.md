# Fixing Unity Catalog Error for Delta Table Analysis

## Problem
When clicking "Analyze Delta Log" in the Approvals tab, you get:
```
[UC_NOT_ENABLED] Unity Catalog is not enabled on this cluster. SQLSTATE: 56038
```

## Root Cause
Your Databricks workspace uses **Hive metastore** (not Unity Catalog), but the Delta table names are using Unity Catalog format.

## Solution

### Option 1: Use Correct Table Names (Hive Metastore Format)
The table names should use the format: `database.table` instead of `catalog.schema.table`

1. Check your existing Delta table names:
   ```bash
   # In Databricks notebook, run:
   SHOW TABLES;  # Shows all tables in default database
   ```

2. Update environment variables in your `.env` file:
   ```bash
   DELTA_CLUSTER_EVENTS_TABLE=default.cluster_events
   DELTA_CLUSTER_LOGS_TABLE=default.cluster_logs
   DELTA_JOB_RUN_LOGS_TABLE=default.job_run_logs
   ```

3. Or specify your actual database name:
   ```bash
   DELTA_CLUSTER_EVENTS_TABLE=your_database.cluster_events
   DELTA_CLUSTER_LOGS_TABLE=your_database.cluster_logs
   DELTA_JOB_RUN_LOGS_TABLE=your_database.job_run_logs
   ```

### Option 2: Check Available SQL Warehouses
The Delta table analysis requires a SQL warehouse to execute queries.

1. Go to backend directory and check available warehouses:
   ```bash
   curl http://localhost:8000/api/debug/warehouses
   ```

2. Or in the Approvals tab, provide the warehouse ID:
   - Click "Analyze Delta Log"
   - In the request body, add: `{"warehouse_id": "<your-warehouse-id>"}`

### Option 3: Use Frontend with Custom Table Names
When clicking "Analyze Delta Log", you can override the default table names:

```json
{
  "cluster_events_table": "your_db.cluster_events",
  "cluster_logs_table": "your_db.cluster_logs",
  "job_run_logs_table": "your_db.job_run_logs",
  "warehouse_id": "optional-warehouse-id"
}
```

## Verify Your Tables Exist
In a Databricks notebook, check your tables:
```sql
-- List all databases
SHOW DATABASES;

-- List tables in a database
USE your_database;
SHOW TABLES;

-- Check table schema
DESC FORMATTED cluster_events;  -- if your table is named this
```

## If Tables Don't Exist
If the Delta tables don't exist yet, you need to create them. Example:

```sql
-- Create in default database
CREATE TABLE IF NOT EXISTS default.cluster_events (
  event_id STRING,
  cluster_id STRING,
  timestamp TIMESTAMP,
  event_type STRING
);

CREATE TABLE IF NOT EXISTS default.cluster_logs (
  log_id STRING,
  cluster_id STRING,
  timestamp TIMESTAMP,
  log_message STRING
);

CREATE TABLE IF NOT EXISTS default.job_run_logs (
  run_id STRING,
  job_id STRING,
  timestamp TIMESTAMP,
  status STRING
);
```

## Configuration Priority
The application checks for table names in this order:
1. Request body parameters (if provided)
2. Environment variables (if set)
3. Default values: `default.cluster_events`, `default.cluster_logs`, `default.job_run_logs`

## Need Help?
- Check backend logs for detailed error messages
- Verify table names and schema in Databricks notebook
- Ensure SQL warehouse is running and accessible
- Test with: `curl http://localhost:8000/api/debug/warehouses`
