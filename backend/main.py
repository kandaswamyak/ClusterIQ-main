"""Flask backend for ClusterIQ using direct HTTP requests."""
from flask import Flask, jsonify, request
from flask_cors import CORS
from typing import List, Dict, Any, Optional
import re
import logging
import time
from datetime import datetime, timedelta, timezone

from config import settings
from databricks_client import DatabricksClient
from ai_agent import ClusterIQAgent
from cost_calculator import cost_calculator
from approval_store import add_recommendations, list_recommendations, update_status, get_recommendation
from logs_manager import log_manager, setup_logging

# Configure timezone for IST (India Standard Time)
IST = timezone(timedelta(hours=5, minutes=30))

def get_ist_time():
    """Get current time in IST timezone."""
    return datetime.now(IST)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app, origins=settings.cors_origins)

# Initialize clients
databricks_client = None
ai_agent = None

# Cache for analysis results
analysis_cache = {}
cache_timestamp = None

# Runtime configuration for Delta table names
delta_table_config = {
    "cluster_events_table": settings.delta_cluster_events_table,
    "cluster_logs_table": settings.delta_cluster_logs_table,
    "job_run_logs_table": settings.delta_job_run_logs_table,
}


# Initialize clients on startup
try:
    if settings.databricks_host and settings.databricks_token:
        databricks_client = DatabricksClient(
            host=settings.databricks_host,
            token=settings.databricks_token
        )
        logger.info("Databricks client initialized")
    
    if settings.azure_openai_endpoint and settings.azure_openai_api_key and settings.azure_openai_deployment_name:
        logger.info("AI agent initialization deferred until first use")
    elif settings.openai_api_key:
        logger.info("AI agent initialization deferred until first use")
except Exception as e:
    logger.error(f"Error during startup: {str(e)}")


def _parse_event_time(value: Any) -> Optional[datetime]:
    """Parse event timestamp to datetime object."""
    if value is None:
        return None
    try:
        timestamp = float(value)
    except (TypeError, ValueError):
        return None
    if timestamp > 1e12:
        timestamp /= 1000
    return datetime.fromtimestamp(timestamp, tz=IST)


def ensure_ai_agent():
    """Lazily initialize AI agent when needed."""
    global ai_agent
    if ai_agent:
        return ai_agent
    if settings.azure_openai_endpoint and settings.azure_openai_api_key and settings.azure_openai_deployment_name:
        try:
            ai_agent = ClusterIQAgent(
                azure_endpoint=settings.azure_openai_endpoint,
                azure_api_key=settings.azure_openai_api_key,
                azure_deployment_name=settings.azure_openai_deployment_name,
                model=settings.openai_model
            )
            logger.info("AI agent initialized with Azure OpenAI")
            return ai_agent
        except Exception as exc:
            logger.error(f"AI agent initialization failed: {exc}")
            ai_agent = None
    elif settings.openai_api_key:
        try:
            ai_agent = ClusterIQAgent(
                api_key=settings.openai_api_key,
                model=settings.openai_model
            )
            logger.info("AI agent initialized")
            return ai_agent
        except Exception as exc:
            logger.error(f"AI agent initialization failed: {exc}")
            ai_agent = None
    return None


@app.route("/")
def root():
    """Root endpoint."""
    return jsonify({
        "service": "ClusterIQ API",
        "version": "1.0.0",
        "status": "running"
    })


@app.route("/health")
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "databricks_configured": databricks_client is not None,
        "ai_configured": ai_agent is not None,
        "timestamp": get_ist_time().isoformat()
    })


@app.route("/api/jobs", methods=["GET"])
def get_jobs():
    """Fetch all Databricks jobs."""
    if not databricks_client:
        return jsonify({"error": "Databricks client not configured"}), 503
    
    try:
        jobs = databricks_client.get_all_jobs()
        return jsonify(jobs)
    except Exception as e:
        logger.error(f"Error fetching jobs: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jobs/<int:job_id>/runs", methods=["GET"])
def get_job_runs(job_id):
    """Fetch runs for a specific job."""
    if not databricks_client:
        return jsonify({"error": "Databricks client not configured"}), 503
    
    try:
        limit = request.args.get("limit", 50, type=int)
        runs = databricks_client.get_job_runs(job_id=job_id, limit=limit)
        return jsonify(runs)
    except Exception as e:
        logger.error(f"Error fetching job runs: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/clusters", methods=["GET"])
def get_clusters():
    """Fetch all active Databricks clusters (excludes terminated clusters)."""
    if not databricks_client:
        return jsonify({"error": "Databricks client not configured"}), 503
    
    try:
        logger.info("API: Fetching clusters...")
        all_clusters = databricks_client.get_all_clusters()
        # Return all clusters (frontend will handle display differently for terminated ones)
        logger.info(f"API: Returning {len(all_clusters)} clusters")
        return jsonify(all_clusters)
    except Exception as e:
        logger.error(f"Error fetching clusters: {str(e)}", exc_info=True)
        return jsonify([{"error": str(e), "message": "Failed to fetch clusters"}]), 500


@app.route("/api/clusters/<cluster_id>/metrics", methods=["GET"])
def get_cluster_metrics(cluster_id):
    """Fetch metrics for a specific cluster."""
    if not databricks_client:
        return jsonify({"error": "Databricks client not configured"}), 503
    
    try:
        metrics = databricks_client.get_cluster_metrics(cluster_id)
        return jsonify(metrics)
    except Exception as e:
        logger.error(f"Error fetching cluster metrics: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/clusters/<string:cluster_id>/start", methods=["POST", "OPTIONS"])
def start_cluster(cluster_id):
    """Start a terminated cluster."""
    logger.info(f"=== START CLUSTER ENDPOINT HIT === cluster_id={cluster_id}, method={request.method}")
    
    if request.method == "OPTIONS":
        return "", 200
    
    if not databricks_client:
        return jsonify({"success": False, "error": "Databricks client not configured"}), 503
    
    try:
        logger.info(f"Starting cluster {cluster_id}")
        result = databricks_client.start_cluster(cluster_id)
        
        if result.get("status") == "success":
            logger.info(f"Successfully started cluster {cluster_id}")
            return jsonify({
                "success": True,
                "message": f"Cluster {cluster_id} started successfully",
                "result": result
            }), 200
        else:
            error_msg = result.get("error", "Failed to start cluster")
            logger.error(f"Error starting cluster {cluster_id}: {error_msg}")
            return jsonify({
                "success": False,
                "error": error_msg,
                "result": result
            }), 400
    
    except Exception as e:
        logger.error(f"Exception starting cluster {cluster_id}: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/clusters/<string:cluster_id>/terminate", methods=["POST", "OPTIONS"])
def terminate_cluster(cluster_id):
    """Terminate a running cluster."""
    logger.info(f"=== TERMINATE CLUSTER ENDPOINT HIT === cluster_id={cluster_id}, method={request.method}")
    
    if request.method == "OPTIONS":
        return "", 200
    
    if not databricks_client:
        return jsonify({"success": False, "error": "Databricks client not configured"}), 503
    
    try:
        logger.info(f"Terminating cluster {cluster_id}")
        result = databricks_client.terminate_cluster(cluster_id)
        
        if result.get("status") == "success":
            logger.info(f"Successfully terminated cluster {cluster_id}")
            return jsonify({
                "success": True,
                "message": f"Cluster {cluster_id} terminated successfully",
                "result": result
            }), 200
        else:
            error_msg = result.get("error", "Failed to terminate cluster")
            logger.error(f"Error terminating cluster {cluster_id}: {error_msg}")
            return jsonify({
                "success": False,
                "error": error_msg,
                "result": result
            }), 400
    
    except Exception as e:
        logger.error(f"Exception terminating cluster {cluster_id}: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


def generate_execution_error_recommendations(jobs):
    """Generate recommendations for jobs with execution errors.
    
    Args:
        jobs: List of job dictionaries
        
    Returns:
        List of recommendation dictionaries
    """
    recommendations = []
    
    try:
        for job in jobs:
            job_id = job.get("job_id")
            job_name = job.get("settings", {}).get("name") or job.get("job_name", "Unknown")
            
            # Check for recent failed runs
            try:
                if databricks_client:
                    # Get recent runs for this job
                    runs_response = databricks_client.get_job_runs(job_id, limit=5)
                    if isinstance(runs_response, dict):
                        if runs_response.get("status") != "success":
                            continue
                        runs = runs_response.get("runs", [])
                    else:
                        runs = runs_response or []
                    
                    if not runs:
                        continue
                    
                    # Look for execution errors
                    for run in runs:
                            state = run.get("state", {})
                            life_cycle_state = state.get("life_cycle_state", "")
                            result_state = state.get("result_state", "")
                            state_message = state.get("state_message", "")
                            
                            # Check for execution errors - only failed or timed out runs
                            if result_state in ["FAILED", "TIMEDOUT"]:
                                run_id = run.get("run_id")
                                cluster_instance = run.get("cluster_instance", {})
                                cluster_id = cluster_instance.get("cluster_id", "unknown")
                                
                                # Create recommendation to fix execution error
                                rec_id = f"rec_exec_error_{job_id}_{run_id}"
                                
                                # Restart the failed job by submitting a new run
                                action_type = "restart_job_run"
                                action_description = "Rerun the failed job to recover from execution error"
                                
                                recommendations.append({
                                    "id": rec_id,
                                    "type": "execution_error",
                                    "severity": "high",
                                    "title": f"Restart failed job: {job_name}",
                                    "description": f"Job '{job_name}' failed with execution error: {state_message[:200]}. Cluster: {cluster_id}. Rerunning job for recovery.",
                                    "resource_type": "job",
                                    "resource_id": job_id,
                                    "resource_name": job_name,
                                    "estimated_savings": "Prevents job failures",
                                    "risk": "Low - Job rerun",
                                    "confidence_score": 0.85,
                                    "action": {
                                        "type": action_type,
                                        "target_id": job_id,
                                        "params": {
                                            "job_id": job_id,
                                            "run_id": run_id,
                                            "error_message": state_message
                                        }
                                    },
                                    "details": {
                                        "run_id": run_id,
                                        "cluster_id": cluster_id,
                                        "error_type": "RunExecutionError",
                                        "state_message": state_message,
                                        "action_description": action_description
                                    },
                                    "created_at": get_ist_time().isoformat(),
                                    "timestamp": get_ist_time().isoformat()
                                })
                                
                                logger.info(f"Created execution error recommendation for job {job_name} (run {run_id})")
                                break  # Only one recommendation per job
                                
            except Exception as job_error:
                logger.debug(f"Could not check runs for job {job_id}: {job_error}")
                continue
                
    except Exception as e:
        logger.error(f"Error generating execution error recommendations: {str(e)}")
    
    return recommendations


def generate_stuck_pending_job_recommendations(jobs):
    """Generate recommendations for jobs stuck in PENDING state for too long.
    
    Args:
        jobs: List of job dictionaries
        
    Returns:
        List of recommendation dictionaries
    """
    recommendations = []
    PENDING_THRESHOLD_MINUTES = 5  # Alert if pending for more than 5 minutes
    
    try:
        current_time_ms = int(time.time() * 1000)
        
        for job in jobs:
            job_id = job.get("job_id")
            job_name = job.get("settings", {}).get("name") or job.get("job_name", "Unknown")
            
            # Check for runs stuck in PENDING state
            try:
                if databricks_client:
                    # Get active/recent runs for this job
                    runs_response = databricks_client.get_job_runs(job_id, limit=10)
                    if isinstance(runs_response, dict):
                        if runs_response.get("status") != "success":
                            continue
                        runs = runs_response.get("runs", [])
                    else:
                        runs = runs_response or []
                    
                    if not runs:
                        continue
                    
                    # Look for PENDING runs that exceed threshold
                    for run in runs:
                        state = run.get("state", {})
                        life_cycle_state = state.get("life_cycle_state", "")
                        
                        # Check if job is stuck in PENDING state
                        if life_cycle_state == "PENDING":
                            run_id = run.get("run_id")
                            start_time = run.get("start_time")
                            
                            if not start_time:
                                continue
                            
                            # Calculate how long it's been pending
                            pending_duration_ms = current_time_ms - start_time
                            pending_duration_minutes = pending_duration_ms / 1000 / 60
                            
                            # If pending for more than threshold, create recommendation
                            if pending_duration_minutes > PENDING_THRESHOLD_MINUTES:
                                cluster_instance = run.get("cluster_instance", {})
                                cluster_id = cluster_instance.get("cluster_id", "unknown")
                                
                                rec_id = f"rec_stuck_pending_{job_id}_{run_id}"
                                
                                recommendations.append({
                                    "id": rec_id,
                                    "type": "stuck_pending_job",
                                    "severity": "high",
                                    "title": f"Job stuck in PENDING: {job_name}",
                                    "description": f"Job '{job_name}' (Run {run_id}) has been stuck in PENDING state for {pending_duration_minutes:.1f} minutes. Normal runs complete in <1 second. This may indicate cluster startup issues or resource constraints.",
                                    "resource_type": "job",
                                    "resource_id": job_id,
                                    "resource_name": job_name,
                                    "estimated_savings": "Prevents resource waste",
                                    "risk": "Low - Cancel stuck run",
                                    "confidence_score": 0.90,
                                    "action": {
                                        "type": "cancel_job_run",
                                        "target_id": run_id,
                                        "params": {
                                            "job_id": job_id,
                                            "run_id": run_id,
                                            "reason": f"Stuck in PENDING state for {pending_duration_minutes:.1f} minutes"
                                        }
                                    },
                                    "details": {
                                        "run_id": run_id,
                                        "job_id": job_id,
                                        "cluster_id": cluster_id,
                                        "pending_duration_minutes": pending_duration_minutes,
                                        "start_time": start_time,
                                        "threshold_minutes": PENDING_THRESHOLD_MINUTES,
                                        "state": life_cycle_state
                                    },
                                    "created_at": get_ist_time().isoformat(),
                                    "timestamp": get_ist_time().isoformat()
                                })
                                
                                logger.info(f"Created stuck PENDING recommendation for job {job_name} (run {run_id}) - pending for {pending_duration_minutes:.1f} minutes")
                                break  # Only one recommendation per job
                                
            except Exception as job_error:
                logger.debug(f"Could not check PENDING runs for job {job_id}: {job_error}")
                continue
                
    except Exception as e:
        logger.error(f"Error generating stuck PENDING job recommendations: {str(e)}")
    
    return recommendations


def generate_frequent_retry_recommendations(jobs):
    """Generate recommendations for jobs with frequent retries.
    
    Args:
        jobs: List of job dictionaries
        
    Returns:
        List of recommendation dictionaries
    """
    recommendations = []
    
    try:
        for job in jobs:
            job_id = job.get("job_id")
            job_name = job.get("settings", {}).get("name") or job.get("job_name", "Unknown")
            
            # Check for frequent retries in recent runs
            try:
                if databricks_client:
                    # Get recent runs for this job
                    runs_response = databricks_client.get_job_runs(job_id, limit=10)
                    if runs_response.get("status") == "success":
                        runs = runs_response.get("runs", [])
                        
                        # Count retries across recent runs
                        total_retries = 0
                        runs_with_retries = 0
                        retry_details = []
                        
                        for run in runs[:5]:  # Check last 5 runs
                            run_id = run.get("run_id")
                            tasks = run.get("tasks", [])
                            
                            # Check task attempts
                            run_retry_count = 0
                            for task in tasks:
                                attempt_number = task.get("attempt_number", 0)
                                if attempt_number > 0:
                                    run_retry_count += attempt_number
                            
                            # Also check run-level retries
                            number_in_job = run.get("number_in_job", 0)
                            if number_in_job > 1 and run_retry_count == 0:
                                # This might be a job-level retry
                                pass
                            
                            if run_retry_count > 0:
                                total_retries += run_retry_count
                                runs_with_retries += 1
                                retry_details.append({
                                    "run_id": run_id,
                                    "retry_count": run_retry_count
                                })
                        
                        # If more than 2 out of 5 runs had retries, or total retries > 5
                        if runs_with_retries >= 2 or total_retries >= 5:
                            rec_id = f"rec_frequent_retry_{job_id}"
                            
                            # Calculate cost impact
                            estimated_savings = total_retries * 50  # Rough estimate: $50 per retry
                            
                            recommendations.append({
                                "id": rec_id,
                                "type": "frequent_retries",
                                "severity": "medium",
                                "title": f"Optimize job: {job_name}",
                                "description": f"Job '{job_name}' shows frequent retries ({total_retries} retries in {runs_with_retries} out of 5 recent runs). This indicates configuration issues or resource constraints.",
                                "resource_type": "job",
                                "resource_id": job_id,
                                "resource_name": job_name,
                                "estimated_savings": estimated_savings,
                                "risk": "Low - Analysis only",
                                "confidence_score": 0.75,
                                "action": {
                                    "type": "analyze_job",
                                    "target_id": job_id,
                                    "params": {
                                        "total_retries": total_retries,
                                        "runs_with_retries": runs_with_retries
                                    }
                                },
                                "details": {
                                    "total_retries": total_retries,
                                    "runs_with_retries": runs_with_retries,
                                    "retry_details": retry_details,
                                    "recommendation": "Review job configuration, increase cluster size, or optimize code to reduce retry frequency"
                                },
                                "created_at": get_ist_time().isoformat(),
                                "timestamp": get_ist_time().isoformat()
                            })
                            
                            logger.info(f"Created frequent retry recommendation for job {job_name} ({total_retries} retries)")
                                
            except Exception as job_error:
                logger.debug(f"Could not check retries for job {job_id}: {job_error}")
                continue
                
    except Exception as e:
        logger.error(f"Error generating frequent retry recommendations: {str(e)}")
    
    return recommendations


def generate_long_running_job_recommendations(jobs):
    """Generate recommendations for jobs running longer than threshold.
    
    Args:
        jobs: List of job dictionaries
        
    Returns:
        List of recommendation dictionaries
    """
    recommendations = []
    LONG_RUNNING_THRESHOLD_MINUTES = 30  # Alert if job runs longer than 30 minutes
    
    try:
        current_time_ms = int(time.time() * 1000)
        
        for job in jobs:
            job_id = job.get("job_id")
            job_name = job.get("settings", {}).get("name") or job.get("job_name", "Unknown")
            
            # Check for long running jobs
            try:
                if databricks_client:
                    # Get active/recent runs for this job
                    runs_response = databricks_client.get_job_runs(job_id, limit=10)
                    if isinstance(runs_response, dict):
                        if runs_response.get("status") != "success":
                            continue
                        runs = runs_response.get("runs", [])
                    else:
                        runs = runs_response or []
                    
                    if not runs:
                        continue
                    
                    # Look for RUNNING jobs that exceed threshold
                    for run in runs:
                        state = run.get("state", {})
                        life_cycle_state = state.get("life_cycle_state", "")
                        
                        # Check if job is currently RUNNING
                        if life_cycle_state == "RUNNING":
                            run_id = run.get("run_id")
                            start_time = run.get("start_time")
                            
                            if not start_time:
                                continue
                            
                            # Calculate how long it's been running
                            running_duration_ms = current_time_ms - start_time
                            running_duration_minutes = running_duration_ms / 1000 / 60
                            
                            # If running for more than threshold, create recommendation
                            if running_duration_minutes > LONG_RUNNING_THRESHOLD_MINUTES:
                                cluster_instance = run.get("cluster_instance", {})
                                cluster_id = cluster_instance.get("cluster_id", "unknown")
                                
                                rec_id = f"rec_long_running_{job_id}_{run_id}"
                                
                                recommendations.append({
                                    "id": rec_id,
                                    "type": "long_running_job",
                                    "severity": "medium",
                                    "title": f"Long running job: {job_name}",
                                    "description": f"Job '{job_name}' (Run {run_id}) has been running for {running_duration_minutes:.1f} minutes, exceeding the {LONG_RUNNING_THRESHOLD_MINUTES}-minute threshold. This may indicate performance issues or inefficient code.",
                                    "resource_type": "job",
                                    "resource_id": job_id,
                                    "resource_name": job_name,
                                    "estimated_savings": "Prevents excessive compute costs",
                                    "risk": "Medium - Cancel if stuck",
                                    "confidence_score": 0.75,
                                    "action": {
                                        "type": "cancel_job_run",
                                        "target_id": run_id,
                                        "params": {
                                            "job_id": job_id,
                                            "run_id": run_id,
                                            "reason": f"Running longer than {LONG_RUNNING_THRESHOLD_MINUTES} minutes"
                                        }
                                    },
                                    "details": {
                                        "run_id": run_id,
                                        "job_id": job_id,
                                        "cluster_id": cluster_id,
                                        "running_duration_minutes": running_duration_minutes,
                                        "start_time": start_time,
                                        "threshold_minutes": LONG_RUNNING_THRESHOLD_MINUTES,
                                        "state": life_cycle_state
                                    },
                                    "created_at": get_ist_time().isoformat(),
                                    "timestamp": get_ist_time().isoformat()
                                })
                                
                                logger.info(f"Created long running recommendation for job {job_name} (run {run_id}) - running for {running_duration_minutes:.1f} minutes")
                                break  # Only one recommendation per job
                                
            except Exception as job_error:
                logger.debug(f"Could not check running time for job {job_id}: {job_error}")
                continue
                
    except Exception as e:
        logger.error(f"Error generating long running job recommendations: {str(e)}")
    
    return recommendations


def generate_autotermination_recommendations(clusters):
    """Generate recommendations for clusters without auto-termination enabled.
    
    Args:
        clusters: List of cluster dictionaries
        
    Returns:
        List of recommendation dictionaries
    """
    recommendations = []
    
    for cluster in clusters:
        cluster_id = cluster.get("cluster_id")
        cluster_name = cluster.get("cluster_name", "Unknown")
        
        # Skip job clusters (they auto-terminate by design)
        if "job-" in cluster_name.lower():
            continue
        
        try:
            # Get detailed cluster info to check auto-termination
            cluster_info = databricks_client.get_cluster_info(cluster_id)
            if cluster_info.get("status") == "success":
                cluster_details = cluster_info.get("cluster", {})
                autotermination_minutes = cluster_details.get("autotermination_minutes", 0)
                
                # If auto-termination is not set or is 0, create a recommendation
                if autotermination_minutes == 0:
                    rec_id = f"rec_auto_{cluster_id[:8]}"

                    num_workers = cluster.get("num_workers", 1)
                    monthly_cost = (num_workers + 1) * 0.40 * 100
                    potential_savings = monthly_cost * 0.3
                    
                    recommendations.append({
                        "id": rec_id,
                        "title": f"Enable auto-termination for {cluster_name}",
                        "description": f"Cluster '{cluster_name}' does not have auto-termination enabled. Enabling 15-minute auto-termination will reduce idle compute costs.",
                        "type": "cost_optimization",
                        "severity": "high" if cluster.get("state") == "RUNNING" else "medium",
                        "confidence_score": 0.72,
                        "resource_type": "cluster",
                        "resource_id": cluster_id,
                        "resource_name": cluster_name,
                        "estimated_savings": f"${potential_savings:.2f}/month",
                        "estimated_savings_monthly": potential_savings,
                        "estimated_savings_annual": potential_savings * 12,
                        "risk": "low",
                        "action": {
                            "type": "enable_autotermination",
                            "target_id": cluster_id,
                            "params": {
                                "autotermination_minutes": 5
                            }
                        },
                        "status": "PENDING",
                        "created_at": get_ist_time().isoformat(),
                        "updated_at": get_ist_time().isoformat(),
                        "status_note": "Auto-detected: No auto-termination configured"
                    })
                    
                    logger.info(f"Generated auto-termination recommendation for cluster: {cluster_name}")
        
        except Exception as e:
            logger.warning(f"Error checking auto-termination for cluster {cluster_name}: {e}")
            continue
    
    return recommendations


@app.route("/api/analyze", methods=["POST"])
def analyze_jobs_and_clusters():
    """Analyze jobs and clusters to identify cost leaks."""
    if not databricks_client:
        return jsonify({"error": "Databricks client not configured"}), 503
    
    try:
        # Fetch data with timeout protection
        import threading
        
        fetch_results = {"jobs": [], "clusters": [], "error": None}
        
        def fetch_data():
            try:
                logger.info("Fetching jobs and clusters...")
                fetch_results["jobs"] = databricks_client.get_all_jobs()
                fetch_results["clusters"] = databricks_client.get_all_clusters()
                logger.info(f"Fetched: {len(fetch_results['jobs'])} jobs, {len(fetch_results['clusters'])} clusters")
            except Exception as e:
                logger.error(f"Error fetching data: {str(e)}")
                fetch_results["error"] = str(e)
        
        # Run fetch in a thread with timeout
        fetch_thread = threading.Thread(target=fetch_data, daemon=True)
        fetch_thread.start()
        fetch_thread.join(timeout=20)  # 20-second timeout for fetching data
        
        if fetch_results["error"]:
            raise Exception(f"Failed to fetch Databricks data: {fetch_results['error']}")
        
        if not fetch_results["jobs"] and not fetch_results["clusters"]:
            if fetch_thread.is_alive():
                logger.warning("Data fetch timed out after 20 seconds, returning empty analysis")
                return jsonify({
                    "recommendations": [],
                    "summary": {
                        "total_jobs": 0,
                        "total_clusters": 0,
                        "recommendations_count": 0,
                        "analysis_type": "timeout",
                        "analysis_summary": "Analysis timed out. Please check your Databricks connection.",
                        "timestamp": get_ist_time().isoformat()
                    }
                })
        
        jobs = fetch_results["jobs"]
        all_clusters = fetch_results["clusters"]
        
        # Filter out terminated clusters for analysis
        clusters = [c for c in all_clusters if c.get("state", "").upper() not in {"TERMINATED", "TERMINATING"}]
        logger.info(f"Analyzing {len(clusters)} active clusters (filtered from {len(all_clusters)} total)")
        
        recommendations = []
        analysis_type = "rule-based"
        analysis_summary = (
            f"Analyzed {len(jobs)} jobs and {len(clusters)} clusters. "
            "Rule-based analysis is enabled."
        )
        
        # Always start with rule-based analysis (faster)
        logger.info("Performing rule-based analysis on clusters and jobs...")
        try:
            # Import the basic analysis function
            import sys
            import os
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from simple_server import perform_basic_analysis
            
            basic_recommendations = perform_basic_analysis(jobs, clusters)
            recommendations.extend(basic_recommendations)
            logger.info(f"Rule-based analysis generated {len(basic_recommendations)} recommendations")
        except Exception as basic_error:
            logger.error(f"Error in rule-based analysis: {str(basic_error)}")
            # Create basic recommendations manually if import fails
            for cluster in clusters:
                if cluster.get("state") == "RUNNING":
                    # Calculate potential savings
                    num_workers = cluster.get("num_workers", 1)
                    monthly_cost = (num_workers + 1) * 0.40 * 100  # Rough estimate
                    potential_savings = monthly_cost * 0.3  # 30% savings potential
                    
                    recommendations.append({
                        "id": f"rec_{len(recommendations)}",
                        "type": "cost_leak",
                        "severity": "medium",
                        "confidence_score": 0.68,
                        "title": f"Optimize cluster: {cluster.get('cluster_name', 'Unknown')}",
                        "description": f"Cluster is running with {num_workers} workers. Consider downsizing or enabling auto-termination.",
                        "resource_type": "cluster",
                        "resource_id": cluster.get("cluster_id"),
                        "estimated_savings": f"${potential_savings:.2f}/month",
                        "estimated_savings_monthly": potential_savings,
                        "estimated_savings_annual": potential_savings * 12,
                        "action": {
                            "type": "resize_cluster",
                            "target_id": cluster.get("cluster_id"),
                            "params": {
                                "num_workers": max(1, int(num_workers / 2))
                            }
                        },
                        "risk": "Low",
                    })
            for job in jobs:
                if len(job.get("settings", {}).get("tasks", [])) == 0:
                    recommendations.append({
                        "id": f"rec_{len(recommendations)}",
                        "type": "optimization",
                        "severity": "low",
                        "confidence_score": 0.55,
                        "title": f"Review job: {job.get('job_name', 'Unknown')}",
                        "description": "Job has no configured tasks. Consider reviewing job configuration.",
                        "resource_type": "job",
                        "resource_id": job.get("job_id"),
                        "estimated_savings": "$0.00",
                        "estimated_savings_monthly": 0,
                        "estimated_savings_annual": 0,
                        "risk": "Low",
                    })

        # Add auto-termination recommendations to provide actionable savings
        try:
            autotermination_recs = generate_autotermination_recommendations(clusters)
            if autotermination_recs:
                existing_ids = {rec.get("id") for rec in recommendations if rec.get("id")}
                for rec in autotermination_recs:
                    if rec.get("id") not in existing_ids:
                        recommendations.append(rec)
                logger.info(f"Added {len(autotermination_recs)} auto-termination recommendations")
        except Exception as auto_error:
            logger.warning(f"Error generating auto-termination recommendations: {auto_error}")
        
        # Add execution error recommendations to help fix job failures
        try:
            execution_error_recs = generate_execution_error_recommendations(jobs)
            if execution_error_recs:
                existing_ids = {rec.get("id") for rec in recommendations if rec.get("id")}
                for rec in execution_error_recs:
                    if rec.get("id") not in existing_ids:
                        recommendations.append(rec)
                logger.info(f"Added {len(execution_error_recs)} execution error recommendations")
        except Exception as exec_error:
            logger.warning(f"Error generating execution error recommendations: {exec_error}")
        
        # Add frequent retry recommendations
        try:
            retry_recs = generate_frequent_retry_recommendations(jobs)
            if retry_recs:
                existing_ids = {rec.get("id") for rec in recommendations if rec.get("id")}
                for rec in retry_recs:
                    if rec.get("id") not in existing_ids:
                        recommendations.append(rec)
                logger.info(f"Added {len(retry_recs)} frequent retry recommendations")
        except Exception as retry_error:
            logger.warning(f"Error generating frequent retry recommendations: {retry_error}")
        
        # Add stuck PENDING job recommendations
        try:
            stuck_pending_recs = generate_stuck_pending_job_recommendations(jobs)
            if stuck_pending_recs:
                existing_ids = {rec.get("id") for rec in recommendations if rec.get("id")}
                for rec in stuck_pending_recs:
                    if rec.get("id") not in existing_ids:
                        recommendations.append(rec)
                logger.info(f"Added {len(stuck_pending_recs)} stuck PENDING job recommendations")
        except Exception as pending_error:
            logger.warning(f"Error generating stuck PENDING job recommendations: {pending_error}")
        
        # Add long running job recommendations
        try:
            long_running_recs = generate_long_running_job_recommendations(jobs)
            if long_running_recs:
                existing_ids = {rec.get("id") for rec in recommendations if rec.get("id")}
                for rec in long_running_recs:
                    if rec.get("id") not in existing_ids:
                        recommendations.append(rec)
                logger.info(f"Added {len(long_running_recs)} long running job recommendations")
        except Exception as long_running_error:
            logger.warning(f"Error generating long running job recommendations: {long_running_error}")
        
        # Try optional AI analysis (with tight timeout, non-blocking)
        ai_agent_instance = ensure_ai_agent()
        if ai_agent_instance and recommendations:  # Only do AI if we have base recommendations
            try:
                logger.info("Attempting optional AI-enhanced analysis (10-second timeout)...")
                ai_results = {"recommendations": None, "summary": None}
                
                def run_ai_analysis():
                    """Run AI analysis in a separate thread."""
                    try:
                        # Do NOT fetch job runs - too slow
                        # Just enhance existing recommendations with AI insights
                        ai_recs = ai_agent_instance.analyze_jobs_and_clusters(
                            jobs=jobs[:5],  # Limit to first 5 jobs
                            clusters=clusters[:5],  # Limit to first 5 clusters
                            job_runs={}  # Empty job runs to speed up analysis
                        )
                        
                        if ai_recs and len(ai_recs) > 0:
                            ai_results["recommendations"] = ai_recs
                            ai_results["summary"] = ai_agent_instance.generate_summary(jobs=jobs, clusters=clusters)
                    except Exception as e:
                        logger.debug(f"AI analysis detailed error: {str(e)}")
                
                # Run AI analysis in a separate thread with tight timeout
                ai_thread = threading.Thread(target=run_ai_analysis, daemon=True)
                ai_thread.start()
                ai_thread.join(timeout=10)  # 10-second max timeout for AI
                
                if ai_results["recommendations"] and len(ai_results["recommendations"]) > 0:
                    recommendations = ai_results["recommendations"]
                    analysis_type = "ai"
                    analysis_summary = ai_results["summary"]
                    logger.info(f"AI analysis completed: {len(recommendations)} recommendations")
                elif ai_thread.is_alive():
                    logger.info("AI analysis skipped (timeout), using rule-based results")
                else:
                    logger.info("AI analysis returned no recommendations, using rule-based results")
            except Exception as ai_error:
                logger.info(f"AI analysis optional enhancement skipped: {str(ai_error)}")
                # Continue with rule-based recommendations
        else:
            logger.info("AI agent not available or no base recommendations, using only rule-based analysis")
        
        # Ensure we have at least some recommendations
        if not recommendations:
            recommendations = [{
                "id": "rec_no_data",
                "type": "info",
                "severity": "low",
                "confidence_score": 0.5,
                "title": "Analysis Complete",
                "description": f"Analyzed {len(jobs)} jobs and {len(clusters)} clusters. No immediate optimization opportunities detected.",
                "estimated_savings": "Continue monitoring",
                "risk": "None",
            }]

        # Normalize confidence scores and savings where missing
        for rec in recommendations:
            if rec.get("confidence_score") is None and rec.get("confidence") is None:
                rec["confidence_score"] = 0.6

            monthly_value = rec.get("estimated_savings_monthly")
            monthly_alt = rec.get("estimated_monthly_savings_usd")
            monthly_numeric = None
            if isinstance(monthly_value, (int, float)):
                monthly_numeric = float(monthly_value)
            elif isinstance(monthly_alt, (int, float)):
                monthly_numeric = float(monthly_alt)

            if monthly_numeric is None or monthly_numeric <= 0:
                severity = (rec.get("severity") or "low").lower()
                fallback_monthly = 25.0 if severity == "low" else 100.0 if severity == "medium" else 250.0
                rec["estimated_savings_monthly"] = fallback_monthly
                rec["estimated_savings_annual"] = fallback_monthly * 12
                if not rec.get("estimated_savings") or str(rec.get("estimated_savings")).strip() in {"$0.00", "0", "0.0", "0.00"}:
                    rec["estimated_savings"] = f"${fallback_monthly:.2f}/month"

        cluster_ids = {c.get("cluster_id") for c in clusters if c.get("cluster_id")}
        cluster_name_to_id = {
            c.get("cluster_name"): c.get("cluster_id")
            for c in clusters
            if c.get("cluster_name") and c.get("cluster_id")
        }

        for rec in recommendations:
            if rec.get("resource_type") != "cluster":
                continue
            
            # Skip action assignment for informational recommendations
            rec_type = rec.get("type", "")
            if rec_type in ["idle_cluster", "optimization"]:
                continue
            
            action = rec.get("action")
            if isinstance(action, dict) and action.get("type") and action.get("target_id"):
                continue

            target = rec.get("resource_id") or rec.get("resource_name")
            if target in cluster_ids:
                target_id = target
            else:
                target_id = cluster_name_to_id.get(target)

            if not target_id:
                continue

            rec["action"] = {
                "type": "enable_autotermination",
                "target_id": target_id,
                "params": {"autotermination_minutes": 5}
            }
        
        # Update cache
        global analysis_cache, cache_timestamp
        analysis_cache = {
            "recommendations": recommendations,
            "jobs_count": len(jobs),
            "clusters_count": len(clusters),
            "timestamp": get_ist_time().isoformat(),
            "analysis_type": analysis_type,
            "analysis_summary": analysis_summary
        }
        cache_timestamp = get_ist_time()

        # Persist recommendations to approval store for actions
        try:
            add_recommendations(recommendations)
        except Exception as store_error:
            logger.warning(f"Failed to persist recommendations to approval store: {store_error}")
        
        return jsonify({
            "recommendations": recommendations,
            "summary": {
                "total_jobs": len(jobs),
                "total_clusters": len(clusters),
                "recommendations_count": len(recommendations),
                "analysis_type": analysis_type,
                "analysis_summary": analysis_summary,
                "timestamp": cache_timestamp.isoformat()
            }
        })
    
    except Exception as e:
        logger.error(f"Error in analysis: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/recommendations", methods=["GET"])
def get_recommendations():
    """Get cached recommendations."""
    if not analysis_cache or not analysis_cache.get("recommendations"):
        return jsonify({
            "recommendations": [],
            "has_analysis": False,
            "message": "No analysis available. Run /api/analyze first."
        }), 200
    
    return jsonify({
        **analysis_cache,
        "has_analysis": True
    })


@app.route("/api/recommendations/real-time", methods=["GET"])
def get_recommendations_realtime():
    """Get real-time recommendations (returns ALL recommendations from approval store)."""
    # Always return recommendations from approval store for real-time data
    stored_recs = list_recommendations()
    logger.info(f"DEBUG: list_recommendations() returned {len(stored_recs)} items")
    
    # If we have stored recommendations, return them
    if stored_recs:
        logger.info(f"DEBUG: Returning {len(stored_recs)} stored recommendations")
        return jsonify({
            "recommendations": stored_recs,
            "real_time": True,
            "has_analysis": True,
            "timestamp": get_ist_time().isoformat()
        })
    
    # If no stored recommendations but we have cached analysis, use cache
    if analysis_cache and analysis_cache.get("recommendations"):
        return jsonify({
            **analysis_cache,
            "real_time": True,
            "has_analysis": True,
            "timestamp": cache_timestamp.isoformat() if cache_timestamp else get_ist_time().isoformat()
        })
    
    # If no cache, check if services are configured
    if not databricks_client:
        return jsonify({
            "recommendations": [],
            "timestamp": get_ist_time().isoformat(),
            "real_time": True,
            "has_analysis": False,
            "message": "No analysis available. Databricks client not configured. Please configure Databricks credentials and run an analysis first."
        }), 200
    
    if not ai_agent:
        return jsonify({
            "recommendations": [],
            "timestamp": get_ist_time().isoformat(),
            "real_time": True,
            "has_analysis": False,
            "message": "No analysis available. AI agent not configured. Please configure OpenAI/Azure OpenAI credentials and run an analysis first."
        }), 200
    
    # If no cache but services are configured, return message to run analysis
    return jsonify({
        "recommendations": [],
        "timestamp": get_ist_time().isoformat(),
        "real_time": True,
        "has_analysis": False,
        "message": "No analysis available. Please run an analysis first."
    }), 200


@app.route("/api/stats", methods=["GET"])
def get_stats():
    """Get overall statistics including all compute resources."""
    if not databricks_client:
        return jsonify({"error": "Databricks client not configured"}), 503
    
    try:
        # Get basic resources with timeout protection
        try:
            jobs = databricks_client.get_all_jobs()
        except Exception as e:
            logger.warning(f"Error getting jobs: {e}")
            jobs = []
            
        try:
            clusters = databricks_client.get_all_clusters()
        except Exception as e:
            logger.warning(f"Error getting clusters: {e}")
            clusters = []
        
        def _is_running_cluster(cluster: Dict[str, Any]) -> bool:
            state = cluster.get("state")
            if not state:
                return False
            state_upper = str(state).upper()
            return state_upper in {"RUNNING", "RESIZING", "STARTING", "RESTARTING"}
        
        def _is_active_cluster(cluster: Dict[str, Any]) -> bool:
            """Check if cluster is active (not terminated)"""
            state = cluster.get("state")
            if not state:
                return True  # Include unknown states
            state_upper = str(state).upper()
            return state_upper not in {"TERMINATED", "TERMINATING"}

        # Filter out terminated clusters
        active_clusters = [c for c in clusters if _is_active_cluster(c)]
        running_clusters = [c for c in active_clusters if _is_running_cluster(c)]
        
        # Get all compute resource types (with individual error handling)
        try:
            sql_warehouses = databricks_client.get_sql_warehouses()
        except Exception as e:
            logger.warning(f"Error getting SQL warehouses: {e}")
            sql_warehouses = []
            
        try:
            pools = databricks_client.get_instance_pools()
        except Exception as e:
            logger.warning(f"Error getting instance pools: {e}")
            pools = []
            
        try:
            vector_search = databricks_client.get_vector_search_endpoints()
        except Exception as e:
            logger.warning(f"Error getting vector search endpoints: {e}")
            vector_search = []
            
        try:
            policies = databricks_client.get_cluster_policies()
        except Exception as e:
            logger.warning(f"Error getting cluster policies: {e}")
            policies = []
            
        try:
            apps = databricks_client.get_apps()
        except Exception as e:
            logger.warning(f"Error getting apps: {e}")
            apps = []
        
        # Get ML/AI resources (with individual error handling)
        try:
            ml_jobs = databricks_client.get_ml_jobs()
        except Exception as e:
            logger.warning(f"Error getting ML jobs: {e}")
            ml_jobs = []
            
        try:
            mlflow_experiments = databricks_client.get_mlflow_experiments()
        except Exception as e:
            logger.warning(f"Error getting MLflow experiments: {e}")
            mlflow_experiments = []
            
        try:
            mlflow_models = databricks_client.get_mlflow_models()
        except Exception as e:
            logger.warning(f"Error getting MLflow models: {e}")
            mlflow_models = []
            
        try:
            model_serving = databricks_client.get_model_serving_endpoints()
        except Exception as e:
            logger.warning(f"Error getting model serving endpoints: {e}")
            model_serving = []
            
        try:
            feature_store = databricks_client.get_feature_store_tables()
            logger.info(f"Successfully fetched {len(feature_store)} feature store tables")
        except Exception as e:
            logger.warning(f"Error getting feature store tables: {e}")
            feature_store = []
        
        logger.info(f"Stats: {len(jobs)} jobs, {len(active_clusters)} active clusters, {len(running_clusters)} running")
        
        return jsonify({
            # Basic stats
            "total_jobs": len(jobs),
            "total_clusters": len(active_clusters),
            "running_clusters": len(running_clusters),
            "idle_clusters": len([c for c in running_clusters if c.get("num_workers", 0) > 0]),
            
            # All compute resource types
            "sql_warehouses": len(sql_warehouses),
            "pools": len(pools),
            "vector_search_endpoints": len(vector_search),
            "policies": len(policies),
            "apps": len(apps),
            "lakebase_resources": 0,  # Placeholder - requires specific API
            
            # ML/AI resources
            "ml_jobs": len(ml_jobs),
            "mlflow_experiments": len(mlflow_experiments),
            "mlflow_models": len(mlflow_models),
            "model_serving_endpoints": len(model_serving),
            "feature_store_tables": len(feature_store),
            
            "timestamp": get_ist_time().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error fetching stats: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/summary", methods=["GET"])
def get_summary():
    """Get summary metrics including cost savings and optimization statistics."""
    try:
        # Get recommendations from cache
        recommendations = analysis_cache.get("recommendations", []) if analysis_cache else []

        def _parse_savings_value(rec: Dict[str, Any]) -> float:
            savings_value = 0.0
            savings_str = rec.get("estimated_savings", "")
            if savings_str:
                import re
                numbers = re.findall(r"\d+\.?\d*", savings_str)
                if numbers:
                    savings_value = float(numbers[0])
                    if "%" in savings_str.lower():
                        savings_value = savings_value * 100
            if not savings_value:
                for key in ("estimated_savings_monthly", "estimated_monthly_savings_usd"):
                    value = rec.get(key)
                    if isinstance(value, (int, float)):
                        savings_value = float(value)
                        break
            return savings_value
        
        # Calculate metrics
        total_recommendations = len(recommendations)
        
        # Calculate cost savings
        total_savings = 0
        savings_by_type = {"cost_leak": 0, "value_leak": 0, "optimization_opportunity": 0}
        
        for rec in recommendations:
            savings_value = _parse_savings_value(rec)
            if savings_value:
                total_savings += savings_value
                
                # Track by type
                rec_type = rec.get("type", "optimization_opportunity")
                if rec_type in savings_by_type:
                    savings_by_type[rec_type] += savings_value
        
        # Count by type
        by_type = {
            "cost_leak": len([r for r in recommendations if r.get("type") == "cost_leak"]),
            "value_leak": len([r for r in recommendations if r.get("type") == "value_leak"]),
            "optimization_opportunity": len([r for r in recommendations if r.get("type") == "optimization_opportunity"])
        }
        
        # Count by severity
        by_severity = {
            "high": len([r for r in recommendations if r.get("severity") == "high"]),
            "medium": len([r for r in recommendations if r.get("severity") == "medium"]),
            "low": len([r for r in recommendations if r.get("severity") == "low"])
        }
        
        # Count unique jobs identified for optimization
        job_ids = set()
        for rec in recommendations:
            if rec.get("resource_type") == "job":
                resource_id = rec.get("resource_id")
                if resource_id:
                    job_ids.add(str(resource_id))
        
        # Count unique resources by type
        resources_by_type = {}
        for rec in recommendations:
            res_type = rec.get("resource_type", "unknown")
            if res_type not in resources_by_type:
                resources_by_type[res_type] = set()
            resource_id = rec.get("resource_id")
            if resource_id:
                resources_by_type[res_type].add(str(resource_id))
        
        resources_count = {k: len(v) for k, v in resources_by_type.items()}
        
        # Get analysis metadata
        analysis_timestamp = cache_timestamp.isoformat() if cache_timestamp else None
        jobs_analyzed = analysis_cache.get("jobs_count", 0) if analysis_cache else 0
        clusters_analyzed = analysis_cache.get("clusters_count", 0) if analysis_cache else 0

        # Approval metrics for last 30 days
        now = get_ist_time()
        window_start = now - timedelta(days=30)
        approvals = list_recommendations()
        recent_approvals = []
        for rec in approvals:
            created_at = rec.get("created_at")
            if not created_at:
                continue
            try:
                created_dt = datetime.fromisoformat(created_at)
            except ValueError:
                continue
            if created_dt >= window_start:
                recent_approvals.append(rec)

        unique_recent = {rec.get("id") for rec in recent_approvals if rec.get("id")}
        applied_recent = [rec for rec in recent_approvals if rec.get("status") == "APPLIED"]
        applied_benefit = sum(_parse_savings_value(rec) for rec in applied_recent)
        
        return jsonify({
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
            "last_30_days": {
                "unique_recommendations": len(unique_recent),
                "applied_recommendations": len(applied_recent),
                "benefit_received": round(applied_benefit, 2),
                "benefit_received_formatted": f"${applied_benefit:,.2f}"
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
        return jsonify({
            "error": str(e),
            "total_cost_savings": 0,
            "total_recommendations": 0,
            "jobs_identified": 0,
            "has_analysis": False
        }), 500


@app.route("/api/config/delta-tables", methods=["GET", "POST"])
def configure_delta_tables():
    """Get or set Delta table configuration for analysis."""
    global delta_table_config
    
    if request.method == "POST":
        try:
            data = request.get_json() or {}
            
            # Update configuration with provided values
            if "cluster_events_table" in data:
                delta_table_config["cluster_events_table"] = data["cluster_events_table"]
                logger.info(f"Updated cluster_events_table to: {data['cluster_events_table']}")
            
            if "cluster_logs_table" in data:
                delta_table_config["cluster_logs_table"] = data["cluster_logs_table"]
                logger.info(f"Updated cluster_logs_table to: {data['cluster_logs_table']}")
            
            if "job_run_logs_table" in data:
                delta_table_config["job_run_logs_table"] = data["job_run_logs_table"]
                logger.info(f"Updated job_run_logs_table to: {data['job_run_logs_table']}")
            
            return jsonify({
                "success": True,
                "message": "Delta table configuration updated",
                "config": delta_table_config
            }), 200
        except Exception as e:
            logger.error(f"Error updating delta table config: {str(e)}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 400
    
    # GET method
    return jsonify({
        "config": delta_table_config,
        "help": "To update table names, send POST request with table names in the format 'database.table' (e.g., 'default.cluster_events')"
    }), 200


@app.route("/api/debug/warehouses", methods=["GET"])
def debug_warehouses():
    """Get available SQL warehouses for debugging."""
    if not databricks_client:
        return jsonify({"error": "Databricks client not configured"}), 503
    
    try:
        warehouses = databricks_client.get_sql_warehouses()
        return jsonify({
            "warehouses": warehouses,
            "count": len(warehouses),
            "help": "Use the 'id' field as warehouse_id in the analyze_delta_tables request body"
        })
    except Exception as e:
        logger.error(f"Error fetching warehouses: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/debug/clusters", methods=["GET"])
def debug_clusters():
    """Debug endpoint to test cluster fetching."""
    if not databricks_client:
        return jsonify({"error": "Databricks client not configured"}), 503
    
    try:
        logger.info("Debug: Testing cluster fetching...")
        clusters = databricks_client.get_all_clusters()
        
        return jsonify({
            "processed_clusters_count": len(clusters),
            "clusters": clusters,
            "client_host": databricks_client.host,
        })
    
    except Exception as e:
        logger.error(f"Debug error: {str(e)}", exc_info=True)
        return jsonify({
            "error": str(e),
            "error_type": type(e).__name__,
            "client_host": databricks_client.host if databricks_client else None,
        }), 500


@app.route("/api/delta-table/read", methods=["POST"])
def read_delta_table():
    """Read data from a Delta table."""
    if not databricks_client:
        return jsonify({"error": "Databricks client not configured"}), 503
    
    try:
        data = request.get_json()
        table_name = data.get("table_name")
        limit = data.get("limit", 1000)
        warehouse_id = data.get("warehouse_id")
        
        if not table_name:
            return jsonify({"error": "table_name is required"}), 400
        
        logger.info(f"Reading Delta table: {table_name}")
        result = databricks_client.read_delta_table(
            table_name=table_name,
            limit=limit,
            warehouse_id=warehouse_id
        )
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error reading Delta table: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/delta-table/summarize", methods=["POST"])
def summarize_delta_table():
    """Read a Delta table and generate an AI summary."""
    if not databricks_client:
        return jsonify({"error": "Databricks client not configured"}), 503
    
    ai_agent_instance = ensure_ai_agent()
    if not ai_agent_instance:
        return jsonify({"error": "AI agent not configured"}), 503
    
    try:
        data = request.get_json()
        table_name = data.get("table_name")
        limit = data.get("limit", 1000)
        warehouse_id = data.get("warehouse_id")
        analysis_focus = data.get("analysis_focus", "general")
        
        if not table_name:
            return jsonify({"error": "table_name is required"}), 400
        
        logger.info(f"Reading and summarizing Delta table: {table_name}")
        
        # Read the Delta table
        table_data = databricks_client.read_delta_table(
            table_name=table_name,
            limit=limit,
            warehouse_id=warehouse_id
        )
        
        if table_data.get("status") != "success":
            return jsonify(table_data), 400
        
        # Generate summary using AI
        summary = ai_agent_instance.summarize_delta_table_data(
            table_data=table_data,
            analysis_focus=analysis_focus
        )
        
        return jsonify(summary)
    
    except Exception as e:
        logger.error(f"Error summarizing Delta table: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/analyze-delta", methods=["POST"])
def analyze_delta_tables():
    """Analyze Delta log tables and create pending recommendations."""
    global delta_table_config
    
    if not databricks_client:
        return jsonify({"error": "Databricks client not configured"}), 503
    
    ai_agent_instance = ensure_ai_agent()
    if not ai_agent_instance:
        return jsonify({"error": "AI agent not configured"}), 503
    
    try:
        data = request.get_json() or {}
        
        # Use runtime configuration or request overrides
        cluster_events_table = data.get("cluster_events_table", delta_table_config.get("cluster_events_table"))
        cluster_logs_table = data.get("cluster_logs_table", delta_table_config.get("cluster_logs_table"))
        job_run_logs_table = data.get("job_run_logs_table", delta_table_config.get("job_run_logs_table"))
        limit = data.get("limit", 1000)
        analysis_focus = data.get("analysis_focus", "cost")
        warehouse_id = data.get("warehouse_id")
        
        # If no warehouse_id provided, try to get one (but don't fail if unavailable)
        if not warehouse_id:
            try:
                warehouses = databricks_client.get_sql_warehouses()
                if warehouses:
                    warehouse_id = warehouses[0].get("id")
                    logger.info(f"Using SQL warehouse: {warehouse_id}")
                else:
                    logger.warning("No SQL warehouses available. Analysis will use sample data.")
                    warehouse_id = None
            except Exception as e:
                logger.warning(f"Could not fetch warehouses: {str(e)}. Analysis will use sample data.")
                warehouse_id = None
        
        logger.info(f"Analyzing Delta tables: {cluster_events_table}, {cluster_logs_table}, {job_run_logs_table}")
        if warehouse_id:
            logger.info(f"Using warehouse: {warehouse_id}")
        else:
            logger.info("No warehouse available - using sample recommendations")
        
        # Try to read Delta tables if warehouse is available
        cluster_events = {}
        cluster_logs = {}
        job_run_logs = {}
        
        if warehouse_id:
            cluster_events = databricks_client.read_delta_table(
                table_name=cluster_events_table,
                limit=limit,
                warehouse_id=warehouse_id
            )
            
            if cluster_events.get("status") != "success":
                error_msg = cluster_events.get("error", "Unknown error")
                logger.error(f"Failed to read cluster_events table: {error_msg}")
                return jsonify({
                    "error": f"Failed to read cluster_events table '{cluster_events_table}': {error_msg}",
                    "table": cluster_events_table,
                    "details": cluster_events
                }), 400
            
            cluster_logs = databricks_client.read_delta_table(
                table_name=cluster_logs_table,
                limit=limit,
                warehouse_id=warehouse_id
            )
            
            if cluster_logs.get("status") != "success":
                error_msg = cluster_logs.get("error", "Unknown error")
                logger.error(f"Failed to read cluster_logs table: {error_msg}")
                return jsonify({
                    "error": f"Failed to read cluster_logs table '{cluster_logs_table}': {error_msg}",
                    "table": cluster_logs_table,
                    "details": cluster_logs
                }), 400
            
            job_run_logs = databricks_client.read_delta_table(
                table_name=job_run_logs_table,
                limit=limit,
                warehouse_id=warehouse_id
            )
            
            if job_run_logs.get("status") != "success":
                error_msg = job_run_logs.get("error", "Unknown error")
                logger.error(f"Failed to read job_run_logs table: {error_msg}")
                return jsonify({
                    "error": f"Failed to read job_run_logs table '{job_run_logs_table}': {error_msg}",
                    "table": job_run_logs_table,
                    "details": job_run_logs
                }), 400
            
            # Analyze with actual data
            analysis = ai_agent_instance.analyze_delta_logs(
                cluster_events=cluster_events,
                cluster_logs=cluster_logs,
                job_run_logs=job_run_logs,
                analysis_focus=analysis_focus
            )
        else:
            # No warehouse available - generate sample recommendations
            logger.info("No warehouse available - generating sample recommendations")
            analysis = {
                "status": "success",
                "summary": "Sample recommendations generated (no warehouse available for live analysis)",
                "recommendations": [
                    {
                        "type": "COST_OPTIMIZATION",
                        "severity": "HIGH",
                        "title": "Right-size cluster memory",
                        "description": "Cluster clusteriq is oversized for workload. Current: Standard_D4ds_v5 (16GB, 4 cores), Recommended: Standard_D2ds_v5 (8GB, 2 cores)",
                        "estimated_savings": 500,
                        "resource_type": "cluster",
                        "resource_name": "clusteriq",
                        "resource_id": "clusteriq",
                        "action": {
                            "type": "resize_cluster",
                            "target_id": "clusteriq",
                            "params": {
                                "node_type_id": "Standard_D2ds_v5",
                                "driver_node_type_id": "Standard_D2ds_v5",
                                "num_workers": 2
                            }
                        }
                    },
                    {
                        "type": "PERFORMANCE",
                        "severity": "MEDIUM",
                        "title": "Optimize job scheduling",
                        "description": "Job execution shows frequent retries",
                        "estimated_savings": 300,
                        "action": None
                    }
                ]
            }
        
        if analysis.get("status") != "success":
            return jsonify(analysis), 500
        
        pending = add_recommendations(analysis.get("recommendations", []))
        
        return jsonify({
            "summary": analysis.get("summary", ""),
            "recommendations": pending,
            "tables": {
                "cluster_events": cluster_events_table,
                "cluster_logs": cluster_logs_table,
                "job_run_logs": job_run_logs_table
            },
            "warehouse_id": warehouse_id,
            "mode": "live" if warehouse_id else "sample"
        })
    
    except Exception as e:
        logger.error(f"Error analyzing delta tables: {str(e)}", exc_info=True)
        error_str = str(e)
        
        # Check for UC_NOT_ENABLED error
        if "UC_NOT_ENABLED" in error_str or "Unity Catalog is not enabled" in error_str:
            return jsonify({
                "error": "Unity Catalog is not enabled on your cluster.",
                "solution": "Use Hive metastore table names in format: 'database.table' (e.g., 'default.cluster_events')",
                "help": "You can configure table names via environment variables: DELTA_CLUSTER_EVENTS_TABLE, DELTA_CLUSTER_LOGS_TABLE, DELTA_JOB_RUN_LOGS_TABLE",
                "details": error_str
            }), 400
        
        return jsonify({
            "error": str(e),
            "help": "Check that the table names exist and are in correct format. Use 'database.table' for Hive metastore."
        }), 500


@app.route("/api/approvals", methods=["GET"])
def get_approvals():
    """List recommendations by approval status."""
    status = request.args.get("status")
    return jsonify({
        "recommendations": list_recommendations(status=status),
        "status_filter": status
    })


@app.route("/api/approvals/<rec_id>/approve", methods=["POST"])
def approve_recommendation(rec_id):
    """Approve a recommendation."""
    try:
        updated = update_status(rec_id, "APPROVED")
        if not updated:
            logger.warning(f"Recommendation {rec_id} not found")
            return jsonify({"success": False, "error": "Recommendation not found"}), 404
        logger.info(f"Approved recommendation {rec_id}")
        return jsonify({"success": True, "message": "Recommendation approved", "data": updated}), 200
    except Exception as e:
        logger.error(f"Error approving recommendation {rec_id}: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/approvals/<rec_id>/reject", methods=["POST"])
def reject_recommendation(rec_id):
    """Reject a recommendation."""
    try:
        updated = update_status(rec_id, "REJECTED")
        if not updated:
            logger.warning(f"Recommendation {rec_id} not found")
            return jsonify({"success": False, "error": "Recommendation not found"}), 404
        logger.info(f"Rejected recommendation {rec_id}")
        return jsonify({"success": True, "message": "Recommendation rejected", "data": updated}), 200
    except Exception as e:
        logger.error(f"Error rejecting recommendation {rec_id}: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/approvals/<rec_id>/apply", methods=["POST"])
def apply_recommendation(rec_id):
    """Apply an approved recommendation using Databricks APIs."""
    try:
        if not databricks_client:
            return jsonify({"success": False, "error": "Databricks client not configured"}), 503

        from self_healing_config import get_history
        history = get_history()
        
        rec = get_recommendation(rec_id)
        if not rec:
            return jsonify({"success": False, "error": "Recommendation not found"}), 404
        
        if rec.get("status") != "APPROVED":
            return jsonify({"success": False, "error": f"Recommendation is not approved (current status: {rec.get('status')})"}), 400
        
        action = rec.get("action", {})
        # Handle case where action is a string or not a dict
        if not isinstance(action, dict):
            action = {}
        action_type = action.get("type")
        target_id = action.get("target_id")
        params = action.get("params", {})
        applied_note = None

        # Handle idle_cluster and informational recommendations that don't require action
        rec_type = rec.get("type", "")
        if rec_type in ["idle_cluster", "optimization"]:
            # These are informational - mark as applied without taking action
            updated = update_status(rec_id, "APPLIED", note="Recommendation noted and monitored")
            return jsonify({
                "success": True,
                "message": f"Recommendation marked as applied",
                "recommendation": updated
            }), 200

        if (not action_type or not target_id) and rec.get("resource_type") == "cluster":
            target_id = rec.get("resource_id") or rec.get("resource_name")
            action_type = "enable_autotermination"
            params = {"autotermination_minutes": 5}

        if not action_type or not target_id:
            logger.warning(f"Recommendation {rec_id} has no actionable details. Action: {action}")
            return jsonify({"success": False, "error": "Recommendation has no actionable details"}), 400
        
        def resolve_cluster_id(cluster_id_or_name: str) -> str:
            clusters = databricks_client.get_all_clusters()
            for cluster in clusters:
                if cluster.get("cluster_id") == cluster_id_or_name:
                    return cluster_id_or_name
            for cluster in clusters:
                if cluster.get("cluster_name") == cluster_id_or_name:
                    return cluster.get("cluster_id")
            return cluster_id_or_name

        def extract_core_limits(error_message: str) -> tuple:
            match = re.search(r"Estimated available:\s*(\d+)\s*,\s*requested:\s*(\d+)", error_message)
            if not match:
                match = re.search(r"available:\s*(\d+).*requested:\s*(\d+)", error_message, re.IGNORECASE)
            if not match:
                return (None, None)
            return (int(match.group(1)), int(match.group(2)))

        def format_estimated_savings(recommendation: Dict[str, Any]) -> Optional[str]:
            if not recommendation:
                return None
            value = recommendation.get("estimated_savings")
            if value is None:
                for key in ("estimated_savings_monthly", "estimated_monthly_savings_usd", "estimated_savings_annual", "estimated_annual_savings_usd"):
                    if isinstance(recommendation.get(key), (int, float)):
                        value = recommendation.get(key)
                        break
            if isinstance(value, (int, float)):
                return f"${value:,.2f}"
            if isinstance(value, str) and value.strip():
                return value
            return None

        if action_type in {"terminate_cluster", "resize_cluster", "enable_autotermination", "restart_cluster", "recreate_cluster"}:
            target_id = resolve_cluster_id(target_id)

        logger.info(f"Applying recommendation {rec_id}: {action_type} on {target_id}")
        
        result = {"status": "error", "error": "Unsupported action type"}
        
        if action_type == "terminate_cluster":
            # Check if cluster exists first
            clusters = databricks_client.get_all_clusters()
            cluster_found = any(c.get("cluster_id") == target_id or c.get("cluster_name") == target_id for c in clusters)
            
            if not cluster_found:
                error_msg = f"Cluster '{target_id}' not found in workspace. It may already be terminated or does not exist."
                logger.warning(f"Cluster {target_id} not found. Available clusters: {[c.get('cluster_name') for c in clusters]}")
                update_status(rec_id, "FAILED", note=error_msg)
                return jsonify({
                    "success": False,
                    "error": error_msg,
                    "result": {"status": "not_found", "message": f"Cluster {target_id} not found"},
                    "recommendation": rec
                }), 404
            
            result = databricks_client.terminate_cluster(target_id)
        
        elif action_type == "resize_cluster":
            node_type = params.get("node_type_id")
            driver_node_type = params.get("driver_node_type_id")
            requested_workers = params.get("num_workers")
            autoscale = params.get("autoscale")

            if node_type or driver_node_type:
                update_params = {}
                if node_type:
                    update_params["node_type_id"] = node_type
                if driver_node_type:
                    update_params["driver_node_type_id"] = driver_node_type
                if requested_workers is not None:
                    update_params["num_workers"] = requested_workers
                if autoscale is not None:
                    update_params["autoscale"] = autoscale

                cluster_info = databricks_client.get_cluster_info(target_id)
                cluster_state = None
                if cluster_info.get("status") == "success":
                    cluster_state = cluster_info.get("cluster", {}).get("state")
                original_state = cluster_state

                # Wait for cluster to reach a stable state before proceeding
                transitional_states = {"PENDING", "RESTARTING", "TERMINATING", "RESIZING"}
                if cluster_state in transitional_states:
                    wait_deadline = time.time() + 300  # 5 minutes timeout
                    while time.time() < wait_deadline:
                        time.sleep(10)
                        cluster_info = databricks_client.get_cluster_info(target_id)
                        if cluster_info.get("status") == "success":
                            cluster_state = cluster_info.get("cluster", {}).get("state")
                            if cluster_state not in transitional_states:
                                break
                    
                    # If still in transitional state after timeout, fail gracefully
                    if cluster_state in transitional_states:
                        result = {
                            "status": "error",
                            "error": f"Cluster is in transitional state '{cluster_state}'. Please wait for cluster to stabilize and try again."
                        }
                        applied_note = f"Cannot resize: cluster is in {cluster_state} state"
                        # Skip further processing
                        node_type = None
                        driver_node_type = None

                if cluster_state and cluster_state not in {"TERMINATED"} and (node_type or driver_node_type):
                    terminate_result = databricks_client.terminate_cluster(target_id)
                    if terminate_result.get("status") != "success":
                        result = terminate_result
                    else:
                        deadline = time.time() + 180
                        while time.time() < deadline:
                            latest = databricks_client.get_cluster_info(target_id)
                            latest_state = latest.get("cluster", {}).get("state") if latest.get("status") == "success" else None
                            if latest_state == "TERMINATED":
                                break
                            time.sleep(5)

                result = databricks_client.update_cluster_config(
                    cluster_id=target_id,
                    **update_params
                )

                if result.get("status") == "success" and original_state == "RUNNING":
                    start_result = databricks_client.start_cluster(target_id)
                    if start_result.get("status") != "success":
                        applied_note = (
                            "Cluster config updated, but failed to restart automatically. "
                            f"Start the cluster manually. Error: {start_result.get('error', 'Unknown error')}"
                        )
                    else:
                        applied_note = "Cluster config updated and cluster restarted with new node type."
            else:
                # Wait for cluster to reach a stable state before resizing
                cluster_info = databricks_client.get_cluster_info(target_id)
                cluster_state = None
                if cluster_info.get("status") == "success":
                    cluster_state = cluster_info.get("cluster", {}).get("state")
                
                transitional_states = {"PENDING", "RESTARTING", "TERMINATING", "RESIZING"}
                if cluster_state in transitional_states:
                    wait_deadline = time.time() + 300  # 5 minutes timeout
                    while time.time() < wait_deadline:
                        time.sleep(10)
                        cluster_info = databricks_client.get_cluster_info(target_id)
                        if cluster_info.get("status") == "success":
                            cluster_state = cluster_info.get("cluster", {}).get("state")
                            if cluster_state not in transitional_states:
                                break
                    
                    # If still in transitional state after timeout, fail gracefully
                    if cluster_state in transitional_states:
                        result = {
                            "status": "error",
                            "error": f"Cluster is in transitional state '{cluster_state}'. Please wait for cluster to stabilize and try again."
                        }
                        applied_note = f"Cannot resize: cluster is in {cluster_state} state"
                
                # Only proceed with resize if not in transitional state
                if cluster_state not in transitional_states:
                    result = databricks_client.resize_cluster(
                        cluster_id=target_id,
                        num_workers=requested_workers,
                        autoscale=autoscale
                    )

                    if result.get("status") != "success":
                        error_msg = str(result.get("error", ""))
                        if "not have enough CPU cores" in error_msg and requested_workers:
                            available_cores, requested_cores = extract_core_limits(error_msg)
                            if available_cores and requested_cores and requested_cores > 0:
                                adjusted_workers = max(1, int((available_cores * requested_workers) // requested_cores))
                                if adjusted_workers < requested_workers:
                                    retry_result = databricks_client.resize_cluster(
                                        cluster_id=target_id,
                                        num_workers=adjusted_workers
                                    )
                                    if retry_result.get("status") == "success":
                                        applied_note = (
                                            "Applied with adjusted workers due to core limits. "
                                            f"Requested workers: {requested_workers}, "
                                            f"available cores: {available_cores}, requested cores: {requested_cores}, "
                                            f"applied workers: {adjusted_workers}."
                                        )
                                        result = retry_result
                                    else:
                                        result = retry_result
        elif action_type == "enable_autotermination":
            # Enable auto-termination on a cluster
            autotermination_minutes = params.get("autotermination_minutes", 5)
            result = databricks_client.update_cluster_config(
                cluster_id=target_id,
                autotermination_minutes=autotermination_minutes
            )
        
        elif action_type in ["restart_cluster", "recreate_cluster"]:
            # Restart a cluster to fix execution errors
            logger.info(f"Restarting cluster {target_id} to fix execution error")
            
            # Get cluster info
            cluster_info = databricks_client.get_cluster_info(target_id)
            if cluster_info.get("status") != "success":
                result = {
                    "status": "error",
                    "error": f"Could not get cluster info: {cluster_info.get('error', 'Unknown')}"
                }
            else:
                cluster_state = cluster_info.get("cluster", {}).get("state")
                cluster_name = cluster_info.get("cluster", {}).get("cluster_name", target_id)
                
                # If cluster is in error state, terminate it first
                if cluster_state in ["FAILED", "ERROR", "TERMINATING"]:
                    logger.info(f"Cluster {cluster_name} is in {cluster_state} state, terminating first")
                    terminate_result = databricks_client.terminate_cluster(target_id)
                    if terminate_result.get("status") != "success":
                        result = terminate_result
                    else:
                        # Wait for termination
                        deadline = time.time() + 60
                        while time.time() < deadline:
                            check = databricks_client.get_cluster_info(target_id)
                            if check.get("cluster", {}).get("state") == "TERMINATED":
                                break
                            time.sleep(2)
                elif cluster_state == "RUNNING":
                    # Restart running cluster
                    logger.info(f"Cluster {cluster_name} is running, restarting")
                    databricks_client.terminate_cluster(target_id)
                    # Wait for termination
                    deadline = time.time() + 60
                    while time.time() < deadline:
                        check = databricks_client.get_cluster_info(target_id)
                        if check.get("cluster", {}).get("state") == "TERMINATED":
                            break
                        time.sleep(2)
                
                # Start the cluster
                logger.info(f"Starting cluster {cluster_name}")
                start_result = databricks_client.start_cluster(target_id)
                if start_result.get("status") == "success":
                    result = {
                        "status": "success",
                        "message": f"Cluster {cluster_name} restarted successfully to fix execution error"
                    }
                    applied_note = f"Cluster restarted successfully. Job should now run without execution errors."
                else:
                    result = start_result
        
        elif action_type == "cancel_job_run":
            # Cancel a stuck job run
            run_id = params.get("run_id") or target_id
            job_id = params.get("job_id")
            reason = params.get("reason", "Stuck in PENDING state")
            
            logger.info(f"Cancelling stuck job run {run_id} (Job ID: {job_id})")
            
            cancel_result = databricks_client.cancel_job_run(run_id)
            if cancel_result.get("status") == "success":
                result = {
                    "status": "success",
                    "message": f"Successfully cancelled stuck job run {run_id}"
                }
                applied_note = f"Cancelled job run that was stuck in PENDING state. Reason: {reason}"
                logger.info(f"Successfully cancelled stuck job run {run_id}")
            else:
                result = cancel_result
                logger.error(f"Failed to cancel job run {run_id}: {cancel_result.get('error')}")
        
        elif action_type == "restart_job_run":
            # Restart a failed job by submitting a new run
            job_id = params.get("job_id") or target_id
            failed_run_id = params.get("run_id")
            error_message = params.get("error_message", "Execution error")
            job_name = rec.get("resource_name") or rec.get("resource_id") or str(job_id)
            
            logger.info(f"Restarting failed job {job_id} (failed run: {failed_run_id})")
            
            submit_result = databricks_client.submit_job_run(job_id)
            if submit_result.get("status") == "success":
                new_run_id = submit_result.get("run_id")
                result = {
                    "status": "success",
                    "message": f"Successfully submitted new run for job {job_id}",
                    "new_run_id": new_run_id,
                    "previous_failed_run_id": failed_run_id
                }
                applied_note = f"Job rerun submitted (new run ID: {new_run_id}). Previous failed run: {failed_run_id}. Error: {error_message[:100]}"
                history.add_action(
                    action_type="restart_failed_job",
                    resource_id=str(job_id),
                    resource_type="job",
                    status="success",
                    details={
                        "job_name": job_name,
                        "job_id": job_id,
                        "new_run_id": new_run_id,
                        "failed_run_id": failed_run_id,
                        "error_message": error_message[:200]
                    }
                )
                logger.info(f"Successfully submitted new run {new_run_id} for job {job_id}")
            else:
                result = submit_result
                history.add_action(
                    action_type="restart_failed_job",
                    resource_id=str(job_id),
                    resource_type="job",
                    status="failed",
                    details={
                        "job_name": job_name,
                        "job_id": job_id,
                        "failed_run_id": failed_run_id,
                        "error": submit_result.get("error", "Unknown error")
                    }
                )
                logger.error(f"Failed to submit new run for job {job_id}: {submit_result.get('error')}")
        
        if result.get("status") == "success":
            savings_label = format_estimated_savings(rec)
            if savings_label:
                if applied_note:
                    applied_note = f"{applied_note} Estimated savings: {savings_label}"
                else:
                    applied_note = f"Applied successfully. Estimated savings: {savings_label}"
            updated = update_status(rec_id, "APPLIED", note=applied_note)
            logger.info(f"Successfully applied recommendation {rec_id}")
            return jsonify({
                "success": True,
                "message": "Recommendation applied successfully",
                "result": result,
                "recommendation": updated
            }), 200
        
        error_msg = result.get("error", "Unknown error")
        update_status(rec_id, "FAILED", note=error_msg)
        logger.error(f"Failed to apply recommendation {rec_id}: {error_msg}")
        return jsonify({
            "success": False,
            "error": f"Failed to apply recommendation: {error_msg}",
            "result": result,
            "recommendation": rec
        }), 400
    
    except Exception as e:
        logger.error(f"Exception while applying recommendation {rec_id}: {str(e)}", exc_info=True)
        update_status(rec_id, "FAILED", note=str(e))
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}"
        }), 500


@app.route("/api/cost/pricing", methods=["GET"])
def get_pricing_tiers():
    """Get all pricing tiers for different resource types."""
    try:
        return jsonify({
            "success": True,
            "pricing_tiers": cost_calculator.pricing_tiers,
            "description": {
                "jobs_compute_standard": "$0.15 per DBU-hour",
                "jobs_compute_premium": "$0.22 per DBU-hour (average)",
                "all_purpose_standard": "$0.40 per DBU-hour",
                "all_purpose_premium": "$0.475 per DBU-hour (average)",
                "serverless_sql": "$0.70 per DBU-hour",
                "model_serving_cpu": "$0.08 per DBU-hour",
                "model_serving_gpu": "$0.65 per DBU-hour"
            }
        }), 200
    except Exception as e:
        logger.error(f"Error getting pricing tiers: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/cost/cluster/<cluster_id>", methods=["GET"])
def get_cluster_cost(cluster_id):
    """Get cost analysis for a specific cluster."""
    if not databricks_client:
        return jsonify({"success": False, "error": "Databricks client not configured"}), 503
    
    try:
        hours_running = request.args.get("hours", 100, type=float)
        
        # Get cluster details
        clusters = databricks_client.get_all_clusters()
        cluster_info = next((c for c in clusters if c.get("cluster_id") == cluster_id), None)
        
        if not cluster_info:
            return jsonify({"success": False, "error": "Cluster not found"}), 404
        
        cost_data = cost_calculator.calculate_cluster_cost(cluster_info, hours_running)
        
        logger.info(f"Calculated cost for cluster {cluster_id}: ${cost_data['total_cost']}")
        
        return jsonify({
            "success": True,
            "cost_analysis": cost_data
        }), 200
    
    except Exception as e:
        logger.error(f"Error calculating cluster cost: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/cost/job/<job_id>", methods=["GET"])
def get_job_cost(job_id):
    """Get cost analysis for a specific job."""
    if not databricks_client:
        return jsonify({"success": False, "error": "Databricks client not configured"}), 503
    
    try:
        runs_per_month = request.args.get("runs", 4, type=int)
        avg_runtime = request.args.get("runtime", 0.5, type=float)
        
        # Get job details
        jobs = databricks_client.get_all_jobs()
        job_info = next((j for j in jobs if j.get("job_id") == int(job_id)), None)
        
        if not job_info:
            return jsonify({"success": False, "error": "Job not found"}), 404
        
        cost_data = cost_calculator.calculate_job_cost(job_info, runs_per_month, avg_runtime)
        
        logger.info(f"Calculated cost for job {job_id}: ${cost_data['monthly_cost']}/month")
        
        return jsonify({
            "success": True,
            "cost_analysis": cost_data
        }), 200
    
    except Exception as e:
        logger.error(f"Error calculating job cost: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/cost/breakdown", methods=["GET"])
def get_cost_breakdown():
    """Get comprehensive cost breakdown for all resources."""
    if not databricks_client:
        return jsonify({"success": False, "error": "Databricks client not configured"}), 503
    
    try:
        # Fetch all resources
        clusters = databricks_client.get_all_clusters()
        jobs = databricks_client.get_all_jobs()
        
        resources = {
            "clusters": clusters,
            "jobs": jobs
        }
        
        breakdown = cost_calculator.generate_cost_breakdown(resources)
        
        logger.info(f"Generated cost breakdown. Total cost: ${breakdown['total_cost']}")
        
        return jsonify({
            "success": True,
            "breakdown": breakdown,
            "cluster_count": len(clusters),
            "job_count": len(jobs)
        }), 200
    
    except Exception as e:
        logger.error(f"Error generating cost breakdown: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/cost/recommendations/<cluster_id>", methods=["GET"])
def get_cost_recommendations(cluster_id):
    """Get cost savings recommendations for a cluster."""
    if not databricks_client:
        return jsonify({"success": False, "error": "Databricks client not configured"}), 503
    
    try:
        # Get cluster details
        clusters = databricks_client.get_all_clusters()
        cluster_info = next((c for c in clusters if c.get("cluster_id") == cluster_id), None)
        
        if not cluster_info:
            return jsonify({"success": False, "error": "Cluster not found"}), 404
        
        recommendations = cost_calculator.get_cost_savings_recommendations(cluster_info)
        
        logger.info(f"Generated {len(recommendations)} cost recommendations for cluster {cluster_id}")
        
        return jsonify({
            "success": True,
            "recommendations": recommendations,
            "cluster_info": {
                "cluster_id": cluster_info.get("cluster_id"),
                "cluster_name": cluster_info.get("cluster_name"),
                "num_workers": cluster_info.get("num_workers")
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting cost recommendations: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/sql/execute", methods=["POST"])
def execute_sql():
    """Execute a SQL query on Databricks."""
    if not databricks_client:
        return jsonify({"error": "Databricks client not configured"}), 503
    
    try:
        data = request.get_json()
        query = data.get("query")
        warehouse_id = data.get("warehouse_id")
        
        if not query:
            return jsonify({"error": "query is required"}), 400
        
        logger.info(f"Executing SQL query")
        result = databricks_client.execute_sql_query(
            query=query,
            warehouse_id=warehouse_id
        )
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error executing SQL: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/logs", methods=["GET"])
def get_logs():
    """Retrieve application logs with optional filtering.
    
    Query parameters:
    - level: Filter by log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - logger: Filter by logger name
    - limit: Maximum number of logs to return (default: 100)
    """
    try:
        level = request.args.get("level")
        logger_name = request.args.get("logger")
        limit = request.args.get("limit", 100, type=int)
        
        logs = log_manager.get_logs(
            level=level,
            limit=limit,
            logger_name=logger_name
        )
        
        return jsonify({
            "success": True,
            "count": len(logs),
            "logs": logs
        })
    
    except Exception as e:
        logger.error(f"Error retrieving logs: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/logs/stats", methods=["GET"])
def get_logs_stats():
    """Get logging statistics."""
    try:
        stats = log_manager.get_stats()
        return jsonify({
            "success": True,
            "stats": stats
        })
    
    except Exception as e:
        logger.error(f"Error retrieving log stats: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/logs/levels", methods=["GET"])
def get_logs_by_level():
    """Get count of logs by level."""
    try:
        level_counts = log_manager.get_logs_by_level()
        return jsonify({
            "success": True,
            "data": level_counts
        })
    
    except Exception as e:
        logger.error(f"Error retrieving logs by level: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/logs/export", methods=["GET"])
def export_logs():
    """Export logs in specified format (json or csv)."""
    try:
        format = request.args.get("format", "json")
        if format not in ["json", "csv"]:
            return jsonify({
                "success": False,
                "error": "Format must be 'json' or 'csv'"
            }), 400
        
        content = log_manager.export_logs(format=format)
        
        if format == "csv":
            return content, 200, {"Content-Type": "text/csv"}
        else:
            return jsonify({
                "success": True,
                "data": content
            })
    
    except Exception as e:
        logger.error(f"Error exporting logs: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/logs/clear", methods=["POST"])
def clear_logs():
    """Clear all stored logs."""
    try:
        log_manager.clear_logs()
        return jsonify({
            "success": True,
            "message": "All logs cleared"
        })
    
    except Exception as e:
        logger.error(f"Error clearing logs: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# Setup logging for the app

# ============================================================================
# SELF-HEALING API ENDPOINTS
# ============================================================================

@app.route("/api/self-healing/config", methods=["GET", "POST"])
def self_healing_config():
    """Get or update self-healing configuration."""
    try:
        from self_healing_config import get_config
        
        config = get_config()
        
        if request.method == "POST":
            updates = request.get_json() or {}
            config.update_config(updates)
            logger.info(f"Self-healing config updated: {updates}")
            return jsonify({
                "success": True,
                "message": "Configuration updated",
                "config": config.config
            }), 200
        
        # GET method
        return jsonify({
            "success": True,
            "config": config.config
        }), 200
    
    except Exception as e:
        logger.error(f"Error managing self-healing config: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/self-healing/health", methods=["GET"])
def get_health_status():
    """Get current health status of all clusters."""
    logger.info("Health check endpoint called")
    try:
        from health_monitor import HealthMonitor
        
        if not databricks_client:
            return jsonify({
                "success": False,
                "error": "Databricks client not initialized",
                "auto_healable": [],
                "auto_healable_issues_count": 0
            }), 500
        
        # Use health monitor to get comprehensive health data
        monitor = HealthMonitor(databricks_client)
        summary = monitor.get_health_summary()
        auto_healable_issues = monitor.get_auto_healable_issues()
        
        idle_recommendations = []
        now = get_ist_time().isoformat()
        for issue_info in auto_healable_issues:
            issue = issue_info.get("issue", {})
            if issue.get("type") != "cluster_idle":
                continue
            cluster_id = issue_info.get("cluster_id")
            cluster_name = issue_info.get("cluster_name") or "Unknown"
            idle_recommendations.append({
                "id": f"rec_idle_{cluster_id}",
                "type": "idle_cluster",
                "severity": "medium",
                "title": f"Idle cluster detected: {cluster_name}",
                "description": "Cluster is idle and consuming resources. Consider terminating or enabling auto-termination.",
                "resource_type": "cluster",
                "resource_id": cluster_id,
                "resource_name": cluster_name,
                "status": "PENDING",
                "action": {
                    "type": "enable_autotermination",
                    "cluster_id": cluster_id,
                    "autotermination_minutes": 5
                },
                "status_note": "Auto-detected from health check",
                "created_at": now,
                "updated_at": now
            })
        if idle_recommendations:
            add_recommendations(idle_recommendations)

        optimization_by_key = {}
        recommendations = list_recommendations()
        for rec in recommendations:
            rec_type = (rec.get("type") or "").lower()
            if rec_type != "cost_optimization":
                continue
            if rec.get("resource_type") != "cluster":
                continue
            if rec.get("status") != "PENDING":
                continue
            action = rec.get("action")
            if action is None or action == "":
                continue
            cluster_id = rec.get("resource_id") or rec.get("resource_name")
            cluster_name = rec.get("resource_name") or rec.get("resource_id") or "Unknown"
            message = rec.get("title") or rec.get("description") or "Optimization available"
            timestamp = rec.get("updated_at") or rec.get("created_at") or now
            try:
                timestamp_dt = datetime.fromisoformat(timestamp)
            except (TypeError, ValueError):
                timestamp_dt = datetime.min
            key = f"{cluster_id}|{message}"
            existing = optimization_by_key.get(key)
            if not existing or timestamp_dt > existing["_ts"]:
                optimization_by_key[key] = {
                    "_ts": timestamp_dt,
                    "cluster_id": cluster_id,
                    "cluster_name": cluster_name,
                    "issue_type": "optimization",
                    "issue": {
                        "type": "optimization",
                        "severity": (rec.get("severity") or "medium").lower(),
                        "message": message
                    },
                    "recommendation_id": rec.get("id"),
                    "timestamp": timestamp
                }

        optimization_issues = []
        for item in optimization_by_key.values():
            item.pop("_ts", None)
            optimization_issues.append(item)

        combined_auto_healable = auto_healable_issues + optimization_issues
        
        logger.info(f"Health check: {summary['total_clusters']} total, {len(auto_healable_issues)} auto-healable issues detected")
        
        response_data = {
            "success": True,
            "summary": {
                "total_clusters": summary.get("total_clusters", 0),
                "healthy": summary.get("healthy", 0),
                "unhealthy": summary.get("unhealthy", 0),
                "health_percentage": summary.get("health_percentage", 0)
            },
            "auto_healable": combined_auto_healable,
            "auto_healable_issues_count": len(combined_auto_healable),
            "timestamp": get_ist_time().isoformat()
        }
        
        logger.info(f"Returning health status with {len(auto_healable_issues)} auto-healable issues")
        return jsonify(response_data), 200
    
    except Exception as e:
        logger.error(f"Error checking health: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e),
            "auto_healable": [],
            "auto_healable_issues_count": 0
        }), 500


@app.route("/api/self-healing/run", methods=["POST"])
def run_self_healing():
    """Manually trigger self-healing process."""
    try:
        from auto_remediation import AutoRemediation
        from self_healing_config import get_config, get_history
        
        logger.info("Self-healing run triggered")
        
        # Get config and history to see what's enabled
        config = get_config()
        history = get_history()
        
        if not databricks_client:
            return jsonify({
                "success": False,
                "error": "Databricks client not initialized",
                "actions_taken": 0,
                "scanned_clusters": 0
            }), 500
        
        # Create remediation engine
        remediation = AutoRemediation(databricks_client)
        
        # Run healing with detailed diagnostics
        actions_taken = 0
        results = []
        diagnostics = []
        
        try:
            # Get current clusters
            clusters = databricks_client.get_all_clusters()
            logger.info(f"Scanned {len(clusters)} clusters for healing")
            
            failed_clusters = []
            running_clusters = []
            
            # Analyze clusters
            for cluster in clusters:
                cluster_id = cluster.get("cluster_id")
                cluster_name = cluster.get("cluster_name", "Unknown")
                state = cluster.get("state", "UNKNOWN")
                
                logger.info(f"Checking cluster {cluster_name} ({cluster_id}): {state}")
                
                if state in ["FAILED", "ERROR"]:
                    failure_time = None
                    for time_key in ("terminated_time", "last_state_loss_time", "last_activity_time", "start_time"):
                        failure_time = _parse_event_time(cluster.get(time_key))
                        if failure_time:
                            break

                    restart_window_minutes = config.get_threshold("failed_restart_window_minutes") or 120
                    if not failure_time:
                        diagnostics.append({
                            "cluster_id": cluster_id,
                            "cluster_name": cluster_name,
                            "issue": f"Cluster is in {state} state but no recent failure timestamp is available",
                            "action_available": f"Auto-restart skipped (requires failure within last {restart_window_minutes} minutes)"
                        })
                    elif get_ist_time() - failure_time > timedelta(minutes=restart_window_minutes):
                        diagnostics.append({
                            "cluster_id": cluster_id,
                            "cluster_name": cluster_name,
                            "issue": f"Cluster is in {state} state but failure is older than {restart_window_minutes} minutes",
                            "action_available": "Auto-restart skipped (outside restart window)"
                        })
                    else:
                        failed_clusters.append((cluster_id, cluster_name, state))
                        diagnostics.append({
                            "cluster_id": cluster_id,
                            "cluster_name": cluster_name,
                            "issue": f"Cluster is in {state} state",
                            "action_available": f"auto_restart_failed_clusters (within {restart_window_minutes} minutes)"
                        })
                
                if state == "RUNNING":
                    running_clusters.append((cluster_id, cluster_name))
            
            # Process failed clusters - auto-restart
            if config.is_feature_enabled("auto_restart_failed_clusters"):
                for cluster_id, cluster_name, state in failed_clusters:
                    try:
                        logger.info(f"Auto-restarting failed cluster {cluster_name}")
                        result = remediation.auto_restart_cluster(cluster_id, f"Auto-restart triggered for {state} cluster")
                        if result.get("success"):
                            actions_taken += 1
                            # Record action in history
                            history.add_action(
                                action_type="auto_restart",
                                resource_id=cluster_id,
                                resource_type="cluster",
                                status="success",
                                details={
                                    "cluster_name": cluster_name,
                                    "reason": f"Auto-restart triggered for {state} cluster",
                                    "dry_run": config.config.get("safety", {}).get("dry_run", False)
                                }
                            )
                            results.append({
                                "action": "restart",
                                "cluster_id": cluster_id,
                                "cluster_name": cluster_name,
                                "status": "success",
                                "message": f"Successfully restarted {cluster_name}"
                            })
                            logger.info(f"Successfully restarted {cluster_name}")
                        else:
                            # Record failed action
                            history.add_action(
                                action_type="auto_restart",
                                resource_id=cluster_id,
                                resource_type="cluster",
                                status="failed",
                                details={
                                    "cluster_name": cluster_name,
                                    "reason": result.get("message", "Unknown error"),
                                    "dry_run": config.config.get("safety", {}).get("dry_run", False)
                                }
                            )
                            results.append({
                                "action": "restart",
                                "cluster_id": cluster_id,
                                "cluster_name": cluster_name,
                                "status": "failed",
                                "message": result.get("message", "Unknown error")
                            })
                    except Exception as e:
                        logger.error(f"Error auto-restarting cluster {cluster_name}: {e}")
                        history.add_action(
                            action_type="auto_restart",
                            resource_id=cluster_id,
                            resource_type="cluster",
                            status="error",
                            details={
                                "cluster_name": cluster_name,
                                "error": str(e),
                                "dry_run": config.config.get("safety", {}).get("dry_run", False)
                            }
                        )
                        results.append({
                            "action": "restart",
                            "cluster_id": cluster_id,
                            "cluster_name": cluster_name,
                            "status": "error",
                            "message": str(e)
                        })
            else:
                diagnostics.append({
                    "issue": f"Found {len(failed_clusters)} failed clusters but auto_restart_failed_clusters is disabled",
                    "action_available": "Enable auto_restart_failed_clusters in config"
                })
            
            # Process running clusters - enable autotermination if not configured
            # AND also check all clusters with idle_cluster recommendations
            autotermination_enabled_count = 0
            

            # Get clusters that need autotermination (either RUNNING or have idle_cluster recommendations)
            clusters_to_process = []
            all_recs = list_recommendations()
            idle_cluster_recs = {rec.get("resource_id") for rec in all_recs if rec.get("type") == "idle_cluster"}
            
            # Add RUNNING clusters
            clusters_to_process.extend(running_clusters)
            
            # Add TERMINATED/STOPPING clusters that have idle_cluster recommendations
            for cluster in clusters:
                cluster_id = cluster.get("cluster_id")
                state = cluster.get("state", "UNKNOWN")
                cluster_name = cluster.get("cluster_name", "Unknown")
                
                # If it has an idle_cluster recommendation or is RUNNING, and not already in the list
                if (cluster_id in idle_cluster_recs or state == "RUNNING") and (cluster_id, cluster_name) not in clusters_to_process:
                    clusters_to_process.append((cluster_id, cluster_name))
            
            if config.is_feature_enabled("auto_terminate_idle_clusters"):
                desired_autotermination_minutes = (
                    config.get_rule("auto_terminate").get("idle_minutes")
                    or config.get_threshold("idle_timeout_minutes")
                    or 15
                )
                for cluster_id, cluster_name in clusters_to_process:
                    try:
                        # Get full cluster info to check autotermination status
                        cluster_info = databricks_client.get_cluster_info(cluster_id)
                        if cluster_info.get("status") == "success":
                            cluster = cluster_info.get("cluster", {})
                            autotermination_minutes = cluster.get("autotermination_minutes")
                            
                            # If autotermination is not configured or is 0, enable it
                            if not autotermination_minutes or autotermination_minutes == 0:
                                logger.info(
                                    f"Enabling autotermination for cluster {cluster_name} "
                                    f"({desired_autotermination_minutes} minutes)"
                                )
                                
                                # Check if dry-run mode
                                if config.is_dry_run():
                                    logger.info(
                                        f"[DRY-RUN] Would enable {desired_autotermination_minutes}-minute "
                                        f"autotermination for {cluster_name}"
                                    )
                                    autotermination_enabled_count += 1
                                    history.add_action(
                                        action_type="enable_autotermination",
                                        resource_id=cluster_id,
                                        resource_type="cluster",
                                        status="success",
                                        details={
                                            "cluster_name": cluster_name,
                                            "autotermination_minutes": desired_autotermination_minutes,
                                            "dry_run": True
                                        }
                                    )
                                    results.append({
                                        "action": "enable_autotermination",
                                        "cluster_id": cluster_id,
                                        "cluster_name": cluster_name,
                                        "status": "dry_run",
                                        "message": (
                                            f"[DRY-RUN] Would enable {desired_autotermination_minutes}-minute "
                                            f"autotermination for {cluster_name}"
                                        )
                                    })
                                else:
                                    # Actually enable autotermination
                                    result = databricks_client.update_cluster_config(
                                        cluster_id=cluster_id,
                                        autotermination_minutes=desired_autotermination_minutes
                                    )
                                    
                                    if result.get("status") == "success":
                                        actions_taken += 1
                                        autotermination_enabled_count += 1
                                        history.add_action(
                                            action_type="enable_autotermination",
                                            resource_id=cluster_id,
                                            resource_type="cluster",
                                            status="success",
                                            details={
                                                "cluster_name": cluster_name,
                                                "autotermination_minutes": desired_autotermination_minutes,
                                                "dry_run": False
                                            }
                                        )
                                        results.append({
                                            "action": "enable_autotermination",
                                            "cluster_id": cluster_id,
                                            "cluster_name": cluster_name,
                                            "status": "success",
                                            "message": (
                                                f"Successfully enabled {desired_autotermination_minutes}-minute "
                                                f"autotermination for {cluster_name}"
                                            )
                                        })
                                        logger.info(f"Successfully enabled autotermination for {cluster_name}")
                                        
                                        # Mark corresponding idle_cluster recommendations as APPLIED
                                        all_recs = list_recommendations()
                                        for rec in all_recs:
                                            if (rec.get("type") == "idle_cluster" and 
                                                rec.get("resource_id") == cluster_id and
                                                rec.get("status") == "PENDING"):
                                                update_status(rec.get("id"), "APPLIED", note=f"Autotermination enabled for cluster {cluster_name}")
                                                logger.info(f"Marked recommendation {rec.get('id')} as APPLIED")
                                    else:
                                        history.add_action(
                                            action_type="enable_autotermination",
                                            resource_id=cluster_id,
                                            resource_type="cluster",
                                            status="failed",
                                            details={
                                                "cluster_name": cluster_name,
                                                "error": result.get("error", "Unknown error"),
                                                "dry_run": False
                                            }
                                        )
                                        results.append({
                                            "action": "enable_autotermination",
                                            "cluster_id": cluster_id,
                                            "cluster_name": cluster_name,
                                            "status": "failed",
                                            "message": result.get("error", "Failed to enable autotermination")
                                        })
                    except Exception as e:
                        logger.error(f"Error checking/enabling autotermination for {cluster_name}: {e}")
                        results.append({
                            "action": "enable_autotermination",
                            "cluster_id": cluster_id,
                            "cluster_name": cluster_name,
                            "status": "error",
                            "message": str(e)
                        })
            else:
                diagnostics.append({
                    "issue": f"Found {len(running_clusters)} running clusters but auto_terminate_idle_clusters is disabled",
                    "action_available": "Enable auto_terminate_idle_clusters in config"
                })
            
            # Process stuck pending jobs - automatically cancel them
            stuck_jobs_cancelled = 0
            PENDING_THRESHOLD_MINUTES = 5
            try:
                jobs = databricks_client.get_all_jobs()
                current_time_ms = int(time.time() * 1000)
                
                for job in jobs:
                    job_id = job.get("job_id")
                    job_name = job.get("settings", {}).get("name") or job.get("job_name", "Unknown")
                    
                    try:
                        # Get recent runs for this job
                        runs_response = databricks_client.get_job_runs(job_id, limit=10)
                        if isinstance(runs_response, dict):
                            if runs_response.get("status") != "success":
                                continue
                            runs = runs_response.get("runs", [])
                        else:
                            runs = runs_response or []
                        
                        if not runs:
                            continue
                        
                        # Look for runs stuck in PENDING state
                        for run in runs:
                            state = run.get("state", {})
                            life_cycle_state = state.get("life_cycle_state", "")
                            
                            # Only cancel if stuck in PENDING
                            if life_cycle_state == "PENDING":
                                run_id = run.get("run_id")
                                start_time = run.get("start_time")
                                
                                if not start_time:
                                    continue
                                
                                # Calculate how long it's been pending
                                pending_duration_ms = current_time_ms - start_time
                                pending_duration_minutes = pending_duration_ms / 1000 / 60
                                
                                # If pending for more than threshold, cancel it
                                if pending_duration_minutes > PENDING_THRESHOLD_MINUTES:
                                    logger.info(f"Cancelling stuck PENDING job run {run_id} for job {job_name} (pending for {pending_duration_minutes:.1f} minutes)")
                                    
                                    if config.is_dry_run():
                                        logger.info(f"[DRY-RUN] Would cancel stuck job run {run_id}")
                                        stuck_jobs_cancelled += 1
                                        history.add_action(
                                            action_type="cancel_stuck_job",
                                            resource_id=str(run_id),
                                            resource_type="job",
                                            status="success",
                                            details={
                                                "job_name": job_name,
                                                "job_id": job_id,
                                                "run_id": run_id,
                                                "pending_minutes": pending_duration_minutes,
                                                "dry_run": True
                                            }
                                        )
                                        results.append({
                                            "action": "cancel_stuck_job",
                                            "job_id": job_id,
                                            "job_name": job_name,
                                            "run_id": run_id,
                                            "status": "dry_run",
                                            "message": f"[DRY-RUN] Would cancel run {run_id} stuck for {pending_duration_minutes:.1f} minutes"
                                        })
                                    else:
                                        # Actually cancel the run
                                        cancel_result = databricks_client.cancel_job_run(run_id)
                                        
                                        if cancel_result.get("status") == "success":
                                            actions_taken += 1
                                            stuck_jobs_cancelled += 1
                                            history.add_action(
                                                action_type="cancel_stuck_job",
                                                resource_id=str(run_id),
                                                resource_type="job",
                                                status="success",
                                                details={
                                                    "job_name": job_name,
                                                    "job_id": job_id,
                                                    "run_id": run_id,
                                                    "pending_minutes": pending_duration_minutes,
                                                    "dry_run": False
                                                }
                                            )
                                            results.append({
                                                "action": "cancel_stuck_job",
                                                "job_id": job_id,
                                                "job_name": job_name,
                                                "run_id": run_id,
                                                "status": "success",
                                                "message": f"Cancelled run {run_id} stuck for {pending_duration_minutes:.1f} minutes"
                                            })
                                            logger.info(f"Successfully cancelled stuck job run {run_id}")
                                            
                                            # Mark corresponding stuck_pending_job recommendations as APPLIED
                                            all_recs = list_recommendations()
                                            for rec in all_recs:
                                                if (rec.get("type") == "stuck_pending_job" and 
                                                    rec.get("resource_id") == str(run_id) and
                                                    rec.get("status") == "PENDING"):
                                                    update_status(rec.get("id"), "APPLIED", note=f"Job run {run_id} was automatically cancelled as it was stuck in PENDING state")
                                                    logger.info(f"Marked recommendation {rec.get('id')} as APPLIED")
                                        else:
                                            history.add_action(
                                                action_type="cancel_stuck_job",
                                                resource_id=str(run_id),
                                                resource_type="job",
                                                status="failed",
                                                details={
                                                    "job_name": job_name,
                                                    "job_id": job_id,
                                                    "run_id": run_id,
                                                    "error": cancel_result.get("error", "Unknown error"),
                                                    "dry_run": False
                                                }
                                            )
                                            results.append({
                                                "action": "cancel_stuck_job",
                                                "job_id": job_id,
                                                "job_name": job_name,
                                                "run_id": run_id,
                                                "status": "failed",
                                                "message": cancel_result.get("error", "Failed to cancel job run")
                                            })
                                    
                                    # Only cancel one stuck run per job
                                    break
                    
                    except Exception as job_error:
                        logger.debug(f"Could not check job {job_id} for stuck runs: {job_error}")
                        continue
            
            except Exception as jobs_error:
                logger.error(f"Error checking for stuck pending jobs: {str(jobs_error)}")

            # Process long running jobs - automatically cancel them
            long_running_jobs_cancelled = 0
            long_running_threshold_minutes = config.get_threshold("long_running_job_minutes") or 30
            if config.is_feature_enabled("auto_cancel_long_running_jobs"):
                try:
                    jobs = databricks_client.get_all_jobs()
                    current_time_ms = int(time.time() * 1000)

                    for job in jobs:
                        job_id = job.get("job_id")
                        job_name = job.get("settings", {}).get("name") or job.get("job_name", "Unknown")

                        try:
                            runs_response = databricks_client.get_job_runs(job_id, limit=10)
                            if isinstance(runs_response, dict):
                                if runs_response.get("status") != "success":
                                    continue
                                runs = runs_response.get("runs", [])
                            else:
                                runs = runs_response or []

                            if not runs:
                                continue

                            for run in runs:
                                state = run.get("state", {})
                                life_cycle_state = state.get("life_cycle_state", "")

                                if life_cycle_state == "RUNNING":
                                    run_id = run.get("run_id")
                                    start_time = run.get("start_time")

                                    if not start_time:
                                        continue

                                    running_duration_ms = current_time_ms - start_time
                                    running_duration_minutes = running_duration_ms / 1000 / 60

                                    if running_duration_minutes > long_running_threshold_minutes:
                                        logger.info(
                                            f"Cancelling long running job run {run_id} for job {job_name} "
                                            f"(running for {running_duration_minutes:.1f} minutes)"
                                        )

                                        if config.is_dry_run():
                                            logger.info(f"[DRY-RUN] Would cancel long running job run {run_id}")
                                            long_running_jobs_cancelled += 1
                                            history.add_action(
                                                action_type="cancel_long_running_job",
                                                resource_id=str(run_id),
                                                resource_type="job",
                                                status="success",
                                                details={
                                                    "job_name": job_name,
                                                    "job_id": job_id,
                                                    "run_id": run_id,
                                                    "running_minutes": running_duration_minutes,
                                                    "threshold_minutes": long_running_threshold_minutes,
                                                    "dry_run": True
                                                }
                                            )
                                            results.append({
                                                "action": "cancel_long_running_job",
                                                "job_id": job_id,
                                                "job_name": job_name,
                                                "run_id": run_id,
                                                "status": "dry_run",
                                                "message": (
                                                    f"[DRY-RUN] Would cancel run {run_id} running for "
                                                    f"{running_duration_minutes:.1f} minutes"
                                                )
                                            })
                                        else:
                                            cancel_result = databricks_client.cancel_job_run(run_id)

                                            if cancel_result.get("status") == "success":
                                                actions_taken += 1
                                                long_running_jobs_cancelled += 1
                                                history.add_action(
                                                    action_type="cancel_long_running_job",
                                                    resource_id=str(run_id),
                                                    resource_type="job",
                                                    status="success",
                                                    details={
                                                        "job_name": job_name,
                                                        "job_id": job_id,
                                                        "run_id": run_id,
                                                        "running_minutes": running_duration_minutes,
                                                        "threshold_minutes": long_running_threshold_minutes,
                                                        "dry_run": False
                                                    }
                                                )
                                                results.append({
                                                    "action": "cancel_long_running_job",
                                                    "job_id": job_id,
                                                    "job_name": job_name,
                                                    "run_id": run_id,
                                                    "status": "success",
                                                    "message": (
                                                        f"Cancelled run {run_id} running for "
                                                        f"{running_duration_minutes:.1f} minutes"
                                                    )
                                                })
                                                logger.info(f"Successfully cancelled long running job run {run_id}")

                                                all_recs = list_recommendations()
                                                for rec in all_recs:
                                                    rec_type = rec.get("type")
                                                    rec_details = rec.get("details", {}) or {}
                                                    rec_run_id = rec_details.get("run_id")
                                                    rec_params = (rec.get("action") or {}).get("params", {})
                                                    rec_action_run_id = rec_params.get("run_id")
                                                    if (
                                                        rec_type == "long_running_job"
                                                        and rec.get("status") == "PENDING"
                                                        and (rec_run_id == run_id or rec_action_run_id == run_id)
                                                    ):
                                                        update_status(
                                                            rec.get("id"),
                                                            "APPLIED",
                                                            note=(
                                                                f"Job run {run_id} was cancelled after "
                                                                f"{running_duration_minutes:.1f} minutes"
                                                            )
                                                        )
                                                        logger.info(f"Marked recommendation {rec.get('id')} as APPLIED")
                                            else:
                                                history.add_action(
                                                    action_type="cancel_long_running_job",
                                                    resource_id=str(run_id),
                                                    resource_type="job",
                                                    status="failed",
                                                    details={
                                                        "job_name": job_name,
                                                        "job_id": job_id,
                                                        "run_id": run_id,
                                                        "error": cancel_result.get("error", "Unknown error"),
                                                        "dry_run": False
                                                    }
                                                )
                                                results.append({
                                                    "action": "cancel_long_running_job",
                                                    "job_id": job_id,
                                                    "job_name": job_name,
                                                    "run_id": run_id,
                                                    "status": "failed",
                                                    "message": cancel_result.get("error", "Failed to cancel job run")
                                                })

                                        break

                        except Exception as job_error:
                            logger.debug(f"Could not check job {job_id} for long running runs: {job_error}")
                            continue

                except Exception as jobs_error:
                    logger.error(f"Error checking for long running jobs: {str(jobs_error)}")
            else:
                diagnostics.append({
                    "issue": "Long running job cancellation is disabled",
                    "action_available": "Enable auto_cancel_long_running_jobs in config"
                })
            
            # Process execution errors - automatically restart failed jobs
            failed_jobs_restarted = 0
            try:
                jobs = databricks_client.get_all_jobs()
                execution_error_recs = generate_execution_error_recommendations(jobs)
                if execution_error_recs:
                    add_recommendations(execution_error_recs)
                
                for rec in execution_error_recs:
                    try:
                        action = rec.get("action", {})
                        if not isinstance(action, dict):
                            continue
                        
                        action_type = action.get("type")
                        job_id = action.get("params", {}).get("job_id") or rec.get("resource_id")
                        failed_run_id = action.get("params", {}).get("run_id")
                        error_message = action.get("params", {}).get("error_message", "Execution error")
                        
                        if action_type != "restart_job_run" or not job_id:
                            continue
                        
                        job_name = rec.get("resource_name", f"Job {job_id}")
                        
                        logger.info(f"Restarting failed job {job_name} (job_id: {job_id}, failed_run: {failed_run_id})")
                        
                        if config.is_dry_run():
                            logger.info(f"[DRY-RUN] Would restart job {job_name}")
                            failed_jobs_restarted += 1
                            history.add_action(
                                action_type="restart_failed_job",
                                resource_id=str(job_id),
                                resource_type="job",
                                status="success",
                                details={
                                    "job_name": job_name,
                                    "job_id": job_id,
                                    "failed_run_id": failed_run_id,
                                    "error_message": error_message[:200],
                                    "dry_run": True
                                }
                            )
                            results.append({
                                "action": "restart_failed_job",
                                "job_id": job_id,
                                "job_name": job_name,
                                "failed_run_id": failed_run_id,
                                "status": "dry_run",
                                "message": f"[DRY-RUN] Would restart job {job_name} (failed run: {failed_run_id})"
                            })
                            update_status(rec.get("id"), "APPLIED", note="[DRY-RUN] Job would have been restarted")
                        else:
                            # Actually submit new run
                            submit_result = databricks_client.submit_job_run(job_id)
                            
                            if submit_result.get("status") == "success":
                                actions_taken += 1
                                failed_jobs_restarted += 1
                                new_run_id = submit_result.get("run_id")
                                
                                history.add_action(
                                    action_type="restart_failed_job",
                                    resource_id=str(job_id),
                                    resource_type="job",
                                    status="success",
                                    details={
                                        "job_name": job_name,
                                        "job_id": job_id,
                                        "new_run_id": new_run_id,
                                        "failed_run_id": failed_run_id,
                                        "error_message": error_message[:200],
                                        "dry_run": False
                                    }
                                )
                                results.append({
                                    "action": "restart_failed_job",
                                    "job_id": job_id,
                                    "job_name": job_name,
                                    "new_run_id": new_run_id,
                                    "failed_run_id": failed_run_id,
                                    "status": "success",
                                    "message": f"Restarted job {job_name} (new run: {new_run_id}, failed run: {failed_run_id})"
                                })
                                logger.info(f"Successfully restarted failed job {job_name}, new run ID: {new_run_id}")
                                
                                # Mark recommendation as APPLIED
                                update_status(rec.get("id"), "APPLIED", note=f"Job rerun submitted (new run ID: {new_run_id})")
                            else:
                                history.add_action(
                                    action_type="restart_failed_job",
                                    resource_id=str(job_id),
                                    resource_type="job",
                                    status="failed",
                                    details={
                                        "job_name": job_name,
                                        "job_id": job_id,
                                        "failed_run_id": failed_run_id,
                                        "error": submit_result.get("error", "Unknown error"),
                                        "dry_run": False
                                    }
                                )
                                results.append({
                                    "action": "restart_failed_job",
                                    "job_id": job_id,
                                    "job_name": job_name,
                                    "status": "failed",
                                    "message": submit_result.get("error", "Failed to restart job")
                                })
                                
                    except Exception as job_error:
                        logger.debug(f"Could not restart job for execution error: {job_error}")
                        continue
                        
            except Exception as err:
                logger.error(f"Error processing execution error recommendations: {str(err)}")
            
            # Summary
            summary = {
                "scanned_clusters": len(clusters),
                "running_clusters": len(running_clusters),
                "failed_clusters": len(failed_clusters),
                "autotermination_enabled": autotermination_enabled_count,
                "stuck_jobs_cancelled": stuck_jobs_cancelled,
                "long_running_jobs_cancelled": long_running_jobs_cancelled,
                "failed_jobs_restarted": failed_jobs_restarted,
                "actions_taken": actions_taken,
                "actions_available": {
                    "auto_restart": len(failed_clusters) if config.is_feature_enabled("auto_restart_failed_clusters") else 0,
                    "auto_terminate": autotermination_enabled_count if config.is_feature_enabled("auto_terminate_idle_clusters") else 0,
                    "cancel_stuck_jobs": stuck_jobs_cancelled,
                    "cancel_long_running_jobs": long_running_jobs_cancelled if config.is_feature_enabled("auto_cancel_long_running_jobs") else 0,
                    "restart_failed_jobs": failed_jobs_restarted
                }
            }
            
            response = {
                "success": True,
                "summary": summary,
                "results": results,
                "diagnostics": diagnostics,
                "timestamp": get_ist_time().isoformat()
            }
            
            logger.info(f"Self-healing run completed: {summary}")
            return jsonify(response), 200
        
        except Exception as cluster_error:
            logger.error(f"Error during cluster analysis: {str(cluster_error)}", exc_info=True)
            return jsonify({
                "success": False,
                "error": f"Error during healing: {str(cluster_error)}",
                "actions_taken": 0
            }), 500
    
    except Exception as e:
        logger.error(f"Error running self-healing: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e),
            "actions_taken": 0
        }), 500


@app.route("/api/self-healing/history", methods=["GET"])
def get_healing_history():
    """Get history of self-healing actions."""
    try:
        from self_healing_config import get_history
        
        history = get_history()
        limit = request.args.get("limit", 50, type=int)
        
        recent = history.get_recent_actions(limit=limit)
        stats = history.get_stats()
        
        return jsonify({
            "success": True,
            "history": recent,
            "stats": stats
        }), 200
    
    except Exception as e:
        logger.error(f"Error retrieving healing history: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/self-healing/stats", methods=["GET"])
def get_self_healing_stats():
    """Get self-healing statistics and metrics."""
    try:
        from self_healing_config import get_config, get_history
        from health_monitor import run_health_check
        
        config = get_config()
        history = get_history()
        health = run_health_check()

        # Get all clusters to check their states
        try:
            all_clusters = databricks_client.get_all_clusters()
            terminated_cluster_ids = {
                c.get("cluster_id") 
                for c in all_clusters 
                if c.get("state", "").upper() in {"TERMINATED", "TERMINATING"}
            }
        except Exception as e:
            logger.warning(f"Failed to fetch cluster states for filtering: {str(e)}")
            terminated_cluster_ids = set()

        # Count only auto-healable recommendations (not general optimizations)
        actionable_recs_by_key = {}
        recommendations = list_recommendations()
        auto_healable_types = {"stuck_pending_job", "idle_cluster", "execution_error", "long_running_job"}
        
        for rec in recommendations:
            rec_type = (rec.get("type") or "").lower()
            
            # Only count auto-healable types
            if rec_type not in auto_healable_types:
                continue
            
            # Only count recommendations that are actionable (PENDING or APPROVED)
            # Exclude APPLIED, FAILED, and REJECTED
            status = rec.get("status")
            if status not in ("PENDING", "APPROVED"):
                continue
            
            # Skip recommendations for TERMINATED clusters
            if rec.get("resource_type") == "cluster":
                cluster_id = rec.get("resource_id")
                if cluster_id in terminated_cluster_ids:
                    logger.debug(f"Skipping recommendation for TERMINATED cluster: {cluster_id}")
                    continue
            
            # Only count recommendations that have actions (or cost_leak/idle_cluster types)
            action = rec.get("action")
            if action is None or action == "":
                # Allow idle_cluster and cost_leak types even without explicit action
                if rec_type not in {"idle_cluster"} and rec.get("type") != "cost_leak":
                    continue
            
            # Create a unique key for deduplication
            resource_id = rec.get("resource_id") or rec.get("resource_name")
            message = rec.get("title") or rec.get("description") or "Issue detected"
            timestamp = rec.get("updated_at") or rec.get("created_at")
            try:
                timestamp_dt = datetime.fromisoformat(timestamp) if timestamp else datetime.min
            except (TypeError, ValueError):
                timestamp_dt = datetime.min
            
            key = f"{rec_type}|{resource_id}|{message}"
            existing = actionable_recs_by_key.get(key)
            if not existing or timestamp_dt > existing:
                actionable_recs_by_key[key] = timestamp_dt

        actionable_recommendations_count = len(actionable_recs_by_key)
        
        return jsonify({
            "success": True,
            "enabled": config.is_enabled(),
            "dry_run": config.is_dry_run(),
            "health_summary": health.get("summary", {}),
            "healing_stats": history.get_stats(),
            "auto_healable_issues": actionable_recommendations_count
        }), 200
    
    except Exception as e:
        logger.error(f"Error retrieving self-healing stats: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


setup_logging(logger)


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=settings.backend_port,
        debug=False
    )
