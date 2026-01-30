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

### From YAML (declarative)

Define a course in `.kst.yaml`:

```yaml
# examples/intro-pandas.kst.yaml
domain:
  name: "Introduction to Pandas"
  items:
    - id: "import"
      label: "Importing pandas"
    - id: "series"
      label: "Understanding Series"
    - id: "dataframe"
      label: "Understanding DataFrames"
    - id: "indexing"
      label: "Indexing and selecting data"
prerequisites:
  edges:
    - ["import", "series"]
    - ["import", "dataframe"]
    - ["series", "indexing"]
    - ["dataframe", "indexing"]
```

```python
from kst_core import parse_file

course = parse_file("examples/intro-pandas.kst.yaml")
print(f"{course.name}: {len(course.domain)} items, {len(course.states)} states")

ls = course.to_learning_space()
for path in ls.learning_paths():
    print(" → ".join(item.id for item in path))
```

### From code (programmatic)

```python
from kst_core import Domain, Item, KnowledgeSpace, KnowledgeState

items = [Item(id="add"), Item(id="sub"), Item(id="mul")]
domain = Domain(items=frozenset(items))

states = frozenset({
    KnowledgeState(),
    KnowledgeState(items=frozenset({items[0]})),
    KnowledgeState(items=frozenset({items[0], items[1]})),
    KnowledgeState(items=frozenset(items)),
})

space = KnowledgeSpace(domain=domain, states=states)
```

## Architecture

```
kst_core/
├── domain.py          # Item, KnowledgeState, Domain
├── space.py           # KnowledgeSpace, LearningSpace
├── prerequisites.py   # SurmiseRelation, PrerequisiteGraph
├── validation.py      # ValidationResult, ValidationReport
├── parser.py          # YAML parser (.kst.yaml → KST structures)
├── assessment.py      # BLIM adaptive assessment engine
├── estimation.py      # EM parameter estimation for BLIM
└── learning.py        # Markov learning model on learning spaces
```

**Data flow:**

```
.kst.yaml ──parse──▸ CourseDefinition
                          │
              ┌───────────┼───────────┐
              ▼           ▼           ▼
           Domain    PrereqGraph   SurmiseRelation
              │           │           │
              └─────┬─────┘     (Birkhoff)
                    ▼                 │
             KnowledgeSpace ◂─────────┘
                    │
                    ▼
             LearningSpace
              ╱          ╲
     learning_paths    fringes
```

## Modules

| Module | Classes | Description |
|--------|---------|-------------|
| `domain` | `Item`, `KnowledgeState`, `Domain` | Set-algebraic foundations |
| `space` | `KnowledgeSpace`, `LearningSpace` | Axiom validation, fringes, learning paths |
| `prerequisites` | `SurmiseRelation`, `PrerequisiteGraph` | Quasi-orders, DAGs, Birkhoff theorem |
| `validation` | `ValidationResult`, `ValidationReport` | Formal validators with bibliographic refs |
| `parser` | `CourseDefinition`, `parse_yaml`, `parse_file` | Declarative YAML course definitions |
| `assessment` | `BLIMParameters`, `BeliefState`, `AdaptiveAssessment` | BLIM adaptive assessment with Bayesian updating |
| `estimation` | `ResponseData`, `BLIMEstimate`, `em_fit`, `goodness_of_fit` | EM parameter estimation and model fit |
| `learning` | `LearningRate`, `LearningModel` | Markov chain learning model with optimal teaching |

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
