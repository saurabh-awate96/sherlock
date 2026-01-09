#!/usr/bin/env python3
"""
Project Analyzer: Automatic Project Detection
==============================================

Analyzes a project directory to detect:
- Framework type (Foundry, Hardhat, Brownie, raw Solidity)
- Contract scope (which files to audit)
- Protocol type (DEX, Lending, Staking, etc.)
- Dependencies and their versions
- Build and test commands

Usage:
    python project_analyzer.py --input ./contracts --output project.json
    python project_analyzer.py --input ./contracts  # prints to stdout
"""

import os
import sys
import json
import argparse
import re
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
from enum import Enum

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


# ==============================================================================
# Data Structures
# ==============================================================================

class Framework(Enum):
    FOUNDRY = "foundry"
    HARDHAT = "hardhat"
    BROWNIE = "brownie"
    TRUFFLE = "truffle"
    RAW_SOLIDITY = "raw_solidity"
    UNKNOWN = "unknown"


class ProtocolType(Enum):
    DEX = "dex"
    LENDING = "lending"
    STAKING = "staking"
    BRIDGE = "bridge"
    NFT = "nft"
    DAO = "dao"
    YIELD = "yield"
    DERIVATIVES = "derivatives"
    INSURANCE = "insurance"
    ORACLE = "oracle"
    GENERIC = "generic"
    UNKNOWN = "unknown"


@dataclass
class ProjectAnalysis:
    """Complete analysis of a project."""
    project_path: str
    project_name: str
    
    # Framework detection
    framework: Framework = Framework.UNKNOWN
    solidity_version: Optional[str] = None
    
    # Scope
    scope_directories: List[str] = field(default_factory=list)
    scope_files: List[str] = field(default_factory=list)
    total_sol_files: int = 0
    total_lines: int = 0
    
    # Protocol classification
    protocol_type: ProtocolType = ProtocolType.UNKNOWN
    protocol_description: str = ""
    
    # Dependencies
    dependencies: Dict[str, str] = field(default_factory=dict)
    
    # Commands
    build_command: str = ""
    test_command: str = ""
    
    # Test coverage
    has_tests: bool = False
    test_files: List[str] = field(default_factory=list)
    
    # README info
    readme_content: str = ""
    
    # Metadata
    analysis_confidence: float = 0.5
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_path": self.project_path,
            "project_name": self.project_name,
            "framework": self.framework.value,
            "solidity_version": self.solidity_version,
            "scope_directories": self.scope_directories,
            "scope_files": self.scope_files,
            "total_sol_files": self.total_sol_files,
            "total_lines": self.total_lines,
            "protocol_type": self.protocol_type.value,
            "protocol_description": self.protocol_description,
            "dependencies": self.dependencies,
            "build_command": self.build_command,
            "test_command": self.test_command,
            "has_tests": self.has_tests,
            "test_files": self.test_files,
            "analysis_confidence": self.analysis_confidence
        }


# ==============================================================================
# Project Analyzer
# ==============================================================================

class ProjectAnalyzer:
    """
    Analyzes a smart contract project to detect its structure and type.
    """
    
    # Framework indicators
    FRAMEWORK_INDICATORS = {
        Framework.FOUNDRY: ["foundry.toml", "forge.lock", "lib/forge-std"],
        Framework.HARDHAT: ["hardhat.config.js", "hardhat.config.ts", "node_modules/hardhat"],
        Framework.BROWNIE: ["brownie-config.yaml", "brownie-config.yml"],
        Framework.TRUFFLE: ["truffle-config.js", "truffle.js"],
    }
    
    # Source directories by framework
    SOURCE_DIRS = {
        Framework.FOUNDRY: ["src", "contracts"],
        Framework.HARDHAT: ["contracts"],
        Framework.BROWNIE: ["contracts"],
        Framework.TRUFFLE: ["contracts"],
        Framework.RAW_SOLIDITY: ["contracts", "src", "."],
    }
    
    # Test directories
    TEST_DIRS = ["test", "tests", "spec"]
    
    # Protocol type keywords
    PROTOCOL_KEYWORDS = {
        ProtocolType.DEX: ["swap", "liquidity", "pool", "amm", "router", "pair", "uniswap", "curve"],
        ProtocolType.LENDING: ["lend", "borrow", "collateral", "liquidat", "aave", "compound", "vault"],
        ProtocolType.STAKING: ["stake", "unstake", "reward", "deposit", "withdraw", "yield"],
        ProtocolType.BRIDGE: ["bridge", "cross-chain", "relay", "message", "l2", "layer2"],
        ProtocolType.NFT: ["erc721", "erc1155", "nft", "mint", "token", "collectible"],
        ProtocolType.DAO: ["governance", "vote", "proposal", "dao", "timelock"],
        ProtocolType.YIELD: ["yield", "farm", "harvest", "strategy", "vault"],
        ProtocolType.DERIVATIVES: ["option", "future", "perp", "leverage", "margin"],
        ProtocolType.INSURANCE: ["insurance", "cover", "claim", "policy"],
        ProtocolType.ORACLE: ["oracle", "price", "feed", "chainlink"],
    }
    
    def __init__(self, project_path: str):
        """Initialize analyzer with project path."""
        self.project_path = Path(project_path).resolve()
        if not self.project_path.exists():
            raise ValueError(f"Project path does not exist: {project_path}")
        
        self.analysis = ProjectAnalysis(
            project_path=str(self.project_path),
            project_name=self.project_path.name
        )
        
        # Initialize LLM if available
        self.llm = LLM() if LLM_AVAILABLE else None
    
    def analyze(self) -> ProjectAnalysis:
        """Run full project analysis."""
        print(f"[Analyzer] Analyzing project: {self.project_path}")
        
        # Step 1: Detect framework
        self._detect_framework()
        print(f"[Analyzer] Framework: {self.analysis.framework.value}")
        
        # Step 2: Find scope
        self._find_scope()
        print(f"[Analyzer] Scope: {len(self.analysis.scope_files)} files in {self.analysis.scope_directories}")
        
        # Step 3: Detect tests
        self._detect_tests()
        print(f"[Analyzer] Tests: {'Yes' if self.analysis.has_tests else 'No'} ({len(self.analysis.test_files)} files)")
        
        # Step 4: Parse dependencies
        self._parse_dependencies()
        print(f"[Analyzer] Dependencies: {len(self.analysis.dependencies)}")
        
        # Step 5: Read README
        self._read_readme()
        
        # Step 6: Determine commands
        self._determine_commands()
        print(f"[Analyzer] Build: {self.analysis.build_command}")
        
        # Step 7: Detect Solidity version
        self._detect_solidity_version()
        print(f"[Analyzer] Solidity: {self.analysis.solidity_version or 'unknown'}")
        
        # Step 8: Classify protocol type
        self._classify_protocol()
        print(f"[Analyzer] Protocol: {self.analysis.protocol_type.value}")
        
        # Step 9: Count lines
        self._count_lines()
        print(f"[Analyzer] Total lines: {self.analysis.total_lines}")
        
        return self.analysis
    
    def _detect_framework(self):
        """Detect which framework the project uses."""
        for framework, indicators in self.FRAMEWORK_INDICATORS.items():
            for indicator in indicators:
                check_path = self.project_path / indicator
                if check_path.exists():
                    self.analysis.framework = framework
                    self.analysis.analysis_confidence += 0.1
                    return
        
        # Check if there are any .sol files
        sol_files = list(self.project_path.rglob("*.sol"))
        if sol_files:
            self.analysis.framework = Framework.RAW_SOLIDITY
        else:
            self.analysis.framework = Framework.UNKNOWN
    
    def _find_scope(self):
        """Find which directories/files are in scope for audit."""
        framework = self.analysis.framework
        if framework == Framework.UNKNOWN:
            framework = Framework.RAW_SOLIDITY
        
        source_dirs = self.SOURCE_DIRS.get(framework, ["contracts", "src"])
        
        found_dirs = []
        for src_dir in source_dirs:
            src_path = self.project_path / src_dir
            if src_path.exists() and src_path.is_dir():
                found_dirs.append(src_dir)
        
        # If no standard dirs found, use root
        if not found_dirs:
            found_dirs = ["."]
        
        self.analysis.scope_directories = found_dirs
        
        # Find all Solidity files in scope
        sol_files = []
        for src_dir in found_dirs:
            src_path = self.project_path / src_dir
            for sol_file in src_path.rglob("*.sol"):
                # Exclude test files and mocks
                rel_path = str(sol_file.relative_to(self.project_path))
                if not any(x in rel_path.lower() for x in ["test", "mock", "script"]):
                    sol_files.append(rel_path)
        
        self.analysis.scope_files = sorted(sol_files)
        self.analysis.total_sol_files = len(sol_files)
    
    def _detect_tests(self):
        """Detect if project has tests."""
        for test_dir in self.TEST_DIRS:
            test_path = self.project_path / test_dir
            if test_path.exists() and test_path.is_dir():
                self.analysis.has_tests = True
                # Find test files
                for ext in ["*.sol", "*.t.sol", "*.js", "*.ts"]:
                    for test_file in test_path.rglob(ext):
                        rel_path = str(test_file.relative_to(self.project_path))
                        self.analysis.test_files.append(rel_path)
                break
    
    def _parse_dependencies(self):
        """Parse project dependencies."""
        deps = {}
        
        # Foundry: foundry.toml
        foundry_toml = self.project_path / "foundry.toml"
        if foundry_toml.exists():
            content = foundry_toml.read_text()
            # Parse remappings
            remappings = re.findall(r'remappings\s*=\s*\[(.*?)\]', content, re.DOTALL)
            if remappings:
                for line in remappings[0].split('\n'):
                    if '=' in line:
                        parts = line.strip().strip('"').strip("'").strip(',').split('=')
                        if len(parts) >= 2:
                            deps[parts[0].strip('/')] = parts[1]
        
        # Check lib/ for Foundry
        lib_path = self.project_path / "lib"
        if lib_path.exists():
            for lib_dir in lib_path.iterdir():
                if lib_dir.is_dir():
                    deps[lib_dir.name] = "local"
        
        # Hardhat: package.json
        package_json = self.project_path / "package.json"
        if package_json.exists():
            try:
                data = json.loads(package_json.read_text())
                for dep_type in ["dependencies", "devDependencies"]:
                    if dep_type in data:
                        for name, version in data[dep_type].items():
                            if any(x in name for x in ["@openzeppelin", "solmate", "solady"]):
                                deps[name] = version
            except:
                pass
        
        self.analysis.dependencies = deps
    
    def _read_readme(self):
        """Read README file for context."""
        readme_names = ["README.md", "readme.md", "README", "README.txt"]
        for readme_name in readme_names:
            readme_path = self.project_path / readme_name
            if readme_path.exists():
                try:
                    content = readme_path.read_text()
                    # Truncate to reasonable size
                    self.analysis.readme_content = content[:5000]
                    return
                except:
                    pass
    
    def _determine_commands(self):
        """Determine build and test commands."""
        framework = self.analysis.framework
        
        commands = {
            Framework.FOUNDRY: ("forge build", "forge test"),
            Framework.HARDHAT: ("npx hardhat compile", "npx hardhat test"),
            Framework.BROWNIE: ("brownie compile", "brownie test"),
            Framework.TRUFFLE: ("truffle compile", "truffle test"),
        }
        
        if framework in commands:
            self.analysis.build_command, self.analysis.test_command = commands[framework]
        else:
            self.analysis.build_command = "# Manual compilation required"
            self.analysis.test_command = "# No test framework detected"
    
    def _detect_solidity_version(self):
        """Detect Solidity version from pragma statements."""
        versions = []
        
        for sol_file in self.analysis.scope_files[:10]:  # Check first 10 files
            try:
                file_path = self.project_path / sol_file
                content = file_path.read_text()
                matches = re.findall(r'pragma\s+solidity\s+([^;]+);', content)
                for match in matches:
                    versions.append(match.strip())
            except:
                pass
        
        if versions:
            # Use most common version
            from collections import Counter
            most_common = Counter(versions).most_common(1)[0][0]
            self.analysis.solidity_version = most_common
    
    def _classify_protocol(self):
        """Classify the protocol type using keywords and AI."""
        # Collect text from file names, README, and contract names
        text_corpus = " ".join([
            self.analysis.project_name.lower(),
            " ".join(f.lower() for f in self.analysis.scope_files),
            self.analysis.readme_content.lower()[:2000] if self.analysis.readme_content else ""
        ])
        
        # Score each protocol type
        scores = {}
        for protocol_type, keywords in self.PROTOCOL_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text_corpus)
            if score > 0:
                scores[protocol_type] = score
        
        if scores:
            # Get highest scoring type
            best_type = max(scores, key=scores.get)
            self.analysis.protocol_type = best_type
            self.analysis.analysis_confidence += 0.1
        
        # Use AI for more detailed classification if available
        if self.llm and self.analysis.readme_content:
            try:
                response = self.llm.ask(
                    f"""Classify this smart contract project in 2-3 sentences.
                    
Project: {self.analysis.project_name}
Files: {', '.join(self.analysis.scope_files[:10])}
README excerpt: {self.analysis.readme_content[:1000]}

What type of protocol is this (DEX, Lending, Staking, etc.) and what does it do?""",
                    persona="mycroft"
                )
                self.analysis.protocol_description = response.content
                self.analysis.analysis_confidence += 0.2
            except Exception as e:
                print(f"[Analyzer] AI classification failed: {e}")
    
    def _count_lines(self):
        """Count total lines of Solidity code."""
        total = 0
        for sol_file in self.analysis.scope_files:
            try:
                file_path = self.project_path / sol_file
                total += len(file_path.read_text().splitlines())
            except:
                pass
        self.analysis.total_lines = total


# ==============================================================================
# CLI
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(description="Project Analyzer - Detect project structure")
    parser.add_argument("--input", "-i", required=True, help="Path to project directory")
    parser.add_argument("--output", "-o", help="Output JSON file (optional, prints to stdout if not specified)")
    parser.add_argument("--json", "-j", action="store_true", help="Output as JSON only")
    
    args = parser.parse_args()
    
    try:
        analyzer = ProjectAnalyzer(args.input)
        analysis = analyzer.analyze()
        
        result = analysis.to_dict()
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"[Analyzer] Results saved to {args.output}")
        else:
            print(json.dumps(result, indent=2))
            
    except Exception as e:
        print(f"[Analyzer] Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
