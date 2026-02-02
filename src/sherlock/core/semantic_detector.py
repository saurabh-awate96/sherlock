import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from sherlock.core.config_loader import ConfigLoader
    from sherlock.core.db import Database

@dataclass
class Detection:
    primitive: str
    confidence: float
    evidence: Dict[str, Any]

class SemanticDetector:
    """
    Use Foundry's forge inspect to detect primitives
    No more regex guessing
    """

    def __init__(self, config_loader: 'ConfigLoader'):
        self.config = config_loader

    def _get_project_root(self, contract_path: str) -> str:
        """Find the directory containing foundry.toml or return current dir"""
        path = Path(contract_path).resolve()
        for parent in path.parents:
            if (parent / "foundry.toml").exists():
                return str(parent)
        return "."

    def detect_primitive(self, contract_path: str, db: Optional['Database'] = None) -> Detection:
        # Step 1: Get storage layout
        storage = self.get_storage_layout(contract_path)

        # Step 2: Get function signatures
        functions = self.get_functions(contract_path)

        # Step 2.5: Fingerprint & Similarity Check (The "Cousin" Check)
        similar_issues = []
        if db:
            from sherlock.core.similarity import SimilarityEngine
            sim_engine = SimilarityEngine(db)
            contract_name = contract_path.split("/")[-1]
            fingerprint = sim_engine.fingerprint_contract(contract_name, storage, functions)
            similar_issues = sim_engine.find_similar_issues(fingerprint)
            if similar_issues:
                # In production usage, use logger instead of print
                pass 

        # Step 3: Match against known patterns
        scores: Dict[str, float] = {}
        evidence_collection: Dict[str, Dict[str, Any]] = {}

        for primitive in self.config.get_all_primitives():
            primitive_config = self.config.get_primitive_config(primitive)
            score, evidence = self.score_primitive(primitive_config, storage, functions)

            if similar_issues:
                evidence['similar_issues'] = similar_issues

            scores[primitive] = score
            evidence_collection[primitive] = evidence

        # Return best match
        if not scores:
            return Detection(primitive="unknown", confidence=0.0, evidence={})

        best_primitive = max(scores.items(), key=lambda x: x[1])[0]
        best_score = scores[best_primitive]
        
        # Check minimum confidence
        threshold = self.config.get_primitive_config(best_primitive).get('detection', {}).get('minimum_confidence', 0.1)
        
        if best_score < threshold:
             return Detection(primitive="unknown", confidence=best_score, evidence=evidence_collection[best_primitive])

        return Detection(
            primitive=best_primitive,
            confidence=best_score,
            evidence=evidence_collection[best_primitive]
        )

    def get_storage_layout(self, contract_path: str) -> Dict[str, Any]:
        """Use forge inspect to get actual storage"""
        try:
            root_dir = self._get_project_root(contract_path)
            # Use relative path from root to avoid path issues in forge
            try:
                rel_path = str(Path(contract_path).resolve().relative_to(Path(root_dir).resolve()))
            except ValueError:
                rel_path = contract_path

            result = subprocess.run(
                ['forge', 'inspect', rel_path, 'storage-layout', '--json'],
                capture_output=True,
                text=True,
                check=True,
                cwd=root_dir
            )
            return json.loads(result.stdout)
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            # Fallback or empty if compilation fails (should be handled by compiler loop later)
            return {"storage": []}

    def get_functions(self, contract_path: str) -> Dict[str, str]:
        """Get function signatures"""
        try:
            root_dir = self._get_project_root(contract_path)
            # Use relative path from root
            try:
                rel_path = str(Path(contract_path).resolve().relative_to(Path(root_dir).resolve()))
            except ValueError:
                rel_path = contract_path

            result = subprocess.run(
                ['forge', 'inspect', rel_path, 'methods', '--json'],
                capture_output=True,
                text=True,
                check=True,
                cwd=root_dir
            )
            print(f"DEBUG: {rel_path} methods: {result.stdout[:200]}...") # DEBUG
            return json.loads(result.stdout)
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            return {}

    def score_primitive(self, config: Dict[str, Any], storage: Dict[str, Any], functions: Dict[str, str]) -> Tuple[float, Dict[str, Any]]:
        """
        Generic scorer based on config requirements
        """
        score = 0.0
        total_weight = 0.0
        evidence: Dict[str, Any] = {
            'storage_matches': [],
            'function_matches': [],
            'missing': []
        }

        # 1. Check Storage Requirements
        storage_reqs = config.get('detection', {}).get('storage_requirements', [])
        for req in storage_reqs:
            weight = 1.0 # Base weight for each requirement
            total_weight += weight

            matches = self._find_storage_matches(storage, req)
            if matches:
                # Check minimum count if specified
                min_count = req.get('minimum_count', 1)
                if len(matches) >= min_count:
                    score += weight
                    evidence['storage_matches'].extend(matches)
                else:
                    evidence['missing'].append(f"Storage {req.get('name_pattern')} (found {len(matches)} < {min_count})")
            else:
                 evidence['missing'].append(f"Storage {req.get('name_pattern')}")

        # 2. Check Function Requirements
        func_reqs = config.get('detection', {}).get('function_requirements', [])
        for req in func_reqs:
            weight = 1.0
            total_weight += weight

            match = self._find_function_match(functions, req)
            if match:
                score += weight
                evidence['function_matches'].append(match)
            else:
                evidence['missing'].append(f"Function {req.get('name_pattern')}")

        # Normalize score
        final_score = score / total_weight if total_weight > 0 else 0.0

        return final_score, evidence

    def _find_storage_matches(self, storage_layout: Dict[str, Any], req: Dict[str, Any]) -> List[str]:
        matches = []
        name_pattern = req.get('name_pattern', '')
        type_pattern = req.get('type', '')

        types_map = storage_layout.get('types', {})

        for item in storage_layout.get('storage', []):
            label = item.get('label', '')
            item_type_key = item.get('type', '')
            
            # Resolve readable type name from types map if possible
            item_type_label = item_type_key
            if item_type_key in types_map:
                item_type_label = types_map[item_type_key].get('label', item_type_key)
            
            name_match = re.search(name_pattern, label, re.IGNORECASE) if name_pattern else True
            
            # Match against both the raw key (t_uint256) and readable label (uint256)
            type_match = False
            if not type_pattern:
                type_match = True
            else:
                 type_match = (type_pattern in item_type_key) or (type_pattern in item_type_label)

            if name_match and type_match:
                matches.append(f"{label} ({item_type_label})")

        return matches

    def _find_function_match(self, methods: Dict[str, str], req: Dict[str, Any]) -> Optional[str]:
        # methods is {"signature": "selector"} or similar from forge inspect
        # Actually `forge inspect methods` returns { "method(args)": "selector" }

        pattern = req.get('name_pattern', '')
        for signature in methods:
            # Check name pattern
            # Signature format: "deposit(uint256)"
            func_name = signature.split('(')[0]
            if re.search(pattern, func_name, re.IGNORECASE):
                return signature
        return None
