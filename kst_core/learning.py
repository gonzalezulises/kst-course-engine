"""Markov learning model on learning spaces.

Models learning as a discrete-time Markov chain on knowledge states:
- From state K, a learner transitions to K ∪ {q} for q in the outer fringe
- Transition probability: P(K → K ∪ {q}) = λ_q / Σ_{q' ∈ OF(K)} λ_{q'}
- The full domain Q is the absorbing state (mastery)

The fundamental matrix N = (I - T)⁻¹ of the absorbing chain yields
expected steps to mastery from any transient state.

References:
    Falmagne, J.-Cl. & Doignon, J.-P. (2011). Learning Spaces, Ch. 15.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from pydantic import BaseModel, model_validator

from kst_core.domain import Domain, KnowledgeState
from kst_core.space import LearningSpace  # noqa: TC001

if TYPE_CHECKING:
    from kst_core.domain import Item


class LearningRate(BaseModel, frozen=True):
    """Per-item learning rate parameters λ_q > 0.

    Higher rates mean the item is learned more quickly (higher
    transition probability when the item is in the outer fringe).
    """

    domain: Domain
    rates: dict[str, float]

    @model_validator(mode="after")
    def validate_rates(self) -> LearningRate:
        domain_ids = self.domain.item_ids
        rate_ids = set(self.rates.keys())
        if rate_ids != domain_ids:
            msg = f"Rate keys {rate_ids} do not match domain {domain_ids}"
            raise ValueError(msg)
        for item_id, rate in self.rates.items():
            if rate <= 0.0:
                msg = f"Rate for '{item_id}' must be positive, got {rate}"
                raise ValueError(msg)
        return self

    @classmethod
    def uniform(cls, domain: Domain, rate: float = 1.0) -> LearningRate:
        """Create uniform rates (same λ for all items)."""
        return cls(domain=domain, rates={iid: rate for iid in domain.item_ids})


class LearningModel(BaseModel, frozen=True):
    """Discrete-time Markov chain on a learning space.

    Models a learner progressing through knowledge states. At each step,
    the learner acquires one item from the outer fringe of their current
    state, with probability proportional to the item's learning rate.

    The full domain Q is the unique absorbing state.
    """

    space: LearningSpace
    rates: LearningRate

    model_config = {"arbitrary_types_allowed": True}

    @model_validator(mode="after")
    def domains_match(self) -> LearningModel:
        if self.space.domain != self.rates.domain:
            msg = "LearningSpace domain and LearningRate domain must match"
            raise ValueError(msg)
        return self

    def transition_probs(
        self, state: KnowledgeState
    ) -> dict[KnowledgeState, float]:
        """Transition probabilities from state K.

        P(K → K ∪ {q}) = λ_q / Σ_{q' ∈ OF(K)} λ_{q'}

        For the absorbing state Q, returns {Q: 1.0}.
        """
        if state == self.space.domain.full_state:
            return {state: 1.0}

        fringe: frozenset[Item] = self.space.outer_fringe(state)
        total_rate = sum(self.rates.rates[item.id] for item in fringe)
        result: dict[KnowledgeState, float] = {}
        for item in fringe:
            next_state = KnowledgeState(items=state.items | {item})
            result[next_state] = self.rates.rates[item.id] / total_rate
        return result

    def transition_matrix(
        self,
    ) -> tuple[tuple[KnowledgeState, ...], np.ndarray]:
        """Full transition matrix over all states.

        Returns (state_ordering, matrix) where matrix[i, j] = P(K_i → K_j).
        States are sorted by cardinality then lexicographically.
        """
        state_list = sorted(
            self.space.states,
            key=lambda s: (len(s), sorted(s.item_ids)),
        )
        n = len(state_list)
        state_idx = {s: i for i, s in enumerate(state_list)}

        matrix = np.zeros((n, n))
        for i, state in enumerate(state_list):
            probs = self.transition_probs(state)
            for next_state, prob in probs.items():
                j = state_idx[next_state]
                matrix[i, j] = prob

        return tuple(state_list), matrix

    def expected_steps(
        self,
    ) -> dict[KnowledgeState, float]:
        """Expected number of steps from each state to full mastery.

        Uses the fundamental matrix of the absorbing Markov chain:
            N = (I - T)⁻¹
        where T is the transient-to-transient sub-matrix.

        Expected steps from state i = Σ_j N_{ij} (row sum of N).

        Returns:
            Dict mapping each transient state to its expected steps.
            The absorbing state Q maps to 0.0.
        """
        state_list, matrix = self.transition_matrix()
        full = self.space.domain.full_state

        # Identify transient states (everything except Q)
        transient = [s for s in state_list if s != full]
        transient_idx = [
            i for i, s in enumerate(state_list) if s != full
        ]
        n_transient = len(transient)

        # Extract transient-to-transient sub-matrix T
        t_matrix = matrix[np.ix_(transient_idx, transient_idx)]

        # Fundamental matrix: N = (I - T)^{-1}
        fundamental = np.linalg.inv(np.eye(n_transient) - t_matrix)

        # Expected steps = row sums of N
        expected = np.sum(fundamental, axis=1)

        result: dict[KnowledgeState, float] = {full: 0.0}
        for i, state in enumerate(transient):
            result[state] = float(expected[i])
        return result

    def simulate_trajectory(
        self,
        start: KnowledgeState | None = None,
        rng: np.random.Generator | None = None,
        max_steps: int = 1000,
    ) -> tuple[KnowledgeState, ...]:
        """Simulate a learning trajectory from start to mastery.

        Args:
            start: Initial state (default: empty set ∅).
            rng: Random number generator.
            max_steps: Safety limit on trajectory length.

        Returns:
            Tuple of states visited, from start to (hopefully) Q.
        """
        if start is None:
            start = KnowledgeState()
        if rng is None:
            rng = np.random.default_rng()

        full = self.space.domain.full_state
        trajectory: list[KnowledgeState] = [start]
        current = start

        for _ in range(max_steps):
            if current == full:
                break
            probs = self.transition_probs(current)
            next_states = list(probs.keys())
            p_values = [probs[s] for s in next_states]
            idx = int(rng.choice(len(next_states), p=p_values))
            current = next_states[idx]
            trajectory.append(current)

        return tuple(trajectory)

    def optimal_teaching_item(
        self, state: KnowledgeState
    ) -> str:
        """Select the item that minimizes expected steps to mastery.

        For each q in the outer fringe of K, compute the expected
        steps from K ∪ {q} to Q. Return the q that minimizes this.

        Args:
            state: Current knowledge state.

        Returns:
            Item ID of the optimal item to teach next.

        Raises:
            ValueError: If the state is already the full domain
                or has no teachable items.
        """
        full = self.space.domain.full_state
        if state == full:
            msg = "Learner has already achieved full mastery"
            raise ValueError(msg)

        fringe = self.space.outer_fringe(state)
        expected = self.expected_steps()

        best_item = ""
        best_expected = float("inf")
        for item in sorted(fringe):
            next_state = KnowledgeState(items=state.items | {item})
            e = expected.get(next_state, 0.0)
            if e < best_expected:
                best_expected = e
                best_item = item.id

        return best_item
