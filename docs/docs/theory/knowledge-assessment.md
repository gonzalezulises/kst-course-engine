---
sidebar_position: 4
title: "Knowledge Assessment"
---

# Knowledge Assessment

This chapter presents the probabilistic framework for **adaptive knowledge assessment** within Knowledge Space Theory. The **Basic Local Independence Model (BLIM)** assigns probabilities to knowledge states and models response errors. We develop the maximum likelihood estimation theory and describe the adaptive assessment procedure that iteratively narrows the set of plausible states.

**Primary reference**: Falmagne, J.-C. & Doignon, J.-P. (2011). *Learning Spaces: Interdisciplinary Applied Mathematics*. Springer, Chapter 12.

---

## 4.1 The Basic Local Independence Model

### Definition 4.1 (BLIM -- Basic Local Independence Model)

> Let $(Q, \mathcal{K})$ be a knowledge structure with $|Q| = n$ and $|\mathcal{K}| = m$. The **Basic Local Independence Model** is a probabilistic model specified by the following parameters:
>
> 1. **State probabilities**: A probability distribution $\pi$ over the knowledge states:
>
> $$
> \pi: \mathcal{K} \to [0, 1], \qquad \sum_{K \in \mathcal{K}} \pi(K) = 1, \qquad \pi(K) \geq 0 \;\;\forall K \in \mathcal{K}
> $$
>
> 2. **Careless error (slip) probabilities**: For each item $q \in Q$:
>
> $$
> \beta_q = P(\text{incorrect response to } q \mid q \in K) \in [0, 1)
> $$
>
> The probability that a learner in state $K$ with $q \in K$ (who has mastered $q$) gives an incorrect response.
>
> 3. **Lucky guess probabilities**: For each item $q \in Q$:
>
> $$
> \eta_q = P(\text{correct response to } q \mid q \notin K) \in [0, 1)
> $$
>
> The probability that a learner in state $K$ with $q \notin K$ (who has not mastered $q$) gives a correct response.

The **local independence** assumption states that, conditional on the knowledge state $K$, the responses to different items are **stochastically independent**.

Let $R \subseteq Q$ denote the **response pattern** (the set of items answered correctly). The probability of observing response pattern $R$ given knowledge state $K$ is:

$$
P(R \mid K) = \prod_{q \in K \cap R} (1 - \beta_q) \cdot \prod_{q \in K \setminus R} \beta_q \cdot \prod_{q \in R \setminus K} \eta_q \cdot \prod_{q \in Q \setminus (K \cup R)} (1 - \eta_q)
$$

More compactly, partitioning items into four groups:

| Category | Items | Probability factor |
|----------|-------|--------------------|
| Mastered, correct | $q \in K \cap R$ | $1 - \beta_q$ |
| Mastered, incorrect (slip) | $q \in K \setminus R$ | $\beta_q$ |
| Unmastered, correct (guess) | $q \in R \setminus K$ | $\eta_q$ |
| Unmastered, incorrect | $q \in Q \setminus (K \cup R)$ | $1 - \eta_q$ |

The **marginal probability** of response pattern $R$ is:

$$
P(R) = \sum_{K \in \mathcal{K}} \pi(K) \cdot P(R \mid K)
$$

---

## 4.2 Maximum Likelihood Estimation

### Theorem 4.1 (Maximum Likelihood Estimation for BLIM)

> Given a dataset of $N$ independent response patterns $\{R_1, R_2, \ldots, R_N\}$, the **log-likelihood** function is:
>
> $$
> \ell(\theta) = \sum_{j=1}^{N} \log P(R_j \mid \theta) = \sum_{j=1}^{N} \log \left( \sum_{K \in \mathcal{K}} \pi(K) \prod_{q \in Q} P_q(R_j, K) \right)
> $$
>
> where $\theta = (\pi, \beta, \eta)$ is the full parameter vector and $P_q(R, K)$ is the per-item response probability.
>
> The MLE $\hat{\theta}$ is obtained by maximizing $\ell(\theta)$ subject to:
>
> $$
> \sum_{K \in \mathcal{K}} \pi(K) = 1, \qquad 0 \leq \beta_q < 1, \qquad 0 \leq \eta_q < 1 \quad \forall q \in Q.
> $$

**EM Algorithm for BLIM.** The log-likelihood involves a mixture and is typically maximized via the **Expectation-Maximization (EM)** algorithm.

**E-step.** Compute the posterior probability that learner $j$ is in state $K$:

$$
w_{jK} = P(K \mid R_j, \theta^{(t)}) = \frac{\pi^{(t)}(K) \cdot P(R_j \mid K, \theta^{(t)})}{\sum_{K' \in \mathcal{K}} \pi^{(t)}(K') \cdot P(R_j \mid K', \theta^{(t)})}
$$

**M-step.** Update parameter estimates:

$$
\pi^{(t+1)}(K) = \frac{1}{N} \sum_{j=1}^{N} w_{jK}
$$

$$
\beta_q^{(t+1)} = \frac{\sum_{j=1}^{N} \sum_{K: q \in K} w_{jK} \cdot \mathbf{1}[q \notin R_j]}{\sum_{j=1}^{N} \sum_{K: q \in K} w_{jK}}
$$

$$
\eta_q^{(t+1)} = \frac{\sum_{j=1}^{N} \sum_{K: q \notin K} w_{jK} \cdot \mathbf{1}[q \in R_j]}{\sum_{j=1}^{N} \sum_{K: q \notin K} w_{jK}}
$$

**Convergence:** The EM algorithm monotonically increases the log-likelihood and converges to a local maximum (or saddle point) of $\ell(\theta)$. Global convergence is not guaranteed; multiple restarts with random initializations are recommended.

---

## 4.3 Adaptive Assessment Procedure

### Algorithm 4.1 (Adaptive Knowledge Assessment)

The adaptive assessment procedure identifies a learner's knowledge state by iteratively selecting informative items and updating a **belief distribution** over knowledge states.

**Input:**
- Knowledge space $(Q, \mathcal{K})$
- Error parameters $\beta_q, \eta_q$ for all $q \in Q$
- Prior distribution $\pi^{(0)}(K)$ for $K \in \mathcal{K}$ (e.g., uniform)
- Stopping criterion (e.g., entropy threshold $\epsilon$ or maximum number of questions $T$)

**Output:** Estimated knowledge state $\hat{K}$

**Procedure:**

```
function ADAPTIVE_ASSESS(Q, K, β, η, π⁰, ε, T):
    π ← π⁰
    asked ← ∅
    t ← 0

    while H(π) > ε and t < T:
        # 1. SELECT the most informative item
        q* ← argmax_{q ∈ Q \ asked} I(q; π)

        # 2. ADMINISTER item q* and observe response r ∈ {0, 1}
        r ← observe_response(q*)

        # 3. UPDATE belief distribution (Bayesian update)
        for each K ∈ K:
            if r = 1:  # correct
                L(K) ← (1 - β_{q*}) if q* ∈ K else η_{q*}
            else:       # incorrect
                L(K) ← β_{q*} if q* ∈ K else (1 - η_{q*})
            π(K) ← π(K) · L(K)

        # Normalize
        Z ← Σ_{K ∈ K} π(K)
        π(K) ← π(K) / Z  for all K

        asked ← asked ∪ {q*}
        t ← t + 1

    # Return MAP estimate
    K̂ ← argmax_{K ∈ K} π(K)
    return K̂
```

**Item selection criterion.** The information gain $I(q; \pi)$ of item $q$ is typically measured by the **expected reduction in Shannon entropy**:

$$
I(q; \pi) = H(\pi) - \mathbb{E}_r\bigl[H(\pi \mid r_q)\bigr]
$$

where $H(\pi) = -\sum_{K \in \mathcal{K}} \pi(K) \log \pi(K)$ is the entropy of the current belief, and the expectation is over the binary response $r_q$:

$$
I(q; \pi) = H(\pi) - P(r_q = 1) \cdot H(\pi \mid r_q = 1) - P(r_q = 0) \cdot H(\pi \mid r_q = 0)
$$

with:

$$
P(r_q = 1) = \sum_{K \in \mathcal{K}} \pi(K) \left[ (1 - \beta_q) \cdot \mathbf{1}[q \in K] + \eta_q \cdot \mathbf{1}[q \notin K] \right]
$$

---

## 4.4 Likelihood Ratios for State Discrimination

### Definition 4.2 (Likelihood Ratio)

> For two candidate knowledge states $K_1, K_2 \in \mathcal{K}$ and an observed response pattern $R$, the **likelihood ratio** is:
>
> $$
> \Lambda(K_1, K_2; R) = \frac{P(R \mid K_1)}{P(R \mid K_2)} = \prod_{q \in Q} \frac{P_q(R, K_1)}{P_q(R, K_2)}
> $$

The likelihood ratio factorizes by item (due to local independence). For a single item $q$ with observed response $r_q \in \{0, 1\}$:

$$
\frac{P_q(r_q \mid K_1)}{P_q(r_q \mid K_2)} = \begin{cases}
\dfrac{1 - \beta_q}{\eta_q} & \text{if } q \in K_1,\; q \notin K_2,\; r_q = 1 \\[10pt]
\dfrac{\beta_q}{1 - \eta_q} & \text{if } q \in K_1,\; q \notin K_2,\; r_q = 0 \\[10pt]
\dfrac{\eta_q}{1 - \beta_q} & \text{if } q \notin K_1,\; q \in K_2,\; r_q = 1 \\[10pt]
\dfrac{1 - \eta_q}{\beta_q} & \text{if } q \notin K_1,\; q \in K_2,\; r_q = 0 \\[10pt]
1 & \text{if } q \in K_1 \cap K_2 \text{ or } q \notin K_1 \cup K_2
\end{cases}
$$

**Interpretation:** When both $\beta_q$ and $\eta_q$ are small (low error rates):
- A correct response to $q$ strongly favors the state containing $q$ (ratio $\approx 1/\eta_q \gg 1$).
- An incorrect response to $q$ strongly favors the state not containing $q$ (ratio $\approx \beta_q \ll 1$).

**Sequential probability ratio test (SPRT).** For distinguishing between two states $K_1$ and $K_2$, one can administer items in the **symmetric difference** $K_1 \triangle K_2$ (the only items that discriminate between the states) and apply a sequential likelihood ratio test with thresholds $A$ and $B$:

$$
\text{Accept } K_1 \text{ if } \Lambda \geq A, \qquad \text{Accept } K_2 \text{ if } \Lambda \leq B, \qquad \text{Continue otherwise.}
$$

The optimal item to administer next is the one in $K_1 \triangle K_2$ that maximizes the expected Kullback-Leibler divergence:

$$
q^* = \arg\max_{q \in K_1 \triangle K_2} D_{\text{KL}}\!\bigl(P(\cdot \mid K_1) \,\|\, P(\cdot \mid K_2)\bigr) \Big|_{\text{item } q}
$$

where the per-item KL divergence is:

$$
D_{\text{KL}}^{(q)}(K_1 \| K_2) = P(r_q = 1 \mid K_1) \log \frac{P(r_q = 1 \mid K_1)}{P(r_q = 1 \mid K_2)} + P(r_q = 0 \mid K_1) \log \frac{P(r_q = 0 \mid K_1)}{P(r_q = 0 \mid K_2)}
$$

---

## 4.5 Model Identifiability and Goodness of Fit

The BLIM has $|\mathcal{K}| - 1 + 2|Q|$ free parameters ($m - 1$ state probabilities, $n$ slip parameters, $n$ guess parameters). For the model to be **identifiable**, the number of observable degrees of freedom ($2^n - 1$ for the full response distribution) must exceed the number of parameters:

$$
2^n - 1 \;\geq\; |\mathcal{K}| - 1 + 2n
$$

$$
|\mathcal{K}| \;\leq\; 2^n - 2n
$$

When this condition is violated, the model is **overparameterized** and additional constraints (e.g., equal error rates $\beta_q = \beta$, $\eta_q = \eta$) are needed.

**Goodness of fit** is typically assessed via the **chi-squared statistic** or the **likelihood ratio test**:

$$
G^2 = 2 \sum_{R \subseteq Q} N_R \log \frac{N_R / N}{\hat{P}(R)}
$$

where $N_R$ is the observed frequency of response pattern $R$ and $\hat{P}(R)$ is the predicted probability under the fitted model.

---

## References

1. Falmagne, J.-C. & Doignon, J.-P. (2011). *Learning Spaces: Interdisciplinary Applied Mathematics*. Springer.
2. Doignon, J.-P. & Falmagne, J.-C. (1999). *Knowledge Spaces*. Springer-Verlag.
3. Heller, J. & Wickelmaier, F. (2013). Minimum discrepancy estimation in probabilistic knowledge structures. *Electronic Notes in Discrete Mathematics*, 42, 49--56.
4. Dempster, A. P., Laird, N. M., & Rubin, D. B. (1977). Maximum likelihood from incomplete data via the EM algorithm. *Journal of the Royal Statistical Society: Series B*, 39(1), 1--38.
5. Wald, A. (1945). Sequential tests of statistical hypotheses. *Annals of Mathematical Statistics*, 16(2), 117--186.
