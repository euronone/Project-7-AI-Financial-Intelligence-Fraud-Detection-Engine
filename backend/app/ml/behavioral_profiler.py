from typing import Dict, Any, List
import pandas as pd

class BehavioralProfiler:
    """
    F2.3: Behavioral Profiling
    Builds per-entity baselines and flags deviations.
    """
    def __init__(self):
        pass
        
    def profile(self, transaction: Dict[str, Any], entity_history: List[Dict[str, Any]]) -> float:
        """
        Returns a behavioral deviation score (0.0 to 1.0).
        High score means highly unusual behavior for this specific entity.
        """
        amount = transaction.get("amount", 0.0)
        
        # If no history, we can't profile well, return neutral/slight risk
        if not entity_history:
            return 0.3
            
        # Calculate baseline
        amounts = [t.get("amount", 0.0) for t in entity_history]
        avg_amount = sum(amounts) / len(amounts)
        
        # Calculate deviation
        if avg_amount == 0:
            return 0.5 if amount > 0 else 0.0
            
        deviation = abs(amount - avg_amount) / avg_amount
        
        # Map deviation to a 0-1 score (squashing function)
        # e.g., deviation of 0 -> 0.0, deviation of 2.0 (3x average) -> ~0.8
        score = min(1.0, deviation / 3.0)
        
        return score
