"""AI Agent for analyzing Databricks jobs and clusters to identify cost leaks."""
from typing import List, Dict, Any, Optional
from datetime import datetime
from langchain_openai import ChatOpenAI, AzureChatOpenAI
import json
import logging

logger = logging.getLogger(__name__)


class ClusterIQAgent:
    """AI Agent for cost optimization analysis."""
    
    def __init__(
        self,
        api_key: str = "",
        model: str = "gpt-4-turbo-preview",
        azure_endpoint: str = "",
        azure_api_key: str = "",
        azure_deployment_name: str = ""
    ):
        """Initialize the AI agent.
        
        Args:
            api_key: OpenAI API key (for standard OpenAI)
            model: Model name to use
            azure_endpoint: Azure OpenAI endpoint URL
            azure_api_key: Azure OpenAI API key
            azure_deployment_name: Azure OpenAI deployment name
        """
        # Use Azure OpenAI if credentials are provided, otherwise use standard OpenAI
        if azure_endpoint and azure_api_key and azure_deployment_name:
            # Ensure endpoint doesn't have trailing slash
            endpoint = azure_endpoint.rstrip('/')
            self.llm = AzureChatOpenAI(
                azure_endpoint=endpoint,
                azure_deployment=azure_deployment_name,
                openai_api_version="2024-02-15-preview",
                api_key=azure_api_key,
                temperature=1,
                model=azure_deployment_name,  # Use deployment name as model
            )
            logger.info(f"Using Azure OpenAI - Endpoint: {endpoint}, Deployment: {azure_deployment_name}")
        elif api_key:
            self.llm = ChatOpenAI(
                temperature=1,
                model=model,
                api_key=api_key,
            )
            logger.info("Using standard OpenAI")
        else:
            raise ValueError("Either OpenAI API key or Azure OpenAI credentials must be provided")
    
    def analyze_jobs_and_clusters(
        self,
        jobs: List[Dict[str, Any]],
        clusters: List[Dict[str, Any]],
        job_runs: Optional[Dict[int, List[Dict[str, Any]]]] = None
    ) -> List[Dict[str, Any]]:
        """Analyze jobs and clusters to identify cost leaks and optimization opportunities.
        
        Args:
            jobs: List of job dictionaries
            clusters: List of cluster dictionaries
            job_runs: Optional dictionary mapping job_id to list of runs
            
        Returns:
            List of recommendations with analysis
        """
        try:
            # Prepare context for AI analysis
            context = self._prepare_analysis_context(jobs, clusters, job_runs)
            
            # Create analysis prompt
            prompt = f"""Analyze the following Databricks jobs and clusters to identify:
1. Cost leaks (over-provisioned clusters, idle resources)
2. Value leaks (small jobs on large clusters, inefficient configurations)
3. Optimization opportunities (right-sizing, scheduling, resource allocation)

Context:
{json.dumps(context, indent=2)}

Provide detailed recommendations for each identified issue, including:
- Issue type (cost leak, value leak, optimization opportunity)
- Severity (high, medium, low)
- Current configuration
- Recommended configuration
- Estimated cost savings
- Risk assessment
- Implementation steps

Format the response as a JSON array of recommendations."""

            # Get AI analysis
            try:
                response = self.llm.invoke(prompt)
                # Handle both ChatOpenAI and AzureChatOpenAI response formats
                if hasattr(response, 'content'):
                    content = response.content
                elif isinstance(response, str):
                    content = response
                else:
                    # Try to get content from AIMessage or similar
                    content = str(response)
                recommendations = self._parse_recommendations(content)
            except Exception as e:
                logger.error(f"Error calling LLM: {str(e)}")
                # Return fallback analysis if LLM call fails
                recommendations = self._fallback_analysis(jobs, clusters)
            
            # Enhance with additional analysis
            enhanced_recommendations = self._enhance_recommendations(
                recommendations, jobs, clusters, job_runs
            )
            
            return enhanced_recommendations
        
        except Exception as e:
            logger.error(f"Error in AI analysis: {str(e)}")
            return self._fallback_analysis(jobs, clusters)

    def generate_summary(
        self,
        jobs: List[Dict[str, Any]],
        clusters: List[Dict[str, Any]]
    ) -> str:
        """Generate a short GenAI summary for jobs and clusters."""
        try:
            context = {
                "jobs_count": len(jobs),
                "clusters_count": len(clusters),
                "running_clusters": len([c for c in clusters if c.get("state") == "RUNNING"]),
                "idle_clusters": len([c for c in clusters if c.get("state") == "RUNNING" and c.get("num_workers", 0) > 0]),
            }
            prompt = (
                "You are an expert Databricks cost optimization analyst. "
                "Provide a concise 2-3 sentence summary of the current state "
                "based on this context, focusing on potential cost or value leaks:\n\n"
                f"{json.dumps(context, indent=2)}"
            )
            response = self.llm.invoke(prompt)
            if hasattr(response, 'content'):
                return response.content.strip()
            if isinstance(response, str):
                return response.strip()
            return str(response).strip()
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            return (
                f"Analyzed {len(jobs)} jobs and {len(clusters)} clusters. "
                "Review running clusters for potential idle time and cost optimization."
            )
    
    def analyze_all_compute(
        self,
        jobs: List[Dict[str, Any]],
        clusters: List[Dict[str, Any]],
        sql_warehouses: List[Dict[str, Any]],
        pools: List[Dict[str, Any]],
        vector_search: List[Dict[str, Any]],
        policies: List[Dict[str, Any]],
        apps: List[Dict[str, Any]],
        lakebase: List[Dict[str, Any]],
        ml_jobs: Optional[List[Dict[str, Any]]] = None,
        mlflow_experiments: Optional[List[Dict[str, Any]]] = None,
        mlflow_models: Optional[List[Dict[str, Any]]] = None,
        model_serving: Optional[List[Dict[str, Any]]] = None,
        feature_store: Optional[List[Dict[str, Any]]] = None,
        job_runs: Optional[Dict[int, List[Dict[str, Any]]]] = None
    ) -> List[Dict[str, Any]]:
        """Analyze all Databricks compute resources to identify cost leaks and optimization opportunities.
        
        Args:
            jobs: List of job dictionaries
            clusters: List of cluster dictionaries (all-purpose compute)
            sql_warehouses: List of SQL warehouse dictionaries
            pools: List of instance pool dictionaries
            vector_search: List of Vector Search endpoint dictionaries
            policies: List of cluster policy dictionaries
            apps: List of app dictionaries
            lakebase: List of Lakebase provisioned resource dictionaries
            job_runs: Optional dictionary mapping job_id to list of runs
            
        Returns:
            List of recommendations with analysis
        """
        try:
            # Prepare comprehensive context for AI analysis
            context = self._prepare_all_compute_context(
                jobs, clusters, sql_warehouses, pools, vector_search, policies, apps, lakebase,
                ml_jobs or [], mlflow_experiments or [], mlflow_models or [], 
                model_serving or [], feature_store or [], job_runs
            )
            
            # Create comprehensive analysis prompt for agentic AI
            prompt = f"""You are an expert Databricks cost optimization analyst. Analyze ALL compute resources to identify cost and value leaks.

COMPUTE INFRASTRUCTURE DATA:
{json.dumps(context, indent=2)}

ANALYSIS REQUIREMENTS:
1. **Cost Leaks**: Identify over-provisioned resources, idle compute, unnecessary running instances
   - All-purpose clusters (running but idle)
   - Job compute (over-provisioned job clusters)
   - SQL warehouses (running but unused)
   - Vector Search endpoints (idle endpoints)
   - Instance pools (unused or oversized pools)
   - Lakebase provisioned resources (underutilized)

2. **Value Leaks**: Detect inefficient resource allocation
   - Small/lightweight jobs running on oversized clusters
   - SQL warehouses sized incorrectly for workload
   - Vector Search endpoints over-provisioned
   - Policies allowing wasteful configurations
   - Apps consuming unnecessary resources

3. **Optimization Opportunities**: Find right-sizing, scheduling, and consolidation opportunities
   - Cluster right-sizing based on actual usage
   - SQL warehouse auto-stop/start configuration
   - Pool optimization
   - Policy improvements
   - Resource consolidation

For each issue found, provide:
- type: "cost_leak", "value_leak", or "optimization_opportunity"
- severity: "high", "medium", or "low"
- title: Clear, actionable title
- description: Detailed explanation of the issue
- resource_type: "cluster", "job", "sql_warehouse", "pool", "vector_search", "policy", "app", or "lakebase"
- resource_id: The specific resource ID
- current_config: Current configuration details
- recommended_config: Recommended changes
- estimated_savings: Estimated monthly cost savings (e.g., "$500/month" or "30% reduction")
- risk: "High", "Medium", or "Low"
- implementation_steps: Array of actionable steps

Return ONLY a valid JSON array of recommendations. Example format:
[
  {{
    "type": "cost_leak",
    "severity": "high",
    "title": "Idle SQL Warehouse detected",
    "description": "SQL warehouse has been running for 24+ hours with no active queries",
    "resource_type": "sql_warehouse",
    "resource_id": "warehouse-123",
    "current_config": {{"state": "RUNNING", "cluster_size": "Large"}},
    "recommended_config": {{"action": "Enable auto-stop after 10 minutes of inactivity"}},
    "estimated_savings": "$800/month",
    "risk": "Low",
    "implementation_steps": ["Enable auto-stop", "Set idle timeout to 10 minutes", "Monitor for 1 week"]
  }}
]"""

            # Get AI analysis
            try:
                response = self.llm.invoke(prompt)
                # Handle both ChatOpenAI and AzureChatOpenAI response formats
                if hasattr(response, 'content'):
                    content = response.content
                elif isinstance(response, str):
                    content = response
                else:
                    content = str(response)
                recommendations = self._parse_recommendations(content)
            except Exception as e:
                logger.error(f"Error calling LLM: {str(e)}")
                # Return fallback analysis if LLM call fails
                recommendations = self._fallback_all_compute_analysis(
                    jobs, clusters, sql_warehouses, pools, vector_search, policies, apps, lakebase,
                    ml_jobs or [], mlflow_experiments or [], mlflow_models or [],
                    model_serving or [], feature_store or []
                )
            
            # Enhance with additional analysis
            enhanced_recommendations = self._enhance_all_compute_recommendations(
                recommendations, jobs, clusters, sql_warehouses, pools, vector_search, policies, apps, lakebase,
                ml_jobs or [], mlflow_experiments or [], mlflow_models or [],
                model_serving or [], feature_store or [], job_runs
            )
            
            return enhanced_recommendations
        
        except Exception as e:
            logger.error(f"Error in AI analysis: {str(e)}")
            return self._fallback_all_compute_analysis(
                jobs, clusters, sql_warehouses, pools, vector_search, policies, apps, lakebase,
                ml_jobs or [], mlflow_experiments or [], mlflow_models or [],
                model_serving or [], feature_store or []
            )
    
    def _prepare_all_compute_context(
        self,
        jobs: List[Dict[str, Any]],
        clusters: List[Dict[str, Any]],
        sql_warehouses: List[Dict[str, Any]],
        pools: List[Dict[str, Any]],
        vector_search: List[Dict[str, Any]],
        policies: List[Dict[str, Any]],
        apps: List[Dict[str, Any]],
        lakebase: List[Dict[str, Any]],
        ml_jobs: List[Dict[str, Any]],
        mlflow_experiments: List[Dict[str, Any]],
        mlflow_models: List[Dict[str, Any]],
        model_serving: List[Dict[str, Any]],
        feature_store: List[Dict[str, Any]],
        job_runs: Optional[Dict[int, List[Dict[str, Any]]]] = None
    ) -> Dict[str, Any]:
        """Prepare comprehensive context for AI analysis of all compute types."""
        # Analyze all-purpose clusters
        cluster_analysis = []
        for cluster in clusters:
            if cluster.get("state") == "RUNNING":
                utilization_score = self._calculate_cluster_utilization(cluster)
                cluster_analysis.append({
                    "cluster_id": cluster.get("cluster_id"),
                    "cluster_name": cluster.get("cluster_name"),
                    "num_workers": cluster.get("num_workers", 0),
                    "node_type": cluster.get("node_type_id"),
                    "utilization_score": utilization_score,
                    "is_idle": utilization_score < 0.2,
                    "cluster_source": cluster.get("cluster_source", "UNKNOWN"),
                })
        
        # Analyze job compute (clusters used by jobs)
        job_cluster_analysis = []
        for job in jobs:
            tasks = job.get("settings", {}).get("tasks", [])
            for task in tasks:
                if task.get("new_cluster"):
                    job_cluster_analysis.append({
                        "job_id": job.get("job_id"),
                        "job_name": job.get("job_name"),
                        "cluster_config": task.get("new_cluster"),
                    })
        
        # Analyze SQL warehouses
        sql_warehouse_analysis = []
        for warehouse in sql_warehouses:
            sql_warehouse_analysis.append({
                "id": warehouse.get("id"),
                "name": warehouse.get("name"),
                "state": warehouse.get("state"),
                "cluster_size": warehouse.get("cluster_size"),
                "warehouse_type": warehouse.get("warehouse_type"),
            })
        
        # Analyze instance pools
        pool_analysis = []
        for pool in pools:
            pool_analysis.append({
                "instance_pool_id": pool.get("instance_pool_id"),
                "instance_pool_name": pool.get("instance_pool_name"),
                "node_type_id": pool.get("node_type_id"),
                "min_idle_instances": pool.get("min_idle_instances", 0),
                "max_capacity": pool.get("max_capacity"),
                "status": pool.get("status", {}),
            })
        
        # Analyze Vector Search endpoints
        vector_search_analysis = []
        for endpoint in vector_search:
            vector_search_analysis.append({
                "endpoint_name": endpoint.get("name"),
                "endpoint_id": endpoint.get("id"),
                "status": endpoint.get("status"),
            })
        
        # Analyze policies
        policy_analysis = []
        for policy in policies:
            policy_analysis.append({
                "policy_id": policy.get("policy_id"),
                "name": policy.get("name"),
                "definition": policy.get("definition"),
            })
        
        # Analyze apps
        app_analysis = []
        for app in apps:
            app_analysis.append({
                "app_id": app.get("id"),
                "name": app.get("name"),
                "status": app.get("status"),
            })
        
        # Analyze Lakebase resources
        lakebase_analysis = []
        for resource in lakebase:
            lakebase_analysis.append({
                "resource_id": resource.get("id") or resource.get("name"),
                "resource_type": resource.get("type") or "lakebase",
                "status": resource.get("status"),
            })
        
        return {
            "all_purpose_clusters": cluster_analysis,
            "job_compute": job_cluster_analysis,
            "sql_warehouses": sql_warehouse_analysis,
            "instance_pools": pool_analysis,
            "vector_search_endpoints": vector_search_analysis,
            "policies": policy_analysis,
            "apps": app_analysis,
            "lakebase_provisioned": lakebase_analysis,
            "summary": {
                "total_clusters": len(clusters),
                "running_clusters": len([c for c in clusters if c.get("state") == "RUNNING"]),
                "total_jobs": len(jobs),
                "sql_warehouses": len(sql_warehouses),
                "pools": len(pools),
                "vector_search_endpoints": len(vector_search),
                "policies": len(policies),
                "apps": len(apps),
                "lakebase_resources": len(lakebase),
            }
        }
    
    def _fallback_all_compute_analysis(
        self,
        jobs: List[Dict[str, Any]],
        clusters: List[Dict[str, Any]],
        sql_warehouses: List[Dict[str, Any]],
        pools: List[Dict[str, Any]],
        vector_search: List[Dict[str, Any]],
        policies: List[Dict[str, Any]],
        apps: List[Dict[str, Any]],
        lakebase: List[Dict[str, Any]],
        ml_jobs: List[Dict[str, Any]],
        mlflow_experiments: List[Dict[str, Any]],
        mlflow_models: List[Dict[str, Any]],
        model_serving: List[Dict[str, Any]],
        feature_store: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Fallback analysis when AI is not available."""
        recommendations = []
        
        # Basic cluster analysis
        for cluster in clusters:
            if cluster.get("state") == "RUNNING":
                recommendations.append({
                    "type": "cost_leak",
                    "severity": "medium",
                    "title": f"Running cluster: {cluster.get('cluster_name')}",
                    "description": "Cluster is running. Monitor for idle time.",
                    "resource_type": "cluster",
                    "resource_id": cluster.get("cluster_id"),
                    "estimated_savings": "Medium",
                    "risk": "Low",
                })
        
        # SQL warehouse analysis
        for warehouse in sql_warehouses:
            if warehouse.get("state") == "RUNNING":
                recommendations.append({
                    "type": "cost_leak",
                    "severity": "medium",
                    "title": f"Running SQL Warehouse: {warehouse.get('name')}",
                    "description": "SQL warehouse is running. Consider auto-stop if idle.",
                    "resource_type": "sql_warehouse",
                    "resource_id": warehouse.get("id"),
                    "estimated_savings": "Medium",
                    "risk": "Low",
                })
        
        # ML/AI job analysis
        for ml_job in ml_jobs:
            recommendations.append({
                "type": "optimization_opportunity",
                "severity": "low",
                "title": f"ML/AI Job detected: {ml_job.get('job_name')}",
                "description": "ML/AI job identified. Monitor for resource optimization opportunities.",
                "resource_type": "ml_job",
                "resource_id": ml_job.get("job_id"),
                "estimated_savings": "Review needed",
                "risk": "Low",
            })
        
        # Model serving endpoint analysis
        for endpoint in model_serving:
            if endpoint.get("state", {}).get("ready") == "READY":
                recommendations.append({
                    "type": "cost_leak",
                    "severity": "medium",
                    "title": f"Active Model Serving Endpoint: {endpoint.get('name')}",
                    "description": "Model serving endpoint is active. Monitor usage and costs.",
                    "resource_type": "model_serving",
                    "resource_id": endpoint.get("name"),
                    "estimated_savings": "Medium",
                    "risk": "Low",
                })
        
        return recommendations
    
    def _enhance_all_compute_recommendations(
        self,
        recommendations: List[Dict[str, Any]],
        jobs: List[Dict[str, Any]],
        clusters: List[Dict[str, Any]],
        sql_warehouses: List[Dict[str, Any]],
        pools: List[Dict[str, Any]],
        vector_search: List[Dict[str, Any]],
        policies: List[Dict[str, Any]],
        apps: List[Dict[str, Any]],
        lakebase: List[Dict[str, Any]],
        ml_jobs: List[Dict[str, Any]],
        mlflow_experiments: List[Dict[str, Any]],
        mlflow_models: List[Dict[str, Any]],
        model_serving: List[Dict[str, Any]],
        feature_store: List[Dict[str, Any]],
        job_runs: Optional[Dict[int, List[Dict[str, Any]]]] = None
    ) -> List[Dict[str, Any]]:
        """Enhance recommendations with additional metadata."""
        for rec in recommendations:
            if "timestamp" not in rec:
                rec["timestamp"] = datetime.utcnow().isoformat()
            if "id" not in rec:
                rec["id"] = f"rec_{hash(str(rec))}"
        
        return recommendations
    
    def _prepare_analysis_context(
        self,
        jobs: List[Dict[str, Any]],
        clusters: List[Dict[str, Any]],
        job_runs: Optional[Dict[int, List[Dict[str, Any]]]] = None
    ) -> Dict[str, Any]:
        """Prepare context for AI analysis."""
        # Analyze cluster utilization
        cluster_analysis = []
        for cluster in clusters:
            if cluster.get("state") == "RUNNING":
                utilization_score = self._calculate_cluster_utilization(cluster)
                cluster_analysis.append({
                    "cluster_id": cluster.get("cluster_id"),
                    "cluster_name": cluster.get("cluster_name"),
                    "num_workers": cluster.get("num_workers", 0),
                    "node_type": cluster.get("node_type_id"),
                    "utilization_score": utilization_score,
                    "is_idle": utilization_score < 0.2,
                })
        
        # Analyze job patterns
        job_analysis = []
        for job in jobs:
            runs = job_runs.get(job.get("job_id"), []) if job_runs else []
            avg_duration = self._calculate_avg_duration(runs)
            job_analysis.append({
                "job_id": job.get("job_id"),
                "job_name": job.get("job_name"),
                "num_tasks": len(job.get("settings", {}).get("tasks", [])),
                "avg_duration_seconds": avg_duration,
                "cluster_config": self._extract_cluster_config(job),
            })
        
        return {
            "clusters": cluster_analysis,
            "jobs": job_analysis,
            "summary": {
                "total_clusters": len(clusters),
                "running_clusters": len([c for c in clusters if c.get("state") == "RUNNING"]),
                "total_jobs": len(jobs),
            }
        }
    
    def _calculate_cluster_utilization(self, cluster: Dict[str, Any]) -> float:
        """Calculate cluster utilization score (0-1)."""
        # Simplified utilization calculation
        # In production, this would use actual metrics
        num_workers = cluster.get("num_workers", 0)
        if num_workers == 0:
            return 0.0
        
        # Placeholder: would use actual metrics from Databricks
        # For now, return a heuristic based on cluster age and activity
        return 0.5  # Default moderate utilization
    
    def _calculate_avg_duration(self, runs: List[Dict[str, Any]]) -> Optional[float]:
        """Calculate average duration of job runs."""
        if not runs:
            return None
        
        durations = [
            run.get("duration")
            for run in runs
            if run.get("duration") is not None
        ]
        
        return sum(durations) / len(durations) if durations else None
    
    def _extract_cluster_config(self, job: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract cluster configuration from job."""
        tasks = job.get("settings", {}).get("tasks", [])
        if not tasks:
            return None
        
        # Get cluster config from first task
        first_task = tasks[0]
        if first_task.get("new_cluster"):
            return first_task.get("new_cluster")
        elif first_task.get("cluster_id"):
            return {"cluster_id": first_task.get("cluster_id")}
        
        return None
    
    def _parse_recommendations(self, content: str) -> List[Dict[str, Any]]:
        """Parse AI response into structured recommendations."""
        try:
            # Try to extract JSON from response
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0].strip()
            else:
                json_str = content.strip()
            
            recommendations = json.loads(json_str)
            if isinstance(recommendations, list):
                return recommendations
            elif isinstance(recommendations, dict) and "recommendations" in recommendations:
                return recommendations["recommendations"]
            else:
                return [recommendations]
        
        except json.JSONDecodeError:
            logger.warning("Failed to parse AI response as JSON, using fallback")
            return []
    
    def _enhance_recommendations(
        self,
        recommendations: List[Dict[str, Any]],
        jobs: List[Dict[str, Any]],
        clusters: List[Dict[str, Any]],
        job_runs: Optional[Dict[int, List[Dict[str, Any]]]] = None
    ) -> List[Dict[str, Any]]:
        """Enhance recommendations with additional analysis."""
        enhanced = []
        
        for rec in recommendations:
            enhanced_rec = {
                **rec,
                "id": f"rec_{len(enhanced)}",
                "timestamp": self._get_current_timestamp(),
                "confidence_score": rec.get("confidence_score", 0.7),
            }
            enhanced.append(enhanced_rec)
        
        return enhanced
    
    def _fallback_analysis(
        self,
        jobs: List[Dict[str, Any]],
        clusters: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Fallback analysis when AI fails."""
        recommendations = []
        
        # Check for idle clusters
        for cluster in clusters:
            if cluster.get("state") == "RUNNING" and cluster.get("num_workers", 0) > 0:
                recommendations.append({
                    "id": f"rec_{len(recommendations)}",
                    "type": "cost_leak",
                    "severity": "medium",
                    "title": f"Idle cluster detected: {cluster.get('cluster_name')}",
                    "description": "Cluster appears to be running with low utilization",
                    "resource_type": "cluster",
                    "resource_id": cluster.get("cluster_id"),
                    "current_config": {
                        "num_workers": cluster.get("num_workers"),
                        "node_type": cluster.get("node_type_id"),
                    },
                    "recommended_config": {
                        "action": "Terminate if idle for extended period",
                    },
                    "estimated_savings": "Medium",
                    "risk": "Low",
                })
        
        return recommendations
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp as ISO string."""
        from datetime import datetime
        return datetime.utcnow().isoformat()
    
    def summarize_delta_table_data(
        self,
        table_data: Dict[str, Any],
        analysis_focus: str = "general"
    ) -> Dict[str, Any]:
        """Analyze and summarize data from a Delta table containing cluster and job logs.
        
        Args:
            table_data: Dictionary containing the Delta table data with 'rows', 'columns', etc.
            analysis_focus: Focus of the analysis - 'general', 'cost', 'performance', 'errors', etc.
            
        Returns:
            Dictionary containing the summary and insights
        """
        try:
            if table_data.get("status") != "success":
                return {
                    "status": "error",
                    "error": "Failed to read Delta table data",
                    "details": table_data.get("error", "Unknown error")
                }
            
            rows = table_data.get("rows", [])
            columns = table_data.get("columns", [])
            table_name = table_data.get("table_name", "Unknown")
            
            if not rows:
                return {
                    "status": "success",
                    "table_name": table_name,
                    "summary": "The table is empty or contains no data.",
                    "row_count": 0,
                    "insights": []
                }
            
            # Prepare data context for AI analysis
            data_sample = rows[:100]  # Use first 100 rows for analysis
            
            # Create focused prompt based on analysis type
            focus_instructions = {
                "general": "Provide a comprehensive overview of the logs, identifying key patterns, trends, and anomalies.",
                "cost": "Focus on identifying cost-related issues, resource wastage, and optimization opportunities.",
                "performance": "Analyze performance metrics, bottlenecks, and execution times.",
                "errors": "Identify errors, failures, and their patterns across the logs.",
                "usage": "Analyze usage patterns, cluster utilization, and job execution frequency."
            }
            
            instruction = focus_instructions.get(analysis_focus, focus_instructions["general"])
            
            prompt = f"""You are an expert Databricks analyst. Analyze the following cluster and job logs data from Delta table '{table_name}'.

DATA SAMPLE (showing {len(data_sample)} of {len(rows)} total rows):
Columns: {', '.join(columns)}

Sample Data:
{json.dumps(data_sample, indent=2, default=str)}

ANALYSIS INSTRUCTIONS:
{instruction}

Provide your analysis in the following JSON format:
{{
    "summary": "2-3 sentence high-level summary of the data",
    "key_findings": [
        "Finding 1",
        "Finding 2",
        ...
    ],
    "insights": [
        {{
            "category": "cost|performance|reliability|usage",
            "severity": "high|medium|low",
            "title": "Brief title",
            "description": "Detailed description",
            "recommendation": "Actionable recommendation"
        }}
    ],
    "statistics": {{
        "total_records": {len(rows)},
        "key_metrics": {{}}
    }}
}}
"""

            # Get AI analysis
            logger.info(f"Generating summary for Delta table: {table_name}")
            response = self.llm.invoke(prompt)
            
            # Extract content from response
            if hasattr(response, 'content'):
                content = response.content
            elif isinstance(response, str):
                content = response
            else:
                content = str(response)
            
            # Parse the JSON response
            try:
                # Try to extract JSON from the response
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    analysis_result = json.loads(json_match.group())
                else:
                    # If no JSON found, create structured response from text
                    analysis_result = {
                        "summary": content,
                        "key_findings": [],
                        "insights": [],
                        "statistics": {
                            "total_records": len(rows),
                            "key_metrics": {}
                        }
                    }
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                analysis_result = {
                    "summary": content,
                    "key_findings": [],
                    "insights": [],
                    "statistics": {
                        "total_records": len(rows),
                        "key_metrics": {}
                    }
                }
            
            # Add metadata
            result = {
                "status": "success",
                "table_name": table_name,
                "row_count": len(rows),
                "column_count": len(columns),
                "columns": columns,
                "analysis_focus": analysis_focus,
                **analysis_result
            }
            
            logger.info(f"Successfully generated summary for {table_name}")
            return result
            
        except Exception as e:
            logger.error(f"Error summarizing Delta table data: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "table_name": table_data.get("table_name", "Unknown")
            }

    def analyze_delta_logs(
        self,
        cluster_events: Dict[str, Any],
        cluster_logs: Dict[str, Any],
        job_run_logs: Dict[str, Any],
        analysis_focus: str = "cost"
    ) -> Dict[str, Any]:
        """Analyze Delta log tables and produce actionable recommendations.
        
        Returns a dict with summary and recommendations.
        """
        try:
            sources = {
                "cluster_events": cluster_events.get("rows", [])[:200],
                "cluster_logs": cluster_logs.get("rows", [])[:200],
                "job_run_logs": job_run_logs.get("rows", [])[:200],
            }

            prompt = f"""You are an expert Databricks optimization analyst. Analyze these Delta log samples and produce optimization recommendations.

Focus: {analysis_focus}

Cluster Events Sample:
{json.dumps(sources['cluster_events'], indent=2, default=str)}

Cluster Logs Sample:
{json.dumps(sources['cluster_logs'], indent=2, default=str)}

Job Run Logs Sample:
{json.dumps(sources['job_run_logs'], indent=2, default=str)}

Return ONLY valid JSON in the following format:
{{
  "summary": "2-3 sentence summary",
  "recommendations": [
    {{
      "title": "Short title",
      "description": "Details and evidence",
      "type": "cost_leak|value_leak|optimization_opportunity",
      "severity": "high|medium|low",
      "resource_type": "cluster|job|sql_warehouse",
      "resource_id": "<id if available>",
      "estimated_savings": "<amount or percentage>",
      "risk": "low|medium|high",
      "action": {{
        "type": "terminate_cluster|resize_cluster",
        "target_id": "<cluster_id>",
        "params": {{ "num_workers": 2 }}
      }}
    }}
  ]
}}
"""

            response = self.llm.invoke(prompt)
            if hasattr(response, 'content'):
                content = response.content
            elif isinstance(response, str):
                content = response
            else:
                content = str(response)

            try:
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    result = {"summary": content, "recommendations": []}
            except json.JSONDecodeError:
                result = {"summary": content, "recommendations": []}

            # Normalize recommendations
            recs = result.get("recommendations", [])
            normalized = []
            for rec in recs:
                action = rec.get("action") or {}
                normalized.append({
                    "title": rec.get("title", "Optimization Opportunity"),
                    "description": rec.get("description", ""),
                    "type": rec.get("type", "optimization_opportunity"),
                    "severity": rec.get("severity", "medium"),
                    "resource_type": rec.get("resource_type", "cluster"),
                    "resource_id": rec.get("resource_id"),
                    "estimated_savings": rec.get("estimated_savings", ""),
                    "risk": rec.get("risk", "low"),
                    "action": {
                        "type": action.get("type"),
                        "target_id": action.get("target_id"),
                        "params": action.get("params", {})
                    },
                    "status": "PENDING"
                })

            return {
                "status": "success",
                "summary": result.get("summary", ""),
                "recommendations": normalized
            }
        except Exception as e:
            logger.error(f"Error analyzing delta logs: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "recommendations": []
            }

