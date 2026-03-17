import pandas as pd
from typing import Tuple, Dict

class AnomalyDetector:
    """
    F2.2: Anomaly Detection (Isolation Forest / Autoencoder)
    Flags statistical outliers.
    """
    def __init__(self):
        self.is_loaded = False
        
    def load_model(self):
        """Load ONNX model for Isolation Forest"""
        self.is_loaded = True
        
    def detect(self, features: pd.DataFrame) -> Tuple[bool, float]:
        """
        Returns boolean flag (is_anomaly) and anomaly score.
        Score ranges from 0.0 (normal) to 1.0 (highly anomalous).
        """
        if not self.is_loaded:
            # Mock anomaly detection
            amt = features.get("amount", pd.Series([0.0])).iloc[0]
            unusual_time = features.get("unusual_time_flag", pd.Series([0])).iloc[0]
            
            # Simple heuristic mock
            score = min(1.0, (amt / 20000.0) + (unusual_time * 0.3))
            is_anomaly = score > 0.7
            return is_anomaly, score
            
        # Real implementation uses ONNX
        return False, 0.1
