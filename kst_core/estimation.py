"""BLIM parameter estimation via the Expectation-Maximization algorithm.

Implements Maximum Likelihood Estimation (MLE) for the Basic Local Independence
Model. Given observed response patterns, estimates:
- State probabilities π(K)
- Slip parameters β_q
- Guess parameters η_q

The EM algorithm iterates:
    E-step: w_{jK} = P(K | R_j, θ^t) — posterior state probabilities
    M-step: θ^{t+1} = argmax E[log L(θ | K)] — updated parameters

References:
    Falmagne, J.-Cl. & Doignon, J.-P. (2011). Learning Spaces, Ch. 12.
    Dempster, A. P., Laird, N. M., & Rubin, D. B. (1977). Maximum likelihood
        from incomplete data via the EM algorithm.
"""

from __future__ import annotations

import math

import numpy as np
from pydantic import BaseModel, field_validator, model_validator

from kst_core.assessment import BeliefState, BLIMParameters
from kst_core.domain import Domain, KnowledgeState  # noqa: TC001

_EPS = 1e-15


class ResponseData(BaseModel, frozen=True):
    """Collection of observed response patterns.

    Each pattern maps item_id → bool (True = correct response).
    All patterns must cover exactly the domain items.
    """

    domain: Domain
    patterns: tuple[dict[str, bool], ...]

    model_config = {"arbitrary_types_allowed": True}

    @field_validator("patterns")
    @classmethod
    def at_least_one_pattern(
        cls, v: tuple[dict[str, bool], ...]
    ) -> tuple[dict[str, bool], ...]:
        if len(v) == 0:
            msg = "Must have at least one response pattern"
            raise ValueError(msg)
        return v

    @model_validator(mode="after")
    def patterns_match_domain(self) -> ResponseData:
        domain_ids = self.domain.item_ids
        for i, pattern in enumerate(self.patterns):
            if set(pattern.keys()) != domain_ids:
                msg = f"Pattern {i} keys do not match domain item IDs"
                raise ValueError(msg)
        return self


class BLIMEstimate(BaseModel, frozen=True):
    """Result of EM parameter estimation.

    Contains fitted BLIM parameters, estimated state distribution π(K),
    final log-likelihood, and convergence diagnostics.
    """

    params: BLIMParameters
    belief: BeliefState
    log_likelihood: float
    iterations: int
    converged: bool

    model_config = {"arbitrary_types_allowed": True}


class GoodnessOfFit(BaseModel, frozen=True):
    """Goodness-of-fit statistics for a fitted BLIM.

    G² = 2 Σ_R N_R log(N_R / (N · P̂(R)))

    where N_R is the observed count of pattern R and P̂(R) is the
    model-predicted probability.
    """

    g_squared: float
    degrees_of_freedom: int
    n_response_patterns: int
    n_observations: int


def em_fit(
    domain: Domain,
    states: frozenset[KnowledgeState],
    data: ResponseData,
    *,
    max_iterations: int = 1000,
    tolerance: float = 1e-6,
    initial_beta: float = 0.1,
    initial_eta: float = 0.1,
) -> BLIMEstimate:
    """Fit BLIM parameters using the EM algorithm.

    Estimates π(K), β_q, η_q that maximize the log-likelihood
    of the observed response patterns.

    Args:
        domain: The knowledge domain Q.
        states: Knowledge states K ⊆ 2^Q.
        data: Observed response patterns.
        max_iterations: Maximum EM iterations.
        tolerance: Convergence threshold on log-likelihood change.
        initial_beta: Initial slip probability for all items.
        initial_eta: Initial guess probability for all items.

    Returns:
        BLIMEstimate with fitted parameters and convergence diagnostics.
    """
    item_ids = sorted(domain.item_ids)
    item_idx = {iid: i for i, iid in enumerate(item_ids)}
    n_items = len(item_ids)
    state_list = sorted(states, key=lambda s: (len(s), sorted(s.item_ids)))
    n_states = len(state_list)

    # Membership matrix: membership[k, q] = (item q ∈ state K_k)
    membership = np.zeros((n_states, n_items), dtype=bool)
    for k, state in enumerate(state_list):
        for iid in state.item_ids:
            membership[k, item_idx[iid]] = True

    # Response matrix: responses[j, q] = (subject j answered item q correctly)
    responses = np.zeros((len(data.patterns), n_items), dtype=bool)
    for j, pattern in enumerate(data.patterns):
        for iid, correct in pattern.items():
            responses[j, item_idx[iid]] = correct

    # Initialize parameters
    pi = np.full(n_states, 1.0 / n_states)
    beta = np.clip(np.full(n_items, initial_beta), _EPS, 0.5 - _EPS)
    eta = np.clip(np.full(n_items, initial_eta), _EPS, 0.5 - _EPS)

    prev_ll = -np.inf
    converged = False
    ll = float(-np.inf)
    n_iter = 0

    for n_iter in range(1, max_iterations + 1):
        # E-step: compute posterior w[j, k] = P(K_k | R_j, θ)
        log_lik = _compute_log_likelihoods(responses, membership, beta, eta)
        log_pi = np.log(np.maximum(pi, _EPS))
        log_joint = log_lik + log_pi[np.newaxis, :]
        log_z = _logsumexp(log_joint, axis=1)
        w = np.exp(log_joint - log_z[:, np.newaxis])
        ll = float(np.sum(log_z))

        # Check convergence (skip first iteration)
        if n_iter > 1 and abs(ll - prev_ll) < tolerance:
            converged = True
            break
        prev_ll = ll

        # M-step: update π, β, η
        pi, beta, eta = _m_step(w, responses, membership)

    # Build result
    beta_final = np.clip(beta, 0.0, 0.4999)
    eta_final = np.clip(eta, 0.0, 0.4999)

    params = BLIMParameters(
        domain=domain,
        beta={iid: float(beta_final[i]) for i, iid in enumerate(item_ids)},
        eta={iid: float(eta_final[i]) for i, iid in enumerate(item_ids)},
    )

    probs = tuple(float(p) for p in pi)
    total = sum(probs)
    probs = tuple(p / total for p in probs)

    belief = BeliefState(
        states=tuple(state_list),
        probabilities=probs,
    )

    return BLIMEstimate(
        params=params,
        belief=belief,
        log_likelihood=ll,
        iterations=n_iter,
        converged=converged,
    )


def goodness_of_fit(
    data: ResponseData,
    estimate: BLIMEstimate,
    states: frozenset[KnowledgeState],
) -> GoodnessOfFit:
    """Compute the G² (likelihood ratio) goodness-of-fit statistic.

    G² = 2 Σ_R N_R log(N_R / (N · P̂(R)))

    A lower G² indicates better fit. Under the null hypothesis that the
    model is correct, G² is asymptotically χ²-distributed.

    Args:
        data: Observed response patterns.
        estimate: Fitted BLIM estimate.
        states: Knowledge states used in estimation.

    Returns:
        GoodnessOfFit with G², degrees of freedom, and counts.
    """
    n_obs = len(data.patterns)
    n_items = len(data.domain)
    item_ids = sorted(data.domain.item_ids)

    # Count unique response patterns
    pattern_counts: dict[tuple[bool, ...], int] = {}
    for pattern in data.patterns:
        key = tuple(pattern[iid] for iid in item_ids)
        pattern_counts[key] = pattern_counts.get(key, 0) + 1

    # Compute G²
    g_squared = 0.0
    for key, count in pattern_counts.items():
        pattern = dict(zip(item_ids, key, strict=True))
        p_predicted = _pattern_probability(pattern, estimate)
        p_predicted = max(p_predicted, _EPS)
        p_observed = count / n_obs
        g_squared += 2.0 * count * math.log(p_observed / p_predicted)

    # Degrees of freedom: (unique patterns - 1) - free parameters
    n_states = len(states)
    n_free_params = (n_states - 1) + 2 * n_items
    n_unique = len(pattern_counts)
    dof = max(n_unique - 1 - n_free_params, 1)

    return GoodnessOfFit(
        g_squared=g_squared,
        degrees_of_freedom=dof,
        n_response_patterns=n_unique,
        n_observations=n_obs,
    )


def _compute_log_likelihoods(
    responses: np.ndarray,
    membership: np.ndarray,
    beta: np.ndarray,
    eta: np.ndarray,
) -> np.ndarray:
    """Compute log P(R_j | K_k) for all (j, k) pairs.

    Uses vectorized computation:
        log P(R_j | K_k) = Σ_q log P_q(r_{jq} | K_k)

    Returns:
        Array of shape (N, m) where N = observations, m = states.
    """
    # Per-item log-probabilities
    log_1mb = np.log(np.maximum(1.0 - beta, _EPS))
    log_b = np.log(np.maximum(beta, _EPS))
    log_e = np.log(np.maximum(eta, _EPS))
    log_1me = np.log(np.maximum(1.0 - eta, _EPS))

    # log P_q(r | q ∈ K): correct → log(1-β), incorrect → log(β)
    log_p_in = np.where(responses, log_1mb, log_b)  # (N, n)
    # log P_q(r | q ∉ K): correct → log(η), incorrect → log(1-η)
    log_p_out = np.where(responses, log_e, log_1me)  # (N, n)

    # log P(R_j | K_k) = Σ_q [log_p_out + membership * (log_p_in - log_p_out)]
    diff = log_p_in - log_p_out  # (N, n)
    base = np.sum(log_p_out, axis=1)  # (N,)
    contrib = diff @ membership.astype(float).T  # (N, m)

    result: np.ndarray = base[:, np.newaxis] + contrib  # (N, m)
    return result


def _logsumexp(x: np.ndarray, axis: int) -> np.ndarray:
    """Numerically stable log-sum-exp along an axis."""
    x_max = np.max(x, axis=axis, keepdims=True)
    result: np.ndarray = np.squeeze(x_max, axis=axis) + np.log(
        np.sum(np.exp(x - x_max), axis=axis)
    )
    return result


def _m_step(
    w: np.ndarray,
    responses: np.ndarray,
    membership: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """M-step: update π, β, η from posterior weights.

    π(K) = (1/N) Σ_j w_{jK}
    β_q = Σ_j Σ_{K: q∈K} w_{jK} · (1-r_{jq}) / Σ_j Σ_{K: q∈K} w_{jK}
    η_q = Σ_j Σ_{K: q∉K} w_{jK} · r_{jq} / Σ_j Σ_{K: q∉K} w_{jK}
    """
    # π[k] = mean of posterior weights
    pi = np.mean(w, axis=0)
    pi = np.maximum(pi, _EPS)
    pi /= pi.sum()

    # Weighted sums for states containing/not containing each item
    membership_f = membership.astype(float)
    w_in = w @ membership_f  # (N, n)
    w_out = w @ (1.0 - membership_f)  # (N, n)

    # β_q: fraction of "in-state" weight that was incorrect
    incorrect = ~responses
    beta_num = np.sum(w_in * incorrect, axis=0)
    beta_den = np.sum(w_in, axis=0)
    beta = np.where(beta_den > _EPS, beta_num / beta_den, _EPS)

    # η_q: fraction of "out-of-state" weight that was correct
    eta_num = np.sum(w_out * responses, axis=0)
    eta_den = np.sum(w_out, axis=0)
    eta = np.where(eta_den > _EPS, eta_num / eta_den, _EPS)

    # Clamp to valid range during iteration
    beta = np.clip(beta, _EPS, 0.5 - _EPS)
    eta = np.clip(eta, _EPS, 0.5 - _EPS)

    return pi, beta, eta


def _pattern_probability(
    pattern: dict[str, bool],
    estimate: BLIMEstimate,
) -> float:
    """Compute P(R) = Σ_K π(K) · P(R | K) for a single response pattern."""
    total = 0.0
    for state, pi_k in zip(estimate.belief.states, estimate.belief.probabilities, strict=True):
        if pi_k < _EPS:
            continue
        log_p = 0.0
        for item_id, correct in pattern.items():
            if correct:
                log_p += math.log(
                    max(estimate.params.p_correct(item_id, state), _EPS)
                )
            else:
                log_p += math.log(
                    max(estimate.params.p_incorrect(item_id, state), _EPS)
                )
        total += pi_k * math.exp(log_p)
    return total
