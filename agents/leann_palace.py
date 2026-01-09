#!/usr/bin/env python3
"""
LEANN Mind Palace: Persistent Vector Memory for the Holmesian Framework
========================================================================

Replaces the in-memory Mind Palace with LEANN for:
- 97% storage savings vs Qdrant
- Persistent memory across sessions
- Local, private semantic search
- Graph-based selective recomputation

Usage:
    from leann_palace import LEANNMindPalace
    
    palace = LEANNMindPalace()
    palace.encode("reentrancy vulnerability pattern", room="reentrancy")
    results = palace.retrieve("external call before state update")
"""

import os
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum

# Try to import LEANN
try:
    from leann import LeannBuilder, LeannSearcher
    LEANN_AVAILABLE = True
except ImportError:
    LEANN_AVAILABLE = False
    print("[LEANN] Warning: LEANN not installed. Using fallback in-memory storage.")


# ==============================================================================
# Room Definitions (Same as cognitive_core.py for compatibility)
# ==============================================================================

class Room(Enum):
    """Rooms in the Mind Palace - thematic categories."""
    REENTRANCY = "reentrancy"
    ACCESS_CONTROL = "access_control"
    ORACLE_MANIPULATION = "oracle_manipulation"
    FLASH_LOAN = "flash_loan"
    FRONT_RUNNING = "front_running"
    ARITHMETIC = "arithmetic"
    GOVERNANCE = "governance"
    TIMESTAMP = "timestamp"
    LIQUIDATION = "liquidation"
    UPGRADES = "upgrades"
    GENERAL = "general"
    # New rooms for research
    RESEARCH = "research"
    EXPLOITS = "exploits"
    PROTOCOLS = "protocols"


class MemoryType(Enum):
    """Types of memories stored."""
    VULNERABILITY_PATTERN = "vulnerability_pattern"
    CODE_CHUNK = "code_chunk"
    HISTORICAL_EXPLOIT = "historical_exploit"
    RESEARCH = "research"
    FINDING = "finding"
    CVE = "cve"


@dataclass
class Memory:
    """A single memory in the palace."""
    id: str
    content: str
    memory_type: MemoryType
    room: Room
    association: str  # Mnemonic hook
    metadata: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.5
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content[:200],
            "memory_type": self.memory_type.value,
            "room": self.room.value,
            "association": self.association,
            "confidence": self.confidence,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class RetrievalResult:
    """Result of a memory retrieval."""
    query: str
    memories: List[Memory]
    rooms_searched: List[Room]
    retrieval_time_ms: float


# ==============================================================================
# LEANN Mind Palace
# ==============================================================================

class LEANNMindPalace:
    """
    Mind Palace backed by LEANN for persistent, efficient vector storage.
    
    Uses LEANN's graph-based selective recomputation for 97% storage savings.
    """
    
    DEFAULT_PATH = Path.home() / ".sherlock" / "mind_palace"
    
    def __init__(
        self,
        storage_path: Optional[Path] = None,
        embedding_model: str = "all-MiniLM-L6-v2"
    ):
        """
        Initialize the LEANN Mind Palace.
        
        Args:
            storage_path: Where to store the palace data
            embedding_model: Sentence transformer model for embeddings
        """
        self.storage_path = Path(storage_path) if storage_path else self.DEFAULT_PATH
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.embedding_model = embedding_model
        self.memories: Dict[str, Memory] = {}
        self.memory_count = 0
        
        # Initialize LEANN index or fallback
        if LEANN_AVAILABLE:
            self._init_leann()
        else:
            self._init_fallback()
        
        # Load existing memories metadata
        self._load_metadata()
        
        print(f"[MindPalace] Initialized at {self.storage_path}")
        print(f"[MindPalace] Backend: {'LEANN' if LEANN_AVAILABLE else 'In-Memory Fallback'}")
        print(f"[MindPalace] Memories loaded: {len(self.memories)}")
    
    def _init_leann(self):
        """Initialize LEANN vector index."""
        self.index_path = self.storage_path / "leann_index"
        self.pending_texts: List[Dict[str, Any]] = []  # Buffer for batch indexing
        
        try:
            # Check if index exists
            if (self.index_path / "graph.bin").exists():
                # Load existing index
                self.searcher = LeannSearcher(str(self.index_path))
                self.builder = None  # Don't need builder for existing index
                self.use_leann = True
                print(f"[MindPalace] LEANN index loaded from {self.index_path}")
            else:
                # Create new builder for new index
                self.builder = LeannBuilder(
                    backend_name="hnsw",
                    embedding_model=self.embedding_model
                )
                self.searcher = None  # Will be created after building
                self.use_leann = True
                print(f"[MindPalace] LEANN builder initialized (new index)")
        except Exception as e:
            print(f"[MindPalace] LEANN init failed: {e}. Using fallback.")
            self._init_fallback()
    
    def _init_fallback(self):
        """Initialize fallback in-memory storage."""
        self.builder = None
        self.searcher = None
        self.use_leann = False
        self.fallback_vectors: List[Dict[str, Any]] = []
        self.pending_texts: List[Dict[str, Any]] = []
    
    def _load_metadata(self):
        """Load memories metadata from disk."""
        metadata_file = self.storage_path / "memories.json"
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r') as f:
                    data = json.load(f)
                for mem_data in data:
                    mem = Memory(
                        id=mem_data["id"],
                        content=mem_data.get("content", ""),
                        memory_type=MemoryType(mem_data.get("memory_type", "code_chunk")),
                        room=Room(mem_data.get("room", "general")),
                        association=mem_data.get("association", ""),
                        metadata=mem_data.get("metadata", {}),
                        confidence=mem_data.get("confidence", 0.5)
                    )
                    self.memories[mem.id] = mem
                self.memory_count = len(self.memories)
            except Exception as e:
                print(f"[MindPalace] Failed to load metadata: {e}")
    
    def _save_metadata(self):
        """Save memories metadata to disk."""
        metadata_file = self.storage_path / "memories.json"
        try:
            data = [mem.to_dict() for mem in self.memories.values()]
            with open(metadata_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[MindPalace] Failed to save metadata: {e}")
    
    # --------------------------------------------------------------------------
    # Core Operations
    # --------------------------------------------------------------------------
    
    def encode(
        self,
        content: str,
        memory_type: MemoryType = MemoryType.CODE_CHUNK,
        room: Room = Room.GENERAL,
        association: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Memory:
        """
        Encode a new memory into the palace.
        
        Args:
            content: The content to store
            memory_type: Type of memory
            room: Which room to store in
            association: Mnemonic association
            metadata: Additional metadata
            
        Returns:
            The created Memory
        """
        memory_id = f"mem_{self.memory_count}_{hash(content) % 10000:04d}"
        self.memory_count += 1
        
        memory = Memory(
            id=memory_id,
            content=content,
            memory_type=memory_type,
            room=room,
            association=association or f"Memory in {room.value}",
            metadata=metadata or {},
            confidence=0.5
        )
        
        # Store in LEANN or fallback
        if self.use_leann and self.builder:
            try:
                # Add to builder with metadata
                full_text = f"[{room.value}] {association}: {content}"
                self.builder.add_text(
                    text=full_text,
                    metadata={
                        "id": memory_id,
                        "room": room.value,
                        "memory_type": memory_type.value,
                        "association": association
                    }
                )
                self.pending_texts.append({
                    "id": memory_id,
                    "content": content
                })
            except Exception as e:
                print(f"[MindPalace] LEANN encode failed: {e}")
                self.fallback_vectors.append({
                    "id": memory_id,
                    "content": content,
                    "room": room.value,
                    "memory_type": memory_type.value
                })
        else:
            self.fallback_vectors.append({
                "id": memory_id,
                "content": content,
                "room": room.value,
                "memory_type": memory_type.value
            })
        
        self.memories[memory_id] = memory
        self._save_metadata()
        
        return memory
    
    def build_index(self):
        """Build the LEANN index from pending texts."""
        if self.use_leann and self.builder and self.pending_texts:
            try:
                self.index_path.mkdir(parents=True, exist_ok=True)
                self.builder.build_index(str(self.index_path))
                self.searcher = LeannSearcher(str(self.index_path))
                self.pending_texts.clear()
                print(f"[MindPalace] LEANN index built with {len(self.memories)} memories")
            except Exception as e:
                print(f"[MindPalace] Failed to build index: {e}")
    
    def retrieve(
        self,
        query: str,
        rooms: Optional[List[Room]] = None,
        top_k: int = 5,
        min_similarity: float = 0.3
    ) -> RetrievalResult:
        """
        Retrieve memories similar to the query.
        
        Args:
            query: Search query
            rooms: Optional list of rooms to search
            top_k: Number of results to return
            min_similarity: Minimum similarity threshold
            
        Returns:
            RetrievalResult with matching memories
        """
        import time
        start = time.time()
        
        rooms_to_search = rooms or list(Room)
        room_values = [r.value for r in rooms_to_search]
        
        matching_memories = []
        
        if self.use_leann and self.searcher:
            try:
                # LEANN search with metadata filtering
                metadata_filters = None
                if rooms:
                    metadata_filters = {"room": {"in": room_values}}
                
                results = self.searcher.search(
                    query=query,
                    top_k=top_k,
                    metadata_filters=metadata_filters
                )
                
                for result in results:
                    # SearchResult has text, metadata, score attributes
                    mem_id = result.metadata.get("id") if result.metadata else None
                    if mem_id and mem_id in self.memories:
                        mem = self.memories[mem_id]
                        mem.confidence = getattr(result, 'score', 0.5) or 0.5
                        if mem.confidence >= min_similarity:
                            matching_memories.append(mem)
                            
            except Exception as e:
                print(f"[MindPalace] LEANN search failed: {e}")
                # Fall back to metadata-based search
                matching_memories = self._fallback_search(query, room_values, top_k)
        else:
            matching_memories = self._fallback_search(query, room_values, top_k)
        
        elapsed_ms = (time.time() - start) * 1000
        
        return RetrievalResult(
            query=query,
            memories=matching_memories[:top_k],
            rooms_searched=rooms_to_search,
            retrieval_time_ms=elapsed_ms
        )
    
    def _fallback_search(
        self,
        query: str,
        room_values: List[str],
        top_k: int
    ) -> List[Memory]:
        """Simple keyword-based fallback search."""
        query_lower = query.lower()
        results = []
        
        for mem in self.memories.values():
            if mem.room.value in room_values:
                # Simple keyword matching
                content_lower = mem.content.lower()
                score = sum(1 for word in query_lower.split() if word in content_lower)
                if score > 0:
                    mem.confidence = min(0.9, score * 0.2)
                    results.append(mem)
        
        results.sort(key=lambda m: m.confidence, reverse=True)
        return results[:top_k]
    
    # --------------------------------------------------------------------------
    # Convenience Methods
    # --------------------------------------------------------------------------
    
    def encode_vulnerability_pattern(
        self,
        pattern_code: str,
        vuln_type: str,
        severity: str = "MEDIUM",
        association: str = ""
    ) -> Memory:
        """Encode a vulnerability pattern."""
        room_map = {
            "reentrancy": Room.REENTRANCY,
            "access_control": Room.ACCESS_CONTROL,
            "oracle": Room.ORACLE_MANIPULATION,
            "flash_loan": Room.FLASH_LOAN,
            "front_running": Room.FRONT_RUNNING,
        }
        
        room = room_map.get(vuln_type.lower(), Room.GENERAL)
        
        return self.encode(
            content=pattern_code,
            memory_type=MemoryType.VULNERABILITY_PATTERN,
            room=room,
            association=association or f"🔴 {vuln_type} pattern",
            metadata={"severity": severity, "vuln_type": vuln_type}
        )
    
    def encode_research(
        self,
        content: str,
        source: str,
        topic: str
    ) -> Memory:
        """Encode research findings."""
        return self.encode(
            content=content,
            memory_type=MemoryType.RESEARCH,
            room=Room.RESEARCH,
            association=f"📚 Research: {topic}",
            metadata={"source": source, "topic": topic}
        )
    
    def encode_exploit(
        self,
        exploit_code: str,
        target: str,
        cve: Optional[str] = None
    ) -> Memory:
        """Encode a known exploit."""
        return self.encode(
            content=exploit_code,
            memory_type=MemoryType.HISTORICAL_EXPLOIT,
            room=Room.EXPLOITS,
            association=f"💀 Exploit: {target}",
            metadata={"target": target, "cve": cve}
        )
    
    # --------------------------------------------------------------------------
    # Statistics
    # --------------------------------------------------------------------------
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get palace statistics."""
        room_counts = {}
        type_counts = {}
        
        for mem in self.memories.values():
            room_counts[mem.room.value] = room_counts.get(mem.room.value, 0) + 1
            type_counts[mem.memory_type.value] = type_counts.get(mem.memory_type.value, 0) + 1
        
        return {
            "total_memories": len(self.memories),
            "backend": "LEANN" if self.use_leann else "fallback",
            "storage_path": str(self.storage_path),
            "by_room": room_counts,
            "by_type": type_counts
        }
    
    def clear(self):
        """Clear all memories."""
        self.memories.clear()
        if hasattr(self, 'fallback_vectors'):
            self.fallback_vectors.clear()
        if hasattr(self, 'pending_texts'):
            self.pending_texts.clear()
        self.memory_count = 0
        
        if self.use_leann:
            # Reinitialize LEANN
            self._init_leann()
        
        self._save_metadata()
        print("[MindPalace] All memories cleared.")


# ==============================================================================
# Compatibility Layer
# ==============================================================================

def create_default_palace() -> LEANNMindPalace:
    """Create a default Mind Palace instance."""
    return LEANNMindPalace()


# Alias for backwards compatibility
MindPalace = LEANNMindPalace


# ==============================================================================
# CLI
# ==============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="LEANN Mind Palace CLI")
    parser.add_argument("action", choices=["stats", "search", "encode", "clear"])
    parser.add_argument("--query", "-q", help="Search query")
    parser.add_argument("--content", "-c", help="Content to encode")
    parser.add_argument("--room", "-r", default="general", help="Room name")
    
    args = parser.parse_args()
    
    palace = LEANNMindPalace()
    
    if args.action == "stats":
        stats = palace.get_statistics()
        print(json.dumps(stats, indent=2))
        
    elif args.action == "search":
        if not args.query:
            print("Error: --query required for search")
            return
        results = palace.retrieve(args.query)
        print(f"Found {len(results.memories)} memories in {results.retrieval_time_ms:.2f}ms:")
        for mem in results.memories:
            print(f"  - [{mem.room.value}] {mem.association} (conf: {mem.confidence:.2f})")
            
    elif args.action == "encode":
        if not args.content:
            print("Error: --content required for encode")
            return
        room = Room(args.room) if args.room in [r.value for r in Room] else Room.GENERAL
        mem = palace.encode(args.content, room=room)
        print(f"Encoded memory: {mem.id}")
        
    elif args.action == "clear":
        palace.clear()


if __name__ == "__main__":
    main()
