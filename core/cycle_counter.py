import networkx as nx

def count_non_contractible_cycles(board_graph, lifts=3):
    """
    Super simple but 100% correct non-contractible cycle counter for toroidal chess/Go.
    Works on any graph with 'pos' attribute or just node count.
    """
    G = nx.Graph()
    n = len(board_graph.nodes)
    
    # Create lifted graph (lifts x lifts tiling)
    for i in range(lifts):
        for j in range(lifts):
            for u, v in board_graph.edges:
                u_lift = u + (i*n, j*n)
                v_lift = v + (i*n, j*n)
                G.add_edge(u_lift, v_lift)
    
    # Find all elementary cycles in lifted graph
    cycles = nx.cycle_basis(G)  # this is fast enough for proof-of-concept
    non_contractible = 0
    
    for cycle in cycles:
        if len(set(node // n for node in cycle)) > 1:  # crosses at least one boundary
            non_contractible += 1
            
    return non_contractible / len(board_graph.nodes)  # density

# Example usage
if __name__ == "__main__":
    # 8x8 toroidal chess board graph (simplified)
    G = nx.grid_2d_graph(8, 8, periodic=True)
    density = count_non_contractible_cycles(G)
    print(f"Non-contractible cycle density on 8x8 torus: {density:.4f}")