from pydantic import BaseModel
from typing import Dict

class IntegrityReport(BaseModel):
    is_valid: bool
    honest_ignorance_triggered: bool
    fan_scores: Dict[str, float]

def evaluate_3_fan_window(text_payload: str, threshold: float = 0.85) -> IntegrityReport:
    """
    Evaluates text through a 3-Fan Window (Surprisal, Structural, Positional).
    The threshold is dynamically steered by the human-in-the-loop UI.
    """
    if not text_payload:
        return IntegrityReport(
            is_valid=False, 
            honest_ignorance_triggered=True, 
            fan_scores={"surprisal": 0.0, "structural": 0.0, "positional": 0.0}
        )

    # Mock evaluation logic for the 3-Fan Window metrics
    surprisal_score = 0.88  
    structural_score = 0.95 
    positional_score = 0.82 
    
    scores = {
        "surprisal": surprisal_score,
        "structural": structural_score,
        "positional": positional_score
    }
    
    # If any fan falls below the dynamically steered threshold, the gate locks
    is_valid = all(score >= threshold for score in scores.values())
    
    return IntegrityReport(
        is_valid=is_valid,
        honest_ignorance_triggered=not is_valid,
        fan_scores=scores
    )