---
id: optimization
title: Optimization
sidebar_label: Optimization
---

# Optimization API Reference

Four optimization algorithms for Knowledge Space Theory structures.

## Functions

### `calibrate_parameters(domain, states, data, *, restarts, max_iterations, tolerance)`

Multi-restart EM calibration with identifiability check (Heller & Wickelmaier, 2013).

```python
from kst_core import calibrate_parameters, ResponseData

result = calibrate_parameters(domain, states, data, restarts=5)
print(result.params.beta)
print(result.identifiable)
```

Returns `CalibrationResult` with best-fit parameters across restarts.

### `optimal_teaching_sequence(space, rates?, start?)`

MDP value iteration for optimal teaching:

$$V^*(Q) = 0$$
$$V^*(K) = 1 + \min_{q \in OF(K)} V^*(K \cup \{q\})$$

```python
from kst_core import optimal_teaching_sequence

plan = optimal_teaching_sequence(learning_space)
for step in plan.steps:
    print(f"Teach {step.item_id}")
```

Returns `TeachingPlan` with the optimal sequence of items.

### `estimate_item_difficulty(domain, graph, data?, params?)`

Combines up to three difficulty sources:

1. **Structural**: DAG depth (number of transitive prerequisites)
2. **Empirical**: Error rate from response data
3. **BLIM**: $\beta_q + (1 - \eta_q)$ from calibrated parameters

```python
from kst_core import estimate_item_difficulty

report = estimate_item_difficulty(domain, prerequisite_graph)
for item in report.items:
    print(f"{item.item_id}: difficulty={item.combined_difficulty:.3f}")
```

### `tune_learning_rates(space, data, *, max_iterations, tolerance)`

MLE on Markov chain log-likelihood:

$$\log L(\lambda) = \sum_t \sum_{\text{transitions}} \log P(K_{t+1} | K_t, \lambda)$$

where $P(K \to K \cup \{q\}) = \lambda_q / \sum_{q' \in OF(K)} \lambda_{q'}$.

```python
from kst_core import tune_learning_rates, TrajectoryData

data = TrajectoryData(domain=domain, trajectories=trajectories)
result = tune_learning_rates(space, data)
print(result.rates.rates)
```

## Types

| Type | Description |
|------|-------------|
| `CalibrationResult` | Multi-restart EM result with identifiability flag |
| `ItemCalibration` | Per-item $\beta_q$, $\eta_q$ estimates |
| `TeachingPlan` | Optimal teaching sequence |
| `TeachingStep` | Single step: item, from/to states, expected remaining |
| `ItemDifficulty` | Per-item difficulty from multiple sources |
| `DifficultyReport` | All items with method description |
| `TrajectoryData` | Observed learning trajectories |
| `TunedRates` | Fitted learning rates with convergence info |

## CLI

```bash
kst optimize examples/intro-pandas.kst.yaml --mode difficulty
kst optimize examples/intro-pandas.kst.yaml --mode teach
kst optimize examples/intro-pandas.kst.yaml --mode calibrate --data responses.csv
kst optimize examples/intro-pandas.kst.yaml --mode rates --data trajectories.csv
```
