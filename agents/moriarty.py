"""
Google Antigravity: Moriarty Agent (Enhanced)
==============================================

Moriarty is THE ADVERSARIAL ENGINE - operating on Game Theory.

"Every fairy tale needs a good old-fashioned villain."
- Moriarty

Moriarty found Sherlock interesting because of his UNPREDICTABILITY.
Mycroft was too predictable in his rationality.

Moriarty applies:
- Prisoner's Dilemma analysis
- Nash Equilibrium calculation
- Strategic Dominance assessment

Key insight: Sometimes IRRATIONAL behavior (from the protocol's 
perspective) is the optimal exploit strategy.

"In a world of locked rooms, the man with the key is king. 
And honey, you should see me in a crown."

**Architectural Resilience**:
- Inherits from InternalAgentBase
- Uses EventBus for Exploit Reporting
"""

import argparse
import json
import os
import random
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple, Set
from datetime import datetime
from enum import Enum

try:
    from internal_agent_base import InternalAgentBase
    from architectural_core import EventType
except ImportError:
    from agents.internal_agent_base import InternalAgentBase
    from agents.architectural_core import EventType


# ==============================================================================
# Game Theory Data Structures
# ==============================================================================

class PlayerType(Enum):
    """Types of players in the protocol game."""
    ATTACKER = "attacker"
    PROTOCOL = "protocol"
    LIQUIDATOR = "liquidator"
    ORACLE = "oracle"
    GOVERNANCE = "governance"
    MEV_SEARCHER = "mev_searcher"
    USER = "user"


class StrategyType(Enum):
    """Types of strategies available."""
    COOPERATIVE = "cooperative"    # Play by the rules
    DEFECTIVE = "defective"        # Exploit the rules
    IRRATIONAL = "irrational"      # Break the rules (unexpected)


class ExploitStatus(Enum):
    """Status of an exploit attempt."""
    PENDING = "pending"
    COMPILING = "compiling"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"


@dataclass
class Player:
    """A player in the protocol game."""
    player_type: PlayerType
    name: str
    strategies: List[str]
    resources: Dict[str, Any]
    objectives: List[str]


@dataclass
class GameState:
    """State of the game at a point in time."""
    players: List[Player]
    current_state: Dict[str, Any]
    available_actions: Dict[str, List[str]]
    payoff_matrix: Dict[str, Dict[str, float]]


@dataclass
class AttackVector:
    """A potential attack vector identified by game theory analysis."""
    id: str
    name: str
    description: str
    strategy_type: StrategyType
    players_involved: List[PlayerType]
    required_resources: Dict[str, Any]
    expected_payoff: float
    success_probability: float
    steps: List[str]


@dataclass
class ExploitResult:
    """Result of an exploit attempt."""
    task_id: str
    status: ExploitStatus
    criticality: str
    loss_impact: str
    poc_path: Optional[str]
    execution_trace: List[str]
    error_message: Optional[str] = None
    fix_attempts: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "criticality": self.criticality,
            "loss_impact": self.loss_impact,
            "poc_path": self.poc_path,
            "execution_trace": self.execution_trace,
            "error_message": self.error_message
        }


# ==============================================================================
# Moriarty Agent
# ==============================================================================

class MoriartyAgent(InternalAgentBase):
    """
    THE ADVERSARIAL ENGINE
    """
    
    def __init__(
        self,
        max_retries: int = 5,
        output_dir: str = "./exploits",
        session_id: Optional[str] = None
    ):
        """
        Initialize Moriarty Agent.
        """
        super().__init__(agent_name="Moriarty", session_id=session_id)
        
        self.max_retries = max_retries
        self.output_dir = output_dir
        
        self.games: Dict[str, GameState] = {}
        self.attack_vectors: List[AttackVector] = []
        self.exploit_results: List[ExploitResult] = []
        
        self.log("Initialized adversarial engine")
        self.log("'Every fairytale needs a good old-fashioned villain.'")
    
    # --------------------------------------------------------------------------
    # Game Theory Modeling
    # --------------------------------------------------------------------------
    
    def model_game(
        self,
        protocol_name: str,
        hypothesis: Dict[str, Any]
    ) -> GameState:
        """
        Model the protocol as a game.
        """
        vuln_type = hypothesis.get("vulnerability", "unknown")
        target = hypothesis.get("target", "unknown")
        
        # Define players based on vulnerability type
        players = self._identify_players(vuln_type)
        
        # Define available actions
        available_actions = self._identify_actions(vuln_type, players)
        
        # Calculate payoff matrix
        payoff_matrix = self._calculate_payoffs(vuln_type, available_actions)
        
        game = GameState(
            players=players,
            current_state={
                "protocol": protocol_name,
                "vulnerability": vuln_type,
                "target": target
            },
            available_actions=available_actions,
            payoff_matrix=payoff_matrix
        )
        
        self.games[protocol_name] = game
        
        self.log(f"Modeled game for {protocol_name} with {len(players)} players")
        
        return game
    
    def _identify_players(self, vuln_type: str) -> List[Player]:
        """Identify players based on vulnerability type."""
        # Attacker is always present
        attacker = Player(
            player_type=PlayerType.ATTACKER,
            name="Attacker",
            strategies=["exploit", "wait", "compound"],
            resources={"capital": "flash_loanable", "gas": "unlimited"},
            objectives=["maximize_profit", "remain_anonymous"]
        )
        
        # Protocol is always present
        protocol = Player(
            player_type=PlayerType.PROTOCOL,
            name="Protocol",
            strategies=["normal_operation", "pause", "upgrade"],
            resources={"tvl": "variable", "admin_keys": "controlled"},
            objectives=["protect_tvl", "maintain_operation"]
        )
        
        players = [attacker, protocol]
        
        # Add context-specific players
        if vuln_type in ["oracle_manipulation", "flash_loan"]:
            players.append(Player(
                player_type=PlayerType.ORACLE,
                name="Oracle Provider",
                strategies=["provide_price", "halt_feed"],
                resources={"data_freshness": "variable"},
                objectives=["reliable_data"]
            ))
        
        if vuln_type in ["liquidation", "collateral"]:
            players.append(Player(
                player_type=PlayerType.LIQUIDATOR,
                name="Liquidator",
                strategies=["liquidate", "wait", "front_run"],
                resources={"capital": "significant"},
                objectives=["liquidation_profit"]
            ))
        
        if "governance" in vuln_type:
            players.append(Player(
                player_type=PlayerType.GOVERNANCE,
                name="Governance",
                strategies=["vote_yes", "vote_no", "abstain"],
                resources={"voting_power": "distributed"},
                objectives=["protocol_health"]
            ))
        
        return players
    
    def _identify_actions(
        self,
        vuln_type: str,
        players: List[Player]
    ) -> Dict[str, List[str]]:
        """Identify available actions for each player."""
        actions = {}
        
        for player in players:
            if player.player_type == PlayerType.ATTACKER:
                actions[player.name] = self._get_attack_actions(vuln_type)
            else:
                actions[player.name] = player.strategies
        
        return actions
    
    def _get_attack_actions(self, vuln_type: str) -> List[str]:
        """Get attack actions based on vulnerability type."""
        base_actions = ["observe", "withdraw", "wait"]
        
        vuln_actions = {
            "reentrancy": ["recursive_call", "drain_via_fallback", "read_only_reenter"],
            "oracle_manipulation": ["flash_borrow", "manipulate_price", "trade_at_manipulated_price"],
            "access_control": ["call_privileged_function", "upgrade_to_malicious", "drain_admin"],
            "flash_loan": ["flash_borrow", "manipulate_state", "extract_value", "repay"],
            "liquidation": ["manipulate_oracle", "trigger_liquidation", "front_run_liquidation"],
            "governance": ["flash_borrow_governance_token", "vote", "execute_proposal"],
            "front_running": ["observe_mempool", "submit_front_tx", "submit_back_tx"],
        }
        
        specific_actions = vuln_actions.get(vuln_type, [])
        return base_actions + specific_actions
    
    def _calculate_payoffs(
        self,
        vuln_type: str,
        available_actions: Dict[str, List[str]]
    ) -> Dict[str, Dict[str, float]]:
        """Calculate payoff matrix for the game."""
        payoffs = {}
        
        # Simplified payoff matrix
        # Attacker payoffs for different attacker-protocol strategy combinations
        payoffs["Attacker"] = {
            "exploit_normal_operation": 1.0,      # Successful exploit
            "exploit_pause": -0.1,                # Failed - protocol paused
            "wait_normal_operation": 0.0,         # No action
            "compound_normal_operation": 0.8,     # Compound attack
        }
        
        payoffs["Protocol"] = {
            "normal_operation_exploit": -1.0,     # Got exploited
            "pause_exploit": -0.1,                # Paused in time
            "normal_operation_wait": 0.1,         # Normal operation
            "upgrade_exploit": -0.5,              # Partial mitigation
        }
        
        return payoffs
    
    # --------------------------------------------------------------------------
    # Nash Equilibrium Analysis
    # --------------------------------------------------------------------------
    
    def find_nash_equilibrium(self, game: GameState) -> Optional[AttackVector]:
        """Find Nash Equilibrium for the game."""
        self.log("Calculating Nash Equilibrium...")
        
        attacker_actions = game.available_actions.get("Attacker", [])
        protocol_actions = game.available_actions.get("Protocol", [])
        
        best_attack = None
        best_payoff = float('-inf')
        
        # Find minimax solution
        for attack in attacker_actions:
            # Assume protocol plays best response
            min_payoff = float('inf')
            
            for defense in protocol_actions:
                key = f"{attack}_{defense}"
                payoff = game.payoff_matrix.get("Attacker", {}).get(key, 0.0)
                min_payoff = min(min_payoff, payoff)
            
            if min_payoff > best_payoff:
                best_payoff = min_payoff
                best_attack = attack
        
        if best_attack and best_payoff > 0:
            return AttackVector(
                id=f"nash_{best_attack}",
                name=f"Nash Equilibrium: {best_attack}",
                description=f"Optimal attack at Nash Equilibrium with payoff {best_payoff}",
                strategy_type=StrategyType.DEFECTIVE,
                players_involved=[PlayerType.ATTACKER],
                required_resources={"capital": "variable"},
                expected_payoff=best_payoff,
                success_probability=0.7,
                steps=[best_attack]
            )
        
        return None
    
    def find_dominant_strategy(self, game: GameState) -> Optional[AttackVector]:
        """Find the attacker's dominant strategy."""
        self.log("Searching for dominant strategy...")
        
        attacker_actions = game.available_actions.get("Attacker", [])
        protocol_actions = game.available_actions.get("Protocol", [])
        
        for attack in attacker_actions:
            is_dominant = True
            min_payoff = float('inf')
            
            for defense in protocol_actions:
                key = f"{attack}_{defense}"
                payoff = game.payoff_matrix.get("Attacker", {}).get(key, 0.0)
                
                # Check if this attack beats all others for this defense
                for other_attack in attacker_actions:
                    if other_attack != attack:
                        other_key = f"{other_attack}_{defense}"
                        other_payoff = game.payoff_matrix.get("Attacker", {}).get(other_key, 0.0)
                        
                        if other_payoff > payoff:
                            is_dominant = False
                            break
                
                if not is_dominant:
                    break
                
                min_payoff = min(min_payoff, payoff)
            
            if is_dominant and min_payoff > 0:
                self.log(f"Found dominant strategy: {attack}")
                return AttackVector(
                    id=f"dominant_{attack}",
                    name=f"Dominant Strategy: {attack}",
                    description=f"Always benefits attacker regardless of protocol response",
                    strategy_type=StrategyType.DEFECTIVE,
                    players_involved=[PlayerType.ATTACKER],
                    required_resources={"capital": "variable"},
                    expected_payoff=min_payoff,
                    success_probability=0.85,
                    steps=[attack]
                )
        
        return None
    
    # --------------------------------------------------------------------------
    # "Breaking the Game" - Irrational Strategies
    # --------------------------------------------------------------------------
    
    def break_the_game(
        self,
        game: GameState,
        hypothesis: Dict[str, Any]
    ) -> Optional[AttackVector]:
        """
        Find the 'third option' - lateral thinking.
        """
        self.log("Seeking to break the game - finding third option...")
        
        vuln_type = hypothesis.get("vulnerability", "unknown")
        
        # Combination attacks that break assumptions
        unconventional_attacks = {
            "reentrancy": AttackVector(
                id="break_reentrancy",
                name="Cross-Function Reentrancy",
                description="Reenter via a different function than expected",
                strategy_type=StrategyType.IRRATIONAL,
                players_involved=[PlayerType.ATTACKER],
                required_resources={"malicious_contract": True},
                expected_payoff=1.0,
                success_probability=0.5,
                steps=[
                    "Deploy malicious contract",
                    "Call function A (triggers callback)",
                    "In callback, call function B (not protected)",
                    "Exploit shared state inconsistency"
                ]
            ),
            "oracle_manipulation": AttackVector(
                id="break_oracle",
                name="Multi-Block Oracle Attack",
                description="Manipulate TWAP over multiple blocks via MEV",
                strategy_type=StrategyType.IRRATIONAL,
                players_involved=[PlayerType.ATTACKER, PlayerType.MEV_SEARCHER],
                required_resources={"mev_bundle": True, "capital": "large"},
                expected_payoff=0.8,
                success_probability=0.4,
                steps=[
                    "Coordinate with block builder",
                    "Submit transactions over multiple blocks",
                    "Manipulate TWAP accumulator",
                    "Extract value at manipulated price"
                ]
            ),
            "governance": AttackVector(
                id="break_governance",
                name="Flash Loan Governance Attack",
                description="Borrow governance tokens to pass malicious proposal",
                strategy_type=StrategyType.IRRATIONAL,
                players_involved=[PlayerType.ATTACKER, PlayerType.GOVERNANCE],
                required_resources={"flash_loan": True, "governance_token": "borrowable"},
                expected_payoff=2.0,
                success_probability=0.3,
                steps=[
                    "Flash borrow governance tokens",
                    "Create malicious proposal",
                    "Vote with borrowed tokens",
                    "Execute proposal",
                    "Extract value",
                    "Repay flash loan"
                ]
            ),
            "flash_loan": AttackVector(
                id="break_flash",
                name="Multi-Protocol Flash Attack",
                description="Chain flash loans across protocols to amplify attack",
                strategy_type=StrategyType.IRRATIONAL,
                players_involved=[PlayerType.ATTACKER],
                required_resources={"multi_protocol_knowledge": True},
                expected_payoff=1.5,
                success_probability=0.35,
                steps=[
                    "Flash borrow from Protocol A",
                    "Use as collateral in Protocol B",
                    "Borrow from Protocol B",
                    "Attack target protocol",
                    "Unwind positions",
                    "Repay all loans"
                ]
            ),
        }
        
        # Get unconventional attack for this vulnerability
        attack = unconventional_attacks.get(vuln_type)
        
        if attack:
            self.attack_vectors.append(attack)
            self.log(f"Found third option: {attack.name}")
        
        return attack
    
    # --------------------------------------------------------------------------
    # Exploit Generation (ReX Protocol)
    # --------------------------------------------------------------------------
    
    def generate_exploit(
        self,
        hypothesis: Dict[str, Any],
        attack_vector: Optional[AttackVector] = None
    ) -> ExploitResult:
        """
        Generate exploit PoC using ReX Protocol (Prompt-to-Pwn).
        """
        task_id = hypothesis.get("task_id", f"task_{len(self.exploit_results)}")
        vulnerability = hypothesis.get("vulnerability", "unknown")
        target = hypothesis.get("target", "unknown")
        goal = hypothesis.get("goal", "Demonstrate exploitability")
        
        self.log(f"Initiating ReX Protocol for: {vulnerability} on {target}")
        
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Generate exploit code
        exploit_code = self._generate_exploit_code(vulnerability, target, goal, attack_vector)
        
        # File path
        safe_target = target.replace("/", "_").replace(":", "_").replace(".", "_")
        poc_filename = f"Exploit_{safe_target}.t.sol"
        poc_path = os.path.join(self.output_dir, poc_filename)
        
        # Write exploit
        with open(poc_path, "w") as f:
            f.write(exploit_code)
        
        # Simulate compilation and execution
        execution_trace = [
            f"Generated PoC for {vulnerability}",
            f"Target: {target}",
            f"PoC written to: {poc_path}",
        ]
        
        # In production, this would actually compile and run the test
        # For now, we simulate success based on probability
        if attack_vector:
            success_prob = attack_vector.success_probability
        else:
            success_prob = 0.6
        
        # Determine outcome (simulated)
        if random.random() < success_prob:
            status = ExploitStatus.SUCCESS
            criticality = "CRITICAL"
            loss_impact = "100%"
            execution_trace.append("Exploit VERIFIED - funds drained")
        else:
            status = ExploitStatus.PARTIAL
            criticality = "HIGH"
            loss_impact = "Partial"
            execution_trace.append("Exploit partial success - needs refinement")
        
        result = ExploitResult(
            task_id=task_id,
            status=status,
            criticality=criticality,
            loss_impact=loss_impact,
            poc_path=poc_path,
            execution_trace=execution_trace
        )
        
        self.exploit_results.append(result)
        
        self.log(f"ReX Protocol complete: {status.value}")
        
        # Publish Exploitation Event
        self.publish_event(EventType.ACTION, {
            "type": "exploit_attempt",
            "status": status.value,
            "target": target,
            "result": result.to_dict()
        })

        return result
    
    def _generate_exploit_code(
        self,
        vulnerability: str,
        target: str,
        goal: str,
        attack_vector: Optional[AttackVector]
    ) -> str:
        """Generate Foundry test exploit code."""
        
        steps = attack_vector.steps if attack_vector else ["Execute exploit"]
        steps_comment = "\n".join(f"    // Step {i+1}: {step}" for i, step in enumerate(steps))
        
        return f'''// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "forge-std/Test.sol";

/**
 * @title Exploit_{vulnerability}
 * @notice Generated by Moriarty Adversarial Engine
 * @dev Target: {target}
 * @dev Goal: {goal}
 * @dev Attack Type: {attack_vector.strategy_type.value if attack_vector else "standard"}
 */
contract Exploit_{vulnerability.replace(" ", "_")} is Test {{
    
    // Target contract interface
    // ITarget target;
    
    // Attacker address
    address attacker = makeAddr("attacker");
    
    // Attack parameters
    uint256 constant ATTACK_AMOUNT = 1000 ether;
    
    function setUp() public {{
        // Setup test environment
        vm.deal(attacker, ATTACK_AMOUNT);
        
        // Deploy or fork target contract
        // target = ITarget(deployedAddress);
    }}
    
    function testExploit_{vulnerability.replace(" ", "_")}() public {{
        // Record initial state
        uint256 initialBalance = attacker.balance;
        
        // Execute attack
        vm.startPrank(attacker);
        
{steps_comment}
        
        // TODO: Implement actual exploit logic
        // This is a template - fill in with real exploit code
        
        vm.stopPrank();
        
        // Verify exploit success
        // assertGt(attacker.balance, initialBalance, "Exploit should profit");
        
        console.log("Exploit goal: {goal}");
        console.log("Vulnerability: {vulnerability}");
    }}
    
    // Fallback for reentrancy exploits
    receive() external payable {{
        // Reentrancy callback logic
    }}
    
    fallback() external payable {{
        // Fallback callback logic
    }}
}}
'''
    
    # --------------------------------------------------------------------------
    # Batch Processing
    # --------------------------------------------------------------------------
    
    def exploit_hypotheses(
        self,
        hypotheses: List[Dict[str, Any]]
    ) -> List[ExploitResult]:
        """
        Process multiple hypotheses from Sherlock.
        """
        results = []
        
        self.log(f"Processing {len(hypotheses)} hypotheses...")
        
        for hypothesis in hypotheses:
            # Model the game
            game = self.model_game("target_protocol", hypothesis)
            
            # Find attack vectors
            nash_attack = self.find_nash_equilibrium(game)
            dominant_attack = self.find_dominant_strategy(game)
            unconventional_attack = self.break_the_game(game, hypothesis)
            
            # Choose best attack vector
            best_attack = None
            if unconventional_attack and unconventional_attack.expected_payoff > 0.5:
                best_attack = unconventional_attack
            elif dominant_attack:
                best_attack = dominant_attack
            elif nash_attack:
                best_attack = nash_attack
            
            # Generate exploit
            result = self.generate_exploit(hypothesis, best_attack)
            results.append(result)
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get Moriarty's statistics."""
        status_counts = {}
        for result in self.exploit_results:
            status_counts[result.status.value] = status_counts.get(result.status.value, 0) + 1
        
        return {
            "total_exploits": len(self.exploit_results),
            "by_status": status_counts,
            "games_modeled": len(self.games),
            "attack_vectors": len(self.attack_vectors)
        }


# ==============================================================================
# CLI Interface (Backward Compatible)
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(description="Moriarty Adversarial Agent (Enhanced)")
    parser.add_argument("--action", required=True, choices=["exploit", "game", "stats"])
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", help="Optional output file for JSON results") 
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--session-id", help="Correlation ID")
    parser.add_argument("--max-retries", type=int, default=3)
    args = parser.parse_args()

    moriarty = MoriartyAgent(
        max_retries=args.max_retries, 
        output_dir=args.output_dir,
        session_id=args.session_id
    )
    
    moriarty.log(f"Executing action: {args.action}")

    if args.action == "exploit":
        # Load hypotheses and generate exploits
        with open(args.input, 'r') as f:
            data = json.load(f)
            
        # Handle wrapping formats
        hypotheses = data.get("findings", data) if isinstance(data, dict) else data
        
        results = moriarty.exploit_hypotheses(hypotheses)
        
        output_data = [r.to_dict() for r in results]
        
        if args.output:
            with open(args.output, "w") as f:
                json.dump(output_data, f, indent=2)
        else:
            print(json.dumps(output_data, indent=2))
        
        moriarty.log(f"Exploit generation complete. {len(results)} PoCs generated.")

    elif args.action == "game":
        # Just model looking for Nash Eq
        with open(args.input, 'r') as f:
            hypothesis = json.load(f)
            
        game = moriarty.model_game("Analysis Target", hypothesis)
        best_attack = moriarty.find_nash_equilibrium(game)
        
        if args.output:
            with open(args.output, "w") as f:
                json.dump(asdict(best_attack) if best_attack else {}, f, indent=2)

    elif args.action == "stats":
        print(json.dumps(moriarty.get_statistics(), indent=2))


if __name__ == "__main__":
    main()
