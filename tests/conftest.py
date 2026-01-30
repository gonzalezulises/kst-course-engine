"""Hypothesis strategies for generating valid KST structures."""

from __future__ import annotations

import pytest
from hypothesis import strategies as st

from kst_core.domain import Domain, Item, KnowledgeState


@st.composite
def items(draw: st.DrawFn, min_size: int = 1, max_size: int = 6) -> list[Item]:
    """Generate a list of Items with unique IDs."""
    n = draw(st.integers(min_value=min_size, max_value=max_size))
    ids = draw(
        st.lists(
            st.text(
                alphabet=st.characters(whitelist_categories=("Ll",)),
                min_size=1,
                max_size=4,
            ),
            min_size=n,
            max_size=n,
            unique=True,
        )
    )
    return [Item(id=i) for i in ids]


@st.composite
def domains(draw: st.DrawFn, min_size: int = 1, max_size: int = 5) -> Domain:
    """Generate a valid Domain."""
    item_list = draw(items(min_size=min_size, max_size=max_size))
    return Domain(items=frozenset(item_list))


@st.composite
def knowledge_states_from_domain(draw: st.DrawFn, domain: Domain) -> KnowledgeState:
    """Generate a KnowledgeState that is a subset of the domain."""
    item_list = sorted(domain.items)
    selected = draw(st.lists(st.sampled_from(item_list), unique=True))
    return KnowledgeState(items=frozenset(selected))


@pytest.fixture()
def sample_items() -> list[Item]:
    """Three items: a, b, c."""
    return [Item(id="a"), Item(id="b"), Item(id="c")]


@pytest.fixture()
def sample_domain(sample_items: list[Item]) -> Domain:
    """Domain Q = {a, b, c}."""
    return Domain(items=frozenset(sample_items))


@pytest.fixture()
def item_a() -> Item:
    return Item(id="a")


@pytest.fixture()
def item_b() -> Item:
    return Item(id="b")


@pytest.fixture()
def item_c() -> Item:
    return Item(id="c")
