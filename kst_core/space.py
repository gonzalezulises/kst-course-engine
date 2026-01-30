"""Knowledge spaces and learning spaces.

Implements the two central structures of KST:
- KnowledgeSpace: a family K of subsets of Q satisfying closure under union
  and containing ∅ and Q (axioms S1, S2, S3).
- LearningSpace: a knowledge space that is also an antimatroid,
  satisfying the accessibility axiom.

References:
    Doignon, J.-P. & Falmagne, J.-Cl. (1999). Knowledge Spaces. Springer.
    Falmagne, J.-Cl. & Doignon, J.-P. (2011). Learning Spaces. Springer.
"""

from __future__ import annotations

from itertools import combinations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

from pydantic import BaseModel, field_validator, model_validator

from kst_core.domain import Domain, Item, KnowledgeState


class KnowledgeSpace(BaseModel, frozen=True):
    """A knowledge space (Q, K).

    A knowledge space satisfies:
    - S1: ∅ ∈ K (the empty set is a state)
    - S2: Q ∈ K (the full domain is a state)
    - S3: K is closed under union (K₁, K₂ ∈ K ⟹ K₁ ∪ K₂ ∈ K)
    """

    domain: Domain
    states: frozenset[KnowledgeState]

    @field_validator("states")
    @classmethod
    def must_be_nonempty(cls, v: frozenset[KnowledgeState]) -> frozenset[KnowledgeState]:
        if not v:
            msg = "Knowledge space must contain at least one state"
            raise ValueError(msg)
        return v

    @model_validator(mode="after")
    def validate_axioms(self) -> KnowledgeSpace:
        """Validate the three axioms of a knowledge space."""
        empty = KnowledgeState()
        if empty not in self.states:
            msg = "Axiom S1 violated: ∅ must be in K"
            raise ValueError(msg)

        full = self.domain.full_state
        if full not in self.states:
            msg = "Axiom S2 violated: Q must be in K"
            raise ValueError(msg)

        for state in self.states:
            if not self.domain.contains_state(state):
                msg = f"State {state} contains items not in domain Q"
                raise ValueError(msg)

        for s1, s2 in combinations(self.states, 2):
            union = s1.union(s2)
            if union not in self.states:
                msg = f"Axiom S3 violated: {s1} ∪ {s2} = {union} is not in K"
                raise ValueError(msg)

        return self

    @property
    def atoms(self) -> frozenset[KnowledgeState]:
        """Minimal non-empty states (atoms of the lattice)."""
        empty = KnowledgeState()
        nonempty = {s for s in self.states if s != empty}
        return frozenset(s for s in nonempty if not any(t.is_proper_subset_of(s) for t in nonempty))

    def inner_fringe(self, state: KnowledgeState) -> frozenset[Item]:
        """Inner fringe of K: items whose removal yields another state.

        I(K) = {q ∈ K : K \\ {q} ∈ K}
        """
        if state not in self.states:
            msg = f"State {state} is not in this knowledge space"
            raise ValueError(msg)

        result: set[Item] = set()
        for item in state:
            reduced = KnowledgeState(items=state.items - {item})
            if reduced in self.states:
                result.add(item)
        return frozenset(result)

    def outer_fringe(self, state: KnowledgeState) -> frozenset[Item]:
        """Outer fringe of K: items whose addition yields another state.

        O(K) = {q ∈ Q \\ K : K ∪ {q} ∈ K}
        """
        if state not in self.states:
            msg = f"State {state} is not in this knowledge space"
            raise ValueError(msg)

        result: set[Item] = set()
        for item in self.domain:
            if item not in state:
                augmented = KnowledgeState(items=state.items | {item})
                if augmented in self.states:
                    result.add(item)
        return frozenset(result)

    def gradation(self) -> list[frozenset[KnowledgeState]]:
        """Partition states into layers by cardinality.

        Returns a list where layer[k] contains all states of size k.
        """
        max_size = len(self.domain)
        layers: list[set[KnowledgeState]] = [set() for _ in range(max_size + 1)]
        for state in self.states:
            layers[len(state)].add(state)
        return [frozenset(layer) for layer in layers if layer]


class LearningSpace(BaseModel, frozen=True):
    """A learning space — an antimatroid on knowledge states.

    A learning space is a knowledge space with the additional property
    of accessibility: for every non-empty state K ∈ K, there exists
    an item q ∈ K such that K \\ {q} ∈ K.

    This ensures that every state can be reached from ∅ by adding
    one item at a time, always staying within the space.
    """

    domain: Domain
    states: frozenset[KnowledgeState]

    @field_validator("states")
    @classmethod
    def must_be_nonempty(cls, v: frozenset[KnowledgeState]) -> frozenset[KnowledgeState]:
        if not v:
            msg = "Learning space must contain at least one state"
            raise ValueError(msg)
        return v

    @model_validator(mode="after")
    def validate_axioms(self) -> LearningSpace:
        """Validate knowledge space axioms + accessibility."""
        empty = KnowledgeState()
        if empty not in self.states:
            msg = "Axiom S1 violated: ∅ must be in K"
            raise ValueError(msg)

        full = self.domain.full_state
        if full not in self.states:
            msg = "Axiom S2 violated: Q must be in K"
            raise ValueError(msg)

        for state in self.states:
            if not self.domain.contains_state(state):
                msg = f"State {state} contains items not in domain Q"
                raise ValueError(msg)

        for s1, s2 in combinations(self.states, 2):
            union = s1.union(s2)
            if union not in self.states:
                msg = f"Axiom S3 violated: {s1} ∪ {s2} = {union} is not in K"
                raise ValueError(msg)

        for state in self.states:
            if state == empty:
                continue
            accessible = False
            for item in state:
                reduced = KnowledgeState(items=state.items - {item})
                if reduced in self.states:
                    accessible = True
                    break
            if not accessible:
                msg = (
                    f"Accessibility violated: state {state} has no item "
                    f"whose removal yields another state in K"
                )
                raise ValueError(msg)

        return self

    @property
    def atoms(self) -> frozenset[KnowledgeState]:
        """Minimal non-empty states."""
        empty = KnowledgeState()
        nonempty = {s for s in self.states if s != empty}
        return frozenset(s for s in nonempty if not any(t.is_proper_subset_of(s) for t in nonempty))

    def inner_fringe(self, state: KnowledgeState) -> frozenset[Item]:
        """Inner fringe: items removable while staying in the space."""
        if state not in self.states:
            msg = f"State {state} is not in this learning space"
            raise ValueError(msg)

        result: set[Item] = set()
        for item in state:
            reduced = KnowledgeState(items=state.items - {item})
            if reduced in self.states:
                result.add(item)
        return frozenset(result)

    def outer_fringe(self, state: KnowledgeState) -> frozenset[Item]:
        """Outer fringe: items addable while staying in the space."""
        if state not in self.states:
            msg = f"State {state} is not in this learning space"
            raise ValueError(msg)

        result: set[Item] = set()
        for item in self.domain:
            if item not in state:
                augmented = KnowledgeState(items=state.items | {item})
                if augmented in self.states:
                    result.add(item)
        return frozenset(result)

    def learning_paths(self) -> list[Sequence[Item]]:
        """Enumerate all learning paths from ∅ to Q.

        A learning path is a sequence (q₁, q₂, ..., qₙ) such that
        {q₁, ..., qₖ} ∈ K for all k = 0, 1, ..., n.
        """
        full = self.domain.full_state
        paths: list[Sequence[Item]] = []

        def _backtrack(current: KnowledgeState, path: list[Item]) -> None:
            if current == full:
                paths.append(tuple(path))
                return
            fringe = self.outer_fringe(current)
            for item in sorted(fringe):
                next_state = KnowledgeState(items=current.items | {item})
                _backtrack(next_state, [*path, item])

        _backtrack(KnowledgeState(), [])
        return paths

    def gradation(self) -> list[frozenset[KnowledgeState]]:
        """Partition states into layers by cardinality."""
        max_size = len(self.domain)
        layers: list[set[KnowledgeState]] = [set() for _ in range(max_size + 1)]
        for state in self.states:
            layers[len(state)].add(state)
        return [frozenset(layer) for layer in layers if layer]
