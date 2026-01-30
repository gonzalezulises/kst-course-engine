---
sidebar_position: 3
title: "Contributing"
---

# Contributing

Thank you for your interest in contributing to `kst_core`. This guide covers the code standards, development workflow, and process for submitting changes.

## Code Style

### Ruff

All code is linted and formatted using **ruff**. The configuration is in `pyproject.toml`:

```toml
[tool.ruff]
target-version = "py312"
line-length = 99

[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "W",    # pycodestyle warnings
    "F",    # pyflakes
    "I",    # isort
    "N",    # pep8-naming
    "UP",   # pyupgrade
    "B",    # flake8-bugbear
    "SIM",  # flake8-simplify
    "TCH",  # flake8-type-checking
    "RUF",  # ruff-specific rules
]
```

Run before committing:

```bash
uv run ruff check --fix .
uv run ruff format .
```

### Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Classes | PascalCase | `KnowledgeSpace`, `ValidationResult` |
| Functions/methods | snake_case | `outer_fringe()`, `to_surmise_relation()` |
| Constants | UPPER_SNAKE_CASE | `MAX_DOMAIN_SIZE` |
| Type variables | PascalCase | `T`, `ItemT` |
| Private methods | Leading underscore | `_validate_union_closure()` |
| Test functions | `test_` prefix | `test_union_commutativity()` |

### Docstrings

All public functions and classes must have docstrings following Google style:

```python
def outer_fringe(self, state: KnowledgeState) -> frozenset[Item]:
    """Compute the outer fringe of a knowledge state.

    The outer fringe K^O consists of all items outside K whose
    addition yields a valid state in the space.

    Args:
        state: A knowledge state in this space.

    Returns:
        The set of items in Q \\ K that can be individually added
        to K to produce another state in the space.

    Raises:
        ValueError: If state is not a member of this space.
    """
```

---

## Type Checking

### mypy Strict Mode

The entire codebase must pass **mypy in strict mode** with zero errors:

```bash
uv run mypy src/kst_core
```

### Requirements

- **All functions** must have complete type annotations (parameters and return type).
- **No `Any` types** -- use specific types or generics.
- **No `# type: ignore` comments** -- fix the underlying issue instead.
- **No `cast()` calls** unless absolutely necessary (and document why).
- **Frozen Pydantic models** must use `model_config = ConfigDict(frozen=True)`.

### Common Patterns

```python
# Correct: explicit frozenset generic
def get_states(self) -> frozenset[KnowledgeState]:
    ...

# Correct: Optional expressed as union
def get_item(self, item_id: str) -> Item | None:
    ...

# Correct: complex return type
def gradation(self) -> list[frozenset[KnowledgeState]]:
    ...
```

---

## Testing Requirements

### All Changes Must Include Tests

Every PR must include tests for new or modified functionality. The project maintains **100% line coverage**.

### Test Types

| Type | When to Use | Framework |
|------|------------|-----------|
| Unit test | Specific behavior or edge case | pytest |
| Property-based test | Algebraic or mathematical invariant | Hypothesis |
| Error test | Invalid input handling | pytest (`raises`) |
| Integration test | Cross-module interaction | pytest |

### Writing Property-Based Tests

When adding a new mathematical structure or operation, identify the algebraic properties it should satisfy and write property-based tests:

```python
from hypothesis import given
import hypothesis.strategies as st
from kst_core.testing.strategies import knowledge_states, domains

@given(data=st.data())
def test_new_operation_is_commutative(data):
    domain = data.draw(domains(min_size=2, max_size=5))
    k1 = data.draw(knowledge_states(domain))
    k2 = data.draw(knowledge_states(domain))
    assert new_operation(k1, k2) == new_operation(k2, k1)
```

### Custom Hypothesis Strategies

If you add a new type, add a corresponding Hypothesis strategy in `kst_core/testing/strategies.py`:

```python
@st.composite
def new_structures(draw, domain: Domain) -> NewStructure:
    """Generate valid NewStructure instances on the given domain."""
    # Generate random valid data
    ...
    return NewStructure(domain=domain, data=data)
```

---

## PR Process

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

Use a descriptive branch name with a prefix:

| Prefix | Use Case |
|--------|----------|
| `feature/` | New functionality |
| `fix/` | Bug fixes |
| `refactor/` | Code restructuring |
| `docs/` | Documentation changes |
| `test/` | Test additions or fixes |

### 2. Make Your Changes

- Write code following the style guidelines above.
- Add or update tests.
- Update documentation if the public API changes.

### 3. Verify Locally

Run the full check suite before pushing:

```bash
# Lint and format
uv run ruff check --fix .
uv run ruff format .

# Type check
uv run mypy src/kst_core

# Tests with coverage
uv run pytest --cov=kst_core --cov-report=term-missing --cov-fail-under=100
```

All four checks must pass.

### 4. Commit Messages

Use conventional commit messages:

```
type(scope): short description

Longer description if needed. Explain *why* the change was made,
not just *what* changed.
```

**Types:**

| Type | Description |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `refactor` | Code change that neither fixes a bug nor adds a feature |
| `test` | Adding or updating tests |
| `docs` | Documentation changes |
| `chore` | Build process or tooling changes |

**Examples:**

```
feat(space): add gradation method to KnowledgeSpace

Implement the gradation of a knowledge space, which partitions states
by cardinality. This is useful for visualizing the structure and for
computing learning paths incrementally.

Ref: Falmagne & Doignon (2011), Section 2.3
```

```
fix(prerequisites): handle isolated nodes in critical path

Nodes with no edges were not included in the critical path computation.
Now isolated nodes are treated as paths of length 0.
```

### 5. Open a Pull Request

- Provide a clear title and description.
- Reference any related issues.
- Ensure CI passes (lint, type check, tests, coverage).
- Request review from a maintainer.

### 6. Code Review

Reviewers will check:

- Correctness of the mathematical implementation.
- Test coverage and quality of property-based tests.
- Type safety (no `Any`, no `# type: ignore`).
- Code style and documentation.

---

## Adding New Mathematical Structures

When extending `kst_core` with a new mathematical structure (e.g., a new type of knowledge structure or a new operation), follow this checklist:

### Checklist

- [ ] **Define the type** as a frozen Pydantic model in the appropriate module.
- [ ] **Validate invariants** in the constructor (e.g., closure properties, acyclicity).
- [ ] **Add type annotations** to all methods (mypy strict).
- [ ] **Write docstrings** with mathematical definitions and references.
- [ ] **Add a Hypothesis strategy** in `kst_core/testing/strategies.py`.
- [ ] **Write property-based tests** for all algebraic properties.
- [ ] **Write unit tests** for edge cases and error handling.
- [ ] **Achieve 100% coverage** for the new code.
- [ ] **Export from `__init__.py`** if it is part of the public API.
- [ ] **Update documentation** in the `docs/` directory.
- [ ] **Add bibliographic references** for the mathematical definitions.

### Example: Adding a New Structure

Suppose you want to add a `KnowledgeStructure` (a family of sets containing $\emptyset$ and $Q$ but not necessarily closed under union):

1. Define in `space.py`:

```python
class KnowledgeStructure(BaseModel, frozen=True):
    """A knowledge structure (Q, K) where K contains {} and Q.

    Reference: Doignon & Falmagne (1999), Definition 1.1.1
    """
    domain: Domain
    states: frozenset[KnowledgeState]

    @model_validator(mode="after")
    def _validate_structure(self) -> "KnowledgeStructure":
        if self.domain.empty_state not in self.states:
            raise ValueError("S1 violated: empty set not in states")
        if self.domain.full_state not in self.states:
            raise ValueError("S2 violated: full domain not in states")
        return self
```

2. Add strategy in `strategies.py`:

```python
@st.composite
def knowledge_structures(draw, domain: Domain) -> KnowledgeStructure:
    subsets = draw(st.frozensets(knowledge_states(domain), min_size=0))
    states = subsets | {domain.empty_state, domain.full_state}
    return KnowledgeStructure(domain=domain, states=frozenset(states))
```

3. Write tests:

```python
@given(data=st.data())
def test_structure_contains_boundary_states(data):
    domain = data.draw(domains(min_size=2, max_size=4))
    structure = data.draw(knowledge_structures(domain))
    assert domain.empty_state in structure.states
    assert domain.full_state in structure.states
```

---

## Questions?

If you have questions about the mathematical theory, the codebase, or the contribution process, open a GitHub issue or discussion. We welcome contributions from researchers, educators, and software engineers alike.
