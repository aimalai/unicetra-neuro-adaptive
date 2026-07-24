import yaml
from pydantic import create_model
from typing import Optional, Dict, Any

def load_schema_config(file_path: str = "app/core/schemas/eu_law_schema.yaml") -> Dict[str, Any]:
    """Loads the ontological schema rules from the YAML file."""
    with open(file_path, "r") as file:
        return yaml.safe_load(file)

def generate_dynamic_models() -> Dict[str, Any]:
    """Dynamically generates Pydantic models based on the YAML nodes."""
    schema_data = load_schema_config()
    models = {}
    
    for node_name, attributes in schema_data.get("nodes", {}).items():
        # Define the fields every node will need, plus its specific parent requirement
        fields = {
            "node_id": (str, ...),
            "text_content": (str, ...),
            "required_parent": (Optional[str], attributes.get("required_parent"))
        }
        
        # Build the Pydantic model at runtime
        models[node_name] = create_model(node_name, **fields)
        
    return models

# Generate the models immediately when the application starts
dynamic_models = generate_dynamic_models()