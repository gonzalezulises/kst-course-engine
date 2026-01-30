"""Tests for kst_core.validation — validators for knowledge/learning spaces."""

from __future__ import annotations

import pytest

from kst_core.domain import Domain, Item, KnowledgeState
from kst_core.validation import (
    ValidationReport,
    ValidationResult,
    validate_knowledge_space,
    validate_learning_space,
)


def _state(*ids: str) -> KnowledgeState:
    return KnowledgeState(items=frozenset(Item(id=i) for i in ids))


@pytest.fixture()
def abc_domain() -> Domain:
    return Domain(items=frozenset({Item(id="a"), Item(id="b"), Item(id="c")}))


@pytest.fixture()
def ab_domain() -> Domain:
    return Domain(items=frozenset({Item(id="a"), Item(id="b")}))


class TestValidationResult:
    def test_create(self) -> None:
        vr = ValidationResult(
            property_name="Test",
            passed=True,
            message="OK",
            reference="Doignon (1999)",
        )
        assert vr.passed
        assert vr.property_name == "Test"
        assert vr.reference == "Doignon (1999)"

    def test_default_reference(self) -> None:
        vr = ValidationResult(property_name="T", passed=True, message="OK")
        assert vr.reference == ""


class TestValidationReport:
    def test_all_pass(self) -> None:
        results = (
            ValidationResult(property_name="A", passed=True, message="ok"),
            ValidationResult(property_name="B", passed=True, message="ok"),
        )
        report = ValidationReport(results=results)
        assert report.is_valid
        assert report.failures == ()
        assert "2/2" in report.summary

    def test_with_failure(self) -> None:
        results = (
            ValidationResult(property_name="A", passed=True, message="ok"),
            ValidationResult(property_name="B", passed=False, message="fail"),
        )
        report = ValidationReport(results=results)
        assert not report.is_valid
        assert len(report.failures) == 1
        assert "1/2" in report.summary


class TestValidateKnowledgeSpace:
    def test_valid_space(self, abc_domain: Domain) -> None:
        states = frozenset(
            {
                _state(),
                _state("a"),
                _state("a", "b"),
                _state("a", "b", "c"),
            }
        )
        report = validate_knowledge_space(abc_domain, states)
        assert report.is_valid

    def test_valid_power_set(self, ab_domain: Domain) -> None:
        states = frozenset(
            {
                _state(),
                _state("a"),
                _state("b"),
                _state("a", "b"),
            }
        )
        report = validate_knowledge_space(ab_domain, states)
        assert report.is_valid

    def test_empty_states(self, ab_domain: Domain) -> None:
        report = validate_knowledge_space(ab_domain, frozenset())
        assert not report.is_valid

    def test_missing_empty_set(self, ab_domain: Domain) -> None:
        states = frozenset({_state("a", "b")})
        report = validate_knowledge_space(ab_domain, states)
        assert not report.is_valid
        failures = report.failures
        names = {f.property_name for f in failures}
        assert "S1: Empty set" in names

    def test_missing_full_domain(self, ab_domain: Domain) -> None:
        states = frozenset({_state()})
        report = validate_knowledge_space(ab_domain, states)
        assert not report.is_valid
        failures = report.failures
        names = {f.property_name for f in failures}
        assert "S2: Full domain" in names

    def test_not_union_closed(self, abc_domain: Domain) -> None:
        states = frozenset(
            {
                _state(),
                _state("a"),
                _state("b"),
                _state("a", "b", "c"),
            }
        )
        report = validate_knowledge_space(abc_domain, states)
        assert not report.is_valid
        failures = report.failures
        names = {f.property_name for f in failures}
        assert "S3: Closure under union" in names

    def test_state_outside_domain(self, ab_domain: Domain) -> None:
        states = frozenset(
            {
                _state(),
                _state("z"),
                _state("a", "b"),
            }
        )
        report = validate_knowledge_space(ab_domain, states)
        assert not report.is_valid

    def test_references_included(self, abc_domain: Domain) -> None:
        states = frozenset(
            {
                _state(),
                _state("a"),
                _state("a", "b"),
                _state("a", "b", "c"),
            }
        )
        report = validate_knowledge_space(abc_domain, states)
        for result in report.results:
            assert "Doignon" in result.reference or result.reference


class TestValidateLearningSpace:
    def test_valid_learning_space(self, abc_domain: Domain) -> None:
        states = frozenset(
            {
                _state(),
                _state("a"),
                _state("a", "b"),
                _state("a", "b", "c"),
            }
        )
        report = validate_learning_space(abc_domain, states)
        assert report.is_valid

    def test_not_accessible(self, abc_domain: Domain) -> None:
        """State {b, c} is not accessible if only ∅, {a}, {b,c}, Q present."""
        states = frozenset(
            {
                _state(),
                _state("a"),
                _state("b", "c"),
                _state("a", "b", "c"),
            }
        )
        report = validate_learning_space(abc_domain, states)
        assert not report.is_valid
        failures = report.failures
        names = {f.property_name for f in failures}
        assert "Accessibility (antimatroid)" in names

    def test_includes_ks_checks(self, abc_domain: Domain) -> None:
        """Learning space validation includes all knowledge space checks."""
        states = frozenset(
            {
                _state(),
                _state("a"),
                _state("a", "b"),
                _state("a", "b", "c"),
            }
        )
        report = validate_learning_space(abc_domain, states)
        names = {r.property_name for r in report.results}
        assert "S1: Empty set" in names
        assert "S2: Full domain" in names
        assert "S3: Closure under union" in names
        assert "Accessibility (antimatroid)" in names

    def test_accessibility_reference(self, abc_domain: Domain) -> None:
        states = frozenset(
            {
                _state(),
                _state("a"),
                _state("a", "b"),
                _state("a", "b", "c"),
            }
        )
        report = validate_learning_space(abc_domain, states)
        acc_result = next(
            r for r in report.results if r.property_name == "Accessibility (antimatroid)"
        )
        assert "Falmagne" in acc_result.reference
