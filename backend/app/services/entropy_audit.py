import math
from collections import Counter
from typing import List, Dict, Any

def calculate_shannon_entropy(text: str) -> float:
    """
    Calculates the Shannon Entropy (H) of a given text string based on token frequencies.
    Higher values indicate higher information density; lower values indicate repetitive boilerplate.
    """
    tokens = text.lower().split()
    if not tokens:
        return 0.0

    total_tokens = len(tokens)
    token_counts = Counter(tokens)
    
    entropy = 0.0
    for count in token_counts.values():
        probability = count / total_tokens
        entropy -= probability * math.log2(probability)
        
    return round(entropy, 4)

def calculate_context_compression(original_chunks: List[str], min_entropy_threshold: float = 1.5) -> Dict[str, Any]:
    """
    Executes the Recursive Entropy Audit (REA) over retrieved document chunks.
    Filters out chunks falling below the minimum information density threshold.
    """
    audited_chunks = []
    pruned_count = 0
    
    for chunk in original_chunks:
        entropy_score = calculate_shannon_entropy(chunk)
        if entropy_score >= min_entropy_threshold:
            audited_chunks.append({
                "chunk_text": chunk,
                "entropy_score": entropy_score
            })
        else:
            pruned_count += 1
            
    compression_ratio = round(len(audited_chunks) / len(original_chunks), 2) if original_chunks else 0.0

    return {
        "retained_chunks": audited_chunks,
        "pruned_chunks_count": pruned_count,
        "context_compression_ratio": compression_ratio
    }