"""
FinShield AI — ML Model Training Script
=========================================
Trains all fraud detection models on the seed dataset.

Run from backend directory:
    cd backend
    python scripts/train_models.py

Reads:
    data/samples/transactions_10000.csv
    data/samples/customers_100.csv

Outputs:
    app/ml/models/anomaly_detector_v1.pkl
    app/ml/models/fraud_classifier_v1.pkl
    app/ml/models/ensemble_scorer_v1.pkl
    app/ml/models/shap_explainer_v1.pkl
    app/ml/models/feature_names_v1.json
    app/ml/models/evaluation_report.json
    app/ml/models/model_registry.json
"""

import json
import os
import sys
import time

import numpy as np

# ── Path setup ────────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app", "ml", "models")
os.makedirs(MODELS_DIR, exist_ok=True)

from app.ml.feature_engineering import batch_features  # noqa: E402
from app.ml.anomaly_detector    import AnomalyDetector  # noqa: E402
from app.ml.fraud_classifier    import FraudClassifier  # noqa: E402
from app.ml.risk_scorer         import EnsembleScorer  # noqa: E402
from app.ml.explainability      import SHAPExplainer  # noqa: E402
from app.ml.model_registry      import ModelRegistry  # noqa: E402
from app.ml.training.data_prep  import load_data, split_data, get_class_weight  # noqa: E402
from app.ml.training.evaluate   import evaluate_model, save_evaluation_report  # noqa: E402


def main():
    t_start = time.time()

    print("\n" + "="*60)
    print("  FinShield AI — ML Model Training Pipeline")
    print("="*60)

    # ── Step 1: Load data ─────────────────────────────────────────────────────
    print("\n[1/7] Loading data...")
    txn_df, cust_df = load_data()

    # ── Step 2: Feature engineering ───────────────────────────────────────────
    print("\n[2/7] Engineering features (this takes ~30 seconds for 10K rows)...")
    t0 = time.time()
    X, feat_cols, sorted_idx = batch_features(txn_df, cust_df)
    # IMPORTANT: re-align labels to the same sorted order as X
    y = txn_df["is_fraud"].values[sorted_idx].astype(np.int32)

    print(f"  Feature matrix: {X.shape}  ({len(feat_cols)} features, {X.shape[0]:,} samples)")
    print(f"  Feature engineering: {time.time()-t0:.1f}s")

    # Save feature names for inference
    feat_path = os.path.join(MODELS_DIR, "feature_names_v1.json")
    with open(feat_path, "w") as f:
        json.dump(feat_cols, f, indent=2)
    print(f"  Saved feature names -> {feat_path}")

    # ── Step 3: Train/test split ──────────────────────────────────────────────
    print("\n[3/7] Splitting data...")
    X_train, X_test, y_train, y_test = split_data(X, y, test_size=0.20)
    scale_pos_w = get_class_weight(y_train)
    print(f"  scale_pos_weight: {scale_pos_w} (for class imbalance)")

    # ── Step 4: Train anomaly detectors (Layer 2) ──────────────────────────────
    print("\n[4/7] Training unsupervised anomaly detectors (Layer 2)...")
    t0 = time.time()
    # Train on legitimate transactions only (true anomaly detection)
    X_legit = X_train[y_train == 0]
    anomaly_detector = AnomalyDetector(contamination=0.03)
    anomaly_detector.fit(X_legit)
    anomaly_detector.save()
    print(f"  Anomaly detector trained on {len(X_legit):,} legit transactions  ({time.time()-t0:.1f}s)")

    # ── Step 5: Train supervised classifiers (Layer 3) ────────────────────────
    print("\n[5/7] Training supervised fraud classifiers (Layer 3)...")
    t0 = time.time()
    fraud_classifier = FraudClassifier(scale_pos_weight=scale_pos_w)
    fraud_classifier.fit(X_train, y_train)
    fraud_classifier.save()
    print(f"  Classifiers trained  ({time.time()-t0:.1f}s)")

    # ── Step 6: Evaluate ──────────────────────────────────────────────────────
    print("\n[6/7] Evaluating on test set...")

    # Get predictions
    supervised_proba = fraud_classifier.predict_proba(X_test)
    anomaly_scores   = anomaly_detector.score(X_test)

    # Combine as a simple ensemble (no rules at training time)
    ensemble_proba = np.clip(
        0.70 * supervised_proba + 0.30 * anomaly_scores, 0, 1
    )

    metrics = evaluate_model(
        y_true=y_test,
        y_pred_proba=ensemble_proba,
        threshold=0.30,   # tuned for recall vs precision balance on 3% fraud rate
        model_name="finshield_ensemble_v1",
        feature_count=len(feat_cols),
        training_samples=len(X_train),
    )
    save_evaluation_report(metrics)

    # ── Step 7: SHAP + ensemble + registry ────────────────────────────────────
    print("\n[7/7] Building SHAP explainer + registering models...")

    # SHAP explainer
    try:
        shap_explainer = SHAPExplainer.build(fraud_classifier, X_train[:500], feat_cols)
        shap_explainer.save()
        # Print global top-10 features
        X_train_scaled = fraud_classifier.scaler.transform(X_train[:500])
        top_features = shap_explainer.global_importance(X_train_scaled, top_n=10)
        print("\n  Top 10 fraud-contributing features (global SHAP):")
        for f in top_features:
            bar = "#" * int(f["mean_abs_shap"] * 50)
            print(f"  {f['rank']:>2}. {f['feature']:<30} {f['mean_abs_shap']:.4f}  {bar}")
    except Exception as e:
        print(f"  [!] SHAP explainer skipped: {e}")

    # Save ensemble scorer
    ensemble_scorer = EnsembleScorer()
    ensemble_scorer.save()

    # Register all models
    registry = ModelRegistry()
    registry.register(
        model_name="anomaly_detector",
        model_type="anomaly_detector",
        version="v1",
        artifact_path=os.path.join(MODELS_DIR, "anomaly_detector_v1.pkl"),
        metrics={"f1_score": 0.0, "auc_roc": 0.0, "training_samples": len(X_legit), "feature_count": len(feat_cols)},
        status="active",
    )
    registry.register(
        model_name="fraud_classifier",
        model_type="fraud_classifier",
        version="v1",
        artifact_path=os.path.join(MODELS_DIR, "fraud_classifier_v1.pkl"),
        metrics={**metrics, "training_samples": len(X_train), "feature_count": len(feat_cols)},
        status="active",
    )
    registry.register(
        model_name="ensemble_scorer",
        model_type="ensemble",
        version="v1",
        artifact_path=os.path.join(MODELS_DIR, "ensemble_scorer_v1.pkl"),
        metrics={**metrics, "training_samples": len(X_train), "feature_count": len(feat_cols)},
        status="active",
    )
    registry.print_summary()

    # ── Summary ───────────────────────────────────────────────────────────────
    elapsed = time.time() - t_start
    print("\n" + "="*60)
    print("  TRAINING COMPLETE")
    print("="*60)
    print(f"  Total time:      {elapsed:.1f}s")
    print(f"  Features:        {len(feat_cols)}")
    print(f"  Training rows:   {len(X_train):,}")
    print(f"  F1 Score:        {metrics['f1_score']:.4f}")
    print(f"  AUC-ROC:         {metrics['auc_roc']:.4f}")
    print(f"  Precision:       {metrics['precision']:.4f}")
    print(f"  Recall:          {metrics['recall']:.4f}")
    print(f"\n  Models saved to: {MODELS_DIR}/")
    print("    anomaly_detector_v1.pkl")
    print("    fraud_classifier_v1.pkl  (XGBoost + RF + NN)")
    print("    ensemble_scorer_v1.pkl")
    print("    shap_explainer_v1.pkl")
    print(f"    feature_names_v1.json   ({len(feat_cols)} features)")
    print("    evaluation_report.json")
    print("    model_registry.json")
    print("="*60 + "\n")
    print("  Next: python scripts/upload_to_supabase.py  (if not done yet)")
    print("        Then proceed to Step 5 — API + Frontend wiring\n")


if __name__ == "__main__":
    main()
