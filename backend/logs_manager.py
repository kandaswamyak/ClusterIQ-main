"""Logs management for ClusterIQ - captures and stores application logs."""
import logging
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from collections import deque
from threading import Lock

# In-memory log storage with a maximum size
MAX_LOGS = 1000


class LogHandler(logging.Handler):
    """Custom logging handler that stores logs in memory."""
    
    def __init__(self, log_manager: 'LogManager'):
        super().__init__()
        self.log_manager = log_manager
    
    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record."""
        try:
            log_entry = {
                "timestamp": datetime.utcfromtimestamp(record.created).isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": self.format(record),
                "module": record.module,
                "function": record.funcName,
                "line_number": record.lineno,
            }
            
            # Add exception info if present
            if record.exc_info:
                log_entry["exception"] = self.format_exception(record.exc_info)
            
            self.log_manager.add_log(log_entry)
        except Exception:
            self.handleError(record)


class LogManager:
    """Manages application logs storage and retrieval."""
    
    def __init__(self, max_logs: int = MAX_LOGS):
        """Initialize log manager.
        
        Args:
            max_logs: Maximum number of logs to store in memory
        """
        self.max_logs = max_logs
        self.logs = deque(maxlen=max_logs)  # Automatically removes oldest when max is reached
        self.lock = Lock()
        self.level_counts = {
            "DEBUG": 0,
            "INFO": 0,
            "WARNING": 0,
            "ERROR": 0,
            "CRITICAL": 0
        }
    
    def add_log(self, log_entry: Dict[str, Any]) -> None:
        """Add a log entry to storage.
        
        Args:
            log_entry: Log entry dictionary
        """
        with self.lock:
            self.logs.append(log_entry)
            level = log_entry.get("level", "INFO")
            if level in self.level_counts:
                self.level_counts[level] += 1
    
    def get_logs(self, level: Optional[str] = None, limit: int = 100,
                 logger_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get logs with optional filtering.
        
        Args:
            level: Log level to filter by (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            limit: Maximum number of logs to return
            logger_name: Logger name to filter by
            
        Returns:
            List of log entries
        """
        with self.lock:
            filtered_logs = list(self.logs)
        
        # Apply filters
        if level:
            filtered_logs = [log for log in filtered_logs if log.get("level") == level]
        
        if logger_name:
            filtered_logs = [log for log in filtered_logs if log_name in log.get("logger", "")]
        
        # Return most recent logs first (reverse order) and limit
        return list(reversed(filtered_logs))[-limit:]
    
    def get_logs_by_level(self) -> Dict[str, int]:
        """Get count of logs by level.
        
        Returns:
            Dictionary with log counts by level
        """
        with self.lock:
            return self.level_counts.copy()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get logging statistics.
        
        Returns:
            Dictionary with logging stats
        """
        with self.lock:
            total_logs = len(self.logs)
            
            if self.logs:
                oldest_log = list(self.logs)[0]
                newest_log = list(self.logs)[-1]
            else:
                oldest_log = None
                newest_log = None
        
        return {
            "total_logs": total_logs,
            "max_capacity": self.max_logs,
            "logs_by_level": self.get_logs_by_level(),
            "oldest_log_timestamp": oldest_log.get("timestamp") if oldest_log else None,
            "newest_log_timestamp": newest_log.get("timestamp") if newest_log else None,
            "capacity_usage": f"{(total_logs / self.max_logs) * 100:.1f}%"
        }
    
    def clear_logs(self) -> None:
        """Clear all logs."""
        with self.lock:
            self.logs.clear()
            self.level_counts = {
                "DEBUG": 0,
                "INFO": 0,
                "WARNING": 0,
                "ERROR": 0,
                "CRITICAL": 0
            }
    
    def export_logs(self, format: str = "json") -> str:
        """Export logs in specified format.
        
        Args:
            format: Export format ('json' or 'csv')
            
        Returns:
            Formatted log data as string
        """
        with self.lock:
            logs_list = list(self.logs)
        
        if format == "json":
            return json.dumps(logs_list, indent=2)
        elif format == "csv":
            import csv
            from io import StringIO
            
            output = StringIO()
            if logs_list:
                fieldnames = logs_list[0].keys()
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(logs_list)
            
            return output.getvalue()
        else:
            raise ValueError(f"Unsupported export format: {format}")


# Global log manager instance
log_manager = LogManager()


def setup_logging(logger: logging.Logger) -> None:
    """Setup logging with the custom handler.
    
    Args:
        logger: Logger instance to configure
    """
    handler = LogHandler(log_manager)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
