---
id: examples
title: Examples
sidebar_label: Examples
---

# Example Files

The `examples/` directory contains course definitions and scripts demonstrating the KST Course Engine.

## YAML Course Definitions

### `linear-chain.kst.yaml`

A 5-item total order: `a → b → c → d → e`. Only 1 learning path exists. This is the simplest non-trivial prerequisite structure.

- Items: 5
- States: 6
- Learning paths: 1

### `diamond-lattice.kst.yaml`

A 4-item diamond: `a → {b, c} → d`. Two parallel branches create 2 learning paths. This is a classic lattice-theoretic structure.

- Items: 4
- States: 6
- Learning paths: 2

### `large-domain.kst.yaml`

A 12-item "Data Science Foundations" course with branching prerequisites covering Python, NumPy, Pandas, ML basics, and more.

- Items: 12
- States: varies
- Learning paths: many

### `intro-pandas.kst.yaml`

An 8-item Introduction to Pandas course with realistic prerequisite structure.

- Items: 8
- States: 15
- Learning paths: multiple

## Scripts

### `api_example.py`

Demonstrates REST API usage with httpx. Covers all endpoints including interactive assessment.

```bash
# Start server first
uvicorn kst_core.api:app --reload

# Then run
python examples/api_example.py
```

### `demo.ipynb`

Jupyter notebook walking through the full pipeline:
1. Parse a course definition
2. Validate the knowledge space
3. Enumerate learning paths
4. Visualize the Hasse diagram
5. Simulate adaptive assessment
6. Run learning trajectory simulations
7. Estimate item difficulty
8. Compute optimal teaching sequences

```bash
jupyter notebook examples/demo.ipynb
```
