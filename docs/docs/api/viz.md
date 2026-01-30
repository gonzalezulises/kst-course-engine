---
sidebar_position: 9
title: "Visualization (viz)"
---

# Visualization Module (`kst_core.viz`)

The visualization module generates **Graphviz DOT**, **Mermaid**, and **JSON** representations of KST structures. All outputs are plain strings with no external rendering dependencies -- they can be piped into Graphviz (`dot`), embedded in Markdown (Mermaid), or parsed as structured data (JSON).

## Export Formats

| Format | Function(s) | Use Case |
|--------|-------------|----------|
| **Graphviz DOT** | `hasse_dot`, `prerequisites_dot`, `trajectory_dot` | High-quality rendered diagrams (`dot -Tpng`) |
| **Mermaid** | `hasse_mermaid` | Embeddable Markdown diagrams (GitHub, Docusaurus) |
| **JSON** | `course_json` | Machine-readable course export |

## Mathematical Background

The primary visualization is the **Hasse diagram** of a knowledge space $\mathcal{K}$. Rather than drawing an edge for every subset relation $L \subset K$, the Hasse diagram displays only the **covering relation**:

$$
K \text{ covers } L \iff L \subset K,\; |K| = |L| + 1,\; \text{and both } K, L \in \mathcal{K}
$$

Each covering edge corresponds to the acquisition of exactly one item $q = K \setminus L$. The resulting diagram is a compact representation of all valid single-step transitions in the space, arranged bottom-up by state cardinality (Sugiyama-style layered layout).

**Reference**: Doignon, J.-P. & Falmagne, J.-C. (1999). *Knowledge Spaces*, Ch. 2.

---

## `hasse_dot(space)`

Generate Graphviz DOT source for the Hasse diagram of a knowledge space.

Nodes are knowledge states (rounded boxes), edges represent the covering relation, and edge labels show the item acquired (`+item`). States are grouped by cardinality using `rank=same` for bottom-to-top layout.

```python
from kst_core import parse_file
from kst_core.viz import hasse_dot

course = parse_file("examples/intro-pandas.kst.yaml")
space = course.to_learning_space()

dot_source = hasse_dot(space)
print(dot_source)
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `space` | `KnowledgeSpace \| LearningSpace` | The knowledge or learning space to visualize |

**Returns:** `str` -- DOT source string.

Render with Graphviz:

```bash
kst export examples/intro-pandas.kst.yaml --format dot > hasse.dot
dot -Tpng hasse.dot -o hasse.png
```

---

## `prerequisites_dot(graph)`

Generate Graphviz DOT source for a prerequisite graph (DAG). Nodes are domain items, edges represent prerequisite relations (left-to-right layout).

```python
from kst_core import parse_file
from kst_core.viz import prerequisites_dot

course = parse_file("examples/intro-pandas.kst.yaml")
dot_source = prerequisites_dot(course.prerequisite_graph)
print(dot_source)
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `graph` | `PrerequisiteGraph` | The prerequisite graph (DAG) to visualize |

**Returns:** `str` -- DOT source string.

---

## `trajectory_dot(trajectory, highlight_items=True)`

Generate Graphviz DOT source for a learning trajectory. Shows the sequence of states visited as a left-to-right chain, with edges labeled by the item acquired at each step. The final state is rendered in bold.

```python
from kst_core import parse_file, LearningRate, LearningModel
from kst_core.viz import trajectory_dot
import numpy as np

course = parse_file("examples/intro-pandas.kst.yaml")
space = course.to_learning_space()
rates = LearningRate.uniform(course.domain)
model = LearningModel(space=space, rates=rates)

traj = model.simulate_trajectory(rng=np.random.default_rng(42))
dot_source = trajectory_dot(traj)
print(dot_source)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `trajectory` | `tuple[KnowledgeState, ...]` | -- | Sequence of knowledge states |
| `highlight_items` | `bool` | `True` | Label edges with the acquired item |

**Returns:** `str` -- DOT source string.

---

## `hasse_mermaid(space)`

Generate a Mermaid `graph BT` flowchart for the Hasse diagram. Suitable for embedding directly in Markdown documentation (GitHub, Docusaurus, Obsidian).

```python
from kst_core import parse_file
from kst_core.viz import hasse_mermaid

course = parse_file("examples/intro-pandas.kst.yaml")
space = course.to_learning_space()

mermaid_source = hasse_mermaid(space)
print(mermaid_source)
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `space` | `KnowledgeSpace \| LearningSpace` | The knowledge or learning space to visualize |

**Returns:** `str` -- Mermaid source string.

Embed in Markdown:

````markdown
```mermaid
graph BT
  s_empty[∅]
  s_a[{a}]
  s_a_b[{a, b}]
  s_a_b_c[{a, b, c}]
  s_empty -->|+a| s_a
  s_a -->|+b| s_a_b
  s_a_b -->|+c| s_a_b_c
```
````

---

## `course_json(course)`

Export a `CourseDefinition` as a structured JSON string. Includes domain items (with labels), prerequisite edges, and all knowledge states.

```python
from kst_core import parse_file
from kst_core.viz import course_json

course = parse_file("examples/intro-pandas.kst.yaml")
print(course_json(course))
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `course` | `CourseDefinition` | A parsed course definition |

**Returns:** `str` -- JSON string with the following structure:

```json
{
  "name": "Course Name",
  "description": "Course description",
  "domain": {
    "items": [{"id": "a", "label": "Item A"}, ...],
    "count": 3
  },
  "prerequisites": {
    "edges": [["a", "b"], ...],
    "count": 1
  },
  "states": {
    "sets": [[], ["a"], ["a", "b"], ["a", "b", "c"]],
    "count": 4
  }
}
```

---

## Internal Helpers

These are not part of the public API but document the underlying algorithms.

### `_state_label(state)`

Returns a human-readable label for a knowledge state: $\emptyset$ for the empty set, or $\{a, b, \ldots\}$ with sorted item IDs.

### `_state_id(state)`

Returns a sanitized node identifier for DOT/Mermaid graphs: `s_empty` for $\emptyset$, or `s_a_b` for $\{a, b\}$ (underscore-joined sorted IDs).

### `_covering_edges(states)`

Computes the covering relation for a set of knowledge states. Groups states by cardinality and checks all pairs where $|K| = |L| + 1$ and $L \subset K$. Returns a list of `(lower, upper)` pairs.

The algorithm runs in $O\bigl(\sum_i |\mathcal{K}_i| \cdot |\mathcal{K}_{i+1}|\bigr)$ where $\mathcal{K}_i$ denotes the set of states with cardinality $i$.

---

## CLI Usage

The `kst export` command provides command-line access to all visualization functions:

```bash
# Hasse diagram as Graphviz DOT (default)
kst export examples/intro-pandas.kst.yaml

# Hasse diagram as Mermaid
kst export examples/intro-pandas.kst.yaml --format mermaid

# Prerequisite graph as DOT
kst export examples/intro-pandas.kst.yaml --format dot --type prerequisites

# Full course as JSON
kst export examples/intro-pandas.kst.yaml --format json
```

**Options:**

| Flag | Choices | Default | Description |
|------|---------|---------|-------------|
| `--format` | `dot`, `json`, `mermaid` | `dot` | Output format |
| `--type` | `hasse`, `prerequisites` | `hasse` | Diagram type (ignored for JSON) |

Pipe DOT output directly to Graphviz for rendering:

```bash
kst export course.kst.yaml --format dot | dot -Tsvg > hasse.svg
kst export course.kst.yaml --format dot --type prerequisites | dot -Tpng > prereqs.png
```

:::note
Mermaid format is currently supported only for Hasse diagrams, not prerequisite graphs.
:::

---

## Complete Example

```python
from kst_core import (
    Domain, Item, KnowledgeState, LearningSpace,
    parse_file, LearningRate, LearningModel,
)
from kst_core.viz import (
    hasse_dot, hasse_mermaid, prerequisites_dot,
    trajectory_dot, course_json,
)
import numpy as np

# --- From a course file ---
course = parse_file("examples/intro-pandas.kst.yaml")
space = course.to_learning_space()

# Graphviz DOT for the Hasse diagram
with open("hasse.dot", "w") as f:
    f.write(hasse_dot(space))

# Mermaid for documentation
with open("hasse.mmd", "w") as f:
    f.write(hasse_mermaid(space))

# Prerequisite graph
with open("prereqs.dot", "w") as f:
    f.write(prerequisites_dot(course.prerequisite_graph))

# JSON export
with open("course.json", "w") as f:
    f.write(course_json(course))

# --- Trajectory visualization ---
rates = LearningRate.uniform(course.domain)
model = LearningModel(space=space, rates=rates)
traj = model.simulate_trajectory(rng=np.random.default_rng(42))

with open("trajectory.dot", "w") as f:
    f.write(trajectory_dot(traj))

# Render all DOT files:
# dot -Tpng hasse.dot -o hasse.png
# dot -Tpng prereqs.dot -o prereqs.png
# dot -Tpng trajectory.dot -o trajectory.png
```

## References

- Doignon, J.-P. & Falmagne, J.-C. (1999). *Knowledge Spaces*, Ch. 2 (Hasse diagrams, covering relation).
- Falmagne, J.-C. & Doignon, J.-P. (2011). *Learning Spaces*, Ch. 1.
