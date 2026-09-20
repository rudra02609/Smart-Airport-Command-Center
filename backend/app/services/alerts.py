"""
Smart Alert Engine for Airport Operations.
Generates threshold-based alerts for congestion, capacity, delays, and staffing.
Also calculates the operational Security Risk Score.
"""

from enum import Enum
from datetime import datetime, timezone
from app.core.config import settings


class AlertSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AlertCategory(str, Enum):
    CONGESTION = "congestion"
    CAPACITY = "capacity"
    DELAY = "delay"
    STAFFING = "staffing"
    SECURITY = "security"


class AlertEngine:
    """
    Evaluates airport operational metrics and generates alerts,
    congestion levels, and a Security Risk Score.
    """
    
    def evaluate(
        self,
        passenger_flow: float,
        queue_length: float,
        waiting_time: float
    ) -> dict:
        """
        Evaluate airport conditions and generate alerts.
        
        Returns:
            dict with: alerts, congestion_level, overall_severity, security_risk_score
        """
        alerts = []
        
        # --- Queue Length Alerts ---
        if queue_length > settings.QUEUE_HIGH_THRESHOLD:
            alerts.append({
                "severity": AlertSeverity.HIGH.value,
                "category": AlertCategory.CONGESTION.value,
                "message": f"Queue length is very high: {queue_length:.0f} people (threshold: {settings.QUEUE_HIGH_THRESHOLD})",
                "metric": "queue_length",
                "value": round(queue_length, 1),
                "threshold": settings.QUEUE_HIGH_THRESHOLD
            })
        elif queue_length > settings.QUEUE_MEDIUM_THRESHOLD:
            alerts.append({
                "severity": AlertSeverity.MEDIUM.value,
                "category": AlertCategory.CONGESTION.value,
                "message": f"Queue length is elevated: {queue_length:.0f} people (threshold: {settings.QUEUE_MEDIUM_THRESHOLD})",
                "metric": "queue_length",
                "value": round(queue_length, 1),
                "threshold": settings.QUEUE_MEDIUM_THRESHOLD
            })
        
        # --- Waiting Time Alerts ---
        if waiting_time > settings.WAITING_HIGH_THRESHOLD:
            alerts.append({
                "severity": AlertSeverity.HIGH.value,
                "category": AlertCategory.DELAY.value,
                "message": f"Waiting time is critically high: {waiting_time:.0f} minutes (threshold: {settings.WAITING_HIGH_THRESHOLD})",
                "metric": "waiting_time",
                "value": round(waiting_time, 1),
                "threshold": settings.WAITING_HIGH_THRESHOLD
            })
        elif waiting_time > settings.WAITING_MEDIUM_THRESHOLD:
            alerts.append({
                "severity": AlertSeverity.MEDIUM.value,
                "category": AlertCategory.DELAY.value,
                "message": f"Waiting time is elevated: {waiting_time:.0f} minutes (threshold: {settings.WAITING_MEDIUM_THRESHOLD})",
                "metric": "waiting_time",
                "value": round(waiting_time, 1),
                "threshold": settings.WAITING_MEDIUM_THRESHOLD
            })
        
        # --- Passenger Flow Alerts ---
        if passenger_flow > settings.PASSENGER_CAPACITY_THRESHOLD:
            alerts.append({
                "severity": AlertSeverity.CRITICAL.value,
                "category": AlertCategory.CAPACITY.value,
                "message": f"Passenger flow exceeds capacity: {passenger_flow:.0f} (threshold: {settings.PASSENGER_CAPACITY_THRESHOLD})",
                "metric": "passenger_flow",
                "value": round(passenger_flow, 1),
                "threshold": settings.PASSENGER_CAPACITY_THRESHOLD
            })
        elif passenger_flow > settings.PASSENGER_WARNING_THRESHOLD:
            alerts.append({
                "severity": AlertSeverity.HIGH.value,
                "category": AlertCategory.CAPACITY.value,
                "message": f"Passenger flow is high: {passenger_flow:.0f} (warning threshold: {settings.PASSENGER_WARNING_THRESHOLD})",
                "metric": "passenger_flow",
                "value": round(passenger_flow, 1),
                "threshold": settings.PASSENGER_WARNING_THRESHOLD
            })
        
        # --- Congestion Detection ---
        congestion_score = self._calculate_congestion_score(
            passenger_flow, queue_length, waiting_time
        )
        congestion_level = self._get_congestion_level(congestion_score)
        
        # Add congestion alert if warranted
        if congestion_level in ["HIGH", "CRITICAL"]:
            alerts.append({
                "severity": AlertSeverity.HIGH.value if congestion_level == "HIGH" else AlertSeverity.CRITICAL.value,
                "category": AlertCategory.CONGESTION.value,
                "message": f"Overall congestion level: {congestion_level} (score: {congestion_score}/100)",
                "metric": "congestion_score",
                "value": congestion_score,
                "threshold": 70
            })
        
        # No alerts = good
        if not alerts:
            alerts.append({
                "severity": AlertSeverity.INFO.value,
                "category": AlertCategory.CONGESTION.value,
                "message": "All operational metrics are within normal ranges",
                "metric": "overall",
                "value": 0,
                "threshold": 0
            })
        
        # Determine overall severity
        severity_order = ["critical", "high", "medium", "low", "info"]
        overall_severity = "info"
        for sev in severity_order:
            if any(a["severity"] == sev for a in alerts):
                overall_severity = sev
                break
        
        # Calculate Security Risk Score
        security_risk_score = self._calculate_risk_score(
            passenger_flow, queue_length, waiting_time,
            congestion_level, overall_severity
        )
        
        return {
            "alerts": alerts,
            "congestion_level": congestion_level,
            "congestion_score": congestion_score,
            "overall_severity": overall_severity,
            "security_risk_score": security_risk_score,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def _calculate_congestion_score(self, passenger_flow, queue_length, waiting_time) -> int:
        """
        Calculate a 0-100 congestion score from operational metrics.
        Weights: passenger_flow=40%, queue_length=35%, waiting_time=25%
        """
        # Normalize each metric to 0-100 scale
        pf_score = min(100, (passenger_flow / settings.PASSENGER_CAPACITY_THRESHOLD) * 100)
        ql_score = min(100, (queue_length / settings.QUEUE_HIGH_THRESHOLD) * 100)
        wt_score = min(100, (waiting_time / settings.WAITING_HIGH_THRESHOLD) * 100)
        
        # Weighted average
        congestion = int(pf_score * 0.40 + ql_score * 0.35 + wt_score * 0.25)
        return min(100, max(0, congestion))
    
    def _get_congestion_level(self, score: int) -> str:
        """Map congestion score to level."""
        if score >= 85:
            return "CRITICAL"
        elif score >= 70:
            return "HIGH"
        elif score >= 45:
            return "MODERATE"
        elif score >= 20:
            return "LOW"
        else:
            return "MINIMAL"
    
    def _calculate_risk_score(
        self,
        passenger_flow: float,
        queue_length: float,
        waiting_time: float,
        congestion_level: str,
        alert_severity: str
    ) -> int:
        """
        Calculate Security Risk Score (0-100) combining operational metrics.
        
        Components:
        - Passenger flow contribution (25%)
        - Queue length contribution (25%)
        - Waiting time contribution (20%)
        - Congestion level (15%)
        - Alert severity (15%)
        """
        # Normalize metrics to 0-100
        pf_component = min(100, (passenger_flow / settings.PASSENGER_CAPACITY_THRESHOLD) * 100) * 0.25
        ql_component = min(100, (queue_length / settings.QUEUE_HIGH_THRESHOLD) * 100) * 0.25
        wt_component = min(100, (waiting_time / settings.WAITING_HIGH_THRESHOLD) * 100) * 0.20
        
        # Congestion level mapping
        congestion_map = {"CRITICAL": 100, "HIGH": 75, "MODERATE": 50, "LOW": 25, "MINIMAL": 5}
        cg_component = congestion_map.get(congestion_level, 0) * 0.15
        
        # Alert severity mapping
        severity_map = {"critical": 100, "high": 75, "medium": 50, "low": 25, "info": 5}
        as_component = severity_map.get(alert_severity, 0) * 0.15
        
        risk_score = int(pf_component + ql_component + wt_component + cg_component + as_component)
        return min(100, max(0, risk_score))


# Global alert engine instance
alert_engine = AlertEngine()
