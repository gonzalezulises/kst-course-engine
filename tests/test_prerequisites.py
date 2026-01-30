"""Tests for kst_core.prerequisites — SurmiseRelation and PrerequisiteGraph."""

from __future__ import annotations

import pytest

from kst_core.domain import Domain, Item, KnowledgeState
from kst_core.prerequisites import PrerequisiteGraph, SurmiseRelation


def _state(*ids: str) -> KnowledgeState:
    return KnowledgeState(items=frozenset(Item(id=i) for i in ids))


@pytest.fixture()
def abc_domain() -> Domain:
    return Domain(items=frozenset({Item(id="a"), Item(id="b"), Item(id="c")}))


@pytest.fixture()
def ab_domain() -> Domain:
    return Domain(items=frozenset({Item(id="a"), Item(id="b")}))


@pytest.fixture()
def linear_relation(abc_domain: Domain) -> SurmiseRelation:
    """a → b → c (a is prereq for b, b is prereq for c)."""
    return SurmiseRelation(
        domain=abc_domain,
        pairs=frozenset(
            {
                ("a", "a"),
                ("b", "b"),
                ("c", "c"),
                ("a", "b"),
                ("b", "c"),
                ("a", "c"),
            }
        ),
    )


@pytest.fixture()
def linear_graph(abc_domain: Domain) -> PrerequisiteGraph:
    return PrerequisiteGraph(
        domain=abc_domain,
        edges=frozenset({("a", "b"), ("b", "c")}),
    )


class TestSurmiseRelation:
    def test_valid_relation(self, linear_relation: SurmiseRelation) -> None:
        assert len(linear_relation.pairs) == 6

    def test_identity_relation(self, abc_domain: Domain) -> None:
        """Just reflexive pairs — no prerequisites."""
        pairs = frozenset({("a", "a"), ("b", "b"), ("c", "c")})
        sr = SurmiseRelation(domain=abc_domain, pairs=pairs)
        assert len(sr.pairs) == 3

    def test_missing_reflexivity_raises(self, abc_domain: Domain) -> None:
        with pytest.raises(ValueError, match="Reflexivity"):
            SurmiseRelation(
                domain=abc_domain,
                pairs=frozenset({("a", "a"), ("b", "b")}),
            )

    def test_missing_transitivity_raises(self, abc_domain: Domain) -> None:
        with pytest.raises(ValueError, match="Transitivity"):
            SurmiseRelation(
                domain=abc_domain,
                pairs=frozenset(
                    {
                        ("a", "a"),
                        ("b", "b"),
                        ("c", "c"),
                        ("a", "b"),
                        ("b", "c"),
                        # missing (a, c)
                    }
                ),
            )

    def test_invalid_item_raises(self, abc_domain: Domain) -> None:
        with pytest.raises(ValueError, match="not in domain"):
            SurmiseRelation(
                domain=abc_domain,
                pairs=frozenset({("a", "a"), ("b", "b"), ("c", "c"), ("z", "a")}),
            )

    def test_prerequisites_of(self, linear_relation: SurmiseRelation) -> None:
        assert linear_relation.prerequisites_of("c") == frozenset({"a", "b"})
        assert linear_relation.prerequisites_of("b") == frozenset({"a"})
        assert linear_relation.prerequisites_of("a") == frozenset()

    def test_dependents_of(self, linear_relation: SurmiseRelation) -> None:
        assert linear_relation.dependents_of("a") == frozenset({"b", "c"})
        assert linear_relation.dependents_of("c") == frozenset()

    def test_is_downset(self, linear_relation: SurmiseRelation) -> None:
        assert linear_relation.is_downset(_state())
        assert linear_relation.is_downset(_state("a"))
        assert linear_relation.is_downset(_state("a", "b"))
        assert linear_relation.is_downset(_state("a", "b", "c"))
        assert not linear_relation.is_downset(_state("b"))
        assert not linear_relation.is_downset(_state("c"))
        assert not linear_relation.is_downset(_state("b", "c"))

    def test_to_knowledge_space_states(self, linear_relation: SurmiseRelation) -> None:
        states = linear_relation.to_knowledge_space_states()
        expected = frozenset(
            {
                _state(),
                _state("a"),
                _state("a", "b"),
                _state("a", "b", "c"),
            }
        )
        assert states == expected

    def test_identity_yields_power_set(self, ab_domain: Domain) -> None:
        """Identity relation (no prereqs) yields the full power set."""
        pairs = frozenset({("a", "a"), ("b", "b")})
        sr = SurmiseRelation(domain=ab_domain, pairs=pairs)
        states = sr.to_knowledge_space_states()
        assert len(states) == 4  # 2^2


class TestPrerequisiteGraph:
    def test_valid_dag(self, linear_graph: PrerequisiteGraph) -> None:
        assert len(linear_graph.edges) == 2

    def test_empty_edges(self, abc_domain: Domain) -> None:
        pg = PrerequisiteGraph(domain=abc_domain, edges=frozenset())
        assert len(pg.edges) == 0

    def test_cycle_raises(self, abc_domain: Domain) -> None:
        with pytest.raises(ValueError, match="acyclic"):
            PrerequisiteGraph(
                domain=abc_domain,
                edges=frozenset({("a", "b"), ("b", "c"), ("c", "a")}),
            )

    def test_self_loop_raises(self, abc_domain: Domain) -> None:
        with pytest.raises(ValueError, match="Self-loop"):
            PrerequisiteGraph(
                domain=abc_domain,
                edges=frozenset({("a", "a")}),
            )

    def test_invalid_item_raises(self, abc_domain: Domain) -> None:
        with pytest.raises(ValueError, match="not in domain"):
            PrerequisiteGraph(
                domain=abc_domain,
                edges=frozenset({("a", "z")}),
            )

    def test_topological_orders(self, linear_graph: PrerequisiteGraph) -> None:
        orders = list(linear_graph.topological_orders())
        assert len(orders) == 1
        assert orders[0] == ["a", "b", "c"]

    def test_to_surmise_relation(self, linear_graph: PrerequisiteGraph) -> None:
        sr = linear_graph.to_surmise_relation()
        assert ("a", "c") in sr.pairs
        assert ("a", "b") in sr.pairs
        assert ("b", "c") in sr.pairs

    def test_critical_path(self, linear_graph: PrerequisiteGraph) -> None:
        path = linear_graph.critical_path()
        assert path == ["a", "b", "c"]

    def test_critical_path_no_edges(self, abc_domain: Domain) -> None:
        pg = PrerequisiteGraph(domain=abc_domain, edges=frozenset())
        path = pg.critical_path()
        assert len(path) == 1

    def test_longest_path_length(self, linear_graph: PrerequisiteGraph) -> None:
        assert linear_graph.longest_path_length() == 2

    def test_longest_path_length_no_edges(self, abc_domain: Domain) -> None:
        pg = PrerequisiteGraph(domain=abc_domain, edges=frozenset())
        assert pg.longest_path_length() == 0

    def test_direct_prerequisites(self, linear_graph: PrerequisiteGraph) -> None:
        assert linear_graph.direct_prerequisites("b") == frozenset({"a"})
        assert linear_graph.direct_prerequisites("c") == frozenset({"b"})
        assert linear_graph.direct_prerequisites("a") == frozenset()

    def test_direct_dependents(self, linear_graph: PrerequisiteGraph) -> None:
        assert linear_graph.direct_dependents("a") == frozenset({"b"})
        assert linear_graph.direct_dependents("c") == frozenset()

    def test_birkhoff_correspondence(self, linear_graph: PrerequisiteGraph) -> None:
        """Birkhoff theorem: DAG → surmise → knowledge space states
        should equal the set of downsets."""
        sr = linear_graph.to_surmise_relation()
        states = sr.to_knowledge_space_states()
        expected = frozenset(
            {
                _state(),
                _state("a"),
                _state("a", "b"),
                _state("a", "b", "c"),
            }
        )
        assert states == expected
