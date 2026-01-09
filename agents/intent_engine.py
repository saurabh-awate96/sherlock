"""
Universal Orchestrator: Intent Recognition Engine
==================================================

Vector Space Intent Classification with Dynamic Discovery.

"Hard-coded keywords (e.g., if command == 'scan') are brittle. 
The IRE replaces this with Semantic Vector Mapping."

This module implements:
- Vector Space Intent Classification: LLM embeddings → cluster mapping
- Dynamic Intent Discovery: Self-expansion for unknown intents
- Semantic Routing: Natural language → capabilities mapping
"""

import hashlib
import math
import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple, Set
from datetime import datetime
from enum import Enum


# ==============================================================================
# Data Structures
# ==============================================================================

class IntentCategory(Enum):
    """Pre-defined intent categories."""
    RECONNAISSANCE = "reconnaissance"
    VULNERABILITY_ASSESSMENT = "vulnerability_assessment"
    EXPLOITATION = "exploitation"
    POST_EXPLOITATION = "post_exploitation"
    HARDENING = "hardening"
    REPORTING = "reporting"
    DISCOVERY = "discovery"
    ANALYSIS = "analysis"
    UNKNOWN = "unknown"


@dataclass
class IntentClassification:
    """Result of intent classification."""
    intent: IntentCategory
    confidence: float
    intent_tags: List[str]
    original_query: str
    
    # Sub-intents detected
    sub_intents: List[str] = field(default_factory=list)
    
    # For dynamic discovery
    is_new_intent: bool = False
    suggested_category: Optional[str] = None


@dataclass
class IntentCluster:
    """A cluster of related intents in vector space."""
    name: str
    category: IntentCategory
    keywords: List[str]
    centroid: List[float]
    examples: List[str]
    
    # Dynamic expansion
    learned_phrases: List[str] = field(default_factory=list)
    
    def add_phrase(self, phrase: str):
        """Add a learned phrase to expand the cluster."""
        if phrase not in self.learned_phrases:
            self.learned_phrases.append(phrase)


@dataclass
class IntentVector:
    """Vector representation of a phrase."""
    phrase: str
    vector: List[float]
    magnitude: float


# ==============================================================================
# Intent Recognition Engine
# ==============================================================================

class IntentRecognitionEngine:
    """
    Maps natural language to intent clusters via vector embeddings.
    
    The "Universal" aspect requires the system to understand requests
    without rigid terminology. This engine uses semantic similarity
    to classify intents, with the ability to discover new intent
    categories dynamically.
    """
    
    # Confidence threshold for reliable classification
    CONFIDENCE_THRESHOLD = 0.35
    
    # Pre-defined intent clusters (expandable at runtime)
    INTENT_CLUSTERS = {
        IntentCategory.RECONNAISSANCE: {
            "keywords": [
                "scan", "discover", "map", "enumerate", "find", "identify",
                "probe", "detect", "explore", "reconnoiter", "survey",
                "inventory", "catalog", "list", "observe", "monitor",
                "research", "deep", "investigate", "study"
            ],
            "examples": [
                "scan the network for open ports",
                "discover all subdomains",
                "map the attack surface",
                "enumerate running services",
                "find exposed endpoints"
            ]
        },
        IntentCategory.VULNERABILITY_ASSESSMENT: {
            "keywords": [
                "assess", "check", "test", "verify", "validate", "analyze",
                "audit", "examine", "review", "evaluate", "inspect",
                "vulnerable", "vulnerability", "weakness", "flaw"
            ],
            "examples": [
                "check for SQL injection vulnerabilities",
                "assess the security posture",
                "test authentication mechanisms",
                "verify input validation",
                "analyze for common weaknesses"
            ]
        },
        IntentCategory.EXPLOITATION: {
            "keywords": [
                "exploit", "attack", "compromise", "breach", "penetrate",
                "pwn", "hack", "bypass", "circumvent", "break",
                "leverage", "abuse", "weaponize"
            ],
            "examples": [
                "exploit the reentrancy vulnerability",
                "attack the oracle mechanism",
                "compromise the access control",
                "bypass the authentication",
                "leverage the flash loan for extraction"
            ]
        },
        IntentCategory.POST_EXPLOITATION: {
            "keywords": [
                "persist", "maintain", "escalate", "pivot", "lateral",
                "exfiltrate", "extract", "dump", "harvest", "collect"
            ],
            "examples": [
                "maintain persistent access",
                "escalate privileges",
                "pivot to internal network",
                "exfiltrate sensitive data"
            ]
        },
        IntentCategory.HARDENING: {
            "keywords": [
                "fix", "patch", "harden", "remediate", "secure", "protect",
                "mitigate", "resolve", "repair", "strengthen", "fortify",
                "upgrade", "update", "configure"
            ],
            "examples": [
                "fix the reentrancy bug",
                "patch the vulnerable function",
                "harden the authentication",
                "remediate the access control issue",
                "secure the oracle feed"
            ]
        },
        IntentCategory.REPORTING: {
            "keywords": [
                "report", "summarize", "document", "describe", "explain",
                "generate", "create", "compile", "produce", "write",
                "format", "export", "output"
            ],
            "examples": [
                "generate a security report",
                "summarize the findings",
                "document all vulnerabilities",
                "create an audit trail",
                "compile the assessment results"
            ]
        },
        IntentCategory.DISCOVERY: {
            "keywords": [
                "discover", "uncover", "reveal", "expose", "find",
                "locate", "trace", "track", "follow", "investigate"
            ],
            "examples": [
                "discover hidden functionality",
                "uncover admin endpoints",
                "reveal debug interfaces",
                "expose internal APIs"
            ]
        },
        IntentCategory.ANALYSIS: {
            "keywords": [
                "analyze", "understand", "interpret", "decode", "parse",
                "examine", "study", "investigate", "research", "review",
                "reverse", "decompile", "disassemble"
            ],
            "examples": [
                "analyze the smart contract logic",
                "understand the token flow",
                "interpret the bytecode",
                "examine the state transitions",
                "reverse engineer the protocol"
            ]
        }
    }
    
    # Vector dimension (simplified hash-based)
    VECTOR_DIM = 128
    
    def __init__(self):
        """Initialize the Intent Recognition Engine."""
        self.clusters: Dict[IntentCategory, IntentCluster] = {}
        self.dynamic_clusters: Dict[str, IntentCluster] = {}
        self.classification_history: List[IntentClassification] = []
        
        # Initialize clusters
        self._initialize_clusters()
        
        print("[IntentEngine] Initialized with semantic intent classification")
    
    def _initialize_clusters(self):
        """Initialize intent clusters with centroids."""
        for category, data in self.INTENT_CLUSTERS.items():
            keywords = data["keywords"]
            examples = data["examples"]
            
            # Compute centroid as average of keyword vectors
            vectors = [self._embed(kw) for kw in keywords]
            centroid = self._compute_centroid(vectors)
            
            self.clusters[category] = IntentCluster(
                name=category.value,
                category=category,
                keywords=keywords,
                centroid=centroid,
                examples=examples
            )
    
    # --------------------------------------------------------------------------
    # Vector Operations
    # --------------------------------------------------------------------------
    
    def _embed(self, text: str) -> List[float]:
        """
        Create vector embedding for text.
        
        This uses a hash-based approach for deterministic, 
        dependency-free operation. In production, replace with
        real LLM embeddings (text-embedding-3-large, etc.)
        """
        # Normalize text
        text = text.lower().strip()
        
        # Generate hash-based vector
        vector = [0.0] * self.VECTOR_DIM
        
        # Word-level hashing
        words = re.findall(r'\w+', text)
        for word in words:
            hash_bytes = hashlib.sha256(word.encode()).digest()
            for i in range(min(len(hash_bytes), self.VECTOR_DIM)):
                # Convert byte to float in [-1, 1]
                vector[i] += (hash_bytes[i] / 127.5) - 1.0
        
        # Normalize
        magnitude = math.sqrt(sum(v * v for v in vector))
        if magnitude > 0:
            vector = [v / magnitude for v in vector]
        
        return vector
    
    def _compute_centroid(self, vectors: List[List[float]]) -> List[float]:
        """Compute centroid (average) of vectors."""
        if not vectors:
            return [0.0] * self.VECTOR_DIM
        
        centroid = [0.0] * self.VECTOR_DIM
        for vec in vectors:
            for i, v in enumerate(vec):
                centroid[i] += v
        
        n = len(vectors)
        centroid = [c / n for c in centroid]
        
        # Normalize
        magnitude = math.sqrt(sum(c * c for c in centroid))
        if magnitude > 0:
            centroid = [c / magnitude for c in centroid]
        
        return centroid
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        mag1 = math.sqrt(sum(a * a for a in vec1))
        mag2 = math.sqrt(sum(b * b for b in vec2))
        
        if mag1 == 0 or mag2 == 0:
            return 0.0
        
        return dot_product / (mag1 * mag2)
    
    # --------------------------------------------------------------------------
    # Intent Classification
    # --------------------------------------------------------------------------
    
    def classify(self, query: str) -> IntentClassification:
        """
        Classify a natural language query into an intent.
        
        Uses vector similarity to map query to closest cluster.
        If confidence is below threshold, triggers dynamic discovery.
        
        Args:
            query: Natural language query/command
        
        Returns:
            IntentClassification with category and confidence
        """
        # Embed query
        query_vector = self._embed(query)
        
        # Compare against all cluster centroids
        similarities: Dict[IntentCategory, float] = {}
        for category, cluster in self.clusters.items():
            similarity = self._cosine_similarity(query_vector, cluster.centroid)
            similarities[category] = max(0, (similarity + 1) / 2)  # Normalize to [0, 1]
        
        # Also check dynamic clusters
        dynamic_similarities: Dict[str, float] = {}
        for name, cluster in self.dynamic_clusters.items():
            similarity = self._cosine_similarity(query_vector, cluster.centroid)
            dynamic_similarities[name] = max(0, (similarity + 1) / 2)
        
        # Find best match
        best_category = max(similarities, key=similarities.get)
        best_confidence = similarities[best_category]
        
        # Check if dynamic cluster is better
        if dynamic_similarities:
            best_dynamic = max(dynamic_similarities, key=dynamic_similarities.get)
            if dynamic_similarities[best_dynamic] > best_confidence:
                # Return dynamic cluster match
                classification = IntentClassification(
                    intent=IntentCategory.UNKNOWN,
                    confidence=dynamic_similarities[best_dynamic],
                    intent_tags=[best_dynamic],
                    original_query=query,
                    suggested_category=best_dynamic
                )
                self.classification_history.append(classification)
                return classification
        
        # Extract sub-intents (secondary matches above threshold)
        sub_intents = [
            cat.value for cat, sim in similarities.items()
            if sim > self.CONFIDENCE_THRESHOLD * 0.8 and cat != best_category
        ]
        
        # Get intent tags from best cluster
        cluster = self.clusters[best_category]
        intent_tags = self._extract_matching_tags(query, cluster.keywords)
        
        # Check if confidence is too low - trigger discovery
        if best_confidence < self.CONFIDENCE_THRESHOLD:
            classification = self._discover_new_intent(
                query, similarities, query_vector
            )
        else:
            classification = IntentClassification(
                intent=best_category,
                confidence=best_confidence,
                intent_tags=intent_tags,
                original_query=query,
                sub_intents=sub_intents
            )
        
        self.classification_history.append(classification)
        
        return classification
    
    def _extract_matching_tags(self, query: str, keywords: List[str]) -> List[str]:
        """Extract keywords that appear in the query."""
        query_lower = query.lower()
        return [kw for kw in keywords if kw in query_lower]
    
    # --------------------------------------------------------------------------
    # Dynamic Intent Discovery
    # --------------------------------------------------------------------------
    
    def _discover_new_intent(
        self,
        query: str,
        similarities: Dict[IntentCategory, float],
        query_vector: List[float]
    ) -> IntentClassification:
        """
        Discover a new intent when query doesn't match existing clusters.
        
        "If an input falls into a low-confidence void, the Orchestrator
        triggers a 'Reflection' routine."
        
        Args:
            query: Original query
            similarities: Similarity scores to existing clusters
            query_vector: Vector representation of query
        
        Returns:
            IntentClassification with discovered intent
        """
        print(f"[IntentEngine] Low confidence ({max(similarities.values()):.2f}) - triggering discovery")
        
        # Extract key terms from query
        words = re.findall(r'\w+', query.lower())
        
        # Filter out common words
        stop_words = {
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'must', 'shall', 'can',
            'for', 'of', 'to', 'in', 'on', 'at', 'by', 'with', 'from',
            'and', 'or', 'but', 'if', 'then', 'else', 'when', 'where',
            'that', 'this', 'these', 'those', 'it', 'its'
        }
        
        key_terms = [w for w in words if w not in stop_words and len(w) > 2]
        
        if not key_terms:
            # Fall back to closest existing category
            best = max(similarities, key=similarities.get)
            return IntentClassification(
                intent=best,
                confidence=similarities[best],
                intent_tags=[],
                original_query=query
            )
        
        # Create suggested category name
        suggested_name = "_".join(key_terms[:3])
        
        # Check if this is similar to an existing dynamic cluster
        for name, cluster in self.dynamic_clusters.items():
            sim = self._cosine_similarity(query_vector, cluster.centroid)
            if sim > 0.7:
                # Add to existing cluster
                cluster.add_phrase(query)
                return IntentClassification(
                    intent=IntentCategory.UNKNOWN,
                    confidence=(sim + 1) / 2,
                    intent_tags=key_terms,
                    original_query=query,
                    suggested_category=name
                )
        
        # Create new dynamic cluster
        new_cluster = IntentCluster(
            name=suggested_name,
            category=IntentCategory.UNKNOWN,
            keywords=key_terms,
            centroid=query_vector,
            examples=[query],
            learned_phrases=[query]
        )
        
        self.dynamic_clusters[suggested_name] = new_cluster
        
        print(f"[IntentEngine] Created new intent cluster: {suggested_name}")
        
        return IntentClassification(
            intent=IntentCategory.UNKNOWN,
            confidence=0.6,  # Medium confidence for new intents
            intent_tags=key_terms,
            original_query=query,
            is_new_intent=True,
            suggested_category=suggested_name
        )
    
    # --------------------------------------------------------------------------
    # Query Enhancement
    # --------------------------------------------------------------------------
    
    def expand_intent(self, classification: IntentClassification) -> Dict[str, Any]:
        """
        Expand an intent classification with additional context.
        
        Returns enriched data including:
        - Related capabilities
        - Suggested tools
        - Risk indicators
        """
        cluster = self.clusters.get(classification.intent)
        
        if not cluster:
            return {
                "classification": classification,
                "related_capabilities": [],
                "suggested_actions": [],
                "risk_level": "unknown"
            }
        
        # Define risk levels by intent
        risk_levels = {
            IntentCategory.RECONNAISSANCE: "low",
            IntentCategory.VULNERABILITY_ASSESSMENT: "low",
            IntentCategory.ANALYSIS: "low",
            IntentCategory.DISCOVERY: "low",
            IntentCategory.REPORTING: "minimal",
            IntentCategory.HARDENING: "low",
            IntentCategory.EXPLOITATION: "high",
            IntentCategory.POST_EXPLOITATION: "high"
        }
        
        # Define related capabilities
        capability_map = {
            IntentCategory.RECONNAISSANCE: ["watson", "scanner", "enumerator"],
            IntentCategory.VULNERABILITY_ASSESSMENT: ["sherlock", "analyzer", "detector"],
            IntentCategory.EXPLOITATION: ["moriarty", "exploiter", "attacker"],
            IntentCategory.REPORTING: ["mycroft", "reporter", "synthesizer"],
            IntentCategory.HARDENING: ["fixer", "patcher", "hardener"],
            IntentCategory.ANALYSIS: ["sherlock", "analyzer", "decompiler"]
        }
        
        return {
            "classification": {
                "intent": classification.intent.value,
                "confidence": classification.confidence,
                "tags": classification.intent_tags
            },
            "related_capabilities": capability_map.get(classification.intent, []),
            "suggested_actions": cluster.examples[:3],
            "risk_level": risk_levels.get(classification.intent, "medium"),
            "keywords": cluster.keywords[:10]
        }
    
    # --------------------------------------------------------------------------
    # Learning
    # --------------------------------------------------------------------------
    
    def learn_from_feedback(
        self,
        query: str,
        correct_intent: IntentCategory,
        success: bool
    ):
        """
        Learn from user feedback to improve classification.
        
        Args:
            query: The original query
            correct_intent: The actual intended category
            success: Whether the classification was correct
        """
        if success:
            # Reinforce: add query to cluster
            cluster = self.clusters.get(correct_intent)
            if cluster:
                cluster.add_phrase(query)
                # Update centroid with new phrase
                vectors = [self._embed(kw) for kw in cluster.keywords]
                vectors.append(self._embed(query))
                cluster.centroid = self._compute_centroid(vectors)
                print(f"[IntentEngine] Reinforced cluster {correct_intent.value} with: {query[:50]}...")
        else:
            # Corrective: note the misclassification for future improvement
            print(f"[IntentEngine] Misclassification noted: '{query[:50]}...' should be {correct_intent.value}")
    
    # --------------------------------------------------------------------------
    # Statistics
    # --------------------------------------------------------------------------
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get engine statistics."""
        return {
            "predefined_clusters": len(self.clusters),
            "dynamic_clusters": len(self.dynamic_clusters),
            "dynamic_cluster_names": list(self.dynamic_clusters.keys()),
            "classifications_performed": len(self.classification_history),
            "average_confidence": (
                sum(c.confidence for c in self.classification_history) / 
                len(self.classification_history)
            ) if self.classification_history else 0
        }
    
    def get_all_intent_tags(self) -> Set[str]:
        """Get all known intent tags."""
        tags = set()
        for cluster in self.clusters.values():
            tags.update(cluster.keywords)
        for cluster in self.dynamic_clusters.values():
            tags.update(cluster.keywords)
        return tags


# ==============================================================================
# CLI Interface
# ==============================================================================

if __name__ == "__main__":
    import json
    
    engine = IntentRecognitionEngine()
    
    # Test queries
    test_queries = [
        "scan the network for open ports",
        "check if the payment gateway is susceptible to injection attacks",
        "exploit the reentrancy vulnerability in the withdraw function",
        "generate a comprehensive security report",
        "fuzz the API endpoints",  # Should trigger discovery
        "analyze the bytecode for hidden functions"
    ]
    
    print("\n=== Intent Classification Tests ===\n")
    
    for query in test_queries:
        result = engine.classify(query)
        expanded = engine.expand_intent(result)
        
        print(f"Query: {query}")
        print(f"  Intent: {result.intent.value}")
        print(f"  Confidence: {result.confidence:.2f}")
        print(f"  Tags: {result.intent_tags}")
        print(f"  Risk Level: {expanded['risk_level']}")
        if result.is_new_intent:
            print(f"  [NEW INTENT] Suggested: {result.suggested_category}")
        print()
    
    print("\n=== Statistics ===")
    print(json.dumps(engine.get_statistics(), indent=2))
