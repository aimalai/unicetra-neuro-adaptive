from typing import Dict, Any, List
from neo4j.exceptions import Neo4jError, ServiceUnavailable
from app.core.neo4j import neo4j_connector

def fetch_node_with_provenance(node_id: str) -> Dict[str, Any]:
    """
    Executes a Cypher query to retrieve a target node and its parent section
    topological context from Neo4j.
    """
    fallback_mock = {
        "node_id": node_id,
        "text_content": f"Sample operating text content for node {node_id}.",
        "labels": ["Article"],
        "parent": {
            "parent_id": "Section_Preamble",
            "parent_content": "Document Preamble"
        }
    }

    try:
        driver = neo4j_connector.get_driver()
        query = """
        MATCH (n {node_id: $node_id})
        OPTIONAL MATCH (s:Section)-[:HAS_CHUNK]->(n)
        OPTIONAL MATCH (n)-[:REQUIRES_CONTEXT|HAS_PARENT]->(parent)
        RETURN n.node_id AS node_id, 
               n.text_content AS text_content, 
               labels(n) AS labels,
               coalesce(parent.node_id, s.name) AS parent_id,
               coalesce(parent.text_content, s.name) AS parent_content
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


def search_graph_by_query(query_text: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Executes a graph containment query across ingested chunks, returning matching
    nodes along with their parent section headers.
    """
    try:
        driver = neo4j_connector.get_driver()
        cypher = """
        MATCH (c)
        WHERE (c:DocumentChunk OR c:Article) AND toLower(c.text_content) CONTAINS toLower($query_text)
        OPTIONAL MATCH (s:Section)-[:HAS_CHUNK]->(c)
        RETURN c.node_id AS node_id,
               c.text_content AS text_content,
               coalesce(s.name, "General Section") AS section_header
        LIMIT $limit
        """
        with driver.session() as session:
            records = session.run(cypher, query_text=query_text, limit=limit)
            results = []
            for r in records:
                results.append({
                    "node_id": r["node_id"],
                    "text_content": r["text_content"],
                    "section_header": r["section_header"]
                })
            return results
    except Exception as e:
        print(f"Graph search error: {e}")
        return []


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


def save_chunks_to_neo4j(validated_nodes: List[Dict[str, Any]], doc_name: str = "EU_AI_Act"):
    """
    Persists validated nodes into Neo4j graph storage with full structural hierarchy.
    """
    initialize_vector_index()
    try:
        driver = neo4j_connector.get_driver()
        with driver.session() as session:
            session.execute_write(_insert_chunks_transaction, validated_nodes, doc_name)
    except Exception as e:
        print(f"Neo4j persistence warning: {e}")


def _insert_chunks_transaction(tx, nodes, doc_name):
    # Step 1: Batch MERGE Document -> Section -> Chunk relationships
    query = """
    MERGE (d:Document {id: $doc_name})
    WITH d
    UNWIND $nodes AS row
    
    MERGE (s:Section {name: coalesce(row.section_header, "Document Preamble"), doc_id: $doc_name})
    MERGE (d)-[:HAS_SECTION]->(s)
    
    MERGE (c:DocumentChunk {node_id: row.node_id})
    SET c.text_content = row.text_content,
        c.category = row.node_type,
        c:Article
        
    MERGE (s)-[:HAS_CHUNK]->(c)
    """
    tx.run(query, nodes=nodes, doc_name=doc_name)

    # Step 2: Connect sequential NEXT relationships between consecutive chunks
    seq_query = """
    UNWIND range(0, size($nodes)-2) AS idx
    WITH $nodes[idx] AS curr, $nodes[idx+1] AS next_node
    MATCH (c1:DocumentChunk {node_id: curr.node_id})
    MATCH (c2:DocumentChunk {node_id: next_node.node_id})
    MERGE (c1)-[:NEXT]->(c2)
    """
    tx.run(seq_query, nodes=nodes)