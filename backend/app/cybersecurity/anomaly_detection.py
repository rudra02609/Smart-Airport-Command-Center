"""
Lightweight ML-based Anomaly Detection using Isolation Forest.
Detects unusual API usage patterns such as:
- Too many requests from a single IP
- Repeated failed login attempts
- Unusual endpoint access patterns
"""

import numpy as np
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from typing import Optional


class AnomalyDetector:
    """
    Detects anomalous API usage patterns using statistical analysis
    and Isolation Forest.
    """
    
    def __init__(self):
        # Track request history per IP
        self.request_history: dict[str, list[dict]] = defaultdict(list)
        # Track failed login attempts per IP
        self.failed_logins: dict[str, list[datetime]] = defaultdict(list)
        # Isolation Forest model (trained on accumulated data)
        self.model = None
        self.is_trained = False
        # Thresholds
        self.max_requests_per_minute = 30
        self.max_failed_logins = 5
        self.suspicious_request_rate = 20  # requests per minute
        self.window_minutes = 5  # analysis window
    
    def record_request(self, ip: str, endpoint: str, user: str = "anonymous") -> None:
        """Record an incoming API request for analysis."""
        now = datetime.now(timezone.utc)
        self.request_history[ip].append({
            "timestamp": now,
            "endpoint": endpoint,
            "user": user
        })
        # Cleanup old entries (keep last 30 minutes)
        cutoff = now - timedelta(minutes=30)
        self.request_history[ip] = [
            r for r in self.request_history[ip] if r["timestamp"] > cutoff
        ]
    
    def record_failed_login(self, ip: str) -> None:
        """Record a failed login attempt."""
        now = datetime.now(timezone.utc)
        self.failed_logins[ip].append(now)
        # Cleanup old entries
        cutoff = now - timedelta(minutes=30)
        self.failed_logins[ip] = [
            t for t in self.failed_logins[ip] if t > cutoff
        ]
    
    def _extract_features(self, ip: str) -> list[float]:
        """
        Extract behavioral features for an IP address.
        Returns: [request_rate, unique_endpoints, failed_logins, burst_score]
        """
        now = datetime.now(timezone.utc)
        window = timedelta(minutes=self.window_minutes)
        
        # Get recent requests for this IP
        recent = [
            r for r in self.request_history.get(ip, [])
            if r["timestamp"] > now - window
        ]
        
        # Feature 1: Request rate (requests per minute)
        request_rate = len(recent) / max(self.window_minutes, 1)
        
        # Feature 2: Number of unique endpoints accessed
        unique_endpoints = len(set(r["endpoint"] for r in recent)) if recent else 0
        
        # Feature 3: Failed login count in window
        recent_failures = [
            t for t in self.failed_logins.get(ip, [])
            if t > now - window
        ]
        failed_login_count = len(recent_failures)
        
        # Feature 4: Burst score (max requests in any 30-second window)
        burst_score = 0
        if recent:
            for i, req in enumerate(recent):
                burst_window = [
                    r for r in recent
                    if 0 <= (r["timestamp"] - req["timestamp"]).total_seconds() <= 30
                ]
                burst_score = max(burst_score, len(burst_window))
        
        return [request_rate, unique_endpoints, failed_login_count, burst_score]
    
    def _train_model(self) -> None:
        """Train Isolation Forest on accumulated data."""
        try:
            from sklearn.ensemble import IsolationForest
            
            # Collect feature vectors from all IPs
            features = []
            for ip in self.request_history:
                feature_vec = self._extract_features(ip)
                features.append(feature_vec)
            
            if len(features) < 5:
                return  # Not enough data to train
            
            X = np.array(features)
            self.model = IsolationForest(
                n_estimators=50,
                contamination=0.1,
                random_state=42
            )
            self.model.fit(X)
            self.is_trained = True
        except Exception as e:
            print(f"Anomaly detection training error: {e}")
    
    def check_anomaly(self, ip: Optional[str] = None) -> dict:
        """
        Check for anomalous behavior from a specific IP or globally.
        
        Returns:
            dict with: threat_level ('normal', 'suspicious', 'critical'),
                       score (0-100), details, recommendations
        """
        if ip is None:
            return self._check_global_status()
        
        features = self._extract_features(ip)
        request_rate, unique_endpoints, failed_logins, burst_score = features
        
        # Rule-based scoring
        score = 0
        details = []
        recommendations = []
        
        # Check request rate
        if request_rate > self.max_requests_per_minute:
            score += 40
            details.append(f"High request rate: {request_rate:.1f} req/min (threshold: {self.max_requests_per_minute})")
            recommendations.append("Consider rate limiting this IP")
        elif request_rate > self.suspicious_request_rate:
            score += 20
            details.append(f"Elevated request rate: {request_rate:.1f} req/min")
        
        # Check failed logins
        if failed_logins >= self.max_failed_logins:
            score += 35
            details.append(f"Multiple failed logins: {failed_logins} attempts")
            recommendations.append("Consider temporarily blocking this IP")
        elif failed_logins >= 3:
            score += 15
            details.append(f"Several failed login attempts: {failed_logins}")
        
        # Check burst behavior
        if burst_score > 15:
            score += 45
            details.append(f"Burst activity detected: {burst_score} requests in 30s")
            recommendations.append("Possible automated attack - monitor closely")
        elif burst_score > 8:
            score += 20
            details.append(f"Moderate burst activity: {burst_score} requests in 30s")
        
        # Isolation Forest prediction (if model is trained)
        if self.is_trained and self.model is not None:
            try:
                prediction = self.model.predict([features])[0]
                if prediction == -1:  # Anomaly detected
                    score += 20
                    details.append("ML model flagged behavior as anomalous")
            except Exception:
                pass
        
        # Try to train/retrain model periodically
        total_requests = sum(len(v) for v in self.request_history.values())
        if total_requests > 10 and not self.is_trained:
            self._train_model()
        
        # Determine threat level
        score = min(score, 100)
        if score >= 70:
            threat_level = "critical"
        elif score >= 35:
            threat_level = "suspicious"
        else:
            threat_level = "normal"
        
        if not details:
            details.append("No anomalous behavior detected")
        if not recommendations:
            recommendations.append("No action required")
        
        return {
            "ip": ip,
            "threat_level": threat_level,
            "anomaly_score": score,
            "details": details,
            "recommendations": recommendations,
            "features": {
                "request_rate_per_min": round(request_rate, 2),
                "unique_endpoints": unique_endpoints,
                "failed_logins": failed_logins,
                "burst_score": burst_score
            },
            "model_status": "trained" if self.is_trained else "collecting_data"
        }
    
    def _check_global_status(self) -> dict:
        """Check overall security status across all tracked IPs."""
        total_ips = len(self.request_history)
        total_requests = sum(len(v) for v in self.request_history.values())
        total_failed = sum(len(v) for v in self.failed_logins.values())
        
        suspicious_ips = []
        for ip in self.request_history:
            result = self.check_anomaly(ip)
            if result["threat_level"] != "normal":
                suspicious_ips.append({
                    "ip": ip,
                    "threat_level": result["threat_level"],
                    "score": result["anomaly_score"]
                })
        
        overall_threat = "normal"
        if any(s["threat_level"] == "critical" for s in suspicious_ips):
            overall_threat = "critical"
        elif suspicious_ips:
            overall_threat = "suspicious"
        
        return {
            "overall_threat_level": overall_threat,
            "tracked_ips": total_ips,
            "total_requests": total_requests,
            "total_failed_logins": total_failed,
            "suspicious_ips": suspicious_ips,
            "model_status": "trained" if self.is_trained else "collecting_data"
        }
    
    def get_status(self) -> dict:
        """Get security system status summary."""
        return {
            "anomaly_detector": "active",
            "model_trained": self.is_trained,
            "tracked_ips": len(self.request_history),
            "total_requests_tracked": sum(len(v) for v in self.request_history.values()),
            "total_failed_logins_tracked": sum(len(v) for v in self.failed_logins.values())
        }


# Global anomaly detector instance
anomaly_detector = AnomalyDetector()
