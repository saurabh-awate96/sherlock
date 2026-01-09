"""
Google Antigravity: The Mind Palace (Method of Loci)
=====================================================

The Holmesian Mind Palace - a mnemonic technique that turns the brain into 
a physical workspace. Unlike simple key-value storage, this architecture:

1. Encodes abstract data into vivid, spatial representations
2. Organizes memory into navigable "rooms" by domain
3. Enables dynamic simulation for hypothesis testing
4. Provides semantic retrieval through "walking" the palace

"I consider that a man's brain originally is like a little empty attic, 
and you have to stock it with such furniture as you choose."
- Sherlock Holmes, A Study in Scarlet
"""

import json
import hashlib
import math
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
from enum import Enum
import numpy as np


# ==============================================================================
# Core Data Structures
# ==============================================================================

class MemoryType(Enum):
    """Types of memories stored in the Mind Palace"""
    VULNERABILITY_PATTERN = "vulnerability_pattern"
    EXPLOIT_SIGNATURE = "exploit_signature"
    SAFE_PATTERN = "safe_pattern"
    CODE_CHUNK = "code_chunk"
    HISTORICAL_EXPLOIT = "historical_exploit"
    INVARIANT = "invariant"


class Room(Enum):
    """Rooms in the Mind Palace - domain-specific memory areas"""
    REENTRANCY = "reentrancy"
    ORACLE_MANIPULATION = "oracle_manipulation"
    ACCESS_CONTROL = "access_control"
    ARITHMETIC = "arithmetic"
    FLASH_LOAN = "flash_loan"
    GOVERNANCE = "governance"
    LIQUIDATION = "liquidation"
    CROSS_CONTRACT = "cross_contract"
    TIMESTAMP = "timestamp"
    FRONT_RUNNING = "front_running"
    STORAGE_COLLISION = "storage_collision"
    GENERAL = "general"


@dataclass
class Memory:
    """
    A single memory in the Mind Palace.
    
    Each memory has:
    - Content: The actual data (code pattern, exploit signature, etc.)
    - Location: The room where it's stored
    - Association: The vivid/absurd mental hook for recall
    - Vector: Semantic embedding for similarity search
    - Access count: For prioritizing frequently-used memories
    """
    id: str
    content: str
    memory_type: MemoryType
    room: Room
    association: str  # The vivid mental hook
    metadata: Dict[str, Any] = field(default_factory=dict)
    vector: Optional[np.ndarray] = None
    created_at: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    confidence: float = 1.0


@dataclass
class SimulationResult:
    """Result of running a mental simulation"""
    scenario: str
    outcome: str
    probability: float
    supporting_evidence: List[str]
    contradicting_evidence: List[str]
    confidence: float


@dataclass
class RetrievalResult:
    """Result of retrieving memories from the palace"""
    memories: List[Memory]
    walk_path: List[Room]
    total_relevance_score: float
    query_vector: Optional[np.ndarray] = None


# ==============================================================================
# The Mind Palace
# ==============================================================================

class MindPalace:
    """
    The Method of Loci implementation for semantic memory.
    
    The Mind Palace is depicted as a vast, labyrinthine vault or museum.
    Sherlock navigates it physically in his mind, opening drawers, checking
    files, and reviewing memories as if they were tangible objects.
    
    This implementation:
    1. Stores memories in domain-specific "rooms"
    2. Uses vector embeddings for semantic retrieval
    3. Tracks access patterns to prioritize frequently-used knowledge
    4. Provides simulation capability for hypothesis testing
    """
    
    def __init__(self, embedding_dim: int = 384, use_external_db: bool = False):
        """
        Initialize the Mind Palace.
        
        Args:
            embedding_dim: Dimension of embedding vectors
            use_external_db: Whether to use external vector DB (Qdrant) or in-memory
        """
        self.embedding_dim = embedding_dim
        self.use_external_db = use_external_db
        
        # In-memory storage: Room -> List[Memory]
        self.rooms: Dict[Room, List[Memory]] = {room: [] for room in Room}
        
        # Index for fast ID lookup
        self.memory_index: Dict[str, Memory] = {}
        
        # Association index for vivid recall
        self.association_index: Dict[str, str] = {}  # association -> memory_id
        
        # Statistics
        self.total_memories = 0
        self.total_retrievals = 0
        
        print(f"[Mind Palace] Initialized with {len(Room)} rooms")
        print(f"[Mind Palace] Mode: {'External Vector DB' if use_external_db else 'In-Memory'}")
    
    # --------------------------------------------------------------------------
    # Encoding (Adding memories)
    # --------------------------------------------------------------------------
    
    def encode(
        self,
        content: str,
        memory_type: MemoryType,
        room: Room,
        association: str,
        metadata: Optional[Dict[str, Any]] = None,
        vector: Optional[np.ndarray] = None
    ) -> str:
        """
        Encode data with spatial/visual memory hooks.
        
        The encoding process:
        1. Assign the memory to a specific room (spatial location)
        2. Create a vivid association for "sticky" recall
        3. Generate semantic embedding if not provided
        4. Store with rich metadata
        
        Args:
            content: The actual content to remember
            memory_type: Type of memory (vulnerability, exploit, etc.)
            room: The room to store it in
            association: A vivid mental image for recall
            metadata: Additional context
            vector: Pre-computed embedding (optional)
        
        Returns:
            Memory ID
        """
        # Generate memory ID
        memory_id = self._generate_id(content, room)
        
        # Generate simple embedding if not provided
        if vector is None:
            vector = self._generate_simple_embedding(content)
        
        # Create memory object
        memory = Memory(
            id=memory_id,
            content=content,
            memory_type=memory_type,
            room=room,
            association=association,
            metadata=metadata or {},
            vector=vector,
            created_at=datetime.now()
        )
        
        # Store in the appropriate room
        self.rooms[room].append(memory)
        self.memory_index[memory_id] = memory
        self.association_index[association.lower()] = memory_id
        self.total_memories += 1
        
        print(f"[Mind Palace] Encoded memory in {room.value}: '{association}'")
        
        return memory_id
    
    def encode_vulnerability_pattern(
        self,
        pattern_code: str,
        vuln_type: str,
        severity: str,
        description: str,
        example_exploit: Optional[str] = None
    ) -> str:
        """
        Convenience method to encode a vulnerability pattern.
        
        Creates a vivid association automatically based on severity.
        """
        # Determine room from vulnerability type
        room = self._vuln_type_to_room(vuln_type)
        
        # Create vivid association (the more absurd, the stickier)
        severity_imagery = {
            "CRITICAL": "🔥 BURNING",
            "HIGH": "⚠️ GLOWING RED",
            "MEDIUM": "🟡 PULSING YELLOW",
            "LOW": "🔵 COOL BLUE"
        }
        imagery = severity_imagery.get(severity.upper(), "🔵 NEUTRAL")
        association = f"{imagery} {vuln_type.upper()} pattern: {description[:50]}"
        
        metadata = {
            "vuln_type": vuln_type,
            "severity": severity,
            "description": description,
            "example_exploit": example_exploit,
            "pattern_hash": hashlib.md5(pattern_code.encode()).hexdigest()
        }
        
        return self.encode(
            content=pattern_code,
            memory_type=MemoryType.VULNERABILITY_PATTERN,
            room=room,
            association=association,
            metadata=metadata
        )
    
    def encode_historical_exploit(
        self,
        exploit_name: str,
        affected_protocol: str,
        loss_amount: str,
        attack_vector: str,
        code_pattern: str,
        date: str
    ) -> str:
        """Encode a historical exploit for pattern matching."""
        room = self._vuln_type_to_room(attack_vector)
        
        # Create memorable association
        association = f"💀 {exploit_name} ({affected_protocol}): ${loss_amount} lost via {attack_vector}"
        
        metadata = {
            "exploit_name": exploit_name,
            "affected_protocol": affected_protocol,
            "loss_amount": loss_amount,
            "attack_vector": attack_vector,
            "date": date
        }
        
        return self.encode(
            content=code_pattern,
            memory_type=MemoryType.HISTORICAL_EXPLOIT,
            room=room,
            association=association,
            metadata=metadata
        )
    
    # --------------------------------------------------------------------------
    # Retrieval (Walking the Palace)
    # --------------------------------------------------------------------------
    
    def retrieve(
        self,
        query: str,
        rooms: Optional[List[Room]] = None,
        memory_types: Optional[List[MemoryType]] = None,
        top_k: int = 5,
        min_similarity: float = 0.5
    ) -> RetrievalResult:
        """
        Navigate the palace to retrieve associated memories.
        
        The retrieval process:
        1. Convert query to vector embedding
        2. Determine which rooms to search (walk path)
        3. Find semantically similar memories
        4. Update access statistics
        5. Return ranked results
        
        Args:
            query: The search query
            rooms: Specific rooms to search (None = all rooms)
            memory_types: Filter by memory type
            top_k: Number of results to return
            min_similarity: Minimum cosine similarity threshold
        
        Returns:
            RetrievalResult with matched memories
        """
        self.total_retrievals += 1
        
        # Generate query vector
        query_vector = self._generate_simple_embedding(query)
        
        # Determine walk path
        walk_path = rooms if rooms else list(Room)
        
        # Collect candidate memories
        candidates: List[Tuple[Memory, float]] = []
        
        for room in walk_path:
            for memory in self.rooms[room]:
                # Filter by type if specified
                if memory_types and memory.memory_type not in memory_types:
                    continue
                
                # Calculate similarity
                similarity = self._cosine_similarity(query_vector, memory.vector)
                
                if similarity >= min_similarity:
                    candidates.append((memory, similarity))
        
        # Sort by similarity and take top_k
        candidates.sort(key=lambda x: x[1], reverse=True)
        top_memories = candidates[:top_k]
        
        # Update access statistics
        for memory, _ in top_memories:
            memory.access_count += 1
            memory.last_accessed = datetime.now()
        
        # Calculate total relevance
        total_relevance = sum(sim for _, sim in top_memories) if top_memories else 0.0
        
        print(f"[Mind Palace] Retrieved {len(top_memories)} memories (walked {len(walk_path)} rooms)")
        
        return RetrievalResult(
            memories=[m for m, _ in top_memories],
            walk_path=walk_path,
            total_relevance_score=total_relevance,
            query_vector=query_vector
        )
    
    def retrieve_by_association(self, association_fragment: str) -> Optional[Memory]:
        """
        Retrieve memory by its vivid association.
        
        This is the "instant recall" - when you see the burning bread 
        in the hallway, you instantly decode: "The suspect is a baker."
        """
        fragment_lower = association_fragment.lower()
        
        for assoc, memory_id in self.association_index.items():
            if fragment_lower in assoc:
                memory = self.memory_index.get(memory_id)
                if memory:
                    memory.access_count += 1
                    memory.last_accessed = datetime.now()
                    print(f"[Mind Palace] Instant recall via association: '{association_fragment}'")
                    return memory
        
        return None
    
    def retrieve_from_room(
        self,
        room: Room,
        top_k: int = 10
    ) -> List[Memory]:
        """
        Get top memories from a specific room, ranked by access frequency.
        
        Like walking to a specific room and scanning its contents.
        """
        memories = self.rooms[room]
        
        # Sort by access count (most accessed = most important)
        sorted_memories = sorted(
            memories,
            key=lambda m: (m.access_count, m.confidence),
            reverse=True
        )
        
        return sorted_memories[:top_k]
    
    # --------------------------------------------------------------------------
    # Simulation (Mental Experimentation)
    # --------------------------------------------------------------------------
    
    def simulate(
        self,
        scenario: str,
        hypothesis: str,
        context_memories: Optional[List[Memory]] = None
    ) -> SimulationResult:
        """
        Run counter-factual scenarios in the mental workspace.
        
        In "The Abominable Bride", Sherlock enters a drug-induced Mind Palace
        scenario set in Victorian London to solve a cold case. This demonstrates
        that the Mind Palace is a sophisticated simulation engine.
        
        Args:
            scenario: The scenario to simulate
            hypothesis: The hypothesis to test
            context_memories: Relevant memories to inform the simulation
        
        Returns:
            SimulationResult with outcome and confidence
        """
        print(f"[Mind Palace] Running simulation: '{hypothesis}'")
        
        # Gather supporting and contradicting evidence from memory
        supporting = []
        contradicting = []
        
        # Search for relevant memories
        if context_memories is None:
            retrieval = self.retrieve(f"{scenario} {hypothesis}", top_k=10)
            context_memories = retrieval.memories
        
        # Analyze each memory for support/contradiction
        for memory in context_memories:
            # Simple heuristic: check if memory type aligns with hypothesis
            if memory.memory_type == MemoryType.HISTORICAL_EXPLOIT:
                supporting.append(f"Historical precedent: {memory.association}")
            elif memory.memory_type == MemoryType.SAFE_PATTERN:
                contradicting.append(f"Safe pattern match: {memory.association}")
            elif memory.memory_type == MemoryType.VULNERABILITY_PATTERN:
                supporting.append(f"Known vulnerability: {memory.association}")
        
        # Calculate probability based on evidence balance
        support_weight = len(supporting) * 0.1
        contradict_weight = len(contradicting) * 0.1
        
        base_probability = 0.5  # Prior
        probability = min(0.95, max(0.05, base_probability + support_weight - contradict_weight))
        
        # Determine outcome
        if probability > 0.7:
            outcome = "LIKELY_VULNERABLE"
        elif probability > 0.4:
            outcome = "REQUIRES_VERIFICATION"
        else:
            outcome = "LIKELY_SAFE"
        
        # Confidence based on evidence quantity
        evidence_count = len(supporting) + len(contradicting)
        confidence = min(0.95, 0.3 + (evidence_count * 0.1))
        
        return SimulationResult(
            scenario=scenario,
            outcome=outcome,
            probability=probability,
            supporting_evidence=supporting,
            contradicting_evidence=contradicting,
            confidence=confidence
        )
    
    # --------------------------------------------------------------------------
    # Utility Methods
    # --------------------------------------------------------------------------
    
    def _generate_id(self, content: str, room: Room) -> str:
        """Generate unique memory ID."""
        hash_input = f"{content}{room.value}{datetime.now().isoformat()}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]
    
    def _generate_simple_embedding(self, text: str) -> np.ndarray:
        """
        Generate a simple embedding for text.
        
        In production, this would call an embedding model like
        text-embedding-3-large. For now, we use a deterministic
        hash-based embedding.
        """
        # Create deterministic pseudo-embedding from text hash
        text_hash = hashlib.sha256(text.encode()).digest()
        
        # Convert bytes to normalized float array
        embedding = np.array([b / 255.0 for b in text_hash])
        
        # Pad or truncate to embedding_dim
        if len(embedding) < self.embedding_dim:
            embedding = np.pad(embedding, (0, self.embedding_dim - len(embedding)))
        else:
            embedding = embedding[:self.embedding_dim]
        
        # Normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        
        return embedding
    
    def _cosine_similarity(self, v1: np.ndarray, v2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        if v1 is None or v2 is None:
            return 0.0
        
        dot = np.dot(v1, v2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot / (norm1 * norm2))
    
    def _vuln_type_to_room(self, vuln_type: str) -> Room:
        """Map vulnerability type to appropriate room."""
        vuln_lower = vuln_type.lower()
        
        mapping = {
            "reentrancy": Room.REENTRANCY,
            "reentrant": Room.REENTRANCY,
            "oracle": Room.ORACLE_MANIPULATION,
            "price": Room.ORACLE_MANIPULATION,
            "access": Room.ACCESS_CONTROL,
            "permission": Room.ACCESS_CONTROL,
            "auth": Room.ACCESS_CONTROL,
            "overflow": Room.ARITHMETIC,
            "underflow": Room.ARITHMETIC,
            "arithmetic": Room.ARITHMETIC,
            "flash": Room.FLASH_LOAN,
            "governance": Room.GOVERNANCE,
            "voting": Room.GOVERNANCE,
            "liquidation": Room.LIQUIDATION,
            "cross": Room.CROSS_CONTRACT,
            "timestamp": Room.TIMESTAMP,
            "block": Room.TIMESTAMP,
            "front": Room.FRONT_RUNNING,
            "sandwich": Room.FRONT_RUNNING,
            "mev": Room.FRONT_RUNNING,
            "storage": Room.STORAGE_COLLISION,
            "collision": Room.STORAGE_COLLISION,
        }
        
        for key, room in mapping.items():
            if key in vuln_lower:
                return room
        
        return Room.GENERAL
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get Mind Palace statistics."""
        room_counts = {room.value: len(memories) for room, memories in self.rooms.items()}
        
        return {
            "total_memories": self.total_memories,
            "total_retrievals": self.total_retrievals,
            "rooms": room_counts,
            "most_accessed": self._get_most_accessed(5)
        }
    
    def _get_most_accessed(self, n: int) -> List[Dict[str, Any]]:
        """Get n most frequently accessed memories."""
        all_memories = []
        for memories in self.rooms.values():
            all_memories.extend(memories)
        
        sorted_memories = sorted(all_memories, key=lambda m: m.access_count, reverse=True)
        
        return [
            {
                "id": m.id,
                "association": m.association,
                "access_count": m.access_count,
                "room": m.room.value
            }
            for m in sorted_memories[:n]
        ]
    
    def export_state(self) -> Dict[str, Any]:
        """Export Mind Palace state to JSON-serializable dict."""
        state = {
            "total_memories": self.total_memories,
            "rooms": {}
        }
        
        for room, memories in self.rooms.items():
            state["rooms"][room.value] = [
                {
                    "id": m.id,
                    "content": m.content,
                    "memory_type": m.memory_type.value,
                    "association": m.association,
                    "metadata": m.metadata,
                    "access_count": m.access_count,
                    "confidence": m.confidence
                }
                for m in memories
            ]
        
        return state
    
    def import_state(self, state: Dict[str, Any]) -> None:
        """Import Mind Palace state from dict."""
        for room_name, memories in state.get("rooms", {}).items():
            room = Room(room_name)
            for m_data in memories:
                self.encode(
                    content=m_data["content"],
                    memory_type=MemoryType(m_data["memory_type"]),
                    room=room,
                    association=m_data["association"],
                    metadata=m_data.get("metadata", {})
                )
        
        print(f"[Mind Palace] Imported {self.total_memories} memories")


# ==============================================================================
# Initialize Default Mind Palace with Common Vulnerability Patterns
# ==============================================================================

def create_default_palace() -> MindPalace:
    """Create a Mind Palace pre-populated with common vulnerability patterns."""
    palace = MindPalace()
    
    # Reentrancy patterns
    palace.encode_vulnerability_pattern(
        pattern_code="external_call(); state_change();",
        vuln_type="reentrancy",
        severity="CRITICAL",
        description="External call before state update (classic reentrancy)",
        example_exploit="The DAO hack"
    )
    
    palace.encode_vulnerability_pattern(
        pattern_code="view_function_reads_balance_during_callback",
        vuln_type="read-only-reentrancy",
        severity="HIGH",
        description="Read-only reentrancy via view function during callback"
    )
    
    # Oracle manipulation
    palace.encode_vulnerability_pattern(
        pattern_code="spot_price = reserve0 / reserve1",
        vuln_type="oracle_manipulation",
        severity="CRITICAL",
        description="Using spot price from AMM reserves (flash loan manipulable)"
    )
    
    # Access control
    palace.encode_vulnerability_pattern(
        pattern_code="tx.origin == owner",
        vuln_type="access_control",
        severity="HIGH",
        description="Using tx.origin for authentication (phishing vulnerability)"
    )
    
    # Historical exploits
    palace.encode_historical_exploit(
        exploit_name="The DAO",
        affected_protocol="The DAO",
        loss_amount="60M",
        attack_vector="reentrancy",
        code_pattern="call.value()() before balance update",
        date="2016-06-17"
    )
    
    palace.encode_historical_exploit(
        exploit_name="Euler Finance",
        affected_protocol="Euler",
        loss_amount="197M",
        attack_vector="flash_loan",
        code_pattern="donate without proper health check",
        date="2023-03-13"
    )
    
    print(f"[Mind Palace] Default palace created with {palace.total_memories} memories")
    
    return palace


# ==============================================================================
# CLI Interface
# ==============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Mind Palace - Holmesian Memory System")
    parser.add_argument("--action", choices=["init", "encode", "retrieve", "stats"], default="init")
    parser.add_argument("--query", type=str, help="Query for retrieval")
    parser.add_argument("--room", type=str, help="Specific room to search")
    args = parser.parse_args()
    
    palace = create_default_palace()
    
    if args.action == "init":
        print(json.dumps(palace.get_statistics(), indent=2))
    
    elif args.action == "retrieve" and args.query:
        rooms = [Room(args.room)] if args.room else None
        result = palace.retrieve(args.query, rooms=rooms)
        
        for memory in result.memories:
            print(f"  - {memory.association}")
            print(f"    Room: {memory.room.value}, Type: {memory.memory_type.value}")
    
    elif args.action == "stats":
        print(json.dumps(palace.get_statistics(), indent=2))
