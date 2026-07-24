from pydantic import BaseModel
from typing import List

class AuditRequest(BaseModel):
    chunks: List[str]
    min_entropy_threshold: float = 1.5

class AuditPayload(BaseModel):
    text_content: str

class CompressionResult(BaseModel):
    shannon_entropy: float
    original_length: int
    compressed_length: int
    c2k_ratio: float
    pruned_text: str