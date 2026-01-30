---
sidebar_position: 1
title: "Getting Started"
---

# Getting Started

This guide covers how to set up a development environment for `kst_core`.

## Prerequisites

- **Python 3.12+** -- The project uses modern Python features including type parameter syntax and `frozenset` generics.
- **uv** -- A fast Python package manager and virtual environment tool. Install it via:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/kst-course-engine.git
cd kst-course-engine
```

### 2. Create a Virtual Environment

```bash
uv venv
```

This creates a `.venv` directory with a Python 3.12+ interpreter.

### 3. Install Dependencies

```bash
uv pip install -e ".[dev]"
```

This installs the package in editable mode along with all development dependencies:

- **pytest** -- Test runner
- **hypothesis** -- Property-based testing
- **mypy** -- Static type checker
- **ruff** -- Linter and formatter
- **coverage** -- Code coverage reporting

### 4. Verify the Installation

```bash
uv run python -c "from kst_core import Item; print(Item(id='test'))"
```

You should see: `id='test' label=''`

## Running Tests

### Full Test Suite

```bash
uv run pytest
```

### With Coverage

```bash
uv run pytest --cov=kst_core --cov-report=term-missing
```

The project requires **100% code coverage**. Any PR that reduces coverage will fail CI.

### Verbose Output

```bash
uv run pytest -v
```

### Run Specific Tests

```bash
# Run a specific test file
uv run pytest tests/test_domain.py

# Run a specific test function
uv run pytest tests/test_domain.py::test_item_equality

# Run tests matching a keyword
uv run pytest -k "knowledge_space"
```

### Property-Based Tests

Property-based tests using Hypothesis may take longer on the first run as Hypothesis builds its example database. Subsequent runs use cached examples for faster execution.

```bash
# Run only property-based tests
uv run pytest -k "property" -v

# Increase Hypothesis examples for thorough testing
uv run pytest --hypothesis-seed=0 -v
```

## Linting

### Ruff (Linting and Formatting)

```bash
# Check for lint errors
uv run ruff check .

# Auto-fix lint errors
uv run ruff check --fix .

# Format code
uv run ruff format .

# Check formatting without modifying files
uv run ruff format --check .
```

### mypy (Type Checking)

```bash
uv run mypy src/kst_core
```

The project uses **mypy strict mode**. All functions must have complete type annotations, and no `Any` types or `# type: ignore` comments are permitted.

## Project Structure

```
kst-course-engine/
├── src/
│   └── kst_core/
│       ├── __init__.py          # Public API exports
│       ├── domain.py            # Item, KnowledgeState, Domain
│       ├── space.py             # KnowledgeSpace, LearningSpace
│       ├── prerequisites.py     # SurmiseRelation, PrerequisiteGraph
│       ├── validation.py        # ValidationResult, ValidationReport
│       └── testing/
│           ├── __init__.py
│           └── strategies.py    # Hypothesis strategies for KST types
├── tests/
│   ├── test_domain.py           # Tests for domain module
│   ├── test_space.py            # Tests for space module
│   ├── test_prerequisites.py    # Tests for prerequisites module
│   ├── test_validation.py       # Tests for validation module
│   └── test_properties.py       # Property-based tests
├── docs/                        # Docusaurus documentation site
│   ├── docs/
│   │   ├── api/                 # API reference
│   │   ├── research/            # Research documentation
│   │   └── development/         # Development guides
│   ├── docusaurus.config.ts
│   └── sidebars.ts
├── pyproject.toml               # Project configuration
└── README.md
```

### Key Directories

| Directory | Contents |
|-----------|----------|
| `src/kst_core/` | Core library source code |
| `src/kst_core/testing/` | Hypothesis strategies for property-based testing |
| `tests/` | Test suite (pytest + Hypothesis) |
| `docs/` | Docusaurus documentation site |

### Key Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Project metadata, dependencies, tool configuration |
| `domain.py` | Foundational types: `Item`, `KnowledgeState`, `Domain` |
| `space.py` | Knowledge structures: `KnowledgeSpace`, `LearningSpace` |
| `prerequisites.py` | Prerequisite structures: `SurmiseRelation`, `PrerequisiteGraph` |
| `validation.py` | Validation framework: `ValidationResult`, `ValidationReport` |

## Next Steps

- Read the [API documentation](../api/domain.md) to understand the core types.
- Review the [Testing Strategy](./testing-strategy.md) to understand the test approach.
- See [Contributing](./contributing.md) for guidelines on submitting changes.
