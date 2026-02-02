import re
from pathlib import Path


class DependencyMapper:
    """
    The Cartographer.
    Maps the dependency graph of the codebase.
    """

    def __init__(self, root_dir: str):
        self.root = Path(root_dir)
        self.graph = {} # Adjacency list: file -> [dependencies]
        self.reverse_graph = {} # file -> [dependents]

    def build_graph(self) -> list[str]:
        """
        Parse all files and build the DAG.
        Returns a topologically sorted list of files (Audit Order).
        """
        # 1. Find all solidity files
        files = list(self.root.rglob("*.sol"))

        # 2. Parse imports
        for file_path in files:
            abs_path = str(file_path.absolute())
            self.graph[abs_path] = self._parse_imports(file_path)

        # 3. Build Reverse Graph (for impact analysis)
        for dependent, dependencies in self.graph.items():
            if dependent not in self.reverse_graph:
                self.reverse_graph[dependent] = []
            for dep in dependencies:
                if dep not in self.reverse_graph:
                    self.reverse_graph[dep] = []
                self.reverse_graph[dep].append(dependent)

        # 4. Topological Sort (Kahn's Algorithm)
        return self._topological_sort()

    def _parse_imports(self, file_path: Path) -> list[str]:
        """
        Extract absolute paths of imported files.
        Handles:
        - import "./Foo.sol";
        - import {Foo} from "./Foo.sol";
        - import "forge-std/Test.sol"; (Ignored/External)
        """
        imports = []
        try:
            content = file_path.read_text()
            # Regex for import path
            # Captures content inside quotes
            matches = re.findall(r'import\s+(?:(?:{[^}]+}\s+from\s+)?["\']([^"\']+)["\']|["\']([^"\']+)["\'])', content)

            for m in matches:
                # regex returns tuple of groups, pick non-empty one
                rel_path = m[0] or m[1]

                # Resolve path
                if rel_path.startswith("."):
                    # Local import
                    resolved = (file_path.parent / rel_path).resolve()
                    if resolved.exists():
                        imports.append(str(resolved))
                else:
                    # Remapping/Library import (e.g. @openzeppelin)
                    # For now, we ignore external libs in the graph unless we map remappings
                    pass

        except Exception as e:
            print(f"[Mapper] Error parsing {file_path}: {e}")

        return imports

    def _topological_sort(self) -> list[str]:
        """
        Return files in order: Dependencies first, then Dependents.
        """
        # Calculate in-degree (number of dependencies)
        in_degree = dict.fromkeys(self.graph, 0)
        for u in self.graph:
            for v in self.graph[u]:
                if v in in_degree:
                    in_degree[u] += 1 # u depends on v, so u has incoming edge?
                    # Wait, 'graph' is adjacency list?
                    # If u imports v, u depends on v.
                    # To audit v first, v must have in-degree 0?
                    # Let's standardize: Edge v -> u means "v must be audited before u"
                    pass

        # Actually, simpler:
        # Dependency Graph: U -> V means U imports V.
        # We want to audit V, then U.
        # So we want Post-Order Traversal or Topological Sort of the reverse graph?
        # Let's use a standard library or simple implementation.

        visited = set()
        stack = []

        def visit(node):
            if node in visited:
                return
            visited.add(node)

            # Visit children (dependencies) first
            for dep in self.graph.get(node, []):
                 # Only visit known source files
                 if dep in self.graph:
                    visit(dep)

            # After all deps are visited, add node
            stack.append(node)

        for node in self.graph:
            visit(node)

        # Stack now contains [Leaf, ..., Root]
        # e.g. [ERC20.sol, Vault.sol] where Vault imports ERC20.
        return stack

    def get_direct_dependencies(self, file_path: str) -> list[str]:
        return self.graph.get(file_path, [])
