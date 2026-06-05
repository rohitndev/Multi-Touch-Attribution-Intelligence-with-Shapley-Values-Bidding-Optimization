# Attribution Methodology

This document explains the models behind the platform and why a composite of
Shapley values and Markov removal effects is more defensible than any single
rule-based model.

## 1. Why not last-click?

Last-click assigns 100% of conversion credit to the final touchpoint. It is
simple but structurally wrong: it ignores ~85% of the customer journey and
systematically over-credits bottom-of-funnel channels (Direct, branded Paid
Search) while starving the awareness channels that actually initiate journeys.

## 2. Shapley Values (cooperative game theory)

Channels are players in a cooperative game. The worth of a coalition `S` is the
empirical conversion rate of journeys whose channel set is a subset of `S`
(Shao & Li, 2011 — the same data-driven formulation GA4 uses natively).

The Shapley value of channel *i* is its average marginal contribution over
every ordering of players:

```
phi_i = Σ_{S ⊆ N\{i}} |S|!·(n−|S|−1)!/n! · ( v(S ∪ {i}) − v(S) )
```

Because journeys are capped at **8 distinct channels**, the coalition space is
at most `2^8 = 256` subsets, so we compute the value **exactly** — no
Monte-Carlo permutation sampling. Shapley is the *only* attribution method that
simultaneously satisfies efficiency, symmetry, null-player and additivity — the
axioms that make credit allocation "fair".

Implementation: [`src/attribution/shapley.py`](../src/attribution/shapley.py).

## 3. Markov Chain removal effect

We model journeys as an absorbing Markov chain over
`{start} → channels → {conversion, null}` and estimate transition
probabilities from observed paths. A channel's **removal effect** is the
relative drop in overall conversion probability when it is removed from the
graph. Normalised removal effects give each channel's attribution share.

Implementation: [`src/attribution/markov.py`](../src/attribution/markov.py).

## 4. Composite score

```
composite_share = 0.70 · shapley_share + 0.30 · markov_share
```

Shapley captures *fair marginal contribution*; Markov captures *structural
necessity in the path*. Blending them yields a score that is both fair and
robust to journey-structure quirks. This composite score drives budget
optimisation and the Attribution Advisor agent.

Implementation: [`src/attribution/composite.py`](../src/attribution/composite.py).
