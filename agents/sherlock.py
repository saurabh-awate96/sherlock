"""
Google Antigravity: Sherlock Agent (Enhanced)
==============================================

Sherlock is THE DEDUCTION ENGINE - actually an ABDUCTION engine.

"The Science of Deduction" is a misnomer. Sherlock's primary methodology is:
- ABDUCTION: Inference to the Best Explanation
- BAYESIAN UPDATING: Rapid probability refinement as evidence accumulates
- BACKWARD REASONING: Tracing effects to causes

Sherlock specializes in the SPECIFIC:
- The mud on a shoe
- The scratch on a watch  
- The specific type of tobacco ash

His genius: reconstructing a SPECIFIC EVENT from physical traces.
He is a TACTICAL genius.

"I never guess. It is a shocking habit—destructive to the logical faculty."
- Sherlock Holmes

**Architectural Resilience**:
- Inherits from InternalAgentBase
- Uses EventBus for Findings
- Enforces Idempotency
"""

import argparse
import json
import os
import hashlib
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
from enum import Enum

# Import cognitive modules
try:
    from cognitive_core import MindPalace, Room, create_default_palace
    from brain_attic import BrainAttic
    from bayesian_engine import (
        BayesianReasoner, Hypothesis, Evidence, EvidenceType, 
        HypothesisStatus, UpdateResult
    )
    from reasoning_protocols import (
        ReasoningEngine, Observation as ReasoningObservation,
        Hypothesis as ReasoningHypothesis, CausalChain
    )
    from internal_agent_base import InternalAgentBase
    from architectural_core import EventType
except ImportError:
    from agents.cognitive_core import MindPalace, Room, create_default_palace
    from agents.brain_attic import BrainAttic
    from agents.bayesian_engine import (
        BayesianReasoner, Hypothesis, Evidence, EvidenceType,
        HypothesisStatus, UpdateResult
    )
    from agents.reasoning_protocols import (
        ReasoningEngine, Observation as ReasoningObservation,
        Hypothesis as ReasoningHypothesis, CausalChain
    )
    from agents.internal_agent_base import InternalAgentBase
    from agents.architectural_core import EventType


# ==============================================================================
# Detection Data Structures
# ==============================================================================

class FindingSeverity(Enum):
    """Severity levels for findings."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFORMATIONAL = "INFORMATIONAL"


class FindingStatus(Enum):
    """Status of a finding in the analysis pipeline."""
    CANDIDATE = "candidate"      # Initial detection
    HYPOTHESIS = "hypothesis"    # Under investigation
    PROBABLE = "probable"        # High probability
    VERIFIED = "verified"        # Confirmed by Moriarty
    DISMISSED = "dismissed"      # False positive


@dataclass
class Finding:
    """A security finding detected by Sherlock."""
    id: str
    title: str
    description: str
    vulnerability_type: str
    location: str
    severity: FindingSeverity
    
    # Probabilistic fields
    confidence: float
    probability: float
    status: FindingStatus
    
    # Evidence chain
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    
    # Reasoning
    reasoning_chain: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    
    # Context
    code_snippet: Optional[str] = None
    rag_matches: List[Dict[str, Any]] = field(default_factory=list)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "vulnerability_type": self.vulnerability_type,
            "location": self.location,
            "severity": self.severity.value,
            "confidence": self.confidence,
            "probability": self.probability,
            "status": self.status.value,
            "evidence": self.evidence,
            "reasoning_chain": self.reasoning_chain,
            "assumptions": self.assumptions,
            "code_snippet": self.code_snippet[:200] if self.code_snippet else None,
            "rag_matches": self.rag_matches,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class HypothesisTask:
    """A task for Moriarty to verify."""
    task_id: str
    finding_id: str
    vulnerability: str
    target: str
    evidence: List[str]
    goal: str
    probability: float
    assumptions: List[str]


# ==============================================================================
# Sherlock Agent
# ==============================================================================

class SherlockAgent(InternalAgentBase):
    """
    THE DEDUCTION ENGINE (Actually Abduction + Bayesian)
    """
    
    def __init__(
        self,
        mind_palace: Optional[MindPalace] = None,
        bayesian_engine: Optional[BayesianReasoner] = None,
        reasoning_engine: Optional[ReasoningEngine] = None,
        session_id: Optional[str] = None
    ):
        """
        Initialize Sherlock Agent.
        """
        super().__init__(agent_name="Sherlock", session_id=session_id)
        
        self.mind_palace = mind_palace or create_default_palace()
        self.bayesian = bayesian_engine or BayesianReasoner()
        self.reasoning = reasoning_engine or ReasoningEngine()
        
        self.findings: Dict[str, Finding] = {}
        self.finding_count = 0
        self.processed_signatures = set() # For Idempotency
        
        self.log("Initialized with abductive reasoning and Bayesian engine")
        self.log("'The game is afoot!'")
    
    # --------------------------------------------------------------------------
    # Idempotency Check
    # --------------------------------------------------------------------------
    def _is_processed(self, obs_id: str, content_hash: str) -> bool:
        """Check if this observation has already been processed (Idempotency)."""
        sig = f"{obs_id}:{content_hash}"
        if sig in self.processed_signatures:
            return True
        self.processed_signatures.add(sig)
        return False

    # --------------------------------------------------------------------------
    # Core Analysis Methods
    # --------------------------------------------------------------------------
    
    def analyze(
        self,
        observation: Dict[str, Any],
        context: Optional[Any] = None
    ) -> Finding:
        """
        Analyze an observation using abductive reasoning.
        """
        obs_id = observation.get("id", f"obs_{self.finding_count}")
        content = observation.get("content", "")
        content_hash = hashlib.md5(content.encode()).hexdigest()
        
        # Idempotency Check
        if self._is_processed(obs_id, content_hash):
            self.log(f"Skipping duplicate observation: {obs_id}")
            # Return existing or placeholder (in reality we just skip, but here we need to return something)
            # We'll return a special "Duplicate" finding that gets filtered out
            return self._create_duplicate_finding(obs_id)

        location = observation.get("location", "unknown")
        signals = observation.get("signals", [])
        anomalies = observation.get("anomalies", [])
        
        # Step 1: Consult Mind Palace
        rag_matches = self._consult_mind_palace(content, signals)
        
        # Step 2: Generate abductive hypothesis
        reasoning_obs = ReasoningObservation(
            id=obs_id,
            description=f"Anomalies: {anomalies}" if anomalies else f"Signals: {signals}",
            context=location,
            code_snippet=content[:500]
        )
        hypotheses = self.reasoning.abduce(reasoning_obs)
        
        if not hypotheses:
            return self._create_informational_finding(observation)
        
        best_hypothesis = self.reasoning.select_best_explanation(hypotheses)
        
        # Step 3: Create Bayesian hypothesis
        vuln_type = self._extract_vulnerability_type(best_hypothesis.explanation)
        
        bayesian_hyp = self.bayesian.create_hypothesis(
            name=f"Finding at {location}",
            description=best_hypothesis.explanation,
            vulnerability_type=vuln_type,
            location=location,
            assumptions=best_hypothesis.assumptions
        )
        
        # Step 4: Apply RAG match evidence
        for match in rag_matches:
            match_score = match.get("relevance", 0.5)
            if match_score > 0.6:
                self.bayesian.apply_rag_match(
                    bayesian_hyp.id,
                    match_score,
                    match.get("description", "Pattern match"),
                    is_historical_exploit=match.get("is_exploit", False)
                )
        
        # Step 4.5: Apply Research Context (Prior Boost)
        if isinstance(context, dict):
            common_vulns = context.get("common_vulnerabilities", [])
            for cv in common_vulns:
                if cv.get("name", "").lower() in vuln_type.lower():
                    self.log(f"Boosting prior for {vuln_type} (Research Match)")
                    self.bayesian.update(
                        bayesian_hyp.id,
                        Evidence(
                            id=f"ev_research_{self.finding_count}",
                            evidence_type=EvidenceType.CONTEXT,
                            description=f"Known common vulnerability for protocol type: {cv.get('name')}",
                            source="researcher",
                            strength=0.7,
                            supports_hypothesis=True
                        )
                    )
                    break

        # Step 5: Apply anomaly evidence
        for anomaly in anomalies:
            evidence = Evidence(
                id=f"ev_{self.finding_count}_{len(self.bayesian.update_history)}",
                evidence_type=EvidenceType.CODE_STRUCTURE,
                description=anomaly.get("description", "Anomaly detected"),
                source="watson",
                strength={"HIGH": 0.8, "MEDIUM": 0.5, "LOW": 0.3}.get(
                    anomaly.get("severity", "MEDIUM"), 0.5
                ),
                supports_hypothesis=True
            )
            self.bayesian.update(bayesian_hyp.id, evidence)
        
        # Step 6: Determine severity and create finding
        probability = self.bayesian.get_posterior(bayesian_hyp.id)
        severity = self._determine_severity(vuln_type, probability, anomalies)
        
        finding = Finding(
            id=f"finding_{self.finding_count}",
            title=f"{vuln_type} in {location.split(':')[0]}",
            description=best_hypothesis.explanation,
            vulnerability_type=vuln_type,
            location=location,
            severity=severity,
            confidence=bayesian_hyp.confidence,
            probability=probability,
            status=FindingStatus.HYPOTHESIS if probability > 0.3 else FindingStatus.CANDIDATE,
            evidence=[
                {
                    "type": e.evidence_type.value,
                    "description": e.description,
                    "strength": e.strength
                }
                for e in bayesian_hyp.evidence_chain
            ],
            reasoning_chain=[
                f"Abduction: {best_hypothesis.explanation}",
                f"Prior: {bayesian_hyp.prior_probability:.2f}",
                f"Posterior: {probability:.2f}",
                f"Evidence count: {len(bayesian_hyp.evidence_chain)}"
            ],
            assumptions=best_hypothesis.assumptions,
            code_snippet=content[:500],
            rag_matches=rag_matches
        )
        
        self.findings[finding.id] = finding
        self.finding_count += 1
        
        self.log(f"Finding: {finding.title} (Prob: {probability:.2f})")
        
        # Publish Finding Event
        self.publish_event(EventType.FINDING, finding.to_dict())
        
        return finding
    
    def rapid_bayesian_scan(
        self,
        observations: List[Dict[str, Any]],
        research_context: Optional[Dict[str, Any]] = None
    ) -> List[Finding]:
        """
        Rapid scan of multiple observations with Bayesian updating.
        """
        self.log(f"Initiating rapid Bayesian scan on {len(observations)} observations...")
        
        findings = []
        
        for obs in observations:
            # Quick scoring - skip if no anomalies and low confidence
            if not obs.get("anomalies") and obs.get("confidence", 0) < 0.5:
                continue
            
            finding = self.analyze(obs, context=research_context)
            
            # Filter out duplicates and dismissed
            if finding.status != FindingStatus.DISMISSED and finding.title != "DUPLICATE":
                findings.append(finding)
        
        # Sort by probability
        findings.sort(key=lambda f: f.probability, reverse=True)
        
        self.log(f"Scan complete: {len(findings)} findings above threshold")
        
        return findings
    
    # --------------------------------------------------------------------------
    # Mind Palace Consultation
    # --------------------------------------------------------------------------
    
    def _consult_mind_palace(
        self,
        code: str,
        signals: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Query the Mind Palace for similar patterns.
        """
        matches = []
        
        # Determine which rooms to search based on signals
        rooms_to_search = set()
        signal_room_map = {
            "external_call": Room.REENTRANCY,
            "delegatecall": Room.REENTRANCY,
            "transfer_call": Room.REENTRANCY,
            "msg_value": Room.REENTRANCY,
            "price": Room.ORACLE_MANIPULATION,
            "oracle": Room.ORACLE_MANIPULATION,
            "owner": Room.ACCESS_CONTROL,
            "tx_origin": Room.ACCESS_CONTROL,
            "block_timestamp": Room.TIMESTAMP,
        }
        
        for signal in signals:
            for key, room in signal_room_map.items():
                if key in signal.lower():
                    rooms_to_search.add(room)
        
        if not rooms_to_search:
            rooms_to_search = [Room.GENERAL]
        
        # Query the palace
        query = f"Code pattern: {' '.join(signals[:5])}"
        result = self.mind_palace.retrieve(
            query=query,
            rooms=list(rooms_to_search),
            top_k=5,
            min_similarity=0.3
        )
        
        for memory in result.memories:
            matches.append({
                "id": memory.id,
                "description": memory.association,
                "room": memory.room.value,
                "relevance": memory.confidence,
                "is_exploit": memory.memory_type.value == "historical_exploit"
            })
        
        return matches
    
    # --------------------------------------------------------------------------
    # Static Analysis Integration
    # --------------------------------------------------------------------------
    
    def process_slither_results(
        self,
        slither_output: Dict[str, Any]
    ) -> List[Finding]:
        """
        Process Slither static analysis results.
        """
        findings = []
        detectors = slither_output.get("results", {}).get("detectors", [])
        
        self.log(f"Processing {len(detectors)} Slither findings...")
        
        for detector in detectors:
            # Create observation from Slither finding
            observation = {
                "id": f"slither_{detector.get('check', 'unknown')}",
                "content": detector.get("first_markdown_element", ""),
                "location": self._extract_location(detector.get("elements", [])),
                "signals": [detector.get("check", "")],
                "anomalies": [{
                    "type": "static_analysis",
                    "description": detector.get("description", ""),
                    "severity": detector.get("impact", "MEDIUM").upper()
                }],
                "confidence": self._slither_confidence(detector.get("confidence", "Medium"))
            }
            
            finding = self.analyze(observation, context="slither")
            
            # Additional Bayesian update with Slither-specific evidence
            if finding.id.startswith("finding_"):
                self._apply_slither_evidence(finding, detector)
            
            findings.append(finding)
        
        return findings
    
    def _apply_slither_evidence(self, finding: Finding, detector: Dict[str, Any]):
        """Apply Slither-specific evidence to a finding."""
        impact = detector.get("impact", "Medium").upper()
        confidence = detector.get("confidence", "Medium").upper()
        
        # Map to strength
        impact_strength = {"HIGH": 0.8, "MEDIUM": 0.5, "LOW": 0.3}.get(impact, 0.5)
        confidence_mult = {"HIGH": 1.0, "MEDIUM": 0.7, "LOW": 0.4}.get(confidence, 0.7)
        
        # This would update the Bayesian hypothesis
        # For now, update the finding directly
        finding.probability *= (1 + impact_strength * confidence_mult * 0.3)
        finding.probability = min(0.99, finding.probability)
    
    def _extract_location(self, elements: List[Dict]) -> str:
        """Extract location from Slither elements."""
        if not elements:
            return "unknown"
        
        first = elements[0]
        source_mapping = first.get("source_mapping", {})
        filename = source_mapping.get("filename_short", "unknown")
        lines = source_mapping.get("lines", [0])
        
        return f"{filename}:{lines[0] if lines else 0}"
    
    def _slither_confidence(self, confidence: str) -> float:
        """Map Slither confidence to numeric value."""
        return {"High": 0.9, "Medium": 0.6, "Low": 0.3}.get(confidence, 0.5)
    
    # --------------------------------------------------------------------------
    # Hypothesis Synthesis for Moriarty
    # --------------------------------------------------------------------------
    
    def synthesize_hypotheses(
        self,
        min_probability: float = 0.4
    ) -> List[HypothesisTask]:
        """
        Synthesize high-confidence hypotheses for Moriarty.
        """
        tasks = []
        
        # Get findings above threshold
        probable_findings = [
            f for f in self.findings.values()
            if f.probability >= min_probability and f.status != FindingStatus.DISMISSED
        ]
        
        # Sort by probability
        probable_findings.sort(key=lambda f: f.probability, reverse=True)
        
        self.log(f"Synthesizing {len(probable_findings)} hypotheses for Moriarty...")
        
        for finding in probable_findings:
            task = HypothesisTask(
                task_id=f"task_{finding.id}",
                finding_id=finding.id,
                vulnerability=finding.vulnerability_type,
                target=finding.location,
                evidence=[
                    f"{e['type']}: {e['description']}"
                    for e in finding.evidence[:3]
                ],
                goal=self._generate_exploit_goal(finding.vulnerability_type),
                probability=finding.probability,
                assumptions=finding.assumptions
            )
            tasks.append(task)
        
        return tasks
    
    def _generate_exploit_goal(self, vuln_type: str) -> str:
        """Generate exploit goal based on vulnerability type."""
        goals = {
            "reentrancy": "Drain contract balance via recursive call",
            "oracle_manipulation": "Manipulate price to extract value",
            "access_control": "Call privileged function as unauthorized user",
            "flash_loan": "Use flash loan to extract value atomically",
            "liquidation": "Trigger unfair liquidation cascade",
            "governance": "Manipulate governance vote outcome",
            "timestamp": "Exploit block.timestamp dependence",
            "front_running": "Front-run transaction for MEV extraction",
        }
        
        for key, goal in goals.items():
            if key in vuln_type.lower():
                return goal
        
        return "Demonstrate exploitability of vulnerability"
    
    # --------------------------------------------------------------------------
    # Backward Reasoning
    # --------------------------------------------------------------------------
    
    def reason_backwards(self, effect: str) -> Dict[str, Any]:
        """
        Apply backward reasoning from an effect.
        """
        chains = self.reasoning.trace_causal_chain(effect, depth=3)
        
        return {
            "effect": effect,
            "causal_chain": [
                {
                    "level": i,
                    "effect": chain.effect,
                    "likely_cause": chain.selected_cause,
                    "all_causes": [
                        {"cause": c, "probability": p}
                        for c, p in chain.potential_causes[:3]
                    ]
                }
                for i, chain in enumerate(chains)
            ]
        }
    
    # --------------------------------------------------------------------------
    # Helper Methods
    # --------------------------------------------------------------------------
    
    def _extract_vulnerability_type(self, explanation: str) -> str:
        """Extract vulnerability type from explanation."""
        vuln_keywords = {
            "reentrancy": ["reentrancy", "recursive", "callback", "re-enter"],
            "oracle_manipulation": ["oracle", "price", "manipulation", "flash loan"],
            "access_control": ["access", "authorization", "permission", "owner"],
            "front_running": ["front-run", "sandwich", "mev"],
            "timestamp": ["timestamp", "block.timestamp"],
            "arithmetic": ["overflow", "underflow", "arithmetic"],
            "liquidation": ["liquidation", "collateral"],
        }
        
        explanation_lower = explanation.lower()
        
        for vuln_type, keywords in vuln_keywords.items():
            if any(kw in explanation_lower for kw in keywords):
                return vuln_type
        
        return "unknown"
    
    def _determine_severity(
        self,
        vuln_type: str,
        probability: float,
        anomalies: List[Dict]
    ) -> FindingSeverity:
        """Determine severity based on vulnerability type and probability."""
        # Base severity from vulnerability type
        type_severity = {
            "reentrancy": FindingSeverity.CRITICAL,
            "oracle_manipulation": FindingSeverity.HIGH,
            "access_control": FindingSeverity.HIGH,
            "flash_loan": FindingSeverity.HIGH,
            "front_running": FindingSeverity.MEDIUM,
            "timestamp": FindingSeverity.LOW,
            "arithmetic": FindingSeverity.MEDIUM,
        }
        
        base_severity = type_severity.get(vuln_type, FindingSeverity.MEDIUM)
        
        # Adjust based on probability
        if probability < 0.3:
            # Lower severity for low-probability findings
            severity_order = [
                FindingSeverity.INFORMATIONAL,
                FindingSeverity.LOW,
                FindingSeverity.MEDIUM,
                FindingSeverity.HIGH,
                FindingSeverity.CRITICAL
            ]
            current_idx = severity_order.index(base_severity)
            return severity_order[max(0, current_idx - 1)]
        
        return base_severity
    
    def _create_informational_finding(self, observation: Dict) -> Finding:
        """Create an informational finding for low-priority observations."""
        self.finding_count += 1
        return Finding(
            id=f"finding_{self.finding_count}",
            title=f"Observation at {observation.get('location', 'unknown')}",
            description="Low-priority observation with no significant anomalies",
            vulnerability_type="informational",
            location=observation.get("location", "unknown"),
            severity=FindingSeverity.INFORMATIONAL,
            confidence=0.2,
            probability=0.1,
            status=FindingStatus.DISMISSED
        )

    def _create_duplicate_finding(self, obs_id: str) -> Finding:
        """Create a placeholder duplicate finding."""
        return Finding(
            id=f"dup_{obs_id}",
            title="DUPLICATE",
            description="Duplicate observation detected",
            vulnerability_type="duplicate",
            location="n/a",
            severity=FindingSeverity.INFORMATIONAL,
            confidence=0.0,
            probability=0.0,
            status=FindingStatus.DISMISSED
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get Sherlock's analysis statistics."""
        severity_counts = {}
        status_counts = {}
        
        for finding in self.findings.values():
            if finding.title == "DUPLICATE": continue
            severity_counts[finding.severity.value] = severity_counts.get(finding.severity.value, 0) + 1
            status_counts[finding.status.value] = status_counts.get(finding.status.value, 0) + 1
        
        return {
            "total_findings": len(self.findings),
            "by_severity": severity_counts,
            "by_status": status_counts,
            "bayesian_stats": {
                "hypotheses": len(self.bayesian.hypotheses),
                "updates": len(self.bayesian.update_history)
            },
            "mind_palace_stats": self.mind_palace.get_statistics()
        }
    
    def export_findings(self) -> List[Dict[str, Any]]:
        """Export all findings as JSON-serializable dicts."""
        return [f.to_dict() for f in self.findings.values() if f.title != "DUPLICATE"]


# ==============================================================================
# CLI Interface (Backward Compatible)
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(description="Sherlock Deduction Agent (Enhanced)")
    parser.add_argument("--action", required=True, choices=["detect", "synthesize", "backward", "stats"])
    parser.add_argument("--slither-input")
    parser.add_argument("--db")
    parser.add_argument("--input", required=True, dest="input_file")
    parser.add_argument("--output", required=True)
    parser.add_argument("--context", help="Path to research context JSON")
    parser.add_argument("--session-id", help="Correlation ID")
    args = parser.parse_args()

    # Load context if provided
    research_context = None
    if args.context and os.path.exists(args.context):
        try:
            with open(args.context, 'r') as f:
                research_context = json.load(f)
        except Exception as e:
            print(f"[Sherlock] Failed to load context: {e}")

    sherlock = SherlockAgent(session_id=args.session_id)
    
    sherlock.log(f"Executing action: {args.action}")

    if args.action == "detect":
        # Load observations and perform RAG-enhanced detection
        with open(args.input_file, 'r') as f:
            data = json.load(f)
        
        # Handle both observation format and slither format
        if "detectors" in str(data):
            # Slither format
            findings = sherlock.process_slither_results(data)
        else:
            # Observation format from Watson
            observations = data if isinstance(data, list) else data.get("observations", [])
            findings = sherlock.rapid_bayesian_scan(observations, research_context=research_context)
        
        output = [f.to_dict() for f in findings]
        
        with open(args.output, "w") as f:
            json.dump(output, f, indent=2)
        
        sherlock.log(f"RAG detection complete. {len(findings)} candidates found.")

    elif args.action == "synthesize":
        # Load candidates and synthesize hypotheses
        with open(args.input_file, 'r') as f:
            candidates = json.load(f)
        
        # Reconstruct findings from candidates
        for cand in candidates:
            finding = Finding(
                id=cand.get("id", f"finding_{sherlock.finding_count}"),
                title=cand.get("title", "Unknown"),
                description=cand.get("description", ""),
                vulnerability_type=cand.get("vulnerability_type", "unknown"),
                location=cand.get("location", "unknown"),
                severity=FindingSeverity(cand.get("severity", "MEDIUM")),
                confidence=cand.get("confidence", 0.5),
                probability=cand.get("probability", 0.5),
                status=FindingStatus(cand.get("status", "hypothesis")),
                evidence=cand.get("evidence", []),
                reasoning_chain=cand.get("reasoning_chain", []),
                assumptions=cand.get("assumptions", [])
            )
            sherlock.findings[finding.id] = finding
            sherlock.finding_count += 1
        
        tasks = sherlock.synthesize_hypotheses()
        
        output = [
            {
                "task_id": t.task_id,
                "vulnerability": t.vulnerability,
                "target": t.target,
                "evidence": t.evidence,
                "goal": t.goal,
                "probability": t.probability,
                "assumptions": t.assumptions
            }
            for t in tasks
        ]
        
        with open(args.output, "w") as f:
            json.dump(output, f, indent=2)
        
        sherlock.log(f"Synthesized {len(tasks)} tasks for Moriarty verification.")

    elif args.action == "backward":
        # Backward reasoning analysis (e.g., from an error message)
        with open(args.input_file, 'r') as f:
            data = json.load(f)
        
        effect = data.get("effect", "unknown error")
        analysis = sherlock.reason_backwards(effect)
        
        with open(args.output, "w") as f:
            json.dump(analysis, f, indent=2)

    elif args.action == "stats":
        print(json.dumps(sherlock.get_statistics(), indent=2))


if __name__ == "__main__":
    main()
