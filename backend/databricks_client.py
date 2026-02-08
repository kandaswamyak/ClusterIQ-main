"""Databricks API client using direct HTTP requests (curl-style)."""
from typing import List, Dict, Any, Optional
import requests
import logging

logger = logging.getLogger(__name__)


class DatabricksClient:
    """Client for interacting with Databricks APIs using direct HTTP requests."""
    
    def __init__(self, host: str, token: str):
        """Initialize Databricks client.
        
        Args:
            host: Databricks workspace URL
            token: Databricks personal access token
        """
        self.host = host.rstrip('/')  # Remove trailing slash
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        logger.info(f"Databricks client initialized for host: {self.host}")
    
    def get_all_jobs(self) -> List[Dict[str, Any]]:
        """Fetch all jobs from Databricks workspace using REST API.
        
        Returns:
            List of job dictionaries with metadata
        """
        try:
            url = f"{self.host}/api/2.1/jobs/list"
            logger.info(f"Fetching jobs from: {url}")
            
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            jobs = data.get("jobs", [])
            
            # Transform to match expected format
            job_list = []
            for job in jobs:
                job_dict = {
                    "job_id": job.get("job_id"),
                    "job_name": job.get("settings", {}).get("name", "Unknown"),
                    "created_time": job.get("created_time"),
                    "creator_user_name": job.get("creator_user_name"),
                    "settings": {
                        "timeout_seconds": job.get("settings", {}).get("timeout_seconds"),
                        "max_concurrent_runs": job.get("settings", {}).get("max_concurrent_runs"),
                        "tasks": [
                            {
                                "task_key": task.get("task_key"),
                                "description": task.get("description"),
                                "timeout_seconds": task.get("timeout_seconds"),
                                "cluster_id": task.get("existing_cluster_id"),
                                "new_cluster": task.get("new_cluster"),
                            }
                            for task in job.get("settings", {}).get("tasks", [])
                        ],
                    },
                    "schedule": job.get("settings", {}).get("schedule"),
                }
                job_list.append(job_dict)
            
            logger.info(f"Fetched {len(job_list)} jobs from Databricks")
            return job_list
        
        except Exception as e:
            logger.error(f"Error fetching jobs: {str(e)}", exc_info=True)
            return []
    
    def get_job_runs(self, job_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch recent runs for a specific job using REST API.
        
        Args:
            job_id: Job ID
            limit: Maximum number of runs to fetch
            
        Returns:
            List of run dictionaries
        """
        try:
            url = f"{self.host}/api/2.1/jobs/runs/list"
            params = {
                "job_id": job_id,
                "limit": limit
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            runs_data = data.get("runs", [])
            
            runs = []
            for run in runs_data:
                start_time = run.get("start_time")
                end_time = run.get("end_time")
                duration = None
                if start_time and end_time:
                    duration = (end_time - start_time) / 1000  # Convert ms to seconds
                
                run_dict = {
                    "run_id": run.get("run_id"),
                    "job_id": run.get("job_id"),
                    "run_name": run.get("run_name"),
                    "state": {
                        "life_cycle_state": run.get("state", {}).get("life_cycle_state"),
                        "result_state": run.get("state", {}).get("result_state"),
                        "state_message": run.get("state", {}).get("state_message"),
                    },
                    "start_time": start_time,
                    "end_time": end_time,
                    "duration": duration,
                    "cluster_instance": {
                        "cluster_id": run.get("cluster_instance", {}).get("cluster_id"),
                    } if run.get("cluster_instance") else None,
                    "tasks": [
                        {
                            "task_key": task.get("task_key"),
                            "run_id": task.get("run_id"),
                            "state": task.get("state", {}).get("life_cycle_state"),
                            "start_time": task.get("start_time"),
                            "end_time": task.get("end_time"),
                            "duration": (task.get("end_time") - task.get("start_time")) / 1000 if task.get("end_time") and task.get("start_time") else None,
                        }
                        for task in run.get("tasks", [])
                    ],
                }
                runs.append(run_dict)
            
            return runs
        
        except Exception as e:
            logger.error(f"Error fetching runs for job {job_id}: {str(e)}")
            return []
    
    def cancel_job_run(self, run_id: int) -> Dict[str, Any]:
        """Cancel a running job.
        
        Args:
            run_id: Run ID to cancel
            
        Returns:
            Result dictionary
        """
        try:
            url = f"{self.host}/api/2.1/jobs/runs/cancel"
            payload = {"run_id": run_id}
            
            logger.info(f"Cancelling job run {run_id}")
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()
            
            logger.info(f"Successfully cancelled job run {run_id}")
            return {"status": "success", "run_id": run_id}
        
        except Exception as e:
            logger.error(f"Error cancelling job run {run_id}: {str(e)}", exc_info=True)
            return {"status": "error", "error": str(e), "run_id": run_id}
    
    def get_all_clusters(self) -> List[Dict[str, Any]]:
        """Fetch all clusters from Databricks workspace using REST API.
        
        Returns:
            List of cluster dictionaries
        """
        try:
            url = f"{self.host}/api/2.1/clusters/list"
            logger.info(f"Fetching clusters from: {url}")
            
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            clusters_data = data.get("clusters", [])
            logger.info(f"Found {len(clusters_data)} clusters in API response")
            
            clusters = []
            for cluster in clusters_data:
                try:
                    # Handle state - can be string or dict
                    state = cluster.get("state")
                    if isinstance(state, dict):
                        state = state.get("cluster_state", "UNKNOWN")
                    elif state is None:
                        state = "UNKNOWN"
                    
                    cluster_dict = {
                        "cluster_id": cluster.get("cluster_id"),
                        "cluster_name": cluster.get("cluster_name") or f"Cluster-{cluster.get('cluster_id')}",
                        "state": state,
                        "spark_version": cluster.get("spark_version"),
                        "node_type_id": cluster.get("node_type_id"),
                        "driver_node_type_id": cluster.get("driver_node_type_id"),
                        "num_workers": cluster.get("num_workers", 0),
                        "autotermination_minutes": cluster.get("autotermination_minutes"),
                        "enable_elastic_disk": cluster.get("enable_elastic_disk"),
                        "cluster_source": cluster.get("cluster_source"),
                        "start_time": cluster.get("start_time"),
                        "terminated_time": cluster.get("terminated_time"),
                        "last_activity_time": cluster.get("last_activity_time"),
                        "cluster_memory_mb": cluster.get("cluster_memory_mb"),
                        "cluster_cores": cluster.get("cluster_cores"),
                        "default_tags": cluster.get("default_tags", {}),
                        "spark_conf": cluster.get("spark_conf", {}),
                        "autoscale": {
                            "min_workers": cluster.get("autoscale", {}).get("min_workers"),
                            "max_workers": cluster.get("autoscale", {}).get("max_workers"),
                        } if cluster.get("autoscale") else None,
                    }
                    clusters.append(cluster_dict)
                    logger.info(f"Added cluster: {cluster_dict['cluster_name']} (State: {cluster_dict['state']})")
                
                except Exception as cluster_error:
                    logger.warning(f"Error processing cluster {cluster.get('cluster_id')}: {str(cluster_error)}")
                    # Add basic info even if processing fails
                    clusters.append({
                        "cluster_id": cluster.get("cluster_id"),
                        "cluster_name": cluster.get("cluster_name", f"Cluster-{cluster.get('cluster_id')}"),
                        "state": cluster.get("state", "UNKNOWN"),
                        "error": f"Could not process: {str(cluster_error)}"
                    })
            
            logger.info(f"Successfully fetched {len(clusters)} clusters from Databricks")
            return clusters
        
        except Exception as e:
            logger.error(f"Error fetching clusters: {str(e)}", exc_info=True)
            return []
    
    def get_cluster_metrics(self, cluster_id: str) -> Dict[str, Any]:
        """Fetch metrics for a specific cluster using REST API.
        
        Args:
            cluster_id: Cluster ID
            
        Returns:
            Dictionary with cluster metrics
        """
        try:
            url = f"{self.host}/api/2.1/clusters/get"
            params = {"cluster_id": cluster_id}
            
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            
            cluster = response.json()
            state = cluster.get("state")
            if isinstance(state, dict):
                state = state.get("cluster_state")
            
            return {
                "cluster_id": cluster_id,
                "state": state,
                "num_workers": cluster.get("num_workers", 0),
                "cluster_cores": cluster.get("cluster_cores"),
                "cluster_memory_mb": cluster.get("cluster_memory_mb"),
            }
        
        except Exception as e:
            logger.error(f"Error fetching metrics for cluster {cluster_id}: {str(e)}")
            return {}

    def get_cluster_info(self, cluster_id: str) -> Dict[str, Any]:
        """Get detailed information about a cluster including auto-termination settings.
        
        Args:
            cluster_id: Cluster ID
            
        Returns:
            Dictionary with cluster information including autotermination_minutes
        """
        try:
            url = f"{self.host}/api/2.1/clusters/get"
            params = {"cluster_id": cluster_id}
            
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            
            cluster = response.json()
            return {
                "status": "success",
                "cluster": cluster
            }
        except Exception as e:
            logger.error(f"Error fetching cluster info for {cluster_id}: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "cluster_id": cluster_id
            }

    def terminate_cluster(self, cluster_id: str) -> Dict[str, Any]:
        """Terminate a cluster using REST API.
        
        Args:
            cluster_id: Cluster ID
            
        Returns:
            Result dictionary
        """
        try:
            url = f"{self.host}/api/2.1/clusters/delete"
            payload = {"cluster_id": cluster_id}
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()
            return {"status": "success", "cluster_id": cluster_id, "action": "terminated"}
        except Exception as e:
            logger.error(f"Error terminating cluster {cluster_id}: {str(e)}", exc_info=True)
            return {"status": "error", "error": str(e), "cluster_id": cluster_id}

    def start_cluster(self, cluster_id: str) -> Dict[str, Any]:
        """Start a terminated cluster using REST API.
        
        Args:
            cluster_id: Cluster ID
            
        Returns:
            Result dictionary
        """
        try:
            url = f"{self.host}/api/2.1/clusters/start"
            payload = {"cluster_id": cluster_id}
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()
            logger.info(f"Successfully started cluster {cluster_id}")
            return {"status": "success", "cluster_id": cluster_id, "action": "started"}
        except Exception as e:
            logger.error(f"Error starting cluster {cluster_id}: {str(e)}", exc_info=True)
            return {"status": "error", "error": str(e), "cluster_id": cluster_id}

    def update_cluster_config(self, cluster_id: str, **kwargs) -> Dict[str, Any]:
        """Update cluster configuration including auto-termination.
        
        Args:
            cluster_id: Cluster ID
            **kwargs: Configuration options (e.g., autotermination_minutes)
            
        Returns:
            Result dictionary
        """
        try:
            # First, get the current cluster configuration
            cluster_info = self.get_cluster_info(cluster_id)
            if cluster_info.get("status") != "success":
                return {
                    "status": "error",
                    "error": f"Could not fetch cluster info: {cluster_info.get('error')}",
                    "cluster_id": cluster_id
                }
            
            # Get the cluster configuration
            cluster = cluster_info.get("cluster", {})
            
            # Build the edit payload with required fields
            url = f"{self.host}/api/2.1/clusters/edit"
            payload = {
                "cluster_id": cluster_id,
                "cluster_name": cluster.get("cluster_name"),
                "spark_version": cluster.get("spark_version"),
                "node_type_id": cluster.get("node_type_id"),
            }
            
            # Add autoscale or num_workers
            if "autoscale" in cluster:
                payload["autoscale"] = cluster["autoscale"]
            elif "num_workers" in cluster:
                payload["num_workers"] = cluster["num_workers"]
            
            # Add other important fields if present
            if "driver_node_type_id" in cluster:
                payload["driver_node_type_id"] = cluster["driver_node_type_id"]
            if "spark_conf" in cluster:
                payload["spark_conf"] = cluster["spark_conf"]
            if "aws_attributes" in cluster:
                payload["aws_attributes"] = cluster["aws_attributes"]
            if "azure_attributes" in cluster:
                payload["azure_attributes"] = cluster["azure_attributes"]
            if "spark_env_vars" in cluster:
                payload["spark_env_vars"] = cluster["spark_env_vars"]
            if "custom_tags" in cluster:
                payload["custom_tags"] = cluster["custom_tags"]
            if "init_scripts" in cluster:
                payload["init_scripts"] = cluster["init_scripts"]
            
            # Update with new values from kwargs
            payload.update(kwargs)
            
            logger.info(f"Updating cluster {cluster_id} with payload: {payload}")
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()
            
            logger.info(f"Successfully updated cluster {cluster_id} config: {kwargs}")
            return {
                "status": "success",
                "cluster_id": cluster_id,
                "action": "config_updated",
                "config": kwargs
            }
        except requests.exceptions.HTTPError as e:
            error_text = e.response.text if e.response is not None else str(e)
            logger.error(f"Error updating cluster {cluster_id} config: {error_text}", exc_info=True)
            return {"status": "error", "error": error_text, "cluster_id": cluster_id}
        except Exception as e:
            logger.error(f"Error updating cluster {cluster_id} config: {str(e)}", exc_info=True)
            return {"status": "error", "error": str(e), "cluster_id": cluster_id}

    def resize_cluster(
        self,
        cluster_id: str,
        num_workers: Optional[int] = None,
        autoscale: Optional[Dict[str, int]] = None
    ) -> Dict[str, Any]:
        """Resize a cluster using REST API.
        
        Args:
            cluster_id: Cluster ID
            num_workers: Fixed number of workers
            autoscale: Autoscale settings with min_workers and max_workers
            
        Returns:
            Result dictionary
        """
        try:
            url = f"{self.host}/api/2.1/clusters/resize"
            payload: Dict[str, Any] = {"cluster_id": cluster_id}
            if autoscale:
                payload["autoscale"] = autoscale
            elif num_workers is not None:
                payload["num_workers"] = num_workers
            else:
                return {"status": "error", "error": "num_workers or autoscale is required", "cluster_id": cluster_id}
            
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()
            return {"status": "success", "cluster_id": cluster_id, "payload": payload}
        except Exception as e:
            logger.error(f"Error resizing cluster {cluster_id}: {str(e)}", exc_info=True)
            return {"status": "error", "error": str(e), "cluster_id": cluster_id}
    
    def get_sql_warehouses(self) -> List[Dict[str, Any]]:
        """Fetch all SQL warehouses from Databricks workspace.
        
        Returns:
            List of SQL warehouse dictionaries
        """
        try:
            url = f"{self.host}/api/2.0/sql/warehouses"
            logger.info(f"Fetching SQL warehouses from: {url}")
            
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Handle different response formats
            warehouses = []
            if isinstance(data, list):
                warehouses = data
            elif isinstance(data, dict):
                # Try common keys for warehouse list
                warehouses = data.get("warehouses", [])
                if not warehouses:
                    warehouses = data.get("results", [])
                if not warehouses and "warehouse_id" in data:
                    # Single warehouse response
                    warehouses = [data]
            
            logger.info(f"Fetched {len(warehouses)} SQL warehouses")
            
            # Log warehouse details for debugging
            for warehouse in warehouses[:3]:  # Log first 3
                logger.debug(f"Warehouse: {warehouse.get('name', 'Unknown')} - ID: {warehouse.get('id', warehouse.get('warehouse_id', 'N/A'))} - State: {warehouse.get('state', 'N/A')}")
            
            return warehouses
        
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning("SQL warehouses API endpoint not found. This workspace may not have SQL warehouses enabled.")
            else:
                logger.error(f"HTTP error fetching SQL warehouses: {e.response.status_code} - {e.response.text}")
            return []
        except Exception as e:
            logger.error(f"Error fetching SQL warehouses: {str(e)}", exc_info=True)
            return []
    
    def get_instance_pools(self) -> List[Dict[str, Any]]:
        """Fetch all instance pools from Databricks workspace.
        
        Returns:
            List of instance pool dictionaries
        """
        try:
            url = f"{self.host}/api/2.0/instance-pools/list"
            logger.info(f"Fetching instance pools from: {url}")
            
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            pools = data.get("instance_pools", [])
            
            logger.info(f"Fetched {len(pools)} instance pools")
            return pools
        
        except Exception as e:
            logger.error(f"Error fetching instance pools: {str(e)}", exc_info=True)
            return []
    
    def get_vector_search_endpoints(self) -> List[Dict[str, Any]]:
        """Fetch all Vector Search endpoints from Databricks workspace.
        
        Returns:
            List of Vector Search endpoint dictionaries
        """
        try:
            url = f"{self.host}/api/2.0/vector-search/endpoints"
            logger.info(f"Fetching Vector Search endpoints from: {url}")
            
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            endpoints = data.get("endpoints", [])
            
            logger.info(f"Fetched {len(endpoints)} Vector Search endpoints")
            return endpoints
        
        except Exception as e:
            logger.error(f"Error fetching Vector Search endpoints: {str(e)}", exc_info=True)
            return []
    
    def get_cluster_policies(self) -> List[Dict[str, Any]]:
        """Fetch all cluster policies from Databricks workspace.
        
        Returns:
            List of cluster policy dictionaries
        """
        try:
            url = f"{self.host}/api/2.1/policies/clusters/list"
            logger.info(f"Fetching cluster policies from: {url}")
            
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            policies = data.get("policies", [])
            
            logger.info(f"Fetched {len(policies)} cluster policies")
            return policies
        
        except Exception as e:
            logger.error(f"Error fetching cluster policies: {str(e)}", exc_info=True)
            return []
    
    def get_apps(self) -> List[Dict[str, Any]]:
        """Fetch all apps from Databricks workspace.
        
        Returns:
            List of app dictionaries
        """
        try:
            url = f"{self.host}/api/2.0/apps/list"
            logger.info(f"Fetching apps from: {url}")
            
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            apps = data.get("apps", [])
            
            logger.info(f"Fetched {len(apps)} apps")
            return apps
        
        except Exception as e:
            logger.error(f"Error fetching apps: {str(e)}", exc_info=True)
            # Apps API might not be available in all workspaces
            logger.warning("Apps API may not be available in this workspace")
            return []
    
    def get_lakebase_provisioned(self) -> List[Dict[str, Any]]:
        """Fetch Lakebase Provisioned resources from Databricks workspace.
        
        Returns:
            List of Lakebase provisioned resource dictionaries
        """
        try:
            # Lakebase might be under Unity Catalog or a different endpoint
            # Try multiple possible endpoints
            endpoints_to_try = [
                "/api/2.1/unity-catalog/storage-credentials",
                "/api/2.1/unity-catalog/external-locations",
                "/api/2.0/lakebase/provisioned",
            ]
            
            all_resources = []
            for endpoint_path in endpoints_to_try:
                try:
                    url = f"{self.host}{endpoint_path}"
                    logger.info(f"Trying to fetch Lakebase resources from: {url}")
                    
                    response = requests.get(url, headers=self.headers, timeout=30)
                    if response.status_code == 200:
                        data = response.json()
                        # Handle different response formats
                        if isinstance(data, list):
                            all_resources.extend(data)
                        elif isinstance(data, dict):
                            # Try common keys
                            for key in ["storage_credentials", "external_locations", "resources", "items"]:
                                if key in data:
                                    all_resources.extend(data[key] if isinstance(data[key], list) else [data[key]])
                        logger.info(f"Found {len(all_resources)} Lakebase resources from {endpoint_path}")
                        break  # Success, no need to try other endpoints
                except Exception as e:
                    logger.debug(f"Endpoint {endpoint_path} not available: {str(e)}")
                    continue
            
            logger.info(f"Fetched {len(all_resources)} Lakebase provisioned resources")
            return all_resources
        
        except Exception as e:
            logger.error(f"Error fetching Lakebase provisioned resources: {str(e)}", exc_info=True)
            return []
    
    def get_mlflow_experiments(self) -> List[Dict[str, Any]]:
        """Fetch all MLflow experiments from Databricks workspace.
        
        Returns:
            List of MLflow experiment dictionaries
        """
        try:
            url = f"{self.host}/api/2.0/mlflow/experiments/search"
            logger.info(f"Fetching MLflow experiments from: {url}")
            
            response = requests.post(url, headers=self.headers, json={}, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            experiments = data.get("experiments", [])
            
            logger.info(f"Fetched {len(experiments)} MLflow experiments")
            return experiments
        
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning("MLflow experiments API endpoint not found. MLflow may not be enabled.")
            else:
                logger.error(f"HTTP error fetching MLflow experiments: {e.response.status_code}")
            return []
        except Exception as e:
            logger.error(f"Error fetching MLflow experiments: {str(e)}", exc_info=True)
            return []
    
    def get_mlflow_models(self) -> List[Dict[str, Any]]:
        """Fetch all MLflow registered models from Databricks workspace.
        
        Returns:
            List of MLflow model dictionaries
        """
        try:
            url = f"{self.host}/api/2.0/mlflow/registered-models/search"
            logger.info(f"Fetching MLflow models from: {url}")
            
            response = requests.post(url, headers=self.headers, json={}, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            models = data.get("registered_models", [])
            
            logger.info(f"Fetched {len(models)} MLflow models")
            return models
        
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning("MLflow models API endpoint not found. MLflow may not be enabled.")
            else:
                logger.error(f"HTTP error fetching MLflow models: {e.response.status_code}")
            return []
        except Exception as e:
            logger.error(f"Error fetching MLflow models: {str(e)}", exc_info=True)
            return []
    
    def get_model_serving_endpoints(self) -> List[Dict[str, Any]]:
        """Fetch all model serving endpoints from Databricks workspace.
        
        Returns:
            List of model serving endpoint dictionaries
        """
        try:
            url = f"{self.host}/api/2.0/serving-endpoints"
            logger.info(f"Fetching model serving endpoints from: {url}")
            
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            endpoints = data.get("endpoints", [])
            
            logger.info(f"Fetched {len(endpoints)} model serving endpoints")
            return endpoints
        
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning("Model serving endpoints API not found. Model serving may not be enabled.")
            else:
                logger.error(f"HTTP error fetching model serving endpoints: {e.response.status_code}")
            return []
        except Exception as e:
            logger.error(f"Error fetching model serving endpoints: {str(e)}", exc_info=True)
            return []
    
    def get_feature_store_tables(self) -> List[Dict[str, Any]]:
        """Fetch all feature store tables from Databricks workspace.
        
        Returns:
            List of feature store table dictionaries
        """
        try:
            # Feature Store API endpoint
            url = f"{self.host}/api/2.0/feature-store/feature-tables/search"
            logger.info(f"Fetching feature store tables from: {url}")
            
            response = requests.post(url, headers=self.headers, json={}, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            tables = data.get("feature_tables", [])
            
            logger.info(f"Fetched {len(tables)} feature store tables")
            return tables
        
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning("Feature store API endpoint not found. Feature Store may not be enabled.")
            else:
                logger.error(f"HTTP error fetching feature store tables: {e.response.status_code}")
            return []
        except Exception as e:
            logger.error(f"Error fetching feature store tables: {str(e)}", exc_info=True)
            return []
    
    def get_ml_jobs(self) -> List[Dict[str, Any]]:
        """Identify and return ML/AI jobs from the jobs list.
        
        Returns:
            List of ML/AI job dictionaries (filtered from all jobs)
        """
        try:
            all_jobs = self.get_all_jobs()
            
            # Filter jobs that are likely ML/AI jobs
            ml_jobs = []
            ml_keywords = ['ml', 'machine learning', 'model', 'training', 'inference', 'mlflow', 
                          'pytorch', 'tensorflow', 'xgboost', 'sklearn', 'spark ml', 'pipeline']
            
            for job in all_jobs:
                job_name = job.get("job_name", "").lower()
                job_settings = job.get("settings", {})
                tasks = job_settings.get("tasks", [])
                
                # Check if job name contains ML keywords
                is_ml_job = any(keyword in job_name for keyword in ml_keywords)
                
                # Check task configurations for ML libraries
                if not is_ml_job:
                    for task in tasks:
                        task_key = task.get("task_key", "").lower()
                        notebook_path = task.get("notebook_task", {}).get("notebook_path", "").lower()
                        spark_python_task = task.get("spark_python_task", {})
                        python_file = spark_python_task.get("python_file", "").lower()
                        
                        if (any(keyword in task_key for keyword in ml_keywords) or
                            any(keyword in notebook_path for keyword in ml_keywords) or
                            any(keyword in python_file for keyword in ml_keywords)):
                            is_ml_job = True
                            break
                
                if is_ml_job:
                    ml_jobs.append({
                        **job,
                        "ml_category": "ML/AI Job",
                        "detected_by": "keyword_match"
                    })
            
            logger.info(f"Identified {len(ml_jobs)} ML/AI jobs out of {len(all_jobs)} total jobs")
            return ml_jobs
        
        except Exception as e:
            logger.error(f"Error identifying ML jobs: {str(e)}", exc_info=True)
            return []
    
    def get_all_compute_resources(self) -> Dict[str, Any]:
        """Fetch all compute resources from Databricks workspace.
        
        Returns:
            Dictionary containing all compute resource types
        """
        return {
            "all_purpose_clusters": self.get_all_clusters(),
            "job_clusters": self.get_all_clusters(),  # Job clusters are also in clusters list
            "sql_warehouses": self.get_sql_warehouses(),
            "vector_search": self.get_vector_search_endpoints(),
            "pools": self.get_instance_pools(),
            "policies": self.get_cluster_policies(),
            "apps": self.get_apps(),
            "lakebase_provisioned": self.get_lakebase_provisioned(),
            "ml_jobs": self.get_ml_jobs(),
            "mlflow_experiments": self.get_mlflow_experiments(),
            "mlflow_models": self.get_mlflow_models(),
            "model_serving_endpoints": self.get_model_serving_endpoints(),
            "feature_store_tables": self.get_feature_store_tables(),
        }
    
    def execute_sql_query(self, query: str, warehouse_id: str = None) -> Dict[str, Any]:
        """Execute a SQL query using Databricks SQL Statement Execution API.
        
        Args:
            query: SQL query to execute
            warehouse_id: Optional SQL warehouse ID. If not provided, will use default warehouse.
            
        Returns:
            Dictionary containing query results and metadata
        """
        try:
            # If no warehouse_id provided, get the first available warehouse
            if not warehouse_id:
                warehouses = self.get_sql_warehouses()
                if not warehouses:
                    raise ValueError("No SQL warehouses available. Please provide a warehouse_id.")
                warehouse_id = warehouses[0].get("id")
                logger.info(f"Using warehouse: {warehouse_id}")
            
            url = f"{self.host}/api/2.0/sql/statements"
            
            payload = {
                "statement": query,
                "warehouse_id": warehouse_id,
                "wait_timeout": "30s"
            }
            
            logger.info(f"Executing SQL query on warehouse {warehouse_id}")
            response = requests.post(url, headers=self.headers, json=payload, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            
            # Extract results
            status = result.get("status", {}).get("state")
            
            if status == "SUCCEEDED":
                manifest = result.get("manifest", {})
                chunks = manifest.get("chunks", [])
                
                # Get result data
                result_data = result.get("result", {})
                data_array = result_data.get("data_array", [])
                
                # Get column names
                columns = [col.get("name") for col in manifest.get("schema", {}).get("columns", [])]
                
                # Convert to list of dictionaries
                rows = []
                for row in data_array:
                    row_dict = {columns[i]: row[i] for i in range(len(columns))}
                    rows.append(row_dict)
                
                logger.info(f"Query executed successfully. Returned {len(rows)} rows.")
                
                return {
                    "status": "success",
                    "rows": rows,
                    "row_count": len(rows),
                    "columns": columns,
                    "statement_id": result.get("statement_id")
                }
            else:
                error_message = result.get("status", {}).get("error", {}).get("message", "Unknown error")
                logger.error(f"Query execution failed: {error_message}")
                return {
                    "status": "failed",
                    "error": error_message,
                    "statement_id": result.get("statement_id")
                }
                
        except Exception as e:
            logger.error(f"Error executing SQL query: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }
    
    def read_delta_table(self, table_name: str, limit: int = 1000, warehouse_id: str = None) -> Dict[str, Any]:
        """Read data from a Delta table.
        
        Args:
            table_name: Name of the Delta table
                       - Hive metastore: database.table (e.g., 'default.cluster_events')
                       - Unity Catalog: catalog.schema.table (e.g., 'main.default.cluster_events')
            limit: Maximum number of rows to return
            warehouse_id: Optional SQL warehouse ID
            
        Returns:
            Dictionary containing table data and metadata
        """
        try:
            query = f"SELECT * FROM {table_name} LIMIT {limit}"
            logger.info(f"Reading Delta table: {table_name}")
            
            result = self.execute_sql_query(query, warehouse_id)
            
            # Check for Unity Catalog error
            if result.get("status") == "error":
                error_msg = str(result.get("error", ""))
                if "UC_NOT_ENABLED" in error_msg or "Unity Catalog is not enabled" in error_msg:
                    logger.warning(f"Unity Catalog not enabled. Table name '{table_name}' might be using Unity Catalog format.")
                    logger.warning("For Hive metastore, use format: database.table (e.g., 'default.cluster_events')")
                    result["error"] = f"Unity Catalog not enabled. Use Hive metastore format 'database.table' instead of 'catalog.schema.table'. Error: {error_msg}"
            
            if result.get("status") == "success":
                result["table_name"] = table_name
                logger.info(f"Successfully read {result.get('row_count', 0)} rows from {table_name}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error reading Delta table {table_name}: {str(e)}", exc_info=True)
            error_msg = str(e)
            
            # Provide helpful error message for Unity Catalog issues
            if "UC_NOT_ENABLED" in error_msg or "Unity Catalog is not enabled" in error_msg:
                error_msg = f"Unity Catalog not enabled. Use Hive metastore format 'database.table' (e.g., 'default.cluster_events') instead of Unity Catalog format 'catalog.schema.table'. Original error: {error_msg}"
            
            return {
                "status": "error",
                "error": error_msg,
                "table_name": table_name
            }


def get_databricks_client() -> "DatabricksClient":
    """Create a Databricks client using configured settings."""
    try:
        from config import settings
        if not settings.databricks_host or not settings.databricks_token:
            raise ValueError("Databricks client not configured")
        return DatabricksClient(host=settings.databricks_host, token=settings.databricks_token)
    except Exception as exc:
        logger.error(f"Failed to create Databricks client: {exc}")
        raise


