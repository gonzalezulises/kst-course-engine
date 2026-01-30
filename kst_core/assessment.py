"""Adaptive assessment based on the Basic Local Independence Model (BLIM).

Implements Bayesian knowledge state estimation:
- BLIM: probabilistic response model with slip (β) and guess (η) parameters
- Adaptive item selection via maximum entropy reduction
- Sequential Bayesian updating of state beliefs

The BLIM assumes local independence: the probability of a response pattern
factorizes over items given the true knowledge state.

For state K and item q:
    P(correct | q ∈ K) = 1 - β_q   (slip: knows but errs)
    P(correct | q ∉ K) = η_q       (guess: doesn't know but correct)

References:
    Falmagne, J.-Cl. & Doignon, J.-P. (2011). Learning Spaces, Ch. 12.
    Doignon, J.-P. & Falmagne, J.-Cl. (1999). Knowledge Spaces, Ch. 7.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import numpy as np
from pydantic import BaseModel, field_validator, model_validator

from kst_core.domain import Domain, KnowledgeState  # noqa: TC001

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence


class BLIMParameters(BaseModel, frozen=True):
    """Parameters for the Basic Local Independence Model.

    β_q: slip probability — P(incorrect | q ∈ K) for each item q.
    η_q: guess probability — P(correct | q ∉ K) for each item q.
    """

    domain: Domain
    beta: dict[str, float]
    eta: dict[str, float]

    @field_validator("beta", "eta")
    @classmethod
    def probabilities_in_range(cls, v: dict[str, float]) -> dict[str, float]:
        for item_id, prob in v.items():
            if not 0.0 <= prob < 0.5:
                msg = f"Parameter for '{item_id}' must be in [0, 0.5), got {prob}"
                raise ValueError(msg)
        return v

    @model_validator(mode="after")
    def items_match_domain(self) -> BLIMParameters:
        domain_ids = self.domain.item_ids
        beta_ids = set(self.beta.keys())
        eta_ids = set(self.eta.keys())
        if beta_ids != domain_ids:
            msg = f"Beta keys {beta_ids} do not match domain {domain_ids}"
            raise ValueError(msg)
        if eta_ids != domain_ids:
            msg = f"Eta keys {eta_ids} do not match domain {domain_ids}"
            raise ValueError(msg)
        return self

    @classmethod
    def uniform(cls, domain: Domain, beta: float = 0.1, eta: float = 0.1) -> BLIMParameters:
        """Create uniform parameters (same β and η for all items)."""
        item_ids = domain.item_ids
        return cls(
            domain=domain,
            beta={iid: beta for iid in item_ids},
            eta={iid: eta for iid in item_ids},
        )

    def p_correct(self, item_id: str, state: KnowledgeState) -> float:
        """P(correct response to q | true state K).

        P(correct | q ∈ K) = 1 - β_q
        P(correct | q ∉ K) = η_q
        """
        if item_id in state.item_ids:
            return 1.0 - self.beta[item_id]
        return self.eta[item_id]

    def p_incorrect(self, item_id: str, state: KnowledgeState) -> float:
        """P(incorrect response to q | true state K)."""
        return 1.0 - self.p_correct(item_id, state)


class BeliefState(BaseModel):
    """Bayesian belief distribution over knowledge states.

    π(K) = P(true state is K) for each K ∈ K.
    """

    states: tuple[KnowledgeState, ...]
    probabilities: tuple[float, ...]

    model_config = {"arbitrary_types_allowed": True}

    @model_validator(mode="after")
    def validate_distribution(self) -> BeliefState:
        if len(self.states) != len(self.probabilities):
            msg = "States and probabilities must have same length"
            raise ValueError(msg)
        if len(self.states) == 0:
            msg = "Must have at least one state"
            raise ValueError(msg)
        for p in self.probabilities:
            if p < 0.0:
                msg = f"Probabilities must be non-negative, got {p}"
                raise ValueError(msg)
        total = sum(self.probabilities)
        if not math.isclose(total, 1.0, rel_tol=1e-6):
            msg = f"Probabilities must sum to 1.0, got {total}"
            raise ValueError(msg)
        return self

    @classmethod
    def uniform(cls, states: frozenset[KnowledgeState]) -> BeliefState:
        """Create a uniform prior over all states."""
        state_list = tuple(sorted(states, key=lambda s: (len(s), sorted(s.item_ids))))
        n = len(state_list)
        return cls(states=state_list, probabilities=tuple(1.0 / n for _ in state_list))

    def entropy(self) -> float:
        """Shannon entropy H(π) = -Σ π(K) log₂ π(K)."""
        h = 0.0
        for p in self.probabilities:
            if p > 0.0:
                h -= p * math.log2(p)
        return h

    def map_estimate(self) -> KnowledgeState:
        """Maximum a posteriori estimate: argmax_K π(K)."""
        max_idx = int(np.argmax(self.probabilities))
        return self.states[max_idx]

    def probability_of(self, state: KnowledgeState) -> float:
        """Return π(K) for a specific state."""
        for s, p in zip(self.states, self.probabilities, strict=True):
            if s == state:
                return p
        return 0.0

    def update(
        self,
        item_id: str,
        correct: bool,
        params: BLIMParameters,
    ) -> BeliefState:
        """Bayesian update given an observed response.

        π'(K) ∝ π(K) · P(response | K, q)
        """
        new_probs: list[float] = []
        for state, prior in zip(self.states, self.probabilities, strict=True):
            if correct:
                likelihood = params.p_correct(item_id, state)
            else:
                likelihood = params.p_incorrect(item_id, state)
            new_probs.append(prior * likelihood)

        total = sum(new_probs)
        if total == 0.0:
            return BeliefState.uniform(frozenset(self.states))

        normalized = tuple(p / total for p in new_probs)
        return BeliefState(states=self.states, probabilities=normalized)


class AdaptiveAssessment(BaseModel):
    """Adaptive assessment engine using BLIM and entropy-based item selection.

    Selects the most informative item to ask next, observes responses,
    and updates beliefs until convergence or a stopping criterion is met.
    """

    domain: Domain
    states: frozenset[KnowledgeState]
    params: BLIMParameters
    belief: BeliefState
    asked: frozenset[str] = frozenset()

    model_config = {"arbitrary_types_allowed": True}

    @classmethod
    def start(
        cls,
        domain: Domain,
        states: frozenset[KnowledgeState],
        params: BLIMParameters | None = None,
    ) -> AdaptiveAssessment:
        """Initialize an assessment session with uniform prior."""
        if params is None:
            params = BLIMParameters.uniform(domain)
        belief = BeliefState.uniform(states)
        return cls(domain=domain, states=states, params=params, belief=belief)

    @property
    def remaining_items(self) -> frozenset[str]:
        """Items not yet asked."""
        return self.domain.item_ids - self.asked

    @property
    def is_complete(self) -> bool:
        """True if all items have been asked."""
        return len(self.remaining_items) == 0

    @property
    def current_estimate(self) -> KnowledgeState:
        """Current MAP estimate of the learner's knowledge state."""
        return self.belief.map_estimate()

    @property
    def current_entropy(self) -> float:
        """Current entropy of the belief distribution."""
        return self.belief.entropy()

    def information_gain(self, item_id: str) -> float:
        """Expected reduction in entropy from asking item q.

        I(q) = H(π) - E_r[ H(π | r_q) ]
             = H(π) - P(correct) · H(π|correct) - P(incorrect) · H(π|incorrect)
        """
        current_h = self.belief.entropy()

        p_correct_marginal = sum(
            p * self.params.p_correct(item_id, state)
            for state, p in zip(self.belief.states, self.belief.probabilities, strict=True)
        )
        p_incorrect_marginal = 1.0 - p_correct_marginal

        belief_if_correct = self.belief.update(item_id, correct=True, params=self.params)
        belief_if_incorrect = self.belief.update(item_id, correct=False, params=self.params)

        expected_h = (
            p_correct_marginal * belief_if_correct.entropy()
            + p_incorrect_marginal * belief_if_incorrect.entropy()
        )

        return current_h - expected_h

    def select_item(self) -> str:
        """Select the most informative item to ask next.

        q* = argmax_{q ∈ remaining} I(q; π)
        """
        if not self.remaining_items:
            msg = "No remaining items to ask"
            raise ValueError(msg)

        best_item = ""
        best_gain = -1.0
        for item_id in sorted(self.remaining_items):
            gain = self.information_gain(item_id)
            if gain > best_gain:
                best_gain = gain
                best_item = item_id
        return best_item

    def observe(self, item_id: str, correct: bool) -> AdaptiveAssessment:
        """Record an observed response and update beliefs.

        Returns a new AdaptiveAssessment with updated state.
        """
        if item_id not in self.domain.item_ids:
            msg = f"Item '{item_id}' not in domain"
            raise ValueError(msg)

        new_belief = self.belief.update(item_id, correct, self.params)
        return AdaptiveAssessment(
            domain=self.domain,
            states=self.states,
            params=self.params,
            belief=new_belief,
            asked=self.asked | {item_id},
        )

    def run(
        self,
        responses: dict[str, bool],
    ) -> AdaptiveAssessment:
        """Run a batch of responses (non-adaptive, fixed order)."""
        session = self
        for item_id, correct in responses.items():
            session = session.observe(item_id, correct)
        return session

    def run_adaptive(
        self,
        respond: Callable[[str], bool],
        max_questions: int | None = None,
        entropy_threshold: float = 0.1,
    ) -> AdaptiveAssessment:
        """Run a fully adaptive assessment session.

        Args:
            respond: Callable that takes an item_id and returns True/False.
            max_questions: Maximum number of questions to ask.
            entropy_threshold: Stop when entropy drops below this.

        Returns:
            Final assessment state.
        """
        session = self
        questions_asked = 0
        max_q = max_questions if max_questions is not None else len(self.domain)

        while (
            not session.is_complete
            and questions_asked < max_q
            and session.current_entropy > entropy_threshold
        ):
            item_id = session.select_item()
            correct = respond(item_id)
            session = session.observe(item_id, correct)
            questions_asked += 1

        return session


def simulate_responses(
    true_state: KnowledgeState,
    params: BLIMParameters,
    items: Sequence[str] | None = None,
    rng: np.random.Generator | None = None,
) -> dict[str, bool]:
    """Simulate stochastic responses given a true knowledge state.

    For each item q:
    - If q ∈ K: correct with probability 1 - β_q
    - If q ∉ K: correct with probability η_q
    """
    if rng is None:
        rng = np.random.default_rng()

    if items is None:
        items = sorted(params.domain.item_ids)

    responses: dict[str, bool] = {}
    for item_id in items:
        p = params.p_correct(item_id, true_state)
        responses[item_id] = bool(rng.random() < p)
    return responses
