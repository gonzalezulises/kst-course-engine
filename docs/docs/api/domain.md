---
sidebar_position: 1
title: "Domain Module"
---

# Domain Module (`kst_core.domain`)

The domain module provides the three foundational types of KST.

## `Item`

An atomic knowledge element $q \in Q$.

```python
from kst_core import Item

item = Item(id="addition", label="Basic Addition")
```

**Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | Unique identifier (non-empty) |
| `label` | `str` | Human-readable label (optional) |

**Properties:**
- Frozen (immutable) Pydantic model
- Equality and hashing based on `id` only
- Supports ordering via `<` for deterministic iteration

## `KnowledgeState`

A knowledge state $K \subseteq Q$ — a frozenset of Items representing mastered knowledge.

```python
from kst_core import Item, KnowledgeState

a, b = Item(id="a"), Item(id="b")
state = KnowledgeState(items=frozenset({a, b}))
```

**Set Operations:**
| Method | Notation | Description |
|--------|----------|-------------|
| `union(other)` | $K_1 \cup K_2$ | Union of states |
| `intersection(other)` | $K_1 \cap K_2$ | Intersection |
| `difference(other)` | $K_1 \setminus K_2$ | Set difference |
| `symmetric_difference(other)` | $K_1 \triangle K_2$ | Symmetric difference |

**Ordering:** Supports `<=`, `<`, `>=`, `>` via subset inclusion.

**Properties:**
- `is_empty: bool` — True if $K = \emptyset$
- `item_ids: frozenset[str]` — Set of item IDs

## `Domain`

The domain $Q$ — a finite non-empty set of Items.

```python
from kst_core import Domain, Item

domain = Domain(items=frozenset({Item(id="a"), Item(id="b"), Item(id="c")}))
```

**Properties:**
- `full_state: KnowledgeState` — $Q$ as a state
- `empty_state: KnowledgeState` — $\emptyset$ as a state
- `item_ids: frozenset[str]` — All item IDs

**Methods:**
- `contains_state(state) -> bool` — Check $K \subseteq Q$
- `get_item(item_id) -> Item | None` — Lookup by ID
