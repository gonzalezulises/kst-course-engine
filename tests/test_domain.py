"""Tests for kst_core.domain — Items, KnowledgeStates, Domains."""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from kst_core.domain import Domain, Item, KnowledgeState

from .conftest import domains, knowledge_states_from_domain


class TestItem:
    def test_create_item(self) -> None:
        item = Item(id="q1", label="Question 1")
        assert item.id == "q1"
        assert item.label == "Question 1"

    def test_create_item_no_label(self) -> None:
        item = Item(id="q1")
        assert item.label == ""

    def test_item_empty_id_raises(self) -> None:
        with pytest.raises(ValueError, match="non-empty"):
            Item(id="")

    def test_item_whitespace_id_raises(self) -> None:
        with pytest.raises(ValueError, match="non-empty"):
            Item(id="   ")

    def test_item_frozen(self) -> None:
        item = Item(id="q1")
        with pytest.raises(ValidationError):
            item.id = "q2"  # type: ignore[misc]

    def test_item_equality(self) -> None:
        assert Item(id="a") == Item(id="a")
        assert Item(id="a") != Item(id="b")
        assert Item(id="a", label="X") == Item(id="a", label="Y")

    def test_item_hash(self) -> None:
        assert hash(Item(id="a")) == hash(Item(id="a"))
        s = {Item(id="a"), Item(id="a")}
        assert len(s) == 1

    def test_item_lt(self) -> None:
        assert Item(id="a") < Item(id="b")
        assert not Item(id="b") < Item(id="a")

    def test_item_lt_not_implemented(self) -> None:
        assert Item(id="a").__lt__("not_an_item") is NotImplemented

    def test_item_eq_not_implemented(self) -> None:
        assert Item(id="a").__eq__("not_an_item") is NotImplemented

    def test_item_repr(self) -> None:
        assert repr(Item(id="a")) == "Item('a')"
        assert repr(Item(id="a", label="label")) == "Item('a', 'label')"


class TestKnowledgeState:
    def test_empty_state(self) -> None:
        state = KnowledgeState()
        assert len(state) == 0
        assert state.is_empty

    def test_state_with_items(self, item_a: Item, item_b: Item) -> None:
        state = KnowledgeState(items=frozenset({item_a, item_b}))
        assert len(state) == 2
        assert item_a in state
        assert not state.is_empty

    def test_contains(self, item_a: Item, item_b: Item) -> None:
        state = KnowledgeState(items=frozenset({item_a}))
        assert item_a in state
        assert item_b not in state

    def test_contains_non_item(self) -> None:
        state = KnowledgeState()
        assert "not_an_item" not in state

    def test_iter_sorted(self, item_a: Item, item_b: Item, item_c: Item) -> None:
        state = KnowledgeState(items=frozenset({item_c, item_a, item_b}))
        result = list(state)
        assert result == [item_a, item_b, item_c]

    def test_union(self, item_a: Item, item_b: Item, item_c: Item) -> None:
        s1 = KnowledgeState(items=frozenset({item_a}))
        s2 = KnowledgeState(items=frozenset({item_b, item_c}))
        result = s1.union(s2)
        assert result == KnowledgeState(items=frozenset({item_a, item_b, item_c}))

    def test_intersection(self, item_a: Item, item_b: Item) -> None:
        s1 = KnowledgeState(items=frozenset({item_a, item_b}))
        s2 = KnowledgeState(items=frozenset({item_b}))
        assert s1.intersection(s2) == KnowledgeState(items=frozenset({item_b}))

    def test_difference(self, item_a: Item, item_b: Item) -> None:
        s1 = KnowledgeState(items=frozenset({item_a, item_b}))
        s2 = KnowledgeState(items=frozenset({item_b}))
        assert s1.difference(s2) == KnowledgeState(items=frozenset({item_a}))

    def test_symmetric_difference(self, item_a: Item, item_b: Item, item_c: Item) -> None:
        s1 = KnowledgeState(items=frozenset({item_a, item_b}))
        s2 = KnowledgeState(items=frozenset({item_b, item_c}))
        assert s1.symmetric_difference(s2) == KnowledgeState(items=frozenset({item_a, item_c}))

    def test_ordering(self, item_a: Item, item_b: Item) -> None:
        s1 = KnowledgeState(items=frozenset({item_a}))
        s2 = KnowledgeState(items=frozenset({item_a, item_b}))
        assert s1 <= s2
        assert s1 < s2
        assert s2 >= s1
        assert s2 > s1
        assert not s2 <= s1
        assert not s2 < s1

    def test_ordering_not_implemented(self) -> None:
        s = KnowledgeState()
        assert s.__le__("x") is NotImplemented
        assert s.__lt__("x") is NotImplemented
        assert s.__ge__("x") is NotImplemented
        assert s.__gt__("x") is NotImplemented

    def test_equality(self, item_a: Item) -> None:
        s1 = KnowledgeState(items=frozenset({item_a}))
        s2 = KnowledgeState(items=frozenset({item_a}))
        assert s1 == s2

    def test_equality_not_implemented(self) -> None:
        s = KnowledgeState()
        assert s.__eq__("x") is NotImplemented

    def test_hash(self, item_a: Item) -> None:
        s1 = KnowledgeState(items=frozenset({item_a}))
        s2 = KnowledgeState(items=frozenset({item_a}))
        assert hash(s1) == hash(s2)
        assert len({s1, s2}) == 1

    def test_is_subset_of(self, item_a: Item, item_b: Item) -> None:
        s1 = KnowledgeState(items=frozenset({item_a}))
        s2 = KnowledgeState(items=frozenset({item_a, item_b}))
        assert s1.is_subset_of(s2)
        assert not s2.is_subset_of(s1)

    def test_is_proper_subset_of(self, item_a: Item, item_b: Item) -> None:
        s1 = KnowledgeState(items=frozenset({item_a}))
        s2 = KnowledgeState(items=frozenset({item_a, item_b}))
        assert s1.is_proper_subset_of(s2)
        assert not s1.is_proper_subset_of(s1)

    def test_item_ids(self, item_a: Item, item_b: Item) -> None:
        state = KnowledgeState(items=frozenset({item_a, item_b}))
        assert state.item_ids == frozenset({"a", "b"})

    def test_repr(self, item_a: Item, item_b: Item) -> None:
        state = KnowledgeState(items=frozenset({item_b, item_a}))
        assert repr(state) == "KnowledgeState({a, b})"

    @given(data=st.data())
    def test_union_commutative(self, data: st.DataObject) -> None:
        domain = data.draw(domains(min_size=2, max_size=4))
        s1 = data.draw(knowledge_states_from_domain(domain))
        s2 = data.draw(knowledge_states_from_domain(domain))
        assert s1.union(s2) == s2.union(s1)

    @given(data=st.data())
    def test_union_associative(self, data: st.DataObject) -> None:
        domain = data.draw(domains(min_size=2, max_size=4))
        s1 = data.draw(knowledge_states_from_domain(domain))
        s2 = data.draw(knowledge_states_from_domain(domain))
        s3 = data.draw(knowledge_states_from_domain(domain))
        assert s1.union(s2).union(s3) == s1.union(s2.union(s3))

    @given(data=st.data())
    def test_union_identity(self, data: st.DataObject) -> None:
        domain = data.draw(domains(min_size=1, max_size=4))
        s = data.draw(knowledge_states_from_domain(domain))
        empty = KnowledgeState()
        assert s.union(empty) == s

    @given(data=st.data())
    def test_intersection_commutative(self, data: st.DataObject) -> None:
        domain = data.draw(domains(min_size=2, max_size=4))
        s1 = data.draw(knowledge_states_from_domain(domain))
        s2 = data.draw(knowledge_states_from_domain(domain))
        assert s1.intersection(s2) == s2.intersection(s1)


class TestDomain:
    def test_create_domain(self, sample_items: list[Item]) -> None:
        domain = Domain(items=frozenset(sample_items))
        assert len(domain) == 3

    def test_empty_domain_raises(self) -> None:
        with pytest.raises(ValueError, match="at least one item"):
            Domain(items=frozenset())

    def test_duplicate_items_collapsed_by_frozenset(self) -> None:
        """Items with same ID are equal, so frozenset deduplicates them."""
        domain = Domain(items=frozenset({Item(id="a"), Item(id="a", label="different")}))
        assert len(domain) == 1

    def test_contains(self, sample_domain: Domain, item_a: Item) -> None:
        assert item_a in sample_domain

    def test_contains_non_item(self, sample_domain: Domain) -> None:
        assert "not_an_item" not in sample_domain

    def test_iter(self, sample_domain: Domain) -> None:
        result = list(sample_domain)
        assert len(result) == 3
        assert result == sorted(result)

    def test_full_state(self, sample_domain: Domain) -> None:
        full = sample_domain.full_state
        assert len(full) == 3

    def test_empty_state(self, sample_domain: Domain) -> None:
        empty = sample_domain.empty_state
        assert len(empty) == 0
        assert empty.is_empty

    def test_contains_state(self, sample_domain: Domain, item_a: Item) -> None:
        state = KnowledgeState(items=frozenset({item_a}))
        assert sample_domain.contains_state(state)

    def test_contains_state_external_item(self, sample_domain: Domain) -> None:
        external = Item(id="z")
        state = KnowledgeState(items=frozenset({external}))
        assert not sample_domain.contains_state(state)

    def test_get_item(self, sample_domain: Domain) -> None:
        assert sample_domain.get_item("a") == Item(id="a")
        assert sample_domain.get_item("z") is None

    def test_item_ids(self, sample_domain: Domain) -> None:
        assert sample_domain.item_ids == frozenset({"a", "b", "c"})

    def test_frozen(self, sample_domain: Domain) -> None:
        with pytest.raises(ValidationError):
            sample_domain.items = frozenset()  # type: ignore[misc]

    @given(domain=domains())
    def test_full_state_contains_all(self, domain: Domain) -> None:
        full = domain.full_state
        for item in domain:
            assert item in full

    @given(domain=domains())
    def test_empty_state_contains_none(self, domain: Domain) -> None:
        empty = domain.empty_state
        for item in domain:
            assert item not in empty
