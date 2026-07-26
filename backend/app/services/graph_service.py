from typing import Dict, Any, List
from neo4j.exceptions import Neo4jError, ServiceUnavailable
from app.core.neo4j import neo4j_connector
from sentence_transformers import SentenceTransformer

# Initialize local lightweight open-source embedding model (runs completely offline)
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

def get_text_embedding(text: str) -> List[float]:
    """Generates a 384-dimensional vector embedding locally."""
    if not text.strip():
        return [0.0] * 384
    return embedding_model.encode(text).tolist()


def fetch_node_with_provenance(node_id: str) -> Dict[str, Any]:
    """
    Executes a multi-hop Cypher query to retrieve a target node, 
    its parent section header, AND its sequential previous/next siblings 
    to populate the interactive D3 graph canvas.
    """
    fallback_mock = {
        "node_id": node_id,
        "text_content": f"Sample operating text content for node {node_id}.",
        "labels": ["Article"],
        "parent": {
            "parent_id": "Section_Preamble",
            "parent_content": "Document Preamble"
        },
        "previous_node": None,
        "next_node": None
    }

    try:
        driver = neo4j_connector.get_driver()
        query = """
        MATCH (n {node_id: $node_id})
        OPTIONAL MATCH (s:Section)-[:HAS_CHUNK]->(n)
        OPTIONAL MATCH (prev)-[:NEXT]->(n)
        OPTIONAL MATCH (n)-[:NEXT]->(next_n)
        RETURN n.node_id AS node_id, 
               n.text_content AS text_content, 
               labels(n) AS labels,
               s.name AS parent_id,
               s.name AS parent_content,
               prev.node_id AS prev_id,
               prev.text_content AS prev_content,
               next_n.node_id AS next_id,
               next_n.text_content AS next_content
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
                    "parent_id": record["parent_id"] or "Document Preamble",
                    "parent_content": record["parent_content"] or "Document Preamble"
                } if record["parent_id"] else None,
                "previous_node": {
                    "node_id": record["prev_id"],
                    "text_content": record["prev_content"]
                } if record["prev_id"] else None,
                "next_node": {
                    "node_id": record["next_id"],
                    "text_content": record["next_content"]
                } if record["next_id"] else None
            }
    except (ServiceUnavailable, Neo4jError, Exception) as e:
        print(f"Error fetching node provenance: {e}")
        return fallback_mock


def search_graph_by_query(query_text: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Performs hybrid Vector Similarity + Multi-Hop Graph Traversal.
    Converts query to embedding vector and finds top K closest nodes in Neo4j.
    """
    try:
        query_vector = get_text_embedding(query_text)
        driver = neo4j_connector.get_driver()
        
        # Cypher Vector Query using Neo4j vector index
        cypher = """
        CALL db.index.vector.queryNodes('chunkEmbedding', $limit, $query_vector)
        YIELD node AS c, score
        OPTIONAL MATCH (s:Section)-[:HAS_CHUNK]->(c)
        OPTIONAL MATCH (c)-[:NEXT]->(next_c:DocumentChunk)
        OPTIONAL MATCH (prev_c:DocumentChunk)-[:NEXT]->(c)
        RETURN c.node_id AS node_id,
               c.text_content AS text_content,
               coalesce(s.name, "Document Preamble") AS section_header,
               prev_c.text_content AS prev_content,
               next_c.text_content AS next_content,
               score
        ORDER BY score DESC
        """
        with driver.session() as session:
            records = session.run(cypher, query_vector=query_vector, limit=limit)
            results = []
            for r in records:
                enriched_text = ""
                if r["prev_content"]: 
                    enriched_text += f"[PREVIOUS PARAGRAPH]: {r['prev_content']} \n\n"
                
                enriched_text += f"[EXACT MATCH]: {r['text_content']} \n\n"
                
                if r["next_content"]: 
                    enriched_text += f"[NEXT PARAGRAPH]: {r['next_content']}"
                
                results.append({
                    "node_id": r["node_id"],
                    "section_header": r["section_header"],
                    "exact_match": r["text_content"],
                    "multi_hop_context": enriched_text.strip(),
                    "similarity_score": round(float(r["score"]), 4)
                })
            return results
    except Exception as e:
        print(f"Vector search fallback to lexical matching due to: {e}")
        # Fallback to lexical containment if index is still building
        return _fallback_lexical_search(query_text, limit)


def _fallback_lexical_search(query_text: str, limit: int = 5) -> List[Dict[str, Any]]:
    try:
        driver = neo4j_connector.get_driver()
        cypher = """
        MATCH (c:DocumentChunk)
        WHERE toLower(c.text_content) CONTAINS toLower($query_text)
        OPTIONAL MATCH (s:Section)-[:HAS_CHUNK]->(c)
        OPTIONAL MATCH (c)-[:NEXT]->(next_c:DocumentChunk)
        OPTIONAL MATCH (prev_c:DocumentChunk)-[:NEXT]->(c)
        RETURN c.node_id AS node_id,
               c.text_content AS text_content,
               coalesce(s.name, "Document Preamble") AS section_header,
               prev_c.text_content AS prev_content,
               next_c.text_content AS next_content
        LIMIT $limit
        """
        with driver.session() as session:
            records = session.run(cypher, query_text=query_text, limit=limit)
            results = []
            for r in records:
                enriched_text = ""
                if r["prev_content"]: 
                    enriched_text += f"[PREVIOUS PARAGRAPH]: {r['prev_content']} \n\n"
                
                enriched_text += f"[EXACT MATCH]: {r['text_content']} \n\n"
                
                if r["next_content"]: 
                    enriched_text += f"[NEXT PARAGRAPH]: {r['next_content']}"
                
                results.append({
                    "node_id": r["node_id"],
                    "section_header": r["section_header"],
                    "exact_match": r["text_content"],
                    "multi_hop_context": enriched_text.strip()
                })
            return results
    except Exception:
        return []


def initialize_vector_index():
    """Initializes a 384-dimensional vector index for SentenceTransformers."""
    try:
        driver = neo4j_connector.get_driver()
        with driver.session() as session:
            # Drop the old 1536-dimensional index if it exists to prevent mismatch errors
            session.run("DROP INDEX chunkEmbedding IF EXISTS")
            session.run("""
                CREATE VECTOR INDEX chunkEmbedding IF NOT EXISTS
                FOR (n:DocumentChunk) ON (n.embedding)
                OPTIONS {indexConfig: { `vector.dimensions`: 384, `vector.similarity_function`: 'cosine' }}
            """)
    except Exception as e:
        print(f"Vector index init warning: {e}")


def save_chunks_to_neo4j(validated_nodes: List[Dict[str, Any]], doc_name: str = "EU_AI_Act"):
    """
    Persists validated nodes into Neo4j graph storage with vector embeddings.
    """
    initialize_vector_index()
    
    # Generate local embeddings for each node payload
    for node in validated_nodes:
        node["embedding"] = get_text_embedding(node.get("text_content", ""))

    try:
        driver = neo4j_connector.get_driver()
        with driver.session() as session:
            session.execute_write(_insert_chunks_transaction, validated_nodes, doc_name)
    except Exception as e:
        print(f"Neo4j persistence warning: {e}")


def _insert_chunks_transaction(tx, nodes, doc_name):
    query = """
    MERGE (d:Document {id: $doc_name})
    WITH d
    UNWIND $nodes AS row
    
    MERGE (s:Section {name: coalesce(row.section_header, "Document Preamble"), doc_id: $doc_name})
    MERGE (d)-[:HAS_SECTION]->(s)
    
    MERGE (c:DocumentChunk {node_id: row.node_id})
    SET c.text_content = row.text_content,
        c.category = row.node_type,
        c.embedding = row.embedding,
        c:Article
        
    MERGE (s)-[:HAS_CHUNK]->(c)
    """
    tx.run(query, nodes=nodes, doc_name=doc_name)

    seq_query = """
    UNWIND range(0, size($nodes)-2) AS idx
    WITH $nodes[idx] AS curr, $nodes[idx+1] AS next_node
    MATCH (c1:DocumentChunk {node_id: curr.node_id})
    MATCH (c2:DocumentChunk {node_id: next_node.node_id})
    MERGE (c1)-[:NEXT]->(c2)
    """
    tx.run(seq_query, nodes=nodes)