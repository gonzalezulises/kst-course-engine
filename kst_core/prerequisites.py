"""Surmise relations and prerequisite graphs.

Implements the prerequisite structures dual to knowledge spaces:
- SurmiseRelation: a quasi-order (reflexive, transitive) encoding
  which items are prerequisites for which.
- PrerequisiteGraph: a DAG representation using NetworkX.

The Birkhoff theorem establishes a bijection between
quasi-orders on Q and knowledge spaces closed under ∩.

References:
    Doignon, J.-P. & Falmagne, J.-Cl. (1999). Knowledge Spaces, Ch. 3.
    Birkhoff, G. (1937). Rings of sets. Duke Mathematical Journal.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import networkx as nx

if TYPE_CHECKING:
    from collections.abc import Iterator
from pydantic import BaseModel, model_validator

from kst_core.domain import Domain, Item, KnowledgeState


class SurmiseRelation(BaseModel, frozen=True):
    """A surmise relation (quasi-order) on a domain Q.

    A surmise relation σ ⊆ Q × Q is a reflexive and transitive relation.
    (q, r) ∈ σ means: mastering item r requires (surmises) mastering item q.
    Equivalently, q is a prerequisite for r.
    """

    domain: Domain
    pairs: frozenset[tuple[str, str]]

    @model_validator(mode="after")
    def validate_quasi_order(self) -> SurmiseRelation:
        """Validate reflexivity and transitivity."""
        item_ids = self.domain.item_ids

        for pair in self.pairs:
            if pair[0] not in item_ids or pair[1] not in item_ids:
                msg = f"Pair {pair} references items not in domain"
                raise ValueError(msg)

        for item_id in item_ids:
            if (item_id, item_id) not in self.pairs:
                msg = f"Reflexivity violated: ({item_id}, {item_id}) not in relation"
                raise ValueError(msg)

        pair_set = set(self.pairs)
        for a, b in self.pairs:
            for c_id in item_ids:
                if (b, c_id) in pair_set and (a, c_id) not in pair_set:
                    msg = (
                        f"Transitivity violated: ({a}, {b}) and ({b}, {c_id}) "
                        f"in σ but ({a}, {c_id}) not in σ"
                    )
                    raise ValueError(msg)

        return self

    def prerequisites_of(self, item_id: str) -> frozenset[str]:
        """Return all prerequisites of an item: {q : (q, item_id) ∈ σ}."""
        return frozenset(a for a, b in self.pairs if b == item_id and a != item_id)

    def dependents_of(self, item_id: str) -> frozenset[str]:
        """Return all items that depend on this item: {r : (item_id, r) ∈ σ}."""
        return frozenset(b for a, b in self.pairs if a == item_id and b != item_id)

    def is_downset(self, state: KnowledgeState) -> bool:
        """Check if a state is a downset (order ideal) of the quasi-order.

        K is a downset iff: q ∈ K and (r, q) ∈ σ implies r ∈ K.
        """
        state_ids = state.item_ids
        for q_id in state_ids:
            for prereq_id in self.prerequisites_of(q_id):
                if prereq_id not in state_ids:
                    return False
        return True

    def to_knowledge_space_states(self) -> frozenset[KnowledgeState]:
        """Generate all downsets of the quasi-order.

        By Birkhoff's theorem, the set of all downsets of a quasi-order
        forms a knowledge space closed under both ∪ and ∩.
        """
        items_by_id: dict[str, Item] = {}
        for item in self.domain:
            items_by_id[item.id] = item

        item_ids = sorted(self.domain.item_ids)
        n = len(item_ids)
        states: set[KnowledgeState] = set()

        for mask in range(2**n):
            selected_ids = {item_ids[i] for i in range(n) if mask & (1 << i)}
            selected_items = frozenset(items_by_id[iid] for iid in selected_ids)
            candidate = KnowledgeState(items=selected_items)
            if self.is_downset(candidate):
                states.add(candidate)

        return frozenset(states)


class PrerequisiteGraph(BaseModel, frozen=True):
    """A DAG-based prerequisite structure using NetworkX.

    Edges represent direct prerequisite relationships.
    The transitive closure yields the surmise relation.
    """

    domain: Domain
    edges: frozenset[tuple[str, str]]

    model_config = {"arbitrary_types_allowed": True}

    @model_validator(mode="after")
    def validate_dag(self) -> PrerequisiteGraph:
        """Validate that edges form a DAG over the domain."""
        item_ids = self.domain.item_ids

        for a, b in self.edges:
            if a not in item_ids or b not in item_ids:
                msg = f"Edge ({a}, {b}) references items not in domain"
                raise ValueError(msg)
            if a == b:
                msg = f"Self-loop ({a}, {a}) not allowed in prerequisite DAG"
                raise ValueError(msg)

        g = self._build_graph()
        if not nx.is_directed_acyclic_graph(g):
            msg = "Prerequisite graph must be acyclic (DAG)"
            raise ValueError(msg)

        return self

    def _build_graph(self) -> nx.DiGraph[str]:
        """Build a NetworkX DiGraph from domain and edges."""
        g: nx.DiGraph[str] = nx.DiGraph()
        for item in self.domain:
            g.add_node(item.id)
        for a, b in self.edges:
            g.add_edge(a, b)
        return g

    def topological_orders(self) -> Iterator[list[str]]:
        """Yield all topological orderings of the DAG."""
        g = self._build_graph()
        yield from nx.all_topological_sorts(g)

    def to_surmise_relation(self) -> SurmiseRelation:
        """Compute the transitive closure to get a surmise relation."""
        g = self._build_graph()
        tc = nx.transitive_closure(g)

        pairs: set[tuple[str, str]] = set()
        for item_id in self.domain.item_ids:
            pairs.add((item_id, item_id))

        for a, b in tc.edges():
            pairs.add((a, b))

        return SurmiseRelation(domain=self.domain, pairs=frozenset(pairs))

    def critical_path(self) -> list[str]:
        """Find the critical (longest) path in the DAG."""
        g = self._build_graph()
        if not g.edges():
            items = sorted(self.domain.item_ids)
            return items[:1] if items else []

        return list(nx.dag_longest_path(g))

    def longest_path_length(self) -> int:
        """Length of the longest path (number of edges)."""
        g = self._build_graph()
        if not g.edges():
            return 0
        return int(nx.dag_longest_path_length(g))

    def direct_prerequisites(self, item_id: str) -> frozenset[str]:
        """Direct prerequisites (parents in the DAG)."""
        return frozenset(a for a, b in self.edges if b == item_id)

    def direct_dependents(self, item_id: str) -> frozenset[str]:
        """Direct dependents (children in the DAG)."""
        return frozenset(b for a, b in self.edges if a == item_id)
