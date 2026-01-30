"""Validation module — formal verification of KST structures.

Provides validators that check the mathematical properties
of knowledge spaces and learning spaces, returning detailed
results with bibliographic references.

References:
    Doignon, J.-P. & Falmagne, J.-Cl. (1999). Knowledge Spaces.
    Falmagne, J.-Cl. & Doignon, J.-P. (2011). Learning Spaces.
"""

from __future__ import annotations

from itertools import combinations

from pydantic import BaseModel

from kst_core.domain import Domain, KnowledgeState


class ValidationResult(BaseModel, frozen=True):
    """A single validation check result."""

    property_name: str
    passed: bool
    message: str
    reference: str = ""


class ValidationReport(BaseModel, frozen=True):
    """Aggregated report of multiple validation results."""

    results: tuple[ValidationResult, ...]

    @property
    def is_valid(self) -> bool:
        return all(r.passed for r in self.results)

    @property
    def failures(self) -> tuple[ValidationResult, ...]:
        return tuple(r for r in self.results if not r.passed)

    @property
    def summary(self) -> str:
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        return f"{passed}/{total} checks passed"


def validate_knowledge_space(
    domain: Domain,
    states: frozenset[KnowledgeState],
) -> ValidationReport:
    """Validate that (Q, K) satisfies the knowledge space axioms.

    Checks:
    1. Non-emptiness: K ≠ ∅
    2. S1 — Contains empty set: ∅ ∈ K
    3. S2 — Contains full domain: Q ∈ K
    4. S3 — Closure under union: K₁, K₂ ∈ K ⟹ K₁ ∪ K₂ ∈ K
    5. States are subsets of Q
    """
    results: list[ValidationResult] = []

    results.append(
        ValidationResult(
            property_name="Non-emptiness",
            passed=len(states) > 0,
            message="K is non-empty" if states else "K is empty",
            reference="Doignon & Falmagne (1999), Definition 1.1.1",
        )
    )

    empty = KnowledgeState()
    results.append(
        ValidationResult(
            property_name="S1: Empty set",
            passed=empty in states,
            message="∅ ∈ K" if empty in states else "∅ ∉ K — axiom S1 violated",
            reference="Doignon & Falmagne (1999), Definition 1.1.1 (i)",
        )
    )

    full = domain.full_state
    results.append(
        ValidationResult(
            property_name="S2: Full domain",
            passed=full in states,
            message="Q ∈ K" if full in states else "Q ∉ K — axiom S2 violated",
            reference="Doignon & Falmagne (1999), Definition 1.1.1 (ii)",
        )
    )

    all_subsets = all(domain.contains_state(s) for s in states)
    results.append(
        ValidationResult(
            property_name="States ⊆ Q",
            passed=all_subsets,
            message=(
                "All states are subsets of Q"
                if all_subsets
                else "Some states contain items not in Q"
            ),
            reference="Doignon & Falmagne (1999), Definition 1.1.1",
        )
    )

    union_closed = True
    violation_msg = ""
    for s1, s2 in combinations(states, 2):
        union = s1.union(s2)
        if union not in states:
            union_closed = False
            violation_msg = f"{s1} ∪ {s2} = {union} ∉ K"
            break

    results.append(
        ValidationResult(
            property_name="S3: Closure under union",
            passed=union_closed,
            message=(
                "K is closed under ∪" if union_closed else f"Not closed under ∪: {violation_msg}"
            ),
            reference="Doignon & Falmagne (1999), Definition 1.1.1 (iii)",
        )
    )

    return ValidationReport(results=tuple(results))


def validate_learning_space(
    domain: Domain,
    states: frozenset[KnowledgeState],
) -> ValidationReport:
    """Validate that (Q, K) satisfies learning space axioms.

    Checks all knowledge space axioms plus:
    - Accessibility: for every non-empty K ∈ K, ∃q ∈ K : K \\ {q} ∈ K
    """
    ks_report = validate_knowledge_space(domain, states)
    results = list(ks_report.results)

    accessible = True
    violation_msg = ""
    empty = KnowledgeState()

    for state in states:
        if state == empty:
            continue
        found = False
        for item in state:
            reduced = KnowledgeState(items=state.items - {item})
            if reduced in states:
                found = True
                break
        if not found:
            accessible = False
            violation_msg = f"State {state} has no removable item"
            break

    results.append(
        ValidationResult(
            property_name="Accessibility (antimatroid)",
            passed=accessible,
            message=(
                "All non-empty states are accessible"
                if accessible
                else f"Not accessible: {violation_msg}"
            ),
            reference="Falmagne & Doignon (2011), Definition 2.1.1",
        )
    )

    return ValidationReport(results=tuple(results))
