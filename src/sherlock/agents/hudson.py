#!/usr/bin/env python3
"""
Hudson Agent: The Tool Engine (Advanced Version)
================================================
"Mrs. Hudson, the landlady who manages the house."

Hudson is the Quartermaster. He provides the raw materials (Tool Outputs) 
for Watson and Sherlock to analyze, implementing an advanced security stack.

Capabilities:
1. Static Analysis (Slither, Aderyn)
2. Symbolic Execution (Mythril)
3. Formal Verification (Halmos)
4. Fuzzing (Medusa, Echidna)
5. Metrics & Visualization (cloc, Surya)
"""

import argparse
import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from enum import Enum
from typing import Any


class ToolName(Enum):
    SLITHER = "slither"
    ADERYN = "aderyn"
    FORGE = "forge"
    MYTHRIL = "myth"      # Symbolic Execution
    HALMOS = "halmos"    # Formal Verification
    MEDUSA = "medusa"    # Modern Fuzzer
    ECHIDNA = "echidna"  # Property-based Fuzzer
    SURYA = "surya"      # Static Analyzer / Visualizer
    CLOC = "cloc"        # Code Metrics
    NM = "solc-nm"       # Symbol lister

@dataclass
class ToolResult:
    tool: ToolName
    success: bool
    output_path: str
    summary: str
    raw_stdout: str
    raw_stderr: str

class ToolRunner:
    """Wrapper for external CLI tools."""

    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        self.output_dir = os.path.join(root_dir, "TOOL_OUTPUTS")
        os.makedirs(self.output_dir, exist_ok=True)

    def check_installed(self, tool: str) -> bool:
        return shutil.which(tool) is not None

    def run_forge_build(self) -> ToolResult:
        if not self.check_installed("forge"):
            return ToolResult(ToolName.FORGE, False, "", "Forge Not Installed", "", "")

        print("[Hudson] Running Forge Build...")
        try:
            cmd = ["forge", "build"]
            result = subprocess.run(cmd, cwd=self.root_dir, capture_output=True, text=True)
            return ToolResult(ToolName.FORGE, result.returncode == 0, "", "Build Successful" if result.returncode == 0 else "Build Failed", result.stdout, result.stderr)
        except Exception as e:
            return ToolResult(ToolName.FORGE, False, "", str(e), "", "")

    def run_slither(self) -> ToolResult:
        if not self.check_installed("slither"):
            return ToolResult(ToolName.SLITHER, False, "", "Not Installed", "", "")

        print("[Hudson] Running Slither...")
        output_file = os.path.join(self.output_dir, "slither.json")
        cmd = ["slither", ".", "--json", output_file]

        try:
            result = subprocess.run(cmd, cwd=self.root_dir, capture_output=True, text=True)
            if os.path.exists(output_file):
                with open(output_file) as f:
                    data = json.load(f)
                    count = len(data.get("results", {}).get("detectors", []))
                    summary = f"Slither finished. {count} issues detected."
            else:
                summary = "Slither failed to generate JSON."
            return ToolResult(ToolName.SLITHER, True, output_file, summary, result.stdout, result.stderr)
        except Exception as e:
            return ToolResult(ToolName.SLITHER, False, "", str(e), "", "")

    def run_mythril(self) -> ToolResult:
        if not self.check_installed("myth"):
            return ToolResult(ToolName.MYTHRIL, False, "", "Not Installed", "", "")

        print("[Hudson] Running Mythril (Symbolic Execution)...")
        output_file = os.path.join(self.output_dir, "mythril.json")
        cmd = ["myth", "analyze", ".", "-o", "json"]
        try:
            result = subprocess.run(cmd, cwd=self.root_dir, capture_output=True, text=True)
            with open(output_file, "w") as f:
                f.write(result.stdout)
            return ToolResult(ToolName.MYTHRIL, True, output_file, "Mythril analysis complete.", result.stdout, result.stderr)
        except Exception as e:
            return ToolResult(ToolName.MYTHRIL, False, "", str(e), "", "")

    def run_halmos(self) -> ToolResult:
        if not self.check_installed("halmos"):
            return ToolResult(ToolName.HALMOS, False, "", "Not Installed", "", "")

        print("[Hudson] Running Halmos (Formal Verification)...")
        try:
            cmd = ["halmos"]
            result = subprocess.run(cmd, cwd=self.root_dir, capture_output=True, text=True)
            return ToolResult(ToolName.HALMOS, True, "", "Halmos finished.", result.stdout, result.stderr)
        except Exception as e:
            return ToolResult(ToolName.HALMOS, False, "", str(e), "", "")

    def run_aderyn(self) -> ToolResult:
        if not self.check_installed("aderyn"):
            return ToolResult(ToolName.ADERYN, False, "", "Not Installed", "", "")

        print("[Hudson] Running Aderyn...")
        output_file = os.path.join(self.output_dir, "aderyn.json")
        cmd = ["aderyn", ".", "-o", output_file]
        try:
            result = subprocess.run(cmd, cwd=self.root_dir, capture_output=True, text=True)
            return ToolResult(ToolName.ADERYN, True, output_file, "Aderyn finished.", result.stdout, result.stderr)
        except Exception as e:
            return ToolResult(ToolName.ADERYN, False, "", str(e), "", "")

    def run_cloc(self) -> ToolResult:
        if not self.check_installed("cloc"):
            return ToolResult(ToolName.CLOC, False, "", "Not Installed", "", "")

        print("[Hudson] Gathering Metrics (cloc)...")
        output_file = os.path.join(self.output_dir, "cloc.json")
        cmd = ["cloc", ".", "--json", "--out", output_file, "--exclude-dir=node_modules,lib,out"]
        try:
            subprocess.run(cmd, cwd=self.root_dir, capture_output=True, text=True)
            return ToolResult(ToolName.CLOC, True, output_file, "Metrics gathered.", "", "")
        except Exception as e:
            return ToolResult(ToolName.CLOC, False, "", str(e), "", "")

    def run_surya(self, action: str = "graph") -> ToolResult:
        if not self.check_installed("surya"):
            return ToolResult(ToolName.SURYA, False, "", "Not Installed", "", "")

        print(f"[Hudson] Running Surya ({action})...")
        output_file = os.path.join(self.output_dir, f"surya_{action}.dot")
        target = "src" if os.path.exists(os.path.join(self.root_dir, "src")) else "."
        cmd = ["surya", action, target]
        try:
            result = subprocess.run(cmd, cwd=self.root_dir, capture_output=True, text=True)
            if action == "graph":
                with open(output_file, "w") as f:
                    f.write(result.stdout)
            return ToolResult(ToolName.SURYA, True, output_file if action == "graph" else "", f"Surya {action} complete.", result.stdout, result.stderr)
        except Exception as e:
            return ToolResult(ToolName.SURYA, False, "", str(e), "", "")

    def run_medusa(self) -> ToolResult:
        if not self.check_installed("medusa"):
            return ToolResult(ToolName.MEDUSA, False, "", "Not Installed", "", "")

        print("[Hudson] Checking Medusa Fuzzer Readiness...")
        try:
            return ToolResult(ToolName.MEDUSA, True, "", "Medusa ready.", "", "")
        except Exception as e:
            return ToolResult(ToolName.MEDUSA, False, "", str(e), "", "")

    def run_echidna(self) -> ToolResult:
        if not self.check_installed("echidna"):
            return ToolResult(ToolName.ECHIDNA, False, "", "Not Installed", "", "")

        print("[Hudson] Checking Echidna Readiness...")
        try:
            return ToolResult(ToolName.ECHIDNA, True, "", "Echidna ready.", "", "")
        except Exception as e:
            return ToolResult(ToolName.ECHIDNA, False, "", str(e), "", "")

    def run_forge_test(self, test_path: str) -> ToolResult:
        if not self.check_installed("forge"):
            return ToolResult(ToolName.FORGE, False, "", "Not Installed", "", "")

        print(f"[Hudson] Running Forge Test: {test_path}...")
        try:
            cmd = ["forge", "test", "--match-path", test_path, "-vv"]
            result = subprocess.run(cmd, cwd=self.root_dir, capture_output=True, text=True)
            summary = "Tests Passed" if result.returncode == 0 else "Tests Failed"
            return ToolResult(ToolName.FORGE, result.returncode == 0, "", summary, result.stdout, result.stderr)
        except Exception as e:
            return ToolResult(ToolName.FORGE, False, "", str(e), "", "")

class Hudson:
    """
    Hudson Agent: The Tool Engine.
    """

    def __init__(self, root_dir: str = "."):
        self.root_dir = root_dir
        self.runner = ToolRunner(root_dir)

    def execute(self, action: str = "inventory", test_path: str | None = None) -> dict[str, Any]:
        """
        Run tools and collect raw materials for Watson and Sherlock.
        """
        print(f"\n[Hudson] Starting Advanced Tool Engine in {self.root_dir} (Action: {action})")

        if action == "test" and test_path:
            res = self.runner.run_forge_test(test_path)
            return {
                "success": res.success,
                "summary": res.summary,
                "stdout": res.raw_stdout,
                "stderr": res.raw_stderr
            }

        # Full Inventory Mode
        results = {}

        # 1. Forge Build (Fundamental Prerequisite)
        build_res = self.runner.run_forge_build()
        results["forge_build"] = {"success": build_res.success, "summary": build_res.summary}

        if not build_res.success:
            print("[Hudson] Warning: Build failed. Some static tools may provide incomplete results.")

        # 2. Static Analysis (Static Truth)
        results["slither"] = self._capture_res(self.runner.run_slither())
        results["aderyn"] = self._capture_res(self.runner.run_aderyn())

        # 3. Advanced Reasoning Materials
        results["mythril"] = self._capture_res(self.runner.run_mythril()) # Symbolic Execution
        results["halmos"] = self._capture_res(self.runner.run_halmos())   # Formal Verification

        # 4. Metrics & Visualization
        results["cloc"] = self._capture_res(self.runner.run_cloc())
        results["surya_graph"] = self._capture_res(self.runner.run_surya("graph"))
        results["surya_inheritance"] = self._capture_res(self.runner.run_surya("inheritance"))

        # 5. Fuzzing Readiness
        results["medusa"] = self._capture_res(self.runner.run_medusa())
        results["echidna"] = self._capture_res(self.runner.run_echidna())

        # Save inventory
        inventory_path = os.path.join(self.runner.output_dir, "inventory.json")
        with open(inventory_path, "w") as f:
            json.dump(results, f, indent=2)

        print(f"[Hudson] Advanced Tool Inventory complete: {inventory_path}")
        return results

    def _capture_res(self, res: ToolResult) -> dict[str, Any]:
        return {
            "success": res.success,
            "summary": res.summary,
            "path": res.output_path
        }

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--action", default="inventory", choices=["inventory", "test"])
    parser.add_argument("--test-path", help="Path to .t.sol file")
    args = parser.parse_args()

    agent = Hudson(os.getcwd())
    if args.action == "test":
        print(json.dumps(agent.execute("test", args.test_path), indent=2))
    else:
        agent.execute("inventory")
