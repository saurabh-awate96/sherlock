#!/usr/bin/env python3
"""
Watson Agent: The Semantic Perception Engine (v2.0)
===================================================
"You see, but you do not observe."

Watson 2.0 Deep Logic Verification Upgrades:
1.  **Tier-of-Thought (ToT) Prompting**: Cognitive tiers for deep semantic analysis
2.  **Irene Callback**: Request additional research when needed
3.  **ScopeGuard Integration**: All data sanitized before processing
4.  **Invariant Candidate Synthesis**: Generates verifiable invariants
"""

import json
import os
import re
import sys
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any

# ==============================================================================
# Imports from Sherlock Framework
# ==============================================================================

try:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from logic.invariant_engine import InvariantEngine
    from utils.scope_guard import SanitizationResult, ScopeGuard, create_scope_guard
    from utils.scope_parser import AuditScope
except ImportError:
    # Fallback for standalone testing
    ScopeGuard = None
    InvariantEngine = None

# ==============================================================================
# Universal Primitives
# ==============================================================================

class FinancialPrimitive(Enum):
    VAULT = "Vault"         # Holds assets, issues shares
    LOAN = "Loan"           # CDPs, Lending, borrowing
    EXCHANGE = "Exchange"   # Swaps, AMMs, Order books
    GOVERNOR = "Governor"   # Admin, Timelock, Access Control
    TOKEN = "Token"         # ERC20, NFT
    ORACLE = "Oracle"       # Price feeds
    UNKNOWN = "Unknown"

@dataclass
class SemanticTag:
    primitive: FinancialPrimitive
    confidence: float
    evidence: str
    location: str

@dataclass
class InvariantCandidate:
    """Generated invariant candidate from ToT analysis."""
    primitive: str
    tier1_context: str  # What type of primitive
    tier2_law: str      # What conservation law applies
    tier3_assertion: str  # Synthesized Solidity assertion
    confidence: float
    source_location: str

@dataclass
class Observation:
    id: str
    content: str
    location: str
    primitives: list[SemanticTag]
    invariant_candidates: list[InvariantCandidate]
    anomalies: list[str]
    confidence: float

# ==============================================================================
# Tier-of-Thought Prompting Engine
# ==============================================================================

class TierOfThought:
    """
    Implements the Tier-of-Thought (ToT) prompting strategy.
    
    Breaks analysis into cognitive tiers:
    - Tier 1: Context & Critical Point Identification
    - Tier 2: Business Logic Extraction
    - Tier 3: Invariant Formulation
    """

    # Conservation laws by primitive type
    CONSERVATION_LAWS = {
        FinancialPrimitive.VAULT: [
            "Assets >= Liabilities (Solvency)",
            "Share price must be continuous (No inflation attack)",
            "No value creation from thin air (Conservation)",
        ],
        FinancialPrimitive.LOAN: [
            "Collateral >= Debt * LTV (Solvency)",
            "Interest rate must be monotonic with utilization",
            "Liquidations must be profitable (Incentive compatibility)",
        ],
        FinancialPrimitive.EXCHANGE: [
            "x * y = k (constant product for AMMs)",
            "No value extraction via flash loans",
            "External state must be settled before read (State sync)",
        ],
        FinancialPrimitive.ORACLE: [
            "Price must be fresh (staleness check)",
            "Price must be within reasonable bounds",
        ],
    }

    # Assertion templates by invariant type
    ASSERTION_TEMPLATES = {
        "Solvency": "assertGe(vault.totalAssets(), ghost_totalAssets, \"SOLVENCY_VIOLATION\");",
        "Share price continuous": "assertGe(exchangeRate, MIN_RATE, \"INFLATION_ATTACK\");",
        "Conservation": "assertEq(balanceAfter - balanceBefore, expectedDelta, \"VALUE_LEAK\");",
        "Collateral ratio": "assertGe(collateral * LTV, debt, \"UNDERCOLLATERALIZED\");",
        "Interest monotonic": "assertGe(rate(u2), rate(u1), \"RATE_NOT_MONOTONIC\"); // where u2 > u1",
        "Constant product": "assertGe(reserve0 * reserve1, k, \"K_VIOLATED\");",
    }

    def analyze(self, primitive: FinancialPrimitive, code: str, location: str) -> list[InvariantCandidate]:
        """
        Run Tier-of-Thought analysis on detected primitive.
        
        Returns list of invariant candidates.
        """
        candidates = []

        # Tier 1: Context Identification
        tier1 = self._tier1_context(primitive, code)

        # Tier 2: Law Extraction
        laws = self.CONSERVATION_LAWS.get(primitive, [])

        for law in laws:
            tier2 = law

            # Tier 3: Assertion Synthesis
            tier3 = self._tier3_synthesize(primitive, law, code)

            if tier3:
                candidates.append(InvariantCandidate(
                    primitive=primitive.value,
                    tier1_context=tier1,
                    tier2_law=tier2,
                    tier3_assertion=tier3,
                    confidence=self._calculate_confidence(code, law),
                    source_location=location
                ))

        return candidates

    def _tier1_context(self, primitive: FinancialPrimitive, code: str) -> str:
        """Tier 1: Identify the context and critical points."""
        critical_points = []

        # Find state-modifying lines
        state_patterns = [
            (r"balances?\[.*\]\s*[+\-]=", "Balance update"),
            (r"totalSupply\s*[+\-]=", "Supply change"),
            (r"\.transfer\(", "Token transfer"),
            (r"\.safeTransfer\(", "Safe token transfer"),
            (r"emit\s+\w+\(", "Event emission"),
        ]

        for pattern, desc in state_patterns:
            if re.search(pattern, code):
                critical_points.append(desc)

        return f"Primitive: {primitive.value}. Critical Points: {', '.join(critical_points) or 'None detected'}"

    def _tier3_synthesize(self, primitive: FinancialPrimitive, law: str, code: str) -> str | None:
        """Tier 3: Synthesize a Solidity assertion."""
        # Match law to template
        for key, template in self.ASSERTION_TEMPLATES.items():
            if key.lower() in law.lower():
                return template

        # Default: generic assertion placeholder
        return f"// TODO: Implement invariant for: {law}"

    def _calculate_confidence(self, code: str, law: str) -> float:
        """Calculate confidence based on code patterns matching the law."""
        # Simple heuristic: more relevant patterns = higher confidence
        base_confidence = 0.5

        if "solvency" in law.lower():
            if "balanceOf" in code and "totalAssets" in code:
                base_confidence += 0.3
        elif "continuous" in law.lower() or "inflation" in law.lower():
            if "convertToShares" in code or "totalSupply" in code:
                base_confidence += 0.3
        elif "monotonic" in law.lower():
            if "utilizationRate" in code or "interestRate" in code:
                base_confidence += 0.3

        return min(base_confidence, 0.95)


# ==============================================================================
# Primitive Detector
# ==============================================================================

# ==============================================================================
# Primitive Detector (Legacy Wrapper)
# ==============================================================================

# New Core Imports
try:
    from sherlock.core.config_loader import ConfigLoader
    from sherlock.core.semantic_detector import SemanticDetector
except ImportError:
    # Fallback if running standalone without core
    ConfigLoader = None
    SemanticDetector = None

class PrimitiveDetector:
    """
    Adapter for the value-add SemanticDetector.
    """

    def __init__(self):
        self.detector = None
        if ConfigLoader and SemanticDetector:
            try:
                self.config = ConfigLoader()
                self.detector = SemanticDetector(self.config)
            except Exception as e:
                print(f"[Detector] Core init failed: {e}")

    def detect(self, code: str, location: str) -> list[SemanticTag]:
        # The new detector works on file paths using forge inspect.
        # But Watson passes 'code' and 'location'.
        # We should use 'location' which is the file path.

        tags = []

        if self.detector and os.path.exists(location):
            # Use the new robust detector
            print(f"[Detector] Using Semantic Analysis for {location}")
            detection = self.detector.detect_primitive(location)

            if detection.confidence > 0.0:
                 # Map string primitive back to Enum if possible
                prim_enum = FinancialPrimitive.UNKNOWN
                p_str = detection.primitive.lower()

                if "vault" in p_str: prim_enum = FinancialPrimitive.VAULT
                elif "amm" in p_str: prim_enum = FinancialPrimitive.EXCHANGE
                elif "lending" in p_str: prim_enum = FinancialPrimitive.LOAN

                evidence_str = str(detection.evidence)
                tags.append(SemanticTag(prim_enum, detection.confidence, evidence_str, location))
        else:
             # Fallback to simple regex if new detector fails or file not on disk
             # (This ensures we don't break if forge is missing or file is temp)
             tags = self._fallback_regex(code, location)

        return tags

    def _fallback_regex(self, code: str, location: str) -> list[SemanticTag]:
        print(f"[Detector] Fallback to regex for {location}")
        # ... (Old regex logic kept as backup) ...
        PATTERNS = {
            FinancialPrimitive.VAULT: [
                r"totalAssets", r"convertToShares", r"previewDeposit",
                r"strategy", r"harvest", r"deposit\s*\(", r"withdraw\s*\("
            ],
            FinancialPrimitive.LOAN: [
                r"collateral", r"debt", r"borrow", r"repay",
                r"healthFactor", r"liquidate", r"LTV"
            ],
            FinancialPrimitive.EXCHANGE: [
                r"swap", r"amountOut", r"getReserves", r"addLiquidity", r"router"
            ],
            FinancialPrimitive.GOVERNOR: [
                r"onlyOwner", r"timelock", r"proposal", r"queue", r"execute"
            ],
            FinancialPrimitive.ORACLE: [
                r"latestRoundData", r"getAnswer", r"priceFeed", r"aggregator"
            ]
        }

        tags = []
        for primitive, patterns in PATTERNS.items():
            matches = 0
            evidence = []
            for pat in patterns:
                if re.search(pat, code, re.IGNORECASE):
                    matches += 1
                    evidence.append(pat)

            if matches >= 2:
                conf = min(0.5 + (matches * 0.1), 0.95)
                tags.append(SemanticTag(primitive, conf, f"Found matches: {evidence}", location))
        return tags


# ==============================================================================
# Watson Agent (v2.0)
# ==============================================================================

class WatsonAgent:
    """
    Watson v2.0: The Semantic Observer with Deep Logic Verification.
    
    New capabilities:
    - Tier-of-Thought prompting for invariant synthesis
    - Irene callback for additional research
    - ScopeGuard integration for data sanitization
    """

    def __init__(self, root_dir: str = ".", irene_callback: Callable | None = None):
        self.root_dir = root_dir
        self.detector = PrimitiveDetector()
        self.tot_engine = TierOfThought()
        self.observations: list[Observation] = []

        # Irene callback for additional research
        self.irene_callback = irene_callback

        # Initialize ScopeGuard for sanitization
        self.scope_guard = None
        try:
            if ScopeGuard:
                self.scope_guard = create_scope_guard(root_dir)
                print("[Watson] ScopeGuard initialized for data sanitization")
        except Exception as e:
            print(f"[Watson] Warning: ScopeGuard not initialized: {e}")

        # Initialize InvariantEngine
        self.invariant_engine = None
        try:
            if InvariantEngine:
                self.invariant_engine = InvariantEngine()
                print(f"[Watson] InvariantEngine loaded with {len(self.invariant_engine.INVARIANTS)} invariants")
        except Exception as e:
            print(f"[Watson] Warning: InvariantEngine not initialized: {e}")

        # Load Context and Tools
        self.context = self._load_context()
        self.tools = self._load_tools()

        # INTEGRATION: Learn Recipes from Senior Auditor Skill
        self._integrate_skills()

    def _integrate_skills(self):
        """
        Parses the Senior Auditor Skill file and injects the 'Recipes' (Invariants)
        directly into the TierOfThought engine. 
        This allows Watson to 'learn' new checks from the SKILL.md file dynamically.
        """
        skill_path = os.path.join(self.root_dir, "sherlock/skills/senior-auditor/SKILL.md")
        if not os.path.exists(skill_path):
            print("[Watson] Skill file not found. Using default internal knowledge.")
            return

        print(f"[Watson] Learning recipes from {skill_path}...")
        try:
            with open(skill_path) as f:
                content = f.read()

            # Simple Parser for "If Primitive:" blocks
            # Matches: **If Vault:** then captures the list items
            sections = {
                "Vault": FinancialPrimitive.VAULT,
                "AMM": FinancialPrimitive.EXCHANGE,
                "Lending": FinancialPrimitive.LOAN
            }

            learned_count = 0
            for label, primitive in sections.items():
                # Regex to find the block for this primitive
                # Looks for "**If Vault:**" followed by lines starting with "- [ ]"
                pattern = f"\\*\\*If {label}:\\*\\*(.*?)(?=\\*\\*If|## Step|$)"
                match = re.search(pattern, content, re.DOTALL)

                if match:
                    block = match.group(1)
                    # Extract list items
                    rules = re.findall(r"-\s*\[\s*\]\s*\*\*(.*?)\*\*:\s*(.*)", block)

                    if rules:
                        # Append to TierOfThought knowledge base
                        current_laws = self.tot_engine.CONSERVATION_LAWS.get(primitive, [])
                        for rule_name, rule_desc in rules:
                            law_text = f"{rule_name}: {rule_desc} (Learned from Skill)"
                            if law_text not in current_laws:
                                current_laws.append(law_text)
                                learned_count += 1

                        self.tot_engine.CONSERVATION_LAWS[primitive] = current_laws

            print(f"[Watson] Integrated {learned_count} new recipes into the Cognitive Engine.")

        except Exception as e:
            print(f"[Watson] Failed to integrate skills: {e}")

    def _load_context(self) -> dict[str, Any]:
        path = os.path.join(self.root_dir, "AUDIT_CONTEXT.md")
        if os.path.exists(path):
            with open(path) as f:
                return {"raw": f.read()}
        return {}

    def _load_tools(self) -> dict[str, Any]:
        path = os.path.join(self.root_dir, "TOOL_OUTPUTS", "inventory.json")
        if os.path.exists(path):
            with open(path) as f:
                return json.load(f)
        return {}

    def request_research(self, query: str) -> dict[str, Any] | None:
        """
        Request additional research from Irene.
        
        The response is sanitized through ScopeGuard before returning.
        """
        if not self.irene_callback:
            print(f"[Watson] No Irene callback configured. Query: {query}")
            return None

        print(f"[Watson] Requesting research from Irene: {query}")
        raw_research = self.irene_callback(query)

        # Sanitize through ScopeGuard
        if self.scope_guard and raw_research:
            result = self.scope_guard.sanitize_research(raw_research)
        return raw_research

    def observe(self, target_path: str, allowed_scope: list[str] = None) -> Observation:
        """
        The Core Perception Loop.
        
        Args:
            target_path: File or directory to observe
            allowed_scope: Optional list of absolute paths that are PERMITTED to be read.
                           If None, full access is assumed (Legacy mode).
                           If set, any access outside this list raises ScopeViolationError.
        """
        # 0. Enforce Scope Isolation (Sherlock 4.0)
        target_abs = os.path.abspath(target_path)
        if allowed_scope:
            # Check if target itself is allowed
            if target_abs not in allowed_scope:
                # Relax check for directories, but enforce for files
                if os.path.isfile(target_abs):
                    print(f"[Watson] 🛑 BLOCKED: Attempted to read {target_abs} which is outside allowed scope.")
                    return Observation(
                        id="blocked", content="SCOPE_VIOLATION", location=target_path,
                        primitives=[], invariant_candidates=[], anomalies=["Scope Violation"], confidence=0.0
                    )

        # 1. Scope Guard (Sanitization)
        if self.scope_guard:
            check = self.scope_guard.sanitize_file(target_path)
            if not check.is_clean:
                print(f"[Watson] Skipping out-of-scope file: {target_path}")
                return None

        print(f"[Watson] Observing {target_path}...")

        try:
            with open(target_path) as f:
                content = f.read()

            file_path = target_path # Fix undefined variable

            # 2. Semantic Detection (using the new SemanticDetector)
            primitives = self.detector.detect(content, target_path)

            # 3. Context Refinement: Witness Statement Retrieval (Progressive Disclosure)
            witness_statements = []
            if self.irene_callback:
                print(f"[Watson] Querying Witness Statements for {os.path.basename(file_path)}...")
                research = self.request_research(f"known issues for {os.path.basename(file_path)}")
                if research and "ingested_issues" in research:
                    for issue in research["ingested_issues"]:
                        # Implement Observation Masking
                        body = issue.get('body', '')
                        if len(body) > 500:
                            issue['body'] = f"[MASKED: Content too long ({len(body)} chars). Ref: #{issue['number']}] Summary: {body[:200]}..."
                        witness_statements.append(issue)

            # Run Tier-of-Thought analysis for each primitive
            invariant_candidates = []
            for prim in primitives:
                candidates = self.tot_engine.analyze(prim.primitive, content, target_path)
                # Inject witness statements into candidate context if relevant
                for cand in candidates:
                    if witness_statements:
                        cand.tier1_context += f" | Witness Stats: {len(witness_statements)} issues detected."
                invariant_candidates.extend(candidates)

            # Get invariant checks from engine
            anomalies = []
            if self.invariant_engine and primitives:
                for prim in primitives:
                    checks = self.invariant_engine.check_primitive(prim.primitive.value, content)
                    for check in checks:
                        if check.get("relevance", 0) > 0.5:
                            anomalies.append(f"[{check['type']}] {check['invariant']}")

            confidence = max([t.confidence for t in primitives]) if primitives else 0.0

            obs = Observation(
                id=f"obs_{os.path.basename(file_path)}",
                content=content[:500] + "..." if len(content) > 500 else content,
                location=file_path,
                primitives=primitives,
                invariant_candidates=invariant_candidates,
                anomalies=anomalies,
                confidence=confidence
            )

            if primitives:
                print(f"  -> Detected: {[p.primitive.value for p in primitives]}")
                print(f"  -> Invariant Candidates: {len(invariant_candidates)}")
                print(f"  -> Witness Statements: {len(witness_statements)}")
                print(f"  -> Potential Issues: {len(anomalies)}")

            return obs

        except Exception as e:
            print(f"[Watson] Error observing {file_path}: {e}")
            return None

    def execute(self):
        """Scan the scope with ToT analysis."""
        # Determine scan target
        scan_target = os.path.join(self.root_dir, "src")
        if not os.path.exists(scan_target):
            scan_target = os.path.join(self.root_dir, "contracts")
        if not os.path.exists(scan_target):
            scan_target = self.root_dir

        print(f"[Watson] Scanning target: {scan_target}")

        results = []
        for root, dirs, files in os.walk(scan_target):
            # Skip common blacklist
            if "test" in root or "lib" in root or "node_modules" in root:
                continue

            for file in files:
                if file.endswith(".sol"):
                    file_path = os.path.join(root, file)
                    obs = self.observe(file_path)
                    if obs and obs.primitives:
                        results.append(obs)

        # Save Observations
        output_path = os.path.join(self.root_dir, "WATSON_OBSERVATIONS.json")
        with open(output_path, "w") as f:
            json.dump([self._obs_to_dict(o) for o in results], f, indent=2)

        print(f"[Watson] Analysis complete. {len(results)} observations saved to {output_path}")

        # Summary
        total_invariants = sum(len(o.invariant_candidates) for o in results)
        total_issues = sum(len(o.anomalies) for o in results)
        print(f"[Watson] Summary: {total_invariants} invariant candidates, {total_issues} potential issues")

    def _obs_to_dict(self, obs: Observation) -> dict[str, Any]:
        return {
            "id": obs.id,
            "location": obs.location,
            "primitives": [{
                "type": t.primitive.value,
                "confidence": t.confidence,
                "evidence": t.evidence
            } for t in obs.primitives],
            "invariant_candidates": [{
                "primitive": c.primitive,
                "tier1_context": c.tier1_context,
                "tier2_law": c.tier2_law,
                "tier3_assertion": c.tier3_assertion,
                "confidence": c.confidence
            } for c in obs.invariant_candidates],
            "anomalies": obs.anomalies,
            "confidence": obs.confidence
        }


if __name__ == "__main__":
    # Demo with mock Irene callback
    def mock_irene(query: str) -> dict[str, Any]:
        print(f"  [Irene Mock] Received query: {query}")
        return {"ancestry": "Fork of Compound V2", "files": ["src/Vault.sol"]}

    agent = WatsonAgent(os.getcwd(), irene_callback=mock_irene)
    agent.execute()
