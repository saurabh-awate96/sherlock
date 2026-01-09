"""
Universal Orchestrator: The Cognitive Control Plane
=====================================================

The single polymorphic entry point for intent-driven autonomous orchestration.

"The Universal Orchestrator functions as a Meta-Agent. It does not perform 
the reconnaissance or the exploitation itself; rather, it acts as the 
cognitive control plane."

This is THE CORE - implementing:
- OODA Loop: Observe → Orient → Decide → Act (continuous)
- Intent-Based Routing: Natural language → capability mapping
- Dynamic Capability Discovery: Runtime introspection
- Self-Calibration: Meta-learning and parameter tuning
- Feedback Integration: Probabilistic belief updating
- **Architectural Resilience**: EventBus integration, Audit Log, Logical Clocks
- **Streaming Thinking**: Real-time agent status visualization (Claude-style)
"""

import os
import sys
import json
import hashlib
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Callable, Tuple
from datetime import datetime
from enum import Enum
import subprocess
import shlex
import tempfile
import threading
import time

try:
    from rich.console import Console
    from rich.live import Live
    from rich.spinner import Spinner
    from rich.text import Text
    from rich.panel import Panel
    from rich.layout import Layout
    from rich.style import Style
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Warning: 'rich' library not found. Falling back to standard output.")

# Import orchestrator components
try:
    from module_registry import ModuleRegistry, ModuleCapability, ModuleType, Tool, CostProfile
    from context_manager import ContextManager, WorldModel, Finding, RiskTolerance
    from intent_engine import IntentRecognitionEngine, IntentClassification, IntentCategory
    from probabilistic_router import ProbabilisticRouter, RoutingDecision
    from architectural_core import global_bus, global_clock, CryptographicAuditLog, EventType, global_performance
except ImportError:
    from agents.module_registry import ModuleRegistry, ModuleCapability, ModuleType, Tool, CostProfile
    from agents.context_manager import ContextManager, WorldModel, Finding, RiskTolerance
    from agents.intent_engine import IntentRecognitionEngine, IntentClassification, IntentCategory
    from agents.probabilistic_router import ProbabilisticRouter, RoutingDecision
    from agents.architectural_core import global_bus, global_clock, CryptographicAuditLog, EventType, global_performance


# ==============================================================================
# OODA Phase Definitions
# ==============================================================================

class OODAPhase(Enum):
    """Phases of the OODA loop."""
    OBSERVE = "observe"     # Data ingestion
    ORIENT = "orient"       # Contextualization
    DECIDE = "decide"       # Planning
    ACT = "act"             # Execution
    REFLECT = "reflect"     # Meta-cognitive feedback


# ==============================================================================
# Data Structures
# ==============================================================================

@dataclass
class Plan:
    """A plan generated during the DECIDE phase."""
    action: str                          # The action to take
    module_id: Optional[str] = None      # Target module
    task: Dict[str, Any] = field(default_factory=dict)
    reasoning: str = ""
    confidence: float = 0.5
    alternatives: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class OODAState:
    """State maintained across OODA iterations."""
    phase: OODAPhase
    iteration: int
    observations: List[Dict[str, Any]]
    oriented_state: Dict[str, Any]
    current_plan: Optional[Plan]
    last_action_result: Optional[Dict[str, Any]]
    
    # Feedback for learning
    actions_taken: List[Dict[str, Any]] = field(default_factory=list)
    accumulated_findings: List[Finding] = field(default_factory=list)


@dataclass
class OrchestratorResult:
    """Final result of an orchestration run."""
    session_id: str
    intent: str
    status: str
    cycles_completed: int
    
    findings: List[Dict[str, Any]]
    observations: List[str]
    actions_taken: List[Dict[str, Any]]
    
    execution_time_ms: float
    final_report: Dict[str, Any]


class PolicyViolation(Exception):
    """Raised when an action violates safety policies."""
    def __init__(self, reason: str, constraint: str):
        self.reason = reason
        self.constraint = constraint
        super().__init__(f"Policy Violation: {reason} ({constraint})")


# ==============================================================================
# Neuro-Symbolic Planner
# ==============================================================================

class NeuroSymbolicPlanner:
    """
    Hybrid reasoning for planning - Neural + Symbolic.
    
    "Pure LLM-based logic is prone to hallucination. The Logic module 
    employs a Neuro-Symbolic Architecture."
    
    - Neural Layer (System 1): Pattern recognition, fast heuristics
    - Symbolic Layer (System 2): Rule verification, constraint checking
    """
    
    # Symbolic rules for plan verification
    # Risk level mapping for comparison
    RISK_LEVELS = {"low": 1, "medium": 2, "high": 3, "critical": 4}
    
    SAFETY_RULES = {
        "scope_check": lambda plan, ctx: ctx.get("scope", "*") != "*" or plan.get("target", "").startswith(ctx.get("scope", "*").replace("*", "")),
        "risk_check": lambda plan, ctx: NeuroSymbolicPlanner.RISK_LEVELS.get(str(plan.get("risk", "low")).lower(), 1) <= NeuroSymbolicPlanner.RISK_LEVELS.get(str(ctx.get("risk_tolerance", "medium")).lower(), 2),
    }
    
    # Action templates by intent category
    ACTION_TEMPLATES = {
        IntentCategory.RECONNAISSANCE: [
            {"action": "research", "module_type": "reconnaissance"},
            {"action": "observe", "module_type": "reconnaissance"},
            {"action": "scan", "module_type": "reconnaissance"},
            {"action": "enumerate", "module_type": "reconnaissance"}
        ],
        IntentCategory.VULNERABILITY_ASSESSMENT: [
            {"action": "analyze", "module_type": "logic"},
            {"action": "detect", "module_type": "logic"},
            {"action": "assess", "module_type": "logic"}
        ],
        IntentCategory.EXPLOITATION: [
            {"action": "exploit", "module_type": "vulnerability"},
            {"action": "verify", "module_type": "vulnerability"}
        ],
        IntentCategory.REPORTING: [
            {"action": "synthesize", "module_type": "synthesis"},
            {"action": "report", "module_type": "synthesis"}
        ],
        IntentCategory.ANALYSIS: [
            {"action": "research", "module_type": "reconnaissance"},
            {"action": "investigate", "module_type": "reconnaissance"},
            {"action": "analyze", "module_type": "logic"}
        ],
        IntentCategory.DISCOVERY: [
            {"action": "observe", "module_type": "reconnaissance"},
            {"action": "research", "module_type": "reconnaissance"},
            {"action": "discover", "module_type": "reconnaissance"}
        ]
    }
    
    def __init__(self):
        """Initialize the Neuro-Symbolic Planner."""
        self.constraint_violations: List[Dict[str, Any]] = []
        print("[Planner] Neuro-Symbolic Planner initialized")
    
    def orient(
        self,
        world_model: WorldModel,
        observations: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        ORIENT phase: Fuse observations into coherent world model.
        """
        # Fuse observations into world model
        for obs in observations:
            # Handle both raw dicts and event dicts
            data = obs.get("data", obs) if "data" in obs else obs
            
            if "services" in data:
                world_model.discovered_services.extend(data["services"])
            if "vulnerabilities" in data:
                world_model.identified_vulnerabilities.extend(data["vulnerabilities"])
            if "constraints" in data:
                world_model.environmental_constraints.extend(data["constraints"])
            
            # If it's a finding, add it to vulnerabilities
            if obs.get("type", "") == "finding":
                world_model.identified_vulnerabilities.append(data)

        # Deduplicate
        try:
            world_model.discovered_services = list({
                json.dumps(s, sort_keys=True): s 
                for s in world_model.discovered_services
            }.values())
        except:
            pass # Skip dedupe if not serializable
        
        # Calculate risk assessment
        vuln_count = len(world_model.identified_vulnerabilities)
        critical_count = sum(
            1 for v in world_model.identified_vulnerabilities
            if isinstance(v, dict) and v.get("severity", "").upper() == "CRITICAL"
        )
        world_model.risk_assessment = min(1.0, (vuln_count * 0.1) + (critical_count * 0.3))
        
        return {
            "world_model": world_model,
            "services_count": len(world_model.discovered_services),
            "vulnerabilities_count": vuln_count,
            "risk_level": world_model.risk_assessment,
            "constraints": world_model.environmental_constraints
        }
    
    def derive_next_step(
        self,
        oriented_state: Dict[str, Any],
        intent: IntentClassification,
        iteration: int
    ) -> Plan:
        """
        DECIDE phase: Generate the next action plan.
        
        Phase progression (Holmesian Cognitive Loop):
        - Iteration 0: Research (Irene) - Deep dive into protocol/context
        - Iteration 1-2: Reconnaissance (Watson) - Observe codebase with research context
        - Iteration 3-5: Analysis (Sherlock) - Deduce vulnerabilities from observations
        - Iteration 6-7: Exploitation (Moriarty) - Verify findings with PoCs
        - Iteration 8+: Synthesis (Mycroft) - Generate final report
        """
        world_model = oriented_state.get("world_model")
        risk_level = oriented_state.get("risk_level", 0)
        observations_count = len(world_model.discovered_services) if world_model else 0
        vulnerabilities_count = oriented_state.get("vulnerabilities_count", 0)
        
        # Phase-based progression (Irene → Watson → Sherlock → Moriarty → Mycroft)
        if iteration == 0:
            # Phase 0: Research - Irene investigates the protocol
            selected = {"action": "research", "module_type": "reconnaissance", "module_id": "irene"}
            reasoning = "Phase 0: Irene performing deep research on target protocol"
            
        elif iteration <= 2:
            # Phase 1: Reconnaissance - Watson observes the codebase
            selected = {"action": "observe", "module_type": "reconnaissance", "module_id": "watson"}
            reasoning = "Phase 1: Watson observing codebase with research context"
            
        elif iteration <= 5:
            # Phase 2: Analysis - Sherlock deduces vulnerabilities
            selected = {"action": "detect", "module_type": "logic", "module_id": "sherlock"}
            reasoning = f"Phase 2: Sherlock analyzing observations (found {observations_count} services)"
                
        elif iteration <= 7:
            # Phase 3: Exploitation - Moriarty verifies with PoCs
            if vulnerabilities_count > 0 or risk_level > 0.3:
                selected = {"action": "exploit", "module_type": "vulnerability", "module_id": "moriarty"}
                reasoning = f"Phase 3: Moriarty exploiting {vulnerabilities_count} vulnerabilities"
            else:
                selected = {"action": "detect", "module_type": "logic", "module_id": "sherlock"}
                reasoning = "Phase 3: Additional Sherlock analysis"
                
        else:
            # Phase 4: Synthesis - Done
            selected = {"action": "TERMINATE", "module_type": "synthesis", "module_id": None}
            reasoning = f"Phase 4: Audit complete after {iteration} iterations"
        
        plan = Plan(
            action=selected["action"],
            module_id=selected.get("module_id"),  # Explicit module assignment
            task={
                "type": selected["action"],
                "intent": intent.intent.value,
                "module_type": selected["module_type"],
                "iteration": iteration,
                "observations_count": observations_count,
                "vulnerabilities_count": vulnerabilities_count,
                "target_module": selected.get("module_id")  # For routing
            },
            reasoning=reasoning,
            confidence=intent.confidence
        )
        
        return plan
    
    def verify_plan(self, plan: Plan, context: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Symbolic Layer: Verify plan against safety rules.
        """
        for rule_name, rule_fn in self.SAFETY_RULES.items():
            try:
                if not rule_fn(plan.task, context):
                    return False, f"Rule violation: {rule_name}"
            except Exception as e:
                print(f"[Planner] Rule check error: {e}")
        
        return True, None
    
    def record_constraint(self, session_id: str, violation: PolicyViolation):
        """Record a constraint violation for learning."""
        self.constraint_violations.append({
            "session_id": session_id,
            "reason": violation.reason,
            "constraint": violation.constraint,
            "timestamp": datetime.now().isoformat()
        })


# ==============================================================================
# Self-Calibration Engine
# ==============================================================================

class SelfCalibrationEngine:
    """
    Meta-learning and runtime adaptation.
    """
    
    def __init__(self):
        """Initialize self-calibration."""
        self.parameters = {
            "concurrency_limit": 5,
            "timeout_threshold": 30.0,
            "rate_limit": 10.0,
            "stealth_mode": False
        }
        self.calibration_history: List[Dict[str, Any]] = []
        print("[Calibration] Self-calibration engine initialized")
    
    def calibrate(self, environment_signals: Dict[str, Any]):
        """
        Calibrate parameters based on environmental signals.
        """
        calibrations = []
        
        # Latency adaptation
        latency = environment_signals.get("latency", 0)
        if latency > 1000:  # High latency
            self.parameters["concurrency_limit"] = max(1, self.parameters["concurrency_limit"] - 1)
            self.parameters["timeout_threshold"] *= 1.5
            calibrations.append(f"Reduced concurrency due to high latency ({latency}ms)")
        
        # Error rate adaptation
        error_rate = environment_signals.get("error_rate", 0)
        if error_rate > 0.3:  # High error rate
            self.parameters["rate_limit"] *= 0.5
            calibrations.append(f"Reduced rate limit due to high errors ({error_rate:.0%})")
        
        # Detection risk adaptation  
        detection_risk = environment_signals.get("detection_risk", 0)
        if detection_risk > 0.6:
            self.parameters["stealth_mode"] = True
            self.parameters["rate_limit"] = min(self.parameters["rate_limit"], 1.0)
            calibrations.append(f"Enabled stealth mode due to detection risk ({detection_risk:.0%})")
        
        if calibrations:
            self.calibration_history.append({
                "timestamp": datetime.now().isoformat(),
                "signals": environment_signals,
                "calibrations": calibrations,
                "new_params": self.parameters.copy()
            })
            print(f"[Calibration] {'; '.join(calibrations)}")
    
    def get_parameters(self) -> Dict[str, Any]:
        """Get current calibrated parameters."""
        return self.parameters.copy()


# ==============================================================================
# Meta-Cognitive Watchdog
# ==============================================================================

class MetaCognitiveWatchdog:
    """
    Detects limit cycles and forces exploration.
    """
    
    def __init__(self, cycle_threshold: int = 3):
        """Initialize watchdog."""
        self.cycle_threshold = cycle_threshold
        self.action_history: List[str] = []
    
    def record_action(self, action: str, result_hash: str):
        """Record an action for cycle detection."""
        self.action_history.append(f"{action}:{result_hash}")
        
        # Keep limited history
        if len(self.action_history) > 20:
            self.action_history = self.action_history[-20:]
    
    def detect_cycle(self) -> bool:
        """Check if we're in a limit cycle."""
        if len(self.action_history) < self.cycle_threshold * 2:
            return False
        
        # Look for repeating patterns
        recent = self.action_history[-self.cycle_threshold:]
        pattern = ":".join(recent)
        
        # Check if this pattern repeated before
        history_str = ":".join(self.action_history[:-self.cycle_threshold])
        
        return pattern in history_str
    
    def should_interrupt(self) -> bool:
        """Should we interrupt the current strategy?"""
        return self.detect_cycle()


# ==============================================================================
# Universal Orchestrator
# ==============================================================================

class UniversalOrchestrator:
    """
    THE UNIVERSAL CALLING FUNCTION
    
    The cognitive control plane that orchestrates autonomous security
    assessment through intent-driven, probabilistic routing.
    """
    
    # Maximum OODA iterations before forced termination
    MAX_ITERATIONS = 50
    
    # Termination signals
    TERMINATION_SIGNALS = ["TERMINATE", "COMPLETE", "ABORT"]
    
    def __init__(self):
        """Initialize the Universal Orchestrator."""
        # Core components
        self.registry = ModuleRegistry(auto_discover=False)
        self.context = ContextManager()
        self.planner = NeuroSymbolicPlanner()
        self.router = ProbabilisticRouter()
        self.intent_engine = IntentRecognitionEngine()
        
        # Self-calibration
        self.calibration = SelfCalibrationEngine()
        self.watchdog = MetaCognitiveWatchdog()
        
        # Architectural Resilience Components
        try:
            self.audit_log = CryptographicAuditLog("secure_audit.log")
            global_bus.set_audit_log(self.audit_log)
            print("[Orchestrator] Secure Audit Log initialized")
        except Exception as e:
            print(f"[Orchestrator] Warning: Failed to init Secure Audit Log: {e}")
            self.audit_log = None
        
        # State
        self.current_session: Optional[str] = None
        self.current_state: Optional[OODAState] = None
        
        # Console for Rich UI
        if RICH_AVAILABLE:
            self.console = Console()
        
        print("[Orchestrator] Universal Orchestrator initialized")
        print("[Orchestrator] 'From software that works to software that thinks.'")
    
    # --------------------------------------------------------------------------
    # Main Entry Point
    # --------------------------------------------------------------------------
    
    def execute(
        self,
        intent: str,
        scope: str = "*",
        risk_tolerance: str = "medium",
        timeout: int = 3600,
        **kwargs
    ) -> OrchestratorResult:
        """
        THE UNIVERSAL CALLING FUNCTION.
        """
        start_time = datetime.now()
        
        # 0. Log Intent via Event Bus
        global_bus.publish(
            EventType.SYSTEM.value,
            "Orchestrator",
            {"event": "EXECUTE_START", "intent": intent, "scope": scope},
            correlation_id="initialization"
        )
        
        print(f"\n{'='*60}")
        print(f"[Orchestrator] EXECUTE: {intent}")
        print(f"[Orchestrator] Scope: {scope}, Risk: {risk_tolerance}")
        print(f"{'='*60}\n")
        
        # 1. Initialize Context
        session_id = self.context.create_session(intent, {
            "scope": scope,
            "risk_tolerance": risk_tolerance,
            "timeout": timeout,
            **kwargs
        })
        self.current_session = session_id
        
        # 2. Classify Intent
        intent_classification = self.intent_engine.classify(intent)
        print(f"[Orchestrator] Intent: {intent_classification.intent.value} "
              f"(confidence: {intent_classification.confidence:.2f})")
        
        # 3. Discovery (Introspection)
        capabilities = self._discover_capabilities()
        print(f"[Orchestrator] Discovered {len(capabilities)} modules")
        
        # 4. Initialize OODA State
        self.current_state = OODAState(
            phase=OODAPhase.OBSERVE,
            iteration=0,
            observations=[],
            oriented_state={},
            current_plan=None,
            last_action_result=None
        )
        
        # 5. Main OODA Loop
        try:
            while not self.context.is_goal_met(session_id):
                # Check iteration limit
                if self.current_state.iteration >= self.MAX_ITERATIONS:
                    print(f"[Orchestrator] Max iterations ({self.MAX_ITERATIONS}) reached")
                    break
                
                # Check for limit cycles
                if self.watchdog.should_interrupt():
                    print("[Orchestrator] Limit cycle detected - forcing exploration")
                    # Force a different approach
                    self.calibration.calibrate({"error_rate": 0.5})
                
                # Execute OODA cycle
                self._execute_ooda_cycle(
                    session_id,
                    intent_classification,
                    capabilities
                )
                
                self.current_state.iteration += 1
                
        except PolicyViolation as e:
            print(f"[Orchestrator] Policy violation: {e}")
            self.planner.record_constraint(session_id, e)
        except Exception as e:
            print(f"[Orchestrator] Error: {e}")
            import traceback
            traceback.print_exc()
        
        # 6. Generate Final Report
        report = self.context.generate_report(session_id)
        
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        
        result = OrchestratorResult(
            session_id=session_id,
            intent=intent,
            status="completed" if self.context.is_goal_met(session_id) else "incomplete",
            cycles_completed=self.current_state.iteration,
            findings=report.get("findings", []),
            observations=report.get("observations", []),
            actions_taken=self.current_state.actions_taken,
            execution_time_ms=execution_time,
            final_report=report
        )
        
        global_bus.publish(
            EventType.SYSTEM.value,
            "Orchestrator",
            {"event": "EXECUTE_COMPLETE", "status": result.status},
            correlation_id=session_id
        )

        print(f"\n{'='*60}")
        print(f"[Orchestrator] COMPLETE: {result.status}")
        print(f"[Orchestrator] Cycles: {result.cycles_completed}, "
              f"Findings: {len(result.findings)}")
        print(f"{'='*60}\n")
        
        return result
    
    # --------------------------------------------------------------------------
    # OODA Cycle Implementation
    # --------------------------------------------------------------------------
    
    def _execute_ooda_cycle(
        self,
        session_id: str,
        intent: IntentClassification,
        capabilities: Dict[str, ModuleCapability]
    ):
        """Execute one complete OODA cycle."""
        
        # OBSERVE
        self.current_state.phase = OODAPhase.OBSERVE
        observations = self._observe(session_id)
        self.current_state.observations.extend(observations)
        
        # ORIENT
        self.current_state.phase = OODAPhase.ORIENT
        world_model = self.context.get_world_model(session_id)
        oriented_state = self.planner.orient(
            world_model,
            observations,
            self.context.get_session(session_id).durable.__dict__
        )
        self.current_state.oriented_state = oriented_state
        
        # DECIDE
        self.current_state.phase = OODAPhase.DECIDE
        plan = self.planner.derive_next_step(
            oriented_state,
            intent,
            self.current_state.iteration
        )
        
        # Check for termination
        if plan.action in self.TERMINATION_SIGNALS:
            self.context.mark_goal_complete(session_id)
            return
        
        # Verify plan with symbolic layer
        is_valid, error = self.planner.verify_plan(
            plan,
            self.context.get_session(session_id).durable.__dict__
        )
        
        if not is_valid:
            raise PolicyViolation(error, plan.action)
        
        self.current_state.current_plan = plan
        
        # ACT
        self.current_state.phase = OODAPhase.ACT
        result = self._act(session_id, plan, capabilities)
        self.current_state.last_action_result = result
        
        # REFLECT (optional meta-cognitive step)
        self.current_state.phase = OODAPhase.REFLECT
        self._reflect(session_id, plan, result)
    
    def _observe(self, session_id: str) -> List[Dict[str, Any]]:
        """
        OBSERVE phase: Ingest data from environment and modules.
        """
        observations = []
        
        # Get any pending module outputs
        if self.current_state.last_action_result:
            result = self.current_state.last_action_result
            
            if "observations" in result:
                for obs in result["observations"]:
                    observations.append({"type": "observation", "data": obs})
            
            if "findings" in result:
                observations.append({
                    "type": "findings",
                    "data": result["findings"]
                })
        
        return observations
    
    def _act(
        self,
        session_id: str,
        plan: Plan,
        capabilities: Dict[str, ModuleCapability]
    ) -> Dict[str, Any]:
        """
        ACT phase: Execute the plan using probabilistic routing.
        """
        # Route to best module
        ctx = self.context.get_session(session_id)
        
        # Check if plan has explicit module assignment (cognitive loop phases)
        if plan.module_id and plan.module_id in capabilities:
            selected_module = plan.module_id
            utility_score = 1.0  # Direct assignment = max utility
            print(f"[Orchestrator] ACT: {plan.action} → {selected_module} (direct assignment)")
        else:
            # Fall back to probabilistic routing
            routing_decision = self.router.select_module(
                plan.task,
                capabilities,
                {"risk_tolerance": ctx.durable.risk_tolerance.value}
            )
            selected_module = routing_decision.selected_module
            utility_score = routing_decision.utility_score
            print(f"[Orchestrator] ACT: {plan.action} → {selected_module} "
                  f"(utility: {utility_score:.3f})")
        
        # Prepare payload with context baggage
        payload = self.context.prepare_payload(plan.task, session_id)
        
        # Execute module
        result = self._execute_module(
            selected_module,
            plan,
            payload,
            session_id
        )
        
        # Record action
        action_record = {
            "action": plan.action,
            "module": selected_module,
            "iteration": self.current_state.iteration,
            "success": result.get("success", False),
            "timestamp": datetime.now().isoformat()
        }
        self.current_state.actions_taken.append(action_record)
        
        # Update context with result
        self.context.update_state(session_id, result)
        
        # Capture module-specific outputs into current_state
        if selected_module == "watson" and result.get("success", False):
            # Watson outputs observations - capture them for Sherlock
            obs_data = result.get("observations", [])
            if obs_data:
                self.current_state.observations.extend(obs_data)
            # Also capture signals and anomalies directly
            signals = result.get("signals", [])
            anomalies = result.get("anomalies", [])
            if signals:
                self.current_state.observations.extend([{"type": "signal", "data": s} for s in signals])
            if anomalies:
                self.current_state.observations.extend([{"type": "anomaly", "data": a} for a in anomalies])
        elif selected_module == "sherlock" and result.get("success", False):
            # Sherlock outputs findings - capture them
            findings_data = result.get("findings", result.get("data", []))
            if findings_data:
                self.current_state.accumulated_findings.extend(findings_data)
        
        # Record for learning
        self.router.record_execution(
            module_id=selected_module,
            task=plan.task,
            context={},
            success=result.get("success", False)
        )
        
        # Record for watchdog
        result_hash = hashlib.md5(str(result).encode()).hexdigest()[:8]
        self.watchdog.record_action(plan.action, result_hash)
        
        return result
    
    def _execute_module(
        self,
        module_id: str,
        plan: Plan,
        payload: Any,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Execute a module (Agent) as a subprocess with Real-Time Streaming (Claude-style).
        """
        # Fallback if rich is not available
        if not RICH_AVAILABLE:
            return self._execute_module_legacy(module_id, plan, payload, session_id)

        print(f"[Orchestrator] Executing Agent: {module_id}")
        
        script_path = os.path.join(os.path.dirname(__file__), f"{module_id}.py")
        if not os.path.exists(script_path):
            return {"success": False, "error": f"Module script not found: {script_path}"}
            
        # Determine inputs based on module type
        is_temp_input = False
        input_path = ""
        
        # Get session context for scope/research
        session = self.context.get_session(session_id)
        scope = session.durable.scope
        # Safely get research context if it exists
        research_context = session.durable.__dict__.get("research_context", None)
        research_path = "" 
        
        # Create temp output file
        fd, output_path = tempfile.mkstemp(suffix=".json", prefix=f"{module_id}_out_")
        os.close(fd)
        
        try:
            cmd = ["python3", script_path, "--output", output_path]
            
            # Pass session ID for correlation
            cmd.extend(["--session-id", session_id])
            
            # --- WATSON ---
            if module_id == "watson":
                cmd.extend(["--action", "observe"])
                cmd.extend(["--input", scope]) 
                # Pass research context if available
                # In a real impl, we'd pass the file path or dump it to a temp file
                if research_context:
                    # Write research context to temp file
                    fd_ctx, ctx_path = tempfile.mkstemp(suffix=".json", prefix="research_context_")
                    os.write(fd_ctx, json.dumps(research_context).encode())
                    os.close(fd_ctx)
                    cmd.extend(["--context", ctx_path])
                    is_temp_input = True # Ensure cleanup
                
            # --- SHERLOCK ---
            elif module_id == "sherlock":
                cmd.extend(["--action", "detect"])
                # Sherlock needs observations
                # Dump current observations to temp file
                is_temp_input = True
                fd_in, input_path = tempfile.mkstemp(suffix=".json", prefix="sherlock_in_")
                # Wrap in dict as expected by Sherlock
                sherlock_input = {"observations": self.current_state.observations}
                os.write(fd_in, json.dumps(sherlock_input).encode())
                os.close(fd_in)
                cmd.extend(["--input", input_path])
                
            # --- MORIARTY ---
            elif module_id == "moriarty":
                cmd.extend(["--action", "exploit"])
                # Moriarty needs findings
                world_model = self.context.get_world_model(session_id)
                findings = [f.__dict__ if hasattr(f, "__dict__") else f for f in world_model.identified_vulnerabilities]
                
                is_temp_input = True
                fd_in, input_path = tempfile.mkstemp(suffix=".json", prefix="moriarty_in_")
                moriarty_input = {"findings": findings}
                os.write(fd_in, json.dumps(moriarty_input).encode())
                os.close(fd_in)
                cmd.extend(["--input", input_path])
                cmd.extend(["--output-dir", "exploits"])
                
            # --- IRENE ---
            elif module_id == "irene":
                # Research module - Irene performs deep research on the target
                cmd = ["python3", os.path.join(os.path.dirname(__file__), "irene.py")]
                cmd.extend(["--action", "research"])
                cmd.extend(["--output", output_path])
                
                # Create input file with intent and scope
                is_temp_input = True
                fd_in, input_path = tempfile.mkstemp(suffix=".json", prefix="irene_in_")
                irene_input = {
                    "intent": session.durable.intent if hasattr(session.durable, 'intent') else "Security Audit",
                    "scope": scope
                }
                os.write(fd_in, json.dumps(irene_input).encode())
                os.close(fd_in)
                cmd.extend(["--input", input_path])
                
            # --- DEFAULT/FALLBACK ---
            else:
                 cmd.extend(["--action", plan.action])
                 cmd.extend(["--input", scope])

            # ==================================================================
            # CLAUDE-STYLE STREAMING EXECUTION
            # ==================================================================
            
            agent_color_map = {
                "watson": "blue",
                "sherlock": "green",
                "moriarty": "red"
            }
            color = agent_color_map.get(module_id, "white")
            
            # Start subprocess with buffered output
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1  # Line buffered
            )
            
            # Live UI Loop
            panel_content = Text(f"Initializing {module_id}...", style=color)
            spinner = Spinner("dots", text=panel_content)
            
            with Live(Panel(spinner, title=f"Agent: {module_id.capitalize()}", border_style=color), refresh_per_second=10) as live:
                while True:
                    # Read line from stdout
                    output_line = process.stdout.readline()
                    
                    if output_line == '' and process.poll() is not None:
                        break
                        
                    if output_line:
                        output_line = output_line.strip()
                        if not output_line: continue
                        
                        # Update Spinner Text 
                        # Only show lines starting with [AgentName] to avoid noise
                        if output_line.startswith("["):
                            panel_content = Text(output_line, style=color)
                            spinner.text = panel_content
                        else:
                            # Log other lines to raw output or ignore
                            pass
                            
            # Check exit code
            if process.returncode != 0:
                stderr_out = process.stderr.read()
                print(f"[Orchestrator] Module execution failed: {stderr_out}")
                return {"success": False, "error": stderr_out}
            
            # Read output
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                with open(output_path, 'r') as f:
                    module_output = json.load(f)
                
                # Wrap list output if necessary
                if isinstance(module_output, list):
                    return {"success": True, "data": module_output, "findings": module_output}
                return module_output
            else:
                return {"success": False, "error": "No output generated", "stdout": ""}
                
        except Exception as e:
            print(f"[Orchestrator] Exception executing module: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}
            
        finally:
            # Cleanup temp files
            if os.path.exists(output_path):
                try: os.unlink(output_path)
                except: pass
            if is_temp_input and input_path and os.path.exists(input_path):
                try: os.unlink(input_path)
                except: pass

    def _execute_module_legacy(
        self,
        module_id: str,
        plan: Plan,
        payload: Any,
        session_id: str
    ) -> Dict[str, Any]:
        """Legacy execution without streaming (original implementation)."""
        # ... (Duplicate of original logic for fallback) or just panic
        # For brevity in this artifact, we assume user has rich installed as verified.
        # But to be safe, we'll just replicate the minimal logic if needed or raise error.
        print("Legacy mode execution not implemented in this snippet.")
        return {"success": False, "error": "Rich required for this versions"}
    
    def _discover_capabilities(self) -> Dict[str, ModuleCapability]:
        """Discover available modules."""
        # Hardcoded registration matching module_registry.py definitions
        
        # Watson
        watson_tool = Tool(
            name="observe",
            description="Analyze codebase and extract security observations",
            intent_tags=[IntentCategory.RECONNAISSANCE.value, "audit", "scan"],
            input_schema={"scope": "path"},
            output_schema={"observations": "list"}
        )
        watson_cap = ModuleCapability(
            module_id="watson",
            module_type=ModuleType.RECONNAISSANCE,
            version="1.0.0",
            tools=[watson_tool],
            intent_tags=[IntentCategory.RECONNAISSANCE.value, IntentCategory.DISCOVERY.value, "observe", "scan", "investigate", "audit"],
            cost_profile=CostProfile(latency="high", compute="high", risk="low")
        )

        # Sherlock
        sherlock_tool = Tool(
            name="detect",
            description="Deduce vulnerabilities from observations",
            intent_tags=[IntentCategory.VULNERABILITY_ASSESSMENT.value, "analyze"],
            input_schema={"observations": "list"},
            output_schema={"findings": "list"}
        )
        sherlock_cap = ModuleCapability(
            module_id="sherlock",
            module_type=ModuleType.LOGIC,
            version="1.0.0",
            tools=[sherlock_tool],
            intent_tags=[IntentCategory.VULNERABILITY_ASSESSMENT.value, IntentCategory.ANALYSIS.value, "detect", "analyze", "assess"],
            cost_profile=CostProfile(latency="medium", compute="high", risk="low")
        )

        # Moriarty
        moriarty_tool = Tool(
            name="exploit",
            description="Generate Proof-of-Concept exploits",
            intent_tags=[IntentCategory.EXPLOITATION.value, "poc", "attack"],
            input_schema={"findings": "list"},
            output_schema={"exploit": "file"}
        )
        moriarty_cap = ModuleCapability(
            module_id="moriarty",
            module_type=ModuleType.VULNERABILITY,
            version="1.0.0",
            tools=[moriarty_tool],
            intent_tags=[IntentCategory.EXPLOITATION.value, "exploit", "attack", "poc"],
            cost_profile=CostProfile(latency="high", compute="high", risk="high")
        )

        # Irene Adler
        irene_tool = Tool(
            name="research",
            description="Deep research on topics",
            intent_tags=[IntentCategory.RECONNAISSANCE.value, "research", "context"],
            input_schema={"query": "string"},
            output_schema={"report": "markdown"}
        )
        irene_cap = ModuleCapability(
            module_id="irene",
            module_type=ModuleType.RECONNAISSANCE,
            version="1.0.0",
            tools=[irene_tool],
            intent_tags=[IntentCategory.RECONNAISSANCE.value, "research", "investigate", "context"],
            cost_profile=CostProfile(latency="high", compute="high", risk="low")
        )

        return {
            "watson": watson_cap,
            "sherlock": sherlock_cap,
            "moriarty": moriarty_cap,
            "irene": irene_cap
        }
    
    def _reflect(self, session_id: str, plan: Plan, result: Dict[str, Any]):
        """Meta-cognitive reflection on action results."""
        pass # Placeholder for advanced meta-cognition


# ==============================================================================
# CLI Entry Point
# ==============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Universal Orchestrator CLI")
    parser.add_argument("--intent", default="Perform a comprehensive security audit of the Flying Tulip protocol", help="High-level intent")
    parser.add_argument("--scope", default="./", help="Target scope (directory or file)")
    parser.add_argument("--risk", default="medium", choices=["low", "medium", "high", "critical"], help="Risk tolerance")
    
    args = parser.parse_args()
    
    orchestrator = UniversalOrchestrator()
    orchestrator.execute(
        intent=args.intent,
        scope=args.scope,
        risk_tolerance=args.risk
    )
