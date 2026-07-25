from typing import Dict, Any, List
from app.services.document_parser import ingestion_parser
from app.services.schema_mapper import schema_loader
from app.services.graph_service import save_chunks_to_neo4j

class UniversalIngestionController:
    def __init__(self):
        self.parser = ingestion_parser
        self.schema = schema_loader

    def process_and_validate_document(self, file_path: str, node_type: str = "Article") -> Dict[str, Any]:
        """
        Universal commercial ingestion pipeline:
        1. Parses raw files format-agnostically (PDF, Word, HTML).
        2. Dynamically generates the validation model from the active YAML schema.
        3. Enforces hierarchical structural rules.
        4. Persists validated structural nodes into Neo4j graph database.
        """
        # Step 1: Extract semantic chunks using format-agnostic parsing
        raw_chunks = self.parser.parse_document(file_path)
        
        # Step 2: Dynamically fetch the runtime Pydantic model based on active YAML schema
        DynamicModel = self.schema.generate_dynamic_model(node_type)
        
        validated_elements = []
        for chunk in raw_chunks:
            # Construct payload mapping chunk data to schema constraints
            payload = {
                "node_id": chunk.get("element_id", "node_unknown"),
                "text_content": chunk.get("text", ""),
                "node_type": node_type
            }
            
            # Runtime validation ensuring enterprise structural compliance
            try:
                validated_node = DynamicModel(**payload)
                validated_elements.append(validated_node.model_dump())
            except Exception as e:
                print(f"Validation warning for element {payload['node_id']}: {e}")

        # Step 3: Persist validated nodes into Neo4j graph storage & vector index
        if validated_elements:
            save_chunks_to_neo4j(validated_elements)

        return {
            "status": "SUCCESS",
            "domain": self.schema.schema_definition.get("domain"),
            "processed_chunks_count": len(validated_elements),
            "validated_nodes": validated_elements
        }

# Global ingestion controller instance
ingestion_controller = UniversalIngestionController()