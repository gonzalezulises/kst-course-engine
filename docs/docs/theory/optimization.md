---
id: optimization-theory
title: Optimization Theory
sidebar_label: Optimization Theory
---

# Optimization Theory

Mathematical foundations for the four optimization algorithms.

## 1. Multi-Restart EM Calibration

The BLIM parameters $\beta_q$ (slip) and $\eta_q$ (guess) are estimated via the Expectation-Maximization algorithm. The EM algorithm maximizes the incomplete-data log-likelihood:

$$\ell(\theta) = \sum_{j=1}^N \log \sum_{K \in \mathcal{K}} \pi(K) \prod_{q \in Q} P_q(r_{jq} | K, \theta)$$

**Identifiability**: Not all parameter configurations are identifiable from response data. Following Heller & Wickelmaier (2013), we run multiple restarts with different initial values and check whether estimates converge to consistent solutions.

A model is considered identifiable when the standard deviation of parameter estimates across restarts is below a threshold.

## 2. Optimal Teaching via MDP Value Iteration

Teaching is modeled as a Markov Decision Process where:
- **States**: Knowledge states $K \in \mathcal{K}$
- **Actions**: Items $q \in OF(K)$ (outer fringe)
- **Transitions**: Deterministic: teaching $q$ moves from $K$ to $K \cup \{q\}$
- **Reward**: $-1$ per step (minimize total steps)

The optimal value function satisfies the Bellman equation:

$$V^*(Q) = 0$$
$$V^*(K) = 1 + \min_{q \in OF(K)} V^*(K \cup \{q\})$$

This is solved exactly via backward induction (dynamic programming), processing states in decreasing order of cardinality.

**Reference**: Falmagne & Doignon (2011), Chapter 15.

## 3. Item Difficulty Estimation

Three complementary difficulty measures:

### Structural Difficulty

Based on DAG depth — the number of transitive prerequisites:

$$d_{\text{struct}}(q) = \frac{|\{r : (r, q) \in \sigma, r \neq q\}|}{\max_{q'} |\{r : (r, q') \in \sigma, r \neq q'\}|}$$

### Empirical Difficulty

Error rate from observed response data:

$$d_{\text{emp}}(q) = \frac{\sum_{j} \mathbf{1}[r_{jq} = 0]}{N}$$

### BLIM Difficulty

Based on the calibrated BLIM parameters:

$$d_{\text{BLIM}}(q) = \beta_q + (1 - \eta_q)$$

This captures the probability of an incorrect response regardless of mastery state.

## 4. Learning Rate Tuning

Learning rates $\lambda_q$ govern the Markov chain transition probabilities:

$$P(K \to K \cup \{q\} | K) = \frac{\lambda_q}{\sum_{q' \in OF(K)} \lambda_{q'}}$$

Given observed trajectories, the rates are estimated via maximum likelihood:

$$\log L(\lambda) = \sum_t \sum_{\text{transitions}} \log \frac{\lambda_{q_t}}{\sum_{q' \in OF(K_t)} \lambda_{q'}}$$

The M-step update rule is:

$$\lambda_q^{\text{new}} = \frac{n_q}{\sum_{\text{transitions where } q \in OF} \frac{1}{\sum_{q' \in OF} \lambda_{q'}}}$$

where $n_q$ counts how many times item $q$ was acquired.

## References

- Falmagne, J.-Cl. & Doignon, J.-P. (2011). *Learning Spaces*. Springer.
- Heller, J. & Wickelmaier, F. (2013). How to deal with identifiability. *Psychometrika*, 78(2), 264-279.
- Dempster, A. P., Laird, N. M., & Rubin, D. B. (1977). Maximum likelihood from incomplete data via the EM algorithm.
