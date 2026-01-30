---
sidebar_position: 4
title: "CLI Reference"
---

# CLI Reference

The `kst` command-line tool provides direct access to all KST Course Engine capabilities.

## Installation

```bash
git clone https://github.com/gonzalezulises/kst-course-engine.git
cd kst-course-engine
uv venv && uv pip install -e ".[dev]"
```

## Commands

### `kst info`

Display course overview including items, states, learning paths, and critical path.

```bash
$ kst info examples/intro-pandas.kst.yaml
Course: Introduction to Pandas
Description: Foundational skills for data manipulation with pandas
Items: 8
States: 15
Prerequisites: 10
Critical path: import -> series -> indexing -> filtering -> pivot
Critical path length: 5
Learning paths: 16
```

### `kst validate`

Run formal validation of the knowledge/learning space axioms.

```bash
$ kst validate examples/intro-pandas.kst.yaml
Validation: 6/6 checks passed
  [PASS] Non-emptiness: K is non-empty
  [PASS] S1: Empty set: ∅ ∈ K
  [PASS] S2: Full domain: Q ∈ K
  [PASS] States ⊆ Q: All states are subsets of Q
  [PASS] S3: Closure under union: K is closed under ∪
  [PASS] Accessibility (antimatroid): All non-empty states are accessible
```

Returns exit code 0 if all checks pass, 1 if any fail.

### `kst paths`

Enumerate all learning paths from $\emptyset$ to $Q$.

```bash
$ kst paths examples/intro-pandas.kst.yaml --max 3
Total learning paths: 16

  1. import -> dataframe -> series -> indexing -> filtering -> groupby -> merge -> pivot
  2. import -> dataframe -> series -> indexing -> filtering -> merge -> groupby -> pivot
  3. import -> dataframe -> series -> indexing -> groupby -> filtering -> merge -> pivot
  ... and 13 more (use --max to show more)
```

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--max N` | 10 | Maximum paths to display |

### `kst simulate`

Simulate a cohort of learners through adaptive assessment and learning trajectories.

```bash
$ kst simulate examples/intro-pandas.kst.yaml --learners 100 --seed 42
Simulating 100 learners on 'Introduction to Pandas'
Parameters: beta=0.1, eta=0.1, seed=42

=== Assessment Results ===
Accuracy: 70/100 (70.0%)
Avg questions: 8.0

=== Learning Trajectories ===
Expected steps to mastery: 8.0
Simulated avg steps: 8.0 (std=0.0)
```

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--learners N` | 100 | Number of learners to simulate |
| `--beta F` | 0.1 | BLIM slip probability $\beta$ |
| `--eta F` | 0.1 | BLIM guess probability $\eta$ |
| `--seed N` | None | Random seed for reproducibility |

## Error Handling

All commands return:
- **Exit code 0** on success
- **Exit code 1** on error (file not found, invalid YAML, validation failure)

Errors are printed to stderr:

```bash
$ kst info nonexistent.yaml
Error: [Errno 2] No such file or directory: 'nonexistent.yaml'
```
