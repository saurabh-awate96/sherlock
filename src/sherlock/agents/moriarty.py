#!/usr/bin/env python3
"""
Moriarty Agent: The Execution Engine (v2.0)
===========================================
"Every problem has a final solution."

Moriarty 2.0 Deep Logic Verification Upgrades:
1.  **Handler-Aware PoCs**: Generates exploits that leverage the Handler's 
    stateful setup and ghost state.
2.  **Undeniable Proof**: Enforces profit assertions (Profit > Gas).
3.  **Stateful Invariants**: Converts fuzzer findings into reproducible 
    Solidity test cases.
"""

import os
import shutil
import subprocess
import structlog
from pathlib import Path
from typing import Any, Dict
from jinja2 import Template

logger = structlog.get_logger()

class Moriarty:
    """
    Moriarty Agent (The Muscle).
    Responsible for "Proof is God": generating and verifying exploits.
    """

    def __init__(self, workspace_dir: Path, db: Any = None):
        self.workspace_dir = workspace_dir
        self.db = db
        self.output_dir = self.workspace_dir / "test" / "poc"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._load_env()
        self._secure_environment()

    def _load_env(self):
        # Load .env from project root if exists
        env_path = Path(".env")
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    if "=" in line and not line.strip().startswith("#"):
                        key, val = line.strip().split("=", 1)
                        os.environ[key] = val

    def _secure_environment(self):
        """Enforces the Secure Execution Environment (Sandboxing)."""
        secure_toml = Path("sherlock/templates/foundry_secure.toml")
        target_toml = self.workspace_dir / "foundry.toml"
        
        if secure_toml.exists():
            shutil.copy2(secure_toml, target_toml)
            logger.info("moriarty_sandbox_enabled", config=str(target_toml))
        else:
            logger.warning("moriarty_sandbox_missing", msg="Secure template not found!")

    def verify_finding(self, finding: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point. Generates PoC, runs it, returns verification status.
        """
        title = finding.get("title", "Unknown")
        logger.info("moriarty_verifying", title=title)

        # 1. Generate PoC
        poc_path = self._generate_poc(finding)
        if not poc_path:
            return {"verified": False, "status": "Generation Failed"}

        # 2. Run Execution
        success, logs = self._run_forge_test(poc_path)
        
        status = "Verified" if success else "Quarantined"
        logger.info("moriarty_verdict", title=title, status=status)
        
        return {
            "verified": success,
            "status": status,
            "poc_path": str(poc_path),
            "logs": logs
        }

    def _generate_poc(self, finding: Dict[str, Any]) -> Path | None:
        try:
            # Load Template - Robust Path Resolution
            # Assuming moriarty.py is in sherlock/agents/
            base_path = Path(__file__).resolve().parent.parent # sherlock/
            template_path = base_path / "templates" / "poc.sol.jinja"
            
            if not template_path.exists():
                logger.error("moriarty_template_missing", path=str(template_path))
                return None

            with open(template_path) as f:
                template = Template(f.read())

            # Render
            # TODO: Improve context generation from 'finding' details
            rpc_url = os.getenv("RPC_URL", "")
            code = template.render(
                title=finding.get("title"),
                block_number=19200000, # TODO: Smart block picking
                attack_step_1="Deposit 1 wei", # Placeholder context
                attack_step_2="Exploit logic"
            )

            filename = f"PoC_{finding.get('id', 'unknown')}.t.sol"
            filepath = self.output_dir / filename
            
            with open(filepath, "w") as f:
                f.write(code)
                
            return filepath
            
        except Exception as e:
            logger.error("moriarty_generation_failed", error=str(e))
            return None

    def _run_forge_test(self, poc_path: Path) -> tuple[bool, str]:
        """Runs the PoC in the hardened workspace."""
        cmd = ["forge", "test", "--match-path", str(poc_path.relative_to(self.workspace_dir)), "-vv"]
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.workspace_dir,
                capture_output=True,
                text=True,
                timeout=45 # Hard timeout constraint
            )
            return (result.returncode == 0, result.stdout)
        except subprocess.TimeoutExpired:
            return (False, "Timeout Limit Exceeded (45s)")
        except Exception as e:
            return (False, str(e))

