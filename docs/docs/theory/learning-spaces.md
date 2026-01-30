---
sidebar_position: 3
title: "Learning Spaces"
---

# Learning Spaces

A **learning space** is a knowledge space that additionally satisfies an **accessibility condition**, ensuring that every knowledge state can be reached from the empty state by adding one item at a time. Learning spaces are the combinatorial equivalent of **antimatroids** -- a well-studied class of greedoid in combinatorial optimization. This chapter develops the theory of learning spaces, fringes, and learning paths.

**Primary reference**: Falmagne, J.-C. & Doignon, J.-P. (2011). *Learning Spaces: Interdisciplinary Applied Mathematics*. Springer, Chapter 2.

---

## 3.1 Antimatroids and Learning Spaces

### Definition 3.1 (Learning Space / Antimatroid)

> A **learning space** is a knowledge space $(Q, \mathcal{L})$ satisfying the additional axiom:
>
> **(L)** **Accessibility** (or **$\mathcal{L}$-accessibility**): For every nonempty state $K \in \mathcal{L}$, there exists an item $q \in K$ such that $K \setminus \{q\} \in \mathcal{L}$.
>
> Equivalently, $(Q, \mathcal{L})$ satisfies:
>
> **(S1)** $\emptyset \in \mathcal{L}$
>
> **(S2)** $Q \in \mathcal{L}$
>
> **(S3)** $\mathcal{L}$ is closed under arbitrary unions
>
> **(L)** Every nonempty $K \in \mathcal{L}$ has a state $K \setminus \{q\} \in \mathcal{L}$ for some $q \in K$

In the language of combinatorics, a learning space is an **antimatroid** on the ground set $Q$. The accessible sets of an antimatroid are precisely the feasible sets of a **convex geometry** (via complementation).

Formally, accessibility requires:

$$
\forall K \in \mathcal{L},\; K \neq \emptyset \;\Longrightarrow\; \exists\, q \in K : K \setminus \{q\} \in \mathcal{L}
$$

**Remark.** The accessibility axiom is a "top-down" condition: every state can be reduced to the empty state by peeling off items one at a time. By induction, it implies the existence of a **learning path** from $\emptyset$ to any state $K$ (see Definition 3.3 below).

---

## 3.2 Well-Gradedness

### Theorem 3.1 (Well-Gradedness of Learning Spaces)

> Every learning space $(Q, \mathcal{L})$ is **well-graded**: for any two states $K, L \in \mathcal{L}$, the distance
>
> $$
> d(K, L) = |K \triangle L| = |K \setminus L| + |L \setminus K|
> $$
>
> equals the length of a shortest path from $K$ to $L$ in the **state transition graph** $\mathcal{G}(\mathcal{L})$, where two states are adjacent if they differ by exactly one item.

**Proof.**

Let $K, L \in \mathcal{L}$ with $d(K, L) = m$. We show there exists a path $K = S_0, S_1, \ldots, S_m = L$ in $\mathcal{L}$ with $|S_{i} \triangle S_{i+1}| = 1$ for all $i$.

**Step 1.** We first construct a path from $K$ to $K \cup L$. Since $K, L \in \mathcal{L}$, we have $K \cup L \in \mathcal{L}$ by (S3). Consider $K \cup L$; by accessibility, there exists a chain:

$$
K \cup L = T_r \supsetneq T_{r-1} \supsetneq \cdots \supsetneq T_0 = \emptyset
$$

where each $T_i \in \mathcal{L}$ and $|T_{i+1} \setminus T_i| = 1$.

**Step 2.** Similarly, $K$ and $L$ each admit such chains from $\emptyset$. More directly, consider $M = K \cup L$ and the subchain consisting of those $T_i$ that contain $K$ (such states exist since $K \subseteq K \cup L = T_r$). Let $T_{j_0} = K \cup L \supseteq T_{j_1} \supseteq \cdots$ be the states obtained by removing items in $L \setminus K$ one at a time. By accessibility applied to the knowledge space restricted to the interval $[K, K \cup L] = \{S \in \mathcal{L} : K \subseteq S \subseteq K \cup L\}$, there exists a monotone chain from $K$ to $K \cup L$ of length $|L \setminus K|$.

**Step 3.** By the same argument applied to $[K \cap L, L]$ and then adjusting, we obtain a monotone chain from $K \cup L$ down to $L$ of length $|K \setminus L|$, proceeding through states in $\mathcal{L}$.

**Step 4.** Concatenating gives a path of length $|L \setminus K| + |K \setminus L| = |K \triangle L| = m$. Since any path in the transition graph between $K$ and $L$ must change at least $m$ items (each step changes exactly one), this path is shortest. $\blacksquare$

**Corollary.** The state transition graph of a learning space is **connected** and the graph distance coincides with the symmetric difference metric.

---

## 3.3 Fringes

### Definition 3.2 (Inner and Outer Fringe)

> Let $(Q, \mathcal{L})$ be a learning space and $K \in \mathcal{L}$ a knowledge state.
>
> The **inner fringe** of $K$ is:
>
> $$
> K^I \;=\; \bigl\{ q \in K : K \setminus \{q\} \in \mathcal{L} \bigr\}
> $$
>
> The **outer fringe** of $K$ is:
>
> $$
> K^O \;=\; \bigl\{ q \in Q \setminus K : K \cup \{q\} \in \mathcal{L} \bigr\}
> $$

The inner fringe $K^I$ consists of items that can be "unlearned" (removed) from $K$ while remaining in a valid state. The outer fringe $K^O$ consists of items that the learner is **ready to learn next**.

**Properties:**

1. By the accessibility axiom, $K^I \neq \emptyset$ for every nonempty $K \in \mathcal{L}$.
2. If $K \neq Q$, then $K^O \neq \emptyset$ (since $K \cup \{q\}$ is accessible from $K$ for some $q$; this follows from the well-gradedness and the fact that $Q \in \mathcal{L}$).
3. $K^I \cap K^O = \emptyset$ (since $K^I \subseteq K$ and $K^O \subseteq Q \setminus K$).
4. $|K^I| + |K^O| \leq |Q|$.

The fringes play a central role in **adaptive assessment**: the inner fringe identifies items to test for potential removal from the estimated state, while the outer fringe identifies items to test for potential addition.

---

## 3.4 Learning Paths

### Definition 3.3 (Learning Path)

> A **learning path** in a learning space $(Q, \mathcal{L})$ is a maximal chain from $\emptyset$ to $Q$:
>
> $$
> \ell \;=\; \bigl(\emptyset = K_0,\; K_1,\; K_2,\; \ldots,\; K_n = Q\bigr)
> $$
>
> where $n = |Q|$ and for each $i \in \{0, 1, \ldots, n-1\}$:
>
> $$
> K_{i+1} = K_i \cup \{q_i\} \quad \text{for some } q_i \in K_i^O
> $$
>
> The sequence $(q_0, q_1, \ldots, q_{n-1})$ is a **permutation** of $Q$ representing the order in which items are learned.

Equivalently, a learning path is a permutation $\pi = (q_0, q_1, \ldots, q_{n-1})$ of $Q$ such that every prefix $\{q_0, q_1, \ldots, q_k\}$ is a knowledge state in $\mathcal{L}$.

**Remark.** By accessibility, learning paths always exist: starting from $Q$, repeatedly remove an item in the inner fringe to reach $\emptyset$. Reading this sequence in reverse yields a learning path.

---

## 3.5 Counting and Gradation

### Proposition 3.1 (Learning Path Enumeration)

> Let $(Q, \mathcal{L})$ be a learning space with $|Q| = n$. Then:
>
> 1. The number of learning paths is at least $1$ and at most $n!$.
> 2. The number of knowledge states satisfies $|\mathcal{L}| \leq \binom{n}{\lfloor n/2 \rfloor} + 1$... More precisely, a learning space on $n$ items satisfies $n + 1 \leq |\mathcal{L}| \leq 2^n$.
> 3. The lower bound $|\mathcal{L}| \geq n + 1$ is tight (achieved by the chain $\emptyset \subset \{q_1\} \subset \{q_1, q_2\} \subset \cdots \subset Q$).
> 4. (**Gradation**) For each $k \in \{0, 1, \ldots, n\}$, there exists at least one state $K \in \mathcal{L}$ with $|K| = k$.

**Proof of (4).** By accessibility, there exists a chain $\emptyset = K_0 \subsetneq K_1 \subsetneq \cdots \subsetneq K_n = Q$ in $\mathcal{L}$ where $|K_{i+1}| = |K_i| + 1$. Hence $|K_i| = i$ for all $i$, and every cardinality from $0$ to $n$ is represented. $\blacksquare$

**Proof of lower bound in (2).** The chain from (4) produces $n + 1$ distinct states ($K_0, K_1, \ldots, K_n$), each of a different cardinality. $\blacksquare$

---

## 3.6 Examples

### Example 3.1 (Learning Paths in an Arithmetic Domain)

Consider the learning space from Example 2.1 (Chapter 2) with $Q = \{a, b, c, d, e\}$ and the partial order:

$$
a \prec b, \quad a \prec c, \quad b \prec d, \quad b \prec e, \quad c \prec e, \quad d \prec e
$$

The knowledge states (downsets) are:

$$
\mathcal{L} = \bigl\{ \emptyset,\; \{a\},\; \{a,b\},\; \{a,c\},\; \{a,b,c\},\; \{a,b,d\},\; \{a,b,c,d\},\; Q \bigr\}
$$

This is a learning space since every nonempty state has an item whose removal yields another state:

| State $K$ | Inner fringe $K^I$ | Outer fringe $K^O$ |
|------------|---------------------|---------------------|
| $\{a\}$ | $\{a\}$ | $\{b, c\}$ |
| $\{a,b\}$ | $\{b\}$ | $\{c, d\}$ |
| $\{a,c\}$ | $\{c\}$ | $\{b\}$ |
| $\{a,b,c\}$ | $\{b, c\}$ | $\{d\}$ |
| $\{a,b,d\}$ | $\{d\}$ | $\{c\}$ |
| $\{a,b,c,d\}$ | $\{c, d\}$ | $\{e\}$ |
| $Q$ | $\{e\}$ | $\emptyset$ |

**Learning paths** (permutations of $Q$ whose prefixes are all states):

1. $(a, b, c, d, e)$: $\emptyset \to \{a\} \to \{a,b\} \to \{a,b,c\} \to \{a,b,c,d\} \to Q$
2. $(a, b, d, c, e)$: $\emptyset \to \{a\} \to \{a,b\} \to \{a,b,d\} \to \{a,b,c,d\} \to Q$
3. $(a, c, b, d, e)$: $\emptyset \to \{a\} \to \{a,c\} \to \{a,b,c\} \to \{a,b,c,d\} \to Q$

There are exactly **3 learning paths** in this space. Notice that every path begins with $a$ (the sole root item) and ends with $e$ (the sole maximal item). The inner items $b, c, d$ can be ordered in ways consistent with the prerequisite structure.

**Pedagogical interpretation:** A curriculum designer can choose any of the three learning paths as a recommended sequence. Path 1 teaches addition before subtraction, then multiplication, then division. Path 2 teaches addition, then multiplication before subtraction, then division. Path 3 teaches subtraction immediately after counting, delaying multiplication.

---

## References

1. Falmagne, J.-C. & Doignon, J.-P. (2011). *Learning Spaces: Interdisciplinary Applied Mathematics*. Springer.
2. Doignon, J.-P. & Falmagne, J.-C. (1999). *Knowledge Spaces*. Springer-Verlag.
3. Korte, B., Lovasz, L., & Schrader, R. (1991). *Greedoids*. Springer-Verlag.
4. Dietrich, B. (1987). A circuit characterization of antimatroids. *Journal of Combinatorial Theory, Series B*, 43(3), 314--321.
5. Eppstein, D. (2008). Media theory: Interdisciplinary applied mathematics. *SIAM Review*, 50(3), 603--604.
