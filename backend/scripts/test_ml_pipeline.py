import sys
import os
import json
import random
import uuid
from datetime import datetime, timedelta
import pandas as pd

# Add backend directory to sys.path so we can import app modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.services.fraud_detection_service import FraudDetectionService

def generate_sample_transactions(num_samples=1000):
    """Generate a realistic dataset of sample transactions for testing."""
    print(f"Generating {num_samples} sample transactions...")
    
    transactions = []
    
    # Define some entity pools
    user_ids = [f"user_{i}" for i in range(1, 101)]
    merchant_ids = [f"merchant_{i}" for i in range(1, 51)]
    device_ids = [f"device_{i}" for i in range(1, 151)]
    ip_addresses = [f"192.168.1.{i}" for i in range(1, 201)]
    
    # Generate transactions over the past 30 days
    end_time = datetime.now()
    start_time = end_time - timedelta(days=30)
    
    for _ in range(num_samples):
        # Decide if this should be an anomalous/fraudulent transaction
        is_fraud_scenario = random.random() < 0.05  # 5% chance of being an explicit fraud scenario
        
        # Base properties
        tx_id = str(uuid.uuid4())
        user_id = random.choice(user_ids)
        merchant_id = random.choice(merchant_ids)
        
        # Time generation
        random_seconds = random.randint(0, int((end_time - start_time).total_seconds()))
        tx_time = start_time + timedelta(seconds=random_seconds)
        
        # Amount generation based on scenario
        if is_fraud_scenario:
            # Fraud scenarios tend to have either very small (testing) or very large amounts
            amount = random.choice([
                random.uniform(0.5, 5.0),    # Card testing
                random.uniform(5000, 25000)  # High value fraud
            ])
        else:
            # Normal distribution for regular transactions
            # Mean $100, std dev $50, but bounded to positive values
            amount = max(1.0, random.gauss(100, 50))
            
            # Occasionally add some larger but normal purchases
            if random.random() < 0.1:
                amount = random.uniform(500, 2000)
                
        # Device and location
        device_id = random.choice(device_ids)
        
        # If fraud, maybe simulate a new device or suspicious IP
        if is_fraud_scenario and random.random() < 0.7:
            device_id = f"suspicious_device_{random.randint(1,10)}"
            ip_address = f"10.0.0.{random.randint(1,255)}" # Different subnet
            location = "High Risk Country"
        else:
            ip_address = random.choice(ip_addresses)
            location = "US"
            
        transaction = {
            "id": tx_id,
            "source_entity_id": user_id,
            "target_entity_id": merchant_id,
            "amount": round(amount, 2),
            "currency": "USD",
            "timestamp": tx_time.isoformat() + "Z",
            "device_id": device_id,
            "ip_address": ip_address,
            "location": location,
            "transaction_type": "purchase"
        }
        
        transactions.append(transaction)
        
    return transactions

def test_ml_pipeline():
    """Test the ML pipeline with the generated transactions."""
    transactions = generate_sample_transactions(1000)
    
    print(f"\nInitializing FraudDetectionService...")
    service = FraudDetectionService()
    
    print(f"Running {len(transactions)} transactions through the pipeline...")
    results = []
    
    for i, tx in enumerate(transactions):
        if (i + 1) % 100 == 0:
            print(f"Processed {i + 1}/{len(transactions)} transactions...")
            
        result = service.detect_fraud(tx)
        
        # Combine transaction data with result for analysis
        combined = {
            "tx_id": tx["id"],
            "amount": tx["amount"],
            "status": result["status"],
            "risk_score": result["risk_score"],
            "ml_score": result["components"]["ml_score"],
            "anomaly_score": result["components"]["anomaly_score"],
            "behavioral_score": result["components"]["behavioral_score"],
            "network_score": result["components"]["network_score"],
            "rule_score": result["components"]["rule_score"],
            "triggered_rules": len(result["triggered_rules"])
        }
        results.append(combined)
        
    # Analyze results
    df = pd.DataFrame(results)
    
    print("\n" + "="*50)
    print("PIPELINE TEST RESULTS")
    print("="*50)
    
    print("\n1. Status Distribution:")
    status_counts = df['status'].value_counts()
    for status, count in status_counts.items():
        percentage = (count / len(df)) * 100
        print(f"  - {status}: {count} ({percentage:.1f}%)")
        
    print("\n2. Risk Score Summary:")
    print(f"  - Mean: {df['risk_score'].mean():.3f}")
    print(f"  - Median: {df['risk_score'].median():.3f}")
    print(f"  - Min: {df['risk_score'].min():.3f}")
    print(f"  - Max: {df['risk_score'].max():.3f}")
    
    print("\n3. Component Score Averages:")
    print(f"  - ML Score: {df['ml_score'].mean():.3f}")
    print(f"  - Anomaly Score: {df['anomaly_score'].mean():.3f}")
    print(f"  - Behavioral Score: {df['behavioral_score'].mean():.3f}")
    print(f"  - Network Score: {df['network_score'].mean():.3f}")
    print(f"  - Rule Score: {df['rule_score'].mean():.3f}")
    
    print("\n4. High Risk Transactions (Score > 0.8):")
    high_risk = df[df['risk_score'] > 0.8]
    print(f"  - Count: {len(high_risk)} ({len(high_risk)/len(df)*100:.1f}%)")
    if not high_risk.empty:
        print(f"  - Average Amount: ${high_risk['amount'].mean():.2f}")
        
    print("\n5. Rule Triggers:")
    rule_triggers = df[df['triggered_rules'] > 0]
    print(f"  - Transactions triggering rules: {len(rule_triggers)} ({len(rule_triggers)/len(df)*100:.1f}%)")
    
    print("\nSample of Blocked/Alerted Transactions:")
    alerts = df[df['status'].isin(['BLOCK', 'ALERT'])].head(5)
    if not alerts.empty:
        print(alerts[['amount', 'risk_score', 'status', 'ml_score', 'rule_score']].to_string())
    else:
        print("  - None found in this sample.")

if __name__ == "__main__":
    test_ml_pipeline()
