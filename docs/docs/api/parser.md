---
sidebar_position: 5
title: "Parser Module"
---

# Parser Module (`kst_core.parser`)

The parser module provides declarative course definition via `.kst.yaml` files. It parses YAML into validated Pydantic schemas and derives the full KST structure pipeline automatically.

## Pipeline

$$
\texttt{.kst.yaml} \xrightarrow{\text{parse}} \texttt{CourseSchema} \xrightarrow{\text{build}} \texttt{Domain} + \texttt{PrerequisiteGraph} \xrightarrow{\text{Birkhoff}} \texttt{KnowledgeSpace}
$$

## YAML Schema

```yaml
domain:
  name: "Course Name"               # required
  description: "Optional text"      # optional
  items:                             # required, non-empty
    - id: "item_id"                  # required, unique
      label: "Human-readable label"  # optional

prerequisites:                       # optional section
  edges:                             # list of [source, target] pairs
    - ["prereq_id", "dependent_id"]
```

### Validation Rules

| Rule | Description |
|------|-------------|
| Non-empty domain | At least one item required |
| Unique IDs | No duplicate item IDs |
| Valid edges | Both endpoints must reference existing item IDs |
| Acyclicity | The prerequisite graph must be a DAG |

## `parse_yaml(content: str) -> CourseDefinition`

Parse a YAML string into a fully validated `CourseDefinition`.

```python
from kst_core import parse_yaml

yaml_str = """
domain:
  name: "Arithmetic"
  items:
    - id: "add"
      label: "Addition"
    - id: "sub"
      label: "Subtraction"
    - id: "mul"
      label: "Multiplication"
prerequisites:
  edges:
    - ["add", "sub"]
    - ["sub", "mul"]
"""

course = parse_yaml(yaml_str)
```

**Raises:**
- `ValueError` if the YAML content is not a valid mapping or fails schema validation
- `yaml.YAMLError` if the YAML syntax is malformed

## `parse_file(path: str | Path) -> CourseDefinition`

Parse a `.kst.yaml` file from disk.

```python
from kst_core import parse_file

course = parse_file("examples/intro-pandas.kst.yaml")
print(f"{course.name}: {len(course.domain)} items")
```

**Raises:**
- `FileNotFoundError` if the file does not exist
- `ValueError` if the content is invalid

## `CourseDefinition`

A fully parsed and validated course. Contains the raw schema and all derived KST structures.

```python
course = parse_file("examples/intro-pandas.kst.yaml")

# Metadata
course.name            # "Introduction to Pandas"
course.description     # "Foundational skills for..."

# Derived structures
course.domain              # Domain with all items
course.prerequisite_graph  # PrerequisiteGraph (DAG)
course.surmise_relation    # SurmiseRelation (transitive closure)
course.states              # frozenset[KnowledgeState] (all downsets)
```

### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `to_knowledge_space()` | `KnowledgeSpace` | Validated knowledge space from derived states |
| `to_learning_space()` | `LearningSpace` | Validated learning space (always valid for DAG-derived states) |

### Why DAG-derived states always form a Learning Space

States generated via Birkhoff's theorem (downsets of a partial order) are guaranteed to satisfy:
- **S1, S2**: $\emptyset$ and $Q$ are always downsets
- **S3 (union closure)**: the union of two downsets is a downset
- **Intersection closure**: the intersection of two downsets is a downset
- **Accessibility**: every non-empty downset $D$ contains a maximal element $q$ such that $D \setminus \{q\}$ is also a downset

This means `to_learning_space()` will always succeed for courses parsed from valid `.kst.yaml` files.

## Schema Classes

### `ItemSchema`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `str` | Yes | Unique item identifier |
| `label` | `str` | No | Human-readable label |

### `DomainSchema`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `str` | Yes | Course name |
| `description` | `str` | No | Course description |
| `items` | `tuple[ItemSchema, ...]` | Yes | Non-empty list of items with unique IDs |

### `PrerequisitesSchema`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `edges` | `tuple[tuple[str, str], ...]` | No | Prerequisite edges `[source, target]` |

### `CourseSchema`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `domain` | `DomainSchema` | Yes | Domain definition |
| `prerequisites` | `PrerequisitesSchema` | No | Prerequisite edges (defaults to empty) |

## Complete Example

```python
from kst_core import parse_file, validate_learning_space

# Parse course
course = parse_file("examples/intro-pandas.kst.yaml")

# Inspect structure
print(f"Course: {course.name}")
print(f"Items: {len(course.domain)}")
print(f"States: {len(course.states)}")
print(f"Critical path: {course.prerequisite_graph.critical_path()}")

# Build learning space and explore paths
ls = course.to_learning_space()
paths = ls.learning_paths()
print(f"Learning paths: {len(paths)}")

for i, path in enumerate(paths[:3]):
    print(f"  Path {i+1}: {' → '.join(item.id for item in path)}")

# Validate formally
report = validate_learning_space(course.domain, course.states)
print(f"Validation: {report.summary}")
```

Output:
```
Course: Introduction to Pandas
Items: 8
States: 15
Critical path: ['import', 'series', 'indexing', 'filtering', 'pivot']
Learning paths: 16
  Path 1: import → dataframe → series → indexing → filtering → groupby → merge → pivot
  Path 2: import → dataframe → series → indexing → filtering → merge → groupby → pivot
  Path 3: import → dataframe → series → indexing → groupby → filtering → merge → pivot
Validation: 6/6 checks passed
```
