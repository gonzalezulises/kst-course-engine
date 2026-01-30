---
id: interactive
title: Interactive Assessment
sidebar_label: Interactive Assessment
---

# Interactive Assessment API

The interactive assessment module provides stateful assessment sessions that track question-by-question progress and produce detailed summaries.

## Types

### `AssessmentStep`

A frozen Pydantic model recording one Q&A interaction:

| Field | Type | Description |
|-------|------|-------------|
| `item_id` | `str` | Item that was asked |
| `correct` | `bool` | Whether the response was correct |
| `entropy_before` | `float` | Shannon entropy $H(\pi)$ before update |
| `entropy_after` | `float` | Shannon entropy after Bayesian update |
| `estimate_ids` | `frozenset[str]` | MAP state estimate item IDs |

### `AssessmentSummary`

Final report after completing an assessment:

| Field | Type | Description |
|-------|------|-------------|
| `total_questions` | `int` | Number of questions asked |
| `steps` | `tuple[AssessmentStep, ...]` | All Q&A records |
| `final_state_ids` | `frozenset[str]` | Estimated knowledge state |
| `confidence` | `float` | $1 - H(\pi) / H_{\max}$ |
| `mastered` | `frozenset[str]` | Items in estimated state |
| `not_mastered` | `frozenset[str]` | Items not in estimated state |

### `SessionStore`

In-memory session storage for the REST API:

```python
store = SessionStore()
session_id, first_item = store.create(course, beta=0.1, eta=0.1)
step, next_item, is_complete = store.respond(session_id, correct=True)
summary = store.summary(session_id)
```

## Terminal Assessment

```python
from kst_core import run_terminal_assessment, parse_file

course = parse_file("examples/intro-pandas.kst.yaml")
summary = run_terminal_assessment(course, beta=0.1, eta=0.1)
```

This runs an interactive loop reading `y`/`n` from stdin.

## CLI

```bash
kst assess examples/intro-pandas.kst.yaml --beta 0.1 --eta 0.1 --threshold 0.1
```

## Confidence Metric

Confidence is defined as the normalized entropy reduction:

$$
\text{confidence} = 1 - \frac{H(\pi)}{H_{\max}}
$$

where $H_{\max} = \log_2 |K|$ is the entropy of a uniform distribution over all states.
