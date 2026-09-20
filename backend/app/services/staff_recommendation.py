"""
Staff Recommendation Engine for Airport Operations.
Provides rule-based staffing recommendations based on predictions.
"""

from app.core.config import settings


class StaffRecommendationEngine:
    """
    Generates staffing recommendations based on predicted operational metrics.
    Uses simple rules that are easy to explain during viva/presentation.
    """
    
    def recommend(
        self,
        passenger_flow: float,
        queue_length: float,
        waiting_time: float,
        security_staff: int = 0,
        checkin_staff: int = 0
    ) -> list[dict]:
        """
        Generate staffing recommendations.
        
        Returns:
            List of recommendation dicts with: priority, category, recommendation, reason
        """
        recommendations = []
        
        # --- High Queue + High Passenger Flow ---
        if queue_length > settings.QUEUE_HIGH_THRESHOLD and passenger_flow > settings.PASSENGER_WARNING_THRESHOLD:
            recommendations.append({
                "priority": "critical",
                "category": "check-in",
                "recommendation": "Open 2-3 additional check-in counters immediately",
                "reason": f"Queue length ({queue_length:.0f}) and passenger flow ({passenger_flow:.0f}) both exceed thresholds"
            })
            recommendations.append({
                "priority": "critical",
                "category": "security",
                "recommendation": "Deploy 4-5 additional security officers to screening lanes",
                "reason": "High congestion requires faster passenger processing"
            })
        
        # --- High Queue Only ---
        elif queue_length > settings.QUEUE_HIGH_THRESHOLD:
            recommendations.append({
                "priority": "high",
                "category": "check-in",
                "recommendation": "Open 1-2 additional check-in counters",
                "reason": f"Queue length is high: {queue_length:.0f} people"
            })
        
        # --- Medium Queue ---
        elif queue_length > settings.QUEUE_MEDIUM_THRESHOLD:
            recommendations.append({
                "priority": "medium",
                "category": "check-in",
                "recommendation": "Prepare to open additional check-in counter if queue grows",
                "reason": f"Queue length is moderate: {queue_length:.0f} people"
            })
        
        # --- High Waiting Time ---
        if waiting_time > settings.WAITING_HIGH_THRESHOLD:
            recommendations.append({
                "priority": "high",
                "category": "security",
                "recommendation": "Deploy 5+ additional security staff to reduce waiting time",
                "reason": f"Waiting time is {waiting_time:.0f} minutes (exceeds {settings.WAITING_HIGH_THRESHOLD} min threshold)"
            })
            recommendations.append({
                "priority": "high",
                "category": "operations",
                "recommendation": "Open additional security screening lanes",
                "reason": "High waiting times indicate insufficient processing capacity"
            })
        elif waiting_time > settings.WAITING_MEDIUM_THRESHOLD:
            recommendations.append({
                "priority": "medium",
                "category": "security",
                "recommendation": "Consider adding 2-3 security staff to screening",
                "reason": f"Waiting time is elevated: {waiting_time:.0f} minutes"
            })
        
        # --- High Passenger Flow ---
        if passenger_flow > settings.PASSENGER_CAPACITY_THRESHOLD:
            recommendations.append({
                "priority": "critical",
                "category": "operations",
                "recommendation": "Activate overflow management protocol - deploy all available staff",
                "reason": f"Passenger flow ({passenger_flow:.0f}) exceeds airport capacity ({settings.PASSENGER_CAPACITY_THRESHOLD})"
            })
            recommendations.append({
                "priority": "high",
                "category": "crowd-management",
                "recommendation": "Deploy crowd management team to terminal areas",
                "reason": "Extremely high passenger volume requires active crowd control"
            })
        elif passenger_flow > settings.PASSENGER_WARNING_THRESHOLD:
            recommendations.append({
                "priority": "medium",
                "category": "operations",
                "recommendation": "Place additional staff on standby for potential surge",
                "reason": f"Passenger flow ({passenger_flow:.0f}) approaching capacity limits"
            })
        
        # --- Low Utilization (Efficiency) ---
        if (queue_length < 15 and waiting_time < 10 and
                passenger_flow < settings.PASSENGER_WARNING_THRESHOLD * 0.3):
            recommendations.append({
                "priority": "low",
                "category": "efficiency",
                "recommendation": "Consider reducing staff by 10-20% during this period",
                "reason": f"Low utilization: queue={queue_length:.0f}, wait={waiting_time:.0f}min, flow={passenger_flow:.0f}"
            })
        
        # --- Default: Everything normal ---
        if not recommendations:
            recommendations.append({
                "priority": "info",
                "category": "operations",
                "recommendation": "Current staffing levels are adequate",
                "reason": "All operational metrics are within acceptable ranges"
            })
        
        # Sort by priority
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
        recommendations.sort(key=lambda x: priority_order.get(x["priority"], 5))
        
        return recommendations


# Global recommendation engine instance
recommendation_engine = StaffRecommendationEngine()
