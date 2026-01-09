"""
Google Antigravity: The Brain Attic
====================================

"I consider that a man's brain originally is like a little empty attic, 
and you have to stock it with such furniture as you choose. A fool takes 
in all the lumber of every sort that he comes across, so that the knowledge 
which might be useful to him gets crowded out... Now the skillful workman 
is very careful indeed as to what he takes into his brain-attic."
- Sherlock Holmes, A Study in Scarlet

The Brain Attic implements STRATEGIC IGNORANCE:
- Deliberately filtering irrelevant information
- Curating intake to maximize retrieval speed
- Maintaining a "quiet mind" for deep reasoning

This is NOT about having less knowledge - it's about having BETTER knowledge.
Sherlock famously claimed ignorance of the Copernican system because it had
no bearing on his work as a detective.
"""

import re
import hashlib
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Set, Tuple
from enum import Enum


# ==============================================================================
# Relevance Categories
# ==============================================================================

class RelevanceCategory(Enum):
    """Categories for classifying code relevance to security auditing."""
    CRITICAL = "critical"          # Must always observe (transfer, delegatecall)
    HIGH = "high"                  # Very relevant (state changes, access control)
    MEDIUM = "medium"              # Potentially relevant (view functions, events)
    LOW = "low"                    # Rarely relevant (pure math, constants)
    IRRELEVANT = "irrelevant"      # Filter out (tests, mocks, logs)


class FilterAction(Enum):
    """Actions to take on filtered content."""
    ADMIT = "admit"                # Store in Mind Palace
    ADMIT_MINIMAL = "admit_minimal" # Store with reduced metadata
    DEFER = "defer"                # Store for later if context demands
    REJECT = "reject"              # Do not store


@dataclass
class FilteredChunk:
    """A code chunk after Brain Attic filtering."""
    content: str
    relevance: RelevanceCategory
    action: FilterAction
    security_signals: List[str]
    filtered_elements: List[str]
    relevance_score: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RelevanceScore:
    """Detailed relevance scoring for a finding."""
    total_score: float
    category: RelevanceCategory
    action: FilterAction
    signals: List[Tuple[str, float]]  # (signal_name, weight)
    explanation: str


# ==============================================================================
# The Brain Attic
# ==============================================================================

class BrainAttic:
    """
    Strategic Ignorance Engine.
    
    This module implements selective encoding to:
    - Maximize retrieval speed for relevant data
    - Minimize interference from noise
    - Maintain a 'quiet mind' for deep reasoning
    
    Unlike the Mind Palace (which stores what we choose to remember),
    the Brain Attic decides WHAT to remember in the first place.
    """
    
    # ==========================================================================
    # ALWAYS OBSERVE - Critical security patterns (override all filtering)
    # ==========================================================================
    CRITICAL_PATTERNS = {
        # High-risk external interactions
        r"\.call\s*\{": "low_level_call",
        r"\.delegatecall\s*\(": "delegatecall",
        r"\.staticcall\s*\(": "staticcall",
        r"selfdestruct\s*\(": "selfdestruct",
        r"suicide\s*\(": "suicide_deprecated",
        
        # Value transfer
        r"\.transfer\s*\(": "transfer",
        r"\.send\s*\(": "send",
        r"payable\s*\(": "payable_cast",
        
        # Authentication/Authorization
        r"tx\.origin": "tx_origin",
        r"msg\.sender\s*==": "sender_check",
        r"onlyOwner": "owner_modifier",
        r"require\s*\(\s*msg\.sender": "sender_require",
        
        # State manipulation
        r"=\s*address\s*\(0\)": "zero_address_assignment",
        r"delete\s+": "storage_delete",
        
        # Assembly
        r"assembly\s*\{": "inline_assembly",
        r"sstore\s*\(": "assembly_sstore",
        r"sload\s*\(": "assembly_sload",
        
        # External calls
        r"interface\s+I": "interface_definition",
        r"\.safeTransfer": "safe_transfer",
        r"\.safeTransferFrom": "safe_transfer_from",
        
        # Reentrancy indicators
        r"ReentrancyGuard": "reentrancy_guard",
        r"nonReentrant": "nonreentrant_modifier",
        
        # Oracle/Price
        r"getPrice": "price_getter",
        r"latestRoundData": "chainlink_oracle",
        r"getReserves": "amm_reserves",
        
        # Flash loans
        r"flashLoan": "flash_loan",
        r"onFlashLoan": "flash_loan_callback",
    }
    
    # ==========================================================================
    # IRRELEVANT - Patterns to filter out (noise reduction)
    # ==========================================================================
    IRRELEVANT_PATTERNS = {
        # Test artifacts
        r"console\.log": "console_log",
        r"emit\s+Debug": "debug_event",
        r"\/\/\s*TODO": "todo_comment",
        r"\/\/\s*FIXME": "fixme_comment",
        
        # Test imports
        r"import.*Test": "test_import",
        r"import.*Mock": "mock_import",
        r"import.*forge-std": "forge_import",
        
        # Test patterns
        r"function\s+test": "test_function",
        r"function\s+setUp": "setup_function",
        r"vm\.": "foundry_cheat",
        
        # Documentation noise
        r"@dev\s": "natspec_dev",
        r"@param\s": "natspec_param",
        r"@return\s": "natspec_return",
        r"@notice\s": "natspec_notice",
        
        # Common safe patterns
        r"using\s+SafeMath": "safemath_using",
        r"SafeERC20": "safe_erc20",
    }
    
    # ==========================================================================
    # Domain-specific exclusion (the "Copernican" principle)
    # ==========================================================================
    EXCLUDE_DIRECTORIES = {
        "test", "tests", "t",
        "mock", "mocks",
        "script", "scripts",
        "lib", "node_modules",
        "out", "artifacts", "cache",
    }
    
    EXCLUDE_FILES = {
        "Test.sol", "Mock.sol", "Helper.sol",
        "Console.sol", "Vm.sol", "Test.t.sol",
    }
    
    def __init__(self, custom_signals: Optional[Dict[str, float]] = None):
        """
        Initialize the Brain Attic.
        
        Args:
            custom_signals: Additional security signals with weights
        """
        # Compile patterns for efficiency
        self._critical_compiled = {
            re.compile(pattern): name 
            for pattern, name in self.CRITICAL_PATTERNS.items()
        }
        self._irrelevant_compiled = {
            re.compile(pattern): name 
            for pattern, name in self.IRRELEVANT_PATTERNS.items()
        }
        
        # Signal weights (higher = more relevant)
        self.signal_weights = {
            # Critical (1.0)
            "delegatecall": 1.0,
            "selfdestruct": 1.0,
            "tx_origin": 1.0,
            "inline_assembly": 0.9,
            
            # High (0.7-0.9)
            "low_level_call": 0.85,
            "transfer": 0.8,
            "flash_loan": 0.8,
            "chainlink_oracle": 0.75,
            
            # Medium (0.4-0.7)
            "owner_modifier": 0.6,
            "sender_check": 0.55,
            "reentrancy_guard": 0.5,  # Actually indicates safety
            
            # Low (0.1-0.4)
            "interface_definition": 0.3,
            "safe_transfer": 0.2,  # Using safe patterns
            
            # Negative (reduce relevance)
            "console_log": -0.5,
            "test_function": -0.8,
            "mock_import": -0.7,
        }
        
        # Add custom signals
        if custom_signals:
            self.signal_weights.update(custom_signals)
        
        # Statistics
        self.total_filtered = 0
        self.admitted = 0
        self.rejected = 0
        
        print("[Brain Attic] Initialized with strategic ignorance filters")
    
    # --------------------------------------------------------------------------
    # Core Filtering
    # --------------------------------------------------------------------------
    
    def filter(self, code_chunk: str, file_path: Optional[str] = None) -> FilteredChunk:
        """
        Only admit security-relevant patterns to memory.
        
        The filtering process:
        1. Check if file should be excluded entirely
        2. Detect critical patterns (must observe)
        3. Detect irrelevant patterns (should filter)
        4. Calculate overall relevance score
        5. Decide action (admit/defer/reject)
        
        Args:
            code_chunk: The code to filter
            file_path: Optional path for directory-based filtering
        
        Returns:
            FilteredChunk with relevance assessment
        """
        self.total_filtered += 1
        
        # Check file exclusion
        if file_path and self._should_exclude_file(file_path):
            self.rejected += 1
            return FilteredChunk(
                content=code_chunk,
                relevance=RelevanceCategory.IRRELEVANT,
                action=FilterAction.REJECT,
                security_signals=[],
                filtered_elements=["excluded_path"],
                relevance_score=0.0,
                metadata={"excluded_reason": "path_filter"}
            )
        
        # Detect signals
        critical_signals = []
        irrelevant_signals = []
        
        for pattern, name in self._critical_compiled.items():
            if pattern.search(code_chunk):
                critical_signals.append(name)
        
        for pattern, name in self._irrelevant_compiled.items():
            if pattern.search(code_chunk):
                irrelevant_signals.append(name)
        
        # Calculate relevance score
        score = self._calculate_relevance_score(critical_signals, irrelevant_signals)
        
        # Determine category and action
        category, action = self._categorize(score, critical_signals, irrelevant_signals)
        
        if action == FilterAction.ADMIT:
            self.admitted += 1
        elif action == FilterAction.REJECT:
            self.rejected += 1
        
        return FilteredChunk(
            content=code_chunk,
            relevance=category,
            action=action,
            security_signals=critical_signals,
            filtered_elements=irrelevant_signals,
            relevance_score=score,
            metadata={
                "critical_count": len(critical_signals),
                "irrelevant_count": len(irrelevant_signals)
            }
        )
    
    def filter_batch(self, chunks: List[str], file_paths: Optional[List[str]] = None) -> List[FilteredChunk]:
        """Filter a batch of code chunks."""
        if file_paths is None:
            file_paths = [None] * len(chunks)
        
        return [
            self.filter(chunk, path) 
            for chunk, path in zip(chunks, file_paths)
        ]
    
    def curate(self, finding: Dict[str, Any]) -> RelevanceScore:
        """
        Score relevance of a finding to core mission (vulnerability detection).
        
        A finding might be technically true but irrelevant to security
        (e.g., "function could be external instead of public").
        
        Args:
            finding: A security finding dict
        
        Returns:
            RelevanceScore with detailed assessment
        """
        description = finding.get("description", "").lower()
        vuln_type = finding.get("type", "").lower()
        severity = finding.get("severity", "").upper()
        
        signals = []
        
        # Severity scoring
        severity_weight = {
            "CRITICAL": 0.4,
            "HIGH": 0.3,
            "MEDIUM": 0.2,
            "LOW": 0.1,
            "INFORMATIONAL": 0.0,
        }
        severity_score = severity_weight.get(severity, 0.1)
        signals.append(("severity", severity_score))
        
        # Vulnerability type scoring
        high_priority_types = {"reentrancy", "oracle", "flash", "access", "delegatecall"}
        if any(t in vuln_type for t in high_priority_types):
            signals.append(("high_priority_type", 0.3))
        
        # Description signals
        high_risk_terms = {"drain", "steal", "bypass", "manipulate", "flash loan", "arbitrary"}
        if any(term in description for term in high_risk_terms):
            signals.append(("high_risk_description", 0.2))
        
        low_priority_terms = {"gas", "naming", "documentation", "style", "visibility"}
        if any(term in description for term in low_priority_terms):
            signals.append(("low_priority_description", -0.2))
        
        # Calculate total
        total_score = sum(weight for _, weight in signals)
        total_score = max(0.0, min(1.0, total_score))  # Clamp to [0, 1]
        
        # Determine category
        if total_score >= 0.7:
            category = RelevanceCategory.CRITICAL
            action = FilterAction.ADMIT
        elif total_score >= 0.5:
            category = RelevanceCategory.HIGH
            action = FilterAction.ADMIT
        elif total_score >= 0.3:
            category = RelevanceCategory.MEDIUM
            action = FilterAction.ADMIT_MINIMAL
        elif total_score >= 0.1:
            category = RelevanceCategory.LOW
            action = FilterAction.DEFER
        else:
            category = RelevanceCategory.IRRELEVANT
            action = FilterAction.REJECT
        
        explanation = self._generate_explanation(signals, category)
        
        return RelevanceScore(
            total_score=total_score,
            category=category,
            action=action,
            signals=signals,
            explanation=explanation
        )
    
    # --------------------------------------------------------------------------
    # Internal Methods
    # --------------------------------------------------------------------------
    
    def _should_exclude_file(self, file_path: str) -> bool:
        """Check if file should be excluded based on path."""
        path_parts = file_path.lower().replace("\\", "/").split("/")
        
        # Check directory exclusions
        for part in path_parts:
            if part in self.EXCLUDE_DIRECTORIES:
                return True
        
        # Check file exclusions
        file_name = path_parts[-1] if path_parts else ""
        for excluded in self.EXCLUDE_FILES:
            if excluded.lower() in file_name:
                return True
        
        return False
    
    def _calculate_relevance_score(
        self,
        critical_signals: List[str],
        irrelevant_signals: List[str]
    ) -> float:
        """Calculate overall relevance score from signals."""
        score = 0.0
        
        # Add positive signals
        for signal in critical_signals:
            weight = self.signal_weights.get(signal, 0.5)
            score += weight
        
        # Subtract negative signals
        for signal in irrelevant_signals:
            weight = self.signal_weights.get(signal, -0.3)
            score += weight  # These weights are already negative
        
        # If no critical signals, reduce score
        if not critical_signals:
            score *= 0.5
        
        # Normalize to [0, 1]
        return max(0.0, min(1.0, score / 2.0 + 0.5))
    
    def _categorize(
        self,
        score: float,
        critical_signals: List[str],
        irrelevant_signals: List[str]
    ) -> Tuple[RelevanceCategory, FilterAction]:
        """Determine category and action based on score and signals."""
        
        # Critical signals override everything
        high_critical = {"delegatecall", "selfdestruct", "tx_origin", "inline_assembly"}
        if any(s in high_critical for s in critical_signals):
            return RelevanceCategory.CRITICAL, FilterAction.ADMIT
        
        # Pure irrelevant
        if not critical_signals and irrelevant_signals:
            return RelevanceCategory.IRRELEVANT, FilterAction.REJECT
        
        # Score-based categorization
        if score >= 0.8:
            return RelevanceCategory.CRITICAL, FilterAction.ADMIT
        elif score >= 0.6:
            return RelevanceCategory.HIGH, FilterAction.ADMIT
        elif score >= 0.4:
            return RelevanceCategory.MEDIUM, FilterAction.ADMIT_MINIMAL
        elif score >= 0.2:
            return RelevanceCategory.LOW, FilterAction.DEFER
        else:
            return RelevanceCategory.IRRELEVANT, FilterAction.REJECT
    
    def _generate_explanation(
        self,
        signals: List[Tuple[str, float]],
        category: RelevanceCategory
    ) -> str:
        """Generate human-readable explanation of relevance decision."""
        positive = [(s, w) for s, w in signals if w > 0]
        negative = [(s, w) for s, w in signals if w < 0]
        
        parts = []
        
        if positive:
            pos_names = [s for s, _ in positive]
            parts.append(f"Relevant signals: {', '.join(pos_names)}")
        
        if negative:
            neg_names = [s for s, _ in negative]
            parts.append(f"Noise signals: {', '.join(neg_names)}")
        
        parts.append(f"Category: {category.value}")
        
        return ". ".join(parts)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get Brain Attic statistics."""
        return {
            "total_filtered": self.total_filtered,
            "admitted": self.admitted,
            "rejected": self.rejected,
            "admission_rate": self.admitted / max(1, self.total_filtered),
            "rejection_rate": self.rejected / max(1, self.total_filtered)
        }
    
    def add_custom_pattern(
        self,
        pattern: str,
        name: str,
        weight: float,
        critical: bool = True
    ) -> None:
        """Add a custom pattern for filtering."""
        compiled = re.compile(pattern)
        
        if critical:
            self._critical_compiled[compiled] = name
        else:
            self._irrelevant_compiled[compiled] = name
        
        self.signal_weights[name] = weight
        
        print(f"[Brain Attic] Added custom pattern: {name} (weight: {weight})")


# ==============================================================================
# The Quiet Mind State
# ==============================================================================

class QuietMind:
    """
    The optimal cognitive state for deep reasoning.
    
    "The most powerful mind is the quiet mind... the mind that is 
    present, reflective, mindful of its thoughts and its state."
    - Maria Konnikova
    
    This class helps maintain focus by tracking cognitive load
    and providing mechanisms to reduce noise.
    """
    
    def __init__(self, attic: BrainAttic, max_active_contexts: int = 5):
        """
        Initialize the Quiet Mind.
        
        Args:
            attic: The Brain Attic for filtering
            max_active_contexts: Maximum concurrent contexts to maintain
        """
        self.attic = attic
        self.max_active_contexts = max_active_contexts
        
        self.active_contexts: List[Dict[str, Any]] = []
        self.cognitive_load = 0.0
        
    def enter_focus(self, context: Dict[str, Any]) -> bool:
        """
        Enter focused state on a specific context.
        
        Returns False if cognitive load is too high.
        """
        if len(self.active_contexts) >= self.max_active_contexts:
            # Find least relevant context to evict
            self._evict_least_relevant()
        
        self.active_contexts.append(context)
        self._update_cognitive_load()
        
        return True
    
    def exit_focus(self, context_id: str) -> None:
        """Exit focused state on a context."""
        self.active_contexts = [
            c for c in self.active_contexts 
            if c.get("id") != context_id
        ]
        self._update_cognitive_load()
    
    def is_overloaded(self) -> bool:
        """Check if cognitive load is too high for new tasks."""
        return self.cognitive_load > 0.8
    
    def _evict_least_relevant(self) -> None:
        """Evict the least relevant active context."""
        if not self.active_contexts:
            return
        
        # Find lowest priority context
        min_priority = min(
            c.get("priority", 0.5) 
            for c in self.active_contexts
        )
        
        self.active_contexts = [
            c for c in self.active_contexts 
            if c.get("priority", 0.5) > min_priority
        ][:self.max_active_contexts - 1]
    
    def _update_cognitive_load(self) -> None:
        """Update cognitive load based on active contexts."""
        if not self.active_contexts:
            self.cognitive_load = 0.0
            return
        
        # Sum of context complexities
        total_complexity = sum(
            c.get("complexity", 0.2) 
            for c in self.active_contexts
        )
        
        self.cognitive_load = min(1.0, total_complexity)


# ==============================================================================
# CLI Interface
# ==============================================================================

if __name__ == "__main__":
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description="Brain Attic - Strategic Ignorance")
    parser.add_argument("--action", choices=["filter", "curate", "stats"], default="stats")
    parser.add_argument("--input", type=str, help="Input code or finding")
    parser.add_argument("--file", type=str, help="File path for context")
    args = parser.parse_args()
    
    attic = BrainAttic()
    
    if args.action == "filter" and args.input:
        result = attic.filter(args.input, args.file)
        print(f"Relevance: {result.relevance.value}")
        print(f"Action: {result.action.value}")
        print(f"Score: {result.relevance_score:.2f}")
        print(f"Security Signals: {result.security_signals}")
        print(f"Filtered: {result.filtered_elements}")
    
    elif args.action == "curate" and args.input:
        finding = json.loads(args.input)
        result = attic.curate(finding)
        print(f"Score: {result.total_score:.2f}")
        print(f"Category: {result.category.value}")
        print(f"Action: {result.action.value}")
        print(f"Explanation: {result.explanation}")
    
    elif args.action == "stats":
        print(json.dumps(attic.get_statistics(), indent=2))
