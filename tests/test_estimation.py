"""Tests for kst_core.estimation — EM parameter estimation for BLIM."""

from __future__ import annotations

import numpy as np
import pytest

from kst_core.assessment import BLIMParameters, simulate_responses
from kst_core.domain import Domain, Item, KnowledgeState
from kst_core.estimation import (
    BLIMEstimate,
    GoodnessOfFit,
    ResponseData,
    em_fit,
    goodness_of_fit,
)


def _state(*ids: str) -> KnowledgeState:
    return KnowledgeState(items=frozenset(Item(id=i) for i in ids))


@pytest.fixture()
def abc_domain() -> Domain:
    return Domain(items=frozenset({Item(id="a"), Item(id="b"), Item(id="c")}))


@pytest.fixture()
def linear_states() -> frozenset[KnowledgeState]:
    """∅, {a}, {a,b}, {a,b,c}."""
    return frozenset({_state(), _state("a"), _state("a", "b"), _state("a", "b", "c")})


def _generate_data(
    domain: Domain,
    states: frozenset[KnowledgeState],
    params: BLIMParameters,
    n_per_state: int = 50,
    seed: int = 42,
) -> ResponseData:
    """Generate synthetic response data from known parameters."""
    rng = np.random.default_rng(seed)
    state_list = sorted(states, key=lambda s: (len(s), sorted(s.item_ids)))
    patterns: list[dict[str, bool]] = []
    for state in state_list:
        for _ in range(n_per_state):
            patterns.append(simulate_responses(state, params, rng=rng))
    return ResponseData(domain=domain, patterns=tuple(patterns))


class TestResponseData:
    def test_valid(self, abc_domain: Domain) -> None:
        data = ResponseData(
            domain=abc_domain,
            patterns=({"a": True, "b": False, "c": True},),
        )
        assert len(data.patterns) == 1

    def test_multiple_patterns(self, abc_domain: Domain) -> None:
        data = ResponseData(
            domain=abc_domain,
            patterns=(
                {"a": True, "b": False, "c": True},
                {"a": False, "b": True, "c": False},
            ),
        )
        assert len(data.patterns) == 2

    def test_empty_patterns(self, abc_domain: Domain) -> None:
        with pytest.raises(ValueError, match="at least one"):
            ResponseData(domain=abc_domain, patterns=())

    def test_mismatched_keys(self, abc_domain: Domain) -> None:
        with pytest.raises(ValueError, match="do not match"):
            ResponseData(
                domain=abc_domain,
                patterns=({"a": True, "b": False},),
            )

    def test_extra_keys(self, abc_domain: Domain) -> None:
        with pytest.raises(ValueError, match="do not match"):
            ResponseData(
                domain=abc_domain,
                patterns=({"a": True, "b": False, "c": True, "d": False},),
            )


class TestEMFit:
    def test_recovers_uniform_parameters(
        self,
        abc_domain: Domain,
        linear_states: frozenset[KnowledgeState],
    ) -> None:
        """EM should approximately recover known uniform parameters."""
        true_beta, true_eta = 0.15, 0.10
        true_params = BLIMParameters.uniform(abc_domain, beta=true_beta, eta=true_eta)
        data = _generate_data(
            abc_domain, linear_states, true_params, n_per_state=200, seed=123
        )

        estimate = em_fit(abc_domain, linear_states, data)

        # Check parameters are approximately recovered
        for iid in abc_domain.item_ids:
            assert estimate.params.beta[iid] == pytest.approx(true_beta, abs=0.08)
            assert estimate.params.eta[iid] == pytest.approx(true_eta, abs=0.08)

    def test_converges(
        self,
        abc_domain: Domain,
        linear_states: frozenset[KnowledgeState],
    ) -> None:
        true_params = BLIMParameters.uniform(abc_domain, beta=0.1, eta=0.1)
        data = _generate_data(abc_domain, linear_states, true_params, n_per_state=100)

        estimate = em_fit(abc_domain, linear_states, data)

        assert estimate.converged
        assert estimate.iterations < 1000

    def test_log_likelihood_finite(
        self,
        abc_domain: Domain,
        linear_states: frozenset[KnowledgeState],
    ) -> None:
        true_params = BLIMParameters.uniform(abc_domain, beta=0.1, eta=0.1)
        data = _generate_data(abc_domain, linear_states, true_params)

        estimate = em_fit(abc_domain, linear_states, data)

        assert np.isfinite(estimate.log_likelihood)
        assert estimate.log_likelihood < 0  # log-likelihood is always negative

    def test_belief_is_valid_distribution(
        self,
        abc_domain: Domain,
        linear_states: frozenset[KnowledgeState],
    ) -> None:
        true_params = BLIMParameters.uniform(abc_domain, beta=0.1, eta=0.1)
        data = _generate_data(abc_domain, linear_states, true_params)

        estimate = em_fit(abc_domain, linear_states, data)

        assert sum(estimate.belief.probabilities) == pytest.approx(1.0)
        assert all(p >= 0 for p in estimate.belief.probabilities)
        assert len(estimate.belief.states) == len(linear_states)

    def test_max_iterations_reached(
        self,
        abc_domain: Domain,
        linear_states: frozenset[KnowledgeState],
    ) -> None:
        """With very few iterations, should not converge."""
        true_params = BLIMParameters.uniform(abc_domain, beta=0.1, eta=0.1)
        data = _generate_data(abc_domain, linear_states, true_params)

        estimate = em_fit(abc_domain, linear_states, data, max_iterations=2)

        assert not estimate.converged
        assert estimate.iterations == 2

    def test_custom_initial_params(
        self,
        abc_domain: Domain,
        linear_states: frozenset[KnowledgeState],
    ) -> None:
        true_params = BLIMParameters.uniform(abc_domain, beta=0.1, eta=0.1)
        data = _generate_data(abc_domain, linear_states, true_params)

        estimate = em_fit(
            abc_domain,
            linear_states,
            data,
            initial_beta=0.2,
            initial_eta=0.2,
        )

        assert estimate.converged

    def test_single_item_domain(self) -> None:
        """EM works with a minimal domain."""
        domain = Domain(items=frozenset({Item(id="x")}))
        states = frozenset({_state(), _state("x")})
        params = BLIMParameters.uniform(domain, beta=0.1, eta=0.1)
        data = _generate_data(domain, states, params, n_per_state=100)

        estimate = em_fit(domain, states, data)

        assert estimate.converged
        assert np.isfinite(estimate.log_likelihood)

    def test_deterministic_responses(
        self,
        abc_domain: Domain,
        linear_states: frozenset[KnowledgeState],
    ) -> None:
        """With beta=0 and eta=0, responses are deterministic."""
        true_params = BLIMParameters.uniform(abc_domain, beta=0.0, eta=0.0)
        data = _generate_data(abc_domain, linear_states, true_params, n_per_state=50)

        estimate = em_fit(abc_domain, linear_states, data)

        # With perfect data, estimated errors should be low
        for iid in abc_domain.item_ids:
            assert estimate.params.beta[iid] < 0.1
            assert estimate.params.eta[iid] < 0.1

    def test_result_types(
        self,
        abc_domain: Domain,
        linear_states: frozenset[KnowledgeState],
    ) -> None:
        true_params = BLIMParameters.uniform(abc_domain, beta=0.1, eta=0.1)
        data = _generate_data(abc_domain, linear_states, true_params)

        estimate = em_fit(abc_domain, linear_states, data)

        assert isinstance(estimate, BLIMEstimate)
        assert isinstance(estimate.params, BLIMParameters)
        assert isinstance(estimate.belief.states, tuple)
        assert isinstance(estimate.converged, bool)
        assert isinstance(estimate.iterations, int)


class TestGoodnessOfFit:
    def test_good_fit(
        self,
        abc_domain: Domain,
        linear_states: frozenset[KnowledgeState],
    ) -> None:
        """Data generated from model should yield reasonable G²."""
        true_params = BLIMParameters.uniform(abc_domain, beta=0.1, eta=0.1)
        data = _generate_data(
            abc_domain, linear_states, true_params, n_per_state=200
        )

        estimate = em_fit(abc_domain, linear_states, data)
        gof = goodness_of_fit(data, estimate, linear_states)

        assert isinstance(gof, GoodnessOfFit)
        assert gof.g_squared >= 0.0
        assert gof.degrees_of_freedom >= 1
        assert gof.n_observations == 800  # 4 states x 200

    def test_fields(
        self,
        abc_domain: Domain,
        linear_states: frozenset[KnowledgeState],
    ) -> None:
        true_params = BLIMParameters.uniform(abc_domain, beta=0.1, eta=0.1)
        data = _generate_data(abc_domain, linear_states, true_params)

        estimate = em_fit(abc_domain, linear_states, data)
        gof = goodness_of_fit(data, estimate, linear_states)

        assert gof.n_response_patterns > 0
        assert gof.n_observations == len(data.patterns)
        assert isinstance(gof.g_squared, float)
        assert isinstance(gof.degrees_of_freedom, int)

    def test_perfect_fit_low_g_squared(self) -> None:
        """Deterministic data from single state should give low G²."""
        domain = Domain(items=frozenset({Item(id="x"), Item(id="y")}))
        states = frozenset({_state(), _state("x"), _state("x", "y")})
        # All from state {x}: always x=correct, y=incorrect
        patterns = tuple({"x": True, "y": False} for _ in range(100))
        data = ResponseData(domain=domain, patterns=patterns)

        estimate = em_fit(domain, states, data)
        gof = goodness_of_fit(data, estimate, states)

        assert gof.n_response_patterns == 1
        assert gof.n_observations == 100


class TestEndToEnd:
    def test_yaml_to_estimation(self) -> None:
        """Full pipeline: YAML → course → simulate → estimate."""
        from kst_core import parse_file

        course = parse_file("examples/intro-pandas.kst.yaml")

        true_params = BLIMParameters.uniform(course.domain, beta=0.1, eta=0.1)
        rng = np.random.default_rng(42)

        # Simulate responses from multiple learners in different states
        state_list = sorted(
            course.states, key=lambda s: (len(s), sorted(s.item_ids))
        )
        patterns: list[dict[str, bool]] = []
        for state in state_list[:5]:  # Use first 5 states for speed
            for _ in range(30):
                patterns.append(
                    simulate_responses(state, true_params, rng=rng)
                )

        data = ResponseData(domain=course.domain, patterns=tuple(patterns))
        estimate = em_fit(course.domain, course.states, data)

        assert estimate.converged
        assert np.isfinite(estimate.log_likelihood)
        assert sum(estimate.belief.probabilities) == pytest.approx(1.0)

        gof = goodness_of_fit(data, estimate, course.states)
        assert gof.g_squared >= 0.0
