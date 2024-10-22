from typing import Dict, List


def suggest_optimizations(module_stats: Dict[str, Dict]) -> List[str]:
    suggestions = []

    heavy_importers = {
        module: stats["imports"]
        for module, stats in module_stats.items()
        if stats["imports"] > 10
    }

    if heavy_importers:
        suggestions.append("Modules with many imports (consider refactoring):")
        for module, count in sorted(heavy_importers.items(), key=lambda x: x[1], reverse=True):
            suggestions.append(f"  - {module}: {count} imports")

    common_imports = {
        module: stats["imported_by"]
        for module, stats in module_stats.items()
        if stats["imported_by"] > 5
    }

    if common_imports:
        suggestions.append("\nFrequently imported modules (consider lazy loading):")
        for module, count in sorted(common_imports.items(), key=lambda x: x[1], reverse=True):
            suggestions.append(f"  - {module}: imported by {count} modules")

    third_party_imports = {
        module: stats["third-party_imports"]
        for module, stats in module_stats.items()
        if stats.get("third-party_imports", 0) > 3
    }

    if third_party_imports:
        suggestions.append("\nConsider centralizing these frequently used third-party imports:")
        for module, count in sorted(third_party_imports.items(), key=lambda x: x[1], reverse=True)[:5]:
            suggestions.append(f"  - {module}: {count} third-party imports")

    local_importers = {
        module: stats.get("local_imports", 0)
        for module, stats in module_stats.items()
        if stats.get("local_imports", 0) > 5
    }

    if local_importers:
        suggestions.append("\nConsider using __all__ to limit exported names in these modules:")
        for module, count in sorted(local_importers.items(), key=lambda x: x[1], reverse=True)[:5]:
            suggestions.append(f"  - {module}: {count} local imports")

    return suggestions
