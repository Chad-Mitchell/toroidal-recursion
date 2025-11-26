import numpy as np
import networkx as nx

def cycleforge_v11_1(steps=80, seeds=25, r_fuse=0.22, branch_p=0.45, dim=3, diffusion_std=0.07):
    G = nx.Graph()
    pos = {}
    terminals = []
    node_id = 0

    # Initialize seeds
    for _ in range(seeds):
        pos[node_id] = np.random.uniform(0, 1, dim)
        terminals.append(node_id)
        G.add_node(node_id)
        node_id += 1

    betti1_history = []
    cum_fusions = 0
    cum_new_tips = 0

    for step in range(steps):
        new_nodes = []
        new_pos = []

        # 1. Branch / Extend
        current_terminals = terminals.copy()
        terminals = []
        for t in current_terminals:
            # Always extend
            new_p = (pos[t] + np.random.normal(0, diffusion_std, dim)) % 1.0
            pos[node_id] = new_p
            new_pos.append(new_p)
            G.add_edge(t, node_id)
            new_nodes.append(node_id)
            node_id += 1

            # Optional bifurcation
            if np.random.rand() < branch_p:
                new_p = (pos[t] + np.random.normal(0, diffusion_std, dim)) % 1.0
                pos[node_id] = new_p
                new_pos.append(new_p)
                G.add_edge(t, node_id)
                new_nodes.append(node_id)
                node_id += 1

        cum_new_tips += len(new_nodes)

        if len(new_nodes) < 2:
            terminals.extend(new_nodes)
            v = G.number_of_nodes()
            e = G.number_of_edges()
            c = nx.number_connected_components(G)
            betti1_history.append(max(0, e - v + c))
            continue

        new_pos = np.array(new_pos)
        # Toroidal dist matrix
        diffs = np.abs(new_pos[:, None, :] - new_pos[None, :, :])
        diffs = np.minimum(diffs, 1 - diffs)
        dists = np.linalg.norm(diffs, axis=-1)
        np.fill_diagonal(dists, np.inf)

        fused_indices = set()
        this_fusions = 0
        triangle_added = False

        # Simplified Nest: Scan for any triple in close pairs
        for i in range(len(new_nodes)):
            if triangle_added: break
            close = np.where(dists[i] < r_fuse)[0]
            if len(close) >= 2:
                for j in close:
                    if j > i:
                        for k in close:
                            if k > j and dists[j, k] < r_fuse:
                                triangle_nodes = [new_nodes[i], new_nodes[j], new_nodes[k]]
                                triangle_added = True
                                fused_indices.update([i, j, k])
                                this_fusions += 3  # Triangle counts as 3 fusions
                                break
                        if triangle_added: break

        # Greedy pairwise: Global sort by dist
        candidates = np.argwhere(dists < r_fuse)
        candidates = candidates[candidates[:, 0] < candidates[:, 1]]
        if len(candidates) > 0:
            pair_dists = dists[candidates[:, 0], candidates[:, 1]]
            order = np.argsort(pair_dists)
            for idx in order:
                i, j = candidates[idx]
                if i in fused_indices or j in fused_indices: continue
                G.add_edge(new_nodes[i], new_nodes[j])
                fused_indices.update([i, j])
                this_fusions += 1

        # Add triangle
        if triangle_added:
            a, b, c = triangle_nodes
            G.add_edges_from([(a, b), (a, c), (b, c)])

        cum_fusions += this_fusions

        # Survivors
        terminals = [new_nodes[i] for i in range(len(new_nodes)) if i not in fused_indices]

        # Betti-1
        v = G.number_of_nodes()
        e = G.number_of_edges()
        c = nx.number_connected_components(G)
        betti1_history.append(max(0, e - v + c))

    # Final metrics
    final_h1 = betti1_history[-1] if betti1_history else 0
    rho = cum_fusions / max(1, cum_new_tips) if cum_new_tips > 0 else 0
    leak = rho / max(1, final_h1)

    # ΔG: log2 ratios every 8 steps
    accum = np.maximum.accumulate(np.array(betti1_history) + 1)
    if len(accum) >= 8:
        windows = np.diff(np.log2(accum[::8]))
        delta_g = np.mean(windows)
    else:
        delta_g = 0

    # R: 25% random edge removal
    G_noisy = G.copy()
    edges = list(G_noisy.edges())
    np.random.shuffle(edges)
    num_remove = int(0.25 * len(edges))
    for ee in edges[:num_remove]:
        G_noisy.remove_edge(*ee)
    v_n = G_noisy.number_of_nodes()
    e_n = G_noisy.number_of_edges()
    c_n = nx.number_connected_components(G_noisy)
    h1_n = max(0, e_n - v_n + c_n)
    robustness = h1_n / max(1, final_h1)

    return {
        'delta_g': delta_g, 'robustness': robustness, 'rho': rho, 'leak': leak,
        'final_h1': final_h1
    }

# Verification: 50 seeds
np.random.seed(314159265)
num_runs = 50
dgs, rs, rhos, leaks = [], [], [], []

for run in range(num_runs):
    np.random.seed(314159265 + run)
    metrics = cycleforge_v11_1(steps=80, r_fuse=0.22)
    dgs.append(metrics['delta_g'])
    rs.append(metrics['robustness'])
    rhos.append(metrics['rho'])
    leaks.append(metrics['leak'])

# Stats
print("50 independent runs completed")
print(f"ΔG      = {np.mean(dgs):.3f} ± {np.std(dgs):.3f}      (threshold >1.3  → {'PASS' if np.mean(dgs) > 1.3 else 'FAIL'})")
print(f"R       = {np.mean(rs):.3f} ± {np.std(rs):.3f}      (threshold >0.6  → {'PASS' if np.mean(rs) > 0.6 else 'FAIL'})")
print(f"ρ       = {np.mean(rhos):.3f} ± {np.std(rhos):.3f}      (target ~0.42    → {'PASS' if 0.38 < np.mean(rhos) < 0.46 else 'FAIL'})")
print(f"leak    = {np.mean(leaks):.3f} ± {np.std(leaks):.3f}      (threshold <0.05 → {'PASS' if np.mean(leaks) < 0.05 else 'FAIL'})")
passes = sum(1 for i in range(num_runs) if dgs[i] > 1.3 and rs[i] > 0.6 and 0.38 < rhos[i] < 0.46 and leaks[i] < 0.05)
print(f"{100 * passes / num_runs:.1f} % of runs passed all antifragility thresholds")
