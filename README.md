# KST Course Engine

[![CI](https://github.com/gonzalezulises/kst-course-engine/actions/workflows/ci.yml/badge.svg)](https://github.com/gonzalezulises/kst-course-engine/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)](https://github.com/gonzalezulises/kst-course-engine)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Knowledge Space Theory (KST) Course Engine** — formal mathematical structures for adaptive learning, implemented in Python with rigorous type safety and 100% test coverage.

## Mathematical Foundation

A **knowledge space** is a pair $(Q, \mathcal{K})$ where $Q$ is a finite set of items and $\mathcal{K} \subseteq 2^Q$ satisfies:

$$
\emptyset \in \mathcal{K}, \quad Q \in \mathcal{K}, \quad K_1, K_2 \in \mathcal{K} \Rightarrow K_1 \cup K_2 \in \mathcal{K}
$$

A **learning space** additionally satisfies the **accessibility** axiom (antimatroid property): every non-empty state $K$ contains an item $q$ such that $K \setminus \{q\} \in \mathcal{K}$.

## Quick Start

```bash
git clone https://github.com/gonzalezulises/kst-course-engine.git
cd kst-course-engine
uv venv && uv pip install -e ".[dev]"
```

```python
from kst_core import Domain, Item, KnowledgeSpace, KnowledgeState

# Define a domain of arithmetic skills
items = [Item(id="add"), Item(id="sub"), Item(id="mul")]
domain = Domain(items=frozenset(items))

# Define feasible knowledge states
states = frozenset({
    KnowledgeState(),                                          # ∅
    KnowledgeState(items=frozenset({items[0]})),              # {add}
    KnowledgeState(items=frozenset({items[0], items[1]})),    # {add, sub}
    KnowledgeState(items=frozenset(items)),                    # {add, sub, mul}
})

# Construct a validated knowledge space
space = KnowledgeSpace(domain=domain, states=states)

# Explore learning paths
from kst_core import LearningSpace
ls = LearningSpace(domain=domain, states=states)
for path in ls.learning_paths():
    print(" → ".join(item.id for item in path))
# add → sub → mul
```

## Features

- **`kst_core.domain`** — `Item`, `KnowledgeState`, `Domain` with full set-algebraic operations
- **`kst_core.space`** — `KnowledgeSpace` (axioms S1-S3) and `LearningSpace` (antimatroid)
- **`kst_core.prerequisites`** — `SurmiseRelation` (quasi-orders) and `PrerequisiteGraph` (DAG with NetworkX)
- **`kst_core.validation`** — Formal validators with bibliographic references

## Development

```bash
uv run pytest                          # Run tests (100% coverage required)
uv run ruff check kst_core/ tests/     # Lint
uv run ruff format kst_core/ tests/    # Format
uv run mypy kst_core/                  # Type check (strict mode)
```

## Documentation

Full doctoral-level documentation with formal proofs available at the [documentation site](https://kst-course-engine.vercel.app).

## References

- Doignon, J.-P. & Falmagne, J.-Cl. (1999). *Knowledge Spaces*. Springer.
- Falmagne, J.-Cl. & Doignon, J.-P. (2011). *Learning Spaces*. Springer.
- Birkhoff, G. (1937). Rings of sets. *Duke Mathematical Journal*, 3(3), 443-454.

## License

MIT
