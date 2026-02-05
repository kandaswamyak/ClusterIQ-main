"""Simple HTTP server for ClusterIQ using Python's built-in http.server."""
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import logging
from datetime import datetime

from config import settings
from databricks_client import DatabricksClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def perform_basic_analysis(jobs, clusters):
    """Perform rule-based analysis without AI."""
    recommendations = []
    
    # Analyze clusters
    for cluster in clusters:
        state = cluster.get("state", "")
        num_workers = cluster.get("num_workers", 0)
        cluster_name = cluster.get("cluster_name", "Unknown")
        cluster_id = cluster.get("cluster_id")
        
        # Check for running clusters that might be idle
        if state == "RUNNING":
            if num_workers > 0:
                recommendations.append({
                    "id": f"rec_{len(recommendations)}",
                    "type": "cost_leak",
                    "severity": "medium",
                    "title": f"Running cluster: {cluster_name}",
                    "description": f"Cluster is running with {num_workers} workers. Monitor for idle time and consider auto-termination if not actively used.",
                    "resource_type": "cluster",
                    "resource_id": cluster_id,
                    "current_config": {
                        "num_workers": num_workers,
                        "node_type": cluster.get("node_type_id"),
                        "state": state,
                        "autotermination_minutes": cluster.get("autotermination_minutes"),
                    },
                    "recommended_config": {
                        "action": "Set auto-termination if cluster is idle for extended periods",
                        "suggested_autotermination": 15,
                    },
                    "estimated_savings": "Medium - depends on idle time",
                    "risk": "Low",
                })
            else:
                # Single node cluster
                recommendations.append({
                    "id": f"rec_{len(recommendations)}",
                    "type": "optimization",
                    "severity": "low",
                    "title": f"Single-node cluster: {cluster_name}",
                    "description": "Single-node cluster detected. Suitable for lightweight workloads.",
                    "resource_type": "cluster",
                    "resource_id": cluster_id,
                    "current_config": {
                        "num_workers": 0,
                        "node_type": cluster.get("node_type_id"),
                    },
                    "recommended_config": {
                        "action": "Continue using single-node for cost efficiency",
                    },
                    "estimated_savings": "Already optimized",
                    "risk": "None",
                })
        
        # Check for terminated clusters that were recently active
        elif state == "TERMINATED":
            terminated_time = cluster.get("terminated_time")
            if terminated_time:
                # Could add logic to check if it was terminated recently
                pass
    
    # Analyze jobs
    for job in jobs:
        job_name = job.get("job_name", "Unknown")
        job_id = job.get("job_id")
        tasks = job.get("settings", {}).get("tasks", [])
        
        if len(tasks) == 0:
            recommendations.append({
                "id": f"rec_{len(recommendations)}",
                "type": "optimization",
                "severity": "low",
                "title": f"Job with no tasks: {job_name}",
                "description": "Job has no configured tasks. Consider reviewing job configuration.",
                "resource_type": "job",
                "resource_id": job_id,
                "estimated_savings": "N/A",
                "risk": "Low",
            })
    
    # If no recommendations, add a summary
    if len(recommendations) == 0:
        recommendations.append({
            "id": "rec_summary",
            "type": "info",
            "severity": "low",
            "title": "Analysis Complete",
            "description": f"Analyzed {len(jobs)} jobs and {len(clusters)} clusters. No immediate optimization opportunities detected.",
            "estimated_savings": "Continue monitoring",
            "risk": "None",
        })
    
    return recommendations

# Initialize clients
databricks_client = None
ai_agent = None
analysis_cache = {}
cache_timestamp = None

# Initialize clients
try:
    if settings.databricks_host and settings.databricks_token:
        databricks_client = DatabricksClient(
            host=settings.databricks_host,
            token=settings.databricks_token
        )
        logger.info("Databricks client initialized")
    
    # Try to initialize AI agent (optional)
    try:
        from ai_agent import ClusterIQAgent
        if settings.azure_openai_endpoint and settings.azure_openai_api_key and settings.azure_openai_deployment_name:
            ai_agent = ClusterIQAgent(
                azure_endpoint=settings.azure_openai_endpoint,
                azure_api_key=settings.azure_openai_api_key,
                azure_deployment_name=settings.azure_openai_deployment_name,
                model=settings.openai_model
            )
            logger.info("AI agent initialized")
        elif settings.openai_api_key:
            ai_agent = ClusterIQAgent(
                api_key=settings.openai_api_key,
                model=settings.openai_model
            )
            logger.info("AI agent initialized")
    except ImportError as e:
        logger.warning(f"AI agent not available (langchain not installed): {str(e)}")
        logger.info("Server will run without AI features. Clusters and jobs will still work.")
    except Exception as e:
        logger.warning(f"Could not initialize AI agent: {str(e)}")
        logger.info("Server will run without AI features.")
        
except Exception as e:
    logger.error(f"Error during startup: {str(e)}")


class APIHandler(BaseHTTPRequestHandler):
    """HTTP request handler for ClusterIQ API."""
    
    def _set_cors_headers(self):
        """Set CORS headers."""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
    
    def _send_json_response(self, data, status=200):
        """Send JSON response."""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self._set_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
    
    def do_OPTIONS(self):
        """Handle OPTIONS request for CORS."""
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        try:
            if path == '/' or path == '/health':
                self._send_json_response({
                    "status": "healthy",
                    "databricks_configured": databricks_client is not None,
                    "ai_configured": ai_agent is not None,
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            elif path == '/api/jobs':
                if not databricks_client:
                    self._send_json_response({"error": "Databricks client not configured"}, 503)
                    return
                jobs = databricks_client.get_all_jobs()
                self._send_json_response(jobs)
            
            elif path.startswith('/api/jobs/') and '/runs' in path:
                job_id = int(path.split('/')[3])
                if not databricks_client:
                    self._send_json_response({"error": "Databricks client not configured"}, 503)
                    return
                runs = databricks_client.get_job_runs(job_id=job_id)
                self._send_json_response(runs)
            
            elif path == '/api/clusters':
                if not databricks_client:
                    self._send_json_response({"error": "Databricks client not configured"}, 503)
                    return
                logger.info("API: Fetching clusters...")
                clusters = databricks_client.get_all_clusters()
                logger.info(f"API: Returning {len(clusters)} clusters")
                self._send_json_response(clusters)
            
            elif path.startswith('/api/clusters/') and path.endswith('/metrics'):
                cluster_id = path.split('/')[3]
                if not databricks_client:
                    self._send_json_response({"error": "Databricks client not configured"}, 503)
                    return
                metrics = databricks_client.get_cluster_metrics(cluster_id)
                self._send_json_response(metrics)
            
            elif path == '/api/sql-warehouses':
                if not databricks_client:
                    self._send_json_response({"error": "Databricks client not configured"}, 503)
                    return
                warehouses = databricks_client.get_sql_warehouses()
                self._send_json_response(warehouses)
            
            elif path == '/api/pools':
                if not databricks_client:
                    self._send_json_response({"error": "Databricks client not configured"}, 503)
                    return
                pools = databricks_client.get_instance_pools()
                self._send_json_response(pools)
            
            elif path == '/api/vector-search':
                if not databricks_client:
                    self._send_json_response({"error": "Databricks client not configured"}, 503)
                    return
                endpoints = databricks_client.get_vector_search_endpoints()
                self._send_json_response(endpoints)
            
            elif path == '/api/policies':
                if not databricks_client:
                    self._send_json_response({"error": "Databricks client not configured"}, 503)
                    return
                policies = databricks_client.get_cluster_policies()
                self._send_json_response(policies)
            
            elif path == '/api/apps':
                if not databricks_client:
                    self._send_json_response({"error": "Databricks client not configured"}, 503)
                    return
                apps = databricks_client.get_apps()
                self._send_json_response(apps)
            
            elif path == '/api/lakebase':
                if not databricks_client:
                    self._send_json_response({"error": "Databricks client not configured"}, 503)
                    return
                lakebase = databricks_client.get_lakebase_provisioned()
                self._send_json_response(lakebase)
            
            elif path == '/api/ml-jobs':
                if not databricks_client:
                    self._send_json_response({"error": "Databricks client not configured"}, 503)
                    return
                ml_jobs = databricks_client.get_ml_jobs()
                self._send_json_response(ml_jobs)
            
            elif path == '/api/mlflow-experiments':
                if not databricks_client:
                    self._send_json_response({"error": "Databricks client not configured"}, 503)
                    return
                experiments = databricks_client.get_mlflow_experiments()
                self._send_json_response(experiments)
            
            elif path == '/api/mlflow-models':
                if not databricks_client:
                    self._send_json_response({"error": "Databricks client not configured"}, 503)
                    return
                models = databricks_client.get_mlflow_models()
                self._send_json_response(models)
            
            elif path == '/api/model-serving':
                if not databricks_client:
                    self._send_json_response({"error": "Databricks client not configured"}, 503)
                    return
                endpoints = databricks_client.get_model_serving_endpoints()
                self._send_json_response(endpoints)
            
            elif path == '/api/feature-store':
                if not databricks_client:
                    self._send_json_response({"error": "Databricks client not configured"}, 503)
                    return
                tables = databricks_client.get_feature_store_tables()
                self._send_json_response(tables)
            
            elif path == '/api/compute':
                if not databricks_client:
                    self._send_json_response({"error": "Databricks client not configured"}, 503)
                    return
                all_compute = databricks_client.get_all_compute_resources()
                self._send_json_response(all_compute)
            
            elif path == '/api/stats':
                if not databricks_client:
                    self._send_json_response({"error": "Databricks client not configured"}, 503)
                    return
                jobs = databricks_client.get_all_jobs()
                clusters = databricks_client.get_all_clusters()
                warehouses = databricks_client.get_sql_warehouses()
                pools = databricks_client.get_instance_pools()
                vector_search = databricks_client.get_vector_search_endpoints()
                policies = databricks_client.get_cluster_policies()
                apps = databricks_client.get_apps()
                lakebase = databricks_client.get_lakebase_provisioned()
                ml_jobs = databricks_client.get_ml_jobs()
                mlflow_experiments = databricks_client.get_mlflow_experiments()
                mlflow_models = databricks_client.get_mlflow_models()
                model_serving = databricks_client.get_model_serving_endpoints()
                feature_store = databricks_client.get_feature_store_tables()
                running_clusters = [c for c in clusters if c.get("state") == "RUNNING"]
                self._send_json_response({
                    "total_jobs": len(jobs),
                    "total_clusters": len(clusters),
                    "running_clusters": len(running_clusters),
                    "sql_warehouses": len(warehouses),
                    "pools": len(pools),
                    "vector_search_endpoints": len(vector_search),
                    "policies": len(policies),
                    "apps": len(apps),
                    "lakebase_resources": len(lakebase),
                    "ml_jobs": len(ml_jobs),
                    "mlflow_experiments": len(mlflow_experiments),
                    "mlflow_models": len(mlflow_models),
                    "model_serving_endpoints": len(model_serving),
                    "feature_store_tables": len(feature_store),
                    "idle_clusters": len([c for c in running_clusters if c.get("num_workers", 0) > 0]),
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            elif path == '/api/recommendations':
                if not analysis_cache or not analysis_cache.get("recommendations"):
                    self._send_json_response({
                        "recommendations": [],
                        "has_analysis": False,
                        "message": "No analysis available. Please run analysis first."
                    }, 200)
                    return
                response_data = {
                    **analysis_cache,
                    "has_analysis": True
                }
                self._send_json_response(response_data)
            
            elif path == '/api/recommendations/real-time':
                # Real-time recommendations endpoint - same as regular recommendations
                if not analysis_cache or not analysis_cache.get("recommendations"):
                    self._send_json_response({
                        "recommendations": [],
                        "timestamp": datetime.utcnow().isoformat(),
                        "real_time": True,
                        "message": "No analysis available. Please run analysis first.",
                        "has_analysis": False
                    }, 200)
                    return
                
                # Return recommendations in real-time format
                response_data = {
                    **analysis_cache,
                    "real_time": True,
                    "has_analysis": True,
                    "timestamp": cache_timestamp.isoformat() if cache_timestamp else datetime.utcnow().isoformat()
                }
                self._send_json_response(response_data)
            
            elif path == '/api/summary':
                # Calculate summary metrics from recommendations
                try:
                    recommendations = analysis_cache.get("recommendations", []) if analysis_cache else []
                    total_recommendations = len(recommendations)
                    
                    # Calculate cost savings
                    import re
                    total_savings = 0
                    savings_by_type = {"cost_leak": 0, "value_leak": 0, "optimization_opportunity": 0}
                    
                    for rec in recommendations:
                        savings_str = rec.get("estimated_savings", "")
                        if savings_str:
                            numbers = re.findall(r'\d+\.?\d*', savings_str)
                            if numbers:
                                savings_value = float(numbers[0])
                                if '%' in savings_str.lower():
                                    savings_value = savings_value * 100
                                total_savings += savings_value
                                rec_type = rec.get("type", "optimization_opportunity")
                                if rec_type in savings_by_type:
                                    savings_by_type[rec_type] += savings_value
                    
                    # Count by type and severity
                    by_type = {
                        "cost_leak": len([r for r in recommendations if r.get("type") == "cost_leak"]),
                        "value_leak": len([r for r in recommendations if r.get("type") == "value_leak"]),
                        "optimization_opportunity": len([r for r in recommendations if r.get("type") == "optimization_opportunity"])
                    }
                    
                    by_severity = {
                        "high": len([r for r in recommendations if r.get("severity") == "high"]),
                        "medium": len([r for r in recommendations if r.get("severity") == "medium"]),
                        "low": len([r for r in recommendations if r.get("severity") == "low"])
                    }
                    
                    # Count unique jobs
                    job_ids = set()
                    resources_by_type = {}
                    for rec in recommendations:
                        if rec.get("resource_type") == "job":
                            resource_id = rec.get("resource_id")
                            if resource_id:
                                job_ids.add(str(resource_id))
                        res_type = rec.get("resource_type", "unknown")
                        if res_type not in resources_by_type:
                            resources_by_type[res_type] = set()
                        resource_id = rec.get("resource_id")
                        if resource_id:
                            resources_by_type[res_type].add(str(resource_id))
                    
                    resources_count = {k: len(v) for k, v in resources_by_type.items()}
                    
                    analysis_timestamp = cache_timestamp.isoformat() if cache_timestamp else None
                    jobs_analyzed = analysis_cache.get("jobs_count", 0) if analysis_cache else 0
                    clusters_analyzed = analysis_cache.get("clusters_count", 0) if analysis_cache else 0
                    
                    self._send_json_response({
                        "total_cost_savings": round(total_savings, 2),
                        "total_cost_savings_formatted": f"${total_savings:,.2f}",
                        "total_recommendations": total_recommendations,
                        "jobs_identified": len(job_ids),
                        "resources_optimized": sum(resources_count.values()),
                        "by_type": by_type,
                        "by_severity": by_severity,
                        "savings_by_type": {k: round(v, 2) for k, v in savings_by_type.items()},
                        "resources_by_type": resources_count,
                        "analysis_metadata": {
                            "timestamp": analysis_timestamp,
                            "jobs_analyzed": jobs_analyzed,
                            "clusters_analyzed": clusters_analyzed,
                            "has_analysis": len(recommendations) > 0
                        },
                        "success_metrics": {
                            "recommendations_generated": total_recommendations,
                            "high_priority_actions": by_severity["high"],
                            "potential_monthly_savings": round(total_savings, 2),
                            "optimization_coverage": f"{len(job_ids)} jobs, {sum(resources_count.values())} resources"
                        }
                    })
                except Exception as e:
                    logger.error(f"Error generating summary: {str(e)}")
                    self._send_json_response({
                        "error": str(e),
                        "total_cost_savings": 0,
                        "total_recommendations": 0,
                        "jobs_identified": 0,
                        "has_analysis": False
                    }, 500)
            
            else:
                self._send_json_response({"error": "Not found"}, 404)
        
        except Exception as e:
            logger.error(f"Error handling request: {str(e)}", exc_info=True)
            self._send_json_response({"error": str(e)}, 500)
    
    def do_POST(self):
        """Handle POST requests."""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        try:
            if path == '/api/analyze':
                if not databricks_client:
                    self._send_json_response({"error": "Databricks client not configured"}, 503)
                    return
                
                # Fetch jobs and clusters (core resources for basic analysis)
                logger.info("Fetching jobs and clusters for analysis...")
                try:
                    jobs = databricks_client.get_all_jobs()
                    clusters = databricks_client.get_all_clusters()
                    logger.info(f"Fetched: {len(jobs)} jobs, {len(clusters)} clusters")
                except Exception as fetch_error:
                    logger.error(f"Error fetching jobs/clusters: {str(fetch_error)}")
                    self._send_json_response({"error": f"Failed to fetch data: {str(fetch_error)}"}, 500)
                    return
                
                # Always start with rule-based analysis for clusters and jobs
                recommendations = []
                analysis_type = "rule-based"
                analysis_summary = (
                    f"Analyzed {len(jobs)} jobs and {len(clusters)} clusters. "
                    "Rule-based analysis is enabled."
                )
                
                # Perform basic rule-based analysis on clusters and jobs
                logger.info("Performing rule-based analysis on clusters and jobs...")
                try:
                    basic_recommendations = perform_basic_analysis(jobs, clusters)
                    recommendations.extend(basic_recommendations)
                    logger.info(f"Rule-based analysis generated {len(basic_recommendations)} recommendations")
                except Exception as basic_error:
                    logger.error(f"Error in rule-based analysis: {str(basic_error)}")
                    # Continue even if basic analysis fails
                
                # Try AI analysis if available (enhances the recommendations)
                if ai_agent:
                    try:
                        logger.info("Attempting AI-enhanced analysis...")
                        # Fetch additional resources for comprehensive analysis
                        sql_warehouses = databricks_client.get_sql_warehouses()
                        pools = databricks_client.get_instance_pools()
                        vector_search = databricks_client.get_vector_search_endpoints()
                        policies = databricks_client.get_cluster_policies()
                        apps = databricks_client.get_apps()
                        lakebase = databricks_client.get_lakebase_provisioned()
                        ml_jobs = databricks_client.get_ml_jobs()
                        mlflow_experiments = databricks_client.get_mlflow_experiments()
                        mlflow_models = databricks_client.get_mlflow_models()
                        model_serving = databricks_client.get_model_serving_endpoints()
                        feature_store = databricks_client.get_feature_store_tables()
                        
                        job_runs = {}
                        for job in jobs[:10]:
                            job_id = job.get("job_id")
                            if job_id:
                                try:
                                    runs = databricks_client.get_job_runs(job_id=job_id, limit=10)
                                    job_runs[job_id] = runs
                                except Exception as run_error:
                                    logger.warning(f"Could not fetch runs for job {job_id}: {str(run_error)}")
                        
                        # Try AI analysis - if it works, use it; otherwise keep rule-based
                        try:
                            ai_recommendations = ai_agent.analyze_all_compute(
                                jobs=jobs,
                                clusters=clusters,
                                sql_warehouses=sql_warehouses,
                                pools=pools,
                                vector_search=vector_search,
                                policies=policies,
                                apps=apps,
                                lakebase=lakebase,
                                ml_jobs=ml_jobs,
                                mlflow_experiments=mlflow_experiments,
                                mlflow_models=mlflow_models,
                                model_serving=model_serving,
                                feature_store=feature_store,
                                job_runs=job_runs
                            )
                            # If AI analysis succeeds, use it (it's more comprehensive)
                            if ai_recommendations and len(ai_recommendations) > 0:
                                recommendations = ai_recommendations
                                analysis_type = "ai"
                                logger.info(f"AI analysis completed: {len(recommendations)} recommendations")
                                analysis_summary = ai_agent.generate_summary(jobs=jobs, clusters=clusters)
                            else:
                                logger.info("AI analysis returned no recommendations, using rule-based results")
                        except Exception as ai_error:
                            logger.warning(f"AI analysis failed, falling back to rule-based: {str(ai_error)}")
                            # Fall through to rule-based analysis
                            recommendations = []
                    except Exception as outer_error:
                        logger.error(f"Error in AI analysis setup: {str(outer_error)}")
                else:
                    logger.info("AI agent not available, using rule-based analysis")
                
                # Ensure we have recommendations from rule-based analysis
                if not recommendations:
                    recommendations = perform_basic_analysis(jobs, clusters)
                    logger.info(f"Rule-based analysis completed: {len(recommendations)} recommendations")
                
                # Try to add analysis for other compute types if we can fetch them
                try:
                    sql_warehouses = databricks_client.get_sql_warehouses() if 'sql_warehouses' not in locals() else sql_warehouses
                    pools = databricks_client.get_instance_pools() if 'pools' not in locals() else pools
                    
                    for warehouse in sql_warehouses:
                        if warehouse.get("state") == "RUNNING":
                            recommendations.append({
                                "id": f"rec_warehouse_{len(recommendations)}",
                                "type": "cost_leak",
                                "severity": "medium",
                                "title": f"Running SQL Warehouse: {warehouse.get('name', 'Unknown')}",
                                "description": "SQL warehouse is running. Monitor usage and consider auto-stop if idle.",
                                "resource_type": "sql_warehouse",
                                "resource_id": warehouse.get("id"),
                                "estimated_savings": "Medium",
                                "risk": "Low",
                            })
                    for pool in pools:
                        if pool.get("status", {}).get("instance_use_count", 0) == 0:
                            recommendations.append({
                                "id": f"rec_pool_{len(recommendations)}",
                                "type": "cost_leak",
                                "severity": "low",
                                "title": f"Unused Instance Pool: {pool.get('instance_pool_name', 'Unknown')}",
                                "description": "Instance pool has no active instances. Consider reviewing pool configuration.",
                                "resource_type": "pool",
                                "resource_id": pool.get("instance_pool_id"),
                                "estimated_savings": "Low",
                                "risk": "Low",
                            })
                    logger.info(f"Rule-based analysis with additional resources completed: {len(recommendations)} recommendations")
                
                except Exception as analysis_error:
                    logger.error(f"Error during analysis: {str(analysis_error)}", exc_info=True)
                    # Return at least a basic analysis result
                    recommendations = perform_basic_analysis(jobs, clusters) if jobs or clusters else []
                    if not recommendations:
                        recommendations = [{
                            "id": "rec_error",
                            "type": "info",
                            "severity": "low",
                            "title": "Analysis Complete",
                            "description": f"Analyzed {len(jobs)} jobs and {len(clusters)} clusters. Some analysis features may be limited.",
                            "estimated_savings": "Continue monitoring",
                            "risk": "None",
                        }]
                
                # Initialize variables for cache (set to empty if not fetched)
                sql_warehouses = sql_warehouses if 'sql_warehouses' in locals() else []
                pools = pools if 'pools' in locals() else []
                vector_search = vector_search if 'vector_search' in locals() else []
                policies = policies if 'policies' in locals() else []
                apps = apps if 'apps' in locals() else []
                lakebase = lakebase if 'lakebase' in locals() else []
                ml_jobs = ml_jobs if 'ml_jobs' in locals() else []
                mlflow_experiments = mlflow_experiments if 'mlflow_experiments' in locals() else []
                mlflow_models = mlflow_models if 'mlflow_models' in locals() else []
                model_serving = model_serving if 'model_serving' in locals() else []
                feature_store = feature_store if 'feature_store' in locals() else []
                
                global analysis_cache, cache_timestamp
                analysis_cache = {
                    "recommendations": recommendations,
                    "jobs_count": len(jobs),
                    "clusters_count": len(clusters),
                    "sql_warehouses_count": len(sql_warehouses),
                    "pools_count": len(pools),
                    "vector_search_count": len(vector_search),
                    "policies_count": len(policies),
                    "apps_count": len(apps),
                    "lakebase_count": len(lakebase),
                    "ml_jobs_count": len(ml_jobs),
                    "mlflow_experiments_count": len(mlflow_experiments),
                    "mlflow_models_count": len(mlflow_models),
                    "model_serving_count": len(model_serving),
                    "feature_store_count": len(feature_store),
                    "timestamp": datetime.utcnow().isoformat(),
                    "analysis_type": analysis_type,
                    "analysis_summary": analysis_summary
                }
                cache_timestamp = datetime.utcnow()
                
                self._send_json_response({
                    "recommendations": recommendations,
                    "summary": {
                        "total_jobs": len(jobs),
                        "total_clusters": len(clusters),
                        "sql_warehouses": len(sql_warehouses),
                        "pools": len(pools),
                        "vector_search_endpoints": len(vector_search),
                        "policies": len(policies),
                        "apps": len(apps),
                        "lakebase_resources": len(lakebase),
                        "ml_jobs": len(ml_jobs),
                        "mlflow_experiments": len(mlflow_experiments),
                        "mlflow_models": len(mlflow_models),
                        "model_serving_endpoints": len(model_serving),
                        "feature_store_tables": len(feature_store),
                        "recommendations_count": len(recommendations),
                        "timestamp": cache_timestamp.isoformat(),
                        "analysis_type": analysis_type,
                        "analysis_summary": analysis_summary,
                        "ai_available": ai_agent is not None
                    }
                })
            
            else:
                self._send_json_response({"error": "Not found"}, 404)
        
        except Exception as e:
            logger.error(f"Error handling POST: {str(e)}", exc_info=True)
            self._send_json_response({"error": str(e)}, 500)
    
    def log_message(self, format, *args):
        """Override to use our logger."""
        logger.info(f"{self.address_string()} - {format % args}")


def run_server():
    """Run the HTTP server."""
    port = settings.backend_port
    server_address = ('0.0.0.0', port)
    httpd = HTTPServer(server_address, APIHandler)
    logger.info(f"ClusterIQ Server starting on http://0.0.0.0:{port}")
    logger.info(f"Using direct HTTP requests to Databricks API")
    httpd.serve_forever()


if __name__ == "__main__":
    run_server()

