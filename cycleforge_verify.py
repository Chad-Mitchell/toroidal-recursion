import numpy as np
import networkx as nx

def toroidal_dist(a, b, L=1.0):
    d = np.abs(a - b)
    d = np.minimum(d, L - d)
    return np.linalg.norm(d)

def cycleforge(steps=80, seeds=25, r_fuse=0.135, branch_p=0.45, dim=3):
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

    for step in range(steps):
        new_nodes = []
        new_pos = []

        # 1. Branch / Extend
        current_terminals = terminals.copy()
        terminals = []
        for t in current_terminals:
            # Always extend
            new_p = (pos[t] + np.random.normal(0, 0.09, dim)) % 1.0
            pos[node_id] = new_p
            new_pos.append(new_p)
            G.add_edge(t, node_id)
            new_nodes.append(node_id)
            node_id += 1

            # Optional bifurcation
            if np.random.rand() < branch_p:
                new_p = (pos[t] + np.random.normal(0, 0.09, dim)) % 1.0
                pos[node_id] = new_p
                new_pos.append(new_p)
                G.add_edge(t, node_id)
                new_nodes.append(node_id)
                node_id += 1

        if len(new_nodes) < 2:
            terminals.extend(new_nodes)
            v = G.number_of_nodes()
            e = G.number_of_edges()
            c = nx.number_connected_components(G)
            betti1_history.append(max(0, e - v + c))
            continue

        new_pos = np.array(new_pos)
        dists = np.linalg.norm(
            np.minimum(np.abs(new_pos[:, None, :] - new_pos[None, :, :]),
                       1 - np.abs(new_pos[:, None, :] - new_pos[None, :, :])), axis=-1)
        np.fill_diagonal(dists, np.inf)

        fused_indices = set()
        triangle_added = False
        triangle_nodes = None

        # Nest: first mutual triple → explicit triangle
        for i in range(len(new_nodes)):
            close = np.where(dists[i] < r_fuse)[0]
            if len(close) >= 2:
                for j in close:
                    if j <= i: continue
                    close2 = np.where(dists[j] < r_fuse)[0]
                    common = np.intersect1d(close, close2)
                    if len(common) >= 2:
                        k_idx = 0
                        while k_idx < len(common) and (common[k_idx] == i or common[k_idx] == j):
                            k_idx += 1
                        if k_idx < len(common):
                            k = common[k_idx]
                            if dists[i,k] < r_fuse and dists[j,k] < r_fuse:
                                triangle_nodes = [new_nodes[i], new_nodes[j], new_nodes[k]]
                                triangle_added = True
                                fused_indices.update([i, j, k])
                                break
                    if triangle_added: break
                if triangle_added: break

        # Greedy pairwise fusion
        candidates = np.argwhere(dists < r_fuse)
        candidates = candidates[candidates[:,0] < candidates[:,1]]
        distances = dists[candidates[:,0], candidates[:,1]]
        order = np.argsort(distances)
        for idx in order:
            i, j = candidates[idx]
            if i in fused_indices or j in fused_indices: continue
            G.add_edge(new_nodes[i], new_nodes[j])
            fused_indices.update([i, j])

        # Explicit triangle
        if triangle_added:
            a, b, c = triangle_nodes
            G.add_edges_from([(a,b), (a,c), (b,c)])

        # Survivors become new terminals
        terminals = [n for i, n in enumerate(new_nodes) if i not in fused_indices]

        # Betti-1 proxy
        v = G.number_of_nodes()
        e = G.number_of_edges()
        c = nx.number_connected_components(G)
        betti1_history.append(max(0, e - v + c))

    return {
        'G': G, 'pos': pos, 'betti1': np.array(betti1_history),
        'final_betti1': betti1_history[-1] if betti1_history else 0
    }

# Verification run: 50 seeds
np.random.seed(314159265)
num_seeds_total = 50
dgs = []
rs = []
rhos = []
leaks = []
seeds = 25  # Hardcoded default

for run in range(num_seeds_total):
    np.random.seed(314159265 + run)  # Independent offsets
    result = cycleforge(steps=80, r_fuse=0.135)
    betti1 = result['betti1']
    
    # ΔG
    accum = np.maximum.accumulate(betti1 + 1)
    if len(accum) >= 8:
        windows = np.diff(np.log2(accum[::8]))
        dg = np.mean(windows)
    else:
        dg = 0
    dgs.append(dg)
    
    # R
    G_noisy = result['G'].copy()
    edges = list(G_noisy.edges())
    np.random.shuffle(edges)
    num_remove = int(0.25 * len(edges))
    for ee in edges[:num_remove]:
        if G_noisy.has_edge(*ee):
            G_noisy.remove_edge(*ee)
    v_n, e_n, c_n = G_noisy.number_of_nodes(), G_noisy.number_of_edges(), nx.number_connected_components(G_noisy)
    h1_n = max(0, e_n - v_n + c_n)
    h1_orig = result['final_betti1']
    r = h1_n / max(1, h1_orig)
    rs.append(r)
    
    # ρ approx (extra edges beyond tree / nodes)
    total_nodes = result['G'].number_of_nodes()
    tree_edges = total_nodes - seeds  # Min spanning tree
    extra_edges = max(0, result['G'].number_of_edges() - tree_edges)
    rho = extra_edges / total_nodes
    rhos.append(rho)
    
    # Leak
    leak = rho / max(1, h1_orig)
    leaks.append(leak)

# Stats
mean_dg = np.mean(dgs)
std_dg = np.std(dgs)
mean_r = np.mean(rs)
std_r = np.std(rs)
mean_rho = np.mean(rhos)
std_rho = np.std(rhos)
mean_leak = np.mean(leaks)
std_leak = np.std(leaks)

# Per-run passes
passes = sum(1 for i in range(num_seeds_total) if dgs[i] > 1.3 and rs[i] > 0.6 and 0.38 < rhos[i] < 0.46 and leaks[i] < 0.05)
pass_rate = 100 * (passes / num_seeds_total)

print(f"50 independent runs completed")
print(f"ΔG      = {mean_dg:.3f} ± {std_dg:.3f}      (threshold >1.3  → {'PASS' if mean_dg > 1.3 else 'FAIL'})")
print(f"R       = {mean_r:.3f} ± {std_r:.3f}      (threshold >0.6  → {'PASS' if mean_r > 0.6 else 'FAIL'})")
print(f"ρ       = {mean_rho:.3f} ± {std_rho:.3f}      (target ~0.42    → {'PASS' if 0.38 < mean_rho < 0.46 else 'FAIL'})")
print(f"leak    = {mean_leak:.3f} ± {std_leak:.3f}      (threshold <0.05 → {'PASS' if mean_leak < 0.05 else 'FAIL'})")
print(f"{pass_rate:.1f} % of runs passed all antifragility thresholds")
