"""REST API for the KST Course Engine.

Provides HTTP endpoints for course analysis, validation, simulation,
and export via FastAPI.

Usage:
    uvicorn kst_core.api:app --reload

The ``create_app()`` factory builds the FastAPI application.  A module-level
``app`` instance is also provided for ``uvicorn kst_core.api:app``.
"""

from __future__ import annotations

from pydantic import BaseModel

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
except ImportError as _exc:  # pragma: no cover
    msg = "FastAPI is required for the REST API. Install with: pip install kst-course-engine[api]"
    raise ImportError(msg) from _exc

from kst_core.assessment import BLIMParameters, simulate_responses
from kst_core.interactive import SessionStore
from kst_core.learning import LearningModel, LearningRate
from kst_core.parser import (
    CourseDefinition,
    CourseSchema,
    DomainSchema,
    ItemSchema,
    PrerequisitesSchema,
    build_course,
)
from kst_core.validation import validate_learning_space
from kst_core.viz import course_json, hasse_dot, hasse_mermaid, prerequisites_dot

# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------


class ItemInput(BaseModel):
    """An item in a course definition."""

    id: str
    label: str = ""


class DomainInput(BaseModel):
    """Domain section of a course."""

    name: str
    description: str = ""
    items: list[ItemInput]


class PrerequisitesInput(BaseModel):
    """Prerequisites section of a course."""

    edges: list[tuple[str, str]] = []


class CourseInput(BaseModel):
    """Full course definition for API input."""

    domain: DomainInput
    prerequisites: PrerequisitesInput = PrerequisitesInput()


class SimulateRequest(BaseModel):
    """Request body for /simulate."""

    domain: DomainInput
    prerequisites: PrerequisitesInput = PrerequisitesInput()
    learners: int = 100
    beta: float = 0.1
    eta: float = 0.1
    seed: int | None = None


class ExportRequest(BaseModel):
    """Request body for /export."""

    domain: DomainInput
    prerequisites: PrerequisitesInput = PrerequisitesInput()
    format: str = "dot"
    type: str = "hasse"


class AssessStartRequest(BaseModel):
    """Request body for /assess/start."""

    domain: DomainInput
    prerequisites: PrerequisitesInput = PrerequisitesInput()
    beta: float = 0.1
    eta: float = 0.1


class AssessRespondRequest(BaseModel):
    """Request body for /assess/{session_id}/respond."""

    correct: bool


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class InfoResponse(BaseModel):
    """Response from /info."""

    name: str
    description: str
    items: int
    states: int
    prerequisites: int
    critical_path: list[str]
    critical_path_length: int
    learning_paths: int


class ValidationCheckResponse(BaseModel):
    """A single validation check result."""

    property_name: str
    passed: bool
    message: str
    reference: str


class ValidationResponse(BaseModel):
    """Response from /validate."""

    is_valid: bool
    summary: str
    results: list[ValidationCheckResponse]


class PathsResponse(BaseModel):
    """Response from /paths."""

    total: int
    paths: list[list[str]]


class SimulateResponse(BaseModel):
    """Response from /simulate."""

    learners: int
    accuracy: float
    accuracy_pct: float
    avg_questions: float
    expected_steps: float
    simulated_avg_steps: float


class ExportResponse(BaseModel):
    """Response from /export."""

    format: str
    type: str
    content: str


class AssessStartResponse(BaseModel):
    """Response from /assess/start."""

    session_id: str
    first_item: str


class AssessStepResponse(BaseModel):
    """A single assessment step in the response."""

    item_id: str
    correct: bool
    entropy_before: float
    entropy_after: float
    estimate_ids: list[str]


class AssessRespondResponse(BaseModel):
    """Response from /assess/{session_id}/respond."""

    step: AssessStepResponse
    next_item: str | None
    is_complete: bool


class AssessSummaryResponse(BaseModel):
    """Response from /assess/{session_id}/summary."""

    total_questions: int
    final_state_ids: list[str]
    confidence: float
    mastered: list[str]
    not_mastered: list[str]


# ---------------------------------------------------------------------------
# Input parsing
# ---------------------------------------------------------------------------


def _parse_input(data: CourseInput) -> CourseDefinition:
    """Convert API input to a CourseDefinition."""
    item_schemas = tuple(ItemSchema(id=i.id, label=i.label) for i in data.domain.items)
    domain_schema = DomainSchema(
        name=data.domain.name,
        description=data.domain.description,
        items=item_schemas,
    )
    prereqs = PrerequisitesSchema(edges=tuple(data.prerequisites.edges))
    schema = CourseSchema(domain=domain_schema, prerequisites=prereqs)
    return build_course(schema)


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------


def create_app() -> FastAPI:
    """Create the FastAPI application."""
    application = FastAPI(
        title="KST Course Engine API",
        description="Knowledge Space Theory — REST API for course analysis",
        version="0.1.0",
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.post("/info", response_model=InfoResponse)
    def info_endpoint(data: CourseInput) -> InfoResponse:
        """Course overview: items, states, prerequisites, paths."""
        try:
            course = _parse_input(data)
        except (ValueError, Exception) as e:
            raise HTTPException(status_code=422, detail=str(e)) from e

        critical = course.prerequisite_graph.critical_path()
        ls = course.to_learning_space()
        n_paths = len(ls.learning_paths())

        return InfoResponse(
            name=course.name,
            description=course.description,
            items=len(course.domain),
            states=len(course.states),
            prerequisites=len(course.prerequisite_graph.edges),
            critical_path=critical,
            critical_path_length=len(critical),
            learning_paths=n_paths,
        )

    @application.post("/validate", response_model=ValidationResponse)
    def validate_endpoint(data: CourseInput) -> ValidationResponse:
        """Formal validation of knowledge space axioms."""
        try:
            course = _parse_input(data)
        except (ValueError, Exception) as e:
            raise HTTPException(status_code=422, detail=str(e)) from e

        report = validate_learning_space(course.domain, course.states)
        results = [
            ValidationCheckResponse(
                property_name=r.property_name,
                passed=r.passed,
                message=r.message,
                reference=r.reference,
            )
            for r in report.results
        ]
        return ValidationResponse(
            is_valid=report.is_valid,
            summary=report.summary,
            results=results,
        )

    @application.post("/paths", response_model=PathsResponse)
    def paths_endpoint(data: CourseInput) -> PathsResponse:
        """Enumerate learning paths from empty set to full domain."""
        try:
            course = _parse_input(data)
        except (ValueError, Exception) as e:
            raise HTTPException(status_code=422, detail=str(e)) from e

        ls = course.to_learning_space()
        paths = ls.learning_paths()
        path_ids = [[item.id for item in path] for path in paths]
        return PathsResponse(total=len(paths), paths=path_ids)

    @application.post("/simulate", response_model=SimulateResponse)
    def simulate_endpoint(data: SimulateRequest) -> SimulateResponse:
        """Simulate a learner cohort with adaptive assessment."""
        import numpy as np

        course_input = CourseInput(
            domain=data.domain,
            prerequisites=data.prerequisites,
        )
        try:
            course = _parse_input(course_input)
        except (ValueError, Exception) as e:
            raise HTTPException(status_code=422, detail=str(e)) from e

        rng = np.random.default_rng(data.seed)
        params = BLIMParameters.uniform(course.domain, beta=data.beta, eta=data.eta)
        state_list = sorted(course.states, key=lambda s: (len(s), sorted(s.item_ids)))

        from kst_core.assessment import AdaptiveAssessment

        correct_count = 0
        total_questions: list[int] = []

        for _ in range(data.learners):
            true_state = state_list[int(rng.integers(len(state_list)))]
            responses = simulate_responses(true_state, params, rng=rng)
            session = AdaptiveAssessment.start(course.domain, course.states, params)
            result = session.run(responses)
            if result.current_estimate == true_state:
                correct_count += 1
            total_questions.append(len(responses))

        accuracy = correct_count / data.learners
        accuracy_pct = accuracy * 100

        ls = course.to_learning_space()
        rates = LearningRate.uniform(course.domain)
        model = LearningModel(space=ls, rates=rates)

        lengths: list[int] = []
        for _ in range(data.learners):
            traj = model.simulate_trajectory(rng=rng)
            lengths.append(len(traj) - 1)

        expected = model.expected_steps()
        empty_state = course.domain.empty_state

        return SimulateResponse(
            learners=data.learners,
            accuracy=float(correct_count),
            accuracy_pct=round(accuracy_pct, 1),
            avg_questions=round(float(np.mean(total_questions)), 1),
            expected_steps=round(expected[empty_state], 1),
            simulated_avg_steps=round(float(np.mean(lengths)), 1),
        )

    @application.post("/export", response_model=ExportResponse)
    def export_endpoint(data: ExportRequest) -> ExportResponse:
        """Export course structure as DOT, JSON, or Mermaid."""
        course_input = CourseInput(
            domain=data.domain,
            prerequisites=data.prerequisites,
        )
        try:
            course = _parse_input(course_input)
        except (ValueError, Exception) as e:
            raise HTTPException(status_code=422, detail=str(e)) from e

        fmt = data.format
        diagram_type = data.type

        if fmt == "json":
            content = course_json(course)
        elif diagram_type == "prerequisites":
            if fmt == "mermaid":
                raise HTTPException(
                    status_code=400,
                    detail="Mermaid format not supported for prerequisites",
                )
            content = prerequisites_dot(course.prerequisite_graph)
        elif fmt == "dot":
            ls = course.to_learning_space()
            content = hasse_dot(ls)
        else:
            ls = course.to_learning_space()
            content = hasse_mermaid(ls)

        return ExportResponse(format=fmt, type=diagram_type, content=content)

    # --- Assessment session endpoints ---
    store = SessionStore()

    @application.post("/assess/start", response_model=AssessStartResponse)
    def assess_start_endpoint(data: AssessStartRequest) -> AssessStartResponse:
        """Start an interactive assessment session."""
        course_input = CourseInput(
            domain=data.domain,
            prerequisites=data.prerequisites,
        )
        try:
            course = _parse_input(course_input)
        except (ValueError, Exception) as e:
            raise HTTPException(status_code=422, detail=str(e)) from e

        session_id, first_item = store.create(course, beta=data.beta, eta=data.eta)
        return AssessStartResponse(session_id=session_id, first_item=first_item)

    @application.post(
        "/assess/{session_id}/respond",
        response_model=AssessRespondResponse,
    )
    def assess_respond_endpoint(
        session_id: str,
        data: AssessRespondRequest,
    ) -> AssessRespondResponse:
        """Record a response and get the next item."""
        if not store.has_session(session_id):
            raise HTTPException(status_code=404, detail="Session not found")

        step, next_item, is_complete = store.respond(session_id, data.correct)
        return AssessRespondResponse(
            step=AssessStepResponse(
                item_id=step.item_id,
                correct=step.correct,
                entropy_before=step.entropy_before,
                entropy_after=step.entropy_after,
                estimate_ids=sorted(step.estimate_ids),
            ),
            next_item=next_item,
            is_complete=is_complete,
        )

    @application.get(
        "/assess/{session_id}/summary",
        response_model=AssessSummaryResponse,
    )
    def assess_summary_endpoint(session_id: str) -> AssessSummaryResponse:
        """Get the assessment summary for a session."""
        if not store.has_session(session_id):
            raise HTTPException(status_code=404, detail="Session not found")

        summary = store.summary(session_id)
        return AssessSummaryResponse(
            total_questions=summary.total_questions,
            final_state_ids=sorted(summary.final_state_ids),
            confidence=summary.confidence,
            mastered=sorted(summary.mastered),
            not_mastered=sorted(summary.not_mastered),
        )

    return application


app: FastAPI = create_app()
