import importlib
import time
from typing import List, Tuple


def analyze_import_load_times(import_graph, top_n: int = 10) -> List[Tuple[str, float]]:
    load_times = []
    for module in import_graph.keys():
        start_time = time.time()
        try:
            importlib.import_module(module)
            load_time = time.time() - start_time
            load_times.append((module, load_time))
        except ImportError:
            print(f"Could not import {module} for load time analysis")

    return sorted(load_times, key=lambda x: x[1], reverse=True)[:top_n]
