import numpy as np
from app.ml.registry import registry
from app.ml.feature_engineering import FeatureEngineer
from app.ml.classifier import FraudClassifierEnsemble
from app.ml.anomaly_detector import AnomalyDetector
from app.ml.behavioral_profiler import BehavioralProfiler
from app.ml.network_analyzer import NetworkAnalyzer
from app.ml.explainability import ExplainabilityEngine

class FraudDetectionService:
    def __init__(self):
        self.feature_engineer = FeatureEngineer()
        self.classifier = FraudClassifierEnsemble()
        self.anomaly_detector = AnomalyDetector()
        self.behavioral_profiler = BehavioralProfiler()
        self.network_analyzer = NetworkAnalyzer()
        self.explainer = ExplainabilityEngine()

    def detect_fraud(self, transaction_data: dict) -> dict:
        """
        Main entry point for fraud detection pipeline.
        Combines ML models, behavioral analysis, network analysis, and rules.
        """
        # 1. Feature Engineering
        features_df = self.feature_engineer.extract_features(transaction_data)
        amount = transaction_data.get("amount", 0.0)
        
        # 2. ML Inference (F2.1, F2.2)
        # In a real system, we would load active models from the registry
        mock_model = None
        ml_score_tuple = self.classifier.predict(features_df)
        ml_score = float(ml_score_tuple[0]) if isinstance(ml_score_tuple, tuple) else float(ml_score_tuple)
        
        anomaly_score_tuple = self.anomaly_detector.detect(features_df)
        anomaly_score = float(anomaly_score_tuple[0]) if isinstance(anomaly_score_tuple, tuple) else float(anomaly_score_tuple)
        
        # 3. Behavioral & Network Analysis (F2.3, F2.4)
        # In a real system, we'd fetch entity history and graph context from DB/Cache
        mock_history = [{"amount": 100.0}, {"amount": 150.0}] if amount < 5000 else [{"amount": 5000.0}]
        behavioral_score = float(self.behavioral_profiler.profile(transaction_data, mock_history))
        
        mock_graph_context = {"known_fraud_nodes": [], "shared_devices": 0}
        source_entity = transaction_data.get("source_entity_id", "unknown")
        target_entity = transaction_data.get("target_entity_id", "unknown")
        network_score = float(self.network_analyzer.analyze(source_entity, target_entity, mock_graph_context))
        
        # 4. Explainability (F2.6)
        explanations = self.explainer.explain(features_df)
        
        # 5. Rule Evaluation (Mocked for now)
        # In a real system, we would call the Rules Engine
        rule_score = 0.0
        triggered_rules = []
        
        if amount > 10000:
            rule_score = 0.8
            triggered_rules.append("High Amount Violation")
            
        # 6. Risk Aggregation (Weighted combination)
        # Combine ML, Anomaly, Behavioral, Network, and Rule scores
        weights = {
            "ml": 0.4,
            "anomaly": 0.2,
            "behavioral": 0.2,
            "network": 0.2
        }
        
        aggregated_ml_score = (
            (ml_score * weights["ml"]) + 
            (anomaly_score * weights["anomaly"]) + 
            (behavioral_score * weights["behavioral"]) + 
            (network_score * weights["network"])
        )
        
        # Final score is the max of the aggregated ML score and the rules score
        # Rules can act as hard overrides (e.g., if rule says 1.0, score is 1.0)
        composite_score = max(aggregated_ml_score, rule_score)
        
        # Determine Status
        status = "PASS"
        if composite_score > 0.8:
            status = "BLOCK"
        elif composite_score > 0.6:
            status = "ALERT"
        elif composite_score > 0.3:
            status = "FLAG"
            
        return {
            "transaction_id": transaction_data.get("id", "unknown"),
            "status": status,
            "risk_score": composite_score,
            "components": {
                "ml_score": ml_score,
                "anomaly_score": anomaly_score,
                "behavioral_score": behavioral_score,
                "network_score": network_score,
                "rule_score": rule_score
            },
            "triggered_rules": triggered_rules,
            "explanations": explanations,
            "features_used": len(features_df.columns)
        }

# For backward compatibility with existing code during refactor
def get_fraud_score(transaction_data):
    return FraudDetectionService().classifier.predict(FeatureEngineer().extract_features(transaction_data))

def get_anomaly_score(transaction_data):
    return FraudDetectionService().anomaly_detector.detect(FeatureEngineer().extract_features(transaction_data))

def detect_fraud(transaction_data):
    return FraudDetectionService().detect_fraud(transaction_data)
