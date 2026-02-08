"""
Self-Healing Configuration Module
Manages auto-healing settings, rules, and thresholds
"""
import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

class SelfHealingConfig:
    """Configuration manager for self-healing capabilities"""
    
    def __init__(self, config_file: str = "data/self_healing_config.json"):
        self.config_file = Path(__file__).parent / config_file
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)
        return self._default_config()
    
    def _default_config(self) -> Dict[str, Any]:
        """Default self-healing configuration"""
        return {
            "enabled": False,
            "features": {
                "auto_restart_failed_clusters": True,
                "auto_terminate_idle_clusters": True,
                "auto_scale_adjustments": False,
                "auto_apply_optimizations": False,
                "proactive_health_checks": True
            },
            "thresholds": {
                "idle_timeout_minutes": 30,
                "failed_restart_window_minutes": 120,
                "max_restart_attempts": 3,
                "cpu_utilization_low": 10,
                "cpu_utilization_high": 90,
                "memory_utilization_high": 85,
                "cost_spike_threshold_percent": 50
            },
            "rules": {
                "auto_restart": {
                    "enabled": True,
                    "conditions": ["FAILED", "ERROR", "TERMINATING"],
                    "max_attempts": 3,
                    "backoff_minutes": 5
                },
                "auto_terminate": {
                    "enabled": True,
                    "idle_minutes": 30,
                    "exclude_tags": ["production", "critical"]
                },
                "auto_scale": {
                    "enabled": False,
                    "scale_up_cpu_threshold": 80,
                    "scale_down_cpu_threshold": 20,
                    "min_workers": 1,
                    "max_workers": 10
                }
            },
            "notifications": {
                "enabled": True,
                "channels": ["dashboard", "log"],
                "notify_on_success": True,
                "notify_on_failure": True
            },
            "safety": {
                "dry_run": True,
                "require_confirmation_for_critical": True,
                "max_actions_per_hour": 10,
                "exclude_clusters": []
            }
        }
    
    def save_config(self):
        """Save configuration to file"""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def update_config(self, updates: Dict[str, Any]):
        """Update configuration with new values"""
        def deep_update(base, updates):
            for key, value in updates.items():
                if isinstance(value, dict) and key in base:
                    deep_update(base[key], value)
                else:
                    base[key] = value
        
        deep_update(self.config, updates)
        self.save_config()
    
    def is_enabled(self) -> bool:
        """Check if self-healing is enabled globally"""
        return self.config.get("enabled", False)
    
    def is_feature_enabled(self, feature: str) -> bool:
        """Check if specific feature is enabled"""
        return self.config.get("features", {}).get(feature, False)
    
    def get_threshold(self, threshold: str) -> Any:
        """Get threshold value"""
        return self.config.get("thresholds", {}).get(threshold)
    
    def get_rule(self, rule: str) -> Dict[str, Any]:
        """Get rule configuration"""
        return self.config.get("rules", {}).get(rule, {})
    
    def is_dry_run(self) -> bool:
        """Check if in dry-run mode"""
        return self.config.get("safety", {}).get("dry_run", True)
    
    def can_auto_heal_cluster(self, cluster_id: str, cluster_tags: List[str] = None) -> bool:
        """Check if cluster is eligible for auto-healing"""
        if not self.is_enabled():
            return False
        
        # Check exclusion list
        excluded = self.config.get("safety", {}).get("exclude_clusters", [])
        if cluster_id in excluded:
            return False
        
        # Check excluded tags
        if cluster_tags:
            excluded_tags = self.get_rule("auto_terminate").get("exclude_tags", [])
            if any(tag in excluded_tags for tag in cluster_tags):
                return False
        
        return True


class HealingHistory:
    """Track self-healing actions and outcomes"""
    
    def __init__(self, history_file: str = "data/healing_history.json"):
        self.history_file = Path(__file__).parent / history_file
        self.history = self._load_history()
    
    def _load_history(self) -> List[Dict[str, Any]]:
        """Load history from file"""
        if self.history_file.exists():
            with open(self.history_file, 'r') as f:
                return json.load(f)
        return []
    
    def _save_history(self):
        """Save history to file"""
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        # Keep only last 1000 entries
        self.history = self.history[-1000:]
        with open(self.history_file, 'w') as f:
            json.dump(self.history, f, indent=2)
    
    def add_action(self, action_type: str, resource_id: str, resource_type: str, 
                   status: str, details: Dict[str, Any] = None):
        """Record a self-healing action"""
        action = {
            "timestamp": datetime.now().isoformat(),
            "action_type": action_type,
            "resource_id": resource_id,
            "resource_type": resource_type,
            "status": status,
            "details": details or {},
            "dry_run": details.get("dry_run", False) if details else False
        }
        self.history.append(action)
        self._save_history()
    
    def get_recent_actions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent healing actions, sorted by newest first"""
        return self.history[-limit:][::-1]
    
    def get_actions_for_resource(self, resource_id: str) -> List[Dict[str, Any]]:
        """Get all actions for a specific resource"""
        return [a for a in self.history if a.get("resource_id") == resource_id]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get healing statistics"""
        total = len(self.history)
        successful = len([a for a in self.history if a.get("status") == "success"])
        failed = len([a for a in self.history if a.get("status") == "failed"])
        
        action_counts = {}
        for action in self.history:
            action_type = action.get("action_type", "unknown")
            action_counts[action_type] = action_counts.get(action_type, 0) + 1
        
        return {
            "total_actions": total,
            "successful": successful,
            "failed": failed,
            "success_rate": (successful / total * 100) if total > 0 else 0,
            "actions_by_type": action_counts,
            "last_action": self.history[-1] if self.history else None
        }


# Global instances
_config = None
_history = None

def get_config() -> SelfHealingConfig:
    """Get global config instance"""
    global _config
    if _config is None:
        _config = SelfHealingConfig()
    return _config

def get_history() -> HealingHistory:
    """Get global history instance"""
    global _history
    if _history is None:
        _history = HealingHistory()
    return _history
