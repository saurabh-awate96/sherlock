"""
Universal Orchestrator: Module Registry
========================================

Runtime Capability Introspection - Dynamic Discovery without Configuration.

"To avoid configuration files, we use Python's importlib and inspect 
modules for Dynamic Module Discovery."

This module implements:
- Plugin Architecture: Modules in modules/ directory
- Duck Typing: Check for execute() + manifest() methods
- Capability Manifests: Standardized JSON schema for tool description
- Hot Reloading: Refresh capabilities at runtime
"""

import os
import sys
import importlib
import importlib.util
import inspect
import hashlib
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Callable, Set
from datetime import datetime
from enum import Enum
from pathlib import Path


# ==============================================================================
# Data Structures
# ==============================================================================

class ModuleType(Enum):
    """Types of modules in the orchestration system."""
    RECONNAISSANCE = "reconnaissance"    # Observation/sensing
    LOGIC = "logic"                       # Reasoning/planning
    VULNERABILITY = "vulnerability"       # Action/exploitation
    SYNTHESIS = "synthesis"               # Aggregation/reporting
    UTILITY = "utility"                   # Helper functions


@dataclass
class Tool:
    """A single tool/capability exposed by a module."""
    name: str
    description: str
    intent_tags: List[str]
    input_schema: Dict[str, str]
    output_schema: Dict[str, str] = field(default_factory=dict)
    cost_estimate: float = 0.5  # 0-1 normalized cost


@dataclass
class CostProfile:
    """Cost characteristics of a module."""
    latency: str = "medium"      # low, medium, high
    compute: str = "medium"      # low, medium, high
    risk: str = "low"            # low, medium, high
    rate_limited: bool = False
    
    def to_numeric(self) -> float:
        """Convert to numeric cost for utility calculation."""
        latency_map = {"low": 0.1, "medium": 0.3, "high": 0.6}
        compute_map = {"low": 0.1, "medium": 0.2, "high": 0.4}
        risk_map = {"low": 0.0, "medium": 0.2, "high": 0.5}
        
        return (
            latency_map.get(self.latency, 0.3) +
            compute_map.get(self.compute, 0.2) +
            risk_map.get(self.risk, 0.1)
        )


@dataclass
class ModuleCapability:
    """Complete capability manifest for a module."""
    module_id: str
    module_type: ModuleType
    version: str
    tools: List[Tool]
    intent_tags: List[str]
    cost_profile: CostProfile
    
    # Runtime metadata
    module_path: Optional[str] = None
    module_instance: Optional[Any] = None
    last_refreshed: datetime = field(default_factory=datetime.now)
    
    def supports_intent(self, intent: str) -> bool:
        """Check if module supports given intent."""
        intent_lower = intent.lower()
        return any(tag in intent_lower for tag in self.intent_tags)
    
    def get_tool(self, tool_name: str) -> Optional[Tool]:
        """Get a specific tool by name."""
        for tool in self.tools:
            if tool.name == tool_name:
                return tool
        return None


@dataclass
class RegistryStats:
    """Statistics about the module registry."""
    total_modules: int
    total_tools: int
    by_type: Dict[str, int]
    last_refresh: datetime


# ==============================================================================
# Module Registry
# ==============================================================================

class ModuleRegistry:
    """
    Dynamic Module Discovery via Runtime Introspection.
    
    This registry eliminates the need for configuration files by:
    1. Scanning the modules directory at runtime
    2. Loading modules that implement the required interface
    3. Building a capability registry from manifest() methods
    4. Supporting hot-reload for dynamic updates
    
    "If the object walks like a module and quacks like a module,
    the Orchestrator integrates it."
    """
    
    # Required interface methods (duck typing)
    REQUIRED_INTERFACE = ['execute', 'manifest']
    
    def __init__(
        self,
        modules_dir: Optional[str] = None,
        auto_discover: bool = True
    ):
        """
        Initialize the Module Registry.
        
        Args:
            modules_dir: Directory containing module files
            auto_discover: Whether to scan on initialization
        """
        if modules_dir is None:
            # Default to agents/ directory relative to this file
            self_path = Path(__file__).parent
            modules_dir = str(self_path)
        
        self.modules_dir = modules_dir
        self.capabilities: Dict[str, ModuleCapability] = {}
        self.module_instances: Dict[str, Any] = {}
        self._intent_index: Dict[str, Set[str]] = {}  # intent -> module_ids
        
        if auto_discover:
            self.refresh_capabilities()
        
        print(f"[Registry] Initialized with modules_dir: {modules_dir}")
    
    # --------------------------------------------------------------------------
    # Core Discovery Methods
    # --------------------------------------------------------------------------
    
    def refresh_capabilities(self) -> Dict[str, ModuleCapability]:
        """
        Scan modules and build capability registry.
        
        This is the core introspection mechanism. It:
        1. Scans the modules directory
        2. Loads each Python file
        3. Checks for required interface
        4. Extracts capability manifest
        5. Registers in the capability index
        
        Returns:
            Dict of module_id -> ModuleCapability
        """
        print("[Registry] Refreshing capabilities...")
        
        discovered = 0
        failed = 0
        
        for module_path in self._scan_modules_directory():
            try:
                capability = self._load_and_register(module_path)
                if capability:
                    self.capabilities[capability.module_id] = capability
                    self._update_intent_index(capability)
                    discovered += 1
            except Exception as e:
                print(f"[Registry] Failed to load {module_path}: {e}")
                failed += 1
        
        print(f"[Registry] Discovered {discovered} modules, {failed} failed")
        
        return self.capabilities
    
    def _scan_modules_directory(self) -> List[str]:
        """Scan directory for Python module files."""
        module_files = []
        
        if not os.path.isdir(self.modules_dir):
            print(f"[Registry] Warning: {self.modules_dir} is not a directory")
            return []
        
        for filename in os.listdir(self.modules_dir):
            if filename.endswith('.py') and not filename.startswith('_'):
                # Skip known non-module files
                if filename in ['universal_orchestrator.py', 'module_registry.py',
                               'context_manager.py', 'intent_engine.py',
                               'probabilistic_router.py', 'self_calibration.py',
                               'policy_engine.py']:
                    continue
                
                module_files.append(os.path.join(self.modules_dir, filename))
        
        return module_files
    
    def _load_and_register(self, module_path: str) -> Optional[ModuleCapability]:
        """Load a module and extract its capability manifest."""
        module_name = Path(module_path).stem
        
        # Dynamic import
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        if spec is None or spec.loader is None:
            return None
        
        module = importlib.util.module_from_spec(spec)
        
        try:
            spec.loader.exec_module(module)
        except Exception as e:
            print(f"[Registry] Error loading {module_name}: {e}")
            return None
        
        # Find classes that implement the interface
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if self._implements_interface(obj):
                return self._extract_capability(obj, module_path, module_name)
        
        # Check module-level functions
        if self._implements_interface(module):
            return self._extract_capability_from_module(module, module_path, module_name)
        
        return None
    
    def _implements_interface(self, obj: Any) -> bool:
        """Check if object implements required interface (duck typing)."""
        for method in self.REQUIRED_INTERFACE:
            if not hasattr(obj, method):
                return False
            if not callable(getattr(obj, method)):
                return False
        return True
    
    def _extract_capability(
        self,
        cls: type,
        module_path: str,
        module_name: str
    ) -> Optional[ModuleCapability]:
        """Extract capability from a class that implements the interface."""
        try:
            # Instantiate the class
            instance = cls()
            
            # Get manifest
            manifest = instance.manifest()
            
            return self._parse_manifest(manifest, module_path, instance)
        except Exception as e:
            print(f"[Registry] Error extracting capability from {module_name}: {e}")
            return None
    
    def _extract_capability_from_module(
        self,
        module: Any,
        module_path: str,
        module_name: str
    ) -> Optional[ModuleCapability]:
        """Extract capability from module-level functions."""
        try:
            manifest = module.manifest()
            return self._parse_manifest(manifest, module_path, module)
        except Exception as e:
            print(f"[Registry] Error extracting capability from module {module_name}: {e}")
            return None
    
    def _parse_manifest(
        self,
        manifest: Dict[str, Any],
        module_path: str,
        instance: Any
    ) -> ModuleCapability:
        """Parse manifest dict into ModuleCapability."""
        # Parse tools
        tools = []
        for tool_data in manifest.get('tools', []):
            tools.append(Tool(
                name=tool_data.get('name', 'unknown'),
                description=tool_data.get('description', ''),
                intent_tags=tool_data.get('intent_tags', []),
                input_schema=tool_data.get('input_schema', {}),
                output_schema=tool_data.get('output_schema', {}),
                cost_estimate=tool_data.get('cost_estimate', 0.5)
            ))
        
        # Parse cost profile
        cost_data = manifest.get('cost_profile', {})
        cost_profile = CostProfile(
            latency=cost_data.get('latency', 'medium'),
            compute=cost_data.get('compute', 'medium'),
            risk=cost_data.get('risk', 'low'),
            rate_limited=cost_data.get('rate_limited', False)
        )
        
        # Parse module type
        type_str = manifest.get('module_type', 'utility')
        try:
            module_type = ModuleType(type_str)
        except ValueError:
            module_type = ModuleType.UTILITY
        
        # Create capability
        capability = ModuleCapability(
            module_id=manifest.get('module_id', Path(module_path).stem),
            module_type=module_type,
            version=manifest.get('version', '1.0.0'),
            tools=tools,
            intent_tags=manifest.get('intent_tags', []),
            cost_profile=cost_profile,
            module_path=module_path,
            module_instance=instance
        )
        
        # Store instance for later use
        self.module_instances[capability.module_id] = instance
        
        return capability
    
    def _update_intent_index(self, capability: ModuleCapability):
        """Update the intent -> modules index."""
        for tag in capability.intent_tags:
            tag_lower = tag.lower()
            if tag_lower not in self._intent_index:
                self._intent_index[tag_lower] = set()
            self._intent_index[tag_lower].add(capability.module_id)
        
        # Also index tool-level intent tags
        for tool in capability.tools:
            for tag in tool.intent_tags:
                tag_lower = tag.lower()
                if tag_lower not in self._intent_index:
                    self._intent_index[tag_lower] = set()
                self._intent_index[tag_lower].add(capability.module_id)
    
    # --------------------------------------------------------------------------
    # Query Methods
    # --------------------------------------------------------------------------
    
    def get_module(self, module_id: str) -> Optional[Any]:
        """Get module instance by ID."""
        return self.module_instances.get(module_id)
    
    def get_capability(self, module_id: str) -> Optional[ModuleCapability]:
        """Get capability manifest by module ID."""
        return self.capabilities.get(module_id)
    
    def find_by_intent(self, intent: str) -> List[ModuleCapability]:
        """Find modules that support a given intent."""
        intent_lower = intent.lower()
        
        matching = []
        for tag, module_ids in self._intent_index.items():
            if tag in intent_lower or intent_lower in tag:
                for module_id in module_ids:
                    if module_id in self.capabilities:
                        cap = self.capabilities[module_id]
                        if cap not in matching:
                            matching.append(cap)
        
        return matching
    
    def find_by_type(self, module_type: ModuleType) -> List[ModuleCapability]:
        """Find modules by type."""
        return [
            cap for cap in self.capabilities.values()
            if cap.module_type == module_type
        ]
    
    def find_tool(self, tool_name: str) -> Optional[tuple]:
        """Find a tool by name, returns (module_id, tool)."""
        for module_id, cap in self.capabilities.items():
            tool = cap.get_tool(tool_name)
            if tool:
                return (module_id, tool)
        return None
    
    def get_all_intent_tags(self) -> Set[str]:
        """Get all registered intent tags."""
        return set(self._intent_index.keys())
    
    # --------------------------------------------------------------------------
    # Registration Methods (for programmatic registration)
    # --------------------------------------------------------------------------
    
    def register(self, module_instance: Any, module_id: Optional[str] = None):
        """Programmatically register a module."""
        if not self._implements_interface(module_instance):
            raise ValueError(f"Module must implement {self.REQUIRED_INTERFACE}")
        
        manifest = module_instance.manifest()
        
        capability = ModuleCapability(
            module_id=module_id or manifest.get('module_id', 'unknown'),
            module_type=ModuleType(manifest.get('module_type', 'utility')),
            version=manifest.get('version', '1.0.0'),
            tools=[
                Tool(**t) for t in manifest.get('tools', [])
            ],
            intent_tags=manifest.get('intent_tags', []),
            cost_profile=CostProfile(**manifest.get('cost_profile', {})),
            module_instance=module_instance
        )
        
        self.capabilities[capability.module_id] = capability
        self.module_instances[capability.module_id] = module_instance
        self._update_intent_index(capability)
        
        print(f"[Registry] Registered: {capability.module_id}")
    
    def unregister(self, module_id: str):
        """Remove a module from the registry."""
        if module_id in self.capabilities:
            del self.capabilities[module_id]
        if module_id in self.module_instances:
            del self.module_instances[module_id]
        
        # Clean intent index
        for tag, ids in list(self._intent_index.items()):
            ids.discard(module_id)
            if not ids:
                del self._intent_index[tag]
    
    # --------------------------------------------------------------------------
    # Statistics
    # --------------------------------------------------------------------------
    
    def get_statistics(self) -> RegistryStats:
        """Get registry statistics."""
        by_type = {}
        total_tools = 0
        
        for cap in self.capabilities.values():
            type_key = cap.module_type.value
            by_type[type_key] = by_type.get(type_key, 0) + 1
            total_tools += len(cap.tools)
        
        return RegistryStats(
            total_modules=len(self.capabilities),
            total_tools=total_tools,
            by_type=by_type,
            last_refresh=datetime.now()
        )
    
    def export_capabilities(self) -> Dict[str, Any]:
        """Export all capabilities as JSON-serializable dict."""
        return {
            module_id: {
                "module_id": cap.module_id,
                "module_type": cap.module_type.value,
                "version": cap.version,
                "intent_tags": cap.intent_tags,
                "tools": [
                    {
                        "name": t.name,
                        "description": t.description,
                        "intent_tags": t.intent_tags
                    }
                    for t in cap.tools
                ],
                "cost_profile": {
                    "latency": cap.cost_profile.latency,
                    "compute": cap.cost_profile.compute,
                    "risk": cap.cost_profile.risk
                }
            }
            for module_id, cap in self.capabilities.items()
        }


# ==============================================================================
# CLI Interface
# ==============================================================================

if __name__ == "__main__":
    import json
    
    registry = ModuleRegistry()
    
    print("\n=== Registry Statistics ===")
    stats = registry.get_statistics()
    print(f"Total Modules: {stats.total_modules}")
    print(f"Total Tools: {stats.total_tools}")
    print(f"By Type: {stats.by_type}")
    
    print("\n=== Registered Capabilities ===")
    print(json.dumps(registry.export_capabilities(), indent=2))
