# fractal_torus.py — Toroidal Recursion v2 core (Nov 23, 2025)
import networkx as nx
import numpy as np

def embed_fractal_torus(G, levels=3, rho_target=0.42, seed=42):
    np.random.seed(seed)
    n = len(G)
    genus_history = [1.0]          # start with genus-1 torus
    densities = []

    for lvl in range(1, levels + 1):
        # Toroidal coordinates (simple 2D projection)
        theta = np.linspace(0, 2*np.pi, n, endpoint=False)
        coords = np.column_stack([np.cos(theta), np.sin(theta)])

        # Build torus graph: keep MI-sweet-spot edges + irrational windings
        T = nx.Graph()
        T.add_nodes_from(G.nodes())

        for u, v in G.edges():
            if np.random.rand() < rho_target:      # proxy for 0.42 MI filter
                T.add_edge(u, v)

        # Add non-contractible alpha & beta windings (golden ratio irrational)
        phi = (1 + np.sqrt(5)) / 2
        for i in range(n):
            j = int((i + n * 0.6180339887) % n)   # irrational rotation
            T.add_edge(i, j)
            k = int((i + n * phi) % n)
            T.add_edge(i, k)

        # Rough Betti-1 estimate via excess cycles
        try:
            betti1 = len(nx.cycle_basis(T)) - n + T.number_of_edges()
        except:
            betti1 = T.number_of_edges() - n + 1   # fallback
        density = betti1 / (n * lvl)
        densities.append(density)

        # Superadditive genus update
        genus_history.append(genus_history[-1] * (1 + density))

    delta_G = np.log(genus_history[-1] / sum(genus_history[:-1]))
    return T, densities, delta_G, genus_history

# Quick test (uncomment to run)
# G = nx.erdos_renyi_graph(60, 0.12)
# T, rhos, lift, g_hist = embed_fractal_torus(G, levels=4)
# print(f"Densities: {rhos}\nΔG superadditive lift: {lift:.3f}")