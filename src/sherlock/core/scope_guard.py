import json
import sqlite3
from typing import List, Dict, Any

class AccessDenied(Exception):
    """Raised when an agent attempts to access knowledge outside their scope."""
    pass

class ScopeGuard:
    """
    The Gatekeeper for the Knowledge Kernel.
    Enforces "Need-to-Know" access based on the audit's active primitive scope.
    """
    
    def __init__(self, db_path: str, active_primitive: str, agent_role: str):
        self.db_path = db_path
        self.scope = active_primitive  # e.g. "Vault"
        self.role = agent_role         # e.g. "Watson"
        
    def query(self, text: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        RAG Query wrapped in Access Control Logic.
        """
        # Hard Force: Watson (Perception) cannot see Invariant Logic (Sherlock's domain)
        if self.role == "Watson" and "Invariant" in text:
             raise AccessDenied("Watson is restricted from Invariant Logic.")

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        # Fetch all knowledge items (MVP: Tag-based filtering, Vector-ready schema)
        # In a full-vector implementation, we would compute the embedding of 'text' 
        # and use a vector distance extension here.
        cur.execute("SELECT id, content, scope_tags, source_ref FROM knowledge_items")
        rows = cur.fetchall()
        conn.close()
        
        results = []
        for row in rows:
            try:
                tags = json.loads(row["scope_tags"])
            except:
                tags = []
                
            # 1. SCOPE GATE: Strict Access Control
            # Agent can ONLY see items tagged 'ALL' or matching their current Audit Primitive
            if "ALL" not in tags and self.scope not in tags:
                continue
                
            # 2. Relevance (Simple text match for MVP)
            # This is where the RAG Vector Search would trigger 
            # For now, we return the item if it passes the Scope Gate 
            # and matches keywords to simulate "Retrieval"
            if text.lower() in row["content"].lower(): # Very basic keyword match
                 results.append({
                     "id": row["id"],
                     "content": row["content"],
                     "source": row["source_ref"],
                     "tags": tags
                 })
        
        return results[:limit]
