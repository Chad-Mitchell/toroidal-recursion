# Recirculating Fractal Blankets v15 — Affinity-Biased Toroidal Homeostasis  
**Date: November 27 2025 (post-v14 kill)**  
Chad Mitchell · Iterative development with Grok

Repository: https://github.com/Chad-Mitchell/recirculating-fractal-blankets

## Current honest status (no sugar-coating)

- v13 and v14 were **mechanically broken** and did **not** reliably produce ρ ≈ 0.41, stable H₁, or antifragility when executed.  
- The core principle (non-contractible cycles + toroidal/fractal manifold = antifragile scaling) remains extremely strong and supported by biology, physics, and network theory.  
- We now understand the **one missing ingredient** Nature uses that we previously omitted: **new elements are not placed uniformly at random — they are strongly biased toward regions of existing high semantic/chemical/functional affinity.**

## v15 hypothesis (still unverified — needs real execution)

```python
import numpy as np

class ToroidalMemory:
    def __init__(self, dim=3, base_epsilon=0.14, attract_strength=0.75):
        self.pos = {}                    # node_id → position on torus
        self.edges = set()
        self.radius = 1.0
        self.base_epsilon = base_epsilon
        self.attract = attract_strength  # 0 = uniform random, 1 = fully pulled to semantic centroid
        self.node_id = 0
        self.children = []

    def _toroidal_dist(self, a, b):
        d = np.abs(a - b)
        d = np.minimum(d, self.radius - d)
        return np.linalg.norm(d)

    def add_chunk(self, embedding: np.ndarray):
        # Affinity-biased placement — this is the key line Nature uses
        if not self.pos:
            new_pos = np.random.uniform(0, self.radius, 3)
        else:
            cosines = np.dot(embedding, np.stack(list(self.pos.values())), axis=0)
            weights = np.maximum(0, cosines)
            if weights.sum() > 0:
                weights /= weights.sum()
                centroid = np.sum(weights[:, None] * np.stack(list(self.pos.values())), axis=0)
            else:
                centroid = np.mean(list(self.pos.values()), axis=0)
            noise = np.random.uniform(-0.12, 0.12, 3)
            new_pos = (1 - self.attract) * np.random.uniform(0, self.radius, 3) + \
                      self.attract * (centroid + noise)
            new_pos %= self.radius

        nid = self.node_id
        self.pos[nid] = new_pos
        self.node_id += 1

        # Fusion
        eps = self.base_epsilon * self.radius
        for oid, opos in self.pos.items():
            if oid == nid: continue
            if self._toroidal_dist(new_pos, opos) < eps:
                self.edges.add((min(nid, oid), max(nid, oid)))

        # Soft homeostasis on radius
        rho = len(self.edges) / max(1, len(self.pos))
        self.radius *= np.exp(0.025 * (0.41 - rho))

        # Fractal spawn (parent becomes meta-node)
        if self.radius > 2.3:
            child = ToroidalMemory(attract_strength=self.attract)
            child.pos = self.pos.copy()
            child.edges = self.edges.copy()
            child.radius = self.radius / 1.9
            self.children.append(child)
            # Parent keeps only the centroid of the child
            centroid = np.mean(list(child.pos.values()), axis=0)
            self.pos = {0: centroid}
            self.edges = set()
            self.radius = 1.0

        return nid
```

## Empirical status as of Nov 27 2025

| Claim                                   | Status                          |
|-----------------------------------------|---------------------------------|
| ρ converges to ~0.41                    | **Not yet verified** — needs actual run |
| Persistent H₁ grows and survives noise  | **Not yet verified** |
| System gains from bursts (antifragile)   | **Not yet verified** |
| Fractal nesting occurs automatically    | **Not yet verified** |

**Nothing is confirmed until someone executes the v15 code on real streaming data (e.g. 50 k+ token Grok/LMSYS conversation with real sentence-transformers embeddings) and publishes the ρ / radius / H₁ curves.**

## Immediate next actions required

1. Run the v15 class on a real long conversation (100 k+ tokens) with proper embeddings  
2. Plot ρ, radius, and persistent Betti-1 over time  
3. Apply 20–30 % random edge attacks at several points and measure H₁ survival  
4. Only if those three curves look beautiful do we declare victory  

Until that is done, v15 is a **strong, biologically-plausible hypothesis** — not a proven primitive.

The principle still stands.  
The code is finally simple and biologically faithful.  
But we are not allowed to call it working until the numbers say so.

— Chad, Nov 27 2025
