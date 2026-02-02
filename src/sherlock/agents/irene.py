#!/usr/bin/env python3
"""
Irene Adler Agent: The Research 2.0 Engine
=====================================================

"To Sherlock Holmes she is always THE woman."
- A Scandal in Bohemia

Irene is the "Internet Eyes" of the operation. She:
1.  **Defines the Boundary**: Strictly enforces what is In/Out of scope.
2.  **Identifies the Archetype**: Determines if the target is a "Lending Market", "AMM", etc.
3.  **Builds the Dossier**: Generates `AUDIT_CONTEXT.md` for the other agents.
"""

import json
import os
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from typing import Any

# Import ScopeParser

# Ensure proper paths are in sys.path
# 'sherlock_dir' allows 'import utils'
sherlock_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 'root_dir' allows 'import sherlock.utils'
root_dir = os.path.dirname(sherlock_dir)

if sherlock_dir not in sys.path:
    sys.path.append(sherlock_dir)
if root_dir not in sys.path:
    sys.path.append(root_dir)

try:
    # Try fully qualified first (Standard for package)
    from sherlock.core.config_loader import ConfigLoader
    from sherlock.core.llm_interface import LLMInterface
    from sherlock.utils.scope_parser import AuditScope, ScopeParser
except ImportError as e1:
    try:
        # Try direct import (common if running inside sherlock dir)
        from core.config_loader import ConfigLoader
        from core.llm_interface import LLMInterface
        from utils.scope_parser import AuditScope, ScopeParser
    except ImportError as e2:
        print(f"[Irene] Warning: Core imports failed. Using mocks. Details: {e1} | {e2}")

        # Mocks for standalone/missing-deps execution
        class AuditScope:
            whitelist = []
            blacklist = []
            known_issues = []
            platform_rules = {}

        class ScopeParser:
            def __init__(self, root): pass
            def parse(self, path): return AuditScope()
            def is_in_scope(self, f, s): return True

        class ConfigLoader:
            def __init__(self, p=None): pass
        class LLMInterface:
            def __init__(self, c=None): pass
            def generate(self, p, t=None): return "Mock Response"

# ==============================================================================
# Data Structures
# ==============================================================================

@dataclass
class ResearchContext:
    """The Universal Dossier."""
    scope: Any # Typed as Any to avoid forward ref issues if AuditScope mock fails, but usually fine
    archetype: str  # e.g., "Lending Market", "Yield Aggregator"
    protocol_name: str
    ancestry: str   # e.g., "Fork of Compound V2"
    critical_invariants: list[str]
    platform_rules: dict[str, Any]

# ==============================================================================
# Search & Scraper Capabilities
# ==============================================================================

class SearchTool:
    """
    The 'Screaming the Web' Engine.
    
    Uses Firecrawl API for web scraping and search.
    API Docs: https://docs.firecrawl.dev/
    """

    FIRECRAWL_BASE_URL = "https://api.firecrawl.dev"

    def __init__(self, llm: Any):
        self.llm = llm

        # Load .env if it exists
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    if "=" in line and not line.startswith("#"):
                        key, val = line.strip().split("=", 1)
                        os.environ[key] = val.strip()

        # Load multiple keys for load balancing
        self.api_keys = [
            os.getenv("FIRECRAWL_API_KEY_1"),
            os.getenv("FIRECRAWL_API_KEY_2")
        ]
        # Filter out None or empty keys
        self.api_keys = [k for k in self.api_keys if k]
        self.current_key_index = 0

        if self.api_keys:
            print(f"[Irene] {len(self.api_keys)} Firecrawl API keys configured for load balancing")
        else:
            # Check legacy key as fallback
            legacy_key = os.getenv("FIRECRAWL_API_KEY")
            if legacy_key:
                self.api_keys = [legacy_key]
                print("[Irene] Firecrawl API configured (legacy key)")
            else:
                print("[Irene] Warning: No FIRECRAWL_API_KEY set. Web research disabled.")

    def _firecrawl_request(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Make an authenticated request to Firecrawl API with load balancing."""
        if not self.api_keys:
            return {"success": False, "error": "FIRECRAWL API keys not configured"}

        # Round-robin selection
        api_key = self.api_keys[self.current_key_index]
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)

        url = f"{self.FIRECRAWL_BASE_URL}{endpoint}"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers=headers, method="POST")

            with urllib.request.urlopen(req, timeout=60) as response:
                return json.loads(response.read().decode())

        except urllib.error.HTTPError as e:
            error_body = e.read().decode() if e.fp else str(e)
            return {"success": False, "error": f"HTTP {e.code}: {error_body}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def search(self, query: str, limit: int = 5) -> list[dict[str, str]]:
        """
        Search the web using Firecrawl API.
        
        Args:
            query: Search query string
            limit: Max results (default: 5)
            
        Returns:
            List of dicts with 'title', 'snippet', 'link'
        """
        if not self.api_keys:
            return self._fallback_search(query)

        print(f"[Irene] Firecrawl search: '{query}'")

        payload = {
            "query": query,
            "limit": limit,
            "sources": ["web"],
            "timeout": 60000,
        }

        response = self._firecrawl_request("/v2/search", payload)

        if not response.get("success"):
            print(f"[Irene] Search failed: {response.get('error')}")
            return self._fallback_search(query)

        results = []
        for item in response.get("data", {}).get("web", []):
            results.append({
                "title": item.get("title", ""),
                "snippet": item.get("description", ""),
                "link": item.get("url", "")
            })

        print(f"[Irene] Found {len(results)} results")
        return results

    def scrape(self, url: str) -> dict[str, str]:
        """
        Scrape a URL and get its content as markdown.
        
        Args:
            url: The URL to scrape
            
        Returns:
            Dict with 'title', 'markdown', 'description', 'url'
        """
        if not self.api_keys:
            return {"error": "FIRECRAWL_API_KEY not configured", "url": url}

        print(f"[Irene] Scraping: {url}")

        payload = {
            "url": url,
            "formats": ["markdown"],
            "onlyMainContent": True,
            "timeout": 30000,
            "blockAds": True,
        }

        response = self._firecrawl_request("/v2/scrape", payload)

        if not response.get("success"):
            return {"error": response.get("error", "Unknown error"), "url": url}

        data = response.get("data", {})
        metadata = data.get("metadata", {})

        return {
            "title": metadata.get("title", ""),
            "markdown": data.get("markdown", ""),
            "description": metadata.get("description", ""),
            "url": url
        }

    def _fallback_search(self, query: str) -> list[dict[str, str]]:
        """Fallback when Firecrawl is not configured."""
        print(f"[Irene] No search API - using fallback for: '{query}'")
        return [{"title": "API Not Configured", "snippet": f"Configure FIRECRAWL_API_KEY to search for: {query}", "link": "#"}]

# ==============================================================================
# Archetype Detector
# ==============================================================================

class ArchetypeDetector:
    """Classifies the 'Nature of the Beast'."""

    ARCHETYPES = {
        "Lending Market": ["lend", "borrow", "collateral", "debt", "interest"],
        "AMM": ["swap", "pool", "liquidity", "provider", "xy=k"],
        "Yield Aggregator": ["vault", "strategy", "harvest", "compound"],
        "Synthetic Asset": ["mint", "burn", "peg", "collateralization"],
        "Governance": ["proposal", "vote", "timelock", "quorum"]
    }

    def detect(self, docs_content: str, llm: Any) -> str:
        """Identify the archetype."""
        # 1. Heuristic Scan
        scores = dict.fromkeys(self.ARCHETYPES, 0)
        lower_content = docs_content.lower()

        for arch, keywords in self.ARCHETYPES.items():
            for kw in keywords:
                if kw in lower_content:
                    scores[arch] += 1

        best_heuristic = max(scores, key=scores.get)

        # 2. LLM Confirmation
        if llm:
            try:
                print(f"[Irene] Verifying archetype '{best_heuristic}' with LLM...")
                prompt = (
                    f"Analyze the following DeFi protocol documentation snippet and determine its archetype.\\n"
                    f"Possible archetypes: {', '.join(self.ARCHETYPES.keys())}\\n\\n"
                    f"Documentation snippet:\\n{docs_content[:2000]}\\n\\n"
                    f"Heuristic identification: {best_heuristic}.\\n"
                    f"Return ONLY the archetype name from the list above. If it is a different valid DeFi category, return that."
                )
                # Use generate instead of ask
                if hasattr(llm, 'generate'):
                    response = llm.generate(prompt, temperature=0.1)
                else:
                    response = best_heuristic

                # Basic cleaning
                cleaned = response.strip().strip('"').strip("'")

                # Check if response matches one of our known archetypes keys
                match = next((k for k in self.ARCHETYPES if k.lower() == cleaned.lower()), None)
                if match:
                   return match

                # If LLM suggests a new plausible one
                if len(cleaned) < 50 and " " in cleaned and "unknown" not in cleaned.lower():
                     return cleaned.title()

            except Exception as e:
                print(f"[Irene] LLM validation failed: {e}")

        return best_heuristic

# ==============================================================================
# Irene Agent
# ==============================================================================

class Irene:
    """
    Irene Adler: Research 2.0
    The Universal Researcher who builds the 'Rules of Engagement'.
    """

    def __init__(self, target_url: str = None, db=None, run_id=None, root_dir: str = "."):
        self.root_dir = root_dir
        self.target_url = target_url
        self.db = db
        self.run_id = run_id

        # Initialize Core LLM
        try:
            self.config_loader = ConfigLoader()
            self.llm = LLMInterface(self.config_loader)
        except Exception as e:
            print(f"[Irene] Failed to initialize LLM: {e}")
            self.llm = None

        self.scope_parser = ScopeParser(root_dir)
        self.search = SearchTool(self.llm)
        self.archetype_detector = ArchetypeDetector()

    def execute(self, intent: str = "Audit Preparation") -> str:
        """
        Run the full Research Loop.
        1. Define Scope
        2. Scrape Context
        3. Detect Archetype & Ancestry
        4. Generate AUDIT_CONTEXT.md
        5. Store Findings in DB
        """
        print(f"\n[Irene] Starting Research 2.0 Loop: {intent}")

        # 1. Boundary Guard
        scope_file = self._find_scope_file()
        scope = self.scope_parser.parse(scope_file)
        print(f"[Irene] Scope Defined: {len(scope.whitelist)} whitelist items, {len(scope.blacklist)} blacklist items.")

        if self.db:
            self._store_research("Scope", json.dumps({"whitelist": scope.whitelist, "blacklist": scope.blacklist}), scope_file, {})

        # 2. Scrape & Learn
        readme_content = self._read_readme()

        if self.db and readme_content:
            self._store_research("README", readme_content, "README.md", {})

        # 3. Detect Archetype & Ancestry
        archetype = self.archetype_detector.detect(readme_content, self.llm)
        print(f"[Irene] Detected Archetype: {archetype}")
        
        ancestry = self._detect_ancestry(readme_content)
        print(f"[Irene] Detected Ancestry: {ancestry}")

        if self.db:
            meta = {"archetype": archetype, "ancestry": ancestry, "target_url": self.target_url}
            self._store_research("Analysis", json.dumps(meta), "IreneAgent", meta)

        # 4. Retrieve High-Signal Issues (Witness Statements - Compaction)
        issue_summary = ""
        if self.db:
            print(f"[Irene] Searching for High-Signal findings (Sherlock Knowledge Base)...")
            # Get top High severity findings from knowledge base
            high_signal_issues = self.db.get_findings_by_severity('High')
            
            if high_signal_issues:
                issue_summary = "\n## 5. High-Signal Witness Statements (Sherlock Findings)\n"
                # Show top 5 most valuable findings
                for issue in high_signal_issues[:5]:
                    issue_summary += f"*   **{issue['title']}**: {issue['summary'] or 'No summary'} `[{issue['vulnerability_type']}]`\n"
            else:
                issue_summary = "\n## 5. High-Signal Witness Statements\n*   No high-signal findings found."

        # 5. Generate Dossier
        dossier_path = self._generate_dossier(scope, archetype, ancestry, readme_content, issue_summary)

        if self.db:
            try:
                with open(dossier_path) as f:
                    self._store_research("Dossier", f.read(), dossier_path, {})
            except:
                pass

        return dossier_path

    def _store_research(self, topic: str, content: str, source: str, metadata: dict):
        """
        Persist findings to the 'research_library' table.
        Isolated from the execution logic.
        """
        if not self.db or not self.run_id:
            return

        try:
            conn = self.db._get_conn()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO research_library (run_id, topic, content, source_path, metadata) VALUES (?, ?, ?, ?, ?)",
                (self.run_id, topic, content, source, json.dumps(metadata))
            )
            conn.commit()
            conn.close()
            print(f"[Irene] Stored '{topic}' in Research Library.")
        except Exception as e:
            print(f"[Irene] DB Store Failed for {topic}: {e}")

    def research_query(self, query: str) -> dict[str, Any]:
        """
        Handle research query from Watson.
        """
        print(f"[Irene] Research Query: {query}")
        result = {}

        query_lower = query.lower()
        readme_content = self._read_readme()

        # 1. Ancestry Query
        if "ancestry" in query_lower or "fork" in query_lower:
            ancestry = self._detect_ancestry(readme_content)
            result["ancestry"] = ancestry
            result["known_issues_from_ancestor"] = self._get_ancestor_issues(ancestry)
            print(f"[Irene] Ancestry: {ancestry}")

        # 2. Known Issues Query
        if "known" in query_lower or "issue" in query_lower:
            # Check DB for ingested issues first
            if self.db:
                # Naive search over high-severity findings
                all_findings = self.db.get_findings_by_severity('High') + self.db.get_findings_by_severity('Medium')
                keywords = query.lower().split()
                
                matches = []
                for f in all_findings:
                    text = (f['title'] + " " + (f['summary'] or "")).lower()
                    if any(kw in text for kw in keywords):
                        matches.append(f)
                
                if matches:
                    result["ingested_issues"] = matches[:10]

            scope_file = self._find_scope_file()
            scope = self.scope_parser.parse(scope_file)
            result["known_issues"] = [
                {"id": ki.id, "title": ki.title, "source": ki.source}
                for ki in scope.known_issues
            ]

        # 3. Protocol Type Query
        if "type" in query_lower or "archetype" in query_lower:
            archetype = self.archetype_detector.detect(readme_content, self.llm)
            result["archetype"] = archetype
            result["invariant_focus"] = self._get_archetype_invariants(archetype)

        # 4. External Documentation Query (Web Search)
        if "external" in query_lower or "docs" in query_lower:
            protocol_name = self.root_dir.split('/')[-1]
            search_results = self.search.search(f"{protocol_name} smart contract audit")
            result["external_docs"] = search_results[:3]  # Top 3

        return result

    def _detect_ancestry(self, content: str) -> str:
        """Detect if protocol is a fork of known protocol."""
        ancestors = {
            "compound": "Compound V2",
            "aave": "Aave V2/V3",
            "uniswap": "Uniswap V2/V3",
            "curve": "Curve Finance",
            "balancer": "Balancer V2",
            "yearn": "Yearn V2",
            "maker": "MakerDAO",
            "openzeppelin": "OpenZeppelin Base",
        }

        content_lower = content.lower()
        for key, name in ancestors.items():
            if key in content_lower:
                if "fork" in content_lower or "based on" in content_lower:
                    return f"Fork of {name}"
                return f"Similar to {name}"

        return "Original Implementation"

    def _get_ancestor_issues(self, ancestry: str) -> list[str]:
        """Return known issue patterns for common ancestors."""
        known_patterns = {
            "Compound": [
                "First depositor inflation attack",
                "Interest rate kink errors",
                "Dust liquidations",
            ],
            "Aave": [
                "Flash loan callback reentrancy",
                "Oracle staleness",
                "Isolated collateral edge cases",
            ],
            "Uniswap": [
                "Read-only reentrancy via reserves",
                "Price manipulation via TWAP",
            ],
            "Curve": [
                "Read-only reentrancy via get_virtual_price",
                "Remove liquidity imbalance attacks",
            ],
        }

        for key, issues in known_patterns.items():
            if key in ancestry:
                return issues

        return []

    def _get_archetype_invariants(self, archetype: str) -> list[str]:
        """Return core invariants to check for an archetype."""
        archetype_invariants = {
            "Lending Market": [
                "Solvency: Collateral >= Debt",
                "Interest Rate Monotonicity",
                "Liquidation Incentive Compatibility",
            ],
            "Yield Aggregator": [
                "Exchange Rate Continuity",
                "No Value Creation (Yield Loops)",
                "First Depositor Protection",
            ],
            "AMM": [
                "Constant Product Invariant",
                "State Sync (Read-Only Reentrancy)",
                "Conservation of Value",
            ],
        }

        return archetype_invariants.get(archetype, ["Solvency", "Conservation of Value"])

    def _find_scope_file(self) -> str:
        for f in ["scope.txt", "README.md", "context.md"]:
            if os.path.exists(os.path.join(self.root_dir, f)):
                return os.path.join(self.root_dir, f)
        return "README.md" # fallback

    def _read_readme(self) -> str:
        try:
            with open(os.path.join(self.root_dir, "README.md")) as f:
                return f.read()
        except:
            return ""

    def _generate_dossier(self, scope, archetype, ancestry, context, issue_summary) -> str:
        """Write the AUDIT_CONTEXT.md artifact."""

        content = f"""# Audit Context: Universal Dossier
Generated by Irene (Research 2.0) on {datetime.now().isoformat()}

## 1. The Nature of the Beast (Archetype)
*   **Archetype**: {archetype}
*   **Ancestry**: {ancestry}
*   **Protocol Name**: {self.root_dir.split('/')[-1]}

## 2. Rules of Engagement (Scope)
### In Scope (Whitelist)
{self._format_list(scope.whitelist)}

### Out of Scope (Blacklist)
{self._format_list(scope.blacklist)}

## 3. Platform Rules
*   Platform: {scope.platform_rules.get('platform', 'Unknown')}
*   Ignore Admin Risk: {scope.platform_rules.get('ignore_admin', False)}

## 4. Research Notes
*   **Detected Keywords**: {archetype} associated keywords found in docs.
*   **Analysis**: This protocol appears to be a {archetype}. 

{issue_summary}
        """
        path = os.path.join(self.root_dir, "AUDIT_CONTEXT.md")
        with open(path, "w") as f:
            f.write(content)

        print(f"[Irene] Dossier generated at: {path}")
        return path

    def _format_list(self, items):
        return "\n".join([f"*   `{i}`" for i in items])

if __name__ == "__main__":
    agent = Irene(os.getcwd())
    agent.execute()
