"""
Universal Orchestrator: Context Manager
========================================

Tiered Context Stack for State Management without Context Bloat.

"Adaptive logic fails without context. However, passing the entire 
history of a project to every module creates 'Context Bloat.'"

This module implements:
- Durable Context (Mission): Immutable constraints
- Session Context (Narrative): Summarized history with RAG
- Working Context (Task): Current cycle I/O
- Context Propagation: W3C-style distributed tracing baggage
"""

import uuid
import hashlib
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Set
from datetime import datetime
from enum import Enum
import json


# ==============================================================================
# Data Structures
# ==============================================================================

class RiskTolerance(Enum):
    """Risk tolerance levels for operations."""
    MINIMAL = "minimal"      # Read-only, no active probing
    LOW = "low"              # Passive techniques only
    MEDIUM = "medium"        # Standard active techniques
    HIGH = "high"            # Aggressive techniques allowed
    MAXIMUM = "maximum"      # All techniques including destructive


class SessionStatus(Enum):
    """Status of an orchestration session."""
    INITIALIZING = "initializing"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETING = "completing"
    COMPLETED = "completed"
    FAILED = "failed"
    TERMINATED = "terminated"


@dataclass
class DurableContext:
    """
    The "Constitution" - Immutable constraints defined at session start.
    
    These constraints NEVER change during a session and represent
    the fundamental rules of engagement.
    """
    scope: str                          # Target scope (wildcards allowed)
    risk_tolerance: RiskTolerance       # Maximum allowed risk level
    time_limit: int                     # Seconds until timeout
    authorized_actions: Set[str]        # Whitelist of allowed action types
    prohibited_patterns: Set[str]       # Blacklist of forbidden patterns
    
    # Compliance constraints
    require_approval: bool = False      # Human approval for critical actions
    audit_trail: bool = True            # Log all actions
    
    # Resource constraints
    max_concurrent: int = 5             # Max concurrent operations
    rate_limit: float = 10.0            # Max operations per second
    
    created_at: datetime = field(default_factory=datetime.now)
    
    def allows_action(self, action_type: str) -> bool:
        """Check if action type is authorized."""
        if self.authorized_actions and action_type not in self.authorized_actions:
            return False
        return True
    
    def is_in_scope(self, target: str) -> bool:
        """Check if target is within scope."""
        import fnmatch
        return fnmatch.fnmatch(target, self.scope)


@dataclass
class Finding:
    """A finding discovered during the session."""
    id: str
    title: str
    severity: str
    description: str
    location: str
    timestamp: datetime = field(default_factory=datetime.now)
    verified: bool = False
    
    def to_summary(self) -> str:
        """Create concise summary for session context."""
        return f"[{self.severity}] {self.title} @ {self.location}"


@dataclass 
class SessionContext:
    """
    The "Narrative" - Summarized history in vector DB for RAG.
    
    This context maintains a compressed representation of what
    has been discovered and done, optimized for retrieval.
    """
    findings: List[Finding] = field(default_factory=list)
    observations: List[str] = field(default_factory=list)
    actions_taken: List[Dict[str, Any]] = field(default_factory=list)
    constraints_discovered: List[str] = field(default_factory=list)
    
    # Semantic memory (for RAG retrieval)
    memory_vectors: List[Dict[str, Any]] = field(default_factory=list)
    
    # Statistics
    total_cycles: int = 0
    successful_actions: int = 0
    failed_actions: int = 0
    
    def add_finding(self, finding: Finding):
        """Add a new finding."""
        self.findings.append(finding)
        self.memory_vectors.append({
            "type": "finding",
            "content": finding.to_summary(),
            "timestamp": finding.timestamp.isoformat()
        })
    
    def add_observation(self, observation: str):
        """Add an observation."""
        self.observations.append(observation)
        self.memory_vectors.append({
            "type": "observation",
            "content": observation,
            "timestamp": datetime.now().isoformat()
        })
    
    def add_action(self, action: Dict[str, Any], success: bool):
        """Record an action taken."""
        action["success"] = success
        action["timestamp"] = datetime.now().isoformat()
        self.actions_taken.append(action)
        
        if success:
            self.successful_actions += 1
        else:
            self.failed_actions += 1
    
    def add_constraint(self, constraint: str):
        """Record a discovered constraint (e.g., WAF detected)."""
        if constraint not in self.constraints_discovered:
            self.constraints_discovered.append(constraint)
    
    def get_summary(self, max_items: int = 10) -> Dict[str, Any]:
        """Get compressed summary for context propagation."""
        return {
            "findings_count": len(self.findings),
            "recent_findings": [f.to_summary() for f in self.findings[-max_items:]],
            "observations_count": len(self.observations),
            "recent_observations": self.observations[-max_items:],
            "constraints": self.constraints_discovered,
            "action_stats": {
                "total": len(self.actions_taken),
                "successful": self.successful_actions,
                "failed": self.failed_actions
            }
        }
    
    def query_similar(self, query: str, top_k: int = 5) -> List[Dict]:
        """RAG-style retrieval from memory vectors."""
        # Simple keyword matching (would use vector similarity in production)
        query_words = set(query.lower().split())
        
        scored = []
        for vec in self.memory_vectors:
            content_words = set(vec["content"].lower().split())
            overlap = len(query_words & content_words)
            if overlap > 0:
                scored.append((vec, overlap))
        
        scored.sort(key=lambda x: x[1], reverse=True)
        return [item[0] for item in scored[:top_k]]


@dataclass
class WorkingContext:
    """
    The "Task" - Immediate inputs/outputs of the current cycle.
    
    This is ephemeral context that exists only for the current
    OODA iteration and is cleared between cycles.
    """
    current_intent: Optional[str] = None
    current_target: Optional[str] = None
    current_plan: Optional[Dict[str, Any]] = None
    
    # Input from previous cycle
    input_data: Dict[str, Any] = field(default_factory=dict)
    
    # Output to next cycle
    output_data: Dict[str, Any] = field(default_factory=dict)
    
    # Cycle metadata
    cycle_number: int = 0
    cycle_start: Optional[datetime] = None
    
    def start_cycle(self, intent: str):
        """Start a new working cycle."""
        self.cycle_number += 1
        self.cycle_start = datetime.now()
        self.current_intent = intent
        self.input_data = self.output_data.copy()
        self.output_data = {}
    
    def end_cycle(self) -> Dict[str, Any]:
        """End current cycle and return output."""
        result = {
            "cycle": self.cycle_number,
            "intent": self.current_intent,
            "output": self.output_data,
            "duration_ms": (datetime.now() - self.cycle_start).total_seconds() * 1000
            if self.cycle_start else 0
        }
        return result


@dataclass
class ContextStack:
    """Complete context stack for a session."""
    durable: DurableContext
    session: SessionContext
    working: WorkingContext


@dataclass
class Payload:
    """Payload sent to modules with context baggage."""
    task: Dict[str, Any]
    baggage: Dict[str, Any]
    trace_id: str
    span_id: str


@dataclass
class WorldModel:
    """The current understanding of the environment."""
    target_attributes: Dict[str, Any]
    discovered_services: List[Dict[str, Any]]
    identified_vulnerabilities: List[Dict[str, Any]]
    environmental_constraints: List[str]
    risk_assessment: float
    last_updated: datetime = field(default_factory=datetime.now)


# ==============================================================================
# Context Manager
# ==============================================================================

class ContextManager:
    """
    Manages the tiered context stack for orchestration sessions.
    
    Key responsibilities:
    1. Create and manage session contexts
    2. Propagate context as "baggage" to decoupled modules
    3. Maintain world model from aggregated observations
    4. Determine when goals are met
    """
    
    def __init__(self):
        """Initialize the Context Manager."""
        self.sessions: Dict[str, ContextStack] = {}
        self.world_models: Dict[str, WorldModel] = {}
        self.goals: Dict[str, Dict[str, Any]] = {}
        self.goal_checkers: Dict[str, callable] = {}
        
        print("[ContextManager] Initialized")
    
    # --------------------------------------------------------------------------
    # Session Management
    # --------------------------------------------------------------------------
    
    def create_session(
        self,
        intent: str,
        constraints: Dict[str, Any]
    ) -> str:
        """
        Create a new orchestration session with durable context.
        
        Args:
            intent: High-level goal of the session
            constraints: Initial constraints and parameters
        
        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())
        
        # Parse risk tolerance
        risk_str = constraints.get("risk_tolerance", "medium").lower()
        try:
            risk_tolerance = RiskTolerance(risk_str)
        except ValueError:
            risk_tolerance = RiskTolerance.MEDIUM
        
        # Create durable context
        durable = DurableContext(
            scope=constraints.get("scope", "*"),
            risk_tolerance=risk_tolerance,
            time_limit=constraints.get("timeout", 3600),
            authorized_actions=set(constraints.get("authorized_actions", [])),
            prohibited_patterns=set(constraints.get("prohibited_patterns", [])),
            require_approval=constraints.get("require_approval", False),
            audit_trail=constraints.get("audit_trail", True),
            max_concurrent=constraints.get("max_concurrent", 5),
            rate_limit=constraints.get("rate_limit", 10.0)
        )
        
        # Create session context
        session = SessionContext()
        
        # Create working context
        working = WorkingContext()
        
        # Store
        self.sessions[session_id] = ContextStack(
            durable=durable,
            session=session,
            working=working
        )
        
        # Initialize world model
        self.world_models[session_id] = WorldModel(
            target_attributes={},
            discovered_services=[],
            identified_vulnerabilities=[],
            environmental_constraints=[]
        , risk_assessment=0.0)
        
        # Store goal
        self.goals[session_id] = {
            "intent": intent,
            "completed": False,
            "success_criteria": constraints.get("success_criteria", {})
        }
        
        print(f"[ContextManager] Created session {session_id[:8]}... for intent: {intent}")
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[ContextStack]:
        """Get session context stack."""
        return self.sessions.get(session_id)
    
    def close_session(self, session_id: str):
        """Close and clean up a session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
        if session_id in self.world_models:
            del self.world_models[session_id]
        if session_id in self.goals:
            del self.goals[session_id]
        
        print(f"[ContextManager] Closed session {session_id[:8]}...")
    
    # --------------------------------------------------------------------------
    # Context Propagation
    # --------------------------------------------------------------------------
    
    def prepare_payload(
        self,
        plan: Dict[str, Any],
        session_id: str
    ) -> Payload:
        """
        Prepare payload with context baggage for module invocation.
        
        This implements W3C-style distributed tracing baggage,
        ensuring decoupled modules receive necessary context.
        
        Args:
            plan: The plan/task to execute
            session_id: Session ID
        
        Returns:
            Payload with task and context baggage
        """
        ctx = self.sessions.get(session_id)
        if not ctx:
            raise ValueError(f"Unknown session: {session_id}")
        
        # Generate span ID for this operation
        span_id = hashlib.md5(
            f"{session_id}:{ctx.working.cycle_number}:{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]
        
        # Build baggage (context that travels with the request)
        baggage = {
            # Durable context (constraints)
            "scope": ctx.durable.scope,
            "risk_tolerance": ctx.durable.risk_tolerance.value,
            "authorized_actions": list(ctx.durable.authorized_actions),
            
            # Session summary
            "session_summary": ctx.session.get_summary(),
            "constraints_discovered": ctx.session.constraints_discovered,
            
            # Working context
            "cycle_number": ctx.working.cycle_number,
            "current_intent": ctx.working.current_intent,
            
            # Tracing
            "trace_id": session_id,
            "span_id": span_id,
            "parent_span_id": None  # Would chain in production
        }
        
        return Payload(
            task=plan,
            baggage=baggage,
            trace_id=session_id,
            span_id=span_id
        )
    
    # --------------------------------------------------------------------------
    # State Updates
    # --------------------------------------------------------------------------
    
    def update_state(
        self,
        session_id: str,
        result: Dict[str, Any]
    ):
        """
        Update session state based on module result.
        
        This is the OBSERVE phase feedback mechanism.
        
        Args:
            session_id: Session ID
            result: Result from module execution
        """
        ctx = self.sessions.get(session_id)
        if not ctx:
            return
        
        # Update working context
        ctx.working.output_data = result.get("data", {})
        
        # Track action
        success = result.get("success", False)
        ctx.session.add_action({
            "type": result.get("action_type", "unknown"),
            "module": result.get("module_id", "unknown"),
            "target": result.get("target", "unknown")
        }, success)
        
        # Update session context based on result type
        if "findings" in result:
            for finding_data in result["findings"]:
                finding = Finding(
                    id=finding_data.get("id", str(uuid.uuid4())),
                    title=finding_data.get("title", "Unknown"),
                    severity=finding_data.get("severity", "MEDIUM"),
                    description=finding_data.get("description", ""),
                    location=finding_data.get("location", "unknown"),
                    verified=finding_data.get("verified", False)
                )
                ctx.session.add_finding(finding)
        
        if "observations" in result:
            for obs in result["observations"]:
                ctx.session.add_observation(obs)
        
        if "constraints" in result:
            for constraint in result["constraints"]:
                ctx.session.add_constraint(constraint)
        
        # Update world model
        self._update_world_model(session_id, result)
        
        # Increment cycle
        ctx.session.total_cycles += 1
    
    def _update_world_model(self, session_id: str, result: Dict[str, Any]):
        """Update world model from result."""
        world = self.world_models.get(session_id)
        if not world:
            return
        
        # Update target attributes
        if "target_info" in result:
            world.target_attributes.update(result["target_info"])
        
        # Add discovered services
        if "services" in result:
            for service in result["services"]:
                if service not in world.discovered_services:
                    world.discovered_services.append(service)
        
        # Add vulnerabilities
        if "vulnerabilities" in result:
            for vuln in result["vulnerabilities"]:
                if vuln not in world.identified_vulnerabilities:
                    world.identified_vulnerabilities.append(vuln)
        
        # Add environmental constraints
        if "constraints" in result:
            for constraint in result["constraints"]:
                if constraint not in world.environmental_constraints:
                    world.environmental_constraints.append(constraint)
        
        world.last_updated = datetime.now()
    
    # --------------------------------------------------------------------------
    # World Model Access
    # --------------------------------------------------------------------------
    
    def get_world_model(self, session_id: str) -> Optional[WorldModel]:
        """Get current world model for session."""
        return self.world_models.get(session_id)
    
    # --------------------------------------------------------------------------
    # Goal Management
    # --------------------------------------------------------------------------
    
    def is_goal_met(self, session_id: str) -> bool:
        """
        Check if session goal has been achieved.
        
        This uses registered goal checkers or default heuristics.
        """
        goal = self.goals.get(session_id)
        if not goal:
            return True  # No goal = done
        
        if goal.get("completed"):
            return True
        
        ctx = self.sessions.get(session_id)
        if not ctx:
            return True
        
        # Check timeout
        elapsed = (datetime.now() - ctx.durable.created_at).total_seconds()
        if elapsed > ctx.durable.time_limit:
            print(f"[ContextManager] Session {session_id[:8]} timed out")
            return True
        
        # Check custom goal checker
        checker = self.goal_checkers.get(session_id)
        if checker:
            return checker(ctx, self.world_models.get(session_id))
        
        # Check success criteria
        criteria = goal.get("success_criteria", {})
        
        # Minimum findings
        if "min_findings" in criteria:
            if len(ctx.session.findings) < criteria["min_findings"]:
                return False
        
        # Minimum cycles
        if "min_cycles" in criteria:
            if ctx.session.total_cycles < criteria["min_cycles"]:
                return False
        
        # Maximum cycles (safety)
        if ctx.session.total_cycles > 100:
            print(f"[ContextManager] Session {session_id[:8]} hit max cycles")
            return True
        
        # Default: not met until explicit completion
        return goal.get("completed", False)
    
    def mark_goal_complete(self, session_id: str):
        """Explicitly mark goal as complete."""
        if session_id in self.goals:
            self.goals[session_id]["completed"] = True
    
    def register_goal_checker(
        self,
        session_id: str,
        checker: callable
    ):
        """Register custom goal completion checker."""
        self.goal_checkers[session_id] = checker
    
    # --------------------------------------------------------------------------
    # Report Generation
    # --------------------------------------------------------------------------
    
    def generate_report(self, session_id: str) -> Dict[str, Any]:
        """Generate final session report."""
        ctx = self.sessions.get(session_id)
        world = self.world_models.get(session_id)
        goal = self.goals.get(session_id)
        
        if not ctx:
            return {"error": "Session not found"}
        
        return {
            "session_id": session_id,
            "intent": goal.get("intent") if goal else "unknown",
            "status": "completed" if goal and goal.get("completed") else "incomplete",
            
            "statistics": {
                "total_cycles": ctx.session.total_cycles,
                "successful_actions": ctx.session.successful_actions,
                "failed_actions": ctx.session.failed_actions,
                "findings_count": len(ctx.session.findings),
                "observations_count": len(ctx.session.observations)
            },
            
            "findings": [
                {
                    "id": f.id,
                    "title": f.title,
                    "severity": f.severity,
                    "description": f.description,
                    "location": f.location,
                    "verified": f.verified
                }
                for f in ctx.session.findings
            ],
            
            "constraints_discovered": ctx.session.constraints_discovered,
            
            "world_model": {
                "target_attributes": world.target_attributes if world else {},
                "services_discovered": len(world.discovered_services) if world else 0,
                "vulnerabilities_identified": len(world.identified_vulnerabilities) if world else 0
            },
            
            "durable_context": {
                "scope": ctx.durable.scope,
                "risk_tolerance": ctx.durable.risk_tolerance.value,
                "time_limit": ctx.durable.time_limit
            },
            
            "generated_at": datetime.now().isoformat()
        }


# ==============================================================================
# CLI Interface
# ==============================================================================

if __name__ == "__main__":
    import json
    
    manager = ContextManager()
    
    # Create a test session
    session_id = manager.create_session(
        intent="Perform security assessment",
        constraints={
            "scope": "*.example.com",
            "risk_tolerance": "medium",
            "timeout": 3600
        }
    )
    
    print(f"\nSession ID: {session_id}")
    
    # Simulate some updates
    manager.update_state(session_id, {
        "success": True,
        "action_type": "scan",
        "module_id": "watson",
        "observations": ["Found open port 443", "TLS 1.2 enabled"],
        "findings": [
            {
                "title": "Outdated TLS",
                "severity": "MEDIUM",
                "description": "TLS 1.2 should be upgraded to 1.3",
                "location": "example.com:443"
            }
        ]
    })
    
    # Generate report
    report = manager.generate_report(session_id)
    print("\n=== Session Report ===")
    print(json.dumps(report, indent=2))
