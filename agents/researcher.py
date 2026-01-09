#!/usr/bin/env python3
"""
Researcher Agent: AI-Powered Pre-Audit Research
================================================

Before the audit begins, the Researcher gathers knowledge:
- What is this protocol?
- What are common vulnerabilities for this type?
- Any known issues with dependencies?
- Historical context from past audits

All research is stored in the LEANN Mind Palace for agents to access.

Usage:
    python researcher.py --project project.json --output research.json
"""

import os
import sys
import json
import argparse
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime

# Try to import LLM router
try:
    from llm_router import LLM
    LLM_AVAILABLE = True
except ImportError:
    try:
        from agents.llm_router import LLM
        LLM_AVAILABLE = True
    except ImportError:
        LLM_AVAILABLE = False
        print("[Researcher] Warning: LLM not available. Research will be limited.")

# Try to import LEANN Mind Palace
try:
    from leann_palace import LEANNMindPalace, Room, MemoryType
    LEANN_AVAILABLE = True
except ImportError:
    try:
        from agents.leann_palace import LEANNMindPalace, Room, MemoryType
        LEANN_AVAILABLE = True
    except ImportError:
        LEANN_AVAILABLE = False
        print("[Researcher] Warning: LEANN not available. Research won't be persisted.")


# ==============================================================================
# Data Structures
# ==============================================================================

@dataclass
class ResearchContext:
    """Research context for the audit."""
    project_name: str
    protocol_type: str
    
    # Protocol understanding
    protocol_summary: str = ""
    key_invariants: List[str] = field(default_factory=list)
    critical_functions: List[str] = field(default_factory=list)
    
    # Vulnerability research
    common_vulnerabilities: List[Dict[str, str]] = field(default_factory=list)
    dependency_risks: List[Dict[str, str]] = field(default_factory=list)
    
    # Historical context
    similar_protocols: List[str] = field(default_factory=list)
    past_exploits: List[Dict[str, str]] = field(default_factory=list)
    
    # Focus areas
    audit_focus_areas: List[str] = field(default_factory=list)
    high_risk_patterns: List[str] = field(default_factory=list)
    
    # Metadata
    research_timestamp: str = ""
    confidence: float = 0.5
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_name": self.project_name,
            "protocol_type": self.protocol_type,
            "protocol_summary": self.protocol_summary,
            "key_invariants": self.key_invariants,
            "critical_functions": self.critical_functions,
            "common_vulnerabilities": self.common_vulnerabilities,
            "dependency_risks": self.dependency_risks,
            "similar_protocols": self.similar_protocols,
            "past_exploits": self.past_exploits,
            "audit_focus_areas": self.audit_focus_areas,
            "high_risk_patterns": self.high_risk_patterns,
            "research_timestamp": self.research_timestamp,
            "confidence": self.confidence
        }


# ==============================================================================
# Researcher Agent
# ==============================================================================

class ResearcherAgent:
    """
    AI-powered research agent that gathers context before audit.
    
    The Researcher:
    1. Analyzes project metadata from ProjectAnalyzer
    2. Queries AI for protocol understanding
    3. Researches common vulnerabilities for protocol type
    4. Queries LEANN for similar past findings
    5. Stores all research in LEANN for agents to access
    """
    
    # Common vulnerabilities by protocol type
    PROTOCOL_VULNS = {
        "dex": [
            {"name": "Price Manipulation", "severity": "CRITICAL", "description": "Flash loan attacks manipulating pool prices"},
            {"name": "Sandwich Attacks", "severity": "HIGH", "description": "Front-running trades for MEV extraction"},
            {"name": "Reentrancy in Swap", "severity": "CRITICAL", "description": "External calls during swap before state updates"},
            {"name": "Incorrect Fee Calculation", "severity": "MEDIUM", "description": "Rounding errors in fee calculations"},
            {"name": "Liquidity Pool Imbalance", "severity": "HIGH", "description": "Attacks that drain one side of the pool"},
        ],
        "lending": [
            {"name": "Oracle Manipulation", "severity": "CRITICAL", "description": "Price oracle attacks for unfair liquidations"},
            {"name": "Flash Loan Attacks", "severity": "CRITICAL", "description": "Using flash loans to manipulate collateral"},
            {"name": "Interest Rate Manipulation", "severity": "HIGH", "description": "Exploiting interest rate model"},
            {"name": "Liquidation Cascades", "severity": "HIGH", "description": "Triggering cascading liquidations"},
            {"name": "Bad Debt Accumulation", "severity": "CRITICAL", "description": "Positions becoming undercollateralized"},
        ],
        "staking": [
            {"name": "Reward Manipulation", "severity": "HIGH", "description": "Gaming reward distribution mechanics"},
            {"name": "Share Inflation", "severity": "CRITICAL", "description": "First depositor attacks, donation attacks"},
            {"name": "Withdrawal Griefing", "severity": "MEDIUM", "description": "Blocking or delaying withdrawals"},
            {"name": "Compounding Exploits", "severity": "MEDIUM", "description": "Exploiting auto-compounding logic"},
        ],
        "bridge": [
            {"name": "Message Replay", "severity": "CRITICAL", "description": "Replaying cross-chain messages"},
            {"name": "Validator Collusion", "severity": "CRITICAL", "description": "Malicious validator consensus"},
            {"name": "Chain Reorg Attacks", "severity": "HIGH", "description": "Exploiting chain reorganizations"},
            {"name": "Finality Issues", "severity": "HIGH", "description": "Acting on non-final transactions"},
        ],
        "nft": [
            {"name": "Reentrancy in Mint", "severity": "HIGH", "description": "Reentrancy during NFT minting"},
            {"name": "Signature Replay", "severity": "HIGH", "description": "Replaying signed messages"},
            {"name": "Metadata Manipulation", "severity": "MEDIUM", "description": "Modifying NFT metadata maliciously"},
            {"name": "Royalty Bypass", "severity": "MEDIUM", "description": "Circumventing royalty payments"},
        ],
        "dao": [
            {"name": "Flash Loan Governance", "severity": "CRITICAL", "description": "Using flash loans to pass proposals"},
            {"name": "Proposal Front-running", "severity": "HIGH", "description": "Front-running governance proposals"},
            {"name": "Timelock Bypass", "severity": "CRITICAL", "description": "Circumventing timelock delays"},
            {"name": "Vote Manipulation", "severity": "HIGH", "description": "Double voting or vote buying"},
        ],
        "generic": [
            {"name": "Reentrancy", "severity": "CRITICAL", "description": "State changes after external calls"},
            {"name": "Access Control", "severity": "HIGH", "description": "Missing or weak access controls"},
            {"name": "Integer Overflow", "severity": "HIGH", "description": "Arithmetic overflow/underflow"},
            {"name": "Unchecked Returns", "severity": "MEDIUM", "description": "Not checking return values"},
            {"name": "Front-running", "severity": "MEDIUM", "description": "Transaction ordering attacks"},
        ],
    }
    
    def __init__(self):
        """Initialize the Researcher."""
        self.llm = LLM() if LLM_AVAILABLE else None
        self.palace = LEANNMindPalace() if LEANN_AVAILABLE else None
        
        print("[Researcher] Initialized")
        print(f"[Researcher] LLM: {'Available' if self.llm else 'Not available'}")
        print(f"[Researcher] LEANN: {'Available' if self.palace else 'Not available'}")
    
    def research(self, project_data: Dict[str, Any]) -> ResearchContext:
        """
        Conduct research on a project.
        
        Args:
            project_data: Output from ProjectAnalyzer
            
        Returns:
            ResearchContext with all gathered information
        """
        project_name = project_data.get("project_name", "Unknown")
        protocol_type = project_data.get("protocol_type", "generic")
        
        print(f"[Researcher] Researching: {project_name} ({protocol_type})")
        
        context = ResearchContext(
            project_name=project_name,
            protocol_type=protocol_type,
            research_timestamp=datetime.now().isoformat()
        )
        
        # Step 1: Protocol understanding (AI)
        self._research_protocol(context, project_data)
        
        # Step 2: Vulnerability research (database + AI)
        self._research_vulnerabilities(context, project_data)
        
        # Step 3: Dependency risks
        self._research_dependencies(context, project_data)
        
        # Step 4: Historical context (LEANN)
        self._research_history(context, project_data)
        
        # Step 5: Generate focus areas
        self._generate_focus_areas(context, project_data)
        
        # Step 6: Store research in LEANN
        self._store_research(context)
        
        print(f"[Researcher] Research complete. Confidence: {context.confidence:.2f}")
        
        return context
    
    def _research_protocol(self, context: ResearchContext, project_data: Dict):
        """Use AI to understand the protocol."""
        if not self.llm:
            context.protocol_summary = f"A {context.protocol_type} protocol"
            return
        
        try:
            # Get protocol summary
            scope_files = project_data.get("scope_files", [])[:15]
            
            response = self.llm.ask(
                f"""Analyze this smart contract project and provide:
1. A 2-3 sentence summary of what this protocol does
2. 3-5 key invariants that should never be violated
3. 3-5 critical functions to focus on

Project: {context.project_name}
Type: {context.protocol_type}
Files: {', '.join(scope_files)}
Description: {project_data.get('protocol_description', 'N/A')}

Respond in this exact format:
SUMMARY: [summary here]
INVARIANTS:
- [invariant 1]
- [invariant 2]
CRITICAL_FUNCTIONS:
- [function 1]
- [function 2]""",
                persona="sherlock"
            )
            
            content = response.content
            
            # Parse response
            if "SUMMARY:" in content:
                summary_match = content.split("SUMMARY:")[1].split("INVARIANTS:")[0]
                context.protocol_summary = summary_match.strip()
            
            if "INVARIANTS:" in content:
                invariants_section = content.split("INVARIANTS:")[1].split("CRITICAL_FUNCTIONS:")[0]
                context.key_invariants = [
                    line.strip().lstrip("- ").lstrip("• ")
                    for line in invariants_section.strip().split("\n")
                    if line.strip() and line.strip() != "-"
                ]
            
            if "CRITICAL_FUNCTIONS:" in content:
                functions_section = content.split("CRITICAL_FUNCTIONS:")[1]
                context.critical_functions = [
                    line.strip().lstrip("- ").lstrip("• ")
                    for line in functions_section.strip().split("\n")
                    if line.strip() and line.strip() != "-"
                ][:5]
            
            context.confidence += 0.2
            print(f"[Researcher] Protocol analysis complete")
            
        except Exception as e:
            print(f"[Researcher] Protocol research failed: {e}")
            context.protocol_summary = f"A {context.protocol_type} protocol (AI analysis failed)"
    
    def _research_vulnerabilities(self, context: ResearchContext, project_data: Dict):
        """Research common vulnerabilities for this protocol type."""
        protocol_type = context.protocol_type.lower()
        
        # Get vulnerabilities from database
        vulns = self.PROTOCOL_VULNS.get(protocol_type, self.PROTOCOL_VULNS["generic"])
        context.common_vulnerabilities = vulns
        
        # Add generic vulnerabilities too
        if protocol_type != "generic":
            generic_vulns = self.PROTOCOL_VULNS["generic"]
            # Add any not already present
            existing_names = {v["name"] for v in vulns}
            for gv in generic_vulns:
                if gv["name"] not in existing_names:
                    context.common_vulnerabilities.append(gv)
        
        context.confidence += 0.1
        print(f"[Researcher] Found {len(context.common_vulnerabilities)} common vulnerabilities")
    
    def _research_dependencies(self, context: ResearchContext, project_data: Dict):
        """Research dependency risks."""
        dependencies = project_data.get("dependencies", {})
        
        # Known risky patterns in dependencies
        risk_patterns = {
            "openzeppelin": "Ensure using latest version. Check for known CVEs.",
            "solmate": "Gas-optimized but less battle-tested than OpenZeppelin.",
            "solady": "Highly optimized, review assembly code carefully.",
            "chainlink": "Validate oracle freshness and heartbeat checks.",
            "uniswap": "Check for correct interface versions.",
        }
        
        for dep_name, version in dependencies.items():
            dep_lower = dep_name.lower()
            for pattern, risk in risk_patterns.items():
                if pattern in dep_lower:
                    context.dependency_risks.append({
                        "dependency": dep_name,
                        "version": version,
                        "risk": risk
                    })
        
        print(f"[Researcher] Found {len(context.dependency_risks)} dependency risks")
    
    def _research_history(self, context: ResearchContext, project_data: Dict):
        """Research historical context from LEANN."""
        if not self.palace:
            return
        
        try:
            # Query for similar protocols
            query = f"{context.protocol_type} {context.project_name} vulnerability exploit"
            results = self.palace.retrieve(
                query,
                rooms=[Room.EXPLOITS, Room.RESEARCH, Room.GENERAL],
                top_k=5
            )
            
            for memory in results.memories:
                if memory.memory_type == MemoryType.HISTORICAL_EXPLOIT:
                    context.past_exploits.append({
                        "description": memory.association,
                        "source": memory.metadata.get("source", "LEANN")
                    })
                elif memory.memory_type == MemoryType.RESEARCH:
                    context.similar_protocols.append(memory.association)
            
            print(f"[Researcher] Found {len(context.past_exploits)} relevant past exploits")
            
        except Exception as e:
            print(f"[Researcher] Historical research failed: {e}")
    
    def _generate_focus_areas(self, context: ResearchContext, project_data: Dict):
        """Generate audit focus areas based on research."""
        # Priority focus based on protocol type
        focus_map = {
            "dex": ["Price manipulation", "Reentrancy in swaps", "Slippage protection", "Fee calculation"],
            "lending": ["Oracle validation", "Liquidation logic", "Interest accrual", "Collateral handling"],
            "staking": ["Reward calculation", "Share accounting", "Withdrawal logic", "Compounding"],
            "bridge": ["Message validation", "Replay protection", "Finality handling"],
            "nft": ["Minting logic", "Access control", "Metadata handling"],
            "dao": ["Voting power", "Proposal execution", "Timelock bypass"],
        }
        
        protocol_type = context.protocol_type.lower()
        context.audit_focus_areas = focus_map.get(protocol_type, [
            "Access control",
            "Reentrancy",
            "Input validation",
            "Math operations"
        ])
        
        # High risk patterns to search for
        context.high_risk_patterns = [
            "external call before state change",
            "unchecked arithmetic",
            "tx.origin authentication",
            "block.timestamp dependency",
            "delegatecall to user input",
            "missing access control",
            "hardcoded addresses",
            "uninitialized storage",
        ]
        
        context.confidence += 0.1
    
    def _store_research(self, context: ResearchContext):
        """Store research in LEANN Mind Palace."""
        if not self.palace:
            return
        
        try:
            # Store protocol summary
            self.palace.encode_research(
                content=f"Protocol: {context.project_name}\n"
                        f"Type: {context.protocol_type}\n"
                        f"Summary: {context.protocol_summary}\n"
                        f"Invariants: {', '.join(context.key_invariants)}",
                source="researcher",
                topic=f"Protocol Analysis: {context.project_name}"
            )
            
            # Store vulnerabilities context
            vuln_summary = "\n".join([
                f"- {v['name']} ({v['severity']}): {v['description']}"
                for v in context.common_vulnerabilities[:5]
            ])
            self.palace.encode_research(
                content=f"Common vulnerabilities for {context.protocol_type}:\n{vuln_summary}",
                source="researcher",
                topic=f"Vulnerabilities for {context.protocol_type}"
            )
            
            # Build index if we added new content
            self.palace.build_index()
            
            print(f"[Researcher] Research stored in LEANN Mind Palace")
            
        except Exception as e:
            print(f"[Researcher] Failed to store research: {e}")


# ==============================================================================
# CLI
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(description="Researcher - AI-powered pre-audit research")
    parser.add_argument("--project", "-p", required=True, help="Path to project.json from analyzer")
    parser.add_argument("--output", "-o", help="Output JSON file (optional)")
    
    args = parser.parse_args()
    
    try:
        # Load project data
        with open(args.project, 'r') as f:
            project_data = json.load(f)
        
        # Run research
        researcher = ResearcherAgent()
        context = researcher.research(project_data)
        
        result = context.to_dict()
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"[Researcher] Results saved to {args.output}")
        else:
            print(json.dumps(result, indent=2))
            
    except Exception as e:
        print(f"[Researcher] Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
