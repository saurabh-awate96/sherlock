import json
import sqlite3
from datetime import datetime
from typing import List


class Database:
    """
    The Brain of Sherlock.
    Stores audit trails and learned knowledge (error fixes).
    """

    def __init__(self, db_path="sherlock/sherlock_output/sherlock.db"):
        self.db_path = db_path
        
        # Ensure FS exists
        import os
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        self._init_db()

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        conn = self._get_conn()
        cur = conn.cursor()

        # 1. Audit Runs
        cur.execute("""
            CREATE TABLE IF NOT EXISTS audit_runs (
                id TEXT PRIMARY KEY,
                timestamp TEXT,
                target_dir TEXT,
                config_hash TEXT
            )
        """)

        # 2. Detections (Audit Trail)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS detections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT,
                file_path TEXT,
                primitive TEXT,
                confidence REAL,
                evidence JSON,
                timestamp TEXT,
                FOREIGN KEY(run_id) REFERENCES audit_runs(id)
            )
        """)

        # 3. Knowledge Base (Smart Fixes & Learned Invariants)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_base (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                error_signature TEXT,        -- Hash of error or pattern
                fix_strategy TEXT,           -- Description or Code snippet
                scope_type TEXT DEFAULT 'GLOBAL', -- LOCAL | INTERFACE | GLOBAL
                related_element TEXT,        -- File path (if LOCAL) or Interface ID (if INTERFACE)
                success_count INTEGER DEFAULT 1,
                last_used TEXT,
                UNIQUE(error_signature, scope_type, related_element)
            )
        """)

        # 4. Protocol Similarity Engine
        cur.execute("""
            CREATE TABLE IF NOT EXISTS protocol_fingerprints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contract_name TEXT,
                fingerprint_hash TEXT,       -- Structural AST Hash
                protocol_tag TEXT,           -- e.g. "Uniswap_V2_Pair"
                source_code_snapshot TEXT
            )
        """)

        # 5. Known Issues Archive (RAG)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS issues_archive (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fingerprint_hash TEXT,       -- Links to protocol_fingerprints
                issue_type TEXT,             -- e.g. "Reentrancy"
                description TEXT,            -- "External call before state update"
                severity TEXT,
                fix_recommendation TEXT
            )
        """)

        # 6. Irene's Research Library (Context Store)
        # Isolated storage for non-code artifacts (Docs, Plans, Diagrams)
        # No ScopeGuard needed on retrieval as this is treated as Passive Data.
        cur.execute("""
            CREATE TABLE IF NOT EXISTS research_library (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT,
                topic TEXT,                  -- e.g. "README", "Architecture", "UserGuide"
                content TEXT,
                source_path TEXT,
                metadata JSON
            )
        """)

        # 7. Secure Knowledge Kernel (RAG Store)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT,
                embedding BLOB,           -- Vector for semantic search
                scope_tags JSON,          -- e.g. ["Vault", "ERC4626", "Security_Common"]
                source_ref TEXT,          -- User's file source
                requires_clearance TEXT   -- "PUBLIC", "INTERNAL", "CLASSIFIED"
            )
        """)

        # 8. Granular Code Analysis (Pure Context Mode)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS granular_insights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT,
                file_path TEXT,
                block_name TEXT,            -- Function name or block identifier
                line_range TEXT,            -- e.g. "100-125"
                purpose TEXT,
                invariants JSON,            -- List of invariant strings
                assumptions JSON,           -- List of assumption strings
                risks JSON,                 -- List of risk considerations
                micro_analysis TEXT,        -- Line-by-line notes
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(run_id) REFERENCES audit_runs(id)
            )
        """)

        # 8. Structured Taxonomy Core
        cur.execute("""
            CREATE TABLE IF NOT EXISTS vulnerability_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                description TEXT,
                parent_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_id) REFERENCES vulnerability_categories(id)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS vulnerability_subcategories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL,
                slug TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES vulnerability_categories(id),
                UNIQUE(category_id, slug)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS issue_classifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                issue_id INTEGER NOT NULL,
                category_id INTEGER NOT NULL,
                subcategory_id INTEGER,
                confidence REAL DEFAULT 1.0,
                source TEXT NOT NULL, -- 'regex', 'llm', 'manual'
                FOREIGN KEY (issue_id) REFERENCES github_issues(id),
                FOREIGN KEY (category_id) REFERENCES vulnerability_categories(id),
                FOREIGN KEY (subcategory_id) REFERENCES vulnerability_subcategories(id)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT NOT NULL UNIQUE,
                category TEXT -- 'protocol', 'integration', 'generic'
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS issue_tags (
                issue_id INTEGER NOT NULL,
                tag_id INTEGER NOT NULL,
                PRIMARY KEY (issue_id, tag_id),
                FOREIGN KEY (issue_id) REFERENCES github_issues(id),
                FOREIGN KEY (tag_id) REFERENCES tags(id)
            )
        """)

        # 9. Normalized Findings (Sherlock Hardening Phase 5)
        # Core Findings Table (Immutable Identity)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS findings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                -- Identity
                contest_id INTEGER NOT NULL,
                contest_title TEXT NOT NULL,
                number INTEGER NOT NULL,
                title TEXT NOT NULL,
                author TEXT,
                
                -- Analysis
                severity TEXT NOT NULL,
                vulnerability_type TEXT,
                summary TEXT,
                root_cause TEXT,
                impact TEXT,
                recommendation TEXT,
                
                -- Content
                markdown_content TEXT,
                github_url TEXT UNIQUE,
                
                -- Meta
                reward REAL,
                is_primary INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- Constraints
                UNIQUE(contest_id, number)
            );
        """)

        # Knowledge Graph: Metadata (Flexible Key-Value)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS finding_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                finding_id INTEGER NOT NULL,
                key TEXT NOT NULL,
                value TEXT,
                FOREIGN KEY(finding_id) REFERENCES findings(id) ON DELETE CASCADE
            );
        """)

        # Context History: Discussions (The Debate)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS discussions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                finding_id INTEGER NOT NULL,
                author TEXT,
                comment TEXT NOT NULL,
                created_at TIMESTAMP,
                FOREIGN KEY(finding_id) REFERENCES findings(id) ON DELETE CASCADE
            );
        """)

        # Smart Contract Context: Code Locations (Precision Targeting)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS code_locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                finding_id INTEGER NOT NULL,
                path TEXT NOT NULL,
                start_line INTEGER,
                end_line INTEGER,
                snippet TEXT,
                function_name TEXT,
                contract_name TEXT,
                FOREIGN KEY(finding_id) REFERENCES findings(id) ON DELETE CASCADE
            );
        """)

        # Performance Indexes
        cur.execute("CREATE INDEX IF NOT EXISTS idx_findings_severity ON findings(severity);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_findings_vulnerability ON findings(vulnerability_type);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_metadata_key ON finding_metadata(key);")

        conn.commit()
        conn.close()

    def log_run(self, run_id: str, target_dir: str):
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO audit_runs (id, timestamp, target_dir) VALUES (?, ?, ?)",
            (run_id, datetime.now().isoformat(), target_dir)
        )
        conn.commit()
        conn.close()

    def log_detection(self, run_id: str, file_path: str, primitive: str, confidence: float, evidence: dict):
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO detections 
               (run_id, file_path, primitive, confidence, evidence, timestamp)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (run_id, file_path, primitive, confidence, json.dumps(evidence), datetime.now().isoformat())
        )
        row_id = cur.lastrowid
        conn.commit()
        conn.close()
        return row_id

    def update_verification(self, detection_id: int, verification_data: dict):
        """
        Updates the evidence JSON with verification results (Proof is God).
        """
        conn = self._get_conn()
        cur = conn.cursor()
        
        # Fetch existing evidence
        cur.execute("SELECT evidence FROM detections WHERE id = ?", (detection_id,))
        row = cur.fetchone()
        if row:
            evidence = json.loads(row[0])
            evidence.update(verification_data)
            
            cur.execute(
                "UPDATE detections SET evidence = ? WHERE id = ?",
                (json.dumps(evidence), detection_id)
            )
            conn.commit()
        
        conn.close()

    def get_known_fix(self, error_msg: str, scope_type="GLOBAL", related_element=None) -> str | None:
        """
        RAG: Retrieve known fix for this error within scope
        """
        conn = self._get_conn()
        cur = conn.cursor()

        sig = self._normalize_error(error_msg)

        # Priority: Check Local -> Interface -> Global?
        # For now, simplistic exact match on scope
        query = "SELECT fix_strategy FROM knowledge_base WHERE error_signature = ? AND scope_type = ?"
        params = [sig, scope_type]

        if related_element:
            query += " AND related_element = ?"
            params.append(related_element)

        cur.execute(query + " ORDER BY success_count DESC LIMIT 1", tuple(params))
        row = cur.fetchone()
        conn.close()

        return row[0] if row else None

    def learn_fix(self, error_msg: str, fix_strategy: str, scope_type="GLOBAL", related_element=None):
        """
        Save a successful fix strategy with scope
        """
        sig = self._normalize_error(error_msg)
        conn = self._get_conn()
        cur = conn.cursor()

        # Check if exists
        query = "SELECT id, success_count FROM knowledge_base WHERE error_signature = ? AND scope_type = ?"
        params = [sig, scope_type]

        if related_element:
            query += " AND related_element = ?"
            params.append(related_element)
        else:
            query += " AND related_element IS NULL"

        cur.execute(query, tuple(params))
        row = cur.fetchone()

        if row:
            # Update
            new_count = row[1] + 1
            cur.execute(
                "UPDATE knowledge_base SET success_count = ?, last_used = ? WHERE id = ?",
                (new_count, datetime.now().isoformat(), row[0])
            )
        else:
            # Insert
            cur.execute(
                "INSERT INTO knowledge_base (error_signature, fix_strategy, scope_type, related_element, last_used) VALUES (?, ?, ?, ?, ?)",
                (sig, fix_strategy, scope_type, related_element, datetime.now().isoformat())
            )

        conn.commit()
        conn.close()

    def insert_knowledge(self, content: str, scope_tags: list, source_ref: str, clearance: str = "INTERNAL"):
        """
        Ingest knowledge into the RAG Kernel.
        """
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO knowledge_items 
               (content, scope_tags, source_ref, requires_clearance)
               VALUES (?, ?, ?, ?)""",
            (content, json.dumps(scope_tags), source_ref, clearance)
        )
        conn.commit()
        conn.close()

    def store_sherlock_finding(self, finding_data: dict):
        """
        Transactional storage of a complete Sherlock finding.
        Guarantees ACID properties: All or Nothing.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            cursor = conn.cursor()
            
            try:
                # 1. Helper to safely get JSON-able fields
                def get_json(key):
                    val = finding_data.get(key)
                    if isinstance(val, (list, dict)):
                        return json.dumps(val)
                    return val

                # 2. Insert Core Finding
                cursor.execute("""
                    INSERT INTO findings (
                        contest_id, contest_title, number, title, author,
                        severity, vulnerability_type, summary, root_cause, 
                        impact, recommendation, markdown_content, github_url, 
                        reward, is_primary
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(github_url) DO UPDATE SET
                        markdown_content=excluded.markdown_content,
                        summary=excluded.summary
                """, (
                    finding_data.get('contest_id'),
                    finding_data.get('contest_title'),
                    finding_data.get('number'),
                    finding_data.get('title'),
                    finding_data.get('author'),
                    finding_data.get('severity'),
                    finding_data.get('vulnerability_type'),
                    finding_data.get('summary'),
                    finding_data.get('root_cause'),
                    finding_data.get('impact'),
                    finding_data.get('recommendation'),
                    finding_data.get('markdown_content'),
                    finding_data.get('github_url'),
                    finding_data.get('reward'),
                    finding_data.get('is_primary', 1)
                ))
                
                # Fetch ID logic for reliability
                cursor.execute("SELECT id FROM findings WHERE contest_id=? AND number=?", 
                             (finding_data['contest_id'], finding_data['number']))
                res = cursor.fetchone()
                if not res:
                     # Fallback if weird
                     return
                finding_id = res[0]

                # 3. Store Metadata (Duplicate Count, Labels)
                meta_params = []
                if 'duplicate_count' in finding_data:
                    meta_params.append((finding_id, 'duplicate_count', str(finding_data['duplicate_count'])))
                if 'github_labels' in finding_data:
                    meta_params.append((finding_id, 'github_labels', get_json('github_labels')))
                
                if meta_params:
                    cursor.executemany("INSERT INTO finding_metadata (finding_id, key, value) VALUES (?, ?, ?)", meta_params)

                # 4. Store Code Snippets (as simple locations for now)
                snippets = finding_data.get('code_snippets')
                if snippets:
                    if isinstance(snippets, str):
                        try:
                            snippets = json.loads(snippets)
                        except:
                            snippets = [snippets] # Treat as single string
                    
                    # Normalize list
                    location_params = []
                    for s in snippets:
                        # naive path parsing (future: use regex to extract path/lines)
                        location_params.append((finding_id, 'unknown_path', 0, 0, s))
                    
                    if location_params:
                        cursor.executemany("""
                            INSERT INTO code_locations (finding_id, path, start_line, end_line, snippet) 
                            VALUES (?, ?, ?, ?, ?)
                        """, location_params)

                conn.commit()

            except Exception as e:
                print(f"[DB] Transaction Failed for Issue {finding_data.get('number')}: {e}")
                conn.rollback()
                raise e

    def get_findings_by_severity(self, severity: str = 'High') -> List[dict]:
        """
        Retrieve unique findings by severity.
        """
        conn = self._get_conn()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT title, summary, vulnerability_type, root_cause, markdown_content 
            FROM findings 
            WHERE severity = ? AND is_primary = 1
            ORDER BY reward DESC
        """, (severity,))
        
        rows = cur.fetchall()
        conn.close()
        
        return [
            {
                'title': r[0], 
                'summary': r[1],
                'vulnerability_type': r[2],
                'root_cause': r[3],
                'body': r[4] # Map markdown_content to body for agent compatibility
            } for r in rows
        ]


    def log_granular_insight(self, run_id: str, insight_data: dict):
        """
        Logs a micro-analysis insight from the Inspector Agent.
        """
        conn = self._get_conn()
        cur = conn.cursor()
        try:
            cur.execute(
                """INSERT INTO granular_insights 
                   (run_id, file_path, block_name, line_range, purpose, invariants, assumptions, risks, micro_analysis)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    run_id,
                    insight_data['file_path'],
                    insight_data['block_name'],
                    insight_data['line_range'],
                    insight_data.get('purpose', ''),
                    json.dumps(insight_data.get('invariants', [])),
                    json.dumps(insight_data.get('assumptions', [])),
                    json.dumps(insight_data.get('risks', [])),
                    insight_data.get('micro_analysis', '')
                )
            )
            conn.commit()
        except Exception as e:
            print(f"[DB] Failed to log granular insight: {e}")
        finally:
            conn.close()

    def _normalize_error(self, error: str) -> str:
        """
        Strip variable parts from error to create stable signature.
        Example: "Error (234): Function foo not found" -> "Error (234): Function [VAR] not found"
        Strictly hash based for now to avoid complexity.
        """
        # Take first 100 chars or specific error lines
        # This is a naive implementation
        return error[:200].strip() # Simplification
