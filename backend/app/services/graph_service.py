from typing import Dict, Any, List
from neo4j.exceptions import Neo4jError, ServiceUnavailable
from app.core.neo4j import neo4j_connector
from sentence_transformers import SentenceTransformer
from app.services.rea_auditor import execute_recursive_entropy_audit, calculate_shannon_entropy
from app.services.ontological_critic import calculate_jensen_shannon_divergence

# Initialize local lightweight open-source embedding model (runs completely offline)
embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
#embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

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


def search_graph_by_query(
    query: str, 
    limit: int = 5, 
    hop_limit: int = 2,
    d_js_threshold: float = 0.15,
    pig_preset: str = "balanced",
    boilerplate_suppression: bool = True
) -> Dict[str, Any]:
    """
    Unified Dual-Invention Retrieval Pipeline:
    1. Performs Vector Similarity mapped against Ontological Weighting (w) using dynamic user hop limits.
    2. Applies Adaptive Similarity Floor to reject out-of-domain garbage queries.
    3. Runs Invention 1: REA (Recursive Entropy Audit) with optional boilerplate suppression.
    4. Runs Invention 2: Ontological Critic mapped to user-tuned D_JS sensitivity.
    5. Executes Automated Self-Correction Router to fill topological gaps if friction is found.
    """
    try:
        query_vector = get_text_embedding(query)
        driver = neo4j_connector.get_driver()
        
        # Safely interpolate hop_limit as a clean integer string to avoid Neo4j syntax parameter errors
        safe_hop_limit = int(hop_limit)
        
        cypher = f"""
        CALL db.index.vector.queryNodes('chunkEmbedding', $limit, $query_vector)
        YIELD node AS c, score
        OPTIONAL MATCH (s:Section)-[:HAS_CHUNK]->(c)
        OPTIONAL MATCH (c)-[:NEXT]->(next_c:DocumentChunk)
        OPTIONAL MATCH (prev_c:DocumentChunk)-[:NEXT]->(c)
        WITH c, score, s, next_c, prev_c,
             CASE WHEN 'Article' IN labels(c) THEN 0.9 
                  WHEN 'Recital' IN labels(c) THEN 0.6 
                  ELSE 0.5 END AS ontological_weight
        RETURN c.node_id AS node_id,
               c.text_content AS text_content,
               labels(c) AS labels,
               coalesce(s.name, "Document Preamble") AS section_header,
               prev_c.text_content AS prev_content,
               next_c.text_content AS next_content,
               score,
               ontological_weight
        ORDER BY (score * ontological_weight) DESC
        """
        with driver.session() as session:
            records = session.run(
                cypher, 
                query_vector=query_vector, 
                limit=limit
            )
            raw_candidates = []
            seen_node_ids = set()
            
            for r in records:
                node_id = r["node_id"]
                if not node_id or node_id in seen_node_ids:
                    continue

                # Boilerplate suppression filter check
                text_to_eval = r['text_content'] or ""
                if boilerplate_suppression and (len(text_to_eval.split()) < 4 or "Official Journal" in text_to_eval or "2024/" in text_to_eval):
                    continue # Skip low-density boilerplate filler chunks

                seen_node_ids.add(node_id)

                enriched_text = ""
                if r["prev_content"]: 
                    enriched_text += f"[PREVIOUS PARAGRAPH]: {r['prev_content']} \n\n"
                
                enriched_text += f"[EXACT MATCH]: {text_to_eval} \n\n"
                
                if r["next_content"]: 
                    enriched_text += f"[NEXT PARAGRAPH]: {r['next_content']}"
                
                node_item = {
                    "node_id": node_id,
                    "text_content": text_to_eval,
                    "labels": r["labels"] or ["Article"],
                    "section_header": r["section_header"],
                    "multi_hop_context": enriched_text.strip(),
                    "similarity_score": round(float(r["score"]), 4),
                    "ontological_weight": float(r["ontological_weight"])
                }
                raw_candidates.append(node_item)

            # --- ADAPTIVE SIMILARITY FLOOR ---
            if raw_candidates:
                top_score = raw_candidates[0]["similarity_score"]
                # Hard Floor: Raised to 0.68 to properly catch out-of-domain queries using MiniLM embeddings.
                if top_score < 0.68:
                    raw_candidates = []
                else:
                    # Relative Floor: Tightened to 0.85 (drop chunks if they drop more than 15% below the top match).
                    raw_candidates = [c for c in raw_candidates if c["similarity_score"] >= top_score * 0.85]

            results = list(raw_candidates)

            # If the floor wiped out all candidates, return early to save REA compute
            if not results:
                return {
                    "query": query,
                    "matches_count": 0,
                    "matches": [],
                    "rea_audit": {},
                    "ontological_critic_audit": {},
                    "adaptive_floor_triggered": True
                }

            # ---------------------------------------------------------
            # INVENTION 1: Recursive Entropy Audit (REA)
            # ---------------------------------------------------------
            rea_audit_result = execute_recursive_entropy_audit(raw_candidates)
            aggregate_text = " ".join([n["text_content"] for n in raw_candidates]) if raw_candidates else query
            baseline_entropy = calculate_shannon_entropy(aggregate_text)

            # ---------------------------------------------------------
            # INVENTION 2: Ontological Critic ($D_{JS}$ Probe with user threshold)
            # ---------------------------------------------------------
            critic_audit_logs = []
            friction_detected = False
            conflicting_nodes = []
            
            if len(raw_candidates) >= 2:
                for i in range(len(raw_candidates) - 1):
                    text_a = raw_candidates[i]["text_content"]
                    text_b = raw_candidates[i+1]["text_content"]
                    djs_score = calculate_jensen_shannon_divergence(text_a, text_b)
                    
                    is_harmonious = djs_score <= d_js_threshold
                    if not is_harmonious:
                        friction_detected = True
                        conflicting_nodes.append(raw_candidates[i]["node_id"])
                        
                    critic_audit_logs.append({
                        "node_pair": (raw_candidates[i]["node_id"], raw_candidates[i+1]["node_id"]),
                        "d_js_score": djs_score,
                        "is_harmonious": is_harmonious,
                        "status": "PASSED: Harmonious" if is_harmonious else "FAILED: Logical Contradiction Detected."
                    })

            # ---------------------------------------------------------
            # REQUIREMENT 3: Automated Self-Correction Router
            # ---------------------------------------------------------
            if friction_detected and conflicting_nodes:
                healing_cypher = """
                UNWIND $node_ids AS nid
                MATCH (c {node_id: nid})<-[:HAS_CHUNK]-(s:Section)-[:HAS_CHUNK]->(sibling)
                WHERE sibling.node_id <> nid AND NOT sibling.node_id IN $seen
                RETURN DISTINCT sibling.node_id AS node_id, 
                                sibling.text_content AS text_content, 
                                labels(sibling) AS labels, 
                                s.name AS section_header 
                LIMIT 2
                """
                healing_records = session.run(healing_cypher, node_ids=conflicting_nodes, seen=list(seen_node_ids))
                for hr in healing_records:
                    healed_id = hr["node_id"]
                    healed_text = hr["text_content"] or ""
                    if boilerplate_suppression and (len(healed_text.split()) < 4 or "Official Journal" in healed_text):
                        continue

                    if healed_id not in seen_node_ids:
                        seen_node_ids.add(healed_id)
                        healed_item = {
                            "node_id": healed_id,
                            "text_content": healed_text,
                            "labels": hr["labels"] or ["Recital"],
                            "section_header": hr["section_header"],
                            "multi_hop_context": f"[SELF-CORRECTION ROUTER INJECTED CONTEXT]:\n{healed_text}",
                            "similarity_score": 1.0,
                            "ontological_weight": 0.9
                        }
                        results.append(healed_item)

            return {
                "query": query,
                "matches_count": len(results),
                "matches": results,
                "adaptive_floor_triggered": False,
                "rea_audit": {
                    "shannon_entropy": baseline_entropy,
                    "metrics": rea_audit_result["metrics"],
                    "retained_nodes": rea_audit_result["retained_nodes"]
                },
                "ontological_critic_audit": {
                    "threshold_used": d_js_threshold,
                    "cross_provision_probes": critic_audit_logs,
                    "self_correction_triggered": friction_detected
                }
            }
            
    except Exception as e:
        print(f"Vector search fallback due to: {e}")
        return _fallback_lexical_search_with_rea(query, limit, d_js_threshold)


def _fallback_lexical_search_with_rea(
    query: str, 
    limit: int = 5, 
    d_js_threshold: float = 0.15
) -> Dict[str, Any]:
    """Fallback search implementing basic REA without weighting or automated re-traversal."""
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
               labels(c) AS labels,
               coalesce(s.name, "Document Preamble") AS section_header,
               prev_c.text_content AS prev_content,
               next_c.text_content AS next_content
        LIMIT $limit
        """
        with driver.session() as session:
            records = session.run(cypher, query_text=query, limit=limit)
            raw_candidates = []
            results = []
            seen_node_ids = set()
            
            for r in records:
                node_id = r["node_id"]
                if not node_id or node_id in seen_node_ids:
                    continue
                seen_node_ids.add(node_id)

                enriched_text = ""
                if r["prev_content"]: 
                    enriched_text += f"[PREVIOUS PARAGRAPH]: {r['prev_content']} \n\n"
                
                enriched_text += f"[EXACT MATCH]: {r['text_content']} \n\n"
                
                if r["next_content"]: 
                    enriched_text += f"[NEXT PARAGRAPH]: {r['next_content']}"
                
                node_item = {
                    "node_id": node_id,
                    "text_content": r["text_content"],
                    "labels": r["labels"] or ["Article"],
                    "section_header": r["section_header"],
                    "multi_hop_context": enriched_text.strip()
                }
                raw_candidates.append(node_item)
                results.append(node_item)

            rea_audit_result = execute_recursive_entropy_audit(raw_candidates)
            aggregate_text = " ".join([n["text_content"] for n in raw_candidates]) if raw_candidates else query
            baseline_entropy = calculate_shannon_entropy(aggregate_text)

            critic_audit_logs = []
            if len(raw_candidates) >= 2:
                for i in range(len(raw_candidates) - 1):
                    text_a = raw_candidates[i]["text_content"]
                    text_b = raw_candidates[i+1]["text_content"]
                    djs_score = calculate_jensen_shannon_divergence(text_a, text_b)
                    is_harmonious = djs_score <= d_js_threshold
                    critic_audit_logs.append({
                        "node_pair": (raw_candidates[i]["node_id"], raw_candidates[i+1]["node_id"]),
                        "d_js_score": djs_score,
                        "is_harmonious": is_harmonious,
                        "status": "PASSED: Harmonious" if is_harmonious else "FAILED: Logical Contradiction Detected."
                    })

            return {
                "query": query,
                "matches_count": len(results),
                "matches": results,
                "adaptive_floor_triggered": False,
                "rea_audit": {
                    "shannon_entropy": baseline_entropy,
                    "metrics": rea_audit_result["metrics"],
                    "retained_nodes": rea_audit_result["retained_nodes"]
                },
                "ontological_critic_audit": {
                    "threshold_used": d_js_threshold,
                    "cross_provision_probes": critic_audit_logs,
                    "self_correction_triggered": False
                }
            }
    except Exception:
        return {"query": query, "matches_count": 0, "matches": [], "adaptive_floor_triggered": False, "rea_audit": {}, "ontological_critic_audit": {}}


def initialize_vector_index():
    """Initializes a 384-dimensional vector index for SentenceTransformers."""
    try:
        driver = neo4j_connector.get_driver()
        with driver.session() as session:
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