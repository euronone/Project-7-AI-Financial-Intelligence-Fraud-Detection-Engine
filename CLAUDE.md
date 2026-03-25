# FinShield AI – Fintech Fraud Detection Platform
## Complete System Design & Developer Guide (`CLAUDE.md`)

> **Single source of truth** for all development, architecture, and product decisions.
> This document governs the entire FinShield AI platform — a multi-tenant, ML-powered fraud detection system for banks, fintech companies, and insurance providers.

---

## 📋 Table of Contents

1. [Platform Overview & Landing Page Design](#platform-overview--landing-page-design)
2. [Subscription Plans & Signup Flow](#subscription-plans--signup-flow)
3. [Login & User Dashboard](#login--user-dashboard)
4. [Sample Data Generation](#sample-data-generation)
5. [ML Model Training on Sample Data](#ml-model-training-on-sample-data)
6. [Database Architecture](#database-architecture)
7. [Data Integration & Connectors (10–20 Sources)](#data-integration--connectors)
8. [Fraud Detection Logic & Thresholds](#fraud-detection-logic--thresholds)
9. [ML Modeling Strategy (Multi-Layered)](#ml-modeling-strategy)
10. [Post-Detection Actions & Alerts](#post-detection-actions--alerts)
11. [Scalability Across Institutions](#scalability-across-institutions)
12. [Admin Dashboard & System Monitoring](#admin-dashboard--system-monitoring)
13. [Settings & API Keys Management](#settings--api-keys-management)
14. [Test Me Tab – Full Transaction Journey](#test-me-tab)
15. [API Architecture](#api-architecture)
16. [Technology Stack](#technology-stack)
17. [Local Development Setup](#local-development-setup)
18. [Testing Strategy](#testing-strategy)
19. [Implementation Roadmap](#implementation-roadmap)
20. [Coding Conventions](#coding-conventions)
21. [Glossary](#glossary)

---

## 🌐 Platform Overview & Landing Page Design

### Design Philosophy

The landing page must be **professional, dark-themed (#0A0A0F background), and section-by-section informative**. Each section uses a ribbon/band layout. One dedicated section serves as a **Project Guide** — explaining the platform purpose, how it works, and use cases for different institution types.

### Landing Page Sections (Ribbon Layout)

#### Section 1 — Hero Ribbon
- **Purpose:** First impression, value proposition
- **Content:**
  - Headline: "Stop Fraud Before It Happens — FinShield AI"
  - Sub-headline: "Real-time ML-powered fraud detection for banks, fintechs, and insurance companies"
  - CTA buttons: `Get Started Free` | `View Demo`
  - Animated background: flowing transaction graph (D3.js or CSS animation)
- **Design:** Full-viewport height, dark gradient, floating card showing live fraud score widget

#### Section 2 — 🔖 Project Guide (Dedicated Ribbon — Required)
- **Purpose:** Explain what the platform is, how to use it, and who it's for
- **Content Structure:**

```
📖 WHAT IS FINSHIELD AI?
FinShield AI is an end-to-end fraud detection platform designed for financial
institutions. It connects to your customer and transaction databases, trains
ML models on your historical data, and provides real-time fraud scoring,
alerting, and case management tools.

🏦 WHO IS IT FOR?
- Banks & Credit Unions: Detect fraudulent card transactions and account takeovers
- Fintech Startups: Add fraud detection without building ML infrastructure
- Insurance Companies: Identify claim fraud patterns from transaction data
- Payment Processors: Screen transactions before settlement

🔄 HOW DOES IT WORK? (Step-by-step)
Step 1: Sign Up — Choose your subscription plan (Free / Pro / Advanced)
Step 2: Connect Data — Provide API keys or DB credentials for your
        Customer DB and Transaction DB
Step 3: First-Run Model Training — System auto-trains ML models on your data
        and creates a `fraud_category` column in your transactions table
Step 4: Real-Time Scoring — Every new transaction is scored by the ML engine
Step 5: Alerts — Suspicious transactions trigger automated alerts
        (SMS/email/call/in-app)
Step 6: Investigate — Use the dashboard to review alerts, manage cases,
        and mark outcomes
Step 7: Retrain — Models improve with feedback from confirmed fraud/non-fraud

🎯 USE CASES BY INSTITUTION TYPE:
| Institution     | Primary Use Case                               |
|-----------------|------------------------------------------------|
| Retail Bank     | Card-not-present fraud, impossible travel      |
| Neobank         | Account takeover, identity fraud               |
| Insurance       | Claim fraud from spending pattern changes      |
| Payment Gateway | Real-time transaction screening                |
| Fintech Lending | Loan application fraud, velocity patterns      |
```

#### Section 3 — How It Works (Visual Flow)
- 6-step animated pipeline visualization
- Steps: Connect → Ingest → Detect → Alert → Investigate → Improve
- Each step with icon, title, and 2-line description

#### Section 4 — Features Grid Ribbon
- 3×2 cards grid, dark card style with colored icon per card:
  - 🤖 Multi-Layer ML Detection
  - ⚡ Real-Time Scoring (<100ms)
  - 🔌 20+ Data Connectors
  - 📊 Live Admin Dashboard
  - 🔔 Multi-Channel Alerts (SMS/Email/Call)
  - 🏢 Multi-Tenant Architecture

#### Section 5 — Subscription Plans Ribbon
- Three plan cards with comparison table (see Section 2 below)
- Dark card with glow border (green for Pro, purple for Advanced)

#### Section 6 — Architecture Diagram Ribbon
- Interactive system architecture diagram
- Layers: Data Sources → Ingestion → Feature Engineering → ML Engine → Action Layer → Dashboard

#### Section 7 — Fraud Detection Logic Ribbon
- Explain detection layers with thresholds (Rules → ML → Ensemble)
- Show sample fraud score gauge (animated)
- Use cases: velocity spike, impossible travel, device anomaly

#### Section 8 — Security & Compliance Ribbon
- ISO 27001, SOC 2, GDPR, PCI-DSS badges
- Data isolation details (per-tenant schemas)
- Encryption at rest and in transit

#### Section 9 — Testimonials / Metrics Ribbon
- Animated counters: Transactions Processed, Fraud Caught, Institutions Served
- Quote cards from fictional institution personas

#### Section 10 — CTA Footer Ribbon
- Final call to action: Sign Up / Contact Sales
- Links: Documentation, GitHub, Support

### Frontend Implementation Notes

```tsx
// app/landing/page.tsx — Next.js 14 App Router
// All sections use Tailwind CSS dark theme
// Background: bg-[#0A0A0F]
// Text: text-white / text-gray-300
// Accent colors: 
//   - Green: #00FF87 (fraud safe / free plan)
//   - Blue: #3B82F6 (data / pro plan)
//   - Purple: #8B5CF6 (advanced plan)
//   - Red: #EF4444 (fraud alert indicators)
// Card background: bg-[#111118] with border border-[#1E1E2E]
// Section ribbon: alternating bg-[#0A0A0F] and bg-[#0D0D15]

// Ribbon section template:
export function RibbonSection({ id, title, children, variant = "dark" }) {
  return (
    <section
      id={id}
      className={`py-20 px-6 ${variant === "dark" ? "bg-[#0A0A0F]" : "bg-[#0D0D15]"}`}
    >
      <div className="max-w-7xl mx-auto">
        <h2 className="text-3xl font-bold text-white mb-4">{title}</h2>
        {children}
      </div>
    </section>
  )
}
```

---

## 💳 Subscription Plans & Signup Flow

### Three Subscription Tiers

| Feature | Free | Pro (₹9,999/mo) | Advanced (₹24,999/mo) |
|---------|------|-----------------|----------------------|
| **Data Schema** | FinShield standard schema | FinShield standard schema | **Custom schema** (define your own column names) |
| **ML Models** | Pre-built FinShield models | Pre-built FinShield models | **Personalized ML model** trained on your custom schema |
| **Transactions/Month** | 10,000 | 500,000 | Unlimited |
| **Connectors** | 2 (Supabase + CSV) | 10 connectors | All 20+ connectors |
| **Fraud Rules** | 5 built-in rules | 25 rules (custom) | Unlimited custom rules |
| **Notifications** | Email only | Email + SMS | Email + SMS + Call + Webhook |
| **Model Retraining** | Monthly (automated) | Weekly | On-demand + scheduled |
| **Admin Dashboard** | Basic metrics | Full analytics | Full + white-label |
| **API Access** | Read-only | Full REST API | Full API + WebSocket |
| **Support** | Community | Email (48h) | Dedicated SLA |
| **Data Isolation** | Shared schema | Dedicated schema | Dedicated schema + VPC |
| **Custom Thresholds** | No | Yes | Yes + per-rule config |
| **Model Explainability** | No | SHAP summaries | Full SHAP + audit trail |

### Signup Flow (Step-by-Step)

```
STEP 1: Institution Details
  ├─ Institution name, type (Bank / Fintech / Insurance / Payment Processor)
  ├─ Primary contact email
  ├─ Password (with confirmation)
  └─ Country / Regulatory jurisdiction

STEP 2: Select Subscription Plan
  ├─ Show three plan cards (Free / Pro / Advanced)
  ├─ Highlight recommended plan
  └─ Payment integration for Pro/Advanced (Razorpay for INR billing)

STEP 3: Database Schema Selection
  ├─ For Free/Pro: Select from FinShield standard schema
  │     └─ System shows pre-defined columns — user confirms mapping
  ├─ For Advanced: Define custom schema
  │     ├─ Upload CSV sample or define column names manually
  │     ├─ Map required fields: customer_id, amount, timestamp, location
  │     └─ System auto-generates personalized ML feature pipeline

STEP 4: Connect Data Sources
  ├─ Customer Database API Key / Connection String
  │     └─ Supported: Supabase URL + anon key / PostgreSQL / MySQL / API endpoint
  ├─ Transaction Database API Key / Connection String
  │     └─ Supported: same as above
  └─ Test connection (system runs a sample query to verify)

STEP 5: First-Run Initialization
  ├─ System pulls existing transaction data (up to 90 days)
  ├─ Trains ML models on historical data (background job)
  ├─ Creates new column `fraud_category` in transaction table
  │     Values: 'legitimate' | 'suspicious' | 'fraudulent' | 'unscored'
  ├─ Creates `fraud_score` column (0.0–1.0)
  └─ Shows progress bar to user: "Initializing your fraud detection engine..."

STEP 6: Dashboard Redirect
  └─ User lands on their personalized dashboard with initial fraud stats
```

### Advanced Plan — Custom Schema Flow

```python
# When Advanced user defines custom schema:

class CustomSchemaBuilder:
    """
    For Advanced plan users who have non-standard column names.
    
    Example: A bank that stores amount as 'txn_value' instead of 'amount',
    or uses 'cust_ref' instead of 'customer_id'.
    """
    
    def map_custom_to_standard(self, custom_columns: Dict[str, str]) -> SchemaMapping:
        """
        User provides: { 'txn_value': 'amount', 'cust_ref': 'customer_id', ... }
        System builds a mapping layer so ML pipeline works transparently.
        """
        return SchemaMapping(
            column_map=custom_columns,
            feature_pipeline=self._build_custom_feature_pipeline(custom_columns),
            model_version=f"custom_{tenant_id}_v1"
        )
    
    def _build_custom_feature_pipeline(self, column_map: Dict) -> FeaturePipeline:
        """Generate a personalized ML feature engineering pipeline
        based on the custom schema's available fields."""
        available_features = []
        
        if 'amount' in column_map.values():
            available_features.extend(AMOUNT_FEATURES)
        if 'location_lat' in column_map.values():
            available_features.extend(GEO_FEATURES)
        if 'device_fingerprint' in column_map.values():
            available_features.extend(DEVICE_FEATURES)
        
        return FeaturePipeline(features=available_features)
```

### Database Schema Created at Signup

```sql
-- New columns added to user's transaction table on first-run:
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS fraud_score DECIMAL(5,4);
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS fraud_category 
  VARCHAR(20) DEFAULT 'unscored';
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS fraud_risk_level 
  VARCHAR(10); -- 'low' | 'medium' | 'high' | 'critical'
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS fraud_model_version VARCHAR(50);
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS fraud_triggered_rules JSONB;
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS fraud_scored_at TIMESTAMPTZ;

-- Index for fast fraud queries
CREATE INDEX IF NOT EXISTS idx_txn_fraud_score ON transactions(fraud_score);
CREATE INDEX IF NOT EXISTS idx_txn_fraud_category ON transactions(fraud_category);
```

---

## 🔐 Login & User Dashboard

### Login Flow

```
POST /api/v1/auth/login
  ├─ Email + Password
  ├─ Returns: JWT access_token (15 min) + refresh_token (7 days)
  └─ Redirects to: /dashboard

Dashboard shows institution's own data — never cross-tenant data.
```

### Post-Login Dashboard View

After login, the user sees their **own dataset details** prominently displayed:

#### Dashboard Sections

**1. Data Overview Panel**
```
┌──────────────────────────────────────────────────────────────────┐
│  YOUR DATA  (Acme Bank — Connected via Supabase)                 │
│                                                                  │
│  Customers in DB: 1,247        Transactions Loaded: 89,342       │
│  Last Sync: 2 min ago          Schema: Standard (Pro Plan)       │
│  Model Version: v2.3           Model Trained: 2 days ago         │
│  Connection Status: ✅ LIVE                                       │
└──────────────────────────────────────────────────────────────────┘
```

**2. Fraud KPI Cards (real-time)**
```
┌────────────┐ ┌──────────────┐ ┌─────────────┐ ┌──────────────┐
│ Total Txns │ │ Fraud Rate   │ │ Blocked     │ │ Alerts Open  │
│  89,342    │ │   2.3%       │ │  1,847      │ │    24        │
│ Today: 423 │ │ ↓ 0.4% week │ │ This month  │ │ 3 critical   │
└────────────┘ └──────────────┘ └─────────────┘ └──────────────┘
```

**3. Live Transaction Feed**
- Streaming table of last 50 transactions
- Each row: customer ID (masked), amount, channel, fraud score (colored badge), status
- Clickable row opens transaction detail modal

**4. Fraud Alerts Queue**
- Active alerts sorted by severity
- One-click: `Confirm Fraud` | `Mark Legitimate` | `Investigate`

**5. Your Customer Data Details**
- Table showing customer summary from connected Customer DB
- Columns: customer_id, name (masked), risk_score, account_type, kyc_status, last_transaction

### Sample Transaction Testing (Live Simulation)

After login, the user can submit a **test transaction** via the Test Cases panel:

```
┌─────────────────────────────────────────────────────────────────┐
│  🧪 TEST A TRANSACTION                                           │
│                                                                  │
│  Customer Name / ID: [________________]                          │
│  Card Number (last 4): [____]                                    │
│  Transaction Amount: [____________]   Currency: [INR ▼]         │
│  Merchant: [_____________]  Category: [Electronics ▼]           │
│  Channel: [Online ▼]        Device: [Mobile ▼]                  │
│  Location (Lat/Lng): [______] [______]  OR  City: [________]     │
│  Transaction Time: [Now ▼]                                       │
│                                                                  │
│              [ RUN FRAUD DETECTION ]                             │
└─────────────────────────────────────────────────────────────────┘

RESULT PANEL (appears after submission):
  Fraud Score: 0.87 ████████████░░ HIGH RISK
  Risk Level: 🔴 CRITICAL
  
  Decision: BLOCKED
  
  Triggered Rules:
    ✅ Rule: Impossible Travel (customer last txn: Mumbai, 10 min ago)
    ✅ Rule: New Device Detected
    ✅ ML Model: XGBoost Fraud Classifier (score: 0.91)
  
  Top Contributing Features (SHAP):
    1. distance_from_last_txn: +0.34
    2. is_new_device: +0.28
    3. amount_zscore: +0.19
  
  Action Taken:
    ✅ Transaction written to transaction table
    ✅ fraud_category = 'fraudulent'
    ✅ fraud_score = 0.87
    ✅ Alert created (ID: ALT-00234)
    ✅ SMS sent to customer (+91-XXXXXXX890)
    ✅ Email sent to analyst (fraud@acmebank.com)
```

**Important:** The test transaction is **written to the actual transaction table** with `is_test = TRUE` flag, so it appears in analytics but is filterable. This lets users validate their connection and ML pipeline is working end-to-end.

---

## 🗃️ Sample Data Generation

### Specification: 100 Customers + 10,000 Transactions

The seed script generates realistic synthetic data for training and demo purposes.

#### Customer Sample Data (100 records)

```python
# backend/scripts/generate_sample_data.py

import uuid
import random
from datetime import datetime, timedelta
from faker import Faker

fake = Faker('en_IN')  # Indian locale for INR amounts and local names

CUSTOMER_PROFILES = [
    # Profile distribution for realistic fraud testing
    {"type": "standard_salaried", "count": 40, "avg_monthly_spend": 25000, "fraud_risk": "low"},
    {"type": "high_net_worth",    "count": 15, "avg_monthly_spend": 200000, "fraud_risk": "low"},
    {"type": "student",           "count": 15, "avg_monthly_spend": 8000, "fraud_risk": "medium"},
    {"type": "small_business",    "count": 15, "avg_monthly_spend": 75000, "fraud_risk": "medium"},
    {"type": "senior_citizen",    "count": 10, "avg_monthly_spend": 15000, "fraud_risk": "high"},
    {"type": "compromised",       "count": 5,  "avg_monthly_spend": 30000, "fraud_risk": "critical"},
]

# Sample Customer Record Structure:
SAMPLE_CUSTOMER = {
    "customer_id": "uuid-v4",
    "full_name": "Rajesh Kumar Sharma",
    "email": "rajesh.sharma@gmail.com",
    "phone_number": "+919876543210",
    "date_of_birth": "1985-03-15",
    "address_line_1": "204, Shanti Apartments",
    "city": "Mumbai",
    "state_province": "Maharashtra",
    "postal_code": "400001",
    "country_code": "IN",
    "account_type": "personal",
    "account_opening_date": "2018-06-01",
    "account_status": "active",
    "kyc_status": "verified",
    "risk_score": 0.12,
    "customer_tier": "standard",
    "bank_account_number": "MASKED_XXXX1234",
    "balance_amount": 145000.00,
    "active_card_count": 2,
    "preferred_card_token": "tok_XXXXXXXX",
    "created_at": "2018-06-01T10:00:00Z"
}
```

**100 Customers CSV Schema:**
```
customer_id, full_name, email, phone_number, date_of_birth, city, state,
account_type, account_opening_date, kyc_status, risk_score, customer_tier,
balance_amount, active_card_count, preferred_card_token
```

#### Transaction Sample Data (10,000 records)

```python
# Transaction Generation Rules:
# - 10,000 transactions across 90 days
# - ~97% legitimate, ~3% fraudulent (300 fraud cases)
# - Realistic patterns: work hours, weekends, merchant categories

TRANSACTION_CATEGORIES = {
    "grocery": {"weight": 0.25, "avg_amount": 2500, "channels": ["pos_physical", "online"]},
    "restaurant": {"weight": 0.15, "avg_amount": 800, "channels": ["pos_physical"]},
    "online_shopping": {"weight": 0.20, "avg_amount": 3500, "channels": ["online"]},
    "fuel": {"weight": 0.10, "avg_amount": 1500, "channels": ["pos_physical"]},
    "entertainment": {"weight": 0.08, "avg_amount": 1200, "channels": ["online", "pos_physical"]},
    "travel": {"weight": 0.07, "avg_amount": 15000, "channels": ["online"]},
    "healthcare": {"weight": 0.05, "avg_amount": 2000, "channels": ["pos_physical"]},
    "atm_withdrawal": {"weight": 0.10, "avg_amount": 5000, "channels": ["atm"]},
}

FRAUD_PATTERNS = [
    "card_not_present_fraud",       # 80 cases — online txns with stolen card
    "account_takeover",             # 60 cases — unusual time + new device
    "impossible_travel",            # 50 cases — geographic anomaly
    "velocity_fraud",               # 40 cases — rapid successive transactions
    "identity_theft",               # 40 cases — new account + high-value txns
    "money_mule",                   # 30 cases — rapid in/out pattern
]

SAMPLE_TRANSACTION = {
    "transaction_id": "uuid-v4",
    "customer_id": "ref_to_customer",
    "card_id": "MASKED_CARD_XXXX5678",
    "merchant_id": "MER_SWIGGY_001",
    "amount": 450.00,
    "currency": "INR",
    "transaction_type": "purchase",
    "channel": "online",
    "merchant_category_code": "5812",  # Food delivery
    "merchant_name": "Swiggy",
    "transaction_location_lat": 19.0760,
    "transaction_location_lng": 72.8777,
    "transaction_country_code": "IN",
    "ip_address": "103.21.56.78",
    "device_fingerprint": "df_abc123xyz",
    "device_type": "mobile",
    "status": "completed",
    "fraud_score": 0.04,
    "fraud_risk_level": "low",
    "fraud_category": "legitimate",   # Added by FinShield on first-run
    "is_flagged": False,
    "is_blocked": False,
    "is_test": False,
    "transaction_timestamp": "2025-06-15T19:45:00Z",
    "processed_timestamp": "2025-06-15T19:45:00.320Z"
}
```

**10,000 Transactions CSV Output File:** `sample_transactions_1000.csv`

**Fraud Label Distribution:**
```
Total: 10,000
  Legitimate:  9,700  (97.0%)
  Fraudulent:    300  ( 3.0%)
    └─ By type:
       Card-Not-Present:   80  (0.8%)
       Account Takeover:   60  (0.6%)
       Impossible Travel:  50  (0.5%)
       Velocity Fraud:     40  (0.4%)
       Identity Theft:     40  (0.4%)
       Money Mule:         30  (0.3%)
```

#### Generation Script

```bash
# Run from backend directory:
python scripts/generate_sample_data.py \
  --customers 100 \
  --transactions 10000 \
  --fraud-rate 0.03 \
  --output-dir ./data/samples/ \
  --seed 42

# Outputs:
# ./data/samples/customers_100.csv
# ./data/samples/transactions_10000.csv
# ./data/samples/fraud_labels.csv  (ground truth for model evaluation)
```

---

## 🧠 ML Model Training on Sample Data

### Training Pipeline (on 10,000 Sample Transactions)

All ML models are trained on the 10,000-sample dataset first. These pre-trained models become the **Free and Pro plan shared models**. Advanced plan users get personalized models trained on their own data with their custom schema.

#### Training Execution

```bash
# Run from backend directory:
python scripts/train_models.py \
  --data ./data/samples/transactions_10000.csv \
  --labels ./data/samples/fraud_labels.csv \
  --model-output ./app/ml/models/ \
  --evaluate True

# Models trained and saved:
# ./app/ml/models/isolation_forest_v1.pkl
# ./app/ml/models/dbscan_v1.pkl
# ./app/ml/models/xgboost_fraud_classifier_v1.pkl
# ./app/ml/models/random_forest_v1.pkl
# ./app/ml/models/neural_network_fraud_v1.onnx
# ./app/ml/models/ensemble_v1.pkl
# ./app/ml/models/feature_scaler_v1.pkl
# ./app/ml/models/evaluation_report.json
```

#### Feature Engineering (200+ Features)

```python
class FeatureEngineer:
    """200+ features across 10+ categories"""
    
    async def engineer_all_features(self,
                                   transaction: Transaction,
                                   customer_history: List[Transaction]
                                   ) -> np.ndarray:
        """Generate full feature vector for ML scoring"""
        
        features = np.concatenate([
            self._transaction_features(transaction),        # ~20
            self._temporal_features(transaction),           # ~15
            self._velocity_features(transaction, history),  # ~40
            self._entity_features(transaction),             # ~20
            self._geographic_features(transaction, history),# ~15
            self._device_features(transaction),             # ~15
            self._behavioral_features(transaction, history),# ~25
            self._network_features(transaction),            # ~15
            self._derived_features(transaction, history)    # ~35
        ])
        
        return features  # Shape: (200+,)
```

| Feature Category | Count | Key Examples |
|-----------------|-------|-------------|
| Transaction | ~20 | amount, currency, channel, mcc, card_present |
| Temporal | ~15 | hour_of_day, day_of_week, is_weekend, is_holiday |
| Velocity | ~40 | txn_count_1h, txn_sum_24h, unique_merchants_7d |
| Entity | ~20 | account_age_days, kyc_level, historical_fraud_count |
| Geographic | ~15 | country_risk_score, distance_from_last_txn, is_cross_border |
| Device | ~15 | device_age_days, is_new_device, ip_reputation_score |
| Behavioral | ~25 | amount_zscore, time_deviation, new_merchant_category_flag |
| Network | ~15 | fraud_ring_proximity, shared_device_count |
| Derived | ~35 | amount_to_balance_ratio, velocity_z_score, anomaly_composite |

#### Model Architecture (Multi-Layer)

```
Layer 1: Unsupervised Anomaly Detection
  ├─ Isolation Forest   → Detects statistical outliers in feature space
  ├─ DBSCAN Clustering  → Groups normal transactions; flags loners as anomalies
  └─ Autoencoder        → Learns normal transaction pattern; flags high reconstruction error

Layer 2: Supervised Classification (trained on labeled 10K sample)
  ├─ XGBoost Classifier → Primary fraud classifier (handles imbalanced data)
  ├─ Random Forest      → Ensemble robustness, feature importance
  └─ Neural Network     → Deep patterns (PyTorch, exported to ONNX)

Layer 3: Rules Engine
  └─ 20 predefined deterministic rules (velocity, geo, device, behavioral)

Layer 4: Ensemble Scorer
  └─ Weighted combination of all layers → Final fraud_score (0.0–1.0)
  
Ensemble Weights (initial, tuned via validation):
  Rules Engine:         0.25
  Isolation Forest:     0.10
  DBSCAN:              0.10
  XGBoost:             0.30
  Random Forest:        0.15
  Neural Network:       0.10
```

#### Model Validation Results (Target Benchmarks)

```json
{
  "model": "ensemble_v1",
  "training_samples": 10000,
  "test_samples": 2000,
  "fraud_samples_test": 60,
  "precision": 0.91,
  "recall": 0.88,
  "f1_score": 0.895,
  "auc_roc": 0.967,
  "false_positive_rate": 0.024,
  "false_negative_rate": 0.12,
  "average_inference_time_ms": 18,
  "model_size_mb": 42
}
```

#### Live Transaction Scoring Pipeline

```python
class FraudScoringPipeline:
    """Scores incoming transactions using trained models"""
    
    async def score(self, transaction: Transaction) -> FraudScore:
        # 1. Load customer history from DB
        history = await db.get_recent_transactions(
            customer_id=transaction.customer_id,
            days=30
        )
        
        # 2. Feature engineering
        features = await self.feature_engineer.engineer_all_features(
            transaction, history
        )
        
        # 3. Rules engine
        rule_result = await self.rules_engine.evaluate(transaction, history)
        
        # 4. ML inference (ONNX for speed)
        isolation_score = self.isolation_forest.score_samples([features])[0]
        xgb_score = self.xgboost.predict_proba([features])[0][1]
        nn_score = self.neural_net_session.run(None, {'input': [features]})[0][0]
        
        # 5. Ensemble
        final_score = (
            rule_result.score * 0.25 +
            isolation_score * 0.10 +
            xgb_score * 0.30 +
            nn_score * 0.10 +
            self.random_forest.predict_proba([features])[0][1] * 0.15 +
            self.dbscan_outlier_score(features) * 0.10
        )
        
        # 6. Write back to transaction table
        await db.update_transaction_fraud_fields(
            transaction_id=transaction.transaction_id,
            fraud_score=final_score,
            fraud_category=self._score_to_category(final_score),
            fraud_risk_level=self._score_to_risk(final_score),
            fraud_model_version="ensemble_v1",
            fraud_triggered_rules=rule_result.triggered_rules,
            fraud_scored_at=datetime.utcnow()
        )
        
        return FraudScore(score=final_score, ...)
    
    def _score_to_category(self, score: float) -> str:
        if score < 0.3: return "legitimate"
        if score < 0.6: return "suspicious"
        return "fraudulent"
    
    def _score_to_risk(self, score: float) -> str:
        if score < 0.3: return "low"
        if score < 0.6: return "medium"
        if score < 0.8: return "high"
        return "critical"
```

---

## 🗄️ Database Architecture

### Primary Database: Supabase (PostgreSQL)

**For testing and default deployment, FinShield uses Supabase.**
For production or enterprise, any PostgreSQL-compatible database is supported.
The system is database-agnostic by design — users can bring their own DB via connection string.

#### Supported Database Backends

| Database | Support Level | Connection Method |
|----------|-------------|------------------|
| **Supabase** | Primary (default) | Supabase URL + anon key + service key |
| PostgreSQL | Full | `postgresql+asyncpg://user:pass@host/db` |
| MySQL / MariaDB | Full | `mysql+aiomysql://user:pass@host/db` |
| MongoDB | Partial | Connection string (transactions only) |
| MS SQL Server | Partial | `mssql+aioodbc://...` |
| SQLite | Dev only | `sqlite+aiosqlite:///./finshield.db` |

#### Core Database Tables

##### A. Customers Table

```sql
CREATE TABLE customers (
  customer_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  
  -- Identity Information
  full_name VARCHAR(255) NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  phone_number VARCHAR(20),
  date_of_birth DATE,
  
  -- Address Information
  address_line_1 VARCHAR(255),
  address_line_2 VARCHAR(255),
  city VARCHAR(100),
  state_province VARCHAR(100),
  postal_code VARCHAR(20),
  country_code VARCHAR(2) DEFAULT 'IN',
  
  -- Account Information
  account_type VARCHAR(20) CHECK (account_type IN ('personal', 'business', 'merchant')),
  account_opening_date DATE NOT NULL,
  account_status VARCHAR(20) DEFAULT 'active' 
    CHECK (account_status IN ('active', 'inactive', 'suspended', 'closed')),
  
  -- KYC & Compliance
  kyc_status VARCHAR(20) DEFAULT 'pending'
    CHECK (kyc_status IN ('pending', 'verified', 'rejected', 'expired')),
  kyc_verified_date TIMESTAMPTZ,
  kyc_verification_level VARCHAR(20) DEFAULT 'basic'
    CHECK (kyc_verification_level IN ('basic', 'enhanced', 'full')),
  risk_score DECIMAL(5,4) DEFAULT 0.0 CHECK (risk_score BETWEEN 0 AND 1),
  
  -- Banking Profile
  customer_tier VARCHAR(20) DEFAULT 'standard'
    CHECK (customer_tier IN ('standard', 'premium', 'vip')),
  banking_profile JSONB DEFAULT '{}',
  bank_account_number VARCHAR(100),
  balance_amount DECIMAL(18,2) DEFAULT 0.0,
  
  -- Card Information (Masked/Tokenized)
  preferred_card_token VARCHAR(255),
  active_card_count INTEGER DEFAULT 0,
  
  -- Audit Trail
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_customer_email ON customers(email);
CREATE INDEX idx_customer_kyc_status ON customers(kyc_status);
CREATE INDEX idx_customer_risk_score ON customers(risk_score);
CREATE INDEX idx_customer_created_at ON customers(created_at);
```

##### B. Transactions Table (with FinShield fraud columns)

```sql
CREATE TABLE transactions (
  transaction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  
  -- Identifiers
  customer_id UUID NOT NULL REFERENCES customers(customer_id),
  card_id VARCHAR(255),
  merchant_id VARCHAR(255),
  
  -- Transaction Details
  amount DECIMAL(18,2) NOT NULL,
  currency VARCHAR(3) NOT NULL DEFAULT 'INR',
  transaction_type VARCHAR(20) NOT NULL
    CHECK (transaction_type IN ('purchase', 'withdrawal', 'transfer', 
                                'refund', 'reversal', 'balance_inquiry')),
  
  -- Channel Information
  channel VARCHAR(20) NOT NULL
    CHECK (channel IN ('pos_physical', 'online', 'atm', 'mobile', 'wire', 'ach')),
  merchant_category_code VARCHAR(4),
  merchant_name VARCHAR(255),
  
  -- Location & Device
  transaction_location_lat DECIMAL(10,8),
  transaction_location_lng DECIMAL(10,8),
  transaction_country_code VARCHAR(2),
  ip_address INET,
  device_fingerprint VARCHAR(255),
  device_type VARCHAR(20)
    CHECK (device_type IN ('mobile', 'desktop', 'tablet', 'pos_terminal', 'unknown')),
  
  -- Transaction Status
  status VARCHAR(20) NOT NULL DEFAULT 'pending'
    CHECK (status IN ('pending', 'completed', 'failed', 'reversed', 'flagged', 'blocked')),
  
  -- ✅ FinShield Fraud Detection Columns (added on first-run)
  fraud_score DECIMAL(5,4),
  fraud_risk_level VARCHAR(10)
    CHECK (fraud_risk_level IN ('low', 'medium', 'high', 'critical')),
  fraud_category VARCHAR(20) DEFAULT 'unscored'
    CHECK (fraud_category IN ('legitimate', 'suspicious', 'fraudulent', 'unscored')),
  is_flagged BOOLEAN DEFAULT FALSE,
  is_blocked BOOLEAN DEFAULT FALSE,
  is_test BOOLEAN DEFAULT FALSE,
  model_version VARCHAR(50),
  triggered_rule_ids JSONB DEFAULT '[]',
  fraud_scored_at TIMESTAMPTZ,
  
  -- Timestamps
  transaction_timestamp TIMESTAMPTZ NOT NULL,
  processed_timestamp TIMESTAMPTZ DEFAULT NOW(),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_transaction_customer_id ON transactions(customer_id);
CREATE INDEX idx_transaction_timestamp ON transactions(transaction_timestamp);
CREATE INDEX idx_transaction_status ON transactions(status);
CREATE INDEX idx_transaction_fraud_score ON transactions(fraud_score);
CREATE INDEX idx_transaction_fraud_category ON transactions(fraud_category);
CREATE INDEX idx_transaction_is_test ON transactions(is_test);

-- Monthly partitioning for performance (production)
-- CREATE TABLE transactions_2025_01 PARTITION OF transactions
--   FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
```

##### C. Supporting Tables

```sql
-- Fraud Rules
CREATE TABLE fraud_rules (
  rule_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID REFERENCES tenants(tenant_id),
  rule_name VARCHAR(255) NOT NULL,
  rule_category VARCHAR(20)
    CHECK (rule_category IN ('velocity', 'amount', 'geographic', 'device', 'pattern', 'behavioral')),
  conditions JSONB NOT NULL,
  threshold DECIMAL(10,2),
  action VARCHAR(20) DEFAULT 'flag'
    CHECK (action IN ('flag', 'block', 'alert', 'log')),
  severity VARCHAR(20) DEFAULT 'medium',
  is_active BOOLEAN DEFAULT TRUE,
  priority INTEGER DEFAULT 100,
  false_positive_rate DECIMAL(5,4),
  hit_rate DECIMAL(5,4),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Fraud Alerts
CREATE TABLE fraud_alerts (
  alert_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID REFERENCES tenants(tenant_id),
  transaction_id UUID NOT NULL REFERENCES transactions(transaction_id),
  customer_id UUID NOT NULL REFERENCES customers(customer_id),
  alert_type VARCHAR(20) CHECK (alert_type IN ('rule', 'ml_model', 'manual', 'watchlist')),
  severity VARCHAR(20) CHECK (severity IN ('low', 'medium', 'high', 'critical')),
  status VARCHAR(20) DEFAULT 'open'
    CHECK (status IN ('open', 'under_review', 'confirmed_fraud', 'false_positive', 'closed')),
  analyst_id UUID,
  resolution_notes TEXT,
  is_confirmed BOOLEAN DEFAULT FALSE,
  notifications_sent JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  resolved_at TIMESTAMPTZ
);

-- Tenants (Institutions)
CREATE TABLE tenants (
  tenant_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_name VARCHAR(255) NOT NULL,
  institution_type VARCHAR(30)
    CHECK (institution_type IN ('bank', 'fintech', 'insurance', 'payment_processor', 'neobank')),
  subscription_plan VARCHAR(20) DEFAULT 'free'
    CHECK (subscription_plan IN ('free', 'pro', 'advanced')),
  plan_started_at TIMESTAMPTZ,
  plan_expires_at TIMESTAMPTZ,
  customer_db_url_encrypted TEXT,
  transaction_db_url_encrypted TEXT,
  custom_schema_mapping JSONB DEFAULT '{}',
  model_preference VARCHAR(20) DEFAULT 'shared_global',
  model_id UUID REFERENCES ml_models(model_id),
  api_rate_limit INTEGER DEFAULT 1000,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ML Models Registry
CREATE TABLE ml_models (
  model_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID REFERENCES tenants(tenant_id),
  model_name VARCHAR(255) NOT NULL,
  model_type VARCHAR(30)
    CHECK (model_type IN ('fraud_classifier', 'anomaly_detector', 'risk_scorer', 'ensemble')),
  version VARCHAR(50) NOT NULL,
  status VARCHAR(20) CHECK (status IN ('training', 'validating', 'active', 'retired', 'failed')),
  precision DECIMAL(5,4),
  recall DECIMAL(5,4),
  f1_score DECIMAL(5,4),
  auc_roc DECIMAL(5,4),
  false_positive_rate DECIMAL(5,4),
  training_samples INTEGER,
  artifact_path VARCHAR(500),
  promoted_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(tenant_id, model_name, version)
);

-- Watchlists
CREATE TABLE watchlists (
  watchlist_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID REFERENCES tenants(tenant_id),
  customer_id UUID REFERENCES customers(customer_id),
  watchlist_type VARCHAR(30)
    CHECK (watchlist_type IN ('sanctions', 'pep', 'adverse_media', 'internal_blacklist')),
  source VARCHAR(100),
  match_score DECIMAL(5,4),
  is_active BOOLEAN DEFAULT TRUE,
  expires_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Audit Log
CREATE TABLE audit_logs (
  log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID REFERENCES tenants(tenant_id),
  user_id UUID,
  action VARCHAR(100) NOT NULL,
  resource_type VARCHAR(50),
  resource_id UUID,
  old_value JSONB,
  new_value JSONB,
  ip_address INET,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 🔌 Data Integration & Connectors

### Design Goal: 10–20 Connectors with Auto Schema Normalization

Each financial institution has different database schemas and data formats. FinShield normalizes all incoming data to its standard schema automatically.

### Connector Abstraction Layer

```python
class DataConnector(ABC):
    """Base abstraction for all data sources"""
    
    @abstractmethod
    async def authenticate(self, credentials: Dict) -> bool:
        pass
    
    @abstractmethod
    async def fetch_customers(self) -> List[NormalizedCustomer]:
        pass
    
    @abstractmethod
    async def fetch_transactions(self, since: datetime) -> AsyncIterator[NormalizedTransaction]:
        pass
    
    @abstractmethod
    async def push_fraud_result(self, transaction_id: str, result: FraudResult) -> bool:
        """Write fraud_score + fraud_category back to source system"""
        pass
```

### 20 Pre-Built Connectors

| # | Category | Connector | Integration Method | Auth |
|---|----------|-----------|-------------------|------|
| 1 | **Core Banking** | SAP Banking Core | REST API + DB Direct | OAuth2/API Key |
| 2 | | Temenos Transact | REST API | OAuth2 |
| 3 | | FIS / Fiserv | REST API | OAuth2 |
| 4 | | Finacle (Infosys) | REST API | API Key |
| 5 | **Payment Networks** | Visa Transaction Data | Real-time feed | OAuth2 |
| 6 | | Mastercard API | Real-time feed | OAuth2 |
| 7 | | RuPay (NPCI) | API | API Key (India) |
| 8 | **Payment Gateways** | Stripe | Webhooks + REST | API Key |
| 9 | | Razorpay | Webhooks + REST | API Key (India) |
| 10 | | PayPal | Webhooks + REST | OAuth2 |
| 11 | | Square | Webhooks + REST | OAuth2 |
| 12 | **Card Processors** | First Data (Fiserv) | REST | OAuth2 |
| 13 | | ACI Worldwide | REST | OAuth2 |
| 14 | **Streaming** | Apache Kafka | Kafka Consumer | SASL/mTLS |
| 15 | | Azure Event Hubs | AMQP | Connection String |
| 16 | **Database Direct** | Supabase (PostgreSQL) | SDK + REST | URL + Keys |
| 17 | | PostgreSQL Generic | asyncpg | User/Pass |
| 18 | | MySQL / MariaDB | aiomysql | User/Pass |
| 19 | **Batch / File** | CSV / SFTP Upload | File Parser | Key-based SFTP |
| 20 | **Legacy** | Custom REST API | Generic Adapter | Configurable |

### Schema Normalization

```python
async def normalize_transaction(
    external_txn: Dict,
    connector_type: str,
    custom_schema_map: Dict = None
) -> NormalizedTransaction:
    """
    Convert any source format to FinShield standard schema.
    
    Handles different field names per institution:
      Temenos: 'txnAmt' → amount
      Stripe:  'charge.amount' / 100 → amount (Stripe uses paise)
      Razorpay:'payment.amount' / 100 → amount
      CSV:     user-defined mapping from signup
    """
    
    # Use custom schema mapping if provided (Advanced plan)
    field_map = custom_schema_map or DEFAULT_FIELD_MAPS[connector_type]
    
    return NormalizedTransaction(
        transaction_id=extract(external_txn, field_map, 'transaction_id') or uuid4(),
        customer_id=extract(external_txn, field_map, 'customer_id'),
        amount=convert_to_base_currency(
            extract(external_txn, field_map, 'amount'),
            extract(external_txn, field_map, 'currency')
        ),
        transaction_timestamp=parse_timestamp(
            extract(external_txn, field_map, 'timestamp')
        ),
        channel=map_channel(extract(external_txn, field_map, 'channel'), connector_type),
        # ... other fields
    )
```

### Ingestion Modes

**1. Real-Time Streaming** (Kafka, Event Hubs, Webhooks)
- Latency: <100ms end-to-end
- Fraud scored before transaction settles
- Supports blocking of fraudulent transactions pre-settlement

**2. Batch Ingestion** (CSV upload, SFTP, scheduled API polls)
- Runs every 15 min / 1 hour / daily (configurable)
- Bulk fraud scoring of historical data
- Used for model retraining data collection

**3. Direct Database Polling**
- Connect directly to customer's Supabase / PostgreSQL
- Poll for new rows in `transactions` table every N seconds
- CDC (Change Data Capture) mode for low-latency DB-backed institutions

---

## 🚨 Fraud Detection Logic & Thresholds

### Fraud Signals Taxonomy

#### A. Amount-Based Signals

| Signal | Threshold | Risk Level |
|--------|-----------|-----------|
| Transaction Amount Deviation | > 3σ above customer avg | HIGH |
| Structuring / Smurfing | Multiple <₹8,00,000 in 24h, sum >₹40L | CRITICAL |
| Round Amount Pattern | Repeated round amounts (₹10,000, ₹20,000) | LOW |
| First High-Value Transaction | First ever txn > 3× account balance | HIGH |

#### B. Velocity-Based Signals

| Signal | Threshold | Time Window | Risk Level |
|--------|-----------|------------|-----------|
| Transaction Frequency Spike | > 5× customer baseline | 1 hour | HIGH |
| Rapid Successive Transactions | 5+ transactions | <10 minutes | MEDIUM |
| Geographic Velocity | 2 txns >500 km apart | <30 min | CRITICAL |
| Cross-Merchant Velocity | 10+ different merchants | 1 hour | MEDIUM |

#### C. Geographic & Location Signals

| Signal | Condition | Risk Level |
|--------|-----------|-----------|
| Impossible Travel | >900 km/hour between transactions | CRITICAL |
| New Country | First transaction in this country | MEDIUM |
| High-Risk Country | Transaction in sanctioned/high-risk country | CRITICAL |
| Multi-Country Spread | Transactions in 5+ countries | HIGH |

#### D. Device & IP Signals

| Signal | Condition | Risk Level |
|--------|-----------|-----------|
| New Device | Device fingerprint never seen before | MEDIUM |
| Proxy/VPN Detected | IP flagged as proxy/VPN | MEDIUM |
| Tor Network | Transaction via Tor exit node | CRITICAL |
| IP on Blocklist | IP on malware/botnet database | HIGH |

#### E. Behavioral Anomaly Signals

| Signal | Condition | Risk Level |
|--------|-----------|-----------|
| Unusual Hour | Transaction at 2–4 AM vs typical profile | LOW–MEDIUM |
| New Merchant Category | Never used this MCC before + high amount | MEDIUM |
| Account Takeover Pattern | Password reset + transaction within 30 min | CRITICAL |
| Multiple Failed Auth | 3+ failed logins before successful transaction | HIGH |

### Rule Configuration Format (YAML DSL)

```yaml
rules:
  - id: rule_velocity_spike
    name: "Transaction Velocity Spike"
    category: "velocity"
    conditions:
      operator: "and"
      rules:
        - field: "txn_count_1h"
          comparator: ">"
          value: 5
        - field: "txn_sum_1h"
          comparator: ">"
          value: 50000
    actions:
      - type: "flag"
        severity: "high"
      - type: "alert"
        notify: ["email", "sms"]
    false_positive_rate: 0.15
    hit_rate: 0.72

  - id: rule_impossible_travel
    name: "Impossible Travel"
    category: "geographic"
    conditions:
      operator: "and"
      rules:
        - field: "km_from_last_txn"
          comparator: ">"
          value: 900
        - field: "minutes_since_last_txn"
          comparator: "<"
          value: 30
    actions:
      - type: "block"
        severity: "critical"
      - type: "alert"
        notify: ["sms", "email", "phone_call"]
    false_positive_rate: 0.02
    hit_rate: 0.95

  - id: rule_account_takeover
    name: "Account Takeover Indicator"
    category: "behavioral"
    conditions:
      operator: "and"
      rules:
        - field: "minutes_since_password_reset"
          comparator: "<"
          value: 30
        - field: "is_new_device"
          comparator: "=="
          value: true
        - field: "amount"
          comparator: ">"
          value: 10000
    actions:
      - type: "block"
        severity: "critical"
      - type: "alert"
        notify: ["sms", "email", "phone_call"]
    false_positive_rate: 0.03
    hit_rate: 0.88
```

---

## 🤖 ML Modeling Strategy

### Multi-Layered Detection Architecture

```
INCOMING TRANSACTION
        │
        ▼
┌─────────────────────────────┐
│   Layer 1: Rules Engine     │  Deterministic, fast (<5ms)
│   20 predefined rules       │  Handles obvious fraud patterns
│   Threshold-based           │  Low FPR, high confidence
└──────────────┬──────────────┘
               │ rule_score (0.0–1.0)
               ▼
┌─────────────────────────────┐
│   Layer 2: Unsupervised     │  No labels needed, anomaly scoring
│   Isolation Forest          │  Outlier detection in feature space
│   DBSCAN Clustering         │  Identifies unusual transaction clusters
│   Autoencoder               │  Reconstruction error as fraud proxy
└──────────────┬──────────────┘
               │ anomaly_score (0.0–1.0)
               ▼
┌─────────────────────────────┐
│   Layer 3: Supervised       │  Trained on labeled data (10K+ samples)
│   XGBoost Classifier        │  Primary fraud probability
│   Random Forest             │  Ensemble stability
│   Neural Network (ONNX)     │  Complex pattern recognition
└──────────────┬──────────────┘
               │ ml_score (0.0–1.0)
               ▼
┌─────────────────────────────┐
│   Layer 4: Ensemble Scorer  │  Weighted combination
│   Final fraud_score         │  0.0–1.0 calibrated probability
└──────────────┬──────────────┘
               │
               ▼
        DECISION ENGINE
   < 0.3 → PASS | 0.3–0.6 → FLAG | 0.6–0.8 → ALERT | ≥ 0.8 → BLOCK
```

### Model Training Pipeline

```
STEP 1: Data Preparation
  ├─ Load 10,000 labeled transactions
  ├─ Handle class imbalance (SMOTE oversampling on fraud minority)
  └─ Train/test split: 80/20 stratified

STEP 2: Feature Engineering
  └─ Generate 200+ features per transaction

STEP 3: Unsupervised Model Training
  ├─ Isolation Forest (n_estimators=100, contamination=0.03)
  ├─ DBSCAN (eps=0.5, min_samples=5 on normalized features)
  └─ Autoencoder (5 layers, bottleneck=32, trained on legitimate only)

STEP 4: Supervised Model Training
  ├─ XGBoost (max_depth=6, learning_rate=0.1, scale_pos_weight=32)
  ├─ Random Forest (n_estimators=200, max_depth=10, class_weight='balanced')
  └─ Neural Network (3 layers: 256→128→64→1, dropout=0.3, sigmoid output)

STEP 5: Ensemble Calibration
  └─ Logistic regression meta-model on Layer 1–3 outputs

STEP 6: Evaluation
  ├─ Precision, Recall, F1, AUC-ROC on holdout
  ├─ Confusion matrix analysis
  └─ SHAP feature importance

STEP 7: ONNX Export
  └─ Export neural network to ONNX for <20ms inference

STEP 8: Model Registry
  └─ Save to ml_models table with all metrics
```

### Model Validation Targets

| Metric | Target | Minimum Acceptable |
|--------|--------|--------------------|
| Precision | > 0.90 | > 0.85 |
| Recall | > 0.85 | > 0.75 |
| F1-Score | > 0.875 | > 0.80 |
| AUC-ROC | > 0.95 | > 0.92 |
| False Positive Rate | < 0.03 | < 0.05 |
| Inference Time | < 20ms | < 50ms |

### Model Drift & Retraining

```python
class DriftDetectionService:
    
    async def check_model_drift(self, tenant_id: str) -> DriftReport:
        """
        Drift triggers:
        - Prediction accuracy drops >3% vs baseline
        - False positive rate increases >5%
        - Feature distribution shift (Kolmogorov-Smirnov test p < 0.05)
        """
        # Compare last 7 days vs training baseline
        recent = await self._compute_recent_metrics(tenant_id)
        baseline = await db.get_model_baseline_metrics(tenant_id)
        
        return DriftReport(
            drift_detected=(
                (baseline.accuracy - recent.accuracy) > 0.03 or
                (recent.fpr - baseline.fpr) > 0.05 or
                await self._feature_shift_detected(tenant_id)
            ),
            recommendation="retrain" if drift_detected else "monitor"
        )
```

**Retraining Schedule:**
- Free plan: Monthly automated
- Pro plan: Weekly automated
- Advanced plan: On-demand + triggered by drift detection
- Minimum data for retraining: 1,000 new labeled transactions

---

## 🔔 Post-Detection Actions & Alerts

### Decision Tree & Response Matrix

```
Fraud Score Calculated
       │
       ├─ < 0.30 → PASS (Green)
       │    └─ Action: Allow transaction, log silently
       │
       ├─ 0.30–0.59 → FLAG (Yellow)
       │    ├─ Allow transaction (do not block)
       │    ├─ Mark: fraud_category = 'suspicious'
       │    ├─ Create alert: severity = 'medium'
       │    └─ Notify: Dashboard + Analyst Email
       │
       ├─ 0.60–0.79 → ALERT (Orange)
       │    ├─ Allow but flag prominently
       │    ├─ Mark: fraud_category = 'suspicious'
       │    ├─ Create alert: severity = 'high'
       │    ├─ Notify: SMS + Email (analyst + optional customer)
       │    └─ Escalate to alert queue for review within 1 hour
       │
       └─ ≥ 0.80 → BLOCK (Red)
            ├─ Block transaction immediately
            ├─ Mark: fraud_category = 'fraudulent', status = 'blocked'
            ├─ Create alert: severity = 'critical'
            ├─ Notify: SMS + Email + In-app push + Optional phone call
            ├─ Optional: Temporary card pause (24 hours)
            └─ Auto-create investigation case
```

### Handling Already-Completed Transactions

For transactions that have already settled when fraud is detected (batch processing scenario):

```
POST-SETTLEMENT FRAUD DETECTION:
  1. Flag transaction: fraud_category = 'fraudulent' (even if completed)
  2. Create fraud alert with note: "Post-settlement detection"
  3. Notify analyst immediately (high priority)
  4. Initiate chargeback workflow (if enabled by institution)
  5. Place customer account on enhanced monitoring (risk_score += 0.3)
  6. Generate SAR (Suspicious Activity Report) if amount > threshold
  7. Notify customer: "We've detected suspicious activity on your account"
```

### Notification Channels (All Free/Low-Cost Services)

| Channel | Service | Free Tier | Notes |
|---------|---------|-----------|-------|
| Email | **Resend.com** | 3,000/month free | Preferred (reliable, easy) |
| Email (fallback) | **SendGrid** | 100/day free | Fallback option |
| SMS | **Twilio** | Paid (~₹0.10/SMS) | For High/Critical alerts |
| SMS (India free alt) | **MSG91** | Trial credits | India-focused |
| Push Notification | **Firebase FCM** | Free unlimited | For mobile app |
| In-App | WebSocket (Socket.IO) | Free (self-hosted) | Real-time dashboard |
| Phone Call | **Twilio Voice** | Paid | Critical alerts only |
| Webhook | Custom HTTP | Free | For external integrations |
| Slack | Slack Webhooks | Free | Team notification |

```python
class NotificationService:
    
    async def send_fraud_alert(self, alert: FraudAlert, customer: Customer):
        
        channels = {
            "critical": ["sms", "email", "push", "in_app", "phone_call"],
            "high":     ["sms", "email", "push", "in_app"],
            "medium":   ["email", "in_app"],
            "low":      ["in_app"]
        }[alert.severity]
        
        for channel in channels:
            await self._send_via(channel, alert, customer)
    
    async def _send_email(self, to: str, alert: FraudAlert):
        """Uses Resend.com API (free tier)"""
        # POST https://api.resend.com/emails
        # Subject: "⚠️ Fraud Alert — Transaction Flagged"
        # Template: fraud_alert_email.html (with SHAP explanation)
        pass
    
    async def _send_sms(self, phone: str, alert: FraudAlert):
        """Uses Twilio SMS API"""
        # "FinShield Alert: Suspicious transaction of ₹X detected 
        #  at [Merchant]. If not you, reply BLOCK. Ref: ALT-00234"
        pass
    
    async def _send_push(self, device_tokens: List[str], alert: FraudAlert):
        """Uses Firebase Cloud Messaging (free)"""
        pass
```

---

## 🏢 Scalability Across Institutions

### Multi-Tenant Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      FinShield Platform                     │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              Shared API & Auth Layer                   │ │
│  └────────────────────────────────────────────────────────┘ │
│         │              │              │              │       │
│  ┌──────▼──┐   ┌───────▼─┐   ┌───────▼─┐   ┌───────▼─┐   │
│  │ Bank A  │   │ Fintech │   │Insurance│   │PayProc. │   │
│  │(schema  │   │  B      │   │   C     │   │   D     │   │
│  │_tenant_a│   │_tenant_b│   │_tenant_c│   │_tenant_d│   │
│  └─────────┘   └─────────┘   └─────────┘   └─────────┘   │
│                                                             │
│  Model Strategy:                                            │
│   Free/Pro  → Shared Global Model (trained on 10K sample)  │
│   Advanced  → Dedicated Model (trained on own data)        │
│   Hybrid    → Global base + tenant fine-tuning             │
└─────────────────────────────────────────────────────────────┘
```

### Row-Level Security (Supabase)

```sql
-- Enable RLS on all tables
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE fraud_alerts ENABLE ROW LEVEL SECURITY;

-- Policy: each tenant only sees their own data
CREATE POLICY tenant_isolation ON transactions
  USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

CREATE POLICY tenant_isolation ON customers
  USING (tenant_id = current_setting('app.current_tenant_id')::uuid);
```

### Model Strategy Per Institution Type

| Strategy | Who | Pros | When |
|----------|-----|------|------|
| **Shared Global** | Free/Pro all tenants | Cost-efficient, cross-institution learning | Default |
| **Dedicated** | Advanced, unique patterns | Customized to institution's fraud profile | Large institutions |
| **Transfer Learning** | Advanced, small data | Leverage global model, fine-tune on own data | New institutions |
| **Ensemble** | Advanced, hybrid | Best accuracy, highest coverage | Enterprise |

---

## 📊 Admin Dashboard & System Monitoring

### Dashboard Sections

#### 1. Overview KPIs (Real-Time)
```
┌──────────────────────────────────────────────────────────────────────┐
│  Today's Transactions: 14,234    Fraud Rate: 2.1%   Blocked: 298    │
│  False Positive Rate: 1.8%       Active Alerts: 47   System: ✅ UP  │
│  Model Accuracy: 96.4%           Avg Latency: 18ms                  │
└──────────────────────────────────────────────────────────────────────┘
```

#### 2. Real-Time Activity Feed
- Live WebSocket-powered transaction stream
- Color-coded fraud score badges
- Model inference latency (P50/P95/P99)

#### 3. Fraud Detection Trends
- Fraud rate over time (line chart — 7d / 30d / 90d)
- Fraud by transaction type (bar chart)
- Fraud by geography (India heatmap using D3.js)
- Fraud by device type (donut chart)
- Top fraud patterns table

#### 4. Model Performance Panel
- Precision/Recall/F1/AUC-ROC trend over time
- Confusion matrix visualization
- SHAP feature importance bar chart
- Model version history with promoted/retired status
- Drift detection indicator (green/yellow/red)

#### 5. Alert Management
- Alert queue: open / under review / resolved
- Average resolution time (SLA tracking)
- Analyst leaderboard (alerts resolved per user)

#### 6. Institution Health (Admin only)
- All tenant onboarding status
- Plan distribution (Free/Pro/Advanced)
- Data source connection health per tenant
- API usage per tenant (rate limit headroom)

### Admin Monitoring — System Metrics

| Metric | Source | Alert Threshold |
|--------|--------|----------------|
| API Response P95 | Application Insights | > 500ms |
| Fraud Score Latency | Custom metric | > 100ms |
| DB Query Time | Supabase / pg_stat | > 200ms |
| Model Drift Score | DriftDetectionService | > 0.05 shift |
| False Positive Rate | Computed daily | > 5% |
| Alert Resolution SLA | Computed hourly | > 4h open critical |

---

## ⚙️ Settings & API Keys Management

### Settings Page Structure

The Settings page under `/dashboard/settings` is fully dynamic. All service integrations are optional — the platform works with partial configuration, falling back gracefully to free/open alternatives.

#### Settings Sections

**1. Database Connections**
```
Customer Database
  ├─ Type: [Supabase ▼ / PostgreSQL / MySQL / MongoDB / API]
  ├─ Connection URL / Supabase Project URL: [_______________]
  ├─ API Key / Password: [_______________]  (encrypted at rest)
  └─ [Test Connection]  [Save]

Transaction Database
  ├─ Same options as above
  └─ [Test Connection]  [Save]
```

**2. Notification Services (All Optional)**
```
Email Provider
  ├─ [Resend.com ▼ / SendGrid / SMTP]
  ├─ API Key: [_______________]
  └─ From Address: [_______________]

SMS Provider (Optional — skip for email-only)
  ├─ [Twilio ▼ / MSG91 / None]
  ├─ Account SID / API Key: [_______________]
  ├─ Auth Token / Secret: [_______________]
  └─ From Number: [_______________]

Push Notifications (Optional)
  ├─ [Firebase FCM ▼ / None]
  └─ Service Account JSON: [Upload file]

Phone Call Alerts (Optional — Critical alerts only)
  ├─ [Twilio Voice ▼ / None]
  └─ Uses same Twilio credentials as SMS
```

**3. Fraud Detection Integrations (Optional)**
```
IP Intelligence (Optional — free alternative built-in)
  ├─ [IPQualityScore ▼ / MaxMind / Built-in free / None]
  └─ API Key: [_______________]

Sanctions / Watchlist Screening (Optional)
  ├─ [Refinitiv ▼ / OFAC Direct (free) / None]
  └─ API Key: [_______________]

Device Intelligence (Optional)
  ├─ [ThreatMetrix ▼ / Fingerprint.js free / None]
  └─ API Key: [_______________]
```

**4. Webhook & External Alerts**
```
Outbound Webhook (Optional)
  ├─ URL: [_______________]
  ├─ Events: [☑ fraud_alert ☑ transaction_blocked ☐ all]
  └─ Secret (HMAC): [_______________]

Slack Notifications (Optional)
  └─ Webhook URL: [_______________]
```

**5. ML Model Settings**
```
Active Model: [ensemble_v1 ▼]
Model Strategy: [Shared Global ▼ / Dedicated / Hybrid]
Retraining Schedule: [Weekly ▼ / Monthly / On-demand]
Drift Alert Threshold: [0.05]

[Trigger Manual Retraining]  [Download Model Report]
```

**6. Subscription & Billing**
```
Current Plan: Pro (₹9,999/month)
Transactions Used: 234,521 / 500,000
Renewal Date: 2026-04-15

[Upgrade to Advanced]  [View Invoices]
```

### Graceful Degradation (No API Key Required)

```python
class NotificationFallbackService:
    """
    System works even without any external API keys.
    Falls back gracefully at each level.
    """
    
    async def notify(self, alert: FraudAlert):
        # Level 1: Try configured email provider
        if settings.RESEND_API_KEY:
            await self._send_resend_email(alert)
        elif settings.SENDGRID_API_KEY:
            await self._send_sendgrid_email(alert)
        elif settings.SMTP_HOST:
            await self._send_smtp_email(alert)
        else:
            # Level 2: In-app notification only (always works)
            await self._create_in_app_notification(alert)
        
        # SMS: only if configured, otherwise skip
        if settings.TWILIO_ACCOUNT_SID and alert.severity in ["critical", "high"]:
            await self._send_twilio_sms(alert)
        
        # Always: WebSocket real-time dashboard update (no API key needed)
        await self.websocket_manager.broadcast_alert(alert)
```

---

## 🧪 Test Me Tab

### Full Transaction Journey Testing

The `/dashboard/test-me` tab lets users simulate a complete end-to-end fraud detection journey without affecting live data.

#### Test Interface

```
┌─────────────────────────────────────────────────────────────────────┐
│  🧪 TEST ME — Full Transaction Journey Simulator                    │
│  ─────────────────────────────────────────────────────────────────  │
│                                                                     │
│  CUSTOMER INFO                                                      │
│  Customer ID / Name:  [_________________________]  [Lookup ▶]      │
│  Use Sample Customer: [Customer #47 — Priya Shah ▼]               │
│                                                                     │
│  CARD / ACCOUNT DETAILS                                             │
│  Card Token / Last 4: [____]  Card Type: [Visa ▼]                 │
│  Account Balance:     [₹ 85,000]  (auto-filled if customer found)  │
│                                                                     │
│  TRANSACTION DETAILS                                                │
│  Amount (₹):          [____________]                               │
│  Currency:            [INR ▼]                                      │
│  Transaction Type:    [Purchase ▼]                                 │
│  Channel:             [Online ▼]                                   │
│  Merchant Name:       [_________________________]                  │
│  Merchant Category:   [Electronics ▼]                             │
│                                                                     │
│  LOCATION & DEVICE                                                  │
│  City / Location:     [_________________________]                  │
│  Latitude / Lng:      [________] [________]  [Use My Location]    │
│  IP Address:          [_____________]  (optional)                  │
│  Device Type:         [Mobile ▼]                                   │
│  New Device:          [Yes ▼]                                      │
│                                                                     │
│  TIMING                                                             │
│  Transaction Time:    [Now ▼ / Custom]                             │
│                                                                     │
│  SCENARIO PRESETS (Quick Test):                                    │
│  [Normal Purchase] [Impossible Travel] [Velocity Fraud]            │
│  [New Device + High Amount] [Account Takeover] [Night Withdrawal]  │
│                                                                     │
│              [ ▶ RUN FRAUD DETECTION ENGINE ]                       │
└─────────────────────────────────────────────────────────────────────┘
```

#### Results Panel (Step-by-Step Journey)

```
STEP 1: DATA RECEIVED                             ✅ 0ms
  Transaction object created
  customer_id: CUST-0047 (Priya Shah)
  amount: ₹45,000
  channel: online | device: new mobile

STEP 2: CUSTOMER HISTORY LOADED                   ✅ 12ms
  Last 30-day transactions: 23
  Average transaction: ₹3,200
  Last transaction: Mumbai 6 hours ago
  Customer risk score: 0.15 (LOW)

STEP 3: FEATURE ENGINEERING                       ✅ 8ms
  Features generated: 212
  Key features:
    amount_zscore:          4.2 (HIGH — 4.2σ above avg)
    distance_from_last_txn: 1,847 km (Mumbai → Delhi)
    km_per_hour:            307 km/h (IMPOSSIBLE)
    is_new_device:          TRUE
    hour_of_day:            23 (11 PM, unusual)
    txn_count_1h:           1 (normal)

STEP 4: RULES ENGINE                              ✅ 2ms
  ✅ Rule Triggered: Impossible Travel
     Condition: 1,847 km in 6 hours (307 km/h)
     Action: BLOCK | Severity: CRITICAL
  ✅ Rule Triggered: New Device + High Amount
     Condition: new device + amount > 3× avg
     Action: FLAG | Severity: HIGH
  ❌ Rule: Velocity Spike — NOT triggered

STEP 5: ML INFERENCE                              ✅ 18ms
  Isolation Forest Score: 0.89 (ANOMALY)
  XGBoost Score:          0.94 (FRAUD)
  Random Forest Score:    0.91 (FRAUD)
  Neural Network Score:   0.93 (FRAUD)

STEP 6: ENSEMBLE SCORING                          ✅ 3ms
  Final Fraud Score: 0.91
  Decision: 🔴 BLOCK

STEP 7: ACTIONS EXECUTED                          ✅ 45ms
  ✅ Transaction written to transactions table
     fraud_score = 0.91
     fraud_category = 'fraudulent'
     fraud_risk_level = 'critical'
     status = 'blocked'
     is_test = TRUE

  ✅ Fraud Alert created (ALT-00891)
  ✅ Investigation Case auto-created (CASE-0234)
  ✅ SMS sent to customer +91-XXXXXX890
     "FinShield: ₹45,000 txn BLOCKED. New device + impossible 
      travel. If you're in Delhi, call 1800-XXX-XXXX"
  ✅ Email sent to analyst team
  ✅ Dashboard notification broadcast

TOTAL PROCESSING TIME: 88ms

─────────────────────────────────────────────────────
SHAP EXPLANATION — Top Fraud Contributors:
  1. distance_from_last_txn (+0.38)
  2. amount_zscore           (+0.24)
  3. is_new_device           (+0.19)
  4. hour_of_day             (+0.08)
  5. customer_risk_score     (+0.02)
─────────────────────────────────────────────────────

[ VIEW IN ALERTS QUEUE ]  [ MARK AS FALSE POSITIVE ]  [ NEW TEST ]
```

### Pre-built Test Scenarios

| Scenario | Setup | Expected Result |
|----------|-------|-----------------|
| **Normal Purchase** | Low amount, known merchant, same city | PASS (score <0.15) |
| **Impossible Travel** | Mumbai then Delhi in 2 hours | BLOCK (score >0.85) |
| **Velocity Fraud** | 8 transactions in 45 minutes | FLAG/BLOCK |
| **Account Takeover** | New device + password reset 20 min ago | BLOCK |
| **Night High Value** | ₹1,00,000 at 3 AM, new device | ALERT |
| **Structuring** | 5× ₹9,50,000 transactions in 6 hours | CRITICAL BLOCK |

---

## 🔧 API Architecture

### Core API Endpoints

#### Authentication
```
POST /api/v1/auth/signup           # New institution signup (with plan)
POST /api/v1/auth/login            # Returns JWT tokens
POST /api/v1/auth/refresh          # Refresh access token
GET  /api/v1/auth/me               # Current user profile
POST /api/v1/auth/logout
```

#### Transactions
```
POST /api/v1/transactions                    # Ingest + score transaction
GET  /api/v1/transactions                    # List with filters (fraud score, date, status)
GET  /api/v1/transactions/{id}               # Transaction details + fraud breakdown
GET  /api/v1/transactions/{id}/score         # Fraud analysis with SHAP
POST /api/v1/transactions/test               # Test transaction (is_test=true)
POST /api/v1/transactions/batch              # Bulk ingest (CSV/JSON)
```

#### Customers
```
POST /api/v1/customers                       # Create customer
GET  /api/v1/customers                       # List customers
GET  /api/v1/customers/{id}                  # Customer 360 view
GET  /api/v1/customers/{id}/transactions     # Transaction history
GET  /api/v1/customers/{id}/fraud-alerts     # Customer's fraud alerts
PUT  /api/v1/customers/{id}/risk-score       # Update risk score
PUT  /api/v1/customers/{id}/watchlist        # Add/remove from watchlist
```

#### Fraud Alerts
```
GET  /api/v1/alerts                          # List alerts (filter: severity, status)
GET  /api/v1/alerts/{id}                     # Alert detail
PUT  /api/v1/alerts/{id}/status              # Update status (confirm/dismiss)
POST /api/v1/cases                           # Create investigation case
GET  /api/v1/cases/{id}                      # Case details with history
```

#### ML Models
```
GET  /api/v1/models                          # List all models
GET  /api/v1/models/{id}                     # Model detail + metrics
POST /api/v1/models/{id}/promote             # Promote to production
POST /api/v1/models/retrain                  # Trigger retraining job
GET  /api/v1/models/active                   # Current active model
```

#### Rules
```
GET  /api/v1/rules                           # List rules (active/all)
POST /api/v1/rules                           # Create custom rule
PUT  /api/v1/rules/{id}                      # Update rule
DELETE /api/v1/rules/{id}                    # Delete rule
POST /api/v1/rules/{id}/test                 # Test rule on sample data
```

#### Analytics
```
GET  /api/v1/analytics/overview              # KPI dashboard data
GET  /api/v1/analytics/fraud-rate            # Fraud rate metrics over time
GET  /api/v1/analytics/fraud-trends          # Trend breakdown by type/channel
GET  /api/v1/analytics/model-performance     # Model accuracy history
GET  /api/v1/analytics/geographic            # Fraud by location
GET  /api/v1/analytics/export                # Export data (CSV/JSON)
```

#### Settings
```
GET  /api/v1/settings                        # Get all settings
PUT  /api/v1/settings/database               # Update DB connections
PUT  /api/v1/settings/notifications          # Update notification API keys
PUT  /api/v1/settings/integrations           # Update external service keys
POST /api/v1/settings/test-connection        # Test DB connection
POST /api/v1/settings/test-notification      # Send test notification
```

#### System
```
GET  /api/v1/health                          # Health check
GET  /api/v1/health/detailed                 # DB, cache, model status
GET  /api/v1/audit                           # Audit log (admin)
```

#### WebSocket Events
```
ws://host/ws/transactions     # Live transaction stream
ws://host/ws/alerts           # Live fraud alert stream
ws://host/ws/metrics          # Real-time dashboard metrics
```

### API Security
- **Rate Limiting:** 1,000 req/min (Free), 5,000 req/min (Pro), Unlimited (Advanced)
- **Authentication:** JWT (Bearer token, 15-min expiry + 7-day refresh)
- **Authorization:** RBAC per tenant (Admin/Analyst/Viewer)
- **Input Validation:** Pydantic models on all request bodies
- **CORS:** Configured per tenant origin
- **Encryption:** HTTPS only; DB credentials encrypted with AES-256

---

## 🛠️ Technology Stack

### Frontend
- **Framework:** Next.js 14 (App Router, React 18)
- **Styling:** Tailwind CSS (dark theme, custom color palette)
- **State Management:** Zustand
- **Charts:** Recharts + D3.js (heatmaps)
- **Real-Time:** Socket.IO client
- **UI Components:** shadcn/ui (dark variant)
- **Tables:** TanStack Table v8

### Backend
- **Framework:** FastAPI (Python 3.12, async)
- **Database ORM:** SQLAlchemy 2.0 (async)
- **Database:** Supabase (PostgreSQL) — primary for testing
- **Cache:** Redis 7 (session, feature cache, real-time scores)
- **Task Queue:** Celery + Redis (model training, notifications)
- **ML Runtime:** scikit-learn 1.4, XGBoost 2.0, PyTorch 2.2, ONNX Runtime
- **Validation:** Pydantic v2
- **Auth:** python-jose (JWT), passlib (bcrypt)

### Infrastructure (Free/Low-Cost Defaults)
- **DB (default):** Supabase (free tier: 500 MB, 2 CPU)
- **Email:** Resend.com (3,000/month free)
- **SMS:** Twilio (paid, ~₹0.10/SMS India)
- **Push:** Firebase FCM (free)
- **Deployment:** Vercel (frontend free tier) + Railway/Render (backend free tier)
- **Monitoring:** Supabase built-in + custom logging
- **Storage:** Supabase Storage (model artifacts)

### Data Storage Strategy
- **Primary DB:** Supabase PostgreSQL (customer + transaction data)
- **Cache:** Redis (feature cache, rate limiting, WebSocket sessions)
- **Model Storage:** Supabase Storage buckets (`.pkl`, `.onnx` files)
- **Logs:** PostgreSQL `audit_logs` table + optional external (LogDNA free tier)

---

## 💾 Local Development Setup

### Prerequisites

```bash
# Backend
Python 3.12+
Poetry (pip install poetry)
PostgreSQL 15+ (or use Supabase cloud free tier)
Redis 7+ (or use Redis Cloud free tier)

# Frontend
Node.js 20+
npm 10+

# Optional (for streaming)
Docker Desktop (for local Kafka/Event Hubs emulator)
```

### Quick Start

```bash
# 1. Clone repository
git clone <repo-url> && cd finshield

# 2. Backend setup
cd backend
cp .env.example .env
# Edit .env with your Supabase URL, keys, Resend API key, etc.
poetry install
poetry run alembic upgrade head
poetry run python scripts/generate_sample_data.py  # Generate 100 customers + 10K transactions
poetry run python scripts/train_models.py           # Train ML models
poetry run uvicorn app.main:app --reload --port 8000

# 3. Frontend setup (new terminal)
cd frontend
cp .env.local.example .env.local
npm install
npm run dev

# Access points:
# Frontend:  http://localhost:3000
# API:       http://localhost:8000
# API Docs:  http://localhost:8000/docs
```

### Docker Compose (Development)

```yaml
# docker-compose.yml
services:
  postgres:
    image: postgres:16-alpine
    ports: ["5432:5432"]
    environment:
      POSTGRES_DB: finshield
      POSTGRES_USER: finshield
      POSTGRES_PASSWORD: localdev123
    volumes: [pgdata:/var/lib/postgresql/data]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

  mailhog:
    image: mailhog/mailhog
    ports: ["1025:1025", "8025:8025"]  # SMTP + preview UI

  backend:
    build: ./backend
    ports: ["8000:8000"]
    env_file: ./backend/.env
    depends_on: [postgres, redis]

  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    env_file: ./frontend/.env.local

volumes:
  pgdata:
```

### Environment Variables

#### Backend `.env`
```env
# Database (Supabase for testing — replace with your Supabase credentials)
DATABASE_URL=postgresql+asyncpg://postgres:[YOUR_PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres
SUPABASE_URL=https://[PROJECT_REF].supabase.co
SUPABASE_ANON_KEY=[YOUR_ANON_KEY]
SUPABASE_SERVICE_KEY=[YOUR_SERVICE_KEY]

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET=your-very-long-random-secret-here-change-this
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Email (Resend.com — free tier, 3K emails/month)
RESEND_API_KEY=re_xxxxxxxxxxxxxxxx
EMAIL_FROM=noreply@finshield.ai

# SMS (Twilio — optional)
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxx
TWILIO_FROM_NUMBER=+1XXXXXXXXXX

# Firebase (push notifications — optional)
FIREBASE_SERVICE_ACCOUNT_JSON=./firebase-service-account.json

# ML
ML_MODEL_PATH=app/ml/models
ML_FRAUD_MODEL_VERSION=latest

# App
APP_ENV=development
LOG_LEVEL=DEBUG
CORS_ORIGINS=http://localhost:3000

# Encryption (for stored DB credentials)
ENCRYPTION_KEY=your-32-byte-base64-encryption-key
```

#### Frontend `.env.local`
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_WS_URL=http://localhost:8000
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=local-dev-secret-change-in-prod
```

### Makefile Commands

```makefile
make dev              # Start all services (backend + frontend + Docker)
make backend          # Start backend only
make frontend         # Start frontend only
make db-migrate       # Run Alembic migrations
make db-seed          # Generate 100 customers + 10,000 transactions
make train-models     # Train all ML models on sample data
make test             # Run all tests
make test-backend     # pytest backend
make test-frontend    # Vitest frontend
make lint             # Lint all code (ruff + eslint)
make format           # Format code (black + prettier)
make build            # Build Docker images
make docs             # Open API docs (localhost:8000/docs)
```

---

## 🧪 Testing Strategy

### Backend Testing

| Type | Tool | Coverage Target | What |
|------|------|-----------------|------|
| Unit | pytest | 80% | Services, ML pipeline, rules engine, feature engineering |
| Integration | pytest + httpx | 70% | API endpoints, DB operations, full transaction flow |
| Load | Locust | N/A | 1,000 TPS for 10 min, P95 <200ms |
| Security | OWASP ZAP | All OWASP Top 10 | Auth, injection, IDOR |

### Frontend Testing

| Type | Tool | Coverage Target | What |
|------|------|-----------------|------|
| Unit | Vitest + RTL | 75% | Components, hooks, utilities |
| E2E | Playwright | Critical paths | Auth flow, dashboard, test-me tab, alert management |
| Accessibility | axe-core | WCAG 2.1 AA | All major flows |

### ML Model Testing

| Test Type | Methodology | Pass Criteria |
|-----------|-------------|---------------|
| Data Validation | Schema checks, null rates, distribution | < 0.1% null in key fields |
| Model Validation | Holdout set evaluation | Precision >0.85, Recall >0.75, AUC-ROC >0.92 |
| Shadow Testing | New model alongside production (48h) | No regression in fraud catch rate |
| A/B Testing | 10% traffic to new model | Compare fraud catch rate, FPR |
| Drift Detection | KS-test on weekly feature distributions | p-value > 0.05 (no drift) |

### Seed Data for Testing

```python
# Default test credentials (dev only):
Admin:    admin@finshield.local  /  Admin123!@#
Analyst:  analyst@finshield.local / Analyst123!@#

# Seed generates:
100 customers (realistic Indian names, addresses, account types)
10,000 transactions (90 days, 3% fraud rate, 6 fraud pattern types)
300 fraud alerts (pre-created from seeded fraud transactions)
20 active fraud rules
3 ML model versions (1 active, 1 retired, 1 in training)
10 investigation cases
```

---

## 📈 Implementation Roadmap

### Phase 1: Foundation (Weeks 1–3)
- [ ] Project scaffolding (Next.js 14 + FastAPI + Docker Compose)
- [ ] Database schema + Supabase setup + Alembic migrations
- [ ] JWT authentication + RBAC
- [ ] Tenant management (signup with plan selection)
- [ ] UI shell: dark landing page, auth pages, dashboard skeleton

### Phase 2: Subscription & Onboarding (Weeks 4–5)
- [ ] 3-tier subscription plan UI (Free / Pro / Advanced)
- [ ] Razorpay payment integration (Pro/Advanced)
- [ ] Signup wizard: plan → schema → DB connection → initialization
- [ ] Custom schema builder (Advanced plan)
- [ ] First-run: pull data, add fraud columns, show progress bar

### Phase 3: Sample Data & Model Training (Weeks 6–7)
- [ ] Generate 100-customer sample data script
- [ ] Generate 10,000-transaction sample data with 6 fraud patterns
- [ ] Feature engineering module (200+ features)
- [ ] Train Isolation Forest, DBSCAN, XGBoost, Random Forest, Neural Network
- [ ] Ensemble scorer with calibrated weights
- [ ] ONNX export for neural network
- [ ] Model registry API + evaluation report

### Phase 4: Data Integration & Connectors (Weeks 8–10)
- [ ] Connector abstraction layer
- [ ] Supabase connector (default)
- [ ] Generic PostgreSQL/MySQL connector
- [ ] CSV batch upload connector
- [ ] Stripe/Razorpay webhook connector
- [ ] Schema normalization pipeline
- [ ] Real-time polling for Supabase

### Phase 5: Fraud Detection Core (Weeks 11–13)
- [ ] Rules engine (YAML DSL, 20 built-in rules)
- [ ] Custom rule builder API + UI
- [ ] Live transaction scoring pipeline
- [ ] Fraud score write-back to user's transaction table
- [ ] Decision engine (PASS/FLAG/ALERT/BLOCK)
- [ ] Post-settlement fraud detection for batch mode

### Phase 6: Alerts, Notifications & Post-Detection (Weeks 14–15)
- [ ] Fraud alert creation and management
- [ ] Multi-channel notifications (Resend email, Twilio SMS, FCM push)
- [ ] Graceful degradation (works without any API keys)
- [ ] WebSocket real-time alert broadcasting
- [ ] Investigation case management
- [ ] Card pause integration (optional)

### Phase 7: Dashboard & Analytics (Weeks 16–17)
- [ ] Post-login dashboard: data overview + KPI cards
- [ ] Live transaction feed
- [ ] Customer data details view
- [ ] Fraud trends visualization (Recharts + D3.js)
- [ ] Model performance panel + SHAP charts
- [ ] Admin system monitoring dashboard

### Phase 8: Test Me Tab & Settings (Weeks 18–19)
- [ ] Test Me tab: full transaction simulator UI
- [ ] Pre-built test scenarios (6 fraud patterns)
- [ ] Step-by-step journey results panel
- [ ] Settings page: all API keys dynamic management
- [ ] Connection test for every integration
- [ ] Fallback logic verification

### Phase 9: Multi-Tenancy, Drift & Scaling (Weeks 20–21)
- [ ] Row-level security (Supabase RLS policies)
- [ ] Tenant model drift detection service
- [ ] Automated retraining pipeline
- [ ] Transfer learning for new Advanced tenants
- [ ] Performance optimization (query caching, connection pooling)

### Phase 10: Hardening & Launch (Weeks 22–24)
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Security audit (OWASP Top 10, auth review)
- [ ] Load testing (Locust: 1,000 TPS target)
- [ ] Documentation (API docs, user guide)
- [ ] Landing page final polish (all ribbons, animations)
- [ ] Production deployment (Vercel + Railway/Render)
- [ ] Go-live monitoring

---

## 💻 Coding Conventions

### Python (Backend)
- Follow PEP 8 via `ruff`
- Use `async/await` for all I/O operations
- Type hints on all function signatures
- Docstrings on public functions (Google style)
- Architecture pattern: `API Routes → Services → Repositories → Models`
- Dependency injection via FastAPI's `Depends()`
- Use Pydantic v2 models for all request/response schemas
- Custom exceptions inheriting from base `AppException`
- Structured logging with `structlog` + correlation IDs
- Never store plaintext credentials — always encrypt with `ENCRYPTION_KEY`

### TypeScript (Frontend)
- Strict TypeScript (`"strict": true` in tsconfig, no `any`)
- Functional components only
- Custom hooks for reusable logic (prefix: `use`)
- Use `cn()` utility for conditional Tailwind classes
- Server components by default; `"use client"` only when needed
- Zod schemas that mirror backend Pydantic models
- Dark theme first: all components default to `#0A0A0F` background

### Git
- Branch naming: `feature/`, `fix/`, `hotfix/`, `chore/`, `docs/`
- Conventional commits: `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`
- Squash merge PRs to `main`
- Require 1+ PR review
- All CI checks must pass before merge

---

## 📚 Glossary

| Term | Definition |
|------|-----------|
| **Fraud Score** | ML-generated probability (0.0–1.0) that a transaction is fraudulent |
| **Risk Score** | Composite score combining ML, rules, behavioral, and entity factors |
| **Fraud Category** | Classification: legitimate / suspicious / fraudulent / unscored |
| **Feature Engineering** | Process of extracting 200+ features from raw transaction data |
| **Velocity Check** | Rule counting transaction frequency in a time window (1h, 24h, etc.) |
| **Impossible Travel** | Two transactions in locations physically unreachable in elapsed time |
| **Model Drift** | Statistical degradation in model accuracy over time due to changing fraud patterns |
| **False Positive** | A legitimate transaction incorrectly flagged as fraud |
| **SHAP Values** | Explainability method showing each feature's contribution to fraud prediction |
| **ONNX** | Open Neural Network Exchange — portable ML model format for fast inference |
| **Multi-Tenancy** | Single platform serving multiple isolated institutions |
| **Connector** | Integration module to pull/push data from external banking/payment systems |
| **Schema Normalization** | Converting connector-specific field names to FinShield standard format |
| **Ensemble Scoring** | Combining outputs of multiple ML models into a single calibrated fraud score |
| **SMOTE** | Synthetic Minority Over-sampling Technique — handles class imbalance in training |
| **CDC** | Change Data Capture — real-time DB-level event streaming for new rows |
| **Shadow Mode** | Running a new model alongside production without affecting decisions |
| **SAR** | Suspicious Activity Report — regulatory filing for confirmed fraud cases |
| **KYC** | Know Your Customer — identity verification process |
| **PEP** | Politically Exposed Person — higher risk category for AML screening |
| **Dead Letter Queue** | Queue for messages that failed processing after maximum retry attempts |
| **Row-Level Security** | Database policy ensuring each tenant only accesses their own rows |
| **Transfer Learning** | Using a global pre-trained model as base for tenant-specific fine-tuning |

---

## ✅ Implementation Checklist

### Core Platform
- [ ] Dark landing page with 10 ribbon sections (incl. Project Guide)
- [ ] 3-tier subscription plans (Free / Pro ₹9,999 / Advanced ₹24,999)
- [ ] Signup wizard with schema selection + DB connection
- [ ] First-run: pull data → train models → add fraud columns
- [ ] Login with per-tenant dashboard showing own data
- [ ] Post-login: customer data details, KPI cards, live feed

### Data & ML
- [ ] 100 sample customers generated (Indian locale)
- [ ] 10,000 sample transactions with 6 fraud patterns (3% fraud rate)
- [ ] Feature engineering: 200+ features
- [ ] 5 ML models trained on sample data (IF, DBSCAN, XGBoost, RF, NN)
- [ ] Ensemble scorer with calibrated weights
- [ ] ONNX export for <20ms inference
- [ ] Model drift detection + automated retraining

### Integrations
- [ ] Supabase as primary DB (testing)
- [ ] 20 connector types supported
- [ ] Schema normalization pipeline
- [ ] Resend.com email (free tier default)
- [ ] Twilio SMS (optional, paid)
- [ ] Firebase FCM push (optional, free)
- [ ] All integrations gracefully degrade if no API key

### User Features
- [ ] Test Me tab: full transaction journey simulator
- [ ] 6 pre-built fraud test scenarios
- [ ] Step-by-step journey results with SHAP explanation
- [ ] Settings page: all API keys dynamically managed
- [ ] Custom rule builder (YAML DSL)
- [ ] Alert management: confirm fraud / dismiss / investigate
- [ ] Admin dashboard: model performance + system health

---

*This document is the single source of truth for the FinShield AI platform.*
*All development, architecture, and product decisions reference this specification.*
*Last updated: 2026-03-23*