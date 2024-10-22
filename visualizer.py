from typing import Dict, Set, Tuple

import matplotlib.cm as cm
import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.colors import LinearSegmentedColormap


def visualize_dependency_graph(
    import_graph: Dict[str, Set[Tuple[str, str]]],
    module_stats: Dict[str, Dict],
    output_file: str = "dependency_graph.png",
) -> None:
    G = nx.DiGraph()
    for module, imports in import_graph.items():
        G.add_node(module, import_time=module_stats[module]["import_time"])
        for imported_module, import_type in imports:
            G.add_edge(module, imported_module, type=import_type)

    fig, ax = plt.subplots(figsize=(20, 20))
    pos = nx.spring_layout(G)

    # Draw nodes with color based on import time
    node_colors = [G.nodes[node]["import_time"] for node in G.nodes()]
    cmap = plt.get_cmap("YlOrRd")
    nx.draw_networkx_nodes(G, pos, node_size=1000, node_color=node_colors, cmap=cmap, ax=ax)

    # Draw labels
    nx.draw_networkx_labels(G, pos, font_size=8, font_weight="bold", ax=ax)

    # Draw edges
    edge_colors = {"stdlib": "green", "third-party": "red", "local": "blue"}
    for u, v, d in G.edges(data=True):
        nx.draw_networkx_edges(
            G, pos, edgelist=[(u, v)], edge_color=edge_colors[d["type"]], arrows=True, ax=ax
        )

    ax.set_title("Project Dependency Graph (Node color indicates import time)")
    ax.axis("off")

    # Add colorbar
    sm = plt.cm.ScalarMappable(
        cmap=cmap, norm=plt.Normalize(vmin=min(node_colors), vmax=max(node_colors))
    )
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax)
    cbar.set_label("Import time (seconds)", rotation=270, labelpad=15)

    plt.tight_layout()
    plt.savefig(output_file, format="png", dpi=300)
    plt.close(fig)
