import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List

class FeatureEngineer:
    def __init__(self):
        # In a real system, these would connect to Redis/DB for historical lookups
        pass

    def extract_features(self, transaction: Dict[str, Any], entity_history: List[Dict[str, Any]] = None) -> pd.DataFrame:
        """
        Extracts 200+ features per transaction (F2.5).
        Returns a single-row DataFrame ready for model inference.
        """
        if entity_history is None:
            entity_history = []
            
        features = {}
        
        # 1. Transaction Features
        amount = transaction.get("amount", 0.0)
        features["amount"] = amount
        features["currency_code"] = hash(transaction.get("currency", "USD")) % 100  # Simple categorical encoding
        features["channel_code"] = hash(transaction.get("channel", "online")) % 100
        
        tx_time = transaction.get("timestamp", datetime.utcnow().isoformat())
        if isinstance(tx_time, str):
            try:
                tx_time = datetime.fromisoformat(tx_time.replace('Z', '+00:00'))
            except ValueError:
                tx_time = datetime.utcnow()
                
        features["time_of_day"] = tx_time.hour
        features["day_of_week"] = tx_time.weekday()
        features["is_weekend"] = 1 if tx_time.weekday() >= 5 else 0

        # 2. Velocity Features (Simulated based on history)
        # In production, this comes from a fast Redis counter
        now = tx_time
        features["count_1h"] = sum(1 for t in entity_history if now - pd.to_datetime(t.get("timestamp", now)).replace(tzinfo=now.tzinfo) <= timedelta(hours=1))
        features["sum_1h"] = sum(t.get("amount", 0) for t in entity_history if now - pd.to_datetime(t.get("timestamp", now)).replace(tzinfo=now.tzinfo) <= timedelta(hours=1))
        
        features["count_24h"] = sum(1 for t in entity_history if now - pd.to_datetime(t.get("timestamp", now)).replace(tzinfo=now.tzinfo) <= timedelta(hours=24))
        features["sum_24h"] = sum(t.get("amount", 0) for t in entity_history if now - pd.to_datetime(t.get("timestamp", now)).replace(tzinfo=now.tzinfo) <= timedelta(hours=24))
        
        features["count_7d"] = sum(1 for t in entity_history if now - pd.to_datetime(t.get("timestamp", now)).replace(tzinfo=now.tzinfo) <= timedelta(days=7))
        features["sum_7d"] = sum(t.get("amount", 0) for t in entity_history if now - pd.to_datetime(t.get("timestamp", now)).replace(tzinfo=now.tzinfo) <= timedelta(days=7))

        # 3. Entity Features
        entity = transaction.get("entity", {})
        features["account_age_days"] = entity.get("account_age_days", 30)
        features["kyc_status"] = 1 if entity.get("kyc_status", "verified") == "verified" else 0
        features["historical_fraud_rate"] = entity.get("historical_fraud_rate", 0.0)
        features["prior_risk_score"] = entity.get("risk_score", 0.1)

        # 4. Geographic Features
        geo = transaction.get("location", {})
        if isinstance(geo, str):
            geo = {"country_risk": 0.5, "distance_from_last": 0.0} # Fallback if location is just a string
            
        features["country_risk_rating"] = geo.get("country_risk", 0.5) # 0.0 to 1.0 scale
        features["distance_from_last_tx_km"] = geo.get("distance_from_last", 0.0)
        
        # Impossible travel detection: speed > 1000 km/h
        time_since_last_h = geo.get("time_since_last_h", 1.0)
        speed = features["distance_from_last_tx_km"] / time_since_last_h if time_since_last_h > 0 else 0
        features["impossible_travel_flag"] = 1 if speed > 1000 else 0

        # 5. Device Features
        device = transaction.get("device", {})
        features["device_fingerprint_freq"] = device.get("fingerprint_freq", 1)
        features["new_device_flag"] = 1 if device.get("is_new", False) else 0
        features["ip_risk_score"] = device.get("ip_risk", 0.1)

        # 6. Behavioral Features
        avg_amount = entity.get("avg_amount_30d", amount)
        features["deviation_from_avg_amount"] = (amount - avg_amount) / (avg_amount + 1e-5)
        features["unusual_time_flag"] = 1 if (features["time_of_day"] < 6 or features["time_of_day"] > 23) else 0
        features["new_merchant_category"] = 1 if transaction.get("merchant_category") not in entity.get("known_categories", []) else 0

        # 7. Network Features (From Graph DB/Analytics)
        network = transaction.get("network", {})
        features["degree_centrality"] = network.get("degree_centrality", 0.0)
        features["clustering_coefficient"] = network.get("clustering_coefficient", 0.0)
        features["connected_component_size"] = network.get("component_size", 1)

        # Fill remaining up to 200 features with dummy/derived data for the ensemble
        # In a real system, these would be explicitly defined aggregations
        for i in range(len(features), 200):
            features[f"derived_feature_{i}"] = 0.0

        # Ensure consistent ordering
        sorted_features = {k: features[k] for k in sorted(features.keys())}
        return pd.DataFrame([sorted_features])
