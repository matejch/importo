import argparse
import ast
import importlib
import importlib.util
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple, Union

import matplotlib.pyplot as plt
import networkx as nx

from import_visitor import ImportVisitor


class ImportAnalyzer:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.import_graph: Dict[str, Set[Tuple[str, str]]] = defaultdict(set)
        self.module_stats: Dict[str, Dict[str, Union[int, float]]] = defaultdict(
            lambda: {"imports": 0, "imported_by": 0, "import_time": 0.0}
        )

    def analyze_project(self) -> None:
        for py_file in self.project_root.rglob("*.py"):
            if self._should_skip_file(py_file):
                continue
            self._analyze_file(py_file)

    def _should_skip_file(self, filepath: Path) -> bool:
        skip_patterns = {
            "venv",
            "env",
            "__pycache__",
            "tests",
            "test_",
            ".tox",
            ".eggs",
            "build",
            "dist",
            ".git",
            ".env",
        }
        skip_extensions = {".json", ".js", ".css", ".html"}

        return (
            any(pattern in str(filepath) for pattern in skip_patterns)
            or filepath.suffix in skip_extensions
        )

    def _analyze_file(self, filepath: Path) -> None:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read())

            module_name = self._get_module_name(filepath)
            visitor = ImportVisitor()
            visitor.visit(tree)

            for imported_module in visitor.imports:
                import_type = self._get_import_type(imported_module)
                self.import_graph[module_name].add((imported_module, import_type))
                self.module_stats[module_name]["imports"] += 1
                self.module_stats[imported_module]["imported_by"] += 1
                self.module_stats[module_name][f"{import_type}_imports"] = (
                    self.module_stats[module_name].get(f"{import_type}_imports", 0) + 1
                )

        except Exception as e:
            print(f"Error analyzing {filepath}: {e}")

    def _get_module_name(self, filepath: Path) -> str:
        relative_path = filepath.relative_to(self.project_root)
        return str(relative_path.with_suffix("")).replace("/", ".")

    def _get_import_type(self, module_name: str) -> str:
        if module_name in sys.builtin_module_names:
            return "stdlib"
        spec = importlib.util.find_spec(module_name)
        if spec is None:
            return "local"
        if "site-packages" in str(spec.origin):
            return "third-party"
        return "stdlib"

    def get_circular_dependencies(self) -> List[List[str]]:
        def find_cycles(node: str, path: List[str], visited: Set[str]) -> List[List[str]]:
            if node in path:
                cycle_start = path.index(node)
                return [path[cycle_start:]]

            cycles: List[List[str]] = []
            if node in visited:
                return cycles

            visited.add(node)
            path.append(node)

            for neighbor, _ in self.import_graph[node]:
                cycles.extend(find_cycles(neighbor, path.copy(), visited))

            return cycles

        all_cycles = []
        visited: Set[str] = set()

        for node in self.import_graph:
            cycles = find_cycles(node, [], visited)
            all_cycles.extend(cycles)

        return all_cycles

    def get_import_statistics(self) -> Dict[str, Dict]:
        return dict(self.module_stats)

    def visualize_dependency_graph(self, output_file: str = "dependency_graph.png") -> None:
        G = nx.DiGraph()
        for module, imports in self.import_graph.items():
            for imported_module, import_type in imports:
                G.add_edge(module, imported_module, type=import_type)

        pos = nx.spring_layout(G)
        plt.figure(figsize=(20, 20))
        nx.draw(
            G,
            pos,
            with_labels=True,
            node_size=1000,
            node_color="lightblue",
            font_size=8,
            font_weight="bold",
            arrows=True,
        )

        edge_colors = {"stdlib": "green", "third-party": "red", "local": "blue"}
        for u, v, d in G.edges(data=True):
            nx.draw_networkx_edges(
                G, pos, edgelist=[(u, v)], edge_color=edge_colors[d["type"]], arrows=True
            )

        plt.title("Project Dependency Graph")
        plt.axis("off")
        plt.tight_layout()
        plt.savefig(output_file, format="png", dpi=300)
        plt.close()

    def suggest_optimizations(self) -> List[str]:
        suggestions = []

        heavy_importers = {
            module: stats["imports"]
            for module, stats in self.module_stats.items()
            if stats["imports"] > 10
        }

        if heavy_importers:
            suggestions.append("Modules with many imports (consider refactoring):")
            for module, count in sorted(heavy_importers.items(), key=lambda x: x[1], reverse=True):
                suggestions.append(f"  - {module}: {count} imports")

        common_imports = {
            module: stats["imported_by"]
            for module, stats in self.module_stats.items()
            if stats["imported_by"] > 5
        }

        if common_imports:
            suggestions.append("\nFrequently imported modules (consider lazy loading):")
            for module, count in sorted(common_imports.items(), key=lambda x: x[1], reverse=True):
                suggestions.append(f"  - {module}: imported by {count} modules")

        third_party_imports = {
            module: stats.get("third-party_imports", 0)
            for module, stats in self.module_stats.items()
            if stats.get("third-party_imports", 0) > 3
        }

        if third_party_imports:
            suggestions.append("\nConsider centralizing these frequently used third-party imports:")
            for module, count in sorted(
                third_party_imports.items(), key=lambda x: x[1], reverse=True
            )[:5]:
                suggestions.append(f"  - {module}: {count} third-party imports")

        local_importers = {
            module: stats.get("local_imports", 0)
            for module, stats in self.module_stats.items()
            if stats.get("local_imports", 0) > 5
        }

        if local_importers:
            suggestions.append("\nConsider using __all__ to limit exported names in these modules:")
            for module, count in sorted(local_importers.items(), key=lambda x: x[1], reverse=True)[
                :5
            ]:
                suggestions.append(f"  - {module}: {count} local imports")

        return suggestions

    def analyze_import_load_times(self) -> None:
        for module in self.import_graph.keys():
            start_time = time.time()
            try:
                importlib.import_module(module)
                load_time = time.time() - start_time
                self.module_stats[module]["import_time"] = load_time
            except ImportError:
                print(f"Could not import {module} for load time analysis")

    def get_top_import_times(self, top_n: int = 10) -> List[Tuple[str, float]]:
        return sorted(
            [(module, stats["import_time"]) for module, stats in self.module_stats.items()],
            key=lambda x: x[1],
            reverse=True,
        )[:top_n]


def main():
    parser = argparse.ArgumentParser(description="Analyze Python project imports and dependencies.")
    parser.add_argument("project_root", help="Root directory of the Python project to analyze")
    parser.add_argument(
        "--visualize", action="store_true", help="Generate a dependency graph visualization"
    )
    parser.add_argument("--load-times", action="store_true", help="Analyze import load times")
    args = parser.parse_args()

    analyzer = ImportAnalyzer(args.project_root)
    analyzer.analyze_project()

    print("Import Statistics:")
    for module, stats in analyzer.get_import_statistics().items():
        print(f"{module}:")
        print(f"  Imports: {stats['imports']}")
        print(f"  Imported by: {stats['imported_by']}")
        print(f"  Stdlib imports: {stats.get('stdlib_imports', 0)}")
        print(f"  Third-party imports: {stats.get('third-party_imports', 0)}")
        print(f"  Local imports: {stats.get('local_imports', 0)}")

    print("\nOptimization Suggestions:")
    for suggestion in analyzer.suggest_optimizations():
        print(suggestion)

    if args.visualize:
        analyzer.visualize_dependency_graph()
        print("\nDependency graph saved as 'dependency_graph.png'")

    if args.load_times:
        analyzer.analyze_import_load_times()
        print("\nTop 10 modules by import time:")
        for module, load_time in analyzer.get_top_import_times():
            print(f"  {module}: {load_time:.4f} seconds")


if __name__ == "__main__":
    main()
