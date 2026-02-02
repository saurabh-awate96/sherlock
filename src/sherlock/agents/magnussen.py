#!/usr/bin/env python3
"""
Magnussen Agent: The Strategy & Risk Mastermind
===============================================
"I know everything having to do with you... your pressure points."

Magnussen is the STRATEGY ENGINE.
While Sherlock looks for logical contradictions (Bugs), 
Magnussen looks for Systemic Weaknesses (Design Flaws).

Focus Areas:
1.  **Centralization Risk**: "Can the admin steal the funds?"
2.  **Griefing Vectors**: "Can I lock the system for $1?" (Inverted DoS)
3.  **Incentive Misalignment**: "Is it rational to be a Liquidator?"
"""

import argparse
import json
import os
from dataclasses import dataclass
from enum import Enum
from typing import Any


class RiskType(Enum):
    CENTRALIZATION = "Centralization Risk"
    GRIEFING = "Economic Griefing"
    INCENTIVE = "Incentive Misalignment"

@dataclass
class RiskFinding:
    type: RiskType
    component: str
    description: str
    impact: str # "High" / "Medium" / "Low"
    vector: str

class MagnussenAgent:
    """
    The Napoleon of Blackmail (and Risk).
    """

    def __init__(self, root_dir: str = "."):
        self.root_dir = root_dir
        self.context = self._load_context()
        self.findings: list[RiskFinding] = []

    def _load_context(self) -> dict[str, Any]:
        path = os.path.join(self.root_dir, "AUDIT_CONTEXT.md")
        # In a real system we'd parse this md, for now we simulate simple loading
        if os.path.exists(path):
            with open(path) as f:
                return {"raw": f.read()}
        return {}

    def analyze(self, watson_output: str, output_path: str):
        print(f"[Magnussen] Analyzing pressure points in {watson_output}...")

        with open(watson_output) as f:
            observations = json.load(f)

        for obs in observations:
            self._analyze_centralization(obs)
            self._analyze_griefing(obs)

        self._save_findings(output_path)

    def _analyze_centralization(self, obs: dict[str, Any]):
        """
        Check for Admin Abuse vectors.
        "If I were the admin, could I destroy this protocol?"
        """
        content = obs.get("content", "").lower()
        location = obs.get("location", "unknown")

        # 1. Timelock Bypass
        if "onlyowner" in content or "accesscontrol" in content:
            if "timelock" not in content and "withdraw" in content:
                 self.findings.append(RiskFinding(
                    RiskType.CENTRALIZATION,
                    location,
                    "Privileged withdrawal without Timelock",
                    "High",
                    "Admin Rug Pull"
                ))

        # 2. Pausable indefinitely
        if "rescuetoken" in content or "emergencywithdraw" in content:
             self.findings.append(RiskFinding(
                RiskType.CENTRALIZATION,
                location,
                "Admin can seize tokens via rescue/emergency mechanism",
                "Critical",
                "Asset Seizure"
            ))

    def _analyze_griefing(self, obs: dict[str, Any]):
        """
        Check for 'Inverted DoS' or Asymmetric costs.
        "Can I pay 1 wei to make you pay 1 ETH?"
        """
        content = obs.get("content", "").lower()
        location = obs.get("location", "unknown")

        # 1. Loop over dynamic array (Griefing Gas Limit)
        if "for" in content and ".length" in content:
            # Heuristic: iterating over a potentially user-controlled array
            if "users" in content or "depositors" in content:
                self.findings.append(RiskFinding(
                    RiskType.GRIEFING,
                    location,
                    "Unbounded loop over user-controlled array",
                    "Medium",
                    "Gas Limit DoS"
                ))

        # 2. Dust Lock / Ratio issues
        if "require" in content and "min" in content:
            # e.g., require(amount > min_deposit) - if min is modifiable or rigid
            pass

    def _save_findings(self, path: str):
        data = [
            {
                "type": f.type.value,
                "component": f.component,
                "description": f.description,
                "impact": f.impact,
                "vector": f.vector
            }
            for f in self.findings
        ]
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"[Magnussen] Strategy analysis complete. {len(self.findings)} risks identified.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--observations", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    agent = MagnussenAgent()
    agent.analyze(args.observations, args.output)
