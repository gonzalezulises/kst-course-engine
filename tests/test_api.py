"""Tests for kst_core.api — REST API endpoints."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from kst_core.api import (
    AssessRespondRequest,
    AssessRespondResponse,
    AssessStartRequest,
    AssessStartResponse,
    AssessStepResponse,
    AssessSummaryResponse,
    CourseInput,
    DomainInput,
    ExportRequest,
    ExportResponse,
    InfoResponse,
    ItemInput,
    PathsResponse,
    PrerequisitesInput,
    SimulateRequest,
    SimulateResponse,
    ValidationCheckResponse,
    ValidationResponse,
    _parse_input,
    create_app,
)


@pytest.fixture()
def client() -> TestClient:
    app = create_app()
    return TestClient(app)


def _minimal_input() -> dict[str, object]:
    return {
        "domain": {
            "name": "Test",
            "items": [{"id": "a"}],
        },
    }


def _linear_input() -> dict[str, object]:
    return {
        "domain": {
            "name": "Linear",
            "description": "Linear chain",
            "items": [
                {"id": "a", "label": "Item A"},
                {"id": "b", "label": "Item B"},
                {"id": "c", "label": "Item C"},
            ],
        },
        "prerequisites": {
            "edges": [["a", "b"], ["b", "c"]],
        },
    }


def _diamond_input() -> dict[str, object]:
    return {
        "domain": {
            "name": "Diamond",
            "items": [
                {"id": "a"},
                {"id": "b"},
                {"id": "c"},
                {"id": "d"},
            ],
        },
        "prerequisites": {
            "edges": [["a", "b"], ["a", "c"], ["b", "d"], ["c", "d"]],
        },
    }


# ---------------------------------------------------------------------------
# Request/Response model tests
# ---------------------------------------------------------------------------


class TestRequestModels:
    def test_item_input(self) -> None:
        item = ItemInput(id="a", label="Item A")
        assert item.id == "a"
        assert item.label == "Item A"

    def test_item_input_default_label(self) -> None:
        item = ItemInput(id="a")
        assert item.label == ""

    def test_domain_input(self) -> None:
        d = DomainInput(name="Test", items=[ItemInput(id="a")])
        assert d.name == "Test"
        assert d.description == ""

    def test_prerequisites_input_default(self) -> None:
        p = PrerequisitesInput()
        assert p.edges == []

    def test_course_input_minimal(self) -> None:
        c = CourseInput(domain=DomainInput(name="T", items=[ItemInput(id="a")]))
        assert c.prerequisites.edges == []

    def test_simulate_request_defaults(self) -> None:
        s = SimulateRequest(domain=DomainInput(name="T", items=[ItemInput(id="a")]))
        assert s.learners == 100
        assert s.beta == 0.1
        assert s.seed is None

    def test_export_request_defaults(self) -> None:
        e = ExportRequest(domain=DomainInput(name="T", items=[ItemInput(id="a")]))
        assert e.format == "dot"
        assert e.type == "hasse"


class TestResponseModels:
    def test_info_response(self) -> None:
        r = InfoResponse(
            name="T",
            description="",
            items=1,
            states=2,
            prerequisites=0,
            critical_path=["a"],
            critical_path_length=1,
            learning_paths=1,
        )
        assert r.name == "T"

    def test_validation_check_response(self) -> None:
        v = ValidationCheckResponse(
            property_name="S1",
            passed=True,
            message="ok",
            reference="ref",
        )
        assert v.passed

    def test_validation_response(self) -> None:
        v = ValidationResponse(is_valid=True, summary="6/6", results=[])
        assert v.is_valid

    def test_paths_response(self) -> None:
        p = PathsResponse(total=1, paths=[["a"]])
        assert p.total == 1

    def test_simulate_response(self) -> None:
        s = SimulateResponse(
            learners=10,
            accuracy=8.0,
            accuracy_pct=80.0,
            avg_questions=1.0,
            expected_steps=1.0,
            simulated_avg_steps=1.0,
        )
        assert s.learners == 10

    def test_export_response(self) -> None:
        e = ExportResponse(format="dot", type="hasse", content="digraph {}")
        assert e.format == "dot"


# ---------------------------------------------------------------------------
# _parse_input tests
# ---------------------------------------------------------------------------


class TestParseInput:
    def test_minimal(self) -> None:
        data = CourseInput(**_minimal_input())  # type: ignore[arg-type]
        course = _parse_input(data)
        assert course.name == "Test"
        assert len(course.domain) == 1

    def test_linear(self) -> None:
        data = CourseInput(**_linear_input())  # type: ignore[arg-type]
        course = _parse_input(data)
        assert len(course.states) == 4

    def test_invalid_edge_raises(self) -> None:
        data = CourseInput(
            domain=DomainInput(name="T", items=[ItemInput(id="a")]),
            prerequisites=PrerequisitesInput(edges=[("a", "z")]),
        )
        with pytest.raises(ValueError, match="unknown item"):
            _parse_input(data)


# ---------------------------------------------------------------------------
# Endpoint tests
# ---------------------------------------------------------------------------


class TestInfoEndpoint:
    def test_info_minimal(self, client: TestClient) -> None:
        resp = client.post("/info", json=_minimal_input())
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Test"
        assert data["items"] == 1
        assert data["states"] == 2

    def test_info_linear(self, client: TestClient) -> None:
        resp = client.post("/info", json=_linear_input())
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Linear"
        assert data["states"] == 4
        assert data["learning_paths"] == 1

    def test_info_invalid(self, client: TestClient) -> None:
        resp = client.post(
            "/info",
            json={
                "domain": {
                    "name": "Bad",
                    "items": [{"id": "a"}],
                },
                "prerequisites": {"edges": [["a", "z"]]},
            },
        )
        assert resp.status_code == 422


class TestValidateEndpoint:
    def test_validate_valid(self, client: TestClient) -> None:
        resp = client.post("/validate", json=_linear_input())
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_valid"] is True
        assert len(data["results"]) == 6

    def test_validate_all_pass(self, client: TestClient) -> None:
        resp = client.post("/validate", json=_minimal_input())
        data = resp.json()
        assert all(r["passed"] for r in data["results"])

    def test_validate_invalid_input(self, client: TestClient) -> None:
        resp = client.post(
            "/validate",
            json={
                "domain": {"name": "Bad", "items": [{"id": "a"}]},
                "prerequisites": {"edges": [["z", "a"]]},
            },
        )
        assert resp.status_code == 422


class TestPathsEndpoint:
    def test_paths_minimal(self, client: TestClient) -> None:
        resp = client.post("/paths", json=_minimal_input())
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["paths"] == [["a"]]

    def test_paths_linear(self, client: TestClient) -> None:
        resp = client.post("/paths", json=_linear_input())
        data = resp.json()
        assert data["total"] == 1
        assert data["paths"][0] == ["a", "b", "c"]

    def test_paths_diamond(self, client: TestClient) -> None:
        resp = client.post("/paths", json=_diamond_input())
        data = resp.json()
        assert data["total"] == 2

    def test_paths_invalid_input(self, client: TestClient) -> None:
        resp = client.post(
            "/paths",
            json={
                "domain": {"name": "Bad", "items": [{"id": "a"}]},
                "prerequisites": {"edges": [["a", "z"]]},
            },
        )
        assert resp.status_code == 422


class TestSimulateEndpoint:
    def test_simulate_basic(self, client: TestClient) -> None:
        payload: dict[str, object] = {
            **_minimal_input(),
            "learners": 5,
            "seed": 42,
        }
        resp = client.post("/simulate", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["learners"] == 5
        assert "accuracy_pct" in data

    def test_simulate_linear(self, client: TestClient) -> None:
        payload: dict[str, object] = {
            **_linear_input(),
            "learners": 5,
            "beta": 0.05,
            "eta": 0.05,
            "seed": 0,
        }
        resp = client.post("/simulate", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["expected_steps"] > 0

    def test_simulate_invalid(self, client: TestClient) -> None:
        resp = client.post(
            "/simulate",
            json={
                "domain": {"name": "Bad", "items": [{"id": "a"}]},
                "prerequisites": {"edges": [["a", "z"]]},
                "learners": 5,
            },
        )
        assert resp.status_code == 422


class TestExportEndpoint:
    def test_export_dot_hasse(self, client: TestClient) -> None:
        payload: dict[str, object] = {**_linear_input(), "format": "dot", "type": "hasse"}
        resp = client.post("/export", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert "digraph Hasse" in data["content"]

    def test_export_mermaid_hasse(self, client: TestClient) -> None:
        payload: dict[str, object] = {**_linear_input(), "format": "mermaid", "type": "hasse"}
        resp = client.post("/export", json=payload)
        assert resp.status_code == 200
        assert "graph BT" in resp.json()["content"]

    def test_export_json(self, client: TestClient) -> None:
        payload: dict[str, object] = {**_linear_input(), "format": "json"}
        resp = client.post("/export", json=payload)
        assert resp.status_code == 200
        content = resp.json()["content"]
        parsed = json.loads(content)
        assert parsed["name"] == "Linear"

    def test_export_prerequisites_dot(self, client: TestClient) -> None:
        payload: dict[str, object] = {
            **_linear_input(),
            "format": "dot",
            "type": "prerequisites",
        }
        resp = client.post("/export", json=payload)
        assert resp.status_code == 200
        assert "digraph Prerequisites" in resp.json()["content"]

    def test_export_prerequisites_mermaid_unsupported(self, client: TestClient) -> None:
        payload: dict[str, object] = {
            **_linear_input(),
            "format": "mermaid",
            "type": "prerequisites",
        }
        resp = client.post("/export", json=payload)
        assert resp.status_code == 400
        assert "not supported" in resp.json()["detail"]

    def test_export_invalid_input(self, client: TestClient) -> None:
        resp = client.post(
            "/export",
            json={
                "domain": {"name": "Bad", "items": [{"id": "a"}]},
                "prerequisites": {"edges": [["a", "z"]]},
            },
        )
        assert resp.status_code == 422


class TestAssessEndpoints:
    def test_assess_start(self, client: TestClient) -> None:
        resp = client.post("/assess/start", json=_linear_input())
        assert resp.status_code == 200
        data = resp.json()
        assert "session_id" in data
        assert "first_item" in data
        assert data["first_item"] in {"a", "b", "c"}

    def test_assess_respond(self, client: TestClient) -> None:
        start = client.post("/assess/start", json=_linear_input())
        sid = start.json()["session_id"]
        resp = client.post(f"/assess/{sid}/respond", json={"correct": True})
        assert resp.status_code == 200
        data = resp.json()
        assert "step" in data
        assert data["step"]["correct"] is True
        assert isinstance(data["is_complete"], bool)

    def test_assess_full_session(self, client: TestClient) -> None:
        start = client.post("/assess/start", json=_minimal_input())
        sid = start.json()["session_id"]
        # Minimal domain: 1 item, should complete quickly
        resp = client.post(f"/assess/{sid}/respond", json={"correct": True})
        data = resp.json()
        assert data["is_complete"] is True
        assert data["next_item"] is None

    def test_assess_summary(self, client: TestClient) -> None:
        start = client.post("/assess/start", json=_minimal_input())
        sid = start.json()["session_id"]
        client.post(f"/assess/{sid}/respond", json={"correct": True})
        resp = client.get(f"/assess/{sid}/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_questions"] == 1
        assert 0.0 <= data["confidence"] <= 1.0

    def test_assess_summary_before_respond(self, client: TestClient) -> None:
        start = client.post("/assess/start", json=_linear_input())
        sid = start.json()["session_id"]
        resp = client.get(f"/assess/{sid}/summary")
        assert resp.status_code == 200
        assert resp.json()["total_questions"] == 0

    def test_assess_respond_not_found(self, client: TestClient) -> None:
        resp = client.post("/assess/nonexistent/respond", json={"correct": True})
        assert resp.status_code == 404

    def test_assess_summary_not_found(self, client: TestClient) -> None:
        resp = client.get("/assess/nonexistent/summary")
        assert resp.status_code == 404

    def test_assess_start_invalid(self, client: TestClient) -> None:
        resp = client.post(
            "/assess/start",
            json={
                "domain": {"name": "Bad", "items": [{"id": "a"}]},
                "prerequisites": {"edges": [["a", "z"]]},
            },
        )
        assert resp.status_code == 422

    def test_assess_request_models(self) -> None:
        req = AssessStartRequest(
            domain=DomainInput(name="T", items=[ItemInput(id="a")])
        )
        assert req.beta == 0.1
        respond = AssessRespondRequest(correct=False)
        assert respond.correct is False

    def test_assess_response_models(self) -> None:
        start = AssessStartResponse(session_id="abc", first_item="a")
        assert start.session_id == "abc"
        step = AssessStepResponse(
            item_id="a",
            correct=True,
            entropy_before=1.0,
            entropy_after=0.5,
            estimate_ids=["a"],
        )
        assert step.item_id == "a"
        respond = AssessRespondResponse(
            step=step, next_item="b", is_complete=False
        )
        assert respond.next_item == "b"
        summary = AssessSummaryResponse(
            total_questions=1,
            final_state_ids=["a"],
            confidence=0.9,
            mastered=["a"],
            not_mastered=["b"],
        )
        assert summary.confidence == 0.9


class TestCreateApp:
    def test_app_has_routes(self) -> None:
        application = create_app()
        route_paths = [r.path for r in application.routes]  # type: ignore[union-attr]
        assert "/info" in route_paths
        assert "/validate" in route_paths
        assert "/paths" in route_paths
        assert "/simulate" in route_paths
        assert "/export" in route_paths
        assert "/assess/start" in route_paths
        assert "/assess/{session_id}/respond" in route_paths
        assert "/assess/{session_id}/summary" in route_paths

    def test_app_metadata(self) -> None:
        application = create_app()
        assert application.title == "KST Course Engine API"
        assert application.version == "0.1.0"
