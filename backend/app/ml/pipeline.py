"""
FinShield AI — Live Fraud Scoring Pipeline
============================================
Loads trained models from disk and scores transactions at runtime.

Used by the API: POST /api/v1/transactions (and Test Me tab).

Usage:
    pipeline = FraudScoringPipeline.get_instance()
    result   = pipeline.score_transaction(transaction_dict, customer_dict, recent_txns_list)
"""

import json
import os
import time
from typing import Optional

import pandas as pd


MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")


class FraudScoringPipeline:
    """
    Singleton pipeline that holds loaded models in memory.

    score_transaction() takes a single transaction + customer context
    and returns a complete FraudDecision within the target <100ms.
    """

    _instance: Optional["FraudScoringPipeline"] = None

    def __init__(self):
        self._anomaly_detector = None
        self._fraud_classifier = None
        self._ensemble_scorer = None
        self._shap_explainer = None
        self._feature_names: list[str] = []
        self._loaded = False

    @classmethod
    def get_instance(cls) -> "FraudScoringPipeline":
        """Return the singleton pipeline (loads models on first call)."""
        if cls._instance is None:
            cls._instance = cls()
            cls._instance._load_models()
        return cls._instance

    def _load_models(self):
        """Load all trained models from disk."""
        import pickle

        def _load_pkl(name: str):
            path = os.path.join(MODELS_DIR, name)
            if not os.path.exists(path):
                return None
            with open(path, "rb") as f:
                return pickle.load(f)

        print("  [Pipeline] Loading trained models...")
        self._anomaly_detector = _load_pkl("anomaly_detector_v1.pkl")
        self._fraud_classifier = _load_pkl("fraud_classifier_v1.pkl")
        self._ensemble_scorer = _load_pkl("ensemble_scorer_v1.pkl")
        self._shap_explainer = _load_pkl("shap_explainer_v1.pkl")

        feat_path = os.path.join(MODELS_DIR, "feature_names_v1.json")
        if os.path.exists(feat_path):
            with open(feat_path) as f:
                self._feature_names = json.load(f)

        loaded = [
            "anomaly_detector" if self._anomaly_detector else None,
            "fraud_classifier" if self._fraud_classifier else None,
            "ensemble_scorer" if self._ensemble_scorer else None,
        ]
        loaded = [m for m in loaded if m]
        print(f"  [Pipeline] Loaded: {', '.join(loaded) or 'NONE — run train_models.py first'}")
        self._loaded = bool(loaded)

    @property
    def is_ready(self) -> bool:
        return self._loaded and self._fraud_classifier is not None

    # ── Main scoring entry point ──────────────────────────────────────────────

    def score_transaction(
        self,
        transaction: dict,
        customer: dict,
        recent_transactions: list[dict],
        rules_score: float = 0.0,
        triggered_rules: list[str] | None = None,
    ) -> dict:
        """
        Score a single transaction.

        Parameters
        ----------
        transaction        : The incoming transaction dict
        customer           : Customer profile dict
        recent_transactions: List of customer's recent transactions (last 30 days)
        rules_score        : Pre-computed rules engine score (0–1)
        triggered_rules    : List of rule IDs triggered

        Returns
        -------
        dict with fraud_score, fraud_category, fraud_risk_level, decision,
             triggered_rules, shap_explanation, processing_ms
        """
        t0 = time.time()

        if not self.is_ready:
            # Fallback: ML models not loaded — ensemble scorer will
            # detect all-zero ML inputs and switch to rules-dominant mode
            from app.ml.risk_scorer import EnsembleScorer

            scorer = EnsembleScorer()
            decision = scorer.score(
                rules_score=rules_score,
                anomaly_score=0.0,
                xgb_score=0.0,
                rf_score=0.0,
                nn_score=0.0,
                triggered_rules=triggered_rules,
            )
            result = self._format_result(decision, [], time.time() - t0)
            result["model_version"] = "rules_only_v1"
            return result

        try:
            # Build a small DataFrame for feature engineering
            all_txns = recent_transactions + [transaction]
            txn_df = pd.DataFrame(all_txns)
            cust_df = pd.DataFrame([customer]).rename(
                columns={
                    "customer_id": "customer_id",
                    "risk_score": "risk_score",
                    "customer_tier": "customer_tier",
                    "balance_amount": "balance_amount",
                    "kyc_level": "kyc_level",
                    "profile_type": "profile_type",
                    "card_network": "card_network",
                    "card_status": "card_status",
                }
            )

            from app.ml.feature_engineering import batch_features

            X, _, _ = batch_features(txn_df, cust_df)

            # Use the last row (= the current transaction)
            x = X[-1:]

            # Layer 2: Anomaly score
            anomaly_score = (
                float(self._anomaly_detector.score(x)[0]) if self._anomaly_detector else 0.0
            )

            # Layer 3: Supervised classifier
            supervised_score, detail = self._fraud_classifier.predict_single(x[0])
            xgb_score = detail.get("xgboost", 0.0)
            rf_score = detail.get("random_forest", 0.0)
            nn_score = detail.get("neural_network", 0.0)

            # Layer 4: Ensemble
            from app.ml.risk_scorer import EnsembleScorer

            scorer = self._ensemble_scorer or EnsembleScorer()
            decision = scorer.score(
                rules_score=rules_score,
                anomaly_score=anomaly_score,
                xgb_score=xgb_score,
                rf_score=rf_score,
                nn_score=nn_score,
                triggered_rules=triggered_rules,
            )

            # SHAP explanation
            shap_explanation = []
            if self._shap_explainer:
                try:
                    x_scaled = self._fraud_classifier.scaler.transform(x)
                    shap_explanation = self._shap_explainer.explain(x_scaled[0], top_n=5)
                    shap_explanation = [
                        {
                            "feature": fc.feature_name,
                            "shap_value": fc.shap_value,
                            "direction": fc.direction,
                        }
                        for fc in shap_explanation
                    ]
                except Exception:
                    shap_explanation = []

            return self._format_result(decision, shap_explanation, time.time() - t0)

        except Exception as e:
            # Graceful degradation: if feature engineering fails, use rules only
            # EnsembleScorer will detect all-zero ML inputs and use rules-dominant mode
            from app.ml.risk_scorer import EnsembleScorer

            scorer = EnsembleScorer()
            decision = scorer.score(
                rules_score=rules_score,
                anomaly_score=0.0,
                xgb_score=0.0,
                rf_score=0.0,
                nn_score=0.0,
                triggered_rules=triggered_rules,
            )
            result = self._format_result(decision, [], time.time() - t0)
            result["error"] = str(e)
            result["model_version"] = "rules_only_v1"
            return result

    @staticmethod
    def _format_result(decision, shap_explanation: list, elapsed: float) -> dict:
        """Convert FraudDecision to API-ready dict."""
        return {
            "fraud_score": decision.fraud_score,
            "fraud_category": decision.fraud_category,
            "fraud_risk_level": decision.fraud_risk_level,
            "decision": decision.decision,
            "rules_score": decision.rules_score,
            "anomaly_score": decision.anomaly_score,
            "xgb_score": decision.xgb_score,
            "rf_score": decision.rf_score,
            "nn_score": decision.nn_score,
            "triggered_rules": decision.triggered_rules,
            "shap_explanation": shap_explanation,
            "confidence": decision.confidence,
            "processing_ms": round(elapsed * 1000, 1),
            "model_version": "ensemble_v1",
        }
