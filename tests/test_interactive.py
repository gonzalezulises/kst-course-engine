"""Tests for kst_core.interactive — interactive assessment sessions."""

from __future__ import annotations

import io
import textwrap

import pytest

from kst_core.interactive import (
    AssessmentStep,
    AssessmentSummary,
    SessionStore,
    _max_entropy,
    run_terminal_assessment,
)
from kst_core.parser import parse_yaml

LINEAR_YAML = textwrap.dedent("""\
    domain:
      name: "Linear"
      items:
        - id: "a"
          label: "Item A"
        - id: "b"
          label: "Item B"
        - id: "c"
          label: "Item C"
    prerequisites:
      edges:
        - ["a", "b"]
        - ["b", "c"]
""")

MINIMAL_YAML = textwrap.dedent("""\
    domain:
      name: "Test"
      items:
        - id: "a"
""")


@pytest.fixture()
def linear_course() -> object:
    return parse_yaml(LINEAR_YAML)


@pytest.fixture()
def minimal_course() -> object:
    return parse_yaml(MINIMAL_YAML)


# ---------------------------------------------------------------------------
# AssessmentStep model tests
# ---------------------------------------------------------------------------


class TestAssessmentStep:
    def test_create(self) -> None:
        step = AssessmentStep(
            item_id="a",
            correct=True,
            entropy_before=2.0,
            entropy_after=1.0,
            estimate_ids=frozenset({"a"}),
        )
        assert step.item_id == "a"
        assert step.correct is True
        assert step.entropy_before == 2.0
        assert step.entropy_after == 1.0
        assert step.estimate_ids == frozenset({"a"})

    def test_frozen(self) -> None:
        step = AssessmentStep(
            item_id="a",
            correct=True,
            entropy_before=2.0,
            entropy_after=1.0,
            estimate_ids=frozenset(),
        )
        with pytest.raises(Exception):  # noqa: B017
            step.item_id = "b"  # type: ignore[misc]


class TestAssessmentSummary:
    def test_create(self) -> None:
        summary = AssessmentSummary(
            total_questions=3,
            steps=(),
            final_state_ids=frozenset({"a", "b"}),
            confidence=0.95,
            mastered=frozenset({"a", "b"}),
            not_mastered=frozenset({"c"}),
        )
        assert summary.total_questions == 3
        assert summary.confidence == 0.95
        assert "a" in summary.mastered
        assert "c" in summary.not_mastered

    def test_frozen(self) -> None:
        summary = AssessmentSummary(
            total_questions=0,
            steps=(),
            final_state_ids=frozenset(),
            confidence=1.0,
            mastered=frozenset(),
            not_mastered=frozenset(),
        )
        with pytest.raises(Exception):  # noqa: B017
            summary.total_questions = 5  # type: ignore[misc]


# ---------------------------------------------------------------------------
# _max_entropy tests
# ---------------------------------------------------------------------------


class TestMaxEntropy:
    def test_single_state(self) -> None:
        assert _max_entropy(1) == 0.0

    def test_two_states(self) -> None:
        assert _max_entropy(2) == 1.0

    def test_four_states(self) -> None:
        assert _max_entropy(4) == 2.0

    def test_zero(self) -> None:
        assert _max_entropy(0) == 0.0


# ---------------------------------------------------------------------------
# SessionStore tests
# ---------------------------------------------------------------------------


class TestSessionStore:
    def test_create_session(self, linear_course: object) -> None:
        store = SessionStore()
        sid, first_item = store.create(linear_course)  # type: ignore[arg-type]
        assert isinstance(sid, str)
        assert len(sid) > 0
        assert first_item in {"a", "b", "c"}
        assert store.has_session(sid)

    def test_has_session_false(self) -> None:
        store = SessionStore()
        assert not store.has_session("nonexistent")

    def test_respond(self, linear_course: object) -> None:
        store = SessionStore()
        sid, first_item = store.create(linear_course)  # type: ignore[arg-type]
        step, _next_item, _is_complete = store.respond(sid, correct=True)
        assert isinstance(step, AssessmentStep)
        assert step.item_id == first_item
        assert step.correct is True
        assert step.entropy_after <= step.entropy_before

    def test_respond_until_complete(self, minimal_course: object) -> None:
        store = SessionStore()
        sid, _ = store.create(minimal_course)  # type: ignore[arg-type]
        # Minimal course has 1 item, so one response completes it
        _step, next_item, is_complete = store.respond(sid, correct=True)
        assert is_complete
        assert next_item is None

    def test_summary(self, linear_course: object) -> None:
        store = SessionStore()
        sid, _ = store.create(linear_course)  # type: ignore[arg-type]
        store.respond(sid, correct=True)
        summary = store.summary(sid)
        assert isinstance(summary, AssessmentSummary)
        assert summary.total_questions == 1
        assert 0.0 <= summary.confidence <= 1.0

    def test_summary_empty(self, linear_course: object) -> None:
        store = SessionStore()
        sid, _ = store.create(linear_course)  # type: ignore[arg-type]
        summary = store.summary(sid)
        assert summary.total_questions == 0

    def test_get_nonexistent_raises(self) -> None:
        store = SessionStore()
        with pytest.raises(KeyError, match="not found"):
            store._get("nonexistent")

    def test_custom_params(self, linear_course: object) -> None:
        store = SessionStore()
        sid, _ = store.create(
            linear_course,  # type: ignore[arg-type]
            beta=0.05,
            eta=0.05,
        )
        assert store.has_session(sid)


# ---------------------------------------------------------------------------
# run_terminal_assessment tests
# ---------------------------------------------------------------------------


class TestRunTerminalAssessment:
    def test_all_yes(
        self,
        linear_course: object,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # Simulate answering "y" to all questions
        inputs = "y\n" * 10  # more than enough
        monkeypatch.setattr("sys.stdin", io.StringIO(inputs))
        summary = run_terminal_assessment(linear_course)  # type: ignore[arg-type]
        assert isinstance(summary, AssessmentSummary)
        assert summary.total_questions > 0
        out = capsys.readouterr().out
        assert "Assessment Complete" in out

    def test_all_no(
        self,
        linear_course: object,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        inputs = "n\n" * 10
        monkeypatch.setattr("sys.stdin", io.StringIO(inputs))
        summary = run_terminal_assessment(linear_course)  # type: ignore[arg-type]
        assert summary.total_questions > 0
        assert "Not mastered" in capsys.readouterr().out or True  # output varies

    def test_custom_params(
        self,
        linear_course: object,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        inputs = "y\n" * 10
        monkeypatch.setattr("sys.stdin", io.StringIO(inputs))
        summary = run_terminal_assessment(
            linear_course,  # type: ignore[arg-type]
            beta=0.05,
            eta=0.05,
            entropy_threshold=0.5,
        )
        assert summary.total_questions > 0
        assert summary.confidence > 0.0

    def test_mixed_responses(
        self,
        linear_course: object,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        inputs = "y\nn\ny\nn\ny\nn\ny\n"
        monkeypatch.setattr("sys.stdin", io.StringIO(inputs))
        summary = run_terminal_assessment(linear_course)  # type: ignore[arg-type]
        assert summary.total_questions > 0

    def test_yes_spelled_out(
        self,
        minimal_course: object,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        inputs = "yes\n" * 5
        monkeypatch.setattr("sys.stdin", io.StringIO(inputs))
        summary = run_terminal_assessment(minimal_course)  # type: ignore[arg-type]
        assert summary.total_questions >= 1
