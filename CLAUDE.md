# CLAUDE.md — Instructions for Claude Code

## Project Overview

KST Course Engine implements Knowledge Space Theory (KST) mathematical structures in Python. The project uses formal algebraic structures (knowledge spaces, learning spaces, surmise relations) with rigorous validation.

## Tech Stack

- **Python 3.12+** with Pydantic v2, NetworkX, NumPy
- **Testing**: pytest + Hypothesis (property-based testing), 100% coverage required
- **Linting**: ruff (strict), mypy (strict)
- **Docs**: Docusaurus with KaTeX for LaTeX math
- **CI/CD**: GitHub Actions, Vercel

## Key Commands

```bash
uv run pytest                          # Run tests (must be 100% coverage)
uv run ruff check kst_core/ tests/     # Lint check
uv run ruff format kst_core/ tests/    # Auto-format
uv run mypy kst_core/                  # Type check (strict)
cd docs && npm run build               # Build documentation
```

## Architecture

```
kst_core/
├── domain.py          # Item, KnowledgeState, Domain (foundational types)
├── space.py           # KnowledgeSpace, LearningSpace (axiom validation)
├── prerequisites.py   # SurmiseRelation, PrerequisiteGraph (DAG/quasi-order)
├── validation.py      # ValidationResult, ValidationReport, validators
└── __init__.py        # Public API exports
```

## Conventions

- All core types are **frozen Pydantic models** (immutable)
- Mathematical properties are validated on construction (fail-fast)
- Use `frozenset` for collections (hashable, immutable)
- Docstrings include mathematical notation and references
- Unicode math symbols are intentional (σ, ∪, ∩, ∅, etc.) — ruff RUF001/RUF002 are disabled
- Every validation result includes a bibliographic reference

## Testing Rules

- 100% code coverage is enforced (`--cov-fail-under=100`)
- Use Hypothesis strategies from `tests/conftest.py` for property-based tests
- Test both valid construction and invalid inputs (must raise `ValueError`)
- Algebraic properties: commutativity, associativity, identity laws

## Mathematical References

- Doignon & Falmagne (1999). *Knowledge Spaces*. Springer.
- Falmagne & Doignon (2011). *Learning Spaces*. Springer.
