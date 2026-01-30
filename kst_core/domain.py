"""Domain module — atomic elements, knowledge states, and domains.

Implements the foundational structures of Knowledge Space Theory (KST):
- Item: atomic knowledge element q ∈ Q
- KnowledgeState: subset K ⊆ Q with set operations
- Domain: the finite set Q of all items

References:
    Doignon, J.-P. & Falmagne, J.-Cl. (1999). Knowledge Spaces. Springer.
    Falmagne, J.-Cl. & Doignon, J.-P. (2011). Learning Spaces. Springer.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, field_validator

if TYPE_CHECKING:
    from collections.abc import Iterator


class Item(BaseModel, frozen=True):
    """An atomic knowledge element q ∈ Q.

    Items are the indivisible units of knowledge in a domain.
    Each item has a unique identifier and an optional human-readable label.
    """

    id: str
    label: str = ""

    @field_validator("id")
    @classmethod
    def id_must_be_nonempty(cls, v: str) -> str:
        if not v.strip():
            msg = "Item id must be a non-empty string"
            raise ValueError(msg)
        return v

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Item):
            return self.id == other.id
        return NotImplemented

    def __lt__(self, other: object) -> bool:
        if isinstance(other, Item):
            return self.id < other.id
        return NotImplemented

    def __repr__(self) -> str:
        if self.label:
            return f"Item({self.id!r}, {self.label!r})"
        return f"Item({self.id!r})"


class KnowledgeState(BaseModel, frozen=True):
    """A knowledge state K ⊆ Q represented as a frozenset of Items.

    A knowledge state represents a feasible pattern of mastery:
    the set of items that a learner has mastered.
    """

    items: frozenset[Item] = frozenset()

    def __contains__(self, item: object) -> bool:
        return item in self.items

    def __len__(self) -> int:
        return len(self.items)

    def __iter__(self) -> Iterator[Item]:  # type: ignore[override]
        return iter(sorted(self.items))

    def __le__(self, other: object) -> bool:
        if isinstance(other, KnowledgeState):
            return self.items <= other.items
        return NotImplemented

    def __lt__(self, other: object) -> bool:
        if isinstance(other, KnowledgeState):
            return self.items < other.items
        return NotImplemented

    def __ge__(self, other: object) -> bool:
        if isinstance(other, KnowledgeState):
            return self.items >= other.items
        return NotImplemented

    def __gt__(self, other: object) -> bool:
        if isinstance(other, KnowledgeState):
            return self.items > other.items
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.items)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, KnowledgeState):
            return self.items == other.items
        return NotImplemented

    def __repr__(self) -> str:
        ids = sorted(item.id for item in self.items)
        return f"KnowledgeState({{{', '.join(ids)}}})"

    def union(self, other: KnowledgeState) -> KnowledgeState:
        """K₁ ∪ K₂ — closure under union is an axiom of knowledge spaces."""
        return KnowledgeState(items=self.items | other.items)

    def intersection(self, other: KnowledgeState) -> KnowledgeState:
        """K₁ ∩ K₂ — closure under intersection holds for well-graded spaces."""
        return KnowledgeState(items=self.items & other.items)

    def difference(self, other: KnowledgeState) -> KnowledgeState:
        """K₁ \\ K₂ — set difference."""
        return KnowledgeState(items=self.items - other.items)

    def symmetric_difference(self, other: KnowledgeState) -> KnowledgeState:
        """K₁ △ K₂ — symmetric difference."""
        return KnowledgeState(items=self.items ^ other.items)

    def is_subset_of(self, other: KnowledgeState) -> bool:
        """Check K₁ ⊆ K₂."""
        return self.items <= other.items

    def is_proper_subset_of(self, other: KnowledgeState) -> bool:
        """Check K₁ ⊂ K₂."""
        return self.items < other.items

    @property
    def is_empty(self) -> bool:
        return len(self.items) == 0

    @property
    def item_ids(self) -> frozenset[str]:
        return frozenset(item.id for item in self.items)


class Domain(BaseModel, frozen=True):
    """The domain Q — a finite non-empty set of Items.

    The domain defines the universe of knowledge elements
    under consideration. All knowledge states are subsets of Q.
    """

    items: frozenset[Item]

    @field_validator("items")
    @classmethod
    def must_be_nonempty(cls, v: frozenset[Item]) -> frozenset[Item]:
        if not v:
            msg = "Domain must contain at least one item"
            raise ValueError(msg)
        return v

    def __contains__(self, item: object) -> bool:
        return item in self.items

    def __len__(self) -> int:
        return len(self.items)

    def __iter__(self) -> Iterator[Item]:  # type: ignore[override]
        return iter(sorted(self.items))

    @property
    def full_state(self) -> KnowledgeState:
        """Q as a KnowledgeState — the maximal state."""
        return KnowledgeState(items=self.items)

    @property
    def empty_state(self) -> KnowledgeState:
        """∅ as a KnowledgeState — the minimal state."""
        return KnowledgeState()

    def contains_state(self, state: KnowledgeState) -> bool:
        """Check if K ⊆ Q."""
        return state.items <= self.items

    def get_item(self, item_id: str) -> Item | None:
        """Look up an item by ID."""
        for item in self.items:
            if item.id == item_id:
                return item
        return None

    @property
    def item_ids(self) -> frozenset[str]:
        return frozenset(item.id for item in self.items)
