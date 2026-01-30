---
sidebar_position: 2
title: "Testing Strategy"
---

# Testing Strategy

The `kst_core` test suite combines traditional unit tests with property-based testing to achieve rigorous verification of mathematical invariants. This document describes the testing philosophy, tools, and patterns used throughout the project.

## Overview

| Layer | Tool | Purpose |
|-------|------|---------|
| Unit tests | pytest | Verify specific behaviors and edge cases |
| Property-based tests | Hypothesis | Verify algebraic laws hold universally |
| Type checking | mypy (strict) | Catch type errors statically |
| Linting | ruff | Enforce code style and catch common errors |
| Coverage | coverage.py | Ensure 100% line coverage |

---

## Property-Based Testing with Hypothesis

### Why Property-Based Testing?

KST is a mathematical theory with well-defined algebraic properties. Traditional example-based tests verify that *specific inputs* produce *expected outputs*. Property-based tests verify that *algebraic laws hold for all valid inputs*.

For example, instead of testing that the union of $\{a\}$ and $\{b\}$ equals $\{a, b\}$, we test that **union is commutative for all pairs of knowledge states**:

$$
\forall\, K_1, K_2 \in \mathcal{K} : K_1 \cup K_2 = K_2 \cup K_1
$$

Hypothesis generates hundreds of random valid inputs and checks the property for each one, providing much stronger guarantees than a handful of examples.

### How Hypothesis Works

Hypothesis uses **strategies** to generate random test data. A strategy describes how to produce valid instances of a type. Tests are decorated with `@given(...)` and receive randomly generated arguments:

```python
from hypothesis import given
import hypothesis.strategies as st

@given(x=st.integers(), y=st.integers())
def test_addition_commutative(x: int, y: int) -> None:
    assert x + y == y + x
```

When a test fails, Hypothesis **shrinks** the failing example to the smallest possible counterexample, making debugging straightforward.

---

## Custom Strategies for KST Types

The module `kst_core.testing.strategies` provides Hypothesis strategies for generating valid KST structures. These strategies are designed to produce well-formed instances that satisfy all required invariants.

### `items()`

Generates random `Item` instances with unique, non-empty IDs.

```python
from kst_core.testing.strategies import items

@given(item=items())
def test_item_has_nonempty_id(item):
    assert len(item.id) > 0
```

### `domains(min_size, max_size)`

Generates random `Domain` instances with a configurable number of items.

```python
from kst_core.testing.strategies import domains

@given(domain=domains(min_size=2, max_size=6))
def test_domain_nonempty(domain):
    assert len(domain.items) >= 2
```

### `knowledge_states(domain)`

Generates random `KnowledgeState` instances that are subsets of the given domain. This is a **dependent strategy** -- it requires a domain to have been drawn first.

```python
from hypothesis import given
import hypothesis.strategies as st
from kst_core.testing.strategies import domains, knowledge_states

@given(data=st.data())
def test_state_subset_of_domain(data):
    domain = data.draw(domains(min_size=3, max_size=5))
    state = data.draw(knowledge_states(domain))
    assert domain.contains_state(state)
```

### `knowledge_spaces(domain)`

Generates valid `KnowledgeSpace` instances on the given domain. The strategy ensures that axioms S1, S2, and S3 are satisfied.

**Strategy algorithm:**
1. Start with $\{\emptyset, Q\}$.
2. Randomly add subsets of $Q$.
3. Close under union to satisfy S3.

```python
from kst_core.testing.strategies import domains, knowledge_spaces

@given(data=st.data())
def test_space_contains_empty_and_full(data):
    domain = data.draw(domains(min_size=2, max_size=4))
    space = data.draw(knowledge_spaces(domain))
    assert space.domain.empty_state in space.states
    assert space.domain.full_state in space.states
```

### `learning_spaces(domain)`

Generates valid `LearningSpace` instances, which additionally satisfy the accessibility axiom.

**Strategy algorithm:**
1. Generate a random DAG on the domain.
2. Compute the surmise relation (transitive closure).
3. Compute all downsets (valid knowledge states).
4. The resulting space is guaranteed to be a learning space.

```python
from kst_core.testing.strategies import domains, learning_spaces

@given(data=st.data())
def test_learning_space_accessible(data):
    domain = data.draw(domains(min_size=2, max_size=4))
    ls = data.draw(learning_spaces(domain))
    for state in ls.states:
        if not state.is_empty:
            # At least one item can be removed
            assert any(
                KnowledgeState(items=state.items - frozenset({item})) in ls.states
                for item in state.items
            )
```

---

## Algebraic Properties Tested

### KnowledgeState Set Operations

| Property | Test |
|----------|------|
| Union commutativity | $K_1 \cup K_2 = K_2 \cup K_1$ |
| Union associativity | $(K_1 \cup K_2) \cup K_3 = K_1 \cup (K_2 \cup K_3)$ |
| Union identity | $K \cup \emptyset = K$ |
| Union idempotence | $K \cup K = K$ |
| Intersection commutativity | $K_1 \cap K_2 = K_2 \cap K_1$ |
| Intersection associativity | $(K_1 \cap K_2) \cap K_3 = K_1 \cap (K_2 \cap K_3)$ |
| Intersection identity | $K \cap Q = K$ (where $K \subseteq Q$) |
| Absorption (union over intersection) | $K_1 \cup (K_1 \cap K_2) = K_1$ |
| Absorption (intersection over union) | $K_1 \cap (K_1 \cup K_2) = K_1$ |
| De Morgan (complement) | $(K_1 \cup K_2)^c = K_1^c \cap K_2^c$ |
| Subset antisymmetry | $K_1 \subseteq K_2 \land K_2 \subseteq K_1 \implies K_1 = K_2$ |
| Subset transitivity | $K_1 \subseteq K_2 \land K_2 \subseteq K_3 \implies K_1 \subseteq K_3$ |

### KnowledgeSpace Axioms

| Property | Test |
|----------|------|
| Empty set membership | $\emptyset \in \mathcal{K}$ |
| Full domain membership | $Q \in \mathcal{K}$ |
| Union closure | $K_1, K_2 \in \mathcal{K} \implies K_1 \cup K_2 \in \mathcal{K}$ |
| Atoms are minimal | $\forall A \in \text{atoms}: \nexists K \in \mathcal{K}: \emptyset \subset K \subset A$ |
| Fringe consistency | $q \in K^O \iff K \cup \{q\} \in \mathcal{K}$ |

### LearningSpace Properties

| Property | Test |
|----------|------|
| Accessibility | $\forall K \neq \emptyset: \exists q \in K: K \setminus \{q\} \in \mathcal{L}$ |
| Learning paths exist | At least one path from $\emptyset$ to $Q$ |
| Path validity | Every state in a learning path is in $\mathcal{L}$ |
| Path monotonicity | Each step in a path adds exactly one item |

### SurmiseRelation Properties

| Property | Test |
|----------|------|
| Reflexivity | $\forall q: q \preceq q$ |
| Transitivity | $p \preceq q \land q \preceq r \implies p \preceq r$ |
| Downsets are states | `is_downset(K)` iff $K$ is a valid knowledge state |
| Birkhoff roundtrip | Relation $\to$ space $\to$ relation recovers original |

### PrerequisiteGraph Properties

| Property | Test |
|----------|------|
| Acyclicity | Graph has no directed cycles |
| Topological order validity | Every edge $(u, v)$ has $u$ before $v$ in every ordering |
| Transitive closure | `to_surmise_relation()` is the transitive closure |
| Critical path is longest | No path in the DAG is longer than `critical_path()` |

---

## 100% Coverage Requirement

The project enforces **100% line coverage** via CI:

```bash
uv run pytest --cov=kst_core --cov-report=term-missing --cov-fail-under=100
```

### Why 100%?

For a mathematical library, untested code is unverified code. Every branch and edge case must be exercised. The combination of property-based testing (which explores edge cases automatically) and 100% coverage ensures comprehensive verification.

### Achieving 100% Coverage

- **Property-based tests** cover the main logic paths through random input generation.
- **Unit tests** cover specific edge cases, error paths, and boundary conditions.
- **Validation error tests** ensure that all invalid inputs raise appropriate errors.

```python
def test_empty_item_id_rejected():
    """Ensure that Items with empty IDs are rejected."""
    with pytest.raises(ValueError, match="non-empty"):
        Item(id="")

def test_cyclic_graph_rejected():
    """Ensure that cyclic prerequisite graphs are rejected."""
    a, b = Item(id="a"), Item(id="b")
    domain = Domain(items=frozenset({a, b}))
    with pytest.raises(ValueError, match="cycle"):
        PrerequisiteGraph(domain=domain, edges=frozenset({(a, b), (b, a)}))
```

---

## Integration Testing

Integration tests verify that the modules work together correctly:

1. **Prerequisite graph to knowledge space**: Build a DAG, derive the surmise relation, compute knowledge states, validate the resulting space.
2. **Validation roundtrip**: Construct structures, validate them, ensure all checks pass.
3. **End-to-end learning path**: Define prerequisites, build a learning space, enumerate learning paths, verify each path is valid.

```python
def test_prerequisite_graph_to_learning_space_roundtrip():
    """Full pipeline: DAG -> SurmiseRelation -> KnowledgeSpace -> validation."""
    # Build prerequisite graph
    a, b, c = Item(id="a"), Item(id="b"), Item(id="c")
    domain = Domain(items=frozenset({a, b, c}))
    graph = PrerequisiteGraph(domain=domain, edges=frozenset({(a, b), (b, c)}))

    # Derive knowledge states
    relation = graph.to_surmise_relation()
    states = relation.to_knowledge_space_states()

    # Validate as learning space
    report = validate_learning_space(domain=domain, states=states)
    assert report.is_valid

    # Build learning space and enumerate paths
    ls = LearningSpace(domain=domain, states=states)
    paths = ls.learning_paths()
    assert len(paths) >= 1

    # Verify path validity
    for path in paths:
        assert path[0].is_empty
        assert path[-1] == domain.full_state
        for i in range(len(path) - 1):
            diff = path[i + 1].items - path[i].items
            assert len(diff) == 1  # exactly one item added per step
```

---

## Running Tests in CI

The CI pipeline runs:

1. `ruff check .` -- Linting
2. `ruff format --check .` -- Formatting
3. `mypy src/kst_core --strict` -- Type checking
4. `pytest --cov=kst_core --cov-fail-under=100` -- Tests with coverage

All four steps must pass for a PR to be merged.
