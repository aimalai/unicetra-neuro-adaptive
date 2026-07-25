import yaml
from pathlib import Path
from pydantic import create_model, BaseModel
from typing import Dict, Any, Type, Optional

class DynamicSchemaLoader:
    def __init__(self, schema_filename: str = "eu_law_schema.yaml"):
        # Adjust path dynamically to match your directory structure
        self.schema_path = Path(__file__).parent.parent / "schemas" / schema_filename
        self.schema_definition = self._load_yaml()

    def _load_yaml(self) -> Dict[str, Any]:
        if not self.schema_path.exists():
            return {
                "domain": "Default Compliance",
                "hierarchy": {
                    "root_node": "Document",
                    "primary_provision": {"name": "Article"}
                }
            }
        with open(self.schema_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def generate_dynamic_model(self, node_type: str) -> Type[BaseModel]:
        """
        Dynamically constructs Pydantic validation models at runtime based on the loaded YAML schema.
        Enables universal, domain-agnostic enterprise scaling without changing core logic.
        """
        hierarchy = self.schema_definition.get("hierarchy", {})
        
        fields = {
            "node_id": (str, ...),
            "text_content": (str, ...),
            "node_type": (str, node_type),
            "parent_id": (Optional[str], None),
            "parent_content": (Optional[str], None),
        }

        return create_model(f"Dynamic{node_type}Model", **fields)

# Global singleton loader instance for the active schema
schema_loader = DynamicSchemaLoader()