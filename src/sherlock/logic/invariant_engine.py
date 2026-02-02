#!/usr/bin/env python3
"""
Invariant Engine: The Laws of DeFi Physics (v2.0)
=================================================
"When you have eliminated the impossible, whatever remains, 
however improbable, must be the truth."

Upgraded to implement 9 Universal Invariants from the 
Deep Logic Verification research framework.

This engine checks if a `FinancialPrimitive` adheres to Universal Mathematical Invariants.
If an Invariant is violated, it is an UNDENIABLE vulnerability.
"""

from dataclasses import dataclass
from enum import Enum


class InvariantType(Enum):
    # Core Economic Invariants
    SOLVENCY = "Solvency"
    CONSERVATION_OF_VALUE = "Conservation of Value"
    CONTINUITY = "Exchange Rate Continuity"
    STATE_SYNC = "State Synchronization"

    # Incentive & Economics
    INCENTIVE_COMPATIBILITY = "Incentive Compatibility"
    MONOTONIC_RATES = "Monotonic Interest Rates"

    # Boundary & Edge Cases
    TIME_ACCUMULATOR = "Time-Dependent Accumulator"
    INVERTED_DOS = "Inverted DoS"
    MITIGATION_BOUNDARY = "Mitigation Boundary"

    # Legacy (for compatibility)
    ACCESS_CONTROL = "Privileged Access"

@dataclass
class InvariantCheck:
    name: str
    type: InvariantType
    description: str
    logic_prompt: str  # The prompt to guide the LLM/Solver
    detection_patterns: list[str]  # Code patterns that trigger this check

class InvariantEngine:
    """
    The Laws of DeFi Physics Engine.
    
    Implements all 9 Universal Invariants from the Deep Logic Verification research.
    Each invariant is designed to catch a specific class of deep logic bugs.
    """

    INVARIANTS = {
        # ============================================================
        # INVARIANT 1: SOLVENCY
        # ============================================================
        InvariantType.SOLVENCY: InvariantCheck(
            name="Fee-on-Transfer Solvency",
            type=InvariantType.SOLVENCY,
            description="The protocol must strictly hold enough assets to cover all internal liabilities.",
            logic_prompt="""
            Does the code explicitly check `balanceAfter - balanceBefore` when receiving assets?
            OR does it assume `balance += amount`?
            
            VIOLATION: If it assumes `amount` without measuring actual received amount,
            it VIOLATES Solvency for Fee-on-Transfer tokens.
            
            Detection: Look for `balanceOf[msg.sender] += amount` instead of 
                       `balanceOf[msg.sender] += receivedAmount`
            """,
            detection_patterns=["transferFrom", "safeTransferFrom", "balances[", "+= amount"]
        ),

        # ============================================================
        # INVARIANT 2: EXCHANGE RATE CONTINUITY
        # ============================================================
        InvariantType.CONTINUITY: InvariantCheck(
            name="Exchange Rate Continuity (Inflation Attack)",
            type=InvariantType.CONTINUITY,
            description="The exchange rate between Assets and Shares must be a continuous function. It should not be possible to manipulate the rate by orders of magnitude in a single transaction.",
            logic_prompt="""
            Check if `convertToShares` or share price calculation handles edge cases:
            
            VIOLATION: Inflation Attack (ERC4626)
            - If TotalSupply == 0, an attacker deposits 1 wei, then donates assets
            - This manipulates the exchange rate to steal from future depositors
            
            Detection: Check if `convertToShares` uses "Dead Shares" or "Virtual Offsets"
                       Look for division by `totalSupply` without offset: `* totalSupply / totalAssets`
            """,
            detection_patterns=["convertToShares", "previewDeposit", "totalSupply", "totalAssets", "/ totalAssets"]
        ),

        # ============================================================
        # INVARIANT 3: CONSERVATION OF VALUE
        # ============================================================
        InvariantType.CONSERVATION_OF_VALUE: InvariantCheck(
            name="Conservation of Value (Yield Loop)",
            type=InvariantType.CONSERVATION_OF_VALUE,
            description="The protocol cannot create value out of thin air. Net Protocol Wealth Change must equal Net External Inputs.",
            logic_prompt="""
            Check for Yield Loops / Flash Loan manipulation:
            
            VIOLATION: Attacker flash loans assets, deposits them, forces a `distributeRewards()` 
            based on the inflated balance, and withdraws.
            
            Detection: Look for reward logic relying on `balanceOf(address(this))` without snapshotting.
                       Reward calculations based on current balance instead of time-weighted average.
            """,
            detection_patterns=["balanceOf(address(this))", "distributeRewards", "harvest", "claim"]
        ),

        # ============================================================
        # INVARIANT 4: STATE SYNCHRONIZATION (Read-Only Reentrancy)
        # ============================================================
        InvariantType.STATE_SYNC: InvariantCheck(
            name="State Synchronization (Read-Only Reentrancy)",
            type=InvariantType.STATE_SYNC,
            description="When querying an external contract (Oracle, AMM) for critical data, that contract must be in a settled state.",
            logic_prompt="""
            Check for Read-Only Reentrancy vectors:
            
            VIOLATION: Curve/Balancer Read-Only Reentrancy
            - Attacker calls withdraw on Curve (unsettling the pool)
            - Gets control via ETH fallback
            - Calls Victim Protocol which reads manipulated `get_virtual_price`
            
            Detection: Map all view calls to external contracts.
                       Are they called during a callback execution?
                       Is there a reentrancy guard on the view-reading function?
            """,
            detection_patterns=["get_virtual_price", "getPrice", "latestRoundData", ".call", "receive()", "fallback()"]
        ),

        # ============================================================
        # INVARIANT 5: INCENTIVE COMPATIBILITY
        # ============================================================
        InvariantType.INCENTIVE_COMPATIBILITY: InvariantCheck(
            name="Incentive Compatibility (Dust Liquidations)",
            type=InvariantType.INCENTIVE_COMPATIBILITY,
            description="Critical maintenance operations (Liquidations, Keepers) must be economically viable.",
            logic_prompt="""
            Check if liquidations are always profitable:
            
            VIOLATION: Dust Liquidations / Bad Debt Accumulation
            - If a position is small, the gas to liquidate exceeds the bonus
            - Rational actors won't liquidate, leading to bad debt
            
            Detection: Check if `liquidate()` has minimum size requirements
                       Does it revert when user is *too* underwater (can't restore health factor)?
                       Is liquidation bonus sufficient to cover gas at various position sizes?
            """,
            detection_patterns=["liquidate", "healthFactor", "collateralRatio", "liquidationBonus", "minDebt"]
        ),

        # ============================================================
        # INVARIANT 6: MONOTONIC INTEREST RATES
        # ============================================================
        InvariantType.MONOTONIC_RATES: InvariantCheck(
            name="Monotonic Interest Rates (Kink Errors)",
            type=InvariantType.MONOTONIC_RATES,
            description="As utilization increases, the borrow interest rate must explicitly increase (or stay flat). It should never decrease.",
            logic_prompt="""
            Graph the interest rate curve logic:
            
            VIOLATION: Kink implementation errors
            - Rate at 91% utilization is lower than at 90%
            - Non-monotonic rate curve can be exploited for arbitrage
            
            Detection: Check the interest rate model
                       Verify that rate(u1) <= rate(u2) for all u1 < u2
                       Look for conditionals in rate calculation that might invert
            """,
            detection_patterns=["utilizationRate", "borrowRate", "interestRate", "kink", "slope"]
        ),

        # ============================================================
        # INVARIANT 7: TIME-DEPENDENT ACCUMULATOR
        # ============================================================
        InvariantType.TIME_ACCUMULATOR: InvariantCheck(
            name="Time-Dependent Accumulator Overflow",
            type=InvariantType.TIME_ACCUMULATOR,
            description="Any state variable that accumulates based on block.timestamp must be mathematically projected to its data type's boundaries.",
            logic_prompt="""
            Calculate overflow timeline for time-based accumulators:
            
            VIOLATION: Exponential functions (`expWad`) or linear accumulators 
            overflowing int256/uint256 within a realistic contractual lifespan.
            
            Formula: T_fail = TypeMax / MaxRate
            If T_fail < 100 years, verify overflow handling
            
            Detection: Look for time-based accumulation patterns
                       `index += rate * (block.timestamp - lastUpdate)`
                       `expWad`, `rpow` with large exponents
            """,
            detection_patterns=["block.timestamp", "lastUpdate", "accumulatedInterest", "expWad", "rpow", "index +="]
        ),

        # ============================================================
        # INVARIANT 8: INVERTED DoS (Weaponized Health Checks)
        # ============================================================
        InvariantType.INVERTED_DOS: InvariantCheck(
            name="Inverted DoS (Weaponized Health Checks)",
            type=InvariantType.INVERTED_DOS,
            description="Health checks that protect the protocol can be weaponized to lock the system if they use strict dominant checks.",
            logic_prompt="""
            Invert the health check logic:
            
            VIOLATION: "Dust Lockups"
            - Malicious user donates 1 wei to make `Total = Cap + 1`
            - Causes `deposit()` or `withdraw()` to revert for everyone else
            
            Detection: Can an external user *cheaply* force the system into a "Reverting State"?
                       Look for strict inequalities (< or >) in health checks
                       Code should prefer `saturatingSub` or non-strict inequalities
            """,
            detection_patterns=["require(", "revert(", "< cap", "> max", "totalSupply >=", "isSolvent", "isBalanced"]
        ),

        # ============================================================
        # INVARIANT 9: MITIGATION BOUNDARY VERIFICATION
        # ============================================================
        InvariantType.MITIGATION_BOUNDARY: InvariantCheck(
            name="Mitigation Boundary Verification",
            type=InvariantType.MITIGATION_BOUNDARY,
            description="Never check if a mitigation *exists*; check if it *works* at the boundary limits (0 and Max).",
            logic_prompt="""
            Test mitigation effectiveness at boundaries:
            
            VIOLATION: Inflation protection with `offset = 0` for 18-decimal assets
            - The variable exists, but the protection is mathematically null
            
            Detection: For every protective constant (buffers, offsets, guards):
                       1. What happens if the value is 0?
                       2. What happens at MAX_UINT?
                       3. Does the protection still hold?
            """,
            detection_patterns=["offset", "buffer", "guard", "MIN_", "MAX_", "VIRTUAL_", "DEAD_SHARES"]
        ),
    }

    # ============================================================
    # PRIMITIVE TO INVARIANT MAPPING
    # ============================================================
    PRIMITIVE_INVARIANTS = {
        "Vault": [
            InvariantType.SOLVENCY,
            InvariantType.CONTINUITY,
            InvariantType.CONSERVATION_OF_VALUE,
            InvariantType.MITIGATION_BOUNDARY,
            InvariantType.INVERTED_DOS,
        ],
        "Loan": [
            InvariantType.SOLVENCY,
            InvariantType.INCENTIVE_COMPATIBILITY,
            InvariantType.MONOTONIC_RATES,
            InvariantType.TIME_ACCUMULATOR,
        ],
        "Exchange": [
            InvariantType.CONTINUITY,
            InvariantType.STATE_SYNC,
            InvariantType.CONSERVATION_OF_VALUE,
        ],
        "Oracle": [
            InvariantType.STATE_SYNC,
        ],
        "Governor": [
            InvariantType.TIME_ACCUMULATOR,
            InvariantType.INVERTED_DOS,
        ],
    }

    def check_primitive(self, primitive_type: str, code: str) -> list[dict[str, str]]:
        """
        Selects relevant invariants for a primitive and generates verification prompts.
        
        Args:
            primitive_type: The detected financial primitive (Vault, Loan, Exchange, etc.)
            code: The source code content to analyze
            
        Returns:
            List of invariant checks with prompts for verification
        """
        results = []

        # Get invariants for this primitive type
        invariant_types = self.PRIMITIVE_INVARIANTS.get(primitive_type, [])

        for inv_type in invariant_types:
            inv_check = self.INVARIANTS.get(inv_type)
            if inv_check:
                # Check if any detection patterns match the code
                pattern_matches = []
                for pattern in inv_check.detection_patterns:
                    if pattern.lower() in code.lower():
                        pattern_matches.append(pattern)

                results.append({
                    "invariant": inv_check.name,
                    "type": inv_check.type.value,
                    "description": inv_check.description,
                    "prompt": inv_check.logic_prompt,
                    "pattern_matches": pattern_matches,
                    "relevance": len(pattern_matches) / len(inv_check.detection_patterns) if inv_check.detection_patterns else 0
                })

        # Sort by relevance (most pattern matches first)
        results.sort(key=lambda x: x["relevance"], reverse=True)

        return results

    def get_all_invariants(self) -> list[dict[str, str]]:
        """Returns all 9 invariants in the engine."""
        return [
            {
                "name": inv.name,
                "type": inv.type.value,
                "description": inv.description
            }
            for inv in self.INVARIANTS.values()
        ]

    def check_code_for_patterns(self, code: str) -> dict[str, list[str]]:
        """
        Scans code for patterns that indicate potential invariant violations.
        Returns a mapping of invariant type to matched patterns.
        """
        findings = {}

        for inv_type, inv_check in self.INVARIANTS.items():
            matches = []
            for pattern in inv_check.detection_patterns:
                if pattern.lower() in code.lower():
                    matches.append(pattern)

            if matches:
                findings[inv_type.value] = matches

        return findings


if __name__ == "__main__":
    # Test the engine
    engine = InvariantEngine()

    print("=== Invariant Engine v2.0 ===")
    print(f"Total Invariants: {len(engine.INVARIANTS)}")
    print("\nAll Invariants:")
    for inv in engine.get_all_invariants():
        print(f"  - {inv['name']} ({inv['type']})")

    print("\n=== Testing Vault Primitive ===")
    sample_vault_code = """
    function deposit(uint256 amount) external {
        asset.transferFrom(msg.sender, address(this), amount);
        balances[msg.sender] += amount;
        uint256 shares = amount * totalSupply / totalAssets;
    }
    """

    checks = engine.check_primitive("Vault", sample_vault_code)
    print(f"\nInvariants to verify for Vault ({len(checks)}):")
    for check in checks:
        print(f"\n  [{check['type']}] {check['invariant']}")
        print(f"    Relevance: {check['relevance']:.0%}")
        print(f"    Patterns: {check['pattern_matches']}")
