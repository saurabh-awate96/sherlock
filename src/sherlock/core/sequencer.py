from datetime import datetime
from enum import Enum

from .db import Database


class AuditState(Enum):
    PENDING = "PENDING"
    ANALYZING = "ANALYZING"
    GENERATING = "GENERATING"
    VERIFYING = "VERIFYING"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"

class Sequencer:
    """
    The Conductor of the Segmented Audit Lifecycle.
    Ensures linear, resumable execution.
    """

    def __init__(self, db: Database, run_id: str):
        self.db = db
        self.run_id = run_id
        self._init_state_table()

    def _init_state_table(self):
        conn = self.db._get_conn()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS audit_lifecycle (
                run_id TEXT,
                file_path TEXT,
                status TEXT,
                stage TEXT,
                updated_at TEXT,
                PRIMARY KEY(run_id, file_path)
            )
        """)
        conn.commit()
        conn.close()

    def add_to_queue(self, file_path: str):
        conn = self.db._get_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT OR IGNORE INTO audit_lifecycle (run_id, file_path, status, stage, updated_at) VALUES (?, ?, ?, ?, ?)",
            (self.run_id, file_path, "PENDING", "INIT", datetime.now().isoformat())
        )
        conn.commit()
        conn.close()

    def update_status(self, file_path: str, status: AuditState, stage: str = None):
        """
        Update the progress of a file.
        This serves as the 'Checkpoint'.
        """
        conn = self.db._get_conn()
        cur = conn.cursor()

        query = "UPDATE audit_lifecycle SET status = ?, updated_at = ?"
        params = [status.value, datetime.now().isoformat()]

        if stage:
            query += ", stage = ?"
            params.append(stage)

        query += " WHERE run_id = ? AND file_path = ?"
        params.extend([self.run_id, file_path])

        cur.execute(query, tuple(params))
        conn.commit()
        conn.close()

        print(f"[Sequencer] {file_path} -> {status.value} ({stage})")

    def get_pending_files(self):
        """
        Return list of files that are NOT Complete.
        Used for resuming.
        """
        conn = self.db._get_conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT file_path FROM audit_lifecycle WHERE run_id = ? AND status != 'COMPLETE'",
            (self.run_id,)
        )
        rows = cur.fetchall()
        conn.close()
        return [r[0] for r in rows]

    def is_complete(self, file_path: str) -> bool:
        conn = self.db._get_conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT status FROM audit_lifecycle WHERE run_id = ? AND file_path = ?",
            (self.run_id, file_path)
        )
        row = cur.fetchone()
        conn.close()
        return row and row[0] == "COMPLETE"
