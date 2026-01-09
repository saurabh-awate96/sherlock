"""
Universal Orchestrator: Probabilistic Router
=============================================

POMDP-Based Utility Calculation for Module Selection.

"Instead of deterministic if-then routing, it employs Probabilistic 
Routing modeled as a Partially Observable Markov Decision Process."

U(M|T, C) = P(Success|M, T, C) × V(Success) - Cost(M)

This module implements:
- Expected Utility Calculation: Probability × Value - Cost
- Experience Knowledge Base: Historical performance lookup
- Reinforcement Learning: PPO-style policy optimization
- Dynamic Routing: Real-time module selection
"""

import hashlib
import random
import math
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
from enum import Enum
from collections import defaultdict


# ==============================================================================
# Data Structures
# ==============================================================================

@dataclass
class ExecutionTrace:
    """Record of a module execution for learning."""
    trace_id: str
    module_id: str
    task_type: str
    target_attributes: Dict[str, Any]
    context_hash: str
    success: bool
    execution_time_ms: float
    result_quality: float  # 0-1 quality score
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class RoutingDecision:
    """A routing decision with utility breakdown."""
    selected_module: str
    utility_score: float
    p_success: float
    value: float
    cost: float
    confidence: float
    alternatives: List[Tuple[str, float]]  # (module_id, utility)
    reasoning: str


@dataclass
class ModulePerformance:
    """Performance statistics for a module."""
    module_id: str
    total_executions: int = 0
    successful_executions: int = 0
    total_time_ms: float = 0.0
    quality_sum: float = 0.0
    
    # By task type
    by_task_type: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    @property
    def success_rate(self) -> float:
        if self.total_executions == 0:
            return 0.5  # Prior
        return self.successful_executions / self.total_executions
    
    @property
    def avg_time_ms(self) -> float:
        if self.total_executions == 0:
            return 1000  # Default 1 second
        return self.total_time_ms / self.total_executions
    
    @property
    def avg_quality(self) -> float:
        if self.total_executions == 0:
            return 0.5  # Prior
        return self.quality_sum / self.total_executions
    
    def get_success_rate_for_task(self, task_type: str) -> float:
        """Get success rate for specific task type."""
        if task_type in self.by_task_type:
            stats = self.by_task_type[task_type]
            total = stats.get("total", 0)
            success = stats.get("success", 0)
            if total > 0:
                return success / total
        return self.success_rate


# ==============================================================================
# Experience Knowledge Base
# ==============================================================================

class ExperienceKnowledgeBase:
    """
    Vector store of successful orchestration traces.
    
    "Successful orchestration traces are stored in a vector database.
    When the system encounters a new target that resembles a previous one,
    it retrieves the 'Winning Strategy' from the EKB."
    """
    
    def __init__(self, max_traces: int = 10000):
        """Initialize the Experience Knowledge Base."""
        self.traces: List[ExecutionTrace] = []
        self.max_traces = max_traces
        
        # Index by module
        self.by_module: Dict[str, List[ExecutionTrace]] = defaultdict(list)
        
        # Index by task type
        self.by_task_type: Dict[str, List[ExecutionTrace]] = defaultdict(list)
        
        # Index by context hash (for similarity lookup)
        self.by_context: Dict[str, List[ExecutionTrace]] = defaultdict(list)
    
    def store(self, trace: ExecutionTrace):
        """Store a new execution trace."""
        self.traces.append(trace)
        self.by_module[trace.module_id].append(trace)
        self.by_task_type[trace.task_type].append(trace)
        self.by_context[trace.context_hash].append(trace)
        
        # Prune if over limit (FIFO)
        if len(self.traces) > self.max_traces:
            old_trace = self.traces.pop(0)
            self._remove_from_indices(old_trace)
    
    def _remove_from_indices(self, trace: ExecutionTrace):
        """Remove trace from indices."""
        if trace.module_id in self.by_module:
            try:
                self.by_module[trace.module_id].remove(trace)
            except ValueError:
                pass
        if trace.task_type in self.by_task_type:
            try:
                self.by_task_type[trace.task_type].remove(trace)
            except ValueError:
                pass
    
    def query_similar(
        self,
        task_type: str,
        context_hash: str,
        limit: int = 10
    ) -> List[ExecutionTrace]:
        """
        Query for similar execution traces.
        
        Args:
            task_type: Type of task
            context_hash: Hash of context for similarity matching
            limit: Maximum results
        
        Returns:
            List of similar traces, most recent first
        """
        # First, try exact context match
        if context_hash in self.by_context:
            matches = self.by_context[context_hash][-limit:]
            if matches:
                return list(reversed(matches))
        
        # Fall back to task type match
        if task_type in self.by_task_type:
            matches = self.by_task_type[task_type][-limit:]
            return list(reversed(matches))
        
        return []
    
    def get_winning_strategy(
        self,
        task_type: str,
        context: Dict[str, Any]
    ) -> Optional[Tuple[str, float]]:
        """
        Get the winning strategy (best module) for a context.
        
        Returns:
            Tuple of (module_id, success_rate) or None
        """
        context_hash = self._hash_context(context)
        traces = self.query_similar(task_type, context_hash, limit=20)
        
        if not traces:
            return None
        
        # Aggregate by module
        module_stats: Dict[str, Dict[str, int]] = {}
        for trace in traces:
            if trace.module_id not in module_stats:
                module_stats[trace.module_id] = {"success": 0, "total": 0}
            module_stats[trace.module_id]["total"] += 1
            if trace.success:
                module_stats[trace.module_id]["success"] += 1
        
        # Find best performer
        best_module = None
        best_rate = 0.0
        
        for module_id, stats in module_stats.items():
            if stats["total"] >= 3:  # Minimum sample size
                rate = stats["success"] / stats["total"]
                if rate > best_rate:
                    best_rate = rate
                    best_module = module_id
        
        return (best_module, best_rate) if best_module else None
    
    def _hash_context(self, context: Dict[str, Any]) -> str:
        """Create hash of context for similarity matching."""
        # Sort keys for determinism
        sorted_items = sorted(context.items(), key=lambda x: x[0])
        context_str = str(sorted_items)
        return hashlib.md5(context_str.encode()).hexdigest()


# ==============================================================================
# Routing Policy (RL)
# ==============================================================================

class RoutingPolicy:
    """
    Reinforcement Learning policy for routing optimization.
    
    "Using Proximal Policy Optimization (PPO), the system updates 
    the weights of its routing model."
    
    This is a simplified policy gradient implementation.
    """
    
    def __init__(self, learning_rate: float = 0.01):
        """Initialize the routing policy."""
        self.learning_rate = learning_rate
        
        # Policy weights: (task_type, module_id) -> weight
        self.weights: Dict[Tuple[str, str], float] = defaultdict(lambda: 0.0)
        
        # Performance tracking
        self.performance = ModulePerformance
        self.module_stats: Dict[str, ModulePerformance] = {}
        
        # Exploration parameters
        self.epsilon = 0.1  # Exploration rate
        self.epsilon_decay = 0.995
        self.min_epsilon = 0.01
    
    def get_preference(self, task_type: str, module_id: str) -> float:
        """Get policy preference for module given task type."""
        return self.weights[(task_type, module_id)]
    
    def update(
        self,
        task_type: str,
        module_id: str,
        reward: float
    ):
        """
        Update policy based on reward signal.
        
        Args:
            task_type: Type of task executed
            module_id: Module that executed
            reward: Reward signal (1.0 for success, -0.5 for failure)
        """
        key = (task_type, module_id)
        
        # Simple policy gradient update
        # Increase weight if positive reward, decrease if negative
        self.weights[key] += self.learning_rate * reward
        
        # Update module stats
        if module_id not in self.module_stats:
            self.module_stats[module_id] = ModulePerformance(module_id=module_id)
        
        stats = self.module_stats[module_id]
        stats.total_executions += 1
        if reward > 0:
            stats.successful_executions += 1
        
        # Task-specific stats
        if task_type not in stats.by_task_type:
            stats.by_task_type[task_type] = {"total": 0, "success": 0}
        stats.by_task_type[task_type]["total"] += 1
        if reward > 0:
            stats.by_task_type[task_type]["success"] += 1
        
        # Decay exploration
        self.epsilon = max(self.min_epsilon, self.epsilon * self.epsilon_decay)
    
    def should_explore(self) -> bool:
        """Decide whether to explore (random) or exploit (best known)."""
        return random.random() < self.epsilon


# ==============================================================================
# Probabilistic Router
# ==============================================================================

class ProbabilisticRouter:
    """
    Routes tasks to modules using expected utility calculation.
    
    U(M|T, C) = P(Success|M, T, C) × V(Success) - Cost(M)
    
    Where:
    - P(Success): Probability module can satisfy task given context
    - V(Success): Value of the outcome (derived from goal)
    - Cost(M): Computational cost, latency, risk of module
    """
    
    # Default success probability for unknown modules
    DEFAULT_SUCCESS_PROBABILITY = 0.5
    
    # Value multipliers by intent urgency
    VALUE_MULTIPLIERS = {
        "critical": 2.0,
        "high": 1.5,
        "medium": 1.0,
        "low": 0.7
    }
    
    def __init__(self):
        """Initialize the Probabilistic Router."""
        self.ekb = ExperienceKnowledgeBase()
        self.policy = RoutingPolicy()
        
        # Cost parameters
        self.latency_weight = 0.3
        self.compute_weight = 0.2
        self.risk_weight = 0.5
        
        print("[ProbabilisticRouter] Initialized with POMDP routing")
    
    def select_module(
        self,
        task: Dict[str, Any],
        capabilities: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> RoutingDecision:
        """
        Select optimal module using expected utility.
        
        Args:
            task: Task to execute
            capabilities: Available module capabilities
            context: Current context (durable + session)
        
        Returns:
            RoutingDecision with selected module and reasoning
        """
        context = context or {}
        task_type = task.get("type", "unknown")
        intent = task.get("intent", "")
        urgency = task.get("urgency", "medium")
        
        # Calculate utility for each capable module
        utilities: Dict[str, Dict[str, float]] = {}
        
        for module_id, capability in capabilities.items():
            # Check if module supports this task type
            if not self._supports_task(capability, task):
                continue
            
            # Calculate utility components
            p_success = self._estimate_success_probability(
                module_id, task_type, context
            )
            
            value = self._compute_value(task, capability, urgency)
            cost = self._compute_cost(module_id, capability, context)
            
            utility = (p_success * value) - cost
            
            utilities[module_id] = {
                "utility": utility,
                "p_success": p_success,
                "value": value,
                "cost": cost
            }
        
        if not utilities:
            # No capable modules found
            return RoutingDecision(
                selected_module="none",
                utility_score=0,
                p_success=0,
                value=0,
                cost=0,
                confidence=0,
                alternatives=[],
                reasoning="No capable modules found for task"
            )
        
        # Check if we should explore (RL)
        if self.policy.should_explore():
            # Random selection among capable modules
            selected = random.choice(list(utilities.keys()))
            reasoning = "Exploration: random selection to gather data"
        else:
            # Exploit: select highest utility
            selected = max(utilities, key=lambda m: utilities[m]["utility"])
            reasoning = "Exploitation: selected highest utility module"
        
        selected_utility = utilities[selected]
        
        # Calculate confidence based on data quality
        confidence = self._calculate_confidence(selected, task_type)
        
        # Prepare alternatives
        alternatives = sorted(
            [(m, u["utility"]) for m, u in utilities.items() if m != selected],
            key=lambda x: x[1],
            reverse=True
        )[:3]
        
        return RoutingDecision(
            selected_module=selected,
            utility_score=selected_utility["utility"],
            p_success=selected_utility["p_success"],
            value=selected_utility["value"],
            cost=selected_utility["cost"],
            confidence=confidence,
            alternatives=alternatives,
            reasoning=reasoning
        )
    
    def _supports_task(self, capability: Any, task: Dict[str, Any]) -> bool:
        """Check if a module capability supports the task."""
        # Get intent tags from capability
        if hasattr(capability, 'intent_tags'):
            intent_tags = capability.intent_tags
        elif isinstance(capability, dict):
            intent_tags = capability.get('intent_tags', [])
        else:
            return True  # Assume supports if can't determine
        
        # Check against task requirements
        task_intent = task.get("intent", "").lower()
        task_type = task.get("type", "").lower()
        
        for tag in intent_tags:
            if tag.lower() in task_intent or tag.lower() in task_type:
                return True
        
        # If no specific tags required, allow
        if not task_intent and not task_type:
            return True
        
        return False
    
    def _estimate_success_probability(
        self,
        module_id: str,
        task_type: str,
        context: Dict[str, Any]
    ) -> float:
        """
        Estimate probability of success given module, task, and context.
        
        Uses:
        1. Historical performance from EKB
        2. Policy weights from RL
        3. Default prior
        """
        # Check EKB for similar executions
        context_hash = self.ekb._hash_context(context)
        similar_traces = self.ekb.query_similar(task_type, context_hash, limit=10)
        
        if similar_traces:
            # Calculate success rate from historical data
            module_traces = [t for t in similar_traces if t.module_id == module_id]
            if module_traces:
                successes = sum(1 for t in module_traces if t.success)
                return successes / len(module_traces)
        
        # Check module stats
        if module_id in self.policy.module_stats:
            stats = self.policy.module_stats[module_id]
            task_rate = stats.get_success_rate_for_task(task_type)
            if stats.total_executions >= 3:
                return task_rate
        
        # Check policy preference
        preference = self.policy.get_preference(task_type, module_id)
        if preference != 0:
            # Convert preference to probability (sigmoid)
            return 1 / (1 + math.exp(-preference))
        
        return self.DEFAULT_SUCCESS_PROBABILITY
    
    def _compute_value(
        self,
        task: Dict[str, Any],
        capability: Any,
        urgency: str
    ) -> float:
        """Compute value of successful execution."""
        base_value = 1.0
        
        # Apply urgency multiplier
        multiplier = self.VALUE_MULTIPLIERS.get(urgency, 1.0)
        
        # Adjust based on task severity/importance
        severity = task.get("severity", "medium").lower()
        severity_bonus = {"critical": 0.5, "high": 0.3, "medium": 0.0, "low": -0.2}
        base_value += severity_bonus.get(severity, 0.0)
        
        return base_value * multiplier
    
    def _compute_cost(
        self,
        module_id: str,
        capability: Any,
        context: Dict[str, Any]
    ) -> float:
        """
        Compute cost of using a module.
        
        Cost = Latency + Compute + Risk
        """
        # Get cost profile from capability
        if hasattr(capability, 'cost_profile'):
            profile = capability.cost_profile
            latency = {"low": 0.1, "medium": 0.3, "high": 0.6}.get(
                getattr(profile, 'latency', 'medium'), 0.3
            )
            compute = {"low": 0.1, "medium": 0.2, "high": 0.4}.get(
                getattr(profile, 'compute', 'medium'), 0.2
            )
            risk = {"low": 0.0, "medium": 0.2, "high": 0.5}.get(
                getattr(profile, 'risk', 'low'), 0.1
            )
        elif isinstance(capability, dict) and 'cost_profile' in capability:
            profile = capability['cost_profile']
            latency = {"low": 0.1, "medium": 0.3, "high": 0.6}.get(
                profile.get('latency', 'medium'), 0.3
            )
            compute = {"low": 0.1, "medium": 0.2, "high": 0.4}.get(
                profile.get('compute', 'medium'), 0.2
            )
            risk = {"low": 0.0, "medium": 0.2, "high": 0.5}.get(
                profile.get('risk', 'low'), 0.1
            )
        else:
            latency = 0.3
            compute = 0.2
            risk = 0.1
        
        # Check context for latency constraints
        if context.get("high_latency"):
            latency *= 1.5  # Penalize high-latency modules more
        
        # Check context for risk tolerance
        risk_tolerance = context.get("risk_tolerance", "medium")
        if risk_tolerance == "low":
            risk *= 2  # Double risk penalty for low tolerance
        elif risk_tolerance == "high":
            risk *= 0.5  # Halve risk penalty for high tolerance
        
        return (
            self.latency_weight * latency +
            self.compute_weight * compute +
            self.risk_weight * risk
        )
    
    def _calculate_confidence(self, module_id: str, task_type: str) -> float:
        """Calculate confidence in the routing decision."""
        # Based on amount of historical data
        if module_id in self.policy.module_stats:
            stats = self.policy.module_stats[module_id]
            
            # More executions = higher confidence
            executions = stats.total_executions
            if executions >= 50:
                return 0.95
            elif executions >= 20:
                return 0.80
            elif executions >= 10:
                return 0.65
            elif executions >= 5:
                return 0.50
            else:
                return 0.35
        
        return 0.30  # Low confidence for unknown modules
    
    # --------------------------------------------------------------------------
    # Learning Interface
    # --------------------------------------------------------------------------
    
    def record_execution(
        self,
        module_id: str,
        task: Dict[str, Any],
        context: Dict[str, Any],
        success: bool,
        execution_time_ms: float = 0,
        result_quality: float = 0.5
    ):
        """
        Record an execution for learning.
        
        Args:
            module_id: Module that executed
            task: Task that was executed
            context: Context during execution
            success: Whether execution succeeded
            execution_time_ms: Execution time
            result_quality: Quality score of result
        """
        task_type = task.get("type", "unknown")
        context_hash = self.ekb._hash_context(context)
        
        # Create trace
        trace = ExecutionTrace(
            trace_id=f"{module_id}_{datetime.now().isoformat()}",
            module_id=module_id,
            task_type=task_type,
            target_attributes=task.get("target_attributes", {}),
            context_hash=context_hash,
            success=success,
            execution_time_ms=execution_time_ms,
            result_quality=result_quality
        )
        
        # Store in EKB
        self.ekb.store(trace)
        
        # Update policy
        reward = 1.0 if success else -0.5
        self.policy.update(task_type, module_id, reward)
    
    # --------------------------------------------------------------------------
    # Statistics
    # --------------------------------------------------------------------------
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get router statistics."""
        return {
            "total_traces": len(self.ekb.traces),
            "exploration_rate": self.policy.epsilon,
            "modules_tracked": len(self.policy.module_stats),
            "module_performance": {
                module_id: {
                    "success_rate": stats.success_rate,
                    "total_executions": stats.total_executions,
                    "avg_quality": stats.avg_quality
                }
                for module_id, stats in self.policy.module_stats.items()
            }
        }


# ==============================================================================
# CLI Interface
# ==============================================================================

if __name__ == "__main__":
    import json
    
    router = ProbabilisticRouter()
    
    # Simulate some capabilities
    capabilities = {
        "watson": {
            "intent_tags": ["reconnaissance", "discovery", "scan"],
            "cost_profile": {"latency": "low", "compute": "low", "risk": "low"}
        },
        "sherlock": {
            "intent_tags": ["analysis", "vulnerability", "detection"],
            "cost_profile": {"latency": "medium", "compute": "medium", "risk": "low"}
        },
        "moriarty": {
            "intent_tags": ["exploitation", "attack", "verify"],
            "cost_profile": {"latency": "high", "compute": "high", "risk": "high"}
        }
    }
    
    # Test routing
    task = {
        "type": "vulnerability_assessment",
        "intent": "check for reentrancy vulnerabilities",
        "urgency": "high"
    }
    
    context = {
        "risk_tolerance": "medium"
    }
    
    print("=== Routing Decision ===\n")
    decision = router.select_module(task, capabilities, context)
    
    print(f"Selected: {decision.selected_module}")
    print(f"Utility: {decision.utility_score:.3f}")
    print(f"P(Success): {decision.p_success:.2f}")
    print(f"Value: {decision.value:.2f}")
    print(f"Cost: {decision.cost:.3f}")
    print(f"Confidence: {decision.confidence:.2f}")
    print(f"Reasoning: {decision.reasoning}")
    print(f"Alternatives: {decision.alternatives}")
    
    # Simulate some learning
    print("\n=== Simulating Learning ===\n")
    
    for i in range(10):
        router.record_execution(
            module_id="sherlock",
            task={"type": "analysis"},
            context={},
            success=random.random() > 0.3,
            result_quality=random.uniform(0.5, 1.0)
        )
    
    print("\n=== Statistics ===")
    print(json.dumps(router.get_statistics(), indent=2))
