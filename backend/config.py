"""Configuration management for ClusterIQ backend."""
import os
from typing import List
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the backend directory
backend_dir = Path(__file__).parent
env_file = backend_dir / '.env'
load_dotenv(dotenv_path=env_file)


class Settings:
    """Application settings."""
    
    # Databricks Configuration
    databricks_host: str = os.getenv("DATABRICKS_HOST", "")
    databricks_token: str = os.getenv("DATABRICKS_TOKEN", "")
    
    # OpenAI Configuration
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
    
    # Azure OpenAI (alternative)
    azure_openai_endpoint: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    azure_openai_api_key: str = os.getenv("AZURE_OPENAI_API_KEY", "")
    azure_openai_deployment_name: str = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "")
    
    # Server Configuration
    backend_port: int = int(os.getenv("BACKEND_PORT", "8000"))
    cors_origins: List[str] = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
    
    # Update Configuration
    update_interval: int = int(os.getenv("UPDATE_INTERVAL", "30"))

    # Delta Table Configuration (Hive metastore format: database.table)
    # For Unity Catalog, use format: catalog.schema.table
    delta_cluster_events_table: str = os.getenv(
        "DELTA_CLUSTER_EVENTS_TABLE",
        "default.cluster_events"
    )
    delta_cluster_logs_table: str = os.getenv(
        "DELTA_CLUSTER_LOGS_TABLE",
        "default.cluster_logs"
    )
    delta_job_run_logs_table: str = os.getenv(
        "DELTA_JOB_RUN_LOGS_TABLE",
        "default.job_run_logs"
    )
    
    def __init__(self):
        """Initialize and log configuration."""
        print(f"DEBUG: DATABRICKS_HOST loaded: {bool(self.databricks_host)}")
        print(f"DEBUG: DATABRICKS_TOKEN loaded: {bool(self.databricks_token)}")
        print(f"DEBUG: AZURE_OPENAI_ENDPOINT loaded: {bool(self.azure_openai_endpoint)}")
        print(f"DEBUG: AZURE_OPENAI_API_KEY loaded: {bool(self.azure_openai_api_key)}")


settings = Settings()

