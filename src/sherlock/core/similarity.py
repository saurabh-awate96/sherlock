import hashlib
import json

from .db import Database


class SimilarityEngine:
    """
    The 'Cousin' Finder.
    Matches current contract against known protocol fingerprints.
    """

    def __init__(self, db: Database):
        self.db = db

    def fingerprint_contract(self, contract_name: str, storage_layout: dict, methods: dict) -> str:
        """
        Create a structural hash. 
        Ignores variable names (mostly), focuses on Types and Order.
        """
        # 1. Normalize Storage: List of types in order
        storage_types = [item['type'] for item in storage_layout.get('storage', [])]

        # 2. Normalize Methods: Sorted list of signatures
        # methods is { "sig": "selector" }
        # We sort by selector to be canonical
        sorted_methods = sorted(methods.items(), key=lambda x: x[1])
        method_sigs = [sig for sig, _ in sorted_methods]

        # 3. Create Hash
        payload = {
            "storage": storage_types,
            "methods": method_sigs
        }
        canonical_str = json.dumps(payload, sort_keys=True)
        fingerprint = hashlib.sha256(canonical_str.encode()).hexdigest()

        # Store in DB
        self._store_fingerprint(contract_name, fingerprint)

        return fingerprint

    def _store_fingerprint(self, name, fingerprint):
        conn = self.db._get_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT OR IGNORE INTO protocol_fingerprints (contract_name, fingerprint_hash) VALUES (?, ?)",
            (name, fingerprint)
        )
        conn.commit()
        conn.close()

    def find_similar_issues(self, fingerprint: str) -> list[dict]:
        """
        Find issues associated with this fingerprint (or close matches).
        For V1, we do exact fingerprint matching.
        """
        conn = self.db._get_conn()
        cur = conn.cursor()

        cur.execute(
            "SELECT issue_type, description, fix_recommendation FROM issues_archive WHERE fingerprint_hash = ?",
            (fingerprint,)
        )
        rows = cur.fetchall()
        conn.close()

        issues = []
        for r in rows:
            issues.append({
                "type": r[0],
                "description": r[1],
                "fix": r[2]
            })

        return issues

    def seed_knowledge(self, fingerprint: str, issue_type: str, description: str):
        """
        Seed the DB with known issues (for testing/training).
        """
        conn = self.db._get_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO issues_archive (fingerprint_hash, issue_type, description) VALUES (?, ?, ?)",
            (fingerprint, issue_type, description)
        )
        conn.commit()
        conn.close()
