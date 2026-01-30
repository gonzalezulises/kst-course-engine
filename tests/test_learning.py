"""Tests for kst_core.learning — Markov learning model."""

from __future__ import annotations

import numpy as np
import pytest

from kst_core.domain import Domain, Item, KnowledgeState
from kst_core.learning import LearningModel, LearningRate
from kst_core.space import LearningSpace


def _state(*ids: str) -> KnowledgeState:
    return KnowledgeState(items=frozenset(Item(id=i) for i in ids))


def _item(id: str) -> Item:
    return Item(id=id)


@pytest.fixture()
def abc_domain() -> Domain:
    return Domain(items=frozenset({_item("a"), _item("b"), _item("c")}))


@pytest.fixture()
def linear_space(abc_domain: Domain) -> LearningSpace:
    """Linear learning space: {} -> {a} -> {a,b} -> {a,b,c}."""
    return LearningSpace(
        domain=abc_domain,
        states=frozenset(
            {
                _state(),
                _state("a"),
                _state("a", "b"),
                _state("a", "b", "c"),
            }
        ),
    )


@pytest.fixture()
def branching_space(abc_domain: Domain) -> LearningSpace:
    """Branching space: {} -> {a} -> {a,b} or {a,c} -> {a,b,c}."""
    return LearningSpace(
        domain=abc_domain,
        states=frozenset(
            {
                _state(),
                _state("a"),
                _state("a", "b"),
                _state("a", "c"),
                _state("a", "b", "c"),
            }
        ),
    )


@pytest.fixture()
def uniform_rates(abc_domain: Domain) -> LearningRate:
    return LearningRate.uniform(abc_domain)


class TestLearningRate:
    def test_uniform(self, abc_domain: Domain) -> None:
        rates = LearningRate.uniform(abc_domain, rate=2.0)
        assert rates.rates["a"] == 2.0
        assert rates.rates["b"] == 2.0

    def test_uniform_default(self, abc_domain: Domain) -> None:
        rates = LearningRate.uniform(abc_domain)
        assert all(r == 1.0 for r in rates.rates.values())

    def test_custom_rates(self, abc_domain: Domain) -> None:
        rates = LearningRate(
            domain=abc_domain,
            rates={"a": 1.0, "b": 2.0, "c": 0.5},
        )
        assert rates.rates["b"] == 2.0

    def test_keys_mismatch(self, abc_domain: Domain) -> None:
        with pytest.raises(ValueError, match="do not match"):
            LearningRate(
                domain=abc_domain,
                rates={"a": 1.0, "b": 2.0},
            )

    def test_nonpositive_rate(self, abc_domain: Domain) -> None:
        with pytest.raises(ValueError, match="positive"):
            LearningRate(
                domain=abc_domain,
                rates={"a": 1.0, "b": 0.0, "c": 1.0},
            )

    def test_negative_rate(self, abc_domain: Domain) -> None:
        with pytest.raises(ValueError, match="positive"):
            LearningRate(
                domain=abc_domain,
                rates={"a": 1.0, "b": -1.0, "c": 1.0},
            )


class TestLearningModel:
    def test_construction(
        self,
        linear_space: LearningSpace,
        uniform_rates: LearningRate,
    ) -> None:
        model = LearningModel(space=linear_space, rates=uniform_rates)
        assert model.space == linear_space

    def test_domain_mismatch(self) -> None:
        domain1 = Domain(items=frozenset({_item("a")}))
        domain2 = Domain(items=frozenset({_item("x")}))
        space = LearningSpace(
            domain=domain1,
            states=frozenset({_state(), _state("a")}),
        )
        rates = LearningRate(domain=domain2, rates={"x": 1.0})
        with pytest.raises(ValueError, match="must match"):
            LearningModel(space=space, rates=rates)


class TestTransitionProbs:
    def test_empty_state_linear(
        self,
        linear_space: LearningSpace,
        uniform_rates: LearningRate,
    ) -> None:
        """From {}, only 'a' is learnable in linear space."""
        model = LearningModel(space=linear_space, rates=uniform_rates)
        probs = model.transition_probs(_state())
        assert len(probs) == 1
        assert probs[_state("a")] == pytest.approx(1.0)

    def test_absorbing_state(
        self,
        linear_space: LearningSpace,
        uniform_rates: LearningRate,
    ) -> None:
        """Full state self-loops with probability 1."""
        model = LearningModel(space=linear_space, rates=uniform_rates)
        full = _state("a", "b", "c")
        probs = model.transition_probs(full)
        assert probs == {full: 1.0}

    def test_branching_state(
        self,
        branching_space: LearningSpace,
        uniform_rates: LearningRate,
    ) -> None:
        """From {a}, both b and c are learnable with equal rates."""
        model = LearningModel(space=branching_space, rates=uniform_rates)
        probs = model.transition_probs(_state("a"))
        assert len(probs) == 2
        assert probs[_state("a", "b")] == pytest.approx(0.5)
        assert probs[_state("a", "c")] == pytest.approx(0.5)

    def test_unequal_rates(
        self,
        branching_space: LearningSpace,
        abc_domain: Domain,
    ) -> None:
        """Unequal rates should weight transitions."""
        rates = LearningRate(
            domain=abc_domain,
            rates={"a": 1.0, "b": 3.0, "c": 1.0},
        )
        model = LearningModel(space=branching_space, rates=rates)
        probs = model.transition_probs(_state("a"))
        # b has rate 3, c has rate 1, total=4
        assert probs[_state("a", "b")] == pytest.approx(0.75)
        assert probs[_state("a", "c")] == pytest.approx(0.25)

    def test_probabilities_sum_to_one(
        self,
        branching_space: LearningSpace,
        uniform_rates: LearningRate,
    ) -> None:
        model = LearningModel(space=branching_space, rates=uniform_rates)
        for state in branching_space.states:
            probs = model.transition_probs(state)
            assert sum(probs.values()) == pytest.approx(1.0)


class TestTransitionMatrix:
    def test_shape(
        self,
        linear_space: LearningSpace,
        uniform_rates: LearningRate,
    ) -> None:
        model = LearningModel(space=linear_space, rates=uniform_rates)
        states, matrix = model.transition_matrix()
        assert matrix.shape == (4, 4)
        assert len(states) == 4

    def test_rows_sum_to_one(
        self,
        branching_space: LearningSpace,
        uniform_rates: LearningRate,
    ) -> None:
        model = LearningModel(space=branching_space, rates=uniform_rates)
        _, matrix = model.transition_matrix()
        row_sums = np.sum(matrix, axis=1)
        np.testing.assert_allclose(row_sums, 1.0)

    def test_absorbing_row(
        self,
        linear_space: LearningSpace,
        uniform_rates: LearningRate,
    ) -> None:
        """The full state row should be [0, ..., 0, 1]."""
        model = LearningModel(space=linear_space, rates=uniform_rates)
        states, matrix = model.transition_matrix()
        full_idx = next(i for i, s in enumerate(states) if s == _state("a", "b", "c"))
        assert matrix[full_idx, full_idx] == pytest.approx(1.0)
        assert sum(matrix[full_idx]) == pytest.approx(1.0)

    def test_state_ordering(
        self,
        linear_space: LearningSpace,
        uniform_rates: LearningRate,
    ) -> None:
        """States sorted by cardinality."""
        model = LearningModel(space=linear_space, rates=uniform_rates)
        states, _ = model.transition_matrix()
        sizes = [len(s) for s in states]
        assert sizes == sorted(sizes)


class TestExpectedSteps:
    def test_linear_space(
        self,
        linear_space: LearningSpace,
        uniform_rates: LearningRate,
    ) -> None:
        """In a linear space with n items, expected steps from {} = n."""
        model = LearningModel(space=linear_space, rates=uniform_rates)
        expected = model.expected_steps()

        # From {}: 3 steps (deterministic linear chain)
        assert expected[_state()] == pytest.approx(3.0)
        # From {a}: 2 steps
        assert expected[_state("a")] == pytest.approx(2.0)
        # From {a,b}: 1 step
        assert expected[_state("a", "b")] == pytest.approx(1.0)
        # Full state: 0 steps
        assert expected[_state("a", "b", "c")] == pytest.approx(0.0)

    def test_branching_fewer_steps(
        self,
        branching_space: LearningSpace,
        uniform_rates: LearningRate,
    ) -> None:
        """Branching should give fewer expected steps than linear (more paths)."""
        model = LearningModel(space=branching_space, rates=uniform_rates)
        expected = model.expected_steps()

        # From {a}: can go to {a,b} or {a,c}, each with prob 0.5
        # Then 1 step to full. So expected from {a} = 1 + 1 = 2
        assert expected[_state("a")] == pytest.approx(2.0)

        # From {}: must go to {a} (only option), so 1 + E[{a}] = 3
        assert expected[_state()] == pytest.approx(3.0)

    def test_all_values_nonnegative(
        self,
        branching_space: LearningSpace,
        uniform_rates: LearningRate,
    ) -> None:
        model = LearningModel(space=branching_space, rates=uniform_rates)
        expected = model.expected_steps()
        assert all(v >= 0.0 for v in expected.values())

    def test_monotone_with_cardinality(
        self,
        linear_space: LearningSpace,
        uniform_rates: LearningRate,
    ) -> None:
        """Larger states should have fewer expected steps."""
        model = LearningModel(space=linear_space, rates=uniform_rates)
        expected = model.expected_steps()
        states_by_size = sorted(expected.keys(), key=len)
        values = [expected[s] for s in states_by_size]
        # Expected steps should be non-increasing
        for i in range(len(values) - 1):
            assert values[i] >= values[i + 1]

    def test_single_item(self) -> None:
        """Single-item domain: 1 step from {} to {x}."""
        domain = Domain(items=frozenset({_item("x")}))
        space = LearningSpace(
            domain=domain,
            states=frozenset({_state(), _state("x")}),
        )
        rates = LearningRate.uniform(domain)
        model = LearningModel(space=space, rates=rates)
        expected = model.expected_steps()
        assert expected[_state()] == pytest.approx(1.0)
        assert expected[_state("x")] == pytest.approx(0.0)


class TestSimulateTrajectory:
    def test_reaches_mastery(
        self,
        linear_space: LearningSpace,
        uniform_rates: LearningRate,
    ) -> None:
        model = LearningModel(space=linear_space, rates=uniform_rates)
        traj = model.simulate_trajectory(rng=np.random.default_rng(42))
        assert traj[0] == _state()
        assert traj[-1] == _state("a", "b", "c")

    def test_monotone_growth(
        self,
        branching_space: LearningSpace,
        uniform_rates: LearningRate,
    ) -> None:
        """Each state in trajectory should be a superset of the previous."""
        model = LearningModel(space=branching_space, rates=uniform_rates)
        traj = model.simulate_trajectory(rng=np.random.default_rng(0))
        for i in range(1, len(traj)):
            assert traj[i - 1].items.issubset(traj[i].items)

    def test_all_states_valid(
        self,
        branching_space: LearningSpace,
        uniform_rates: LearningRate,
    ) -> None:
        model = LearningModel(space=branching_space, rates=uniform_rates)
        traj = model.simulate_trajectory(rng=np.random.default_rng(7))
        for state in traj:
            assert state in branching_space.states

    def test_custom_start(
        self,
        linear_space: LearningSpace,
        uniform_rates: LearningRate,
    ) -> None:
        model = LearningModel(space=linear_space, rates=uniform_rates)
        traj = model.simulate_trajectory(start=_state("a"), rng=np.random.default_rng(0))
        assert traj[0] == _state("a")
        assert traj[-1] == _state("a", "b", "c")

    def test_max_steps(
        self,
        linear_space: LearningSpace,
        uniform_rates: LearningRate,
    ) -> None:
        model = LearningModel(space=linear_space, rates=uniform_rates)
        traj = model.simulate_trajectory(rng=np.random.default_rng(0), max_steps=1)
        assert len(traj) <= 2  # start + at most 1 step

    def test_default_rng(
        self,
        linear_space: LearningSpace,
        uniform_rates: LearningRate,
    ) -> None:
        model = LearningModel(space=linear_space, rates=uniform_rates)
        traj = model.simulate_trajectory()
        assert len(traj) >= 2

    def test_start_at_mastery(
        self,
        linear_space: LearningSpace,
        uniform_rates: LearningRate,
    ) -> None:
        model = LearningModel(space=linear_space, rates=uniform_rates)
        full = _state("a", "b", "c")
        traj = model.simulate_trajectory(start=full)
        assert traj == (full,)


class TestOptimalTeachingItem:
    def test_linear_space(
        self,
        linear_space: LearningSpace,
        uniform_rates: LearningRate,
    ) -> None:
        """In linear space, there's only one option at each state."""
        model = LearningModel(space=linear_space, rates=uniform_rates)
        assert model.optimal_teaching_item(_state()) == "a"
        assert model.optimal_teaching_item(_state("a")) == "b"
        assert model.optimal_teaching_item(_state("a", "b")) == "c"

    def test_branching_favors_lower_expected(
        self,
        branching_space: LearningSpace,
        abc_domain: Domain,
    ) -> None:
        """With unequal rates, optimal item changes."""
        # Give 'b' a much higher rate than 'c'
        rates = LearningRate(
            domain=abc_domain,
            rates={"a": 1.0, "b": 10.0, "c": 1.0},
        )
        model = LearningModel(space=branching_space, rates=rates)
        # From {a}: both {a,b} and {a,c} lead to 1 step to mastery
        # Expected steps are the same, so either could be optimal
        item = model.optimal_teaching_item(_state("a"))
        assert item in {"b", "c"}

    def test_full_state_raises(
        self,
        linear_space: LearningSpace,
        uniform_rates: LearningRate,
    ) -> None:
        model = LearningModel(space=linear_space, rates=uniform_rates)
        with pytest.raises(ValueError, match="full mastery"):
            model.optimal_teaching_item(_state("a", "b", "c"))


class TestEndToEnd:
    def test_yaml_to_learning_model(self) -> None:
        """Full pipeline: YAML -> course -> learning model."""
        from kst_core import parse_file

        course = parse_file("examples/intro-pandas.kst.yaml")
        space = course.to_learning_space()
        rates = LearningRate.uniform(course.domain)
        model = LearningModel(space=space, rates=rates)

        # Expected steps
        expected = model.expected_steps()
        empty = KnowledgeState()
        assert expected[empty] > 0
        assert expected[course.domain.full_state] == 0.0

        # Simulate
        traj = model.simulate_trajectory(rng=np.random.default_rng(42))
        assert traj[0] == empty
        assert traj[-1] == course.domain.full_state

        # Optimal teaching
        item = model.optimal_teaching_item(empty)
        assert item in course.domain.item_ids
