"""
Health Monitor Module
Continuously monitors cluster health and detects issues
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from databricks_client import DatabricksClient
from self_healing_config import get_config, get_history

logger = logging.getLogger(__name__)

class HealthMonitor:
    """Monitor cluster health and detect issues"""
    
    def __init__(self, databricks_client: DatabricksClient):
        self.client = databricks_client
        self.config = get_config()
        self.history = get_history()
    
    def check_cluster_health(self, cluster_id: str) -> Dict[str, Any]:
        """Check health of a specific cluster"""
        try:
            cluster_response = self.client.get_cluster_info(cluster_id)
            cluster = cluster_response.get("cluster", {}) if cluster_response.get("status") == "success" else {}
            
            health = {
                "cluster_id": cluster_id,
                "cluster_name": cluster.get("cluster_name"),
                "state": cluster.get("state"),
                "is_healthy": True,
                "issues": [],
                "recommendations": [],
                "timestamp": datetime.now().isoformat()
            }
            
            # Check for failure states
            if cluster.get("state") in ["FAILED", "ERROR", "TERMINATING"]:
                health["is_healthy"] = False
                health["issues"].append({
                    "type": "cluster_failed",
                    "severity": "critical",
                    "message": f"Cluster in {cluster.get('state')} state",
                    "auto_healable": True
                })
            
            # Check for idle clusters
            if self._is_cluster_idle(cluster):
                health["issues"].append({
                    "type": "cluster_idle",
                    "severity": "warning",
                    "message": "Cluster is idle and consuming resources",
                    "auto_healable": True
                })
            
            # Check for resource utilization issues
            utilization_issues = self._check_resource_utilization(cluster)
            if utilization_issues:
                health["issues"].extend(utilization_issues)
            
            return health
            
        except Exception as e:
            logger.error(f"Error checking cluster health for {cluster_id}: {e}")
            return {
                "cluster_id": cluster_id,
                "is_healthy": False,
                "issues": [{"type": "check_failed", "message": str(e)}],
                "timestamp": datetime.now().isoformat()
            }
    
    def check_all_clusters(self) -> List[Dict[str, Any]]:
        """Check health of all active clusters (excludes terminated clusters)"""
        try:
            all_clusters = self.client.get_all_clusters()
            # Filter out terminated clusters
            clusters = [c for c in all_clusters if c.get("state", "").upper() not in {"TERMINATED"}]
            logging.info(f"Health check: analyzing {len(clusters)} active clusters (filtered from {len(all_clusters)} total)")
            health_reports = []
            
            for cluster in clusters:
                cluster_id = cluster.get("cluster_id")
                cluster_name = cluster.get("cluster_name", "Unknown")
                state = cluster.get("state", "UNKNOWN")
                
                is_healthy = state not in ["FAILED", "ERROR", "TERMINATING"]
                issues = []
                
                if state in ["FAILED", "ERROR", "TERMINATING"]:
                    issues.append({
                        "type": "cluster_failed",
                        "severity": "critical",
                        "message": f"Cluster in {state} state",
                        "auto_healable": True
                    })
                
                # Check for idle clusters (RUNNING clusters that haven't been used recently)
                if state == "RUNNING" and self._is_cluster_idle(cluster):
                    issues.append({
                        "type": "cluster_idle",
                        "severity": "warning",
                        "message": "Cluster is idle and consuming resources",
                        "auto_healable": True
                    })
                    is_healthy = False
                
                health = {
                    "cluster_id": cluster_id,
                    "cluster_name": cluster_name,
                    "state": state,
                    "is_healthy": is_healthy,
                    "issues": issues,
                    "timestamp": datetime.now().isoformat()
                }
                health_reports.append(health)
            
            return health_reports
            
        except Exception as e:
            logger.error(f"Error checking all clusters: {e}")
            return []
    
    def _is_cluster_idle(self, cluster: Dict[str, Any]) -> bool:
        """Check if cluster is idle"""
        state = cluster.get("state")
        
        # Only running clusters can be idle
        if state != "RUNNING":
            return False
        
        # Check last activity time
        last_activity = cluster.get("last_activity_time")
        if last_activity:
            idle_threshold = self.config.get_threshold("idle_timeout_minutes")
            last_activity_dt = datetime.fromtimestamp(last_activity / 1000)
            idle_time = datetime.now() - last_activity_dt
            
            if idle_time > timedelta(minutes=idle_threshold):
                return True
        
        return False
    
    def _check_resource_utilization(self, cluster: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for resource utilization issues"""
        issues = []
        
        # Get cluster metrics (placeholder - would need actual metrics API)
        # In production, this would integrate with Databricks metrics/monitoring
        
        return issues
    
    def get_unhealthy_clusters(self) -> List[Dict[str, Any]]:
        """Get all unhealthy clusters"""
        health_reports = self.check_all_clusters()
        return [report for report in health_reports if not report.get("is_healthy", True)]
    
    def get_auto_healable_issues(self) -> List[Dict[str, Any]]:
        """Get issues that can be auto-healed (detected regardless of enabled flag)"""
        unhealthy = self.get_unhealthy_clusters()
        auto_healable = []
        
        for cluster_health in unhealthy:
            cluster_id = cluster_health.get("cluster_id")
            cluster_name = cluster_health.get("cluster_name")
            
            # Get auto-healable issues from this cluster
            # Include all auto-healable issues detected, regardless of whether healing is enabled
            # The enabled flag only controls whether actions are taken, not whether we detect issues
            for issue in cluster_health.get("issues", []):
                if issue.get("auto_healable", False):
                    auto_healable.append({
                        "cluster_id": cluster_id,
                        "cluster_name": cluster_name,
                        "issue_type": issue.get("type"),
                        "issue": issue,
                        "timestamp": cluster_health.get("timestamp"),
                        "can_heal": self.config.can_auto_heal_cluster(cluster_id)
                    })
        
        return auto_healable
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get overall health summary"""
        health_reports = self.check_all_clusters()
        
        total = len(health_reports)
        healthy = len([r for r in health_reports if r.get("is_healthy", True)])
        unhealthy = total - healthy
        
        issues_by_type = {}
        for report in health_reports:
            for issue in report.get("issues", []):
                issue_type = issue.get("type", "unknown")
                issues_by_type[issue_type] = issues_by_type.get(issue_type, 0) + 1
        
        auto_healable = len(self.get_auto_healable_issues())
        
        return {
            "total_clusters": total,
            "healthy": healthy,
            "unhealthy": unhealthy,
            "health_percentage": (healthy / total * 100) if total > 0 else 100,
            "issues_by_type": issues_by_type,
            "auto_healable_issues": auto_healable,
            "timestamp": datetime.now().isoformat()
        }


class ProactiveHealthCheck:
    """Proactive health checking and prediction"""
    
    def __init__(self, databricks_client: DatabricksClient):
        self.client = databricks_client
        self.config = get_config()
    
    def predict_failures(self) -> List[Dict[str, Any]]:
        """Predict potential failures based on patterns"""
        predictions = []
        
        # This would use ML/patterns to predict issues
        # For now, use simple heuristics
        
        try:
            all_clusters_list = self.client.get_all_clusters()
            # Filter out terminated clusters
            clusters_list = [c for c in all_clusters_list if c.get("state", "").upper() not in {"TERMINATED"}]
            clusters = {"clusters": clusters_list}
            
            for cluster in clusters.get("clusters", []):
                # Check for clusters that restart frequently
                cluster_id = cluster.get("cluster_id")
                recent_actions = get_history().get_actions_for_resource(cluster_id)
                
                restart_count = len([a for a in recent_actions 
                                   if a.get("action_type") == "auto_restart"])
                
                if restart_count >= 2:
                    predictions.append({
                        "cluster_id": cluster_id,
                        "cluster_name": cluster.get("cluster_name"),
                        "prediction": "likely_to_fail",
                        "confidence": "medium",
                        "reason": f"Restarted {restart_count} times recently",
                        "recommendation": "Review cluster configuration and logs"
                    })
        
        except Exception as e:
            logger.error(f"Error predicting failures: {e}")
        
        return predictions
    
    def check_cost_anomalies(self) -> List[Dict[str, Any]]:
        """Detect cost anomalies and spikes"""
        anomalies = []
        
        # Placeholder for cost anomaly detection
        # Would integrate with cost tracking and baseline comparison
        
        return anomalies


def run_health_check() -> Dict[str, Any]:
    """Run a complete health check"""
    from databricks_client import get_databricks_client
    
    client = get_databricks_client()
    monitor = HealthMonitor(client)
    proactive = ProactiveHealthCheck(client)
    
    results = {
        "summary": monitor.get_health_summary(),
        "unhealthy_clusters": monitor.get_unhealthy_clusters(),
        "auto_healable": monitor.get_auto_healable_issues(),
        "predictions": proactive.predict_failures(),
        "timestamp": datetime.now().isoformat()
    }
    
    return results
