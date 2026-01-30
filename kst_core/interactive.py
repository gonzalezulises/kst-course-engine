"""Interactive assessment sessions for the KST Course Engine.

Provides stateful assessment sessions that track question-by-question
progress and produce detailed summaries.

- ``AssessmentStep``: one Q&A record with entropy and state estimates.
- ``AssessmentSummary``: final report after assessment completion.
- ``SessionStore``: in-memory session storage for the REST API.
- ``run_terminal_assessment``: interactive terminal loop (stdin y/n).

References:
    Falmagne, J.-Cl. & Doignon, J.-P. (2011). Learning Spaces, Ch. 12.
"""

from __future__ import annotations

import sys
import uuid
from typing import TYPE_CHECKING

from pydantic import BaseModel

from kst_core.assessment import AdaptiveAssessment, BLIMParameters

if TYPE_CHECKING:
    from kst_core.parser import CourseDefinition


class AssessmentStep(BaseModel, frozen=True):
    """Record of a single assessment question.

    Captures the item asked, response, entropy before/after,
    and the MAP state estimate after the update.
    """

    item_id: str
    correct: bool
    entropy_before: float
    entropy_after: float
    estimate_ids: frozenset[str]

    model_config = {"arbitrary_types_allowed": True}


class AssessmentSummary(BaseModel, frozen=True):
    """Final report after completing an interactive assessment.

    Contains the sequence of steps, the final estimated state,
    a confidence metric (1 - normalized entropy), and
    mastered/not-mastered item lists.
    """

    total_questions: int
    steps: tuple[AssessmentStep, ...]
    final_state_ids: frozenset[str]
    confidence: float
    mastered: frozenset[str]
    not_mastered: frozenset[str]

    model_config = {"arbitrary_types_allowed": True}


class _SessionState:
    """Internal mutable state for an ongoing assessment session."""

    def __init__(self, session: AdaptiveAssessment, course: CourseDefinition) -> None:
        self.session = session
        self.course = course
        self.steps: list[AssessmentStep] = []
        self.completed = False


class SessionStore:
    """In-memory session store for REST API assessment sessions.

    Maps session IDs (strings) to active ``_SessionState`` objects.
    """

    def __init__(self) -> None:
        self._sessions: dict[str, _SessionState] = {}

    def create(
        self,
        course: CourseDefinition,
        beta: float = 0.1,
        eta: float = 0.1,
    ) -> tuple[str, str]:
        """Start a new assessment session.

        Returns:
            (session_id, first_item_id) tuple.
        """
        params = BLIMParameters.uniform(course.domain, beta=beta, eta=eta)
        session = AdaptiveAssessment.start(course.domain, course.states, params)
        first_item = session.select_item()
        sid = uuid.uuid4().hex
        self._sessions[sid] = _SessionState(session=session, course=course)
        return sid, first_item

    def respond(
        self,
        session_id: str,
        correct: bool,
    ) -> tuple[AssessmentStep, str | None, bool]:
        """Record a response for the current item.

        Returns:
            (step, next_item_id_or_None, is_complete) tuple.
        """
        state = self._get(session_id)
        session = state.session

        item_id = session.select_item()
        entropy_before = session.current_entropy
        new_session = session.observe(item_id, correct)
        entropy_after = new_session.current_entropy
        estimate = new_session.current_estimate

        step = AssessmentStep(
            item_id=item_id,
            correct=correct,
            entropy_before=round(entropy_before, 6),
            entropy_after=round(entropy_after, 6),
            estimate_ids=estimate.item_ids,
        )
        state.steps.append(step)
        state.session = new_session

        is_complete = new_session.is_complete or new_session.current_entropy < 0.1
        if is_complete:
            state.completed = True
            return step, None, True

        next_item = new_session.select_item()
        return step, next_item, False

    def summary(self, session_id: str) -> AssessmentSummary:
        """Get the summary for a completed (or in-progress) session."""
        state = self._get(session_id)
        session = state.session
        estimate = session.current_estimate
        domain_ids = session.domain.item_ids

        max_entropy = _max_entropy(len(session.states))
        confidence = 1.0 - (session.current_entropy / max_entropy) if max_entropy > 0 else 1.0

        return AssessmentSummary(
            total_questions=len(state.steps),
            steps=tuple(state.steps),
            final_state_ids=estimate.item_ids,
            confidence=round(confidence, 4),
            mastered=estimate.item_ids,
            not_mastered=domain_ids - estimate.item_ids,
        )

    def has_session(self, session_id: str) -> bool:
        """Check if a session exists."""
        return session_id in self._sessions

    def _get(self, session_id: str) -> _SessionState:
        if session_id not in self._sessions:
            msg = f"Session not found: {session_id}"
            raise KeyError(msg)
        return self._sessions[session_id]


def _max_entropy(n_states: int) -> float:
    """Maximum entropy for a uniform distribution over n_states."""
    import math

    if n_states <= 1:
        return 0.0
    return math.log2(n_states)


def run_terminal_assessment(
    course: CourseDefinition,
    beta: float = 0.1,
    eta: float = 0.1,
    entropy_threshold: float = 0.1,
) -> AssessmentSummary:
    """Run an interactive assessment in the terminal (stdin y/n).

    Asks questions one at a time, reads y/n from stdin, and updates
    the belief state until convergence or all items are asked.

    Args:
        course: A parsed CourseDefinition.
        beta: Uniform slip probability.
        eta: Uniform guess probability.
        entropy_threshold: Stop when entropy drops below this.

    Returns:
        AssessmentSummary with the assessment results.
    """
    params = BLIMParameters.uniform(course.domain, beta=beta, eta=eta)
    session = AdaptiveAssessment.start(course.domain, course.states, params)
    steps: list[AssessmentStep] = []

    print(f"Interactive Assessment: {course.name}")
    print(f"Domain: {len(course.domain)} items, {len(course.states)} states")
    print("Answer y (yes/correct) or n (no/incorrect) for each item.\n")

    while not session.is_complete and session.current_entropy > entropy_threshold:
        item_id = session.select_item()
        item = course.domain.get_item(item_id)
        label = item.label if item and item.label else item_id

        print(f"  Q: Can the learner demonstrate '{label}'? (y/n) ", end="", flush=True)
        answer = sys.stdin.readline().strip().lower()
        correct = answer in ("y", "yes")

        entropy_before = session.current_entropy
        session = session.observe(item_id, correct)
        entropy_after = session.current_entropy
        estimate = session.current_estimate

        step = AssessmentStep(
            item_id=item_id,
            correct=correct,
            entropy_before=round(entropy_before, 6),
            entropy_after=round(entropy_after, 6),
            estimate_ids=estimate.item_ids,
        )
        steps.append(step)
        status = "correct" if correct else "incorrect"
        print(f"     -> {status}, entropy: {entropy_before:.3f} -> {entropy_after:.3f}")

    estimate = session.current_estimate
    domain_ids = session.domain.item_ids
    max_ent = _max_entropy(len(session.states))
    confidence = 1.0 - (session.current_entropy / max_ent) if max_ent > 0 else 1.0

    summary = AssessmentSummary(
        total_questions=len(steps),
        steps=tuple(steps),
        final_state_ids=estimate.item_ids,
        confidence=round(confidence, 4),
        mastered=estimate.item_ids,
        not_mastered=domain_ids - estimate.item_ids,
    )

    print("\n=== Assessment Complete ===")
    print(f"Questions asked: {summary.total_questions}")
    print(f"Confidence: {summary.confidence:.1%}")
    print(f"Mastered: {sorted(summary.mastered)}")
    print(f"Not mastered: {sorted(summary.not_mastered)}")

    return summary
