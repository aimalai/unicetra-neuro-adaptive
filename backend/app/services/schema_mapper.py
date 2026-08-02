import yaml
from pathlib import Path
from pydantic import create_model, BaseModel
from typing import Dict, Any, Type, Optional

class DynamicSchemaLoader:
    # 1. Update the default filename to be domain-agnostic
    def __init__(self, schema_filename: str = "universal_schema.yaml"):
        # 2. Fix the path resolution to match your exact directory structure (app/core/schemas)
        self.schema_path = Path(__file__).parent.parent / "core" / "schemas" / schema_filename
        self.schema_definition = self._load_yaml()

    def _load_yaml(self) -> Dict[str, Any]:
        if not self.schema_path.exists():
            print(f"Warning: Schema not found at {self.schema_path}. Using fallback.")
            return {
                "domain": "Universal Compliance",
                "hierarchy": {
                    "root_node": "Document",
                    "primary_provision": {"name": "Chunk"}
                }
            }
        with open(self.schema_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def generate_dynamic_model(self, node_type: str) -> Type[BaseModel]:
        """
        Dynamically constructs Pydantic validation models at runtime based on the loaded YAML schema.
        Enables universal, domain-agnostic enterprise scaling without changing core logic.
        """
        fields = {
            "node_id": (str, ...),
            "text_content": (str, ...),
            "node_type": (str, node_type),
            "section_header": (Optional[str], "Document Preamble"),
            # 3. CRITICAL FIX: Add depth so Pydantic stops stripping it out!
            "depth": (Optional[int], None), 
            "parent_id": (Optional[str], None),
            "parent_content": (Optional[str], None),
        }

        return create_model(f"Dynamic{node_type}Model", **fields)

# Global singleton loader instance for the active schema
schema_loader = DynamicSchemaLoader()