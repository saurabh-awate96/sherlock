"""
Google Antigravity: The Bayesian Engine
========================================

"The superiority of the Holmes brothers over other high-IQ individuals lies 
in their capacity for rapid Bayesian updating. While a standard detective 
might hold onto a theory until it is disproven, Sherlock's mind operates 
as a high-speed Bayesian processor, constantly adjusting the likelihood 
of a conclusion in real-time."

This module implements:
1. Prior probability setting based on pattern matching
2. Evidence-driven probability updates (Bayes' theorem)
3. Hypothesis comparison and ranking
4. Occam's Razor penalty for complex explanations
"""

import math
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
from enum import Enum


# ==============================================================================
# Core Data Structures
# ==============================================================================

class EvidenceType(Enum):
    """Types of evidence that can update hypotheses."""
    STATIC_ANALYSIS = "static_analysis"      # Slither, Aderyn findings
    PATTERN_MATCH = "pattern_match"          # RAG retrieval match
    HISTORICAL_EXPLOIT = "historical_exploit" # Similar past exploit
    CODE_STRUCTURE = "code_structure"        # AST-level pattern
    FUZZING_RESULT = "fuzzing_result"        # Echidna/Medusa result
    EXPLOIT_VERIFIED = "exploit_verified"    # Moriarty confirmed
    EXPLOIT_FAILED = "exploit_failed"        # Moriarty couldn't exploit
    SAFE_PATTERN = "safe_pattern"            # Known safe pattern match
    MODIFIER_PRESENT = "modifier_present"    # Safety modifier detected
    MANUAL_REVIEW = "manual_review"          # Human analyst input


class HypothesisStatus(Enum):
    """Status of a hypothesis in the reasoning process."""
    ACTIVE = "active"              # Currently being evaluated
    PROBABLE = "probable"          # High probability, pending verification
    VERIFIED = "verified"          # Confirmed by exploit
    REFUTED = "refuted"            # Disproven by evidence
    DORMANT = "dormant"            # Low probability, deprioritized


@dataclass
class Evidence:
    """A piece of evidence that affects hypothesis probability."""
    id: str
    evidence_type: EvidenceType
    description: str
    source: str                    # Where this evidence came from
    strength: float               # How strongly it affects probability [0, 1]
    supports_hypothesis: bool     # True = supports, False = contradicts
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Hypothesis:
    """
    A hypothesis about a potential vulnerability.
    
    This is the "baton" that Sherlock passes to Moriarty,
    but now enriched with probabilistic reasoning.
    """
    id: str
    name: str
    description: str
    vulnerability_type: str
    location: str                 # File:Line or contract/function
    
    # Probability tracking
    prior_probability: float      # Initial belief before evidence
    current_probability: float    # Updated belief after evidence
    confidence: float             # How confident we are in our probability
    
    # Evidence chain
    evidence_chain: List[Evidence] = field(default_factory=list)
    
    # Reasoning metadata
    complexity_penalty: float = 0.0  # Occam's Razor penalty
    assumptions: List[str] = field(default_factory=list)
    
    # Status
    status: HypothesisStatus = HypothesisStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class UpdateResult:
    """Result of a probability update."""
    hypothesis_id: str
    previous_probability: float
    new_probability: float
    evidence_applied: Evidence
    delta: float
    reasoning: str


# ==============================================================================
# The Bayesian Reasoner
# ==============================================================================

class BayesianReasoner:
    """
    The engine that allows 'rapid-fire hypothesis generation and refinement'.
    
    When Sherlock meets a client, he begins with a 'prior probability'.
    As he observes details—mud on a shoe, a callus on a finger—he 
    UPDATES the probability of his hypothesis in real-time.
    
    This implements:
    - Bayes' theorem for probability updates
    - Likelihood ratios for evidence strength
    - Occam's Razor for hypothesis simplicity
    - Parallel hypothesis tracking
    """
    
    # Default prior probabilities for common vulnerability types
    DEFAULT_PRIORS = {
        "reentrancy": 0.15,
        "read_only_reentrancy": 0.10,
        "oracle_manipulation": 0.20,
        "flash_loan_attack": 0.15,
        "access_control": 0.25,
        "arithmetic_overflow": 0.05,  # Low in Solidity 0.8+
        "front_running": 0.20,
        "timestamp_dependence": 0.10,
        "governance_attack": 0.12,
        "liquidation_bug": 0.15,
        "cross_contract": 0.18,
        "storage_collision": 0.08,
        "unchecked_return": 0.15,
        "denial_of_service": 0.12,
    }
    
    # Evidence type base strengths (how much they influence probability)
    EVIDENCE_WEIGHTS = {
        EvidenceType.STATIC_ANALYSIS: 0.15,
        EvidenceType.PATTERN_MATCH: 0.25,
        EvidenceType.HISTORICAL_EXPLOIT: 0.35,
        EvidenceType.CODE_STRUCTURE: 0.20,
        EvidenceType.FUZZING_RESULT: 0.40,
        EvidenceType.EXPLOIT_VERIFIED: 0.90,
        EvidenceType.EXPLOIT_FAILED: 0.50,  # Absence of exploit is evidence
        EvidenceType.SAFE_PATTERN: 0.30,
        EvidenceType.MODIFIER_PRESENT: 0.25,
        EvidenceType.MANUAL_REVIEW: 0.45,
    }
    
    def __init__(
        self,
        complexity_penalty_weight: float = 0.05,
        pursuit_threshold: float = 0.20,
        max_hypotheses: int = 10
    ):
        """
        Initialize the Bayesian Reasoner.
        
        Args:
            complexity_penalty_weight: How much to penalize complex hypotheses
            pursuit_threshold: Minimum probability to pursue a hypothesis
            max_hypotheses: Maximum concurrent hypotheses to track
        """
        self.complexity_penalty_weight = complexity_penalty_weight
        self.pursuit_threshold = pursuit_threshold
        self.max_hypotheses = max_hypotheses
        
        # Active hypotheses
        self.hypotheses: Dict[str, Hypothesis] = {}
        
        # Update history
        self.update_history: List[UpdateResult] = []
        
        print(f"[Bayesian Engine] Initialized with pursuit threshold {pursuit_threshold}")
    
    # --------------------------------------------------------------------------
    # Hypothesis Management
    # --------------------------------------------------------------------------
    
    def create_hypothesis(
        self,
        name: str,
        description: str,
        vulnerability_type: str,
        location: str,
        prior: Optional[float] = None,
        assumptions: Optional[List[str]] = None
    ) -> Hypothesis:
        """
        Create a new hypothesis with initial prior probability.
        
        The prior is set based on:
        1. Base rate for this vulnerability type
        2. Adjusted by the number of assumptions required
        
        Args:
            name: Short name for the hypothesis
            description: Detailed description
            vulnerability_type: Type of vulnerability
            location: Where in the code
            prior: Custom prior (optional)
            assumptions: Assumptions this hypothesis requires
        
        Returns:
            The created Hypothesis
        """
        # Generate ID
        hypothesis_id = f"hyp_{len(self.hypotheses)}_{vulnerability_type[:8]}"
        
        # Get prior
        if prior is None:
            prior = self.DEFAULT_PRIORS.get(
                vulnerability_type.lower().replace(" ", "_"),
                0.15  # Default moderate prior
            )
        
        # Calculate complexity penalty based on assumptions
        assumptions = assumptions or []
        complexity_penalty = len(assumptions) * self.complexity_penalty_weight
        
        # Apply Occam's Razor - simpler explanations preferred
        adjusted_prior = prior * (1 - complexity_penalty)
        
        hypothesis = Hypothesis(
            id=hypothesis_id,
            name=name,
            description=description,
            vulnerability_type=vulnerability_type,
            location=location,
            prior_probability=prior,
            current_probability=adjusted_prior,
            confidence=0.3,  # Low initial confidence
            complexity_penalty=complexity_penalty,
            assumptions=assumptions
        )
        
        self.hypotheses[hypothesis_id] = hypothesis
        
        print(f"[Bayesian Engine] Created hypothesis: {name}")
        print(f"  Prior: {prior:.2f}, Adjusted: {adjusted_prior:.2f} (complexity penalty: {complexity_penalty:.2f})")
        
        return hypothesis
    
    def set_prior(self, hypothesis_id: str, probability: float) -> None:
        """Set or update the prior probability for a hypothesis."""
        if hypothesis_id in self.hypotheses:
            hyp = self.hypotheses[hypothesis_id]
            hyp.prior_probability = probability
            hyp.current_probability = probability * (1 - hyp.complexity_penalty)
            hyp.last_updated = datetime.now()
            print(f"[Bayesian Engine] Updated prior for {hypothesis_id}: {probability:.2f}")
    
    # --------------------------------------------------------------------------
    # Evidence Application (Bayesian Updating)
    # --------------------------------------------------------------------------
    
    def update(
        self,
        hypothesis_id: str,
        evidence: Evidence
    ) -> UpdateResult:
        """
        Apply Bayes' theorem to update probability.
        
        P(H|E) = P(E|H) * P(H) / P(E)
        
        In practice, we use likelihood ratios:
        - P(E|H) / P(E|¬H) for supporting evidence
        - P(E|¬H) / P(E|H) for contradicting evidence
        
        Args:
            hypothesis_id: ID of hypothesis to update
            evidence: The new evidence
        
        Returns:
            UpdateResult detailing the change
        """
        if hypothesis_id not in self.hypotheses:
            raise ValueError(f"Unknown hypothesis: {hypothesis_id}")
        
        hyp = self.hypotheses[hypothesis_id]
        previous_prob = hyp.current_probability
        
        # Get base strength for this evidence type
        base_strength = self.EVIDENCE_WEIGHTS.get(evidence.evidence_type, 0.15)
        
        # Combine with evidence-specific strength
        likelihood_strength = base_strength * evidence.strength
        
        # Calculate likelihood ratio
        if evidence.supports_hypothesis:
            # Supporting evidence increases probability
            likelihood_ratio = 1 + likelihood_strength
        else:
            # Contradicting evidence decreases probability
            likelihood_ratio = 1 / (1 + likelihood_strength)
        
        # Apply Bayes' update
        # Using odds form: O(H|E) = O(H) * LR
        prior_odds = previous_prob / (1 - previous_prob + 1e-10)
        posterior_odds = prior_odds * likelihood_ratio
        new_prob = posterior_odds / (1 + posterior_odds)
        
        # Clamp to reasonable bounds
        new_prob = max(0.01, min(0.99, new_prob))
        
        # Update hypothesis
        hyp.current_probability = new_prob
        hyp.evidence_chain.append(evidence)
        hyp.last_updated = datetime.now()
        
        # Update confidence based on evidence quantity
        evidence_count = len(hyp.evidence_chain)
        hyp.confidence = min(0.95, 0.3 + (evidence_count * 0.1))
        
        # Update status
        self._update_status(hyp)
        
        # Create result
        delta = new_prob - previous_prob
        reasoning = self._generate_reasoning(evidence, previous_prob, new_prob)
        
        result = UpdateResult(
            hypothesis_id=hypothesis_id,
            previous_probability=previous_prob,
            new_probability=new_prob,
            evidence_applied=evidence,
            delta=delta,
            reasoning=reasoning
        )
        
        self.update_history.append(result)
        
        print(f"[Bayesian Engine] Updated {hyp.name}: {previous_prob:.2f} → {new_prob:.2f} ({delta:+.2f})")
        
        return result
    
    def update_with_finding(
        self,
        hypothesis_id: str,
        finding: Dict[str, Any],
        evidence_type: EvidenceType = EvidenceType.STATIC_ANALYSIS
    ) -> UpdateResult:
        """
        Convenience method to update from a raw finding dict.
        
        Args:
            hypothesis_id: ID of hypothesis
            finding: Raw finding from static analyzer
            evidence_type: Type of evidence
        
        Returns:
            UpdateResult
        """
        # Determine support/contradiction
        severity = finding.get("severity", "").upper()
        confidence = finding.get("confidence", "").upper()
        
        # High severity/confidence supports the hypothesis
        severity_map = {"CRITICAL": 0.9, "HIGH": 0.7, "MEDIUM": 0.5, "LOW": 0.3, "INFO": 0.1}
        strength = severity_map.get(severity, 0.5)
        
        # Create evidence
        evidence = Evidence(
            id=f"ev_{len(self.update_history)}",
            evidence_type=evidence_type,
            description=finding.get("description", "Static analysis finding"),
            source=finding.get("detector", "unknown"),
            strength=strength,
            supports_hypothesis=True,  # Static findings support vulnerability hypothesis
            metadata=finding
        )
        
        return self.update(hypothesis_id, evidence)
    
    def apply_rag_match(
        self,
        hypothesis_id: str,
        match_score: float,
        match_description: str,
        is_historical_exploit: bool = False
    ) -> UpdateResult:
        """
        Apply RAG retrieval match as evidence.
        
        When the Vector DB returns a high-similarity match to a known exploit,
        this strongly increases the confidence score.
        
        Args:
            hypothesis_id: ID of hypothesis
            match_score: Similarity score from RAG [0, 1]
            match_description: Description of the matched pattern
            is_historical_exploit: Whether match is a real historical exploit
        
        Returns:
            UpdateResult
        """
        evidence_type = (
            EvidenceType.HISTORICAL_EXPLOIT if is_historical_exploit 
            else EvidenceType.PATTERN_MATCH
        )
        
        evidence = Evidence(
            id=f"rag_{len(self.update_history)}",
            evidence_type=evidence_type,
            description=f"RAG match: {match_description}",
            source="mind_palace",
            strength=match_score,
            supports_hypothesis=True,
            metadata={"match_score": match_score}
        )
        
        return self.update(hypothesis_id, evidence)
    
    def apply_exploit_result(
        self,
        hypothesis_id: str,
        success: bool,
        exploit_details: str
    ) -> UpdateResult:
        """
        Apply exploit verification result as evidence.
        
        If Moriarty successfully generated a PoC that worked,
        this is near-certain proof.
        
        Args:
            hypothesis_id: ID of hypothesis
            success: Whether exploit succeeded
            exploit_details: Details of the exploit attempt
        
        Returns:
            UpdateResult
        """
        evidence_type = (
            EvidenceType.EXPLOIT_VERIFIED if success 
            else EvidenceType.EXPLOIT_FAILED
        )
        
        evidence = Evidence(
            id=f"exploit_{len(self.update_history)}",
            evidence_type=evidence_type,
            description=exploit_details,
            source="moriarty",
            strength=0.95 if success else 0.60,
            supports_hypothesis=success,
            metadata={"exploit_success": success}
        )
        
        return self.update(hypothesis_id, evidence)
    
    def apply_safe_pattern(
        self,
        hypothesis_id: str,
        pattern_name: str,
        pattern_description: str
    ) -> UpdateResult:
        """
        Apply safe pattern detection as contradicting evidence.
        
        If the code follows a known safe pattern (e.g., CEI, ReentrancyGuard),
        this reduces the probability of vulnerability.
        
        Args:
            hypothesis_id: ID of hypothesis
            pattern_name: Name of the safe pattern
            pattern_description: Description
        
        Returns:
            UpdateResult
        """
        evidence = Evidence(
            id=f"safe_{len(self.update_history)}",
            evidence_type=EvidenceType.SAFE_PATTERN,
            description=f"Safe pattern: {pattern_name} - {pattern_description}",
            source="code_analysis",
            strength=0.7,
            supports_hypothesis=False,  # Contradicts vulnerability hypothesis
            metadata={"pattern": pattern_name}
        )
        
        return self.update(hypothesis_id, evidence)
    
    # --------------------------------------------------------------------------
    # Hypothesis Ranking and Selection
    # --------------------------------------------------------------------------
    
    def get_posterior(self, hypothesis_id: str) -> float:
        """Get current probability after all updates."""
        if hypothesis_id not in self.hypotheses:
            return 0.0
        return self.hypotheses[hypothesis_id].current_probability
    
    def rank_hypotheses(self) -> List[Tuple[str, float, float]]:
        """
        Rank competing hypotheses by probability.
        
        Returns list of (hypothesis_id, probability, confidence) tuples,
        sorted by probability * confidence.
        """
        rankings = []
        
        for hyp_id, hyp in self.hypotheses.items():
            if hyp.status != HypothesisStatus.REFUTED:
                # Combined score = probability * confidence
                combined = hyp.current_probability * hyp.confidence
                rankings.append((hyp_id, hyp.current_probability, hyp.confidence, combined))
        
        # Sort by combined score
        rankings.sort(key=lambda x: x[3], reverse=True)
        
        return [(r[0], r[1], r[2]) for r in rankings]
    
    def get_active_hypotheses(self) -> List[Hypothesis]:
        """Get all hypotheses above pursuit threshold."""
        return [
            hyp for hyp in self.hypotheses.values()
            if hyp.current_probability >= self.pursuit_threshold
            and hyp.status == HypothesisStatus.ACTIVE
        ]
    
    def get_probable_hypotheses(self) -> List[Hypothesis]:
        """Get hypotheses with high probability (> 0.6)."""
        return [
            hyp for hyp in self.hypotheses.values()
            if hyp.current_probability >= 0.6
            and hyp.status in [HypothesisStatus.ACTIVE, HypothesisStatus.PROBABLE]
        ]
    
    def get_verified_hypotheses(self) -> List[Hypothesis]:
        """Get hypotheses verified by exploit."""
        return [
            hyp for hyp in self.hypotheses.values()
            if hyp.status == HypothesisStatus.VERIFIED
        ]
    
    # --------------------------------------------------------------------------
    # Internal Methods
    # --------------------------------------------------------------------------
    
    def _update_status(self, hyp: Hypothesis) -> None:
        """Update hypothesis status based on probability."""
        prob = hyp.current_probability
        
        # Check for exploitation evidence
        has_exploit_verified = any(
            e.evidence_type == EvidenceType.EXPLOIT_VERIFIED 
            for e in hyp.evidence_chain
        )
        
        has_exploit_failed = any(
            e.evidence_type == EvidenceType.EXPLOIT_FAILED 
            for e in hyp.evidence_chain
        )
        
        if has_exploit_verified:
            hyp.status = HypothesisStatus.VERIFIED
        elif prob > 0.7:
            hyp.status = HypothesisStatus.PROBABLE
        elif prob < 0.1:
            hyp.status = HypothesisStatus.REFUTED
        elif prob < self.pursuit_threshold:
            hyp.status = HypothesisStatus.DORMANT
        else:
            hyp.status = HypothesisStatus.ACTIVE
    
    def _generate_reasoning(
        self,
        evidence: Evidence,
        prev_prob: float,
        new_prob: float
    ) -> str:
        """Generate explanation of the probability update."""
        direction = "increased" if new_prob > prev_prob else "decreased"
        support = "supporting" if evidence.supports_hypothesis else "contradicting"
        
        return (
            f"{evidence.evidence_type.value} evidence {support} the hypothesis. "
            f"Probability {direction} from {prev_prob:.1%} to {new_prob:.1%}. "
            f"Source: {evidence.source}"
        )
    
    def get_evidence_chain(self, hypothesis_id: str) -> List[Dict[str, Any]]:
        """Get the evidence chain for a hypothesis as JSON-serializable dict."""
        if hypothesis_id not in self.hypotheses:
            return []
        
        hyp = self.hypotheses[hypothesis_id]
        return [
            {
                "id": e.id,
                "type": e.evidence_type.value,
                "description": e.description,
                "strength": e.strength,
                "supports": e.supports_hypothesis,
                "source": e.source
            }
            for e in hyp.evidence_chain
        ]
    
    def export_hypothesis(self, hypothesis_id: str) -> Dict[str, Any]:
        """Export a hypothesis to JSON-serializable dict."""
        if hypothesis_id not in self.hypotheses:
            return {}
        
        hyp = self.hypotheses[hypothesis_id]
        return {
            "id": hyp.id,
            "name": hyp.name,
            "description": hyp.description,
            "vulnerability_type": hyp.vulnerability_type,
            "location": hyp.location,
            "prior_probability": hyp.prior_probability,
            "current_probability": hyp.current_probability,
            "confidence": hyp.confidence,
            "status": hyp.status.value,
            "complexity_penalty": hyp.complexity_penalty,
            "assumptions": hyp.assumptions,
            "evidence_count": len(hyp.evidence_chain),
            "evidence_chain": self.get_evidence_chain(hypothesis_id)
        }
    
    def export_all_hypotheses(self) -> List[Dict[str, Any]]:
        """Export all hypotheses."""
        return [
            self.export_hypothesis(hyp_id) 
            for hyp_id in self.hypotheses
        ]


# ==============================================================================
# Occam's Razor Helper
# ==============================================================================

class OccamsRazor:
    """
    "The simplest explanation is usually the correct one."
    
    This helper applies complexity penalties to hypotheses
    based on the number of assumptions required.
    """
    
    @staticmethod
    def calculate_penalty(
        assumptions: List[str],
        base_penalty: float = 0.05
    ) -> float:
        """
        Calculate complexity penalty.
        
        Each assumption adds to the penalty, with
        diminishing returns for additional assumptions.
        """
        if not assumptions:
            return 0.0
        
        # Logarithmic scaling - first assumptions penalize more
        penalty = 0.0
        for i, _ in enumerate(assumptions):
            penalty += base_penalty / (1 + i * 0.5)
        
        return min(0.5, penalty)  # Cap at 50% penalty
    
    @staticmethod
    def compare_hypotheses(
        hyp1: Hypothesis,
        hyp2: Hypothesis
    ) -> Hypothesis:
        """
        Compare two hypotheses and return the simpler one
        (adjusted for probability).
        
        Even if hyp1 has slightly higher probability,
        prefer hyp2 if it's significantly simpler.
        """
        # Adjusted probabilities (accounting for complexity)
        adj1 = hyp1.current_probability * (1 - hyp1.complexity_penalty)
        adj2 = hyp2.current_probability * (1 - hyp2.complexity_penalty)
        
        return hyp1 if adj1 >= adj2 else hyp2


# ==============================================================================
# CLI Interface
# ==============================================================================

if __name__ == "__main__":
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description="Bayesian Engine - Probabilistic Reasoning")
    parser.add_argument("--action", choices=["create", "update", "rank", "export"], default="rank")
    parser.add_argument("--hypothesis", type=str, help="Hypothesis ID")
    parser.add_argument("--evidence", type=str, help="JSON evidence")
    args = parser.parse_args()
    
    engine = BayesianReasoner()
    
    # Demo: Create some hypotheses
    hyp1 = engine.create_hypothesis(
        name="Reentrancy in withdraw()",
        description="External call before state update in withdraw function",
        vulnerability_type="reentrancy",
        location="VulnerableBank.sol:45",
        assumptions=["Attacker can receive ETH", "Fallback function exists"]
    )
    
    hyp2 = engine.create_hypothesis(
        name="Oracle Manipulation",
        description="Using spot price from AMM reserves",
        vulnerability_type="oracle_manipulation",
        location="PriceOracle.sol:22"
    )
    
    if args.action == "rank":
        rankings = engine.rank_hypotheses()
        print("\nHypothesis Rankings:")
        for hyp_id, prob, conf in rankings:
            hyp = engine.hypotheses[hyp_id]
            print(f"  {hyp.name}: P={prob:.2f}, C={conf:.2f}, Status={hyp.status.value}")
    
    elif args.action == "export":
        export = engine.export_all_hypotheses()
        print(json.dumps(export, indent=2))
