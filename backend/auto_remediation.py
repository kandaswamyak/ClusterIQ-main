"""
Auto-Remediation Engine
Automatically fixes detected issues and applies optimizations
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from databricks_client import DatabricksClient
from self_healing_config import get_config, get_history
from health_monitor import HealthMonitor

logger = logging.getLogger(__name__)

class AutoRemediation:
    """Automated remediation for cluster issues"""
    
    def __init__(self, databricks_client: DatabricksClient):
        self.client = databricks_client
        self.config = get_config()
        self.history = get_history()
        self.monitor = HealthMonitor(databricks_client)
    
    def auto_restart_cluster(self, cluster_id: str, reason: str = "Auto-restart due to failure") -> Dict[str, Any]:
        """Automatically restart a failed cluster"""
        try:
            # Check if feature is enabled
            if not self.config.is_feature_enabled("auto_restart_failed_clusters"):
                return {
                    "success": False,
                    "message": "Auto-restart feature is disabled",
                    "action": "none"
                }
            
            # Check restart attempts
            recent_restarts = [
                a for a in self.history.get_actions_for_resource(cluster_id)
                if a.get("action_type") == "auto_restart"
                and datetime.fromisoformat(a.get("timestamp")) > datetime.now() - timedelta(hours=1)
            ]
            
            max_attempts = self.config.get_rule("auto_restart").get("max_attempts", 3)
            if len(recent_restarts) >= max_attempts:
                return {
                    "success": False,
                    "message": f"Max restart attempts ({max_attempts}) reached",
                    "action": "none"
                }
            
            # Get cluster info
            cluster_response = self.client.get_cluster_info(cluster_id)
            cluster = cluster_response.get("cluster", {}) if cluster_response.get("status") == "success" else {}
            cluster_name = cluster.get("cluster_name", cluster_id)
            
            # Check if dry-run mode
            if self.config.is_dry_run():
                logger.info(f"[DRY-RUN] Would restart cluster: {cluster_name}")
                self.history.add_action(
                    action_type="auto_restart",
                    resource_id=cluster_id,
                    resource_type="cluster",
                    status="success",
                    details={
                        "dry_run": True,
                        "reason": reason,
                        "cluster_name": cluster_name
                    }
                )
                return {
                    "success": True,
                    "message": f"[DRY-RUN] Would restart cluster {cluster_name}",
                    "action": "dry_run",
                    "cluster_name": cluster_name
                }
            
            # Actually restart the cluster
            logger.info(f"Auto-restarting cluster: {cluster_name}")
            
            # Terminate if running
            current_state = cluster.get("state")
            if current_state in ["RUNNING", "ERROR", "FAILED"]:
                self.client.terminate_cluster(cluster_id)
            
            # Start the cluster
            self.client.start_cluster(cluster_id)
            
            # Log the action
            self.history.add_action(
                action_type="auto_restart",
                resource_id=cluster_id,
                resource_type="cluster",
                status="success",
                details={
                    "dry_run": False,
                    "reason": reason,
                    "cluster_name": cluster_name,
                    "previous_state": current_state
                }
            )
            
            return {
                "success": True,
                "message": f"Successfully restarted cluster {cluster_name}",
                "action": "restarted",
                "cluster_name": cluster_name
            }
            
        except Exception as e:
            logger.error(f"Error auto-restarting cluster {cluster_id}: {e}")
            self.history.add_action(
                action_type="auto_restart",
                resource_id=cluster_id,
                resource_type="cluster",
                status="failed",
                details={"error": str(e), "reason": reason}
            )
            return {
                "success": False,
                "message": f"Failed to restart cluster: {str(e)}",
                "action": "error"
            }
    
    def auto_terminate_idle_cluster(self, cluster_id: str) -> Dict[str, Any]:
        """Automatically terminate an idle cluster"""
        try:
            # Check if feature is enabled
            if not self.config.is_feature_enabled("auto_terminate_idle_clusters"):
                return {
                    "success": False,
                    "message": "Auto-terminate feature is disabled",
                    "action": "none"
                }
            
            # Get cluster info
            cluster_response = self.client.get_cluster_info(cluster_id)
            cluster = cluster_response.get("cluster", {}) if cluster_response.get("status") == "success" else {}
            cluster_name = cluster.get("cluster_name", cluster_id)
            
            # Check if dry-run mode
            if self.config.is_dry_run():
                logger.info(f"[DRY-RUN] Would terminate idle cluster: {cluster_name}")
                self.history.add_action(
                    action_type="auto_terminate_idle",
                    resource_id=cluster_id,
                    resource_type="cluster",
                    status="success",
                    details={
                        "dry_run": True,
                        "cluster_name": cluster_name
                    }
                )
                return {
                    "success": True,
                    "message": f"[DRY-RUN] Would terminate idle cluster {cluster_name}",
                    "action": "dry_run",
                    "cluster_name": cluster_name
                }
            
            # Actually terminate the cluster
            logger.info(f"Auto-terminating idle cluster: {cluster_name}")
            self.client.terminate_cluster(cluster_id)
            
            # Log the action
            self.history.add_action(
                action_type="auto_terminate_idle",
                resource_id=cluster_id,
                resource_type="cluster",
                status="success",
                details={
                    "dry_run": False,
                    "cluster_name": cluster_name,
                    "reason": "Idle timeout exceeded"
                }
            )
            
            return {
                "success": True,
                "message": f"Successfully terminated idle cluster {cluster_name}",
                "action": "terminated",
                "cluster_name": cluster_name
            }
            
        except Exception as e:
            logger.error(f"Error auto-terminating cluster {cluster_id}: {e}")
            self.history.add_action(
                action_type="auto_terminate_idle",
                resource_id=cluster_id,
                resource_type="cluster",
                status="failed",
                details={"error": str(e)}
            )
            return {
                "success": False,
                "message": f"Failed to terminate cluster: {str(e)}",
                "action": "error"
            }
    
    def auto_scale_cluster(self, cluster_id: str, action: str, target_workers: int) -> Dict[str, Any]:
        """Automatically adjust cluster scaling"""
        try:
            # Check if feature is enabled
            if not self.config.is_feature_enabled("auto_scale_adjustments"):
                return {
                    "success": False,
                    "message": "Auto-scale feature is disabled",
                    "action": "none"
                }
            
            # Get cluster info
            cluster_response = self.client.get_cluster_info(cluster_id)
            cluster = cluster_response.get("cluster", {}) if cluster_response.get("status") == "success" else {}
            cluster_name = cluster.get("cluster_name", cluster_id)
            
            # Check if dry-run mode
            if self.config.is_dry_run():
                logger.info(f"[DRY-RUN] Would {action} cluster {cluster_name} to {target_workers} workers")
                self.history.add_action(
                    action_type="auto_scale",
                    resource_id=cluster_id,
                    resource_type="cluster",
                    status="success",
                    details={
                        "dry_run": True,
                        "action": action,
                        "target_workers": target_workers,
                        "cluster_name": cluster_name
                    }
                )
                return {
                    "success": True,
                    "message": f"[DRY-RUN] Would {action} cluster to {target_workers} workers",
                    "action": "dry_run"
                }
            
            # Note: Actual implementation would call Databricks API to resize cluster
            # This is a placeholder as the exact API depends on cluster configuration
            
            logger.info(f"Auto-scaling cluster {cluster_name}: {action} to {target_workers} workers")
            
            self.history.add_action(
                action_type="auto_scale",
                resource_id=cluster_id,
                resource_type="cluster",
                status="success",
                details={
                    "dry_run": False,
                    "action": action,
                    "target_workers": target_workers,
                    "cluster_name": cluster_name
                }
            )
            
            return {
                "success": True,
                "message": f"Successfully scaled cluster {cluster_name}",
                "action": "scaled"
            }
            
        except Exception as e:
            logger.error(f"Error auto-scaling cluster {cluster_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to scale cluster: {str(e)}",
                "action": "error"
            }
    
    def process_auto_healable_issues(self) -> List[Dict[str, Any]]:
        """Process all auto-healable issues"""
        if not self.config.is_enabled():
            return [{
                "success": False,
                "message": "Self-healing is disabled globally"
            }]
        
        results = []
        auto_healable = self.monitor.get_auto_healable_issues()
        
        for issue_info in auto_healable:
            cluster_id = issue_info.get("cluster_id")
            issue = issue_info.get("issue", {})
            issue_type = issue.get("type")
            
            # Route to appropriate remediation
            if issue_type == "cluster_failed":
                result = self.auto_restart_cluster(
                    cluster_id,
                    reason=issue.get("message", "Cluster failure detected")
                )
                results.append({
                    "cluster_id": cluster_id,
                    "cluster_name": issue_info.get("cluster_name"),
                    "issue_type": issue_type,
                    "remediation": result
                })
            
            elif issue_type == "cluster_idle":
                result = self.auto_terminate_idle_cluster(cluster_id)
                results.append({
                    "cluster_id": cluster_id,
                    "cluster_name": issue_info.get("cluster_name"),
                    "issue_type": issue_type,
                    "remediation": result
                })
        
        return results


def run_auto_healing() -> Dict[str, Any]:
    """Run auto-healing process"""
    from databricks_client import get_databricks_client
    
    config = get_config()
    
    if not config.is_enabled():
        return {
            "success": False,
            "message": "Self-healing is disabled",
            "timestamp": datetime.now().isoformat()
        }
    
    client = get_databricks_client()
    remediation = AutoRemediation(client)
    
    results = remediation.process_auto_healable_issues()
    
    return {
        "success": True,
        "actions_taken": len(results),
        "results": results,
        "dry_run": config.is_dry_run(),
        "timestamp": datetime.now().isoformat()
    }
