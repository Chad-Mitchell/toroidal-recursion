import numpy as np
import networkx as nx
from collections import deque
import warnings
warnings.filterwarnings('ignore')

def grow_recirculating_system(steps=25, n_seeds=20, fuse_radius=0.20, branch_prob=0.45):
    G = nx.Graph()
    pos_dict = {}
    terminals = []
    genus_history = [0]  # Start with 0 (tree-like)
    total_fused = 0
    total_new_terminals = 0

    # Seeds
    for i in range(n_seeds):
        node = i
        G.add_node(node)
        pos_dict[node] = np.random.uniform(0, 1, 3)
        terminals.append(node)

    for step in range(steps):
        new_terminals = []
        this_fusions = 0
        cluster_bonus = 0

        for t in terminals:
            if np.random.rand() < branch_prob:
                a = len(G)
                b = len(G) + 1
                G.add_edges_from([(t, a), (t, b)])
                direction = np.random.normal(0, 0.1, 3)
                pos_dict[a] = (pos_dict[t] + direction) % 1.0
                pos_dict[b] = (pos_dict[t] + direction * 1.1) % 1.0
                new_terminals.extend([a, b])
            else:
                a = len(G)
                G.add_edge(t, a)
                step_vec = np.random.normal(0, 0.08, 3)
                pos_dict[a] = (pos_dict[t] + step_vec) % 1.0
                new_terminals.append(a)

        total_new_terminals += len(new_terminals)

        # Vectorized fusions
        if len(new_terminals) > 1:
            new_pos = np.array([pos_dict[nt] for nt in new_terminals])
            diffs = np.abs(new_pos[:, np.newaxis, :] - new_pos[np.newaxis, :, :])
            diffs = np.minimum(diffs, 1.0 - diffs)
            dist_matrix = np.linalg.norm(diffs, axis=2)

            fused_set = set()
            for idx_u, u in enumerate(new_terminals):
                if u in fused_set: continue
                close_indices = np.where(dist_matrix[idx_u] < fuse_radius)[0]
                for idx_v in close_indices:
                    if idx_v <= idx_u: continue
                    v = new_terminals[idx_v]
                    if v in fused_set: continue
                    G.add_edge(u, v)
                    fused_set.add(u)
                    fused_set.add(v)
                    this_fusions += 1
                    total_fused += 1
                    nearby_count = np.sum(dist_matrix[idx_u] < fuse_radius * 1.5)
                    if nearby_count >= 3:
                        cluster_bonus += 1

        terminals = [t for t in new_terminals if t not in fused_set]

        # b1-based genus
        v = len(G.nodes)
        e = len(G.edges)
        c = nx.number_connected_components(G)
        b1 = e - v + c
        genus = max(1, b1 + this_fusions * 0.5 + cluster_bonus)
        genus_history.append(genus)

    # ΔG over ~5-gen periods
    if len(genus_history) >= 10:
        periods = len(genus_history) // 5
        log_ratios = []
        for p in range(periods):
            start = p * 5
            end = min((p + 1) * 5, len(genus_history))
            g_start = genus_history[start] if start < len(genus_history) else 0
            g_end = np.mean(genus_history[max(0, end - 5):end])
            if g_start > 0:
                log_ratios.append(np.log2(g_end / g_start))
        delta_G = np.mean(log_ratios) if log_ratios else 0
    else:
        delta_G = np.log2(max(1, genus_history[-1]) / max(1, np.mean(genus_history[:5]))) if len(genus_history) > 5 else 0

    # R via b1
    v, e, c = len(G.nodes), len(G.edges), nx.number_connected_components(G)
    cycles = e - v + c
    noisy_G = G.copy()
    edges_list = list(noisy_G.edges())
    np.random.shuffle(edges_list)
    remove_count = int(0.20 * len(edges_list))
    for ee in edges_list[:remove_count]:
        noisy_G.remove_edge(*ee)
    v_n, e_n, c_n = len(noisy_G.nodes), len(noisy_G.edges), nx.number_connected_components(noisy_G)
    surviving_cycles = e_n - v_n + c_n
    R = surviving_cycles / max(1, cycles)

    # ρ
    rho = total_fused / max(1, total_new_terminals * 0.5)

    return {
        'G': G, 'pos': pos_dict, 'genus_history': genus_history,
        'ΔG': delta_G, 'R': R, 'final_genus': genus_history[-1], 'ρ': rho
    }

# Example run (30 seeds; tune seed for repro)
if __name__ == "__main__":
    results = []
    for seed in range(30):
        np.random.seed(seed)
        res = grow_recirculating_system(steps=25, n_seeds=20)
        results.append(res)

    deltaGs = [r['ΔG'] for r in results]
    Rs = [r['R'] for r in results]
    rhos = [r['ρ'] for r in results]
    final_genus = [r['final_genus'] for r in results]

    print(f"ΔG = {np.mean(deltaGs):.3f} ± {np.std(deltaGs):.3f}")
    print(f"R  = {np.mean(Rs):.3f} ± {np.std(Rs):.3f}")
    print(f"ρ  = {np.mean(rhos):.3f} ± {np.std(rhos):.3f}")
    print(f"Final genus = {np.mean(final_genus):.1f}")