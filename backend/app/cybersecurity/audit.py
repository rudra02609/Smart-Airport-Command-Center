"""
Audit Logging System for Smart Airport Command Center.
Logs security events, API requests, and admin actions to a JSON-line file.
"""

import json
import os
from datetime import datetime, timezone
from typing import Optional
from app.core.config import settings


class AuditLogger:
    """
    Logs audit events to a JSON-lines file.
    Each line is a JSON object representing one event.
    """
    
    def __init__(self):
        self.log_file = os.path.join(settings.LOGS_DIR, "audit.log")
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
    
    def log(
        self,
        user: str = "anonymous",
        action: str = "",
        endpoint: str = "",
        status: str = "success",
        ip_address: str = "",
        details: str = ""
    ) -> dict:
        """
        Record an audit event.
        
        Args:
            user: Username who performed the action
            action: Type of action (login, prediction, admin_action, etc.)
            endpoint: API endpoint called
            status: Result status (success, failed, error)
            ip_address: Client IP address
            details: Additional details about the event
        """
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user": user,
            "action": action,
            "endpoint": endpoint,
            "status": status,
            "ip_address": ip_address,
            "details": details
        }
        
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(event) + "\n")
        except Exception as e:
            print(f"Audit log write error: {e}")
        
        return event
    
    def get_logs(
        self,
        limit: int = 50,
        user: Optional[str] = None,
        action: Optional[str] = None
    ) -> list[dict]:
        """
        Retrieve recent audit logs with optional filtering.
        
        Args:
            limit: Maximum number of logs to return
            user: Filter by username
            action: Filter by action type
        """
        logs = []
        
        if not os.path.exists(self.log_file):
            return logs
        
        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        event = json.loads(line)
                        # Apply filters
                        if user and event.get("user") != user:
                            continue
                        if action and event.get("action") != action:
                            continue
                        logs.append(event)
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"Audit log read error: {e}")
        
        # Return most recent logs
        return logs[-limit:]
    
    def get_stats(self) -> dict:
        """
        Get summary statistics from audit logs.
        Returns counts by action type and status.
        """
        logs = self.get_logs(limit=10000)  # Get all recent logs
        
        stats = {
            "total_events": len(logs),
            "by_action": {},
            "by_status": {},
            "by_user": {},
            "recent_failures": []
        }
        
        for log in logs:
            # Count by action
            action = log.get("action", "unknown")
            stats["by_action"][action] = stats["by_action"].get(action, 0) + 1
            
            # Count by status
            status = log.get("status", "unknown")
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
            
            # Count by user
            user = log.get("user", "unknown")
            stats["by_user"][user] = stats["by_user"].get(user, 0) + 1
            
            # Track failures
            if status == "failed":
                stats["recent_failures"].append(log)
        
        # Keep only last 10 failures
        stats["recent_failures"] = stats["recent_failures"][-10:]
        
        return stats


# Global audit logger instance
audit_logger = AuditLogger()
