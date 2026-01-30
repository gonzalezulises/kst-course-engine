---
sidebar_position: 4
title: "Validation Module"
---

# Validation Module (`kst_core.validation`)

The validation module provides structured validation for knowledge structures, returning detailed reports with references to the relevant mathematical definitions.

## `ValidationResult`

A single validation check result.

```python
from kst_core.validation import ValidationResult

result = ValidationResult(
    check="S1: Empty set membership",
    passed=True,
    message="The empty set is a member of the knowledge space.",
    reference="Doignon & Falmagne (1999), Definition 1.1.1",
)
```

**Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `check` | `str` | Name of the validation check |
| `passed` | `bool` | Whether the check passed |
| `message` | `str` | Human-readable explanation |
| `reference` | `str \| None` | Bibliographic reference for the axiom |

## `ValidationReport`

An aggregated report containing multiple `ValidationResult` entries.

```python
from kst_core.validation import ValidationReport

report = ValidationReport(results=[result1, result2, result3])
```

**Properties:**
| Property | Type | Description |
|----------|------|-------------|
| `is_valid` | `bool` | `True` if all checks passed |
| `results` | `list[ValidationResult]` | All individual results |
| `failures` | `list[ValidationResult]` | Only failed results |
| `summary` | `str` | Human-readable summary |

**Usage:**

```python
if not report.is_valid:
    for failure in report.failures:
        print(f"FAIL: {failure.check}")
        print(f"  {failure.message}")
        print(f"  Ref: {failure.reference}")
```

---

## `validate_knowledge_space()`

Validates that a candidate family of sets $\mathcal{K}$ satisfies the axioms of a knowledge space on domain $Q$.

```python
from kst_core.validation import validate_knowledge_space
from kst_core import Domain, Item, KnowledgeState

a = Item(id="a")
b = Item(id="b")
domain = Domain(items=frozenset({a, b}))

empty = KnowledgeState(items=frozenset())
s_a = KnowledgeState(items=frozenset({a}))
full = KnowledgeState(items=frozenset({a, b}))

report = validate_knowledge_space(
    domain=domain,
    states=frozenset({empty, s_a, full}),
)
```

### Checks Performed

| Check | Axiom | Reference |
|-------|-------|-----------|
| S1: Empty set | $\emptyset \in \mathcal{K}$ | Doignon & Falmagne (1999), Def. 1.1.1 |
| S2: Full domain | $Q \in \mathcal{K}$ | Doignon & Falmagne (1999), Def. 1.1.1 |
| S3: Union closure | $\forall \mathcal{F} \subseteq \mathcal{K}: \bigcup \mathcal{F} \in \mathcal{K}$ | Doignon & Falmagne (1999), Def. 1.1.1 |
| Domain consistency | $\forall K \in \mathcal{K}: K \subseteq Q$ | Well-formedness |

### Example Output

```python
report = validate_knowledge_space(domain=domain, states=frozenset({empty, full}))

print(report.summary)
# Validation Report: 3 of 4 checks passed.
#
# PASSED: S1 — Empty set is a member of the space.
# PASSED: S2 — Full domain is a member of the space.
# FAILED: S3 — Union closure violated. The union of {} and {a, b} is {a, b},
#         which is in the space, but pairwise union of {a} | {b} = {a, b}...
#         (specific violation details)
# PASSED: Domain consistency — All states are subsets of Q.
```

---

## `validate_learning_space()`

Validates all knowledge space axioms **plus** the accessibility axiom required for a learning space.

```python
from kst_core.validation import validate_learning_space

report = validate_learning_space(
    domain=domain,
    states=frozenset({empty, s_a, full}),
)
```

### Additional Checks

| Check | Axiom | Reference |
|-------|-------|-----------|
| Accessibility | $\forall K \in \mathcal{L},\; K \neq \emptyset \implies \exists q \in K : K \setminus \{q\} \in \mathcal{L}$ | Falmagne & Doignon (2011), Def. 1.4.1 |

The accessibility axiom ensures that every knowledge state can be reached from the empty state by learning one item at a time.

### Example: Detecting Accessibility Violation

```python
from kst_core import Domain, Item, KnowledgeState
from kst_core.validation import validate_learning_space

a = Item(id="a")
b = Item(id="b")
c = Item(id="c")
domain = Domain(items=frozenset({a, b, c}))

empty = KnowledgeState(items=frozenset())
s_ab = KnowledgeState(items=frozenset({a, b}))  # no single-item state!
full = KnowledgeState(items=frozenset({a, b, c}))

report = validate_learning_space(
    domain=domain,
    states=frozenset({empty, s_ab, full}),
)

print(report.is_valid)
# False

for failure in report.failures:
    print(f"{failure.check}: {failure.message}")
# Accessibility: State {a, b} is not accessible — neither {a} nor {b}
# is a member of the space. (Ref: Falmagne & Doignon, 2011)
```

### Full Validation Workflow

```python
from kst_core import Domain, Item, KnowledgeState, PrerequisiteGraph
from kst_core.validation import validate_learning_space

# Build from prerequisites
add = Item(id="add", label="Addition")
sub = Item(id="sub", label="Subtraction")
mul = Item(id="mul", label="Multiplication")

domain = Domain(items=frozenset({add, sub, mul}))

graph = PrerequisiteGraph(
    domain=domain,
    edges=frozenset({(add, sub), (add, mul)}),
)

# Derive states from the prerequisite structure
relation = graph.to_surmise_relation()
states = relation.to_knowledge_space_states()

# Validate the derived space
report = validate_learning_space(domain=domain, states=states)

assert report.is_valid, report.summary
print("All checks passed:")
for result in report.results:
    print(f"  {result.check}: {result.message}")
    if result.reference:
        print(f"    Ref: {result.reference}")
```
