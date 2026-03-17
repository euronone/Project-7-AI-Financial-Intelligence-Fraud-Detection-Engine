import numpy as np
import xgboost as xgb
from sklearn.neural_network import MLPClassifier
from typing import Dict, Any, Tuple
import pandas as pd

class FraudClassifierEnsemble:
    """
    F2.1: Fraud Classifier — XGBoost + Neural Network ensemble model.
    Outputs fraud probability (0.0–1.0) per transaction.
    """
    def __init__(self):
        # In a real system, these models would be loaded via ONNX Runtime (F2.9)
        # Here we mock the behavior for the architecture setup.
        self.xgb_model = None
        self.nn_model = None
        self.is_loaded = False

    def load_models(self, registry_path: str = "models/"):
        """Simulate loading pre-trained models from the registry"""
        self.is_loaded = True
        # Actual implementation would use onnxruntime.InferenceSession

    def predict(self, features: pd.DataFrame) -> Tuple[float, Dict[str, float]]:
        """
        Returns ensemble probability and individual model scores.
        """
        if not self.is_loaded:
            # Mock prediction if models aren't loaded
            # Use a few features to generate a deterministic mock score
            amt = features.get("amount", pd.Series([0.0])).iloc[0]
            dist = features.get("distance_from_last_tx_km", pd.Series([0.0])).iloc[0]
            
            xgb_score = min(1.0, (amt / 10000.0) + (dist / 5000.0))
            nn_score = min(1.0, (amt / 12000.0) + (dist / 4000.0))
        else:
            # Actual ONNX inference would happen here
            xgb_score = 0.1
            nn_score = 0.15

        # Ensemble logic (e.g., weighted average)
        ensemble_score = (xgb_score * 0.6) + (nn_score * 0.4)
        
        return ensemble_score, {
            "xgb_probability": xgb_score,
            "nn_probability": nn_score
        }
