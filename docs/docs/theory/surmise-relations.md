---
sidebar_position: 2
title: "Surmise Relations"
---

# Surmise Relations

This chapter develops the algebraic correspondence between **quasi-orders** (surmise relations) on a domain and the combinatorial families that constitute knowledge spaces. The central result is a form of **Birkhoff's Representation Theorem**, establishing a bijection between quasi-orders on $Q$ and union-closed families of subsets of $Q$ containing $\emptyset$ and $Q$.

**Primary references**: Doignon & Falmagne (1999), Chapter 3; Birkhoff (1937).

---

## 2.1 Surmise Relations

### Definition 2.1 (Surmise Relation)

> A **surmise relation** on a finite set $Q$ is a binary relation $\preceq$ on $Q$ that is a **quasi-order** (preorder), i.e., it satisfies:
>
> 1. **Reflexivity**: $\forall q \in Q,\; q \preceq q$.
> 2. **Transitivity**: $\forall p, q, r \in Q,\; p \preceq q \text{ and } q \preceq r \;\Longrightarrow\; p \preceq r$.
>
> The interpretation is: $p \preceq q$ means "mastery of $q$ **surmises** (implies) mastery of $p$", or equivalently, "$p$ is a **prerequisite** of $q$".

For any quasi-order $\preceq$ on $Q$ and any item $q \in Q$, the **downset** (or **predecessor set**) of $q$ is:

$$
{\downarrow}q \;=\; \{ p \in Q : p \preceq q \}
$$

The **upset** of $q$ is:

$$
{\uparrow}q \;=\; \{ r \in Q : q \preceq r \}
$$

Note that reflexivity ensures $q \in {\downarrow}q$ and $q \in {\uparrow}q$.

When $\preceq$ is additionally **antisymmetric** ($p \preceq q$ and $q \preceq p$ imply $p = q$), the quasi-order is a **partial order**. In KST, we typically work with partial orders on the item set, representing strict prerequisite hierarchies.

---

## 2.2 Surmise Systems

### Definition 2.2 (Surmise System)

> A **surmise system** on $Q$ is a mapping $\sigma: Q \to 2^{2^Q} \setminus \{\emptyset\}$ that assigns to each item $q \in Q$ a nonempty family $\sigma(q)$ of subsets of $Q \setminus \{q\}$, called the **clauses** for $q$. The interpretation is:
>
> A learner who has mastered item $q$ must have mastered **at least one** clause $C \in \sigma(q)$ entirely.

Formally, a knowledge state $K$ containing $q$ must satisfy:

$$
q \in K \;\Longrightarrow\; \exists\, C \in \sigma(q) \text{ such that } C \subseteq K.
$$

**Special case.** When each $\sigma(q)$ is a singleton $\{C_q\}$, the surmise system reduces to a **surmise function**, and the corresponding knowledge structure is a **quasi-ordinal knowledge space** (see Section 2.3).

When $\sigma(q) = \{\emptyset\}$ for an item $q$, the item has no prerequisites and can appear in any state (it is a **root** item).

**Remark.** The distinction between surmise relations and surmise systems is fundamental:
- A **surmise relation** yields a unique prerequisite set for each item (conjunctive model -- all prerequisites must be mastered).
- A **surmise system** allows alternative prerequisite sets (disjunctive model -- at least one clause must be satisfied).

---

## 2.3 Birkhoff's Representation Theorem

### Theorem 2.1 (Birkhoff's Theorem for Knowledge Spaces)

> There is a **bijection** between:
>
> (a) Quasi-orders $\preceq$ on a finite set $Q$, and
>
> (b) Families $\mathcal{K} \subseteq 2^Q$ that are closed under both **arbitrary unions** and **arbitrary intersections** and contain $\emptyset$ and $Q$.
>
> Moreover, if $\preceq$ is a **partial order**, the corresponding family $\mathcal{K}$ is the set of **downsets** (order ideals) of $(Q, \preceq)$.

**Proof sketch.**

**(a) $\Rightarrow$ (b):** Given a quasi-order $\preceq$ on $Q$, define:

$$
\mathcal{K}_\preceq \;=\; \bigl\{ K \subseteq Q : \forall q \in K,\; {\downarrow}q \subseteq K \bigr\}
$$

That is, $\mathcal{K}_\preceq$ consists of all **downward-closed** subsets (downsets or order ideals) of $(Q, \preceq)$.

**Claim**: $\mathcal{K}_\preceq$ is closed under arbitrary unions and arbitrary intersections.

*Union closure*: Let $\{K_i\}_{i \in I} \subseteq \mathcal{K}_\preceq$. Take any $q \in \bigcup_i K_i$. Then $q \in K_j$ for some $j$. Since $K_j$ is a downset, ${\downarrow}q \subseteq K_j \subseteq \bigcup_i K_i$. Hence $\bigcup_i K_i \in \mathcal{K}_\preceq$.

*Intersection closure*: Let $\{K_i\}_{i \in I} \subseteq \mathcal{K}_\preceq$. Take any $q \in \bigcap_i K_i$. Then $q \in K_i$ for all $i$, so ${\downarrow}q \subseteq K_i$ for all $i$, hence ${\downarrow}q \subseteq \bigcap_i K_i$. Thus $\bigcap_i K_i \in \mathcal{K}_\preceq$.

*Containment*: $\emptyset$ is vacuously a downset. $Q$ is a downset since ${\downarrow}q \subseteq Q$ for all $q$.

**(b) $\Rightarrow$ (a):** Given a family $\mathcal{K}$ closed under arbitrary unions and intersections, define:

$$
p \preceq_\mathcal{K} q \;\;\Longleftrightarrow\;\; \forall K \in \mathcal{K},\; q \in K \Rightarrow p \in K
$$

*Reflexivity*: $q \in K \Rightarrow q \in K$ trivially, so $q \preceq_\mathcal{K} q$.

*Transitivity*: If $p \preceq_\mathcal{K} q$ and $q \preceq_\mathcal{K} r$, then for any $K \in \mathcal{K}$ with $r \in K$, we get $q \in K$ (by $q \preceq r$), and then $p \in K$ (by $p \preceq q$). Hence $p \preceq_\mathcal{K} r$.

**Bijection**: One verifies that $\mathcal{K}_{\preceq_\mathcal{K}} = \mathcal{K}$ and $\preceq_{\mathcal{K}_\preceq} = \preceq$, establishing the bijection. The key step for the first identity uses the fact that every element of $\mathcal{K}$ can be written as both a union of principal downsets and an intersection of principal upsets (this relies on both closure properties). $\blacksquare$

**Corollary.** A knowledge space $(Q, \mathcal{K})$ is **quasi-ordinal** (i.e., $\mathcal{K}$ is also closed under intersection) if and only if it arises from a quasi-order via the downset construction.

---

## 2.4 Computing Downsets

### Algorithm 2.1 (Downset Enumeration from a Partial Order)

Given a partial order $(Q, \preceq)$ represented as a directed acyclic graph (DAG), enumerate all downsets (order ideals).

**Input:** A DAG $G = (Q, E)$ where $(p, q) \in E$ iff $p \prec q$ (covering relation).

**Output:** The family $\mathcal{K}$ of all downsets.

**Procedure:**

```
function ENUMERATE_DOWNSETS(G):
    K ← {∅}                          # Initialize with the empty set
    queue ← {∅}

    while queue is not empty:
        S ← queue.pop()
        # Find all items whose prerequisites are satisfied by S
        for q in Q \ S:
            if ↓q ⊆ S ∪ {q}:         # All predecessors of q are in S
                S_new ← S ∪ {q}
                if S_new ∉ K:
                    K ← K ∪ {S_new}
                    queue.add(S_new)

    return K
```

**Complexity analysis:**

- Let $n = |Q|$ and $d = |\mathcal{K}|$ (number of downsets).
- Each downset is generated at most once: $O(d)$ iterations.
- For each, we scan $O(n)$ candidate items, and checking ${\downarrow}q \subseteq S \cup \{q\}$ takes $O(n)$ with adjacency-list representation.
- **Total**: $O(d \cdot n^2)$.
- **Worst case**: $d$ can be exponential in $n$ (up to $2^n$ for the antichain). The **Dedekind number** $D(n)$ gives the maximum number of antichains of an $n$-element set, and the number of downsets of a poset is at most $D(n)$.

$$
|{\mathcal{K}}| \;\leq\; 2^n, \quad \text{so worst-case time is } O(2^n \cdot n^2).
$$

---

## 2.5 Examples

### Example 2.1 (Prerequisite Structure for Arithmetic)

Consider the domain $Q = \{a, b, c, d, e\}$ with the following interpretation:

| Item | Skill |
|------|-------|
| $a$ | Counting |
| $b$ | Addition |
| $c$ | Subtraction |
| $d$ | Multiplication |
| $e$ | Division |

**Partial order** (prerequisite relation):

$$
a \prec b, \quad a \prec c, \quad b \prec d, \quad b \prec e, \quad c \prec e, \quad d \prec e
$$

The Hasse diagram:

```
          e
         / \
        d   |
        |   c
        b  /
         \/
          a
```

**Downsets** (knowledge states):

| State | Items mastered |
|-------|----------------|
| $K_0$ | $\emptyset$ |
| $K_1$ | $\{a\}$ |
| $K_2$ | $\{a, b\}$ |
| $K_3$ | $\{a, c\}$ |
| $K_4$ | $\{a, b, c\}$ |
| $K_5$ | $\{a, b, d\}$ |
| $K_6$ | $\{a, b, c, d\}$ |
| $K_7$ | $\{a, b, c, d, e\} = Q$ |

The resulting knowledge space:

$$
\mathcal{K} = \bigl\{ \emptyset,\; \{a\},\; \{a,b\},\; \{a,c\},\; \{a,b,c\},\; \{a,b,d\},\; \{a,b,c,d\},\; Q \bigr\}
$$

**Verification:** Since $\mathcal{K}$ consists of all downsets of a partial order, Theorem 2.1 guarantees it is closed under both unions and intersections. For instance:

$$
\{a,c\} \cup \{a,b,d\} = \{a,b,c,d\} \in \mathcal{K}
$$

$$
\{a,b,c\} \cap \{a,b,d\} = \{a,b\} \in \mathcal{K}
$$

**Surmise relation interpretation:** $a \preceq d$ means "mastery of multiplication ($d$) surmises mastery of counting ($a$)." The surmise function for item $e$ gives $\sigma(e) = \{\{d, c\}\}$ (both $d$ and $c$ are direct prerequisites of $e$).

---

## References

1. Birkhoff, G. (1937). Rings of sets. *Duke Mathematical Journal*, 3(3), 443--454.
2. Doignon, J.-P. & Falmagne, J.-C. (1999). *Knowledge Spaces*. Springer-Verlag.
3. Falmagne, J.-C. & Doignon, J.-P. (2011). *Learning Spaces: Interdisciplinary Applied Mathematics*. Springer.
4. Davey, B. A. & Priestley, H. A. (2002). *Introduction to Lattices and Order* (2nd ed.). Cambridge University Press.
