"""
Google Antigravity: Watson Agent (Enhanced)
=============================================

Watson is the PERCEPTION ENGINE with Holmesian 'Observing' capability.

"You see, but you do not observe. The distinction is clear."
- Sherlock Holmes to Dr. Watson

The difference between 'seeing' and 'observing':
- SEEING: Passive visual intake (Watson knows nothing about the stairs)  
- OBSERVING: Active cognitive logging (Holmes knows there are 17 steps)

Watson implements:
- System 2 thinking (deliberate, energy-intensive attention)
- Mindfulness-based scanning for anomalies
- Inattentional blindness override
- Signal-noise management before passing to Sherlock
- **Architectural Resilience**: Uses EventBus, Logical Clocks, and Batch Processing.
"""

import argparse
import json
import os
import sys
import hashlib
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
from enum import Enum

# Import cognitive modules
try:
    from cognitive_core import MindPalace, MemoryType, Room, create_default_palace
    from brain_attic import BrainAttic, FilteredChunk, RelevanceCategory, FilterAction
    from internal_agent_base import InternalAgentBase
    from architectural_core import EventType
except ImportError:
    # Running standalone
    from agents.cognitive_core import MindPalace, MemoryType, Room, create_default_palace
    from agents.brain_attic import BrainAttic, FilteredChunk, RelevanceCategory, FilterAction
    from agents.internal_agent_base import InternalAgentBase
    from agents.architectural_core import EventType

# Try to import LEANN Mind Palace
try:
    from agents.leann_palace import LEANNMindPalace
    LEANN_AVAILABLE = True
except ImportError:
    try:
        from leann_palace import LEANNMindPalace
        LEANN_AVAILABLE = True
    except ImportError:
        LEANN_AVAILABLE = False
        print("[Watson] LEANN not available, using standard Mind Palace")


# ==============================================================================
# Observation Data Structures
# ==============================================================================

class ObservationLevel(Enum):
    """The level of observation applied."""
    SEEING = "seeing"          # Passive intake (legacy mode)
    OBSERVING = "observing"    # Active System 2 attention
    DEEP_FOCUS = "deep_focus"  # Maximum attention on anomalies


class AnomalyType(Enum):
    """Types of anomalies Watson can detect."""
    MISSING_PATTERN = "missing_pattern"       # Expected pattern absent
    UNEXPECTED_PATTERN = "unexpected_pattern"  # Pattern shouldn't be here
    DEVIATION = "deviation"                    # Differs from normal
    STRUCTURAL = "structural"                  # Code structure issue
    CONTEXTUAL = "contextual"                  # Makes no sense in context


@dataclass
class Observation:
    """A single observation made by Watson."""
    id: str
    content: str
    location: str
    observation_level: ObservationLevel
    anomalies: List[Dict[str, Any]] = field(default_factory=list)
    signals: List[str] = field(default_factory=list)
    confidence: float = 0.5
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content[:200] + "..." if len(self.content) > 200 else self.content,
            "location": self.location,
            "observation_level": self.observation_level.value,
            "anomalies": self.anomalies,
            "signals": self.signals,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class ObservationSet:
    """A collection of observations from a codebase scan."""
    observations: List[Observation]
    total_chunks_seen: int
    total_chunks_observed: int
    anomaly_count: int
    filtered_count: int
    metadata: Dict[str, Any] = field(default_factory=dict)


# ==============================================================================
# Watson Agent
# ==============================================================================

class WatsonAgent(InternalAgentBase):
    """
    THE PERCEPTION ENGINE
    
    Watson transforms raw code into structured observations.
    Unlike simple parsers, Watson actively OBSERVES:
    
    1. Fights inattentional blindness by scanning everything
    2. Tags anomalies with confidence scores
    3. Applies Brain Attic filtering to reduce noise
    4. Stores relevant patterns in the Mind Palace
    
    "The world is full of obvious things which nobody by any 
    chance ever observes." - Sherlock Holmes
    """
    
    # Security patterns to ALWAYS observe (override filtering)
    ALWAYS_OBSERVE = {
        "external_call": r"\.call\s*\{",
        "delegatecall": r"\.delegatecall\s*\(",
        "selfdestruct": r"selfdestruct\s*\(",
        "transfer_call": r"\.transfer\s*\(",
        "send_call": r"\.send\s*\(",
        "assembly": r"assembly\s*\{",
        "tx_origin": r"tx\.origin",
    }
    
    # Expected patterns for context (anomaly if missing)
    EXPECTED_PATTERNS = {
        "external_call": ["ReentrancyGuard", "nonReentrant", "CEI pattern"],
        "delegatecall": ["trusted_implementation", "upgradeability check"],
        "transfer_ownership": ["two-step process", "renounce check"],
    }
    
    def __init__(
        self,
        mind_palace: Optional[MindPalace] = None,
        brain_attic: Optional[BrainAttic] = None,
        observation_level: ObservationLevel = ObservationLevel.OBSERVING,
        session_id: Optional[str] = None
    ):
        """
        Initialize Watson Agent.
        
        Args:
            mind_palace: Memory storage (creates default if None)
            brain_attic: Noise filter (creates default if None)
            observation_level: Default observation intensity
            session_id: Correlation ID for the session
        """
        super().__init__(agent_name="Watson", session_id=session_id)
        
        if mind_palace:
            self.mind_palace = mind_palace
        elif LEANN_AVAILABLE:
            self.log("[Watson] Upgrading to LEANN Mind Palace")
            self.mind_palace = LEANNMindPalace()
        else:
            self.mind_palace = create_default_palace()
            
        self.brain_attic = brain_attic or BrainAttic()
        self.default_observation_level = observation_level
        
        self.observations: List[Observation] = []
        self.observation_count = 0
        
        self.log(f"Initialized in {observation_level.value} mode")
        self.log("'You see, but you do not observe' - Not anymore.")
    
    # --------------------------------------------------------------------------
    # Core Observation Methods
    # --------------------------------------------------------------------------
    
    def observe(
        self,
        code: str,
        location: str,
        context: Optional[str] = None,
        force_deep: bool = False
    ) -> Observation:
        """
        Active observation of a code chunk.
        
        Unlike passive 'seeing', this:
        1. Applies System 2 deliberate attention
        2. Scans for ALL patterns (not just obvious ones)
        3. Compares against expected patterns for context
        4. Tags anomalies with confidence scores
        5. **Publishes observation events via EventBus**
        
        Args:
            code: The code to observe
            location: Where in the codebase
            context: Additional context (function type, etc.)
            force_deep: Force deep focus mode
        
        Returns:
            Observation with anomalies and signals
        """
        obs_level = ObservationLevel.DEEP_FOCUS if force_deep else self.default_observation_level
        
        # Generate observation ID
        obs_id = f"obs_{self.observation_count}_{hashlib.md5(code.encode()).hexdigest()[:8]}"
        self.observation_count += 1
        
        # Phase 1: Signal detection (what's present)
        signals = self._detect_signals(code)
        
        # Phase 2: Anomaly detection (what's unusual)
        anomalies = self._detect_anomalies(code, signals, context)
        
        # Phase 3: Calculate confidence
        confidence = self._calculate_confidence(signals, anomalies)
        
        # Phase 4: LEANN augmentation (if available and significant)
        if LEANN_AVAILABLE and (anomalies or confidence > 0.4) and isinstance(self.mind_palace, LEANNMindPalace):
            try:
                # Search for similar patterns in memory
                results = self.mind_palace.retrieve(
                    code[:200], # Query with snippet
                    rooms=[Room.VULNERABILITY_PATTERN, Room.EXPLOITS],
                    top_k=1,
                    min_similarity=0.75
                )
                if results.memories:
                    match = results.memories[0]
                    anomalies.append({
                        "type": AnomalyType.DEVIATION.value,
                        "description": f"Similar to known pattern: {match.association}",
                        "severity": "HIGH",
                        "signal": "leann_match"
                    })
                    self.log(f"LEANN match: {match.association}")
                    confidence = max(confidence, 0.8)
            except Exception as e:
                pass # Don't fail observation on LEANN error

        observation = Observation(
            id=obs_id,
            content=code,
            location=location,
            observation_level=obs_level,
            anomalies=anomalies,
            signals=signals,
            confidence=confidence
        )
        
        self.observations.append(observation)
        
        # If significant, store in Mind Palace
        if anomalies or confidence > 0.6:
            self._store_in_palace(observation)
        
        if anomalies:
            self.log(f"ANOMALY detected at {location}: {len(anomalies)} issues")
            
        # Publish event
        self.publish_event(EventType.OBSERVATION, observation.to_dict())
        
        return observation
    
    def scan_codebase(
        self,
        chunks: List[Dict[str, Any]],
        file_paths: Optional[List[str]] = None,
        research_context: Optional[Dict[str, Any]] = None
    ) -> ObservationSet:
        """
        Scan an entire codebase with active observation.
        
        Applies Brain Attic filtering to reduce noise,
        then observes each remaining chunk.
        
        Args:
            chunks: List of code chunks with metadata
            file_paths: Optional list of file paths for filtering
            research_context: AI research data (critical functions, etc.)
        
        Returns:
            ObservationSet with all observations
        """
        observations = []
        filtered_count = 0
        anomaly_count = 0
        
        self.log(f"Scanning {len(chunks)} chunks with System 2 attention...")
        
        # Extract research priorities
        critical_funcs = []
        high_risk_patterns = []
        if research_context:
            critical_funcs = [f.lower() for f in research_context.get("critical_functions", [])]
            high_risk_patterns = research_context.get("high_risk_patterns", [])
            self.log(f"Applied research context: {len(critical_funcs)} critical functions")
        
        # BATCH PROCESSING LOOP (To mitigate N+1 / high load) 
        # In a real distributed system, this would be a generator or distributed task queue
        for i, chunk in enumerate(chunks):
            content = chunk.get("content", "")
            location = chunk.get("location", f"chunk_{i}")
            file_path = file_paths[i] if file_paths and i < len(file_paths) else None
            
            # Apply Brain Attic filtering
            filtered = self.brain_attic.filter(content, file_path)
            
            if filtered.action == FilterAction.REJECT:
                filtered_count += 1
                continue
            
            # Adjust observation level based on relevance AND research
            force_deep = False
            if filtered.relevance == RelevanceCategory.CRITICAL:
                force_deep = True
            
            # Check against research context
            if research_context:
                # Check for critical functions
                for cf in critical_funcs:
                    if cf in content.lower():
                        force_deep = True
                        self.log(f"Critical function found: {cf}")
                        break
            
            # Observe the chunk
            obs = self.observe(content, location, force_deep=force_deep)
            observations.append(obs)
            
            if obs.anomalies:
                anomaly_count += len(obs.anomalies)
        
        self.log(f"Observation complete: {len(observations)} observed, {filtered_count} filtered, {anomaly_count} anomalies")
        
        return ObservationSet(
            observations=observations,
            total_chunks_seen=len(chunks),
            total_chunks_observed=len(observations),
            anomaly_count=anomaly_count,
            filtered_count=filtered_count,
            metadata={
                "observation_level": self.default_observation_level.value,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    # --------------------------------------------------------------------------
    # Signal Detection (What's Present)
    # --------------------------------------------------------------------------
    
    def _detect_signals(self, code: str) -> List[str]:
        """
        Detect security-relevant signals in the code.
        """
        import re
        signals = []
        
        # Always-observe patterns
        for signal_name, pattern in self.ALWAYS_OBSERVE.items():
            if re.search(pattern, code):
                signals.append(signal_name)
        
        # Additional patterns for full coverage
        additional_patterns = {
            "state_change": r"\w+\s*=\s*",
            "require_statement": r"require\s*\(",
            "modifier_usage": r"modifier\s+\w+",
            "event_emission": r"emit\s+\w+",
            "loop_structure": r"for\s*\(|while\s*\(",
            "mapping_access": r"\w+\[\w+\]",
            "msg_sender": r"msg\.sender",
            "msg_value": r"msg\.value",
            "block_timestamp": r"block\.timestamp",
            "address_payable": r"payable\s*\(",
            "abi_encode": r"abi\.encode",
            "abi_decode": r"abi\.decode",
            "interface_call": r"I\w+\(",
            "safemath": r"\.add\(|\.sub\(|\.mul\(|\.div\(",
            "ownable": r"onlyOwner|Ownable",
            "pausable": r"whenNotPaused|Pausable",
            "upgradeable": r"UUPS|TransparentProxy|Initializable",
        }
        
        for signal_name, pattern in additional_patterns.items():
            if re.search(pattern, code):
                signals.append(signal_name)
        
        return signals
    
    # --------------------------------------------------------------------------
    # Anomaly Detection (What's Unusual)
    # --------------------------------------------------------------------------
    
    def _detect_anomalies(
        self,
        code: str,
        signals: List[str],
        context: Optional[str]
    ) -> List[Dict[str, Any]]:
        """
        Detect anomalies by fighting inattentional blindness.
        """
        anomalies = []
        
        # Missing expected patterns
        for signal in signals:
            expected = self.EXPECTED_PATTERNS.get(signal, [])
            for expected_pattern in expected:
                if expected_pattern.lower() not in code.lower():
                    anomalies.append({
                        "type": AnomalyType.MISSING_PATTERN.value,
                        "description": f"'{signal}' detected without expected '{expected_pattern}'",
                        "severity": "MEDIUM",
                        "signal": signal,
                        "expected": expected_pattern
                    })
        
        # External call anomalies
        import re
        
        # Check for external call before state change (classic reentrancy)
        external_call_match = re.search(r'\.call\s*\{[^}]*\}\s*\([^)]*\)\s*;', code)
        state_change_after = re.search(r'\.call[^;]*;[^}]*\w+\s*-=|\w+\s*\+=', code)
        if external_call_match and state_change_after:
            anomalies.append({
                "type": AnomalyType.STRUCTURAL.value,
                "description": "External call appears before state change (reentrancy pattern)",
                "severity": "HIGH",
                "signal": "external_call",
                "pattern": "CEI_VIOLATION"
            })
        
        # tx.origin in access control
        if "tx_origin" in signals and "require" in code.lower():
            anomalies.append({
                "type": AnomalyType.UNEXPECTED_PATTERN.value,
                "description": "tx.origin used in access control (phishing vulnerable)",
                "severity": "HIGH",
                "signal": "tx_origin"
            })
        
        # Unchecked call return
        if "external_call" in signals or "send_call" in signals:
            if not re.search(r'(bool\s+success|require\s*\([^)]*call)', code):
                anomalies.append({
                    "type": AnomalyType.MISSING_PATTERN.value,
                    "description": "External call return value not checked",
                    "severity": "MEDIUM",
                    "signal": "unchecked_return"
                })
        
        # Timestamp dependence in critical logic
        if "block_timestamp" in signals and any(s in signals for s in ["transfer_call", "external_call", "state_change"]):
            anomalies.append({
                "type": AnomalyType.CONTEXTUAL.value,
                "description": "block.timestamp in security-critical logic (miner-manipulable)",
                "severity": "LOW",
                "signal": "block_timestamp"
            })
        
        return anomalies
    
    def _calculate_confidence(
        self,
        signals: List[str],
        anomalies: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate confidence that this observation is security-relevant.
        """
        base_confidence = 0.3
        
        # High-risk signals increase confidence
        high_risk_signals = {"external_call", "delegatecall", "selfdestruct", "assembly"}
        high_risk_count = sum(1 for s in signals if s in high_risk_signals)
        base_confidence += high_risk_count * 0.15
        
        # Anomalies significantly increase confidence
        if anomalies:
            severity_boost = {
                "HIGH": 0.25,
                "MEDIUM": 0.15,
                "LOW": 0.05
            }
            for anomaly in anomalies:
                base_confidence += severity_boost.get(anomaly.get("severity", "LOW"), 0.05)
        
        return min(0.95, base_confidence)
    
    # --------------------------------------------------------------------------
    # Mind Palace Integration
    # --------------------------------------------------------------------------
    
    def _store_in_palace(self, observation: Observation):
        """Store significant observation in Mind Palace."""
        # Determine appropriate room
        room = Room.GENERAL
        for signal in observation.signals:
            if "reentr" in signal or "external_call" in signal:
                room = Room.REENTRANCY
                break
            elif "oracle" in signal or "price" in signal:
                room = Room.ORACLE_MANIPULATION
                break
            elif "access" in signal or "owner" in signal:
                room = Room.ACCESS_CONTROL
                break
        
        # Create memorable association
        anomaly_desc = observation.anomalies[0]["description"] if observation.anomalies else "Observed pattern"
        association = f"📍 {observation.location}: {anomaly_desc[:50]}"
        
        self.mind_palace.encode(
            content=observation.content[:500],
            memory_type=MemoryType.CODE_CHUNK,
            room=room,
            association=association,
            metadata={
                "observation_id": observation.id,
                "signals": observation.signals,
                "anomaly_count": len(observation.anomalies)
            }
        )
    
    # --------------------------------------------------------------------------
    # AST Chunking (Semantic Code Splitting)
    # --------------------------------------------------------------------------
    
    def chunk_code(self, source_code: str, file_path: str) -> List[Dict[str, Any]]:
        """
        Split source code into semantic chunks.
        """
        import re
        chunks = []
        
        # Split by contract definitions
        contract_pattern = r'(contract\s+\w+[^{]*\{)'
        function_pattern = r'(function\s+\w+[^{]*\{)'
        
        # Find all contracts
        lines = source_code.split('\n')
        current_chunk = []
        current_type = "header"
        brace_depth = 0
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Track brace depth
            brace_depth += line.count('{') - line.count('}')
            
            # Detect chunk boundaries
            if re.match(r'contract\s+', stripped):
                if current_chunk:
                    chunks.append({
                        "id": f"chunk_{len(chunks)}",
                        "type": current_type,
                        "content": '\n'.join(current_chunk),
                        "location": f"{file_path}:{i-len(current_chunk)+1}-{i}",
                        "start_line": i - len(current_chunk) + 1,
                        "end_line": i
                    })
                current_chunk = [line]
                current_type = "ContractDefinition"
            
            elif re.match(r'function\s+', stripped) and brace_depth <= 1:
                if current_chunk and current_type != "header":
                    chunks.append({
                        "id": f"chunk_{len(chunks)}",
                        "type": current_type,
                        "content": '\n'.join(current_chunk),
                        "location": f"{file_path}:{i-len(current_chunk)+1}-{i}",
                        "start_line": i - len(current_chunk) + 1,
                        "end_line": i
                    })
                current_chunk = [line]
                current_type = "FunctionDefinition"
            
            else:
                current_chunk.append(line)
        
        # Don't forget the last chunk
        if current_chunk:
            chunks.append({
                "id": f"chunk_{len(chunks)}",
                "type": current_type,
                "content": '\n'.join(current_chunk),
                "location": f"{file_path}:{len(lines)-len(current_chunk)+1}-{len(lines)}",
                "start_line": len(lines) - len(current_chunk) + 1,
                "end_line": len(lines)
            })
        
        self.log(f"Chunked {file_path} into {len(chunks)} semantic units")
        
        return chunks
    
    # --------------------------------------------------------------------------
    # Export Methods
    # --------------------------------------------------------------------------
    
    def export_observations(self) -> List[Dict[str, Any]]:
        """Export all observations as JSON-serializable dicts."""
        return [obs.to_dict() for obs in self.observations]
    
    def get_high_priority_observations(self) -> List[Observation]:
        """Get observations with high confidence or anomalies."""
        return [
            obs for obs in self.observations
            if obs.confidence > 0.6 or obs.anomalies
        ]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get Watson's observation statistics."""
        return {
            "total_observations": len(self.observations),
            "anomaly_observations": sum(1 for obs in self.observations if obs.anomalies),
            "high_confidence": sum(1 for obs in self.observations if obs.confidence > 0.7),
            "brain_attic_stats": self.brain_attic.get_statistics(),
            "mind_palace_stats": self.mind_palace.get_statistics()
        }


# ==============================================================================
# CLI Interface (Backward Compatible with Original)
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(description="Watson Perception Agent (Enhanced)")
    parser.add_argument("--action", required=True, choices=["chunk", "ingest", "observe", "stats"])
    parser.add_argument("--input", required=True)
    parser.add_argument("--output")
    parser.add_argument("--db")
    parser.add_argument("--context", help="Path to research context JSON")
    parser.add_argument("--session-id", help="Correlation ID for the session")
    parser.add_argument("--observation-level", choices=["seeing", "observing", "deep_focus"], default="observing")
    args = parser.parse_args()

    # Load context if provided
    research_context = None
    if args.context and os.path.exists(args.context):
        try:
            with open(args.context, 'r') as f:
                research_context = json.load(f)
        except Exception as e:
            print(f"Failed to load context: {e}")

    # Initialize Watson with specified observation level
    obs_level = ObservationLevel(args.observation_level)
    watson = WatsonAgent(observation_level=obs_level, session_id=args.session_id)
    
    # Use log instead of print
    watson.log(f"Executing action: {args.action}")

    if args.action == "chunk":
        # Read input file and chunk it
        if os.path.isfile(args.input):
            with open(args.input, 'r') as f:
                source_code = f.read()
            chunks = watson.chunk_code(source_code, args.input)
        else:
            # Mock for directory input
            chunks = [
                {"id": "chunk_1", "type": "ContractDefinition", "content": "contract Foo {...}"},
                {"id": "chunk_2", "type": "FunctionDefinition", "content": "function bar() {...}"}
            ]
        
        data = {
            "chunks": chunks,
            "metadata": {
                "perception_level": "fine-grained",
                "observation_mode": args.observation_level
            }
        }
        
        if args.output:
            with open(args.output, "w") as f:
                json.dump(data, f, indent=2)
            watson.log(f"Generated {len(chunks)} semantic chunks at {args.output}")
        else:
            print(json.dumps(data, indent=2))

    elif args.action == "ingest":
        # Load chunks and observe them
        with open(args.input, 'r') as f:
            data = json.load(f)
        
        chunks = data.get("chunks", [])
        observation_set = watson.scan_codebase(chunks, research_context=research_context)
        
        watson.log(f"Ingested and observed {observation_set.total_chunks_observed} chunks")
        watson.log(f"Found {observation_set.anomaly_count} anomalies")
        
        # In a real system we would rely on the EventBus for downstream,
        # but for compatibility with current orchestrator we also output the Result Set
        result_payload = {
            "observations": watson.export_observations(),
            "counts": watson.get_statistics()
        }
        
        if args.output:
            with open(args.output, "w") as f:
                json.dump(result_payload, f, indent=2)
    
    elif args.action == "observe":
        # Direct observation of a code file OR directory
        all_observations = []
        all_signals = []
        all_anomalies = []
        
        if os.path.isdir(args.input):
            # Scan directory for .sol files
            watson.log(f"Scanning directory: {args.input}")
            sol_files = []
            for root, dirs, files in os.walk(args.input):
                for file in files:
                    if file.endswith('.sol'):
                        sol_files.append(os.path.join(root, file))
            
            watson.log(f"Found {len(sol_files)} Solidity files")
            
            for sol_file in sol_files:
                try:
                    with open(sol_file, 'r') as f:
                        code = f.read()
                    observation = watson.observe(code, sol_file, force_deep=True)
                    all_observations.append(observation.to_dict())
                    all_signals.extend(observation.signals)
                    all_anomalies.extend(observation.anomalies)
                    watson.log(f"Observed: {os.path.basename(sol_file)} - {len(observation.signals)} signals, {len(observation.anomalies)} anomalies")
                except Exception as e:
                    watson.log(f"Error observing {sol_file}: {e}")
        else:
            # Single file
            with open(args.input, 'r') as f:
                code = f.read()
            
            observation = watson.observe(code, args.input, force_deep=True)
            all_observations.append(observation.to_dict())
            all_signals = observation.signals
            all_anomalies = observation.anomalies
        
        result = {
            "success": True,
            "observations": all_observations,
            "signals": all_signals,
            "anomalies": all_anomalies,
            "summary": {
                "files_observed": len(all_observations),
                "total_signals": len(all_signals),
                "total_anomalies": len(all_anomalies)
            }
        }
        
        watson.log(f"Observation complete: {len(all_observations)} files, {len(all_signals)} signals, {len(all_anomalies)} anomalies")
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2)
        else:
            print(json.dumps(result, indent=2))
    
    elif args.action == "stats":
        print(json.dumps(watson.get_statistics(), indent=2))


if __name__ == "__main__":
    main()
