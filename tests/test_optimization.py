"""Tests for kst_core.optimization — optimization algorithms."""

from __future__ import annotations

import textwrap

import numpy as np
import pytest

from kst_core.assessment import BLIMParameters, simulate_responses
from kst_core.domain import Domain, Item, KnowledgeState
from kst_core.estimation import ResponseData
from kst_core.learning import LearningRate
from kst_core.optimization import (
    CalibrationResult,
    DifficultyReport,
    ItemCalibration,
    ItemDifficulty,
    TeachingPlan,
    TeachingStep,
    TrajectoryData,
    TunedRates,
    _check_identifiability,
    calibrate_parameters,
    estimate_item_difficulty,
    optimal_teaching_sequence,
    tune_learning_rates,
)
from kst_core.parser import parse_yaml

LINEAR_YAML = textwrap.dedent("""\
    domain:
      name: "Linear"
      items:
        - id: "a"
        - id: "b"
        - id: "c"
    prerequisites:
      edges:
        - ["a", "b"]
        - ["b", "c"]
""")

DIAMOND_YAML = textwrap.dedent("""\
    domain:
      name: "Diamond"
      items:
        - id: "a"
        - id: "b"
        - id: "c"
        - id: "d"
    prerequisites:
      edges:
        - ["a", "b"]
        - ["a", "c"]
        - ["b", "d"]
        - ["c", "d"]
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
def diamond_course() -> object:
    return parse_yaml(DIAMOND_YAML)


@pytest.fixture()
def minimal_course() -> object:
    return parse_yaml(MINIMAL_YAML)


# ---------------------------------------------------------------------------
# Type model tests
# ---------------------------------------------------------------------------


class TestItemCalibration:
    def test_create(self) -> None:
        ic = ItemCalibration(item_id="a", beta=0.1, eta=0.1)
        assert ic.item_id == "a"
        assert ic.beta == 0.1

    def test_frozen(self) -> None:
        ic = ItemCalibration(item_id="a", beta=0.1, eta=0.1)
        with pytest.raises(Exception):  # noqa: B017
            ic.item_id = "b"  # type: ignore[misc]


class TestTeachingStep:
    def test_create(self) -> None:
        step = TeachingStep(
            item_id="a",
            from_state_ids=frozenset(),
            to_state_ids=frozenset({"a"}),
            expected_remaining=3.0,
        )
        assert step.item_id == "a"
        assert step.expected_remaining == 3.0


class TestTeachingPlan:
    def test_create(self) -> None:
        plan = TeachingPlan(steps=(), total_expected_steps=0.0)
        assert plan.total_expected_steps == 0.0


class TestItemDifficulty:
    def test_create(self) -> None:
        d = ItemDifficulty(
            item_id="a",
            structural_depth=0,
            structural_difficulty=0.0,
            combined_difficulty=0.0,
        )
        assert d.item_id == "a"
        assert d.empirical_difficulty is None
        assert d.blim_difficulty is None

    def test_with_optional(self) -> None:
        d = ItemDifficulty(
            item_id="a",
            structural_depth=2,
            structural_difficulty=1.0,
            empirical_difficulty=0.3,
            blim_difficulty=1.1,
            combined_difficulty=0.5,
        )
        assert d.empirical_difficulty == 0.3
        assert d.blim_difficulty == 1.1


class TestDifficultyReport:
    def test_create(self) -> None:
        r = DifficultyReport(items=(), method="structural")
        assert r.method == "structural"


class TestTrajectoryData:
    def test_create(self) -> None:
        domain = Domain(items=frozenset({Item(id="a")}))
        td = TrajectoryData(
            domain=domain,
            trajectories=((frozenset(), frozenset({"a"})),),
        )
        assert len(td.trajectories) == 1


class TestTunedRates:
    def test_create(self) -> None:
        domain = Domain(items=frozenset({Item(id="a")}))
        rates = LearningRate(domain=domain, rates={"a": 1.0})
        tr = TunedRates(
            rates=rates,
            log_likelihood=-1.0,
            converged=True,
            iterations=10,
        )
        assert tr.converged


class TestCalibrationResult:
    def test_create(self) -> None:
        domain = Domain(items=frozenset({Item(id="a")}))
        params = BLIMParameters.uniform(domain)
        cr = CalibrationResult(
            params=params,
            item_calibrations=(ItemCalibration(item_id="a", beta=0.1, eta=0.1),),
            log_likelihood=-10.0,
            converged=True,
            restarts=5,
            identifiable=True,
        )
        assert cr.converged
        assert cr.identifiable


# ---------------------------------------------------------------------------
# _check_identifiability tests
# ---------------------------------------------------------------------------


class TestCheckIdentifiability:
    def test_single_restart(self) -> None:
        assert _check_identifiability([{"a": 0.1}], [{"a": 0.1}]) is True

    def test_consistent(self) -> None:
        betas = [{"a": 0.1, "b": 0.1}, {"a": 0.1, "b": 0.1}]
        etas = [{"a": 0.1, "b": 0.1}, {"a": 0.1, "b": 0.1}]
        assert _check_identifiability(betas, etas) is True

    def test_divergent_beta(self) -> None:
        betas = [{"a": 0.01}, {"a": 0.49}]
        etas = [{"a": 0.1}, {"a": 0.1}]
        assert _check_identifiability(betas, etas) is False

    def test_divergent_eta(self) -> None:
        betas = [{"a": 0.1}, {"a": 0.1}]
        etas = [{"a": 0.01}, {"a": 0.49}]
        assert _check_identifiability(betas, etas) is False


# ---------------------------------------------------------------------------
# calibrate_parameters tests
# ---------------------------------------------------------------------------


class TestCalibrateParameters:
    def test_basic(self, linear_course: object) -> None:
        course = linear_course  # type: ignore[assignment]
        rng = np.random.default_rng(42)
        params = BLIMParameters.uniform(course.domain)  # type: ignore[union-attr]
        state_list = sorted(course.states, key=lambda s: (len(s), sorted(s.item_ids)))  # type: ignore[union-attr]

        patterns = []
        for _ in range(50):
            true_state = state_list[int(rng.integers(len(state_list)))]
            resp = simulate_responses(true_state, params, rng=rng)
            patterns.append(resp)

        data = ResponseData(domain=course.domain, patterns=tuple(patterns))  # type: ignore[union-attr]
        result = calibrate_parameters(
            course.domain,  # type: ignore[union-attr]
            course.states,  # type: ignore[union-attr]
            data,
            restarts=2,
            max_iterations=50,
        )
        assert isinstance(result, CalibrationResult)
        assert result.restarts == 2
        assert result.log_likelihood < 0  # negative log-likelihood
        assert len(result.item_calibrations) == 3

    def test_minimal(self, minimal_course: object) -> None:
        course = minimal_course  # type: ignore[assignment]
        data = ResponseData(
            domain=course.domain,  # type: ignore[union-attr]
            patterns=({"a": True}, {"a": False}, {"a": True}),
        )
        result = calibrate_parameters(
            course.domain,  # type: ignore[union-attr]
            course.states,  # type: ignore[union-attr]
            data,
            restarts=2,
            max_iterations=20,
        )
        assert result.converged or result.log_likelihood > -100


# ---------------------------------------------------------------------------
# optimal_teaching_sequence tests
# ---------------------------------------------------------------------------


class TestOptimalTeachingSequence:
    def test_linear(self, linear_course: object) -> None:
        course = linear_course  # type: ignore[assignment]
        ls = course.to_learning_space()  # type: ignore[union-attr]
        plan = optimal_teaching_sequence(ls)
        assert isinstance(plan, TeachingPlan)
        assert len(plan.steps) == 3
        # Linear: must teach a, then b, then c
        assert plan.steps[0].item_id == "a"
        assert plan.steps[1].item_id == "b"
        assert plan.steps[2].item_id == "c"
        assert plan.total_expected_steps == 3.0

    def test_diamond(self, diamond_course: object) -> None:
        course = diamond_course  # type: ignore[assignment]
        ls = course.to_learning_space()  # type: ignore[union-attr]
        plan = optimal_teaching_sequence(ls)
        assert len(plan.steps) == 4
        assert plan.steps[0].item_id == "a"
        # b and c can be in either order
        middle_ids = {plan.steps[1].item_id, plan.steps[2].item_id}
        assert middle_ids == {"b", "c"}
        assert plan.steps[3].item_id == "d"

    def test_with_rates(self, diamond_course: object) -> None:
        course = diamond_course  # type: ignore[assignment]
        ls = course.to_learning_space()  # type: ignore[union-attr]
        rates = LearningRate(
            domain=course.domain,  # type: ignore[union-attr]
            rates={"a": 1.0, "b": 2.0, "c": 0.5, "d": 1.0},
        )
        plan = optimal_teaching_sequence(ls, rates=rates)
        assert len(plan.steps) == 4
        # With rates, still produces a valid plan
        middle_ids = {plan.steps[1].item_id, plan.steps[2].item_id}
        assert middle_ids == {"b", "c"}

    def test_minimal(self, minimal_course: object) -> None:
        course = minimal_course  # type: ignore[assignment]
        ls = course.to_learning_space()  # type: ignore[union-attr]
        plan = optimal_teaching_sequence(ls)
        assert len(plan.steps) == 1
        assert plan.steps[0].item_id == "a"

    def test_custom_start(self, linear_course: object) -> None:
        course = linear_course  # type: ignore[assignment]
        ls = course.to_learning_space()  # type: ignore[union-attr]
        item_a = course.domain.get_item("a")  # type: ignore[union-attr]
        start = KnowledgeState(items=frozenset({item_a}))
        plan = optimal_teaching_sequence(ls, start=start)
        assert len(plan.steps) == 2
        assert plan.steps[0].item_id == "b"

    def test_step_state_ids(self, linear_course: object) -> None:
        course = linear_course  # type: ignore[assignment]
        ls = course.to_learning_space()  # type: ignore[union-attr]
        plan = optimal_teaching_sequence(ls)
        assert plan.steps[0].from_state_ids == frozenset()
        assert plan.steps[0].to_state_ids == frozenset({"a"})
        assert plan.steps[1].from_state_ids == frozenset({"a"})
        assert plan.steps[1].to_state_ids == frozenset({"a", "b"})


# ---------------------------------------------------------------------------
# estimate_item_difficulty tests
# ---------------------------------------------------------------------------


class TestEstimateItemDifficulty:
    def test_structural_only(self, linear_course: object) -> None:
        course = linear_course  # type: ignore[assignment]
        report = estimate_item_difficulty(
            course.domain,  # type: ignore[union-attr]
            course.prerequisite_graph,  # type: ignore[union-attr]
        )
        assert isinstance(report, DifficultyReport)
        assert report.method == "structural"
        assert len(report.items) == 3
        # Item a has depth 0, b has depth 1, c has depth 2
        by_id = {d.item_id: d for d in report.items}
        assert by_id["a"].structural_depth == 0
        assert by_id["b"].structural_depth == 1
        assert by_id["c"].structural_depth == 2
        # c should be hardest
        assert by_id["c"].combined_difficulty > by_id["a"].combined_difficulty

    def test_with_data(self, linear_course: object) -> None:
        course = linear_course  # type: ignore[assignment]
        rng = np.random.default_rng(42)
        params = BLIMParameters.uniform(course.domain)  # type: ignore[union-attr]
        state_list = sorted(course.states, key=lambda s: (len(s), sorted(s.item_ids)))  # type: ignore[union-attr]

        patterns = []
        for _ in range(20):
            true_state = state_list[int(rng.integers(len(state_list)))]
            resp = simulate_responses(true_state, params, rng=rng)
            patterns.append(resp)

        data = ResponseData(domain=course.domain, patterns=tuple(patterns))  # type: ignore[union-attr]
        report = estimate_item_difficulty(
            course.domain,  # type: ignore[union-attr]
            course.prerequisite_graph,  # type: ignore[union-attr]
            data=data,
        )
        assert "empirical" in report.method
        for item in report.items:
            assert item.empirical_difficulty is not None

    def test_with_params(self, linear_course: object) -> None:
        course = linear_course  # type: ignore[assignment]
        params = BLIMParameters.uniform(course.domain)  # type: ignore[union-attr]
        report = estimate_item_difficulty(
            course.domain,  # type: ignore[union-attr]
            course.prerequisite_graph,  # type: ignore[union-attr]
            params=params,
        )
        assert "blim" in report.method
        for item in report.items:
            assert item.blim_difficulty is not None

    def test_with_data_and_params(self, linear_course: object) -> None:
        course = linear_course  # type: ignore[assignment]
        params = BLIMParameters.uniform(course.domain)  # type: ignore[union-attr]
        data = ResponseData(
            domain=course.domain,  # type: ignore[union-attr]
            patterns=(
                {"a": True, "b": True, "c": False},
                {"a": True, "b": False, "c": False},
            ),
        )
        report = estimate_item_difficulty(
            course.domain,  # type: ignore[union-attr]
            course.prerequisite_graph,  # type: ignore[union-attr]
            data=data,
            params=params,
        )
        assert report.method == "structural+empirical+blim"

    def test_diamond_ordering(self, diamond_course: object) -> None:
        course = diamond_course  # type: ignore[assignment]
        report = estimate_item_difficulty(
            course.domain,  # type: ignore[union-attr]
            course.prerequisite_graph,  # type: ignore[union-attr]
        )
        by_id = {d.item_id: d for d in report.items}
        # d requires a, b, c transitively
        assert by_id["d"].structural_depth > by_id["a"].structural_depth

    def test_minimal(self, minimal_course: object) -> None:
        course = minimal_course  # type: ignore[assignment]
        report = estimate_item_difficulty(
            course.domain,  # type: ignore[union-attr]
            course.prerequisite_graph,  # type: ignore[union-attr]
        )
        assert len(report.items) == 1
        assert report.items[0].structural_depth == 0


# ---------------------------------------------------------------------------
# tune_learning_rates tests
# ---------------------------------------------------------------------------


class TestTuneLearningRates:
    def test_basic(self, linear_course: object) -> None:
        course = linear_course  # type: ignore[assignment]
        ls = course.to_learning_space()  # type: ignore[union-attr]

        # Generate synthetic trajectories
        trajectories: list[tuple[frozenset[str], ...]] = []
        for _ in range(20):
            trajectories.append(
                (
                    frozenset(),
                    frozenset({"a"}),
                    frozenset({"a", "b"}),
                    frozenset({"a", "b", "c"}),
                )
            )
        data = TrajectoryData(
            domain=course.domain,  # type: ignore[union-attr]
            trajectories=tuple(trajectories),
        )
        result = tune_learning_rates(ls, data, max_iterations=50)
        assert isinstance(result, TunedRates)
        assert result.iterations > 0

    def test_biased_rates(self, linear_course: object) -> None:
        course = linear_course  # type: ignore[assignment]
        ls = course.to_learning_space()  # type: ignore[union-attr]

        # Create trajectories where 'a' is always learned first
        trajectories: list[tuple[frozenset[str], ...]] = []
        for _ in range(30):
            trajectories.append(
                (
                    frozenset(),
                    frozenset({"a"}),
                    frozenset({"a", "b"}),
                    frozenset({"a", "b", "c"}),
                )
            )
        data = TrajectoryData(
            domain=course.domain,  # type: ignore[union-attr]
            trajectories=tuple(trajectories),
        )
        result = tune_learning_rates(ls, data, max_iterations=100)
        # All items have equal exposure in linear chain
        assert all(v > 0 for v in result.rates.rates.values())

    def test_convergence(self, minimal_course: object) -> None:
        course = minimal_course  # type: ignore[assignment]
        ls = course.to_learning_space()  # type: ignore[union-attr]
        trajectories = (
            (frozenset(), frozenset({"a"})),
            (frozenset(), frozenset({"a"})),
            (frozenset(), frozenset({"a"})),
        )
        data = TrajectoryData(
            domain=course.domain,  # type: ignore[union-attr]
            trajectories=trajectories,
        )
        result = tune_learning_rates(ls, data, max_iterations=100)
        assert result.rates.rates["a"] > 0

    def test_empty_fringe_state(self, linear_course: object) -> None:
        course = linear_course  # type: ignore[assignment]
        ls = course.to_learning_space()  # type: ignore[union-attr]
        # Include a trajectory with the full state (no fringe)
        trajectories = (
            (
                frozenset(),
                frozenset({"a"}),
                frozenset({"a", "b"}),
                frozenset({"a", "b", "c"}),
                frozenset({"a", "b", "c"}),
            ),
        )
        data = TrajectoryData(
            domain=course.domain,  # type: ignore[union-attr]
            trajectories=trajectories,
        )
        result = tune_learning_rates(ls, data, max_iterations=20)
        assert isinstance(result, TunedRates)

    def test_invalid_state_in_trajectory(self, linear_course: object) -> None:
        """Trajectory includes a state not in the space (e.g. {b} without {a})."""
        course = linear_course  # type: ignore[assignment]
        ls = course.to_learning_space()  # type: ignore[union-attr]
        # {b} is NOT a valid state in a→b→c linear space
        trajectories = (
            (
                frozenset({"b"}),
                frozenset({"a", "b"}),
                frozenset({"a", "b", "c"}),
            ),
        )
        data = TrajectoryData(
            domain=course.domain,  # type: ignore[union-attr]
            trajectories=trajectories,
        )
        result = tune_learning_rates(ls, data, max_iterations=20)
        assert isinstance(result, TunedRates)

    def test_no_acquisition_trajectory(self, linear_course: object) -> None:
        """Trajectory with no actual acquisitions (same state repeated)."""
        course = linear_course  # type: ignore[assignment]
        ls = course.to_learning_space()  # type: ignore[union-attr]
        # Same state repeated — no items acquired
        trajectories = (
            (
                frozenset({"a"}),
                frozenset({"a"}),
                frozenset({"a"}),
            ),
        )
        data = TrajectoryData(
            domain=course.domain,  # type: ignore[union-attr]
            trajectories=trajectories,
        )
        result = tune_learning_rates(ls, data, max_iterations=20)
        assert isinstance(result, TunedRates)
        # Items never acquired should get default rate
        assert result.rates.rates["c"] > 0


# ---------------------------------------------------------------------------
# CLI optimize tests (added to test_cli.py via separate class)
# ---------------------------------------------------------------------------


class TestOptimizeCLI:
    """Test the optimize CLI command via test_optimization.py."""

    def test_difficulty_mode(self, capsys: pytest.CaptureFixture[str]) -> None:
        from kst_core.cli import main

        rc = main(["optimize", "examples/intro-pandas.kst.yaml", "--mode", "difficulty"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "Item Difficulty" in out
        assert "depth=" in out

    def test_teach_mode(self, capsys: pytest.CaptureFixture[str]) -> None:
        from kst_core.cli import main

        rc = main(["optimize", "examples/intro-pandas.kst.yaml", "--mode", "teach"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "Optimal Teaching Sequence" in out
        assert "Teach" in out

    def test_calibrate_no_data(self, capsys: pytest.CaptureFixture[str]) -> None:
        from kst_core.cli import main

        rc = main(["optimize", "examples/intro-pandas.kst.yaml", "--mode", "calibrate"])
        assert rc == 1
        err = capsys.readouterr().err
        assert "--data is required" in err

    def test_rates_no_data(self, capsys: pytest.CaptureFixture[str]) -> None:
        from kst_core.cli import main

        rc = main(["optimize", "examples/intro-pandas.kst.yaml", "--mode", "rates"])
        assert rc == 1

    def test_calibrate_with_data(self, capsys: pytest.CaptureFixture[str]) -> None:
        from kst_core.cli import main

        rc = main([
            "optimize",
            "examples/intro-pandas.kst.yaml",
            "--mode",
            "calibrate",
            "--data",
            "data.csv",
        ])
        assert rc == 1
        err = capsys.readouterr().err
        assert "not yet implemented" in err

    def test_file_not_found(self, capsys: pytest.CaptureFixture[str]) -> None:
        from kst_core.cli import main

        rc = main(["optimize", "nonexistent.kst.yaml", "--mode", "difficulty"])
        assert rc == 1
        err = capsys.readouterr().err
        assert "Error" in err
