---
sidebar_position: 1
title: "Knowledge Spaces"
---

# Knowledge Spaces

This chapter introduces the foundational combinatorial structures of Knowledge Space Theory. We define knowledge structures and knowledge spaces, establish their closure properties, and prove that the family of knowledge spaces on a fixed domain forms a complete lattice under set inclusion.

**Primary reference**: Doignon, J.-P. & Falmagne, J.-C. (1999). *Knowledge Spaces*. Springer-Verlag, Chapter 1.

---

## 1.1 Basic Definitions

Let $Q$ denote a finite, nonempty set of **items** (problems, skills, or competencies). A subset $K \subseteq Q$ is interpreted as the collection of items that a given learner has mastered. We call $K$ a **knowledge state**.

### Definition 1.1 (Knowledge Structure)

> A **knowledge structure** is an ordered pair $(Q, \mathcal{K})$ where $Q$ is a nonempty finite set (the **domain**) and $\mathcal{K} \subseteq 2^Q$ is a family of subsets of $Q$ satisfying:
>
> **(S1)** $\emptyset \in \mathcal{K}$
>
> **(S2)** $Q \in \mathcal{K}$
>
> The elements of $\mathcal{K}$ are called **knowledge states**.

Formally:

$$
\mathcal{K} \subseteq 2^Q, \quad \text{with} \quad \emptyset \in \mathcal{K} \quad \text{and} \quad Q \in \mathcal{K}.
$$

The requirement that $\emptyset \in \mathcal{K}$ captures the existence of a learner who has mastered nothing; $Q \in \mathcal{K}$ captures the existence of a fully knowledgeable learner. No further structural constraints are imposed at this level.

### Definition 1.2 (Knowledge Space)

> A **knowledge space** is a knowledge structure $(Q, \mathcal{K})$ that additionally satisfies:
>
> **(S3)** For any nonempty subfamily $\mathcal{F} \subseteq \mathcal{K}$, we have $\bigcup \mathcal{F} \in \mathcal{K}$.
>
> That is, $\mathcal{K}$ is **closed under arbitrary unions**.

Equivalently, axioms (S1)--(S3) state:

$$
\emptyset \in \mathcal{K}, \qquad Q \in \mathcal{K}, \qquad \forall\, \mathcal{F} \subseteq \mathcal{K},\; \mathcal{F} \neq \emptyset \;\Longrightarrow\; \bigcup_{K \in \mathcal{F}} K \in \mathcal{K}.
$$

Note that (S2) follows from (S3) when $\mathcal{K}$ is finite and nonempty (take $\mathcal{F} = \mathcal{K}$), but we state it explicitly for clarity.

**Remark.** A knowledge space is a particular case of a **Moore family** (closed under arbitrary intersections) only when it is also intersection-closed. In general, knowledge spaces are union-closed but need not be intersection-closed. The dual notion -- a family closed under arbitrary intersections and containing $\emptyset$ and $Q$ -- is called a **closure space** or **closure system**.

---

## 1.2 Closure Properties

### Theorem 1.1 (Complete Lattice Structure)

> Let $(Q, \mathcal{K})$ be a knowledge space. Then $(\mathcal{K}, \subseteq)$ is a **complete join-semilattice** with the join operation given by set union. Specifically:
>
> 1. For any $\mathcal{F} \subseteq \mathcal{K}$, the **join** $\bigvee \mathcal{F} = \bigcup \mathcal{F} \in \mathcal{K}$.
> 2. For any $K \in \mathcal{K}$ and any $q \in Q$, there exists a unique **smallest** state containing $q$, namely $K_q = \bigcup \{ K' \in \mathcal{K} : q \in K' \}$.
> 3. $(\mathcal{K}, \subseteq)$ forms a **complete lattice** where the meet is given by $\bigwedge \mathcal{F} = \bigcup \{ K \in \mathcal{K} : K \subseteq \bigcap \mathcal{F} \}$.

**Proof.**

*(1)* Closure under arbitrary unions is axiom (S3).

*(2)* Let $q \in Q$ and define $\mathcal{K}_q = \{ K \in \mathcal{K} : q \in K \}$. Since $Q \in \mathcal{K}$ and $q \in Q$, we have $\mathcal{K}_q \neq \emptyset$. By (S3), $K_q := \bigcup \mathcal{K}_q \in \mathcal{K}$. But observe that $K_q$ contains $q$ and is contained in every state that contains $q$? No -- $K_q$ is the largest such state. For the *smallest* state containing $q$, define instead:

$$
K_q^* = \bigcap \{ K \in \mathcal{K} : q \in K \}.
$$

However, $K_q^*$ need not belong to $\mathcal{K}$ in general (since knowledge spaces are not necessarily intersection-closed). Instead, define:

$$
\sigma(q) = \bigcup \{ K \in \mathcal{K} : q \in K \text{ and } \forall K' \subsetneq K,\, q \notin K' \text{ or } K' \notin \mathcal{K} \}.
$$

More precisely, the atom-like state for $q$ is handled via the **notion of a clause** or **surmise function** (see Chapter 2). In a knowledge space, for each item $q$, the family $\{ K \in \mathcal{K} : q \in K \}$ has a well-defined join, namely $Q$ itself or a smaller state. The key insight is that every element of a union-closed family containing $\emptyset$ and $Q$ participates in a complete lattice when we define the meet appropriately.

*(3)* Define the **meet** (greatest lower bound) of a subfamily $\mathcal{F} \subseteq \mathcal{K}$ as:

$$
\bigwedge \mathcal{F} = \bigcup \bigl\{ K \in \mathcal{K} : K \subseteq \bigcap \mathcal{F} \bigr\}.
$$

We verify this is the greatest lower bound. Let $L = \bigwedge \mathcal{F}$.

- **$L \in \mathcal{K}$**: The set $\{ K \in \mathcal{K} : K \subseteq \bigcap \mathcal{F} \}$ is a subfamily of $\mathcal{K}$ (possibly just $\{\emptyset\}$, which is nonempty since $\emptyset \in \mathcal{K}$ and $\emptyset \subseteq \bigcap \mathcal{F}$). By (S3), its union belongs to $\mathcal{K}$.

- **$L \subseteq F$ for all $F \in \mathcal{F}$**: Every $K$ in the defining family satisfies $K \subseteq \bigcap \mathcal{F} \subseteq F$, so $L = \bigcup\{K : K \subseteq \bigcap \mathcal{F}\} \subseteq \bigcap \mathcal{F} \subseteq F$.

- **Maximality**: If $M \in \mathcal{K}$ with $M \subseteq F$ for all $F \in \mathcal{F}$, then $M \subseteq \bigcap \mathcal{F}$, so $M$ is one of the sets in $\{ K \in \mathcal{K} : K \subseteq \bigcap \mathcal{F} \}$, hence $M \subseteq L$.

Therefore $(\mathcal{K}, \subseteq)$ is a complete lattice. $\blacksquare$

---

## 1.3 Intersection Properties

### Proposition 1.1

> Let $\mathcal{K}_1$ and $\mathcal{K}_2$ be knowledge spaces on the same domain $Q$. Their intersection $\mathcal{K}_1 \cap \mathcal{K}_2$ is a knowledge space **if and only if** $\mathcal{K}_1 \cap \mathcal{K}_2$ is closed under arbitrary unions.

**Proof.**

($\Rightarrow$) If $\mathcal{K}_1 \cap \mathcal{K}_2$ is a knowledge space, it is union-closed by definition.

($\Leftarrow$) Assume $\mathcal{K}_1 \cap \mathcal{K}_2$ is closed under arbitrary unions. We verify the axioms:

- **(S1)**: $\emptyset \in \mathcal{K}_1$ and $\emptyset \in \mathcal{K}_2$, so $\emptyset \in \mathcal{K}_1 \cap \mathcal{K}_2$.
- **(S2)**: $Q \in \mathcal{K}_1$ and $Q \in \mathcal{K}_2$, so $Q \in \mathcal{K}_1 \cap \mathcal{K}_2$.
- **(S3)**: Holds by assumption.

Therefore $\mathcal{K}_1 \cap \mathcal{K}_2$ is a knowledge space. $\blacksquare$

**Remark.** In general, $\mathcal{K}_1 \cap \mathcal{K}_2$ need *not* be union-closed. Consider $Q = \{a,b\}$, $\mathcal{K}_1 = \{\emptyset, \{a\}, Q\}$, $\mathcal{K}_2 = \{\emptyset, \{b\}, Q\}$. Then $\mathcal{K}_1 \cap \mathcal{K}_2 = \{\emptyset, Q\}$, which *is* trivially union-closed. However, more complex examples can fail. The intersection of two union-closed families is not guaranteed to be union-closed -- this is a well-known fact in lattice theory. The *union* $\mathcal{K}_1 \cup \mathcal{K}_2$, taken as a family of sets, is also not generally a knowledge space; one must take the **union closure** $\langle \mathcal{K}_1 \cup \mathcal{K}_2 \rangle_\cup$.

---

## 1.4 Examples

### Example 1.1

Let $Q = \{a, b, c\}$ with the prerequisite interpretation:
- Item $a$ has no prerequisites.
- Item $b$ requires mastery of $a$.
- Item $c$ requires mastery of both $a$ and $b$.

**Valid knowledge space:**

$$
\mathcal{K}_1 = \bigl\{\, \emptyset,\; \{a\},\; \{a,b\},\; \{a,b,c\} \,\bigr\}
$$

**Verification of axioms:**

| Axiom | Check | Result |
|-------|-------|--------|
| (S1) $\emptyset \in \mathcal{K}_1$ | $\emptyset$ is listed | Pass |
| (S2) $Q \in \mathcal{K}_1$ | $\{a,b,c\}$ is listed | Pass |
| (S3) Union closure | $\{a\} \cup \{a,b\} = \{a,b\} \in \mathcal{K}_1$; all other unions are supersets already in $\mathcal{K}_1$ | Pass |

This is a **chain** (totally ordered by inclusion):

$$
\emptyset \subset \{a\} \subset \{a,b\} \subset \{a,b,c\}
$$

**A richer knowledge space on the same domain:**

$$
\mathcal{K}_2 = \bigl\{\, \emptyset,\; \{a\},\; \{b\},\; \{a,b\},\; \{a,c\},\; \{a,b,c\} \,\bigr\}
$$

Verification of (S3): we must check all pairwise unions (and beyond):

$$
\{a\} \cup \{b\} = \{a,b\} \in \mathcal{K}_2, \quad \{a\} \cup \{a,c\} = \{a,c\} \in \mathcal{K}_2, \quad \{b\} \cup \{a,c\} = \{a,b,c\} \in \mathcal{K}_2
$$

All unions remain in $\mathcal{K}_2$. This is a valid knowledge space.

**An invalid family (not a knowledge space):**

$$
\mathcal{K}_3 = \bigl\{\, \emptyset,\; \{a\},\; \{b\},\; \{a,b,c\} \,\bigr\}
$$

This fails (S3) because:

$$
\{a\} \cup \{b\} = \{a,b\} \notin \mathcal{K}_3.
$$

---

## 1.5 Lattice Diagram

For the knowledge space $\mathcal{K}_1 = \{\emptyset, \{a\}, \{a,b\}, \{a,b,c\}\}$, the Hasse diagram of $(\mathcal{K}_1, \subseteq)$ is:

```
        {a,b,c}
           |
         {a,b}
           |
          {a}
           |
           ∅
```

For $\mathcal{K}_2$, the lattice structure is:

```
         {a,b,c}
         /     \
      {a,b}   {a,c}
      /   \     |
    {a}   {b}   |
      \   /    /
        ∅ ---+
```

The meet and join are computed as described in Theorem 1.1. For instance, in $\mathcal{K}_2$:

$$
\{b\} \wedge \{a,c\} = \bigcup\{K \in \mathcal{K}_2 : K \subseteq \{b\} \cap \{a,c\}\} = \bigcup\{K \in \mathcal{K}_2 : K \subseteq \emptyset\} = \emptyset
$$

$$
\{b\} \vee \{a,c\} = \{b\} \cup \{a,c\} = \{a,b,c\}
$$

---

## References

1. Doignon, J.-P. & Falmagne, J.-C. (1985). Spaces for the assessment of knowledge. *International Journal of Man-Machine Studies*, 23(2), 175--196.
2. Doignon, J.-P. & Falmagne, J.-C. (1999). *Knowledge Spaces*. Springer-Verlag.
3. Falmagne, J.-C. & Doignon, J.-P. (2011). *Learning Spaces: Interdisciplinary Applied Mathematics*. Springer.
