"""Optimization algorithms for Knowledge Space Theory.

Provides four optimization routines:

1. ``calibrate_parameters``: Multi-restart EM with identifiability check
   (Heller & Wickelmaier, 2013).
2. ``optimal_teaching_sequence``: MDP value iteration for optimal teaching
   V*(K) = 1 + min_{q ∈ OF(K)} V*(K ∪ {q}) (Falmagne & Doignon 2011, Ch. 15).
3. ``estimate_item_difficulty``: Structural (DAG depth) + empirical + BLIM
   difficulty estimation.
4. ``tune_learning_rates``: MLE on Markov chain log-likelihood via EM.

References:
    Falmagne, J.-Cl. & Doignon, J.-P. (2011). Learning Spaces. Springer.
    Heller, J. & Wickelmaier, F. (2013). How to deal with identifiability.
        Psychometrika, 78(2), 264-279.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import numpy as np
from pydantic import BaseModel

from kst_core.assessment import BLIMParameters  # noqa: TC001
from kst_core.domain import Domain, KnowledgeState
from kst_core.estimation import ResponseData, em_fit
from kst_core.learning import LearningRate
from kst_core.space import LearningSpace  # noqa: TC001

if TYPE_CHECKING:
    from kst_core.prerequisites import PrerequisiteGraph

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------


class ItemCalibration(BaseModel, frozen=True):
    """Calibrated parameters for a single item."""

    item_id: str
    beta: float
    eta: float


class CalibrationResult(BaseModel, frozen=True):
    """Result of multi-restart EM calibration.

    Contains the best-fit parameters, convergence diagnostics,
    and identifiability information.
    """

    params: BLIMParameters
    item_calibrations: tuple[ItemCalibration, ...]
    log_likelihood: float
    converged: bool
    restarts: int
    identifiable: bool

    model_config = {"arbitrary_types_allowed": True}


class TeachingStep(BaseModel, frozen=True):
    """A single step in an optimal teaching plan."""

    item_id: str
    from_state_ids: frozenset[str]
    to_state_ids: frozenset[str]
    expected_remaining: float

    model_config = {"arbitrary_types_allowed": True}


class TeachingPlan(BaseModel, frozen=True):
    """Complete optimal teaching sequence from a start state to mastery.

    Computed via MDP value iteration:
    V*(K) = 1 + min_{q ∈ OF(K)} V*(K ∪ {q})
    """

    steps: tuple[TeachingStep, ...]
    total_expected_steps: float


class ItemDifficulty(BaseModel, frozen=True):
    """Difficulty estimate for a single item."""

    item_id: str
    structural_depth: int
    structural_difficulty: float
    empirical_difficulty: float | None = None
    blim_difficulty: float | None = None
    combined_difficulty: float


class DifficultyReport(BaseModel, frozen=True):
    """Difficulty report for all items in a course."""

    items: tuple[ItemDifficulty, ...]
    method: str


class TrajectoryData(BaseModel, frozen=True):
    """Observed learning trajectory data for rate tuning."""

    domain: Domain
    trajectories: tuple[tuple[frozenset[str], ...], ...]

    model_config = {"arbitrary_types_allowed": True}


class TunedRates(BaseModel, frozen=True):
    """Result of learning rate tuning via MLE."""

    rates: LearningRate
    log_likelihood: float
    converged: bool
    iterations: int

    model_config = {"arbitrary_types_allowed": True}


# ---------------------------------------------------------------------------
# 1. calibrate_parameters — Multi-restart EM
# ---------------------------------------------------------------------------


def calibrate_parameters(
    domain: Domain,
    states: frozenset[KnowledgeState],
    data: ResponseData,
    *,
    restarts: int = 5,
    max_iterations: int = 1000,
    tolerance: float = 1e-6,
) -> CalibrationResult:
    """Calibrate BLIM parameters using multi-restart EM.

    Runs the EM algorithm multiple times with different initial values
    and selects the run with the highest log-likelihood.

    Identifiability is checked by comparing parameter estimates across
    restarts (Heller & Wickelmaier, 2013): if estimates diverge
    beyond a threshold, the model may not be identifiable.

    Args:
        domain: The knowledge domain Q.
        states: Knowledge states K ⊆ 2^Q.
        data: Observed response patterns.
        restarts: Number of random restarts.
        max_iterations: Maximum EM iterations per restart.
        tolerance: Convergence threshold.

    Returns:
        CalibrationResult with best parameters and diagnostics.
    """
    rng = np.random.default_rng(42)
    best_ll = -math.inf
    best_estimate = None
    all_betas: list[dict[str, float]] = []
    all_etas: list[dict[str, float]] = []

    for _ in range(restarts):
        init_beta = float(np.clip(rng.uniform(0.05, 0.2), 0.01, 0.49))
        init_eta = float(np.clip(rng.uniform(0.05, 0.2), 0.01, 0.49))

        estimate = em_fit(
            domain,
            states,
            data,
            max_iterations=max_iterations,
            tolerance=tolerance,
            initial_beta=init_beta,
            initial_eta=init_eta,
        )

        all_betas.append(dict(estimate.params.beta))
        all_etas.append(dict(estimate.params.eta))

        if estimate.log_likelihood > best_ll:
            best_ll = estimate.log_likelihood
            best_estimate = estimate

    assert best_estimate is not None

    # Identifiability check: parameter variance across restarts
    identifiable = _check_identifiability(all_betas, all_etas)

    item_calibrations = tuple(
        ItemCalibration(
            item_id=iid,
            beta=best_estimate.params.beta[iid],
            eta=best_estimate.params.eta[iid],
        )
        for iid in sorted(domain.item_ids)
    )

    return CalibrationResult(
        params=best_estimate.params,
        item_calibrations=item_calibrations,
        log_likelihood=best_ll,
        converged=best_estimate.converged,
        restarts=restarts,
        identifiable=identifiable,
    )


def _check_identifiability(
    all_betas: list[dict[str, float]],
    all_etas: list[dict[str, float]],
    threshold: float = 0.1,
) -> bool:
    """Check parameter identifiability across restarts.

    Parameters are considered identifiable if the standard deviation
    across restarts is below the threshold for all items.
    """
    if len(all_betas) < 2:
        return True

    for item_id in all_betas[0]:
        beta_vals = [b[item_id] for b in all_betas]
        eta_vals = [e[item_id] for e in all_etas]
        if np.std(beta_vals) > threshold or np.std(eta_vals) > threshold:
            return False
    return True


# ---------------------------------------------------------------------------
# 2. optimal_teaching_sequence — MDP value iteration
# ---------------------------------------------------------------------------


def optimal_teaching_sequence(
    space: LearningSpace,
    rates: LearningRate | None = None,
    start: KnowledgeState | None = None,
) -> TeachingPlan:
    """Compute the optimal teaching sequence via MDP value iteration.

    V*(Q) = 0
    V*(K) = 1 + min_{q ∈ OF(K)} V*(K ∪ {q})

    If rates are provided, they are used as tie-breakers: among items
    with equal V*, prefer the one with the highest learning rate.

    Args:
        space: The learning space.
        rates: Optional learning rates for tie-breaking.
        start: Starting state (default: empty set).

    Returns:
        TeachingPlan with optimal sequence of items to teach.
    """
    if start is None:
        start = KnowledgeState()

    full = space.domain.full_state
    state_list = sorted(space.states, key=lambda s: (-len(s), sorted(s.item_ids)))

    # Value iteration (backward induction)
    values: dict[KnowledgeState, float] = {full: 0.0}
    policy: dict[KnowledgeState, str] = {}

    for state in state_list:
        if state == full:
            continue
        fringe = space.outer_fringe(state)
        best_item = ""
        best_value = math.inf

        for item in sorted(fringe):
            next_state = KnowledgeState(items=state.items | {item})
            v = 1.0 + values.get(next_state, math.inf)
            rate_bonus = rates.rates.get(item.id, 0.0) if rates else 0.0

            if v < best_value or (v == best_value and rate_bonus > 0):
                best_value = v
                best_item = item.id

        values[state] = best_value
        policy[state] = best_item

    # Extract plan from start to full
    steps: list[TeachingStep] = []
    current = start
    while current != full:
        item_id = policy[current]
        resolved_item = space.domain.get_item(item_id)
        assert resolved_item is not None
        next_state = KnowledgeState(items=current.items | {resolved_item})
        steps.append(
            TeachingStep(
                item_id=item_id,
                from_state_ids=current.item_ids,
                to_state_ids=next_state.item_ids,
                expected_remaining=values[current],
            )
        )
        current = next_state

    return TeachingPlan(
        steps=tuple(steps),
        total_expected_steps=values.get(start, 0.0),
    )


# ---------------------------------------------------------------------------
# 3. estimate_item_difficulty
# ---------------------------------------------------------------------------


def estimate_item_difficulty(
    domain: Domain,
    graph: PrerequisiteGraph,
    data: ResponseData | None = None,
    params: BLIMParameters | None = None,
) -> DifficultyReport:
    """Estimate item difficulty using structural and/or empirical methods.

    Combines up to three sources:
    - Structural: DAG depth (number of transitive prerequisites)
    - Empirical: error rate from response data
    - BLIM: difficulty = β + (1 - η) from calibrated parameters

    Args:
        domain: The knowledge domain.
        graph: The prerequisite DAG.
        data: Optional response data for empirical estimates.
        params: Optional BLIM parameters for model-based estimates.

    Returns:
        DifficultyReport with per-item difficulty estimates.
    """
    sr = graph.to_surmise_relation()
    items_list: list[ItemDifficulty] = []

    # Structural difficulty: count of transitive prerequisites
    max_depth = max(
        (len(sr.prerequisites_of(iid)) for iid in domain.item_ids),
        default=0,
    )
    norm = max_depth if max_depth > 0 else 1

    for item_id in sorted(domain.item_ids):
        depth = len(sr.prerequisites_of(item_id))
        structural = depth / norm

        # Empirical difficulty
        empirical: float | None = None
        if data is not None:
            incorrect_count = sum(
                1 for p in data.patterns if not p[item_id]
            )
            empirical = incorrect_count / len(data.patterns)

        # BLIM difficulty: β + (1 - η) captures "hard to show mastery"
        blim: float | None = None
        if params is not None:
            blim = params.beta[item_id] + (1.0 - params.eta[item_id])

        # Combined: weighted average of available sources
        sources: list[float] = [structural]
        if empirical is not None:
            sources.append(empirical)
        if blim is not None:
            sources.append(blim / 2.0)  # Scale BLIM to ~[0,1]

        combined = sum(sources) / len(sources)

        items_list.append(
            ItemDifficulty(
                item_id=item_id,
                structural_depth=depth,
                structural_difficulty=round(structural, 4),
                empirical_difficulty=round(empirical, 4) if empirical is not None else None,
                blim_difficulty=round(blim, 4) if blim is not None else None,
                combined_difficulty=round(combined, 4),
            )
        )

    method_parts = ["structural"]
    if data is not None:
        method_parts.append("empirical")
    if params is not None:
        method_parts.append("blim")

    return DifficultyReport(
        items=tuple(items_list),
        method="+".join(method_parts),
    )


# ---------------------------------------------------------------------------
# 4. tune_learning_rates — MLE on Markov chain
# ---------------------------------------------------------------------------


def tune_learning_rates(
    space: LearningSpace,
    data: TrajectoryData,
    *,
    max_iterations: int = 200,
    tolerance: float = 1e-6,
    initial_rate: float = 1.0,
) -> TunedRates:
    """Tune per-item learning rates from observed trajectories via MLE.

    Maximizes the log-likelihood of the observed Markov chain transitions:

    log L(λ) = Σ_t Σ_transitions log P(K_{t+1} | K_t, λ)

    where P(K → K ∪ {q}) = λ_q / Σ_{q' ∈ OF(K)} λ_{q'}

    Uses iterative proportional fitting (a form of EM):
    λ_q^{new} = n_q / Σ_{transitions where q ∈ OF} (1 / Σ_{q' ∈ OF} λ_{q'})

    Args:
        space: The learning space.
        data: Observed learning trajectories.
        max_iterations: Maximum iterations.
        tolerance: Convergence threshold.
        initial_rate: Initial rate for all items.

    Returns:
        TunedRates with fitted learning rates.
    """
    item_ids = sorted(space.domain.item_ids)
    n_items = len(item_ids)
    item_idx = {iid: i for i, iid in enumerate(item_ids)}

    # Count transitions: for each item q, count how many times
    # a learner acquired q (transitioned from K to K union {q})
    acquire_count = np.zeros(n_items)
    # For denominator: sum of (1/total_rate) over all transitions
    # where item q was in the outer fringe
    fringe_exposure = np.zeros(n_items)

    # Pre-compute outer fringes
    fringe_cache: dict[frozenset[str], frozenset[str]] = {}

    for traj in data.trajectories:
        for t in range(len(traj) - 1):
            current_ids = traj[t]
            next_ids = traj[t + 1]
            acquired = next_ids - current_ids

            if not acquired:
                continue

            # Get outer fringe from cache
            key = current_ids
            if key not in fringe_cache:
                resolved = [
                    space.domain.get_item(iid)
                    for iid in current_ids
                ]
                current_state = KnowledgeState(
                    items=frozenset(it for it in resolved if it is not None)
                )
                if current_state in space.states:
                    of = space.outer_fringe(current_state)
                    fringe_cache[key] = frozenset(item.id for item in of)
                else:
                    fringe_cache[key] = frozenset()

            fringe_ids = fringe_cache[key]
            for acq_id in acquired:
                if acq_id in item_idx:
                    acquire_count[item_idx[acq_id]] += 1

    # Iterative rate estimation
    rates = np.full(n_items, initial_rate)
    prev_ll = -np.inf
    converged = False
    n_iter = 0

    for n_iter in range(1, max_iterations + 1):
        # Compute log-likelihood and update exposure
        fringe_exposure[:] = 0.0
        ll = 0.0

        for traj in data.trajectories:
            for t in range(len(traj) - 1):
                current_ids = traj[t]
                next_ids = traj[t + 1]
                acquired = next_ids - current_ids

                if not acquired:
                    continue

                fringe_ids = fringe_cache.get(current_ids, frozenset())
                if not fringe_ids:
                    continue

                total_rate = sum(
                    rates[item_idx[fid]] for fid in fringe_ids if fid in item_idx
                )

                if total_rate <= 0:  # pragma: no cover
                    continue

                for acq_id in acquired:
                    if acq_id in item_idx:
                        ll += math.log(max(rates[item_idx[acq_id]] / total_rate, 1e-15))

                inv_total = 1.0 / total_rate
                for fid in fringe_ids:
                    if fid in item_idx:
                        fringe_exposure[item_idx[fid]] += inv_total

        if n_iter > 1 and abs(ll - prev_ll) < tolerance:
            converged = True
            break
        prev_ll = ll

        # M-step: update rates
        for i in range(n_items):
            if fringe_exposure[i] > 0:
                rates[i] = max(acquire_count[i] / fringe_exposure[i], 1e-10)
            else:
                rates[i] = initial_rate

    # Normalize rates so max = 1
    max_rate = float(np.max(rates)) if np.max(rates) > 0 else 1.0
    rates = rates / max_rate

    rate_dict = {iid: max(float(rates[i]), 1e-10) for i, iid in enumerate(item_ids)}
    learning_rate = LearningRate(domain=space.domain, rates=rate_dict)

    return TunedRates(
        rates=learning_rate,
        log_likelihood=float(prev_ll),
        converged=converged,
        iterations=n_iter,
    )
