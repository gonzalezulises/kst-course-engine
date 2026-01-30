"""Tests for kst_core.viz — visualization and export."""

from __future__ import annotations

import json

from kst_core.domain import Domain, Item, KnowledgeState
from kst_core.parser import parse_file
from kst_core.prerequisites import PrerequisiteGraph
from kst_core.space import KnowledgeSpace, LearningSpace
from kst_core.viz import (
    course_json,
    hasse_dot,
    hasse_mermaid,
    prerequisites_dot,
    trajectory_dot,
)

EXAMPLE_FILE = "examples/intro-pandas.kst.yaml"


def _make_items() -> tuple[Item, Item, Item]:
    return Item(id="a"), Item(id="b"), Item(id="c")


def _make_learning_space() -> LearningSpace:
    a, b, c = _make_items()
    domain = Domain(items=frozenset({a, b, c}))
    states = frozenset(
        {
            KnowledgeState(),
            KnowledgeState(items=frozenset({a})),
            KnowledgeState(items=frozenset({b})),
            KnowledgeState(items=frozenset({a, b})),
            KnowledgeState(items=frozenset({a, b, c})),
        }
    )
    return LearningSpace(domain=domain, states=states)


def _make_knowledge_space() -> KnowledgeSpace:
    a, b, c = _make_items()
    domain = Domain(items=frozenset({a, b, c}))
    states = frozenset(
        {
            KnowledgeState(),
            KnowledgeState(items=frozenset({a})),
            KnowledgeState(items=frozenset({b})),
            KnowledgeState(items=frozenset({a, b})),
            KnowledgeState(items=frozenset({a, b, c})),
        }
    )
    return KnowledgeSpace(domain=domain, states=states)


class TestCoveringEdgesGap:
    """Test covering relation with gaps in state sizes."""

    def test_size_gap_no_covering_edges(self) -> None:
        """A space with sizes 0 and 2 (gap at 1) has no covering edges."""
        a, b = Item(id="a"), Item(id="b")
        domain = Domain(items=frozenset({a, b}))
        # {}, {a,b} -- valid KnowledgeSpace (closed under union), gap at size 1
        states = frozenset(
            {
                KnowledgeState(),
                KnowledgeState(items=frozenset({a, b})),
            }
        )
        ks = KnowledgeSpace(domain=domain, states=states)
        dot = hasse_dot(ks)
        # No covering edges since there's a size gap (0 → 2)
        assert "->" not in dot


class TestHasseDot:
    def test_basic_structure(self) -> None:
        ls = _make_learning_space()
        dot = hasse_dot(ls)
        assert "digraph Hasse" in dot
        assert "rankdir=BT" in dot
        assert "s_empty" in dot
        assert "s_a_b_c" in dot

    def test_contains_edges(self) -> None:
        ls = _make_learning_space()
        dot = hasse_dot(ls)
        assert "->" in dot

    def test_edge_labels(self) -> None:
        ls = _make_learning_space()
        dot = hasse_dot(ls)
        # Covering edges from empty to {a} and {b} should have +a and +b labels
        assert "+a" in dot or "+b" in dot

    def test_rank_same_grouping(self) -> None:
        ls = _make_learning_space()
        dot = hasse_dot(ls)
        assert "rank=same" in dot

    def test_node_labels(self) -> None:
        ls = _make_learning_space()
        dot = hasse_dot(ls)
        # Empty state
        assert "\u2205" in dot
        # Full state contains all items
        assert "a" in dot
        assert "b" in dot
        assert "c" in dot

    def test_knowledge_space_input(self) -> None:
        ks = _make_knowledge_space()
        dot = hasse_dot(ks)
        assert "digraph Hasse" in dot
        assert "s_empty" in dot

    def test_from_example_file(self) -> None:
        course = parse_file(EXAMPLE_FILE)
        ls = course.to_learning_space()
        dot = hasse_dot(ls)
        assert "digraph Hasse" in dot
        assert "}" in dot


class TestPrerequisitesDot:
    def test_basic_structure(self) -> None:
        a, b, c = _make_items()
        domain = Domain(items=frozenset({a, b, c}))
        graph = PrerequisiteGraph(domain=domain, edges=frozenset({("a", "b"), ("b", "c")}))
        dot = prerequisites_dot(graph)
        assert "digraph Prerequisites" in dot
        assert "rankdir=LR" in dot

    def test_contains_nodes_and_edges(self) -> None:
        a, b, c = _make_items()
        domain = Domain(items=frozenset({a, b, c}))
        graph = PrerequisiteGraph(domain=domain, edges=frozenset({("a", "b"), ("b", "c")}))
        dot = prerequisites_dot(graph)
        assert '"a"' in dot
        assert '"b"' in dot
        assert '"c"' in dot
        assert '"a" -> "b"' in dot
        assert '"b" -> "c"' in dot

    def test_from_example_file(self) -> None:
        course = parse_file(EXAMPLE_FILE)
        dot = prerequisites_dot(course.prerequisite_graph)
        assert "digraph Prerequisites" in dot


class TestTrajectoryDot:
    def test_basic_structure(self) -> None:
        a, b = Item(id="a"), Item(id="b")
        traj = (
            KnowledgeState(),
            KnowledgeState(items=frozenset({a})),
            KnowledgeState(items=frozenset({a, b})),
        )
        dot = trajectory_dot(traj)
        assert "digraph Trajectory" in dot
        assert "rankdir=LR" in dot

    def test_edge_labels(self) -> None:
        a, b = Item(id="a"), Item(id="b")
        traj = (
            KnowledgeState(),
            KnowledgeState(items=frozenset({a})),
            KnowledgeState(items=frozenset({a, b})),
        )
        dot = trajectory_dot(traj)
        assert "+a" in dot
        assert "+b" in dot

    def test_no_highlight(self) -> None:
        a, b = Item(id="a"), Item(id="b")
        traj = (
            KnowledgeState(),
            KnowledgeState(items=frozenset({a})),
            KnowledgeState(items=frozenset({a, b})),
        )
        dot = trajectory_dot(traj, highlight_items=False)
        assert "+a" not in dot
        assert "+b" not in dot
        assert "->" in dot

    def test_final_state_bold(self) -> None:
        a = Item(id="a")
        traj = (
            KnowledgeState(),
            KnowledgeState(items=frozenset({a})),
        )
        dot = trajectory_dot(traj)
        assert "bold" in dot

    def test_multi_item_step(self) -> None:
        """A trajectory step adding 2 items at once has no label."""
        a, b = Item(id="a"), Item(id="b")
        traj = (
            KnowledgeState(),
            KnowledgeState(items=frozenset({a, b})),
        )
        dot = trajectory_dot(traj)
        # No label for multi-item step
        assert "label" not in dot.split("\n")[-3] or "+a" not in dot.split("\n")[-3]


class TestHasseMermaid:
    def test_basic_structure(self) -> None:
        ls = _make_learning_space()
        mermaid = hasse_mermaid(ls)
        assert "graph BT" in mermaid

    def test_contains_nodes(self) -> None:
        ls = _make_learning_space()
        mermaid = hasse_mermaid(ls)
        assert "s_empty" in mermaid
        assert "s_a_b_c" in mermaid

    def test_contains_edges(self) -> None:
        ls = _make_learning_space()
        mermaid = hasse_mermaid(ls)
        assert "-->" in mermaid

    def test_edge_labels(self) -> None:
        ls = _make_learning_space()
        mermaid = hasse_mermaid(ls)
        assert "+a" in mermaid or "+b" in mermaid

    def test_from_example_file(self) -> None:
        course = parse_file(EXAMPLE_FILE)
        ls = course.to_learning_space()
        mermaid = hasse_mermaid(ls)
        assert "graph BT" in mermaid


class TestCourseJson:
    def test_valid_json(self) -> None:
        course = parse_file(EXAMPLE_FILE)
        result = course_json(course)
        data = json.loads(result)
        assert isinstance(data, dict)

    def test_contains_fields(self) -> None:
        course = parse_file(EXAMPLE_FILE)
        result = course_json(course)
        data = json.loads(result)
        assert "name" in data
        assert "description" in data
        assert "domain" in data
        assert "prerequisites" in data
        assert "states" in data

    def test_domain_structure(self) -> None:
        course = parse_file(EXAMPLE_FILE)
        result = course_json(course)
        data = json.loads(result)
        domain = data["domain"]
        assert "items" in domain
        assert "count" in domain
        assert domain["count"] == len(domain["items"])
        for item in domain["items"]:
            assert "id" in item
            assert "label" in item

    def test_prerequisites_structure(self) -> None:
        course = parse_file(EXAMPLE_FILE)
        result = course_json(course)
        data = json.loads(result)
        prereqs = data["prerequisites"]
        assert "edges" in prereqs
        assert "count" in prereqs
        assert prereqs["count"] == len(prereqs["edges"])

    def test_states_structure(self) -> None:
        course = parse_file(EXAMPLE_FILE)
        result = course_json(course)
        data = json.loads(result)
        states = data["states"]
        assert "sets" in states
        assert "count" in states
        assert states["count"] == len(states["sets"])
        # Each state is a list of item IDs
        for state_set in states["sets"]:
            assert isinstance(state_set, list)
