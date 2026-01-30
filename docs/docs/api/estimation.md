---
sidebar_position: 7
title: "Estimation Module"
---

# Estimation Module (`kst_core.estimation`)

The estimation module implements **Maximum Likelihood Estimation (MLE)** for the Basic Local Independence Model using the **Expectation-Maximization (EM) algorithm**. Given observed response patterns, it estimates the state distribution and error parameters.

## Mathematical Foundation

The EM algorithm iterates two steps:

**E-step**: Compute the posterior probability that learner $j$ is in state $K$:

$$
w_{jK} = P(K \mid R_j, \theta^{(t)}) = \frac{\pi^{(t)}(K) \cdot P(R_j \mid K, \theta^{(t)})}{\sum_{K'} \pi^{(t)}(K') \cdot P(R_j \mid K', \theta^{(t)})}
$$

**M-step**: Update parameter estimates:

$$
\pi^{(t+1)}(K) = \frac{1}{N} \sum_{j=1}^{N} w_{jK}
$$

$$
\beta_q^{(t+1)} = \frac{\sum_j \sum_{K: q \in K} w_{jK} \cdot \mathbf{1}[q \notin R_j]}{\sum_j \sum_{K: q \in K} w_{jK}}, \qquad
\eta_q^{(t+1)} = \frac{\sum_j \sum_{K: q \notin K} w_{jK} \cdot \mathbf{1}[q \in R_j]}{\sum_j \sum_{K: q \notin K} w_{jK}}
$$

See [Knowledge Assessment](/docs/theory/knowledge-assessment) for the full theoretical treatment.

---

## `ResponseData`

Collection of observed response patterns for parameter estimation.

```python
from kst_core import ResponseData, Domain, Item

domain = Domain(items=frozenset({Item(id="a"), Item(id="b"), Item(id="c")}))

data = ResponseData(
    domain=domain,
    patterns=(
        {"a": True, "b": False, "c": True},
        {"a": True, "b": True, "c": False},
        {"a": False, "b": False, "c": False},
    ),
)
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `domain` | `Domain` | The knowledge domain |
| `patterns` | `tuple[dict[str, bool], ...]` | Response patterns (item_id -> correct) |

**Validation:**
- At least one pattern required
- Each pattern's keys must exactly match domain item IDs

---

## `em_fit`

Fit BLIM parameters using the EM algorithm.

```python
from kst_core import em_fit, ResponseData, Domain, Item, KnowledgeState

estimate = em_fit(
    domain=domain,
    states=states,
    data=response_data,
    max_iterations=1000,
    tolerance=1e-6,
    initial_beta=0.1,
    initial_eta=0.1,
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `domain` | `Domain` | required | Knowledge domain $Q$ |
| `states` | `frozenset[KnowledgeState]` | required | Knowledge states $\mathcal{K}$ |
| `data` | `ResponseData` | required | Observed response patterns |
| `max_iterations` | `int` | `1000` | Maximum EM iterations |
| `tolerance` | `float` | `1e-6` | Convergence threshold on $\Delta\ell$ |
| `initial_beta` | `float` | `0.1` | Initial slip probability |
| `initial_eta` | `float` | `0.1` | Initial guess probability |

**Returns:** `BLIMEstimate`

### Implementation Details

The E-step uses a vectorized numpy computation for efficiency:

$$
\log P(R_j \mid K_k) = \sum_q \left[\log P_q^{\text{out}} + m_{kq} \cdot (\log P_q^{\text{in}} - \log P_q^{\text{out}})\right]
$$

where $m_{kq} = \mathbf{1}[q \in K_k]$ is the membership matrix. This reduces to a single matrix multiplication per E-step.

Numerical stability is ensured via log-sum-exp normalization for posterior computation.

---

## `BLIMEstimate`

Result of EM parameter estimation. Frozen Pydantic model.

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `params` | `BLIMParameters` | Fitted BLIM parameters ($\hat\beta$, $\hat\eta$) |
| `belief` | `BeliefState` | Estimated state distribution $\hat\pi(K)$ |
| `log_likelihood` | `float` | Final log-likelihood $\ell(\hat\theta)$ |
| `iterations` | `int` | Number of EM iterations performed |
| `converged` | `bool` | Whether the algorithm converged within tolerance |

---

## `goodness_of_fit`

Compute the $G^2$ (likelihood ratio) goodness-of-fit statistic.

```python
from kst_core import goodness_of_fit

gof = goodness_of_fit(data, estimate, states)
print(f"G² = {gof.g_squared:.2f}, df = {gof.degrees_of_freedom}")
```

$$
G^2 = 2 \sum_R N_R \log \frac{N_R / N}{\hat{P}(R)}
$$

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `ResponseData` | Observed response patterns |
| `estimate` | `BLIMEstimate` | Fitted model |
| `states` | `frozenset[KnowledgeState]` | Knowledge states used |

**Returns:** `GoodnessOfFit`

---

## `GoodnessOfFit`

Goodness-of-fit statistics. Frozen Pydantic model.

| Field | Type | Description |
|-------|------|-------------|
| `g_squared` | `float` | $G^2$ statistic (lower = better fit) |
| `degrees_of_freedom` | `int` | Degrees of freedom for $\chi^2$ test |
| `n_response_patterns` | `int` | Number of unique observed patterns |
| `n_observations` | `int` | Total number of observations $N$ |

---

## Complete Example

```python
from kst_core import (
    parse_file,
    BLIMParameters,
    simulate_responses,
    ResponseData,
    em_fit,
    goodness_of_fit,
)
import numpy as np

# 1. Parse course
course = parse_file("examples/intro-pandas.kst.yaml")

# 2. Simulate response data from multiple learners
true_params = BLIMParameters.uniform(course.domain, beta=0.15, eta=0.10)
rng = np.random.default_rng(42)

patterns = []
for state in sorted(course.states, key=len)[:5]:
    for _ in range(100):
        patterns.append(simulate_responses(state, true_params, rng=rng))

data = ResponseData(domain=course.domain, patterns=tuple(patterns))

# 3. Estimate parameters via EM
estimate = em_fit(course.domain, course.states, data)

print(f"Converged: {estimate.converged} ({estimate.iterations} iterations)")
print(f"Log-likelihood: {estimate.log_likelihood:.1f}")

# 4. Inspect fitted parameters
for item_id in sorted(course.domain.item_ids):
    b = estimate.params.beta[item_id]
    e = estimate.params.eta[item_id]
    print(f"  {item_id}: beta={b:.3f}, eta={e:.3f}")

# 5. Assess fit quality
gof = goodness_of_fit(data, estimate, course.states)
print(f"G² = {gof.g_squared:.2f}, df = {gof.degrees_of_freedom}")
```

## References

- Falmagne, J.-C. & Doignon, J.-P. (2011). *Learning Spaces*, Ch. 12.
- Dempster, A. P., Laird, N. M., & Rubin, D. B. (1977). Maximum likelihood from incomplete data via the EM algorithm. *JRSS-B*, 39(1), 1-38.
