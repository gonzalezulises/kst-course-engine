---
sidebar_position: 8
title: "Learning Module"
---

# Learning Module (`kst_core.learning`)

The learning module implements a **discrete-time Markov chain** model on learning spaces. It models how learners transition between knowledge states by acquiring new items, with transition probabilities proportional to per-item learning rates.

## Mathematical Foundation

From state $K$, a learner transitions to $K \cup \{q\}$ for $q$ in the outer fringe $O(K)$:

$$
P(K \to K \cup \{q\}) = \frac{\lambda_q}{\sum_{q' \in O(K)} \lambda_{q'}}
$$

where $\lambda_q > 0$ is the learning rate for item $q$.

The full domain $Q$ is the unique **absorbing state** (full mastery). Expected steps to mastery are computed via the **fundamental matrix** of the absorbing chain:

$$
N = (I - T)^{-1}
$$

where $T$ is the transient-to-transient sub-matrix. Expected steps from state $K_i = \sum_j N_{ij}$ (row sum).

**Reference**: Falmagne, J.-C. & Doignon, J.-P. (2011). *Learning Spaces*, Ch. 15.

---

## `LearningRate`

Per-item learning rate parameters $\lambda_q > 0$. Frozen Pydantic model.

```python
from kst_core import LearningRate, Domain, Item

domain = Domain(items=frozenset({
    Item(id="a"), Item(id="b"), Item(id="c"),
}))

# Uniform rates
rates = LearningRate.uniform(domain, rate=2.0)

# Custom per-item rates
rates = LearningRate(
    domain=domain,
    rates={"a": 1.0, "b": 3.0, "c": 0.5},
)
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `domain` | `Domain` | The knowledge domain |
| `rates` | `dict[str, float]` | Learning rates $\lambda_q > 0$ per item |

**Validation:**
- All rates must be strictly positive
- Keys must exactly match the domain's item IDs

### Class Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `uniform(domain, rate=1.0)` | `LearningRate` | Uniform rates for all items |

---

## `LearningModel`

Markov chain learning model. Frozen Pydantic model.

```python
from kst_core import LearningModel, LearningRate, parse_file

course = parse_file("examples/intro-pandas.kst.yaml")
space = course.to_learning_space()
rates = LearningRate.uniform(course.domain)
model = LearningModel(space=space, rates=rates)
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `space` | `LearningSpace` | The learning space |
| `rates` | `LearningRate` | Per-item learning rates |

**Validation:**
- Space domain and rate domain must match

### Instance Methods

#### `transition_probs(state) -> dict[KnowledgeState, float]`

Transition probabilities from state $K$.

```python
from kst_core import KnowledgeState, Item

empty = KnowledgeState()
probs = model.transition_probs(empty)
# {KnowledgeState({import}): 1.0} for linear prerequisite
```

For the absorbing state $Q$, returns $\{Q: 1.0\}$.

#### `transition_matrix() -> tuple[tuple[KnowledgeState, ...], ndarray]`

Full $|K| \times |K|$ transition matrix.

```python
states, matrix = model.transition_matrix()
# matrix[i, j] = P(K_i -> K_j)
# Rows sum to 1.0
```

States are sorted by cardinality then lexicographically.

#### `expected_steps() -> dict[KnowledgeState, float]`

Expected number of steps from each state to full mastery $Q$.

```python
expected = model.expected_steps()
print(f"Steps from empty: {expected[KnowledgeState()]:.1f}")
# Full state always maps to 0.0
```

Uses the fundamental matrix $N = (I - T)^{-1}$ of the absorbing Markov chain.

#### `simulate_trajectory(start, rng, max_steps) -> tuple[KnowledgeState, ...]`

Simulate a learning trajectory.

```python
import numpy as np

traj = model.simulate_trajectory(rng=np.random.default_rng(42))
for state in traj:
    print(sorted(state.item_ids))
# [] -> ['import'] -> ['dataframe', 'import'] -> ... -> [all items]
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `start` | `KnowledgeState \| None` | `None` (= $\emptyset$) | Initial state |
| `rng` | `Generator \| None` | `None` | Random generator |
| `max_steps` | `int` | `1000` | Safety limit |

#### `optimal_teaching_item(state) -> str`

Select the item that minimizes expected steps to mastery if taught next.

```python
item = model.optimal_teaching_item(KnowledgeState())
print(f"Teach: {item}")  # The item leading to lowest expected mastery time
```

---

## Complete Example

```python
from kst_core import parse_file, LearningRate, LearningModel, KnowledgeState
import numpy as np

# Parse course and build model
course = parse_file("examples/intro-pandas.kst.yaml")
space = course.to_learning_space()

# Custom rates: some items are easier to learn
rates = LearningRate(
    domain=course.domain,
    rates={item.id: 2.0 if "import" in item.id else 1.0
           for item in course.domain},
)
model = LearningModel(space=space, rates=rates)

# Expected steps to mastery
expected = model.expected_steps()
empty = KnowledgeState()
print(f"Expected steps from scratch: {expected[empty]:.1f}")

# Optimal teaching sequence
state = empty
while state != course.domain.full_state:
    item = model.optimal_teaching_item(state)
    print(f"  Teach: {item}")
    from kst_core import Item
    state = KnowledgeState(items=state.items | {Item(id=item)})

# Simulate 100 learners
rng = np.random.default_rng(42)
lengths = []
for _ in range(100):
    traj = model.simulate_trajectory(rng=rng)
    lengths.append(len(traj) - 1)  # steps = transitions
print(f"Average trajectory length: {np.mean(lengths):.1f}")
print(f"Std dev: {np.std(lengths):.1f}")
```

## References

- Falmagne, J.-C. & Doignon, J.-P. (2011). *Learning Spaces*, Ch. 15.
