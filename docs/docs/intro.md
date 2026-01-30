---
sidebar_position: 1
---

# KST Course Engine

**Knowledge Space Theory (KST)** provides the mathematical foundation for adaptive assessment and personalized learning. This project implements the core algebraic structures of KST as a Python library with formal validation.

## What is Knowledge Space Theory?

Knowledge Space Theory, introduced by Doignon and Falmagne (1985), models the structure of knowledge in a domain as a combinatorial system of **knowledge states** — feasible patterns of mastery over a set of problems or skills.

The central idea: not all subsets of problems are plausible knowledge states. The **prerequisite relationships** between items constrain which combinations of mastery are feasible.

$$
\mathcal{K} \subseteq 2^Q, \quad \emptyset \in \mathcal{K}, \quad Q \in \mathcal{K}, \quad K_1, K_2 \in \mathcal{K} \Rightarrow K_1 \cup K_2 \in \mathcal{K}
$$

## Project Structure

- **Theory**: Formal mathematical foundations with proofs
- **API Reference**: Complete documentation of the Python implementation
- **Research**: Literature review and novel contributions
- **Development**: Getting started, testing, and contributing guides

## Quick Start

```python
from kst_core import Domain, Item, KnowledgeSpace, KnowledgeState

# Define items
items = [Item(id="add"), Item(id="sub"), Item(id="mul")]
domain = Domain(items=frozenset(items))

# Define knowledge states
states = frozenset({
    KnowledgeState(),                                          # ∅
    KnowledgeState(items=frozenset({items[0]})),              # {add}
    KnowledgeState(items=frozenset({items[0], items[1]})),    # {add, sub}
    KnowledgeState(items=frozenset(items)),                    # {add, sub, mul}
})

# Create and validate a knowledge space
space = KnowledgeSpace(domain=domain, states=states)
```
