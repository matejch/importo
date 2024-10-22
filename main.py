import argparse
import os

from import_analyzer import ImportAnalyzer
from visualizer import visualize_dependency_graph


def setup_pre_commit_hook():
    hook_path = os.path.join(".git", "hooks", "pre-commit")
    hook_content = """#!/bin/sh
python lint_and_format.py
"""
    with open(hook_path, "w") as f:
        f.write(hook_content)
    os.chmod(hook_path, 0o755)
    print("Pre-commit hook set up successfully.")


def main():
    parser = argparse.ArgumentParser(description="Analyze Python project imports and dependencies.")
    parser.add_argument("project_root", help="Root directory of the Python project to analyze")
    parser.add_argument(
        "--visualize", action="store_true", help="Generate a dependency graph visualization"
    )
    parser.add_argument("--load-times", action="store_true", help="Analyze import load times")
    parser.add_argument("--setup-hook", action="store_true", help="Set up pre-commit hook")
    args = parser.parse_args()

    if args.setup_hook:
        setup_pre_commit_hook()
        return

    analyzer = ImportAnalyzer(args.project_root)
    analyzer.analyze_project()
    
    if args.load_times:
        analyzer.analyze_import_load_times()
    
    print("Import Statistics:")
    for module, stats in analyzer.get_import_statistics().items():
        print(f"{module}:")
        print(f"  Imports: {stats['imports']}")
        print(f"  Imported by: {stats['imported_by']}")
        print(f"  Stdlib imports: {stats.get('stdlib_imports', 0)}")
        print(f"  Third-party imports: {stats.get('third-party_imports', 0)}")
        print(f"  Local imports: {stats.get('local_imports', 0)}")
        if args.load_times:
            print(f"  Import time: {stats['import_time']:.4f} seconds")
    
    print("\nOptimization Suggestions:")
    for suggestion in analyzer.suggest_optimizations():
        print(suggestion)
    
    if args.visualize:
        visualize_dependency_graph(analyzer.import_graph, analyzer.module_stats)
        print("\nDependency graph saved as 'dependency_graph.png'")
    
    if args.load_times:
        print("\nTop 10 modules by import time:")
        for module, load_time in analyzer.get_top_import_times():
            print(f"  {module}: {load_time:.4f} seconds")


if __name__ == "__main__":
    main()
