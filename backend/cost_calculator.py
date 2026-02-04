"""Cost calculation and analysis module for ClusterIQ."""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Pricing constants (per DBU-hour)
PRICING_TIERS = {
    "jobs_compute_standard": 0.15,
    "jobs_compute_premium": 0.22,  # Average
    "all_purpose_standard": 0.40,
    "all_purpose_premium": 0.475,  # Average
    "serverless_sql": 0.70,
    "model_serving_cpu": 0.08,
    "model_serving_gpu": 0.65,
    "sql_warehouse": 0.50,  # Estimated
    "pools": 0.35,
    "vector_search": 0.45,
}


class CostCalculator:
    """Calculate costs based on DBU consumption and cluster types."""
    
    def __init__(self):
        """Initialize cost calculator."""
        self.pricing_tiers = PRICING_TIERS
    
    def get_price_per_dbu_hour(self, resource_type: str, tier: str = "standard") -> float:
        """Get price per DBU-hour for a resource type.
        
        Args:
            resource_type: Type of resource (jobs, all_purpose, serverless_sql, etc.)
            tier: Tier type (standard, premium)
            
        Returns:
            Price per DBU-hour
        """
        key = f"{resource_type}_{tier}".lower()
        return self.pricing_tiers.get(key, 0.30)  # Default to 0.30 if not found
    
    def calculate_cluster_cost(self, cluster_info: Dict[str, Any], 
                              hours_running: float) -> Dict[str, Any]:
        """Calculate cost for a cluster based on its configuration.
        
        Args:
            cluster_info: Cluster information dictionary
            hours_running: Number of hours the cluster has been running
            
        Returns:
            Dictionary with cost breakdown
        """
        cluster_type = cluster_info.get("cluster_type", "all_purpose").lower()
        num_workers = cluster_info.get("num_workers", 1)
        driver_node_type = cluster_info.get("driver_node_type", "i3.xlarge")
        
        # Estimate DBU multiplier based on node type (simplified)
        dbu_multiplier = self._estimate_dbu_multiplier(driver_node_type)
        total_workers = 1 + num_workers  # 1 driver + workers
        
        # Calculate total DBU consumption
        estimated_dbu = total_workers * dbu_multiplier * hours_running
        
        # Get pricing based on cluster type
        if "job" in cluster_type.lower():
            price_per_dbu = self.get_price_per_dbu_hour("jobs_compute_standard")
        elif "serverless" in cluster_type.lower():
            price_per_dbu = self.get_price_per_dbu_hour("serverless_sql")
        else:  # all-purpose
            price_per_dbu = self.get_price_per_dbu_hour("all_purpose_standard")
        
        total_cost = estimated_dbu * price_per_dbu
        
        return {
            "cluster_id": cluster_info.get("cluster_id"),
            "cluster_name": cluster_info.get("cluster_name"),
            "cluster_type": cluster_type,
            "estimated_dbu": round(estimated_dbu, 2),
            "price_per_dbu_hour": price_per_dbu,
            "total_cost": round(total_cost, 2),
            "hours_running": hours_running,
            "num_workers": num_workers,
            "is_idle": cluster_info.get("state") == "TERMINATED" or hours_running == 0
        }
    
    def _estimate_dbu_multiplier(self, node_type: str) -> float:
        """Estimate DBU multiplier for a node type.
        
        Args:
            node_type: Databricks node type (e.g., i3.xlarge, m5.large)
            
        Returns:
            Estimated DBU multiplier per hour
        """
        # Simplified DBU multiplier mapping
        node_type_lower = node_type.lower()
        
        if "large" in node_type_lower and "2x" in node_type_lower:
            return 2.0
        elif "large" in node_type_lower:
            return 1.0
        elif "xlarge" in node_type_lower and "2x" in node_type_lower:
            return 4.0
        elif "xlarge" in node_type_lower:
            return 2.0
        elif "2xlarge" in node_type_lower:
            return 4.0
        elif "4xlarge" in node_type_lower:
            return 8.0
        elif "small" in node_type_lower:
            return 0.5
        else:
            return 1.0  # Default multiplier
    
    def calculate_job_cost(self, job_info: Dict[str, Any], 
                          runs_count: int = 1, avg_runtime_hours: float = 0.5) -> Dict[str, Any]:
        """Calculate cost for a job based on its configuration.
        
        Args:
            job_info: Job information dictionary
            runs_count: Number of runs per month
            avg_runtime_hours: Average runtime per job in hours
            
        Returns:
            Dictionary with job cost breakdown
        """
        job_type = job_info.get("job_type", "jobs_compute")
        
        # Get pricing
        price_per_dbu = self.get_price_per_dbu_hour(job_type)
        
        # Estimate DBU based on cluster size
        cluster_size = job_info.get("cluster_size", "small")
        if cluster_size == "small":
            dbu_per_run = 1.0
        elif cluster_size == "medium":
            dbu_per_run = 2.5
        elif cluster_size == "large":
            dbu_per_run = 5.0
        else:
            dbu_per_run = 1.5
        
        # Calculate monthly cost
        dbu_per_month = dbu_per_run * avg_runtime_hours * runs_count
        total_cost = dbu_per_month * price_per_dbu
        
        return {
            "job_id": job_info.get("job_id"),
            "job_name": job_info.get("job_name", "Unknown"),
            "job_type": job_type,
            "runs_per_month": runs_count,
            "avg_runtime_hours": avg_runtime_hours,
            "dbu_per_month": round(dbu_per_month, 2),
            "price_per_dbu_hour": price_per_dbu,
            "monthly_cost": round(total_cost, 2),
            "annual_cost": round(total_cost * 12, 2)
        }
    
    def generate_cost_breakdown(self, resources: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive cost breakdown for all resources.
        
        Args:
            resources: Dictionary containing clusters, jobs, and other resources
            
        Returns:
            Cost breakdown by resource type
        """
        breakdown = {
            "by_type": {
                "clusters": 0,
                "jobs": 0,
                "sql_warehouses": 0,
                "model_serving": 0,
                "other": 0
            },
            "by_tier": {
                "jobs_compute": 0,
                "all_purpose": 0,
                "serverless_sql": 0,
                "model_serving": 0
            },
            "idle_resources": [],
            "high_cost_resources": [],
            "optimization_opportunities": [],
            "total_cost": 0,
            "estimated_monthly": 0,
            "estimated_annual": 0
        }
        
        # Process clusters
        clusters = resources.get("clusters", [])
        for cluster in clusters:
            cost_data = self.calculate_cluster_cost(cluster, hours_running=100)  # Assume 100 hrs/month
            breakdown["by_type"]["clusters"] += cost_data["total_cost"]
            breakdown["total_cost"] += cost_data["total_cost"]
            
            if cost_data["is_idle"]:
                breakdown["idle_resources"].append({
                    "name": cost_data["cluster_name"],
                    "type": "cluster",
                    "cost": cost_data["total_cost"]
                })
            
            if cost_data["total_cost"] > 100:  # High cost threshold
                breakdown["high_cost_resources"].append({
                    "name": cost_data["cluster_name"],
                    "type": "cluster",
                    "cost": cost_data["total_cost"]
                })
                
                # Optimization opportunity
                if cost_data["num_workers"] > 5:
                    breakdown["optimization_opportunities"].append({
                        "type": "downsize_cluster",
                        "resource": cost_data["cluster_name"],
                        "potential_savings": cost_data["total_cost"] * 0.3,
                        "recommendation": "Downsize cluster - too many workers"
                    })
        
        # Process jobs
        jobs = resources.get("jobs", [])
        for job in jobs:
            cost_data = self.calculate_job_cost(job)
            breakdown["by_type"]["jobs"] += cost_data["monthly_cost"]
            breakdown["total_cost"] += cost_data["monthly_cost"]
        
        # Calculate estimated costs
        breakdown["estimated_monthly"] = round(breakdown["total_cost"] * 20, 2)  # Rough estimate
        breakdown["estimated_annual"] = round(breakdown["estimated_monthly"] * 12, 2)
        
        # Sort resources by cost
        breakdown["high_cost_resources"] = sorted(
            breakdown["high_cost_resources"],
            key=lambda x: x["cost"],
            reverse=True
        )[:10]
        
        return breakdown
    
    def get_cost_savings_recommendations(self, cluster_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get cost savings recommendations for a cluster.
        
        Args:
            cluster_info: Cluster information
            
        Returns:
            List of cost savings recommendations
        """
        recommendations = []
        
        num_workers = cluster_info.get("num_workers", 0)
        state = cluster_info.get("state", "RUNNING")
        
        # Recommendation 1: Downsize cluster
        if num_workers > 8:
            estimated_savings = (num_workers - 5) * 50  # Rough estimate
            recommendations.append({
                "type": "downsize_cluster",
                "title": "Downsize Cluster",
                "description": f"Reduce workers from {num_workers} to 5",
                "estimated_savings": estimated_savings,
                "priority": "high"
            })
        
        # Recommendation 2: Terminate idle cluster
        if state == "TERMINATED" or cluster_info.get("is_idle", False):
            recommendations.append({
                "type": "terminate_cluster",
                "title": "Terminate Idle Cluster",
                "description": "This cluster is idle and consuming costs",
                "estimated_savings": 200,
                "priority": "critical"
            })
        
        # Recommendation 3: Use spot instances
        recommendations.append({
            "type": "enable_spot_instances",
            "title": "Enable Spot Instances",
            "description": "Switch to spot instances for 30-50% cost savings",
            "estimated_savings": (num_workers + 1) * 50 * 0.4,  # 40% savings
            "priority": "medium"
        })
        
        return recommendations


cost_calculator = CostCalculator()
