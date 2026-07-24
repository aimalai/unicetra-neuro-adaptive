from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class NodeParentInfo(BaseModel):
    parent_id: str
    parent_content: str

class NodeProvenanceResponse(BaseModel):
    node_id: str
    text_content: str
    labels: List[str]
    parent: Optional[NodeParentInfo] = None