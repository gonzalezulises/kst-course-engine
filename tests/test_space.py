"""Tests for kst_core.space — KnowledgeSpace and LearningSpace."""

from __future__ import annotations

import pytest

from kst_core.domain import Domain, Item, KnowledgeState
from kst_core.space import KnowledgeSpace, LearningSpace


@pytest.fixture()
def abc_domain() -> Domain:
    return Domain(items=frozenset({Item(id="a"), Item(id="b"), Item(id="c")}))


@pytest.fixture()
def ab_domain() -> Domain:
    return Domain(items=frozenset({Item(id="a"), Item(id="b")}))


def _state(*ids: str) -> KnowledgeState:
    return KnowledgeState(items=frozenset(Item(id=i) for i in ids))


class TestKnowledgeSpace:
    def test_valid_power_set(self, ab_domain: Domain) -> None:
        """Power set of {a,b} is a valid knowledge space."""
        states = frozenset(
            {
                _state(),
                _state("a"),
                _state("b"),
                _state("a", "b"),
            }
        )
        ks = KnowledgeSpace(domain=ab_domain, states=states)
        assert len(ks.states) == 4

    def test_valid_linear_space(self, abc_domain: Domain) -> None:
        """Linear chain ∅ ⊂ {a} ⊂ {a,b} ⊂ {a,b,c}."""
        states = frozenset(
            {
                _state(),
                _state("a"),
                _state("a", "b"),
                _state("a", "b", "c"),
            }
        )
        ks = KnowledgeSpace(domain=abc_domain, states=states)
        assert len(ks.states) == 4

    def test_missing_empty_raises(self, ab_domain: Domain) -> None:
        with pytest.raises(ValueError, match="S1"):
            KnowledgeSpace(
                domain=ab_domain,
                states=frozenset({_state("a", "b")}),
            )

    def test_missing_full_raises(self, ab_domain: Domain) -> None:
        with pytest.raises(ValueError, match="S2"):
            KnowledgeSpace(
                domain=ab_domain,
                states=frozenset({_state()}),
            )

    def test_not_union_closed_raises(self, abc_domain: Domain) -> None:
        states = frozenset(
            {
                _state(),
                _state("a"),
                _state("b"),
                _state("a", "b", "c"),
            }
        )
        with pytest.raises(ValueError, match="S3"):
            KnowledgeSpace(domain=abc_domain, states=states)

    def test_state_outside_domain_raises(self, ab_domain: Domain) -> None:
        states = frozenset(
            {
                _state(),
                _state("a", "b"),
                _state("z"),
            }
        )
        with pytest.raises(ValueError, match="not in domain"):
            KnowledgeSpace(domain=ab_domain, states=states)

    def test_empty_states_raises(self, ab_domain: Domain) -> None:
        with pytest.raises(ValueError, match="at least one state"):
            KnowledgeSpace(domain=ab_domain, states=frozenset())

    def test_atoms(self, abc_domain: Domain) -> None:
        states = frozenset(
            {
                _state(),
                _state("a"),
                _state("b"),
                _state("a", "b"),
                _state("a", "b", "c"),
            }
        )
        ks = KnowledgeSpace(domain=abc_domain, states=states)
        assert ks.atoms == frozenset({_state("a"), _state("b")})

    def test_inner_fringe(self, abc_domain: Domain) -> None:
        states = frozenset(
            {
                _state(),
                _state("a"),
                _state("a", "b"),
                _state("a", "b", "c"),
            }
        )
        ks = KnowledgeSpace(domain=abc_domain, states=states)
        fringe = ks.inner_fringe(_state("a", "b"))
        assert fringe == frozenset({Item(id="b")})

    def test_inner_fringe_invalid_state(self, abc_domain: Domain) -> None:
        states = frozenset(
            {
                _state(),
                _state("a"),
                _state("a", "b"),
                _state("a", "b", "c"),
            }
        )
        ks = KnowledgeSpace(domain=abc_domain, states=states)
        with pytest.raises(ValueError, match="not in this knowledge space"):
            ks.inner_fringe(_state("b"))

    def test_outer_fringe(self, abc_domain: Domain) -> None:
        states = frozenset(
            {
                _state(),
                _state("a"),
                _state("a", "b"),
                _state("a", "b", "c"),
            }
        )
        ks = KnowledgeSpace(domain=abc_domain, states=states)
        fringe = ks.outer_fringe(_state("a"))
        assert fringe == frozenset({Item(id="b")})

    def test_outer_fringe_invalid_state(self, abc_domain: Domain) -> None:
        states = frozenset(
            {
                _state(),
                _state("a"),
                _state("a", "b"),
                _state("a", "b", "c"),
            }
        )
        ks = KnowledgeSpace(domain=abc_domain, states=states)
        with pytest.raises(ValueError, match="not in this knowledge space"):
            ks.outer_fringe(_state("b"))

    def test_gradation(self, abc_domain: Domain) -> None:
        states = frozenset(
            {
                _state(),
                _state("a"),
                _state("a", "b"),
                _state("a", "b", "c"),
            }
        )
        ks = KnowledgeSpace(domain=abc_domain, states=states)
        grad = ks.gradation()
        assert len(grad) == 4
        assert _state() in grad[0]
        assert _state("a") in grad[1]
        assert _state("a", "b") in grad[2]
        assert _state("a", "b", "c") in grad[3]


class TestLearningSpace:
    def test_valid_learning_space(self, abc_domain: Domain) -> None:
        states = frozenset(
            {
                _state(),
                _state("a"),
                _state("a", "b"),
                _state("a", "b", "c"),
            }
        )
        ls = LearningSpace(domain=abc_domain, states=states)
        assert len(ls.states) == 4

    def test_valid_branching(self, abc_domain: Domain) -> None:
        """Multiple paths: ∅→{a}→{a,b}→Q and ∅→{a}→{a,c}→Q."""
        states = frozenset(
            {
                _state(),
                _state("a"),
                _state("a", "b"),
                _state("a", "c"),
                _state("a", "b", "c"),
            }
        )
        ls = LearningSpace(domain=abc_domain, states=states)
        assert len(ls.states) == 5

    def test_not_accessible_raises(self, abc_domain: Domain) -> None:
        """State {a,c} is not accessible if only {a} and {a,b,c} also present."""
        states = frozenset(
            {
                _state(),
                _state("a"),
                _state("b", "c"),
                _state("a", "b", "c"),
            }
        )
        with pytest.raises(ValueError, match="Accessibility"):
            LearningSpace(domain=abc_domain, states=states)

    def test_missing_empty_raises(self, ab_domain: Domain) -> None:
        with pytest.raises(ValueError, match="S1"):
            LearningSpace(
                domain=ab_domain,
                states=frozenset({_state("a", "b")}),
            )

    def test_missing_full_raises(self, ab_domain: Domain) -> None:
        with pytest.raises(ValueError, match="S2"):
            LearningSpace(
                domain=ab_domain,
                states=frozenset({_state()}),
            )

    def test_not_union_closed_raises(self, abc_domain: Domain) -> None:
        """Union of {a} and {b} = {a,b} must be in states."""
        states = frozenset(
            {
                _state(),
                _state("a"),
                _state("b"),
                _state("a", "b", "c"),
            }
        )
        with pytest.raises(ValueError, match="S3"):
            LearningSpace(domain=abc_domain, states=states)

    def test_state_outside_domain_raises(self, ab_domain: Domain) -> None:
        states = frozenset(
            {
                _state(),
                _state("a", "b"),
                _state("z"),
            }
        )
        with pytest.raises(ValueError, match="not in domain"):
            LearningSpace(domain=ab_domain, states=states)

    def test_empty_states_raises(self, ab_domain: Domain) -> None:
        with pytest.raises(ValueError, match="at least one state"):
            LearningSpace(domain=ab_domain, states=frozenset())

    def test_atoms(self, abc_domain: Domain) -> None:
        states = frozenset(
            {
                _state(),
                _state("a"),
                _state("a", "b"),
                _state("a", "c"),
                _state("a", "b", "c"),
            }
        )
        ls = LearningSpace(domain=abc_domain, states=states)
        assert ls.atoms == frozenset({_state("a")})

    def test_inner_fringe(self, abc_domain: Domain) -> None:
        states = frozenset(
            {
                _state(),
                _state("a"),
                _state("a", "b"),
                _state("a", "b", "c"),
            }
        )
        ls = LearningSpace(domain=abc_domain, states=states)
        fringe = ls.inner_fringe(_state("a", "b"))
        assert fringe == frozenset({Item(id="b")})

    def test_inner_fringe_invalid(self, abc_domain: Domain) -> None:
        states = frozenset(
            {
                _state(),
                _state("a"),
                _state("a", "b"),
                _state("a", "b", "c"),
            }
        )
        ls = LearningSpace(domain=abc_domain, states=states)
        with pytest.raises(ValueError, match="not in this learning space"):
            ls.inner_fringe(_state("b"))

    def test_outer_fringe(self, abc_domain: Domain) -> None:
        states = frozenset(
            {
                _state(),
                _state("a"),
                _state("a", "b"),
                _state("a", "b", "c"),
            }
        )
        ls = LearningSpace(domain=abc_domain, states=states)
        fringe = ls.outer_fringe(_state())
        assert fringe == frozenset({Item(id="a")})

    def test_outer_fringe_invalid(self, abc_domain: Domain) -> None:
        states = frozenset(
            {
                _state(),
                _state("a"),
                _state("a", "b"),
                _state("a", "b", "c"),
            }
        )
        ls = LearningSpace(domain=abc_domain, states=states)
        with pytest.raises(ValueError, match="not in this learning space"):
            ls.outer_fringe(_state("c"))

    def test_learning_paths_linear(self, abc_domain: Domain) -> None:
        states = frozenset(
            {
                _state(),
                _state("a"),
                _state("a", "b"),
                _state("a", "b", "c"),
            }
        )
        ls = LearningSpace(domain=abc_domain, states=states)
        paths = ls.learning_paths()
        assert len(paths) == 1
        assert paths[0] == (Item(id="a"), Item(id="b"), Item(id="c"))

    def test_learning_paths_branching(self, abc_domain: Domain) -> None:
        states = frozenset(
            {
                _state(),
                _state("a"),
                _state("a", "b"),
                _state("a", "c"),
                _state("a", "b", "c"),
            }
        )
        ls = LearningSpace(domain=abc_domain, states=states)
        paths = ls.learning_paths()
        assert len(paths) == 2

    def test_gradation(self, abc_domain: Domain) -> None:
        states = frozenset(
            {
                _state(),
                _state("a"),
                _state("a", "b"),
                _state("a", "c"),
                _state("a", "b", "c"),
            }
        )
        ls = LearningSpace(domain=abc_domain, states=states)
        grad = ls.gradation()
        assert len(grad) == 4
        assert len(grad[2]) == 2
