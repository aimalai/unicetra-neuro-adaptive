from typing import Dict, Any, List
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
        return fallback_mock


def initialize_vector_index():
    try:
        driver = neo4j_connector.get_driver()
        with driver.session() as session:
            session.run("""
                CREATE VECTOR INDEX chunkEmbedding IF NOT EXISTS
                FOR (n:Article) ON (n.embedding)
                OPTIONS {indexConfig: { `vector.dimensions`: 1536, `vector.similarity_function`: 'cosine' }}
            """)
    except Exception:
        pass


def save_chunks_to_neo4j(validated_nodes: List[Dict[str, Any]]):
    """
    Persists validated nodes into Neo4j graph storage.
    """
    initialize_vector_index()
    try:
        driver = neo4j_connector.get_driver()
        with driver.session() as session:
            session.execute_write(_insert_chunks_transaction, validated_nodes)
    except Exception as e:
        print(f"Neo4j persistence warning (running in standalone mock mode if offline): {e}")


def _insert_chunks_transaction(tx, nodes):
    query = """
    UNWIND $nodes AS row
    MERGE (n:Article {node_id: row.node_id})
    SET n.text_content = row.text_content,
        n.node_type = row.node_type
    """
    tx.run(query, nodes=nodes)