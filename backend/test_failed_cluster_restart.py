#!/usr/bin/env python3
"""
Auto Restart - Failed Cluster Detection and Restart
Monitors clusters for failures within the last 2 hours and automatically restarts them.

Usage:
    python test_failed_cluster_restart.py --check       # Check failed clusters in last 2 hours
    python test_failed_cluster_restart.py --restart-id <cluster_id>  # Restart a specific cluster
    python test_failed_cluster_restart.py --test-scenario            # Show test scenarios
"""

import argparse
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from databricks_client import DatabricksClient
from self_healing_config import get_config, get_history

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FailedClusterRestarter:
    """Handles detection and restart of failed clusters."""
    
    # Threshold for considering a failure "recent" (in hours)
    FAILURE_WINDOW_HOURS = 2
    
    # Maximum number of restart attempts per cluster (only last failed job)
    MAX_RESTART_ATTEMPTS = 1
    
    # States that indicate cluster failure
    FAILED_STATES = {"FAILED", "ERROR"}
    
    # States that indicate potential failure
    CHECK_STATES = {"FAILED", "ERROR", "TERMINATED", "TERMINATING"}
    
    def __init__(self, databricks_client: DatabricksClient):
        """Initialize the failed cluster restarter.
        
        Args:
            databricks_client: Databricks API client
        """
        self.client = databricks_client
        self.config = get_config()
        self.history = get_history()
    
    def get_failed_clusters_last_n_hours(self, hours: int = 2) -> List[Dict[str, Any]]:
        """Get clusters that failed in the last N hours.
        
        Args:
            hours: Number of hours to look back (default: 2)
            
        Returns:
            List of failed cluster information
        """
        try:
            logger.info(f"Fetching clusters that failed in the last {hours} hours...")
            clusters = self.client.get_all_clusters()
            failed_clusters = []
            now = datetime.now()
            cutoff_time = now - timedelta(hours=hours)
            
            for cluster in clusters:
                cluster_id = cluster.get("cluster_id")
                cluster_name = cluster.get("cluster_name", "Unknown")
                state = cluster.get("state", "UNKNOWN")
                
                # Check if cluster is in a failed state
                if state not in self.CHECK_STATES:
                    continue
                
                # Parse failure/termination timestamp
                failure_time = self._parse_timestamp(
                    cluster.get("terminated_time") or 
                    cluster.get("last_state_loss_time") or
                    cluster.get("start_time")
                )
                
                if not failure_time:
                    logger.debug(f"Cluster {cluster_name}: No timestamp found")
                    continue
                
                # Check if failure is within our window
                if failure_time < cutoff_time:
                    logger.debug(f"Cluster {cluster_name}: Failure too old ({failure_time})")
                    continue
                
                # Calculate how long ago the failure occurred
                time_since_failure = now - failure_time
                minutes_ago = int(time_since_failure.total_seconds() / 60)
                
                failed_clusters.append({
                    "cluster_id": cluster_id,
                    "cluster_name": cluster_name,
                    "state": state,
                    "failure_time": failure_time.isoformat(),
                    "minutes_ago": minutes_ago,
                    "hours_ago": round(minutes_ago / 60, 1),
                    "restart_attempts": self._get_restart_attempts(cluster_id),
                    "can_restart": self._can_restart_cluster(cluster_id)
                })
                
                logger.info(
                    f"Found failed cluster: {cluster_name} ({cluster_id}) "
                    f"- State: {state}, Failed {minutes_ago} minutes ago"
                )
            
            return sorted(
                failed_clusters,
                key=lambda x: x["minutes_ago"]
            )
            
        except Exception as e:
            logger.error(f"Error fetching failed clusters: {str(e)}", exc_info=True)
            return []
    
    def _parse_timestamp(self, timestamp_str: Optional[str]) -> Optional[datetime]:
        """Parse ISO format timestamp string to datetime object.
        
        Args:
            timestamp_str: ISO format timestamp string
            
        Returns:
            datetime object or None if parsing fails
        """
        if not timestamp_str:
            return None
        
        try:
            # Handle ISO format with timezone
            if isinstance(timestamp_str, (int, float)):
                # Unix timestamp in seconds
                return datetime.fromtimestamp(timestamp_str)
            
            # Try ISO format
            return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError, TypeError) as e:
            logger.debug(f"Could not parse timestamp {timestamp_str}: {e}")
            return None
    
    def _get_restart_attempts(self, cluster_id: str) -> int:
        """Get number of restart attempts for a cluster.
        
        Args:
            cluster_id: Cluster ID
            
        Returns:
            Number of restart attempts
        """
        try:
            actions = self.history.get_actions()
            restart_count = sum(
                1 for action in actions
                if (action.get("action_type") == "auto_restart" and 
                    action.get("resource_id") == cluster_id)
            )
            return restart_count
        except Exception as e:
            logger.warning(f"Could not get restart attempts for {cluster_id}: {e}")
            return 0
    
    def _can_restart_cluster(self, cluster_id: str) -> bool:
        """Check if a cluster can be restarted.
        
        Args:
            cluster_id: Cluster ID
            
        Returns:
            True if cluster can be restarted, False otherwise
        """
        restart_attempts = self._get_restart_attempts(cluster_id)
        return restart_attempts < self.MAX_RESTART_ATTEMPTS
    
    def restart_cluster(self, cluster_id: str, reason: str = "Auto-restart triggered") -> Dict[str, Any]:
        """Restart a failed cluster.
        
        Args:
            cluster_id: Cluster ID to restart
            reason: Reason for restarting
            
        Returns:
            Result dictionary with status and message
        """
        try:
            logger.info(f"Attempting to restart cluster {cluster_id}...")
            
            # Check restart policy
            if not self._can_restart_cluster(cluster_id):
                message = f"Max restart attempts ({self.MAX_RESTART_ATTEMPTS}) reached"
                logger.warning(message)
                return {
                    "status": "failed",
                    "cluster_id": cluster_id,
                    "message": message,
                    "reason": "max_attempts_exceeded"
                }
            
            # Attempt restart via Databricks API
            url = f"{self.client.host}/api/2.0/clusters/start"
            payload = {"cluster_id": cluster_id}
            
            response = self.client._make_request("POST", url, payload)
            
            if response.get("status") == "success" or response.get("status_code") == 200:
                message = f"Successfully initiated restart for cluster {cluster_id}"
                logger.info(message)
                
                # Record in history
                self.history.add_action(
                    action_type="auto_restart",
                    resource_id=cluster_id,
                    resource_type="cluster",
                    status="success",
                    details={
                        "reason": reason,
                        "restart_initiated": True
                    }
                )
                
                return {
                    "status": "success",
                    "cluster_id": cluster_id,
                    "message": message
                }
            else:
                message = response.get("error", "Unknown error during restart")
                logger.error(f"Failed to restart cluster: {message}")
                
                self.history.add_action(
                    action_type="auto_restart",
                    resource_id=cluster_id,
                    resource_type="cluster",
                    status="failed",
                    details={
                        "reason": reason,
                        "error": message
                    }
                )
                
                return {
                    "status": "failed",
                    "cluster_id": cluster_id,
                    "message": message
                }
                
        except Exception as e:
            logger.error(f"Error restarting cluster: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "cluster_id": cluster_id,
                "message": str(e)
            }
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate a report of failed clusters and restart status.
        
        Returns:
            Report dictionary
        """
        failed_clusters = self.get_failed_clusters_last_n_hours(self.FAILURE_WINDOW_HOURS)
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "window_hours": self.FAILURE_WINDOW_HOURS,
            "total_failed_clusters": len(failed_clusters),
            "clusters": failed_clusters,
            "summary": {
                "can_restart": sum(1 for c in failed_clusters if c["can_restart"]),
                "max_attempts_reached": sum(1 for c in failed_clusters if not c["can_restart"]),
                "config": {
                    "max_restart_attempts": self.MAX_RESTART_ATTEMPTS,
                    "failure_window_hours": self.FAILURE_WINDOW_HOURS
                }
            }
        }
        
        return report


def show_test_scenarios():
    """Show test scenarios for failed cluster restart."""
    scenarios = """
╔════════════════════════════════════════════════════════════════════════════════╗
║           AUTO RESTART - FAILED CLUSTER TEST SCENARIOS                         ║
╚════════════════════════════════════════════════════════════════════════════════╝

SCENARIO 1: Cluster Failed in Last 2 Hours
─────────────────────────────────────────────
When: ERROR or FAILED state with timestamp < 2 hours ago
Action: Auto-restart initiated (up to 3 times per cluster)
Result: Cluster transitions to RUNNING state

Cluster Details:
  • Cluster ID: 0204-144158-example
  • Cluster Name: test-cluster
  • State: ERROR
  • Failed: 45 minutes ago
  • Restart Attempts: 0/3
  ✅ Can Restart: YES

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SCENARIO 2: Cluster Failed > 2 Hours Ago
─────────────────────────────────────────────
When: ERROR or FAILED state with timestamp > 2 hours ago
Action: SKIPPED (outside failure window)
Result: No auto-restart action taken

Cluster Details:
  • Cluster ID: 0204-144158-old
  • Cluster Name: old-cluster
  • State: ERROR
  • Failed: 3 hours ago
  ✅ Status: Outside 2-hour window (SKIPPED)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SCENARIO 3: Max Restart Attempts Reached
─────────────────────────────────────────────
When: Cluster has been restarted 3 times already
Action: SKIPPED (max attempts exceeded)
Result: Manual intervention required

Cluster Details:
  • Cluster ID: 0204-144158-flaky
  • Cluster Name: flaky-cluster
  • State: ERROR
  • Failed: 30 minutes ago
  • Restart Attempts: 3/3
  ⚠️  Can Restart: NO (Max attempts reached)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CONFIGURATION DETAILS
─────────────────────────────────────────────
File: backend/data/self_healing_config.json

{
  "features": {
    "auto_restart_failed_clusters": true    ← Enable/disable feature
  },
  "thresholds": {
    "failed_restart_window_minutes": 120    ← 2 hours window
    "max_restart_attempts": 1               ← Max attempts per cluster (only last failed job)
  },
  "rules": {
    "auto_restart": {
      "conditions": ["FAILED", "ERROR"],    ← States to watch
      "max_attempts": 1,
      "backoff_minutes": 5
    }
  }
}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

HOW TO TEST
─────────────────────────────────────────────

1. Check failed clusters in the last 2 hours:
   $ python test_failed_cluster_restart.py --check

2. View test scenarios:
   $ python test_failed_cluster_restart.py --test-scenario

3. Restart a specific cluster:
   $ python test_failed_cluster_restart.py --restart-id <cluster_id>

4. View detailed report:
   $ python test_failed_cluster_restart.py --report

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    print(scenarios)


def main():
    """Main entry point."""
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    host = os.getenv("DATABRICKS_HOST")
    token = os.getenv("DATABRICKS_TOKEN")
    
    if not host or not token:
        logger.error("DATABRICKS_HOST and DATABRICKS_TOKEN environment variables are required")
        print("❌ Error: Missing Databricks credentials in .env file")
        return
    
    parser = argparse.ArgumentParser(
        description="Auto Restart - Failed Cluster Detection and Restart"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check for failed clusters in the last 2 hours"
    )
    parser.add_argument(
        "--restart-id",
        type=str,
        help="Restart a specific cluster by ID"
    )
    parser.add_argument(
        "--restart-all",
        action="store_true",
        help="Attempt to restart all restartable failed clusters"
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate a detailed report"
    )
    parser.add_argument(
        "--test-scenario",
        action="store_true",
        help="Show test scenarios and configuration details"
    )
    
    args = parser.parse_args()
    
    # Show test scenarios
    if args.test_scenario:
        show_test_scenarios()
        return
    
    # Initialize client and restarter
    try:
        client = DatabricksClient(host=host, token=token)
        restarter = FailedClusterRestarter(client)
    except Exception as e:
        logger.error(f"Failed to initialize Databricks client: {e}")
        return
    
    # Check for failed clusters
    if args.check or args.report or args.restart_all:
        failed_clusters = restarter.get_failed_clusters_last_n_hours(2)
        
        if not failed_clusters:
            print("\n✅ No failed clusters in the last 2 hours\n")
            return
        
        print(f"\n📊 Found {len(failed_clusters)} failed cluster(s) in the last 2 hours:\n")
        print("─" * 100)
        
        for cluster in failed_clusters:
            status = "✅ Can Restart" if cluster["can_restart"] else "⚠️  Max Attempts"
            print(f"ID: {cluster['cluster_id']}")
            print(f"Name: {cluster['cluster_name']}")
            print(f"State: {cluster['state']}")
            print(f"Failed: {cluster['minutes_ago']} minutes ago ({cluster['hours_ago']} hours)")
            print(f"Restart Attempts: {cluster['restart_attempts']}/{restarter.MAX_RESTART_ATTEMPTS}")
            print(f"Status: {status}")
            print("─" * 100)
        
        # Generate report if requested
        if args.report:
            report = restarter.generate_report()
            print("\n📋 DETAILED REPORT:")
            print(json.dumps(report, indent=2))
        
        # Restart all restartable clusters
        if args.restart_all:
            print("\n🔄 Attempting to restart all restartable clusters...\n")
            for cluster in failed_clusters:
                if cluster["can_restart"]:
                    result = restarter.restart_cluster(
                        cluster["cluster_id"],
                        reason=f"Auto-restart triggered - cluster {cluster['state']}"
                    )
                    print(f"  {cluster['cluster_name']}: {result['message']}")
    
    # Restart specific cluster
    if args.restart_id:
        print(f"\n🔄 Restarting cluster {args.restart_id}...\n")
        result = restarter.restart_cluster(args.restart_id)
        print(f"Result: {result['message']}")
        if result['status'] == 'success':
            print("✅ Restart initiated successfully!")
        else:
            print(f"❌ Restart failed: {result.get('reason', 'Unknown error')}")


if __name__ == "__main__":
    main()
