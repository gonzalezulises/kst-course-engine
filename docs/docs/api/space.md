---
sidebar_position: 2
title: "Space Module"
---

# Space Module (`kst_core.space`)

The space module implements knowledge structures and learning spaces, the central constructs of Knowledge Space Theory.

## `KnowledgeSpace`

A knowledge space is a pair $(Q, \mathcal{K})$ where $Q$ is a domain and $\mathcal{K} \subseteq 2^Q$ is a family of knowledge states satisfying closure properties.

### Constructor Validation

When constructing a `KnowledgeSpace`, the following axioms are validated:

| Axiom | Formal Statement | Description |
|-------|-----------------|-------------|
| **S1** | $\emptyset \in \mathcal{K}$ | The empty set is a state |
| **S2** | $Q \in \mathcal{K}$ | The full domain is a state |
| **S3** | For all $\mathcal{F} \subseteq \mathcal{K}$, $\bigcup \mathcal{F} \in \mathcal{K}$ | Closed under union |

If any axiom is violated, a `ValueError` is raised with a descriptive message.

```python
from kst_core import Domain, Item, KnowledgeState, KnowledgeSpace

a = Item(id="a")
b = Item(id="b")
c = Item(id="c")
domain = Domain(items=frozenset({a, b, c}))

empty = KnowledgeState(items=frozenset())
s_a = KnowledgeState(items=frozenset({a}))
s_ab = KnowledgeState(items=frozenset({a, b}))
full = KnowledgeState(items=frozenset({a, b, c}))

space = KnowledgeSpace(
    domain=domain,
    states=frozenset({empty, s_a, s_ab, full}),
)
```

### `atoms`

The atoms of a knowledge space are the minimal non-empty states:

$$
\text{atoms}(\mathcal{K}) = \{ K \in \mathcal{K} \mid K \neq \emptyset \text{ and } \nexists\, K' \in \mathcal{K} : \emptyset \subset K' \subset K \}
$$

```python
atoms = space.atoms
# frozenset({KnowledgeState(items=frozenset({a}))})
```

### `inner_fringe(state)`

The inner fringe of a state $K$ is the set of items whose removal still yields a valid state:

$$
K^I = \{ q \in K \mid K \setminus \{q\} \in \mathcal{K} \}
$$

This identifies items that a learner in state $K$ has most recently mastered.

```python
fringe = space.inner_fringe(s_ab)
# Items that can be individually removed from {a, b} and still leave a valid state
```

### `outer_fringe(state)`

The outer fringe of a state $K$ is the set of items whose addition yields a valid state:

$$
K^O = \{ q \in Q \setminus K \mid K \cup \{q\} \in \mathcal{K} \}
$$

This identifies items that a learner in state $K$ is ready to learn next.

```python
fringe = space.outer_fringe(s_a)
# Items that can be individually added to {a} and still yield a valid state
```

### `gradation()`

A gradation is a sequence of nested sub-families $\mathcal{K}_0 \subset \mathcal{K}_1 \subset \cdots \subset \mathcal{K}_n = \mathcal{K}$ where each $\mathcal{K}_i$ is itself a knowledge space on some sub-domain. The gradation partitions the states by cardinality:

$$
\mathcal{K}_i = \{ K \in \mathcal{K} \mid |K| = i \}
$$

```python
gradation = space.gradation()
# Returns a list of sets of states, grouped by cardinality
# gradation[0] = {empty}, gradation[1] = {s_a}, ...
```

## `LearningSpace`

A learning space is a knowledge space $(Q, \mathcal{L})$ that additionally satisfies an **accessibility** axiom:

$$
\forall\, K \in \mathcal{L},\; K \neq \emptyset \implies \exists\, q \in K : K \setminus \{q\} \in \mathcal{L}
$$

This guarantees that every non-empty state can be reached from the empty state by adding one item at a time along a valid learning path.

A `LearningSpace` inherits all methods from `KnowledgeSpace` and adds:

### Constructor Validation

In addition to axioms S1, S2, and S3 from `KnowledgeSpace`, the constructor validates:

| Axiom | Formal Statement | Description |
|-------|-----------------|-------------|
| **Accessibility** | $\forall K \in \mathcal{L},\; K \neq \emptyset \implies \exists q \in K : K \setminus \{q\} \in \mathcal{L}$ | Every state is reachable |

```python
from kst_core import LearningSpace

learning_space = LearningSpace(
    domain=domain,
    states=frozenset({empty, s_a, s_ab, full}),
)
```

### `learning_paths()`

Returns all maximal learning paths from $\emptyset$ to $Q$. A learning path is a sequence of states:

$$
\emptyset = K_0 \subset K_1 \subset \cdots \subset K_n = Q
$$

where each $K_{i+1} = K_i \cup \{q_i\}$ for some $q_i \in Q$ and each $K_i \in \mathcal{L}$.

```python
paths = learning_space.learning_paths()
# Each path is a tuple of KnowledgeStates from empty to full
for path in paths:
    items_learned = [
        path[i + 1].items - path[i].items
        for i in range(len(path) - 1)
    ]
    print("Order:", [next(iter(s)).id for s in items_learned])
```

### Full Example

```python
from kst_core import Domain, Item, KnowledgeState, LearningSpace

# Define items
add = Item(id="addition", label="Addition")
sub = Item(id="subtraction", label="Subtraction")
mul = Item(id="multiplication", label="Multiplication")

domain = Domain(items=frozenset({add, sub, mul}))

# Build states — subtraction and multiplication both require addition
empty = KnowledgeState(items=frozenset())
s_add = KnowledgeState(items=frozenset({add}))
s_add_sub = KnowledgeState(items=frozenset({add, sub}))
s_add_mul = KnowledgeState(items=frozenset({add, mul}))
full = KnowledgeState(items=frozenset({add, sub, mul}))

ls = LearningSpace(
    domain=domain,
    states=frozenset({empty, s_add, s_add_sub, s_add_mul, full}),
)

# Outer fringe: what can a learner study next?
ready = ls.outer_fringe(s_add)
# {sub, mul} — both are available after mastering addition

# Learning paths from empty to full
for path in ls.learning_paths():
    print(path)
```
