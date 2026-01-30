---
sidebar_position: 2
title: "Novel Contributions"
---

# Novel Contributions

This project, `kst_core`, makes several novel contributions to the implementation and practical application of Knowledge Space Theory. While the mathematical foundations of KST are well-established, the software engineering aspects have received comparatively little attention. This work bridges that gap by providing a modern, rigorous Python implementation.

---

## 1. Formal Python Implementation with Pydantic Validation

### Contribution

`kst_core` is the first Python implementation of KST that uses **Pydantic v2** models with strict validation to enforce mathematical invariants at the type level.

### Motivation

Previous implementations of KST (notably the `kst` R package by Unlu and Sargin, 2010, and various ALEKS internals) do not leverage modern type systems to enforce constraints. This leads to runtime errors that could be caught earlier, and makes it difficult to distinguish valid from invalid structures.

### Approach

Every core type in `kst_core` is a frozen Pydantic model with custom validators:

```python
from pydantic import BaseModel, field_validator

class Item(BaseModel, frozen=True):
    id: str
    label: str = ""

    @field_validator("id")
    @classmethod
    def id_must_be_nonempty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Item id must be non-empty")
        return v
```

Knowledge spaces validate axioms S1 ($\emptyset \in \mathcal{K}$), S2 ($Q \in \mathcal{K}$), and S3 (union closure) at construction time. Learning spaces additionally validate the accessibility axiom. Surmise relations validate reflexivity and transitivity. Prerequisite graphs validate acyclicity.

This means that **if you hold a reference to a `KnowledgeSpace` object, it is guaranteed to be a valid knowledge space**. Invalid structures cannot exist in memory.

### Impact

- Eliminates an entire class of bugs (operating on invalid structures).
- Provides clear, actionable error messages referencing the specific axiom violated.
- Enables IDE autocompletion and static analysis through type annotations.

---

## 2. Property-Based Testing with Hypothesis

### Contribution

`kst_core` uses **Hypothesis** (MacIver, 2019) for property-based testing, with custom strategies that generate valid KST structures and verify algebraic properties.

### Motivation

Traditional unit tests check specific examples. For mathematical software, this is insufficient -- we need to verify that **algebraic laws hold universally**, not just for a few hand-picked cases. Property-based testing generates random inputs and checks that properties hold for all of them.

### Custom Strategies

We define Hypothesis strategies for generating:

- **Items** with unique, non-empty IDs.
- **Domains** of configurable size.
- **Knowledge states** that are subsets of a given domain.
- **Valid knowledge spaces** satisfying S1, S2, and S3.
- **Valid learning spaces** additionally satisfying accessibility.
- **Quasi-orders** (surmise relations) on a domain.
- **DAGs** (prerequisite graphs) on a domain.

### Algebraic Properties Tested

The test suite verifies fundamental mathematical properties:

| Property | Structure | Formal Statement |
|----------|-----------|-----------------|
| Commutativity of union | `KnowledgeState` | $K_1 \cup K_2 = K_2 \cup K_1$ |
| Associativity of union | `KnowledgeState` | $(K_1 \cup K_2) \cup K_3 = K_1 \cup (K_2 \cup K_3)$ |
| Identity of union | `KnowledgeState` | $K \cup \emptyset = K$ |
| Idempotence of union | `KnowledgeState` | $K \cup K = K$ |
| Absorption laws | `KnowledgeState` | $K_1 \cup (K_1 \cap K_2) = K_1$ |
| Union closure | `KnowledgeSpace` | $K_1, K_2 \in \mathcal{K} \implies K_1 \cup K_2 \in \mathcal{K}$ |
| Boundary states | `KnowledgeSpace` | $\emptyset, Q \in \mathcal{K}$ |
| Accessibility | `LearningSpace` | $K \neq \emptyset \implies \exists q : K \setminus \{q\} \in \mathcal{L}$ |
| Birkhoff correspondence | `SurmiseRelation` | Downsets of $\preceq$ form a knowledge space |
| Reflexivity | `SurmiseRelation` | $q \preceq q$ for all $q$ |
| Transitivity | `SurmiseRelation` | $p \preceq q \land q \preceq r \implies p \preceq r$ |
| Acyclicity | `PrerequisiteGraph` | No directed cycles exist |
| Transitive closure correctness | `PrerequisiteGraph` | `to_surmise_relation()` produces the transitive closure |

### Example

```python
from hypothesis import given
import hypothesis.strategies as st
from kst_core.testing.strategies import knowledge_states, domains

@given(data=st.data())
def test_union_commutativity(data):
    domain = data.draw(domains(min_size=2, max_size=5))
    k1 = data.draw(knowledge_states(domain))
    k2 = data.draw(knowledge_states(domain))
    assert k1.union(k2) == k2.union(k1)
```

---

## 3. Type-Safe API with Full mypy Strict Compliance

### Contribution

The entire codebase passes **mypy in strict mode** with zero errors, providing complete static type safety.

### Motivation

KST involves complex nested types (frozensets of frozensets, tuples of Items, etc.) where type errors are easy to introduce. Static type checking catches these before runtime.

### Implementation Details

- All function signatures are fully annotated.
- Generic types are used where appropriate (e.g., `frozenset[KnowledgeState]`).
- No `Any` types or `# type: ignore` comments.
- Pydantic models use strict field types.
- Custom `__eq__`, `__hash__`, and `__lt__` methods are typed correctly.

```python
def outer_fringe(self, state: KnowledgeState) -> frozenset[Item]:
    """Compute the outer fringe K^O of a state K."""
    result: set[Item] = set()
    for item in self.domain.items - state.items:
        candidate = KnowledgeState(items=state.items | frozenset({item}))
        if candidate in self.states:
            result.add(item)
    return frozenset(result)
```

### Configuration

```toml
[tool.mypy]
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
```

---

## 4. DAG-Based Prerequisite Management with NetworkX

### Contribution

`kst_core` uses **NetworkX** for representing and analyzing prerequisite graphs, providing efficient algorithms for topological sorting, transitive closure, critical path analysis, and cycle detection.

### Motivation

While the surmise relation provides the complete prerequisite information, practitioners typically think in terms of direct prerequisites (a DAG). The `PrerequisiteGraph` class bridges this gap, allowing users to specify direct prerequisites and automatically compute:

- The full surmise relation (via transitive closure).
- All valid topological orderings (complete learning sequences).
- The critical path (minimum sequential learning steps).
- All valid knowledge states (via Birkhoff's theorem through the derived surmise relation).

### Implementation

```python
import networkx as nx

class PrerequisiteGraph:
    def __init__(self, domain: Domain, edges: frozenset[tuple[Item, Item]]):
        self._graph = nx.DiGraph()
        self._graph.add_nodes_from(domain.items)
        self._graph.add_edges_from(edges)
        if not nx.is_directed_acyclic_graph(self._graph):
            raise ValueError("Prerequisite graph contains a cycle")

    def critical_path(self) -> list[Item]:
        return nx.dag_longest_path(self._graph)

    def topological_orders(self) -> list[tuple[Item, ...]]:
        return [tuple(order) for order in nx.all_topological_sorts(self._graph)]
```

### Benefits

- Leverages battle-tested graph algorithms from NetworkX.
- Efficient cycle detection prevents invalid prerequisite structures.
- All topological sorts enumeration enables curriculum flexibility analysis.
- Critical path computation identifies bottleneck prerequisite chains.

---

## 5. Validation Framework with Bibliographic References

### Contribution

`kst_core` provides a structured validation framework that not only checks mathematical axioms but also returns **bibliographic references** for each violated axiom.

### Motivation

When a knowledge structure fails validation, users need to understand *why* and *where the definition comes from*. By citing the specific definition from Doignon and Falmagne (1999) or Falmagne and Doignon (2011), the validation framework serves an educational purpose alongside its technical function.

### Implementation

```python
from kst_core.validation import validate_knowledge_space

report = validate_knowledge_space(domain=domain, states=states)
for result in report.results:
    print(f"{'PASS' if result.passed else 'FAIL'}: {result.check}")
    if result.reference:
        print(f"  Reference: {result.reference}")
```

Output:
```
PASS: S1 — Empty set membership
  Reference: Doignon & Falmagne (1999), Definition 1.1.1
PASS: S2 — Full domain membership
  Reference: Doignon & Falmagne (1999), Definition 1.1.1
FAIL: S3 — Union closure
  Reference: Doignon & Falmagne (1999), Definition 1.1.1
PASS: Domain consistency
  Reference: Well-formedness check
```

### Benefits

- Actionable error messages for researchers and developers.
- Bridges the gap between mathematical theory and software practice.
- Facilitates learning KST through interactive experimentation.
- Structured `ValidationReport` objects enable programmatic handling of validation failures.

---

## Summary of Contributions

| Contribution | Key Technology | Novel Aspect |
|-------------|---------------|-------------|
| Pydantic validation | Pydantic v2 | Invariants enforced at construction |
| Property-based testing | Hypothesis | Algebraic laws verified stochastically |
| Type safety | mypy strict | Complete static type coverage |
| DAG prerequisites | NetworkX | Graph algorithms for curriculum analysis |
| Validation framework | Custom | Bibliographic references in error messages |

These contributions collectively provide the first **production-quality, formally verified** Python implementation of Knowledge Space Theory, suitable for both research and educational technology applications.
