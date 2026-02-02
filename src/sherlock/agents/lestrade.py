import os
import shutil
import subprocess
import tempfile
import urllib.request
import json
import re
from pathlib import Path
from urllib.parse import urlparse
import structlog

# Try importing LLMInterface, might fail if dependencies missing
try:
    from sherlock.core.llm_interface import LLMInterface
    from sherlock.core.config_loader import ConfigLoader
except ImportError:
    LLMInterface = None
    ConfigLoader = None

logger = structlog.get_logger()

class Lestrade:
    """
    Inspector Lestrade.
    The Legwork Agent. He gathers evidence from the crime scene (URL, Repo, Etherscan)
    and packages it for Sherlock.
    Now also handles Witness Statements (GitHub Issues).
    """
    
    def __init__(self, workspace_dir: str = "./.sherlock_workspace", db=None):
        self.workspace_dir = Path(workspace_dir)
        self.evidence_dir = self.workspace_dir / "evidence"
        self._ensure_workspace()
        self.db = db
        
        # Initialize LLM for classification if available
        self.llm = None
        if LLMInterface and ConfigLoader:
            try:
                self.llm = LLMInterface(ConfigLoader())
            except Exception as e:
                logger.warning("lestrade_llm_init_failed", error=str(e))
        
        # Verify tools
        if not shutil.which("git"):
            logger.warning("lestrade_missing_tool", tool="git", msg="Git clone will fail if needed.")

    def _ensure_workspace(self):
        # We don't wipe the whole workspace, just the evidence dir to be clean for each run
        if self.evidence_dir.exists():
            shutil.rmtree(self.evidence_dir)
        self.evidence_dir.mkdir(parents=True, exist_ok=True)

    def gather_evidence(self, target: str) -> str:
        """
        Goes to the scene and retrieves the code.
        Returns: Absolute path to the directory containing the source code.
        """
        logger.info("lestrade_deploying", target=target)

        # 1. URL Detection (GitHub)
        if target.startswith("http") or target.startswith("git@"):
            return self._clone_repo(target)
        
        # 2. Local Path
        local_path = Path(target).resolve()
        if local_path.exists():
            return self._secure_scene(local_path)

        # 3. Vision/Etherscan (Future generic/placeholder)
        raise ValueError(f"Lestrade cannot locate evidence at: {target}")

    def ingest_from_appledore(self, db_path: str = "appledore/data/knowledge_base.db"):
        """
        Ingest unique, verified findings from the Appledore Knowledge Base.
        Populates the normalized 'findings' and 'finding_metadata' tables.
        """
        import sqlite3
        
        if not os.path.exists(db_path):
            logger.warning("lestrade_appledore_db_missing", path=db_path)
            return

        logger.info("lestrade_ingesting_appledore", path=db_path)
        
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Query for valid Sherlock issues (High/Medium)
            # excluding duplicates and low-reward placeholders if possible
            cursor.execute("""
                SELECT 
                    contest_id, contest_title, number, title, author, 
                    severity, final_severity, reward, github_url, 
                    summary, vulnerability_type, impact, root_cause, 
                    recommendation, markdown_content,
                    (SELECT COUNT(*) FROM issues i2 WHERE i2.contest_id = i.contest_id AND i2.title = i.title) as duplicate_count
                FROM issues i
                WHERE severity IN ('High', 'Medium')
                  AND (markdown_content IS NOT NULL AND markdown_content != '')
                  AND (title NOT LIKE '%Placeholder%')
            """)
            
            rows = cursor.fetchall()
            conn.close()
            
            count = 0
            for row in rows:
                # Prepare data structure for 'store_sherlock_finding'
                # The DB method now handles normalization internally
                finding_data = {
                    'contest_id': row['contest_id'],
                    'contest_title': row['contest_title'],
                    'number': row['number'],
                    'title': row['title'],
                    'author': row['author'],
                    'severity': row['severity'],
                    'final_severity': row['final_severity'],
                    'reward': row['reward'],
                    'github_url': row['github_url'],
                    'summary': row['summary'],
                    'vulnerability_type': row['vulnerability_type'],
                    'impact': row['impact'],
                    'root_cause': row['root_cause'],
                    'recommendation': row['recommendation'],
                    'markdown_content': row['markdown_content'],
                    'is_primary': 1, 
                    'duplicate_count': row['duplicate_count'],
                    # Future: extracting code snippets from markdown if needed
                    'code_snippets': [] 
                }
                
                if self.db:
                    self.db.store_sherlock_finding(finding_data)
                    count += 1
            
            logger.info("lestrade_ingestion_complete", count=count)

        except Exception as e:
            logger.error("lestrade_ingestion_failed", error=str(e))


    def _clone_repo(self, url: str) -> str:
        """Clones a remote repository."""
        logger.info("lestrade_cloning", url=url)
        try:
            subprocess.run(
                ["git", "clone", "--depth", "1", "--recurse-submodules", url, str(self.evidence_dir)],
                check=True,
                capture_output=True
            )
            return str(self.evidence_dir.resolve())
        except subprocess.CalledProcessError as e:
            logger.error("clone_failed", error=str(e))
            raise ValueError(f"Failed to clone repository: {url}")

    def _secure_scene(self, path: Path) -> str:
        """
        Copies local files to a clean workspace to avoid polluting the user's dir.
        """
        logger.info("lestrade_securing_scene", path=str(path))
        
        # Safety check: Don't copy if target IS the workspace
        if str(self.workspace_dir.resolve()) in str(path.resolve()):
            return str(path)

        if path.is_dir():
            # Copy dir content to evidence_dir
            # Ignore hidden files and build artifacts to speed up
            shutil.copytree(
                path, 
                self.evidence_dir, 
                dirs_exist_ok=True,
                ignore=shutil.ignore_patterns('.git', 'venv', '.sherlock_workspace', 'out', 'broadcast')
            )
        else:
            # Single file?
            shutil.copy2(path, self.evidence_dir)
            
        return str(self.evidence_dir.resolve())
