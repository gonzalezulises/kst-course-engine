"""Tests for kst_core.assessment — BLIM and adaptive assessment."""

from __future__ import annotations

import math

import numpy as np
import pytest

from kst_core.assessment import (
    AdaptiveAssessment,
    BeliefState,
    BLIMParameters,
    simulate_responses,
)
from kst_core.domain import Domain, Item, KnowledgeState


def _state(*ids: str) -> KnowledgeState:
    return KnowledgeState(items=frozenset(Item(id=i) for i in ids))


@pytest.fixture()
def abc_domain() -> Domain:
    return Domain(items=frozenset({Item(id="a"), Item(id="b"), Item(id="c")}))


@pytest.fixture()
def linear_states() -> frozenset[KnowledgeState]:
    """∅, {a}, {a,b}, {a,b,c}."""
    return frozenset({_state(), _state("a"), _state("a", "b"), _state("a", "b", "c")})


@pytest.fixture()
def params(abc_domain: Domain) -> BLIMParameters:
    return BLIMParameters.uniform(abc_domain, beta=0.1, eta=0.1)


class TestBLIMParameters:
    def test_uniform(self, abc_domain: Domain) -> None:
        p = BLIMParameters.uniform(abc_domain, beta=0.2, eta=0.05)
        assert p.beta["a"] == 0.2
        assert p.eta["a"] == 0.05

    def test_uniform_defaults(self, abc_domain: Domain) -> None:
        p = BLIMParameters.uniform(abc_domain)
        assert p.beta["a"] == 0.1
        assert p.eta["a"] == 0.1

    def test_custom_params(self, abc_domain: Domain) -> None:
        p = BLIMParameters(
            domain=abc_domain,
            beta={"a": 0.1, "b": 0.2, "c": 0.05},
            eta={"a": 0.1, "b": 0.15, "c": 0.1},
        )
        assert p.beta["b"] == 0.2
        assert p.eta["b"] == 0.15

    def test_beta_out_of_range(self, abc_domain: Domain) -> None:
        with pytest.raises(ValueError, match=r"0, 0\.5"):
            BLIMParameters(
                domain=abc_domain,
                beta={"a": 0.6, "b": 0.1, "c": 0.1},
                eta={"a": 0.1, "b": 0.1, "c": 0.1},
            )

    def test_eta_out_of_range(self, abc_domain: Domain) -> None:
        with pytest.raises(ValueError, match=r"0, 0\.5"):
            BLIMParameters(
                domain=abc_domain,
                beta={"a": 0.1, "b": 0.1, "c": 0.1},
                eta={"a": 0.5, "b": 0.1, "c": 0.1},
            )

    def test_negative_probability(self, abc_domain: Domain) -> None:
        with pytest.raises(ValueError, match=r"0, 0\.5"):
            BLIMParameters(
                domain=abc_domain,
                beta={"a": -0.1, "b": 0.1, "c": 0.1},
                eta={"a": 0.1, "b": 0.1, "c": 0.1},
            )

    def test_beta_keys_mismatch(self, abc_domain: Domain) -> None:
        with pytest.raises(ValueError, match="Beta keys"):
            BLIMParameters(
                domain=abc_domain,
                beta={"a": 0.1, "b": 0.1},
                eta={"a": 0.1, "b": 0.1, "c": 0.1},
            )

    def test_eta_keys_mismatch(self, abc_domain: Domain) -> None:
        with pytest.raises(ValueError, match="Eta keys"):
            BLIMParameters(
                domain=abc_domain,
                beta={"a": 0.1, "b": 0.1, "c": 0.1},
                eta={"a": 0.1, "z": 0.1, "c": 0.1},
            )

    def test_p_correct_in_state(self, params: BLIMParameters) -> None:
        state = _state("a", "b")
        assert params.p_correct("a", state) == pytest.approx(0.9)

    def test_p_correct_not_in_state(self, params: BLIMParameters) -> None:
        state = _state("a")
        assert params.p_correct("b", state) == pytest.approx(0.1)

    def test_p_incorrect(self, params: BLIMParameters) -> None:
        state = _state("a")
        assert params.p_incorrect("a", state) == pytest.approx(0.1)
        assert params.p_incorrect("b", state) == pytest.approx(0.9)


class TestBeliefState:
    def test_uniform(self, linear_states: frozenset[KnowledgeState]) -> None:
        belief = BeliefState.uniform(linear_states)
        assert len(belief.states) == 4
        assert all(math.isclose(p, 0.25) for p in belief.probabilities)

    def test_entropy_uniform(self, linear_states: frozenset[KnowledgeState]) -> None:
        belief = BeliefState.uniform(linear_states)
        assert belief.entropy() == pytest.approx(2.0)  # log2(4)

    def test_entropy_certain(self) -> None:
        states = (_state(), _state("a"))
        belief = BeliefState(states=states, probabilities=(1.0, 0.0))
        assert belief.entropy() == pytest.approx(0.0)

    def test_map_estimate(self) -> None:
        s0 = _state()
        s1 = _state("a")
        belief = BeliefState(states=(s0, s1), probabilities=(0.3, 0.7))
        assert belief.map_estimate() == s1

    def test_probability_of(self) -> None:
        s0 = _state()
        s1 = _state("a")
        belief = BeliefState(states=(s0, s1), probabilities=(0.4, 0.6))
        assert belief.probability_of(s1) == pytest.approx(0.6)
        assert belief.probability_of(_state("b")) == pytest.approx(0.0)

    def test_update_correct(
        self,
        linear_states: frozenset[KnowledgeState],
        params: BLIMParameters,
    ) -> None:
        belief = BeliefState.uniform(linear_states)
        updated = belief.update("a", correct=True, params=params)
        # States containing 'a' should get higher probability
        p_empty = updated.probability_of(_state())
        p_a = updated.probability_of(_state("a"))
        assert p_a > p_empty

    def test_update_incorrect(
        self,
        linear_states: frozenset[KnowledgeState],
        params: BLIMParameters,
    ) -> None:
        belief = BeliefState.uniform(linear_states)
        updated = belief.update("a", correct=False, params=params)
        p_empty = updated.probability_of(_state())
        p_a = updated.probability_of(_state("a"))
        assert p_empty > p_a

    def test_update_preserves_normalization(
        self,
        linear_states: frozenset[KnowledgeState],
        params: BLIMParameters,
    ) -> None:
        belief = BeliefState.uniform(linear_states)
        updated = belief.update("a", correct=True, params=params)
        assert sum(updated.probabilities) == pytest.approx(1.0)

    def test_update_zero_total_fallback(self) -> None:
        """If all likelihoods are zero, fall back to uniform."""
        s0 = _state()
        s1 = _state("a")
        domain = Domain(items=frozenset({Item(id="a")}))
        # Extreme params: beta=0, eta=0
        params = BLIMParameters(domain=domain, beta={"a": 0.0}, eta={"a": 0.0})
        belief = BeliefState(states=(s0, s1), probabilities=(1.0, 0.0))
        # s0 has p(correct|a not in s0)=eta=0, p(incorrect|a not in s0)=1
        # s1 has prob=0, so contribution=0
        # Asking 'a' correctly: s0 gives 0*1.0=0, s1 gives 0.0*1.0=0 → total=0 → uniform
        updated = belief.update("a", correct=True, params=params)
        assert sum(updated.probabilities) == pytest.approx(1.0)

    def test_mismatched_lengths(self) -> None:
        with pytest.raises(ValueError, match="same length"):
            BeliefState(states=(_state(),), probabilities=(0.5, 0.5))

    def test_empty_states(self) -> None:
        with pytest.raises(ValueError, match="at least one"):
            BeliefState(states=(), probabilities=())

    def test_negative_probability(self) -> None:
        with pytest.raises(ValueError, match="non-negative"):
            BeliefState(states=(_state(),), probabilities=(-1.0,))

    def test_not_normalized(self) -> None:
        with pytest.raises(ValueError, match="sum to 1"):
            BeliefState(states=(_state(), _state("a")), probabilities=(0.3, 0.3))


class TestAdaptiveAssessment:
    def test_start(
        self,
        abc_domain: Domain,
        linear_states: frozenset[KnowledgeState],
    ) -> None:
        session = AdaptiveAssessment.start(abc_domain, linear_states)
        assert session.current_entropy > 0
        assert not session.is_complete
        assert len(session.remaining_items) == 3

    def test_start_custom_params(
        self,
        abc_domain: Domain,
        linear_states: frozenset[KnowledgeState],
        params: BLIMParameters,
    ) -> None:
        session = AdaptiveAssessment.start(abc_domain, linear_states, params)
        assert session.params == params

    def test_observe(
        self,
        abc_domain: Domain,
        linear_states: frozenset[KnowledgeState],
    ) -> None:
        session = AdaptiveAssessment.start(abc_domain, linear_states)
        updated = session.observe("a", correct=True)
        assert "a" in updated.asked
        assert len(updated.remaining_items) == 2

    def test_observe_invalid_item(
        self,
        abc_domain: Domain,
        linear_states: frozenset[KnowledgeState],
    ) -> None:
        session = AdaptiveAssessment.start(abc_domain, linear_states)
        with pytest.raises(ValueError, match="not in domain"):
            session.observe("z", correct=True)

    def test_select_item(
        self,
        abc_domain: Domain,
        linear_states: frozenset[KnowledgeState],
    ) -> None:
        session = AdaptiveAssessment.start(abc_domain, linear_states)
        item_id = session.select_item()
        assert item_id in abc_domain.item_ids

    def test_select_item_no_remaining(
        self,
        abc_domain: Domain,
        linear_states: frozenset[KnowledgeState],
    ) -> None:
        session = AdaptiveAssessment.start(abc_domain, linear_states)
        session = session.observe("a", True)
        session = session.observe("b", True)
        session = session.observe("c", True)
        assert session.is_complete
        with pytest.raises(ValueError, match="No remaining"):
            session.select_item()

    def test_information_gain_nonnegative(
        self,
        abc_domain: Domain,
        linear_states: frozenset[KnowledgeState],
    ) -> None:
        session = AdaptiveAssessment.start(abc_domain, linear_states)
        for item_id in abc_domain.item_ids:
            gain = session.information_gain(item_id)
            assert gain >= -1e-10  # allow small floating point errors

    def test_entropy_decreases_with_evidence(
        self,
        abc_domain: Domain,
        linear_states: frozenset[KnowledgeState],
    ) -> None:
        session = AdaptiveAssessment.start(abc_domain, linear_states)
        h0 = session.current_entropy
        session = session.observe("a", correct=True)
        h1 = session.current_entropy
        assert h1 <= h0

    def test_run_batch(
        self,
        abc_domain: Domain,
        linear_states: frozenset[KnowledgeState],
    ) -> None:
        session = AdaptiveAssessment.start(abc_domain, linear_states)
        result = session.run({"a": True, "b": True, "c": False})
        assert result.is_complete
        estimate = result.current_estimate
        assert isinstance(estimate, KnowledgeState)

    def test_run_adaptive(
        self,
        abc_domain: Domain,
        linear_states: frozenset[KnowledgeState],
    ) -> None:
        true_state = _state("a", "b")
        params = BLIMParameters.uniform(abc_domain, beta=0.0, eta=0.0)
        session = AdaptiveAssessment.start(abc_domain, linear_states, params)

        def respond(item_id: str) -> bool:
            return item_id in true_state.item_ids

        result = session.run_adaptive(respond, max_questions=3)
        assert result.current_estimate == true_state

    def test_run_adaptive_entropy_stop(
        self,
        abc_domain: Domain,
        linear_states: frozenset[KnowledgeState],
    ) -> None:
        params = BLIMParameters.uniform(abc_domain, beta=0.0, eta=0.0)
        session = AdaptiveAssessment.start(abc_domain, linear_states, params)

        def respond(item_id: str) -> bool:
            return item_id in {"a", "b", "c"}

        result = session.run_adaptive(respond, entropy_threshold=0.5)
        assert result.current_entropy <= 0.5 or result.is_complete

    def test_run_adaptive_max_questions(
        self,
        abc_domain: Domain,
        linear_states: frozenset[KnowledgeState],
    ) -> None:
        session = AdaptiveAssessment.start(abc_domain, linear_states)

        def respond(_item_id: str) -> bool:
            return True

        result = session.run_adaptive(respond, max_questions=1)
        assert len(result.asked) == 1

    def test_run_adaptive_default_max(
        self,
        abc_domain: Domain,
        linear_states: frozenset[KnowledgeState],
    ) -> None:
        params = BLIMParameters.uniform(abc_domain, beta=0.0, eta=0.0)
        session = AdaptiveAssessment.start(abc_domain, linear_states, params)

        def respond(_item_id: str) -> bool:
            return True

        result = session.run_adaptive(respond, entropy_threshold=-1.0)
        assert result.is_complete
        assert len(result.asked) == 3


class TestSimulateResponses:
    def test_deterministic_no_errors(self, abc_domain: Domain) -> None:
        """With beta=0, eta=0, responses are deterministic."""
        state = _state("a", "b")
        params = BLIMParameters.uniform(abc_domain, beta=0.0, eta=0.0)
        responses = simulate_responses(state, params, rng=np.random.default_rng(0))
        assert responses["a"] is True
        assert responses["b"] is True
        assert responses["c"] is False

    def test_all_items_covered(self, abc_domain: Domain, params: BLIMParameters) -> None:
        state = _state("a")
        responses = simulate_responses(state, params, rng=np.random.default_rng(0))
        assert set(responses.keys()) == abc_domain.item_ids

    def test_custom_items(self, abc_domain: Domain, params: BLIMParameters) -> None:
        state = _state("a")
        responses = simulate_responses(
            state, params, items=["a", "b"], rng=np.random.default_rng(0)
        )
        assert set(responses.keys()) == {"a", "b"}

    def test_default_rng(self, abc_domain: Domain, params: BLIMParameters) -> None:
        state = _state("a")
        responses = simulate_responses(state, params)
        assert len(responses) == 3

    def test_stochastic_with_errors(self, abc_domain: Domain) -> None:
        """With nonzero errors, responses are stochastic."""
        state = _state("a", "b", "c")
        params = BLIMParameters.uniform(abc_domain, beta=0.3, eta=0.3)
        rng = np.random.default_rng(42)
        # Run many simulations and check distribution
        n_trials = 1000
        correct_counts = {iid: 0 for iid in abc_domain.item_ids}
        for _ in range(n_trials):
            r = simulate_responses(state, params, rng=rng)
            for iid, c in r.items():
                if c:
                    correct_counts[iid] += 1
        # For items in state: expected ~70% correct (1 - beta=0.3)
        for iid in abc_domain.item_ids:
            rate = correct_counts[iid] / n_trials
            assert 0.55 < rate < 0.85


class TestEndToEnd:
    def test_full_pipeline_from_yaml(self) -> None:
        """Full pipeline: YAML → course → assessment → estimate."""
        from kst_core import parse_file

        course = parse_file("examples/intro-pandas.kst.yaml")
        true_state = KnowledgeState(
            items=frozenset(
                item
                for item in course.domain
                if item.id in {"import", "series", "dataframe", "indexing"}
            )
        )

        params = BLIMParameters.uniform(course.domain, beta=0.0, eta=0.0)
        session = AdaptiveAssessment.start(course.domain, course.states, params)

        def respond(item_id: str) -> bool:
            return item_id in true_state.item_ids

        result = session.run_adaptive(respond, entropy_threshold=0.01)
        assert result.current_estimate == true_state
