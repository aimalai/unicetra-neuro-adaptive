from typing import Dict, Any
from neo4j.exceptions import Neo4jError, ServiceUnavailable
from app.core.neo4j import neo4j_connector

def fetch_node_with_provenance(node_id: str) -> Dict[str, Any]:
    """
    Executes a Cypher query to retrieve a target node and its required 
    topological context. Falls back to mock provenance data if Neo4j is offline.
    """
    fallback_mock = {
        "node_id": node_id,
        "text_content": f"Sample operating text content for node {node_id}.",
        "labels": ["Article"],
        "parent": {
            "parent_id": "Recital_1",
            "parent_content": "Sample interpretive recital context from fallback."
        }
    }

    try:
        driver = neo4j_connector.get_driver()
        
        query = """
        MATCH (n {node_id: $node_id})
        OPTIONAL MATCH (n)-[:REQUIRES_CONTEXT|HAS_PARENT]->(parent)
        RETURN n.node_id AS node_id, 
               n.text_content AS text_content, 
               labels(n) AS labels,
               parent.node_id AS parent_id,
               parent.text_content AS parent_content
        """
        
        with driver.session() as session:
            result = session.run(query, node_id=node_id)
            record = result.single()
            
            if not record or not record["node_id"]:
                return fallback_mock
                
            return {
                "node_id": record["node_id"],
                "text_content": record["text_content"],
                "labels": record["labels"],
                "parent": {
                    "parent_id": record["parent_id"],
                    "parent_content": record["parent_content"]
                } if record["parent_id"] else None
            }
            
    except (ServiceUnavailable, Neo4jError, Exception):
        # Graceful fallback when Neo4j container/server is not active locally
        return fallback_mock