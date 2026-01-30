---
sidebar_position: 6
title: "Assessment Module"
---

# Assessment Module (`kst_core.assessment`)

The assessment module implements adaptive knowledge assessment based on the **Basic Local Independence Model (BLIM)**. It provides Bayesian knowledge state estimation with entropy-based item selection.

## Mathematical Foundation

For a knowledge state $K$ and item $q$:

$$
P(\text{correct} \mid q \in K) = 1 - \beta_q \quad \text{(slip: knows but errs)}
$$

$$
P(\text{correct} \mid q \notin K) = \eta_q \quad \text{(guess: doesn't know but correct)}
$$

See [Knowledge Assessment](/docs/theory/knowledge-assessment) for the full theoretical treatment.

---

## `BLIMParameters`

Parameters for the Basic Local Independence Model. Frozen Pydantic model.

```python
from kst_core import BLIMParameters, Domain, Item

domain = Domain(items=frozenset({
    Item(id="a"), Item(id="b"), Item(id="c"),
}))

# Uniform parameters (same β and η for all items)
params = BLIMParameters.uniform(domain, beta=0.1, eta=0.1)

# Custom per-item parameters
params = BLIMParameters(
    domain=domain,
    beta={"a": 0.1, "b": 0.2, "c": 0.05},
    eta={"a": 0.1, "b": 0.15, "c": 0.1},
)
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `domain` | `Domain` | The knowledge domain |
| `beta` | `dict[str, float]` | Slip probabilities $\beta_q \in [0, 0.5)$ per item |
| `eta` | `dict[str, float]` | Guess probabilities $\eta_q \in [0, 0.5)$ per item |

**Validation:**
- All probabilities must be in $[0, 0.5)$
- Keys must exactly match the domain's item IDs

### Class Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `uniform(domain, beta=0.1, eta=0.1)` | `BLIMParameters` | Create uniform parameters for all items |

### Instance Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `p_correct(item_id, state)` | `float` | $P(\text{correct} \mid q, K)$ |
| `p_incorrect(item_id, state)` | `float` | $P(\text{incorrect} \mid q, K) = 1 - P(\text{correct})$ |

---

## `BeliefState`

Bayesian belief distribution $\pi(K) = P(\text{true state is } K)$ over knowledge states.

```python
from kst_core import BeliefState, KnowledgeState, Item

s0 = KnowledgeState(items=frozenset())
s1 = KnowledgeState(items=frozenset({Item(id="a")}))

# Uniform prior
belief = BeliefState.uniform(frozenset({s0, s1}))

# Custom distribution
belief = BeliefState(
    states=(s0, s1),
    probabilities=(0.3, 0.7),
)
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `states` | `tuple[KnowledgeState, ...]` | Ordered knowledge states |
| `probabilities` | `tuple[float, ...]` | $\pi(K)$ for each state, must sum to 1 |

**Validation:**
- States and probabilities must have same length
- At least one state required
- All probabilities non-negative
- Probabilities must sum to 1.0 (within tolerance $10^{-6}$)

### Class Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `uniform(states)` | `BeliefState` | Uniform prior $\pi(K) = 1/|\mathcal{K}|$ |

### Instance Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `entropy()` | `float` | Shannon entropy $H(\pi) = -\sum \pi(K) \log_2 \pi(K)$ |
| `map_estimate()` | `KnowledgeState` | MAP estimate $\hat{K} = \arg\max_K \pi(K)$ |
| `probability_of(state)` | `float` | $\pi(K)$ for a specific state (0 if not found) |
| `update(item_id, correct, params)` | `BeliefState` | Bayesian update $\pi'(K) \propto \pi(K) \cdot P(r \mid K, q)$ |

---

## `AdaptiveAssessment`

Adaptive assessment engine combining BLIM with entropy-based item selection.

```python
from kst_core import AdaptiveAssessment, Domain, Item, KnowledgeState, BLIMParameters

domain = Domain(items=frozenset({Item(id="a"), Item(id="b"), Item(id="c")}))

states = frozenset({
    KnowledgeState(items=frozenset()),
    KnowledgeState(items=frozenset({Item(id="a")})),
    KnowledgeState(items=frozenset({Item(id="a"), Item(id="b")})),
    KnowledgeState(items=frozenset({Item(id="a"), Item(id="b"), Item(id="c")})),
})

# Start assessment with uniform prior
session = AdaptiveAssessment.start(domain, states)
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `domain` | `Domain` | Knowledge domain |
| `states` | `frozenset[KnowledgeState]` | Possible knowledge states |
| `params` | `BLIMParameters` | BLIM error parameters |
| `belief` | `BeliefState` | Current belief distribution |
| `asked` | `frozenset[str]` | Items already asked |

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `remaining_items` | `frozenset[str]` | Items not yet asked |
| `is_complete` | `bool` | True if all items have been asked |
| `current_estimate` | `KnowledgeState` | Current MAP estimate |
| `current_entropy` | `float` | Current belief entropy |

### Class Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `start(domain, states, params=None)` | `AdaptiveAssessment` | Initialize with uniform prior |

### Instance Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `information_gain(item_id)` | `float` | Expected entropy reduction $I(q; \pi)$ |
| `select_item()` | `str` | Most informative item $q^* = \arg\max_q I(q; \pi)$ |
| `observe(item_id, correct)` | `AdaptiveAssessment` | Record response, update beliefs |
| `run(responses)` | `AdaptiveAssessment` | Batch (non-adaptive) assessment |
| `run_adaptive(respond, max_questions, entropy_threshold)` | `AdaptiveAssessment` | Fully adaptive session |

---

## `simulate_responses`

Simulate stochastic responses given a true knowledge state.

```python
from kst_core import simulate_responses, BLIMParameters, KnowledgeState, Item

import numpy as np

true_state = KnowledgeState(items=frozenset({Item(id="a"), Item(id="b")}))
params = BLIMParameters.uniform(domain, beta=0.1, eta=0.1)

responses = simulate_responses(
    true_state, params,
    rng=np.random.default_rng(42),
)
# {'a': True, 'b': True, 'c': False}  (typical with low error rates)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `true_state` | `KnowledgeState` | required | The learner's true knowledge state |
| `params` | `BLIMParameters` | required | BLIM error parameters |
| `items` | `Sequence[str] \| None` | `None` | Items to simulate (all if None) |
| `rng` | `np.random.Generator \| None` | `None` | Random number generator |

---

## Complete Example

```python
from kst_core import (
    parse_file,
    AdaptiveAssessment,
    BLIMParameters,
    simulate_responses,
)
import numpy as np

# 1. Parse course definition
course = parse_file("examples/intro-pandas.kst.yaml")

# 2. Set up BLIM parameters
params = BLIMParameters.uniform(course.domain, beta=0.1, eta=0.1)

# 3. Define a "true" learner state
true_state = next(s for s in course.states if len(s) == 4)

# 4. Run adaptive assessment
session = AdaptiveAssessment.start(course.domain, course.states, params)

def respond(item_id: str) -> bool:
    """Simulate a learner responding based on their true state."""
    rng = np.random.default_rng()
    return bool(rng.random() < params.p_correct(item_id, true_state))

result = session.run_adaptive(respond, entropy_threshold=0.5)

print(f"Questions asked: {len(result.asked)}")
print(f"Estimated state: {sorted(result.current_estimate.item_ids)}")
print(f"Final entropy: {result.current_entropy:.3f}")
```

### Batch (Non-Adaptive) Assessment

```python
session = AdaptiveAssessment.start(course.domain, course.states, params)

# Use simulate_responses for a complete response set
responses = simulate_responses(true_state, params, rng=np.random.default_rng(42))
result = session.run(responses)

print(f"MAP estimate: {sorted(result.current_estimate.item_ids)}")
print(f"P(true state): {result.belief.probability_of(true_state):.4f}")
```

## References

- Falmagne, J.-C. & Doignon, J.-P. (2011). *Learning Spaces*, Ch. 12.
- Doignon, J.-P. & Falmagne, J.-C. (1999). *Knowledge Spaces*, Ch. 7.
