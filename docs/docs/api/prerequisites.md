---
sidebar_position: 3
title: "Prerequisites Module"
---

# Prerequisites Module (`kst_core.prerequisites`)

The prerequisites module provides two complementary representations of prerequisite relationships between knowledge items: the `SurmiseRelation` (a quasi-order) and the `PrerequisiteGraph` (a directed acyclic graph). These are connected through Birkhoff's theorem.

## Birkhoff's Theorem

Birkhoff's theorem establishes a foundational correspondence in KST:

> There is a one-to-one correspondence between knowledge spaces and quasi-ordinal knowledge spaces (surmise relations). Specifically, for any knowledge space $(Q, \mathcal{K})$, there exists a unique quasi-order $\preceq$ on $Q$ such that $\mathcal{K}$ is exactly the collection of downsets of $(Q, \preceq)$.

$$
\mathcal{K} = \{ K \subseteq Q \mid \forall\, q \in K,\; p \preceq q \implies p \in K \}
$$

This means prerequisite structures and knowledge spaces are two sides of the same coin.

---

## `SurmiseRelation`

A surmise relation is a quasi-order $\preceq$ on the domain $Q$. If $p \preceq q$, then mastery of $p$ is a prerequisite for mastery of $q$.

### Constructor Validation

The constructor validates that the relation is a **quasi-order** (reflexive and transitive):

| Property | Formal Statement | Description |
|----------|-----------------|-------------|
| **Reflexivity** | $\forall q \in Q : q \preceq q$ | Every item is a prerequisite of itself |
| **Transitivity** | $p \preceq q \land q \preceq r \implies p \preceq r$ | Prerequisites are transitive |

```python
from kst_core import Domain, Item, SurmiseRelation

a = Item(id="a")
b = Item(id="b")
c = Item(id="c")
domain = Domain(items=frozenset({a, b, c}))

# a is prerequisite for b, b is prerequisite for c (and transitively, a for c)
relation = SurmiseRelation(
    domain=domain,
    pairs=frozenset({
        (a, a), (b, b), (c, c),  # reflexive
        (a, b), (a, c), (b, c),  # a -> b -> c
    }),
)
```

### `prerequisites_of(item)`

Returns the set of all prerequisites for a given item:

$$
\text{pre}(q) = \{ p \in Q \mid p \preceq q \}
$$

```python
prereqs = relation.prerequisites_of(c)
# {a, b, c} — a and b must be mastered before c
```

### `dependents_of(item)`

Returns the set of all items that depend on the given item:

$$
\text{dep}(q) = \{ r \in Q \mid q \preceq r \}
$$

```python
deps = relation.dependents_of(a)
# {a, b, c} — mastering a unlocks b and c
```

### `is_downset(state)`

Checks whether a knowledge state $K$ is a downset (order ideal) of the quasi-order:

$$
K \text{ is a downset} \iff \forall\, q \in K,\; p \preceq q \implies p \in K
$$

Downsets correspond exactly to valid knowledge states under Birkhoff's theorem.

```python
from kst_core import KnowledgeState

state_ab = KnowledgeState(items=frozenset({a, b}))
state_ac = KnowledgeState(items=frozenset({a, c}))

relation.is_downset(state_ab)  # True — {a, b} respects prerequisites
relation.is_downset(state_ac)  # False — c requires b, which is missing
```

### `to_knowledge_space_states()`

Generates all valid knowledge states (downsets) from the surmise relation, producing the knowledge space $\mathcal{K}$ via Birkhoff's theorem:

$$
\mathcal{K} = \{ K \subseteq Q \mid K \text{ is a downset of } \preceq \}
$$

```python
states = relation.to_knowledge_space_states()
# frozenset({
#     KnowledgeState(frozenset()),       # empty
#     KnowledgeState(frozenset({a})),     # {a}
#     KnowledgeState(frozenset({a, b})),  # {a, b}
#     KnowledgeState(frozenset({a, b, c}))  # {a, b, c}
# })
```

---

## `PrerequisiteGraph`

A prerequisite graph is a directed acyclic graph (DAG) where edges represent direct prerequisite relationships. It provides the most compact representation of prerequisites by storing only the **transitive reduction** of the surmise relation.

### Constructor Validation

The constructor validates that the graph is a **DAG** (no cycles):

```python
from kst_core import PrerequisiteGraph, Domain, Item

a = Item(id="a")
b = Item(id="b")
c = Item(id="c")
domain = Domain(items=frozenset({a, b, c}))

# a -> b -> c (direct edges only, no need for a -> c)
graph = PrerequisiteGraph(
    domain=domain,
    edges=frozenset({(a, b), (b, c)}),
)
```

If a cycle is detected, a `ValueError` is raised.

### `topological_orders()`

Returns all valid topological orderings of the DAG. Each ordering represents a valid complete learning sequence:

```python
orders = graph.topological_orders()
# [("a", "b", "c")] — only one valid order for a linear chain
```

For a DAG with parallel branches, multiple orderings are possible.

### `to_surmise_relation()`

Computes the transitive closure of the DAG to produce the corresponding `SurmiseRelation`:

$$
p \preceq q \iff \text{there is a directed path from } p \text{ to } q \text{ in the graph}
$$

```python
relation = graph.to_surmise_relation()
# Now relation.prerequisites_of(c) includes both a and b
```

### `critical_path()`

Returns the critical path -- the longest path in the DAG. This represents the minimum number of sequential learning steps required:

```python
path = graph.critical_path()
# [a, b, c]
```

### `longest_path_length()`

Returns the length of the critical path:

$$
\ell = \max_{(v_0, v_1, \ldots, v_k) \text{ path in } G} k
$$

```python
length = graph.longest_path_length()
# 2 — two edges in the path a -> b -> c
```

### `direct_prerequisites(item)`

Returns only the immediate predecessors in the DAG (not the full transitive closure):

```python
graph.direct_prerequisites(c)
# {b} — only b is a direct prerequisite of c
```

### `direct_dependents(item)`

Returns only the immediate successors in the DAG:

```python
graph.direct_dependents(a)
# {b} — only b directly depends on a
```

### Full Example

```python
from kst_core import Domain, Item, PrerequisiteGraph

# Arithmetic curriculum
add = Item(id="addition", label="Addition")
sub = Item(id="subtraction", label="Subtraction")
mul = Item(id="multiplication", label="Multiplication")
div = Item(id="division", label="Division")
frac = Item(id="fractions", label="Fractions")

domain = Domain(items=frozenset({add, sub, mul, div, frac}))

graph = PrerequisiteGraph(
    domain=domain,
    edges=frozenset({
        (add, sub),   # addition before subtraction
        (add, mul),   # addition before multiplication
        (mul, div),   # multiplication before division
        (div, frac),  # division before fractions
    }),
)

# Critical path determines minimum sequential steps
print(graph.critical_path())
# [addition, multiplication, division, fractions]

print(graph.longest_path_length())
# 3

# Convert to surmise relation for full prerequisite analysis
relation = graph.to_surmise_relation()
print(relation.prerequisites_of(frac))
# {addition, multiplication, division, fractions}

# Generate all valid knowledge states
states = relation.to_knowledge_space_states()
print(len(states))  # Number of valid knowledge states
```
