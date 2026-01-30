---
sidebar_position: 5
title: "Algorithmic Analysis"
---

# Algorithmic Analysis

This chapter provides a detailed complexity analysis of the core algorithms in the KST Course Engine. We examine the computational cost of constructing knowledge spaces, verifying axioms, enumerating learning paths, and performing graph operations on prerequisite DAGs. All complexities are stated in terms of the fundamental parameters: $n = |Q|$ (number of items), $m = |\mathcal{K}|$ (number of knowledge states), and $e$ (number of edges in the prerequisite DAG).

---

## 5.1 Space Construction Complexity

### 5.1.1 Constructing the Knowledge Space from a Partial Order

Given a partial order $(Q, \preceq)$ on $n$ items, the knowledge space $\mathcal{K}$ consists of all **downsets** (order ideals). The enumeration of downsets proceeds via Algorithm 2.1 (Chapter 2).

**Worst-case analysis.** The number of downsets of a poset can range from $n + 1$ (for a total order) to $2^n$ (for an antichain, where every subset is a downset):

$$
n + 1 \;\leq\; |\mathcal{K}| \;\leq\; 2^n
$$

The bound $2^n$ is tight: when $Q$ has no nontrivial prerequisite relations (the poset is an antichain), every subset of $Q$ is a downset. The width $w$ of the poset (maximum antichain size) gives an intermediate bound via **Dilworth's theorem**:

$$
|\mathcal{K}| \;\leq\; \binom{n}{\lfloor n/2 \rfloor}^{w / n} \cdot 2^n \quad \text{(loosely)}
$$

More precisely, the maximum number of antichains (and hence downsets) of a poset of width $w$ is bounded by the $w$-th **Dedekind number** $D(w)$.

| Width $w$ | $D(w)$ (Dedekind number) | Approximate value |
|-----------|--------------------------|-------------------|
| 1 | 3 | 3 |
| 2 | 6 | 6 |
| 3 | 20 | 20 |
| 4 | 168 | 168 |
| 5 | 7581 | $7.6 \times 10^3$ |
| 6 | 7828354 | $7.8 \times 10^6$ |
| 7 | 2414682040998 | $2.4 \times 10^{12}$ |
| 8 | 56130437228687557907788 | $5.6 \times 10^{22}$ |

**Per-state cost.** Each downset is stored as a `frozenset` of size up to $n$, and membership checks during BFS/DFS enumeration cost $O(n)$ per candidate item. Total construction time:

$$
T_{\text{construct}} = O(m \cdot n^2) \quad \text{where } m = |\mathcal{K}|
$$

### 5.1.2 Construction via Closure Operator

An alternative approach uses the **closure operator** $\varphi: 2^Q \to 2^Q$ defined by:

$$
\varphi(S) = \bigcap \{ K \in \mathcal{K} : S \subseteq K \}
$$

Given a surmise relation, $\varphi(S) = {\downarrow}S = \bigcup_{q \in S} {\downarrow}q$. Starting from $\emptyset$ and systematically applying $\varphi$ to $S \cup \{q\}$ for each $q \notin S$, one generates all states. The **NextClosure** algorithm (Ganter, 1984) enumerates closed sets in lexicographic order with **amortized** $O(n)$ time per closed set:

$$
T_{\text{NextClosure}} = O(m \cdot n) \quad \text{(amortized)}
$$

This is optimal in the sense that any algorithm must at least enumerate all $m$ states and represent each as a subset of $Q$.

---

## 5.2 Axiom Verification

### 5.2.1 Checking Union Closure

Given a family $\mathcal{K}$ of subsets of $Q$ (represented as a set of frozensets), we verify axiom (S3): for all $K_1, K_2 \in \mathcal{K}$, $K_1 \cup K_2 \in \mathcal{K}$.

**Naive algorithm:** Enumerate all pairs $(K_1, K_2)$ and check membership of $K_1 \cup K_2$:

$$
T_{\text{union-check}} = O\!\left(\binom{m}{2} \cdot n\right) = O(m^2 \cdot n)
$$

The factor of $n$ comes from computing the union and performing a hash-set lookup (the union of two sets of size up to $n$ takes $O(n)$; lookup in a hash set of frozensets costs $O(n)$ for hashing).

**Optimized algorithm:** For each pair, compute the union incrementally. Using a hash set for $\mathcal{K}$:

| Operation | Cost |
|-----------|------|
| Store $\mathcal{K}$ in hash set | $O(m \cdot n)$ |
| Enumerate pairs | $O(m^2)$ |
| Compute union per pair | $O(n)$ |
| Lookup per pair | $O(n)$ expected |
| **Total** | $O(m^2 \cdot n)$ |

### 5.2.2 Checking Accessibility (Learning Space Axiom)

For each nonempty $K \in \mathcal{K}$, verify that there exists $q \in K$ with $K \setminus \{q\} \in \mathcal{K}$:

$$
T_{\text{accessibility}} = O(m \cdot n \cdot n) = O(m \cdot n^2)
$$

For each of $m$ states, we try removing each of up to $n$ items and checking membership ($O(n)$ per lookup).

**Using a hash set** for $\mathcal{K}$, each lookup is $O(n)$ expected, so:

$$
T_{\text{accessibility}} = O(m \cdot n^2)
$$

### 5.2.3 Summary of Axiom Checks

| Axiom | Description | Time Complexity | Space |
|-------|-------------|-----------------|-------|
| (S1) | $\emptyset \in \mathcal{K}$ | $O(1)$ | $O(1)$ |
| (S2) | $Q \in \mathcal{K}$ | $O(n)$ | $O(1)$ |
| (S3) | Union closure | $O(m^2 \cdot n)$ | $O(m \cdot n)$ |
| (L) | Accessibility | $O(m \cdot n^2)$ | $O(m \cdot n)$ |
| All (Knowledge Space) | (S1) + (S2) + (S3) | $O(m^2 \cdot n)$ | $O(m \cdot n)$ |
| All (Learning Space) | (S1) + (S2) + (S3) + (L) | $O(m^2 \cdot n)$ | $O(m \cdot n)$ |

---

## 5.3 Learning Path Enumeration

A **learning path** is a maximal chain $\emptyset = K_0 \subsetneq K_1 \subsetneq \cdots \subsetneq K_n = Q$ in $\mathcal{L}$. Enumerating all learning paths is equivalent to counting all maximal chains in the lattice $(\mathcal{L}, \subseteq)$.

### 5.3.1 Backtracking Algorithm

```
function ENUMERATE_PATHS(K_current, path, all_paths, L):
    if K_current = Q:
        all_paths.append(path)
        return

    for q in K_current^O:              # Outer fringe
        K_next ← K_current ∪ {q}
        ENUMERATE_PATHS(K_next, path + [q], all_paths, L)
```

**Complexity.** Let $p$ denote the total number of learning paths. At each step, the branching factor is $|K^O|$ (outer fringe size). The depth of the recursion tree is $n$. Therefore:

$$
T_{\text{paths}} = O(p \cdot n)
$$

since each complete path has length $n$ and we perform $O(1)$ work per step (assuming precomputed fringes).

**Worst case.** When $\mathcal{L} = 2^Q$ (the antichain poset), every permutation of $Q$ is a learning path, giving $p = n!$. Thus:

$$
T_{\text{paths}}^{\text{worst}} = O(n! \cdot n) = O((n+1)!)
$$

### 5.3.2 Counting Without Enumeration

The number of learning paths can be computed without explicit enumeration via a **dynamic programming** approach on the lattice. Define $f(K)$ as the number of learning paths from $K$ to $Q$:

$$
f(K) = \begin{cases} 1 & \text{if } K = Q \\ \displaystyle\sum_{q \in K^O} f(K \cup \{q\}) & \text{otherwise} \end{cases}
$$

The answer is $f(\emptyset)$. This requires computing $f(K)$ for all $K \in \mathcal{L}$, in reverse topological order:

$$
T_{\text{count}} = O(m \cdot n), \qquad S_{\text{count}} = O(m)
$$

---

## 5.4 DAG Operations with NetworkX

The prerequisite structure is stored as a **directed acyclic graph** (DAG) using the NetworkX library. The following table summarizes key operations:

### 5.4.1 Core DAG Operations

| Operation | NetworkX Function | Time Complexity | Description |
|-----------|-------------------|-----------------|-------------|
| Build DAG | `nx.DiGraph()` + `add_edges_from` | $O(n + e)$ | Construct from item set and edges |
| Topological sort | `nx.topological_sort(G)` | $O(n + e)$ | Linear ordering respecting $\preceq$ |
| Transitive closure | `nx.transitive_closure(G)` | $O(n \cdot (n + e))$ | Compute all reachable pairs |
| Transitive reduction | `nx.transitive_reduction(G)` | $O(n \cdot (n + e))$ | Minimal edge set (Hasse diagram) |
| Ancestors of node $q$ | `nx.ancestors(G, q)` | $O(n + e)$ | Compute ${\downarrow}q \setminus \{q\}$ |
| Descendants of node $q$ | `nx.descendants(G, q)` | $O(n + e)$ | Compute ${\uparrow}q \setminus \{q\}$ |
| All downsets | Custom BFS (Algo 2.1) | $O(m \cdot n^2)$ | Enumerate knowledge states |
| Is DAG? | `nx.is_directed_acyclic_graph(G)` | $O(n + e)$ | Verify acyclicity |
| Longest path | `nx.dag_longest_path(G)` | $O(n + e)$ | Critical path length |
| Connected components | `nx.weakly_connected_components(G)` | $O(n + e)$ | Independent sub-domains |

### 5.4.2 Batch Operations

| Operation | Time Complexity | Space Complexity |
|-----------|-----------------|------------------|
| Build all downsets from DAG | $O(m \cdot n^2)$ | $O(m \cdot n)$ |
| Compute all inner fringes | $O(m \cdot n^2)$ | $O(m \cdot n)$ |
| Compute all outer fringes | $O(m \cdot n^2)$ | $O(m \cdot n)$ |
| Build state transition graph | $O(m \cdot n)$ | $O(m \cdot n)$ |
| Verify knowledge space axioms | $O(m^2 \cdot n)$ | $O(m \cdot n)$ |
| Verify learning space axioms | $O(m^2 \cdot n)$ | $O(m \cdot n)$ |
| Count learning paths (DP) | $O(m \cdot n)$ | $O(m)$ |
| Enumerate all learning paths | $O(p \cdot n)$ | $O(p \cdot n)$ |

---

## 5.5 Overall Space and Time Complexity

### 5.5.1 Space Complexity

| Data Structure | Space | Notes |
|----------------|-------|-------|
| Domain $Q$ | $O(n)$ | Set of item identifiers |
| DAG $G = (Q, E)$ | $O(n + e)$ | Adjacency list representation |
| Knowledge space $\mathcal{K}$ | $O(m \cdot n)$ | $m$ frozensets, each up to size $n$ |
| State transition graph | $O(m \cdot n)$ | Adjacency list on $m$ nodes |
| BLIM parameters | $O(m + n)$ | $\pi$: $m$ values; $\beta, \eta$: $n$ each |
| Belief distribution (assessment) | $O(m)$ | Posterior over states |

**Dominant term:** $O(m \cdot n)$ for storing the knowledge space itself.

### 5.5.2 Time Complexity Summary

| Task | Time | Dominates when... |
|------|------|--------------------|
| Parse domain and build DAG | $O(n + e)$ | Always fast |
| Construct knowledge space | $O(m \cdot n^2)$ | $m$ large (exponential in $n$) |
| Verify knowledge space | $O(m^2 \cdot n)$ | $m$ large |
| Verify learning space | $O(m^2 \cdot n)$ | $m$ large |
| Single adaptive assessment step | $O(m \cdot n)$ | Per question |
| Full adaptive assessment ($T$ questions) | $O(T \cdot m \cdot n)$ | $T \leq n$ typically |
| BLIM parameter estimation ($I$ EM iterations, $N$ learners) | $O(I \cdot N \cdot m \cdot n)$ | Large datasets |

### 5.5.3 Scaling Guidelines

| $n$ (items) | Max feasible $m$ | Typical use case |
|-------------|-------------------|------------------|
| $\leq 10$ | $\leq 1024$ | Full enumeration, exact methods |
| $11$--$15$ | $\leq 32768$ | Feasible with optimization |
| $16$--$20$ | $\leq 10^6$ | Requires pruning or sampling |
| $> 20$ | $> 10^6$ | Approximate methods needed |

For domains with $n > 20$ items and dense prerequisite structures, **exact** knowledge space construction becomes impractical. In such cases, one should consider:

1. **Decomposition**: Split the domain into weakly connected components and handle each independently.
2. **Sampling**: Use Markov chain Monte Carlo to sample from $\mathcal{K}$ rather than enumerating all states.
3. **Approximation**: Work with a subset of "important" states (e.g., states on short learning paths).

---

## 5.6 Amortized and Average-Case Analysis

### 5.6.1 Average Number of States

For a **random partial order** on $n$ items (each edge present independently with probability $p$), the expected number of downsets is:

$$
\mathbb{E}[|\mathcal{K}|] \;\approx\; 2^{n(1 - p)} \quad \text{(heuristic, for sparse posets)}
$$

For **tree-structured** prerequisite DAGs (common in practice), the number of downsets satisfies:

$$
|\mathcal{K}| \;\leq\; \prod_{v \in \text{leaves}} (d_v + 1)
$$

where $d_v$ is the depth of leaf $v$. This is typically much smaller than $2^n$.

### 5.6.2 Adaptive Assessment Convergence

Under the BLIM with bounded error rates $\beta_q \leq \beta < 0.5$ and $\eta_q \leq \eta < 0.5$, the entropy of the belief distribution decreases by at least:

$$
\Delta H \;\geq\; \frac{(1 - \beta - \eta)^2}{2 \ln 2} \cdot \frac{1}{m}
$$

per question (information-theoretic lower bound on per-item information gain). Consequently, the expected number of questions to identify the correct state is:

$$
T^* \;\leq\; \frac{\log_2 m}{(1 - \beta - \eta)^2 / (2 \ln 2)} \;=\; O\!\left(\frac{\log m}{(1 - \beta - \eta)^2}\right)
$$

In practice, adaptive assessment typically requires $O(\log m)$ questions, which is far fewer than the $n$ items in the domain.

---

## References

1. Ganter, B. (1984). Two basic algorithms in concept analysis. *Preprint 831*, Technische Hochschule Darmstadt.
2. Eppstein, D., Falmagne, J.-C., & Ovchinnikov, S. (2008). *Media Theory*. Springer.
3. Doignon, J.-P. & Falmagne, J.-C. (1999). *Knowledge Spaces*. Springer-Verlag.
4. Falmagne, J.-C. & Doignon, J.-P. (2011). *Learning Spaces*. Springer.
5. Haberman, S. J. (1979). *Analysis of Qualitative Data* (Vol. 2). Academic Press.
6. Hagberg, A. A., Schult, D. A., & Swart, P. J. (2008). Exploring network structure, dynamics, and function using NetworkX. *Proceedings of the 7th Python in Science Conference*, 11--15.
