"""Visualization and export for KST structures.

Generates Graphviz DOT, Mermaid, and JSON representations of
knowledge spaces, prerequisite graphs, and learning trajectories.

Hasse diagrams display the covering relation of the knowledge space:
K covers L iff L ⊂ K, |K| = |L| + 1, and both are states.

No external dependencies required — outputs are plain strings that
can be rendered by Graphviz, Mermaid-compatible tools, or parsed as JSON.
"""

from __future__ import annotations

import json

from kst_core.domain import KnowledgeState  # noqa: TC001
from kst_core.parser import CourseDefinition  # noqa: TC001
from kst_core.prerequisites import PrerequisiteGraph  # noqa: TC001
from kst_core.space import KnowledgeSpace, LearningSpace  # noqa: TC001


def _state_label(state: KnowledgeState) -> str:
    """Human-readable label for a knowledge state."""
    if len(state) == 0:
        return "\u2205"
    return "{" + ", ".join(sorted(state.item_ids)) + "}"


def _state_id(state: KnowledgeState) -> str:
    """Sanitized identifier for DOT/Mermaid nodes."""
    if len(state) == 0:
        return "s_empty"
    return "s_" + "_".join(sorted(state.item_ids))


def _covering_edges(
    states: frozenset[KnowledgeState],
) -> list[tuple[KnowledgeState, KnowledgeState]]:
    """Compute the covering relation (Hasse diagram edges).

    K covers L iff L ⊂ K, |K| = |L| + 1, and both are states.
    Returns list of (lower, upper) pairs.
    """
    edges: list[tuple[KnowledgeState, KnowledgeState]] = []
    by_size: dict[int, list[KnowledgeState]] = {}
    for s in states:
        by_size.setdefault(len(s), []).append(s)

    sizes = sorted(by_size.keys())
    for i in range(len(sizes) - 1):
        lower_size = sizes[i]
        upper_size = sizes[i + 1]
        if upper_size != lower_size + 1:
            continue
        for lower in by_size[lower_size]:
            for upper in by_size[upper_size]:
                if lower.items < upper.items:
                    edges.append((lower, upper))
    return edges


def hasse_dot(space: KnowledgeSpace | LearningSpace) -> str:
    """Generate Graphviz DOT for the Hasse diagram of a knowledge space.

    Nodes are knowledge states, edges represent the covering relation.
    States are arranged bottom-up by cardinality (Sugiyama layout).

    Args:
        space: A KnowledgeSpace or LearningSpace.

    Returns:
        DOT source string.
    """
    lines = [
        "digraph Hasse {",
        "  rankdir=BT;",
        '  node [shape=box, style=rounded, fontname="Helvetica"];',
        "  edge [arrowsize=0.7];",
    ]

    # Group states by cardinality for rank alignment
    by_size: dict[int, list[KnowledgeState]] = {}
    for s in space.states:
        by_size.setdefault(len(s), []).append(s)

    for size in sorted(by_size.keys()):
        group = sorted(by_size[size], key=lambda s: sorted(s.item_ids))
        rank_nodes = " ".join(f'"{_state_id(s)}"' for s in group)
        lines.append(f"  {{ rank=same; {rank_nodes} }}")

    # Node declarations
    for s in sorted(space.states, key=lambda s: (len(s), sorted(s.item_ids))):
        lines.append(f'  "{_state_id(s)}" [label="{_state_label(s)}"];')

    # Covering edges (each covers exactly one item by construction)
    for lower, upper in _covering_edges(space.states):
        diff = upper.items - lower.items
        label = next(iter(diff)).id
        lines.append(f'  "{_state_id(lower)}" -> "{_state_id(upper)}" [label="+{label}"];')

    lines.append("}")
    return "\n".join(lines)


def prerequisites_dot(graph: PrerequisiteGraph) -> str:
    """Generate Graphviz DOT for a prerequisite graph.

    Args:
        graph: A PrerequisiteGraph (DAG).

    Returns:
        DOT source string.
    """
    lines = [
        "digraph Prerequisites {",
        "  rankdir=LR;",
        '  node [shape=box, style=rounded, fontname="Helvetica"];',
        "  edge [arrowsize=0.7];",
    ]

    for item_id in sorted(graph.domain.item_ids):
        lines.append(f'  "{item_id}";')

    for source, target in sorted(graph.edges):
        lines.append(f'  "{source}" -> "{target}";')

    lines.append("}")
    return "\n".join(lines)


def trajectory_dot(
    trajectory: tuple[KnowledgeState, ...],
    highlight_items: bool = True,
) -> str:
    """Generate Graphviz DOT for a learning trajectory.

    Shows the sequence of states visited, with edges labeled by
    the item acquired at each step.

    Args:
        trajectory: Sequence of KnowledgeStates.
        highlight_items: Label edges with acquired items.

    Returns:
        DOT source string.
    """
    lines = [
        "digraph Trajectory {",
        "  rankdir=LR;",
        '  node [shape=box, style=rounded, fontname="Helvetica"];',
        "  edge [arrowsize=0.7];",
    ]

    for i, state in enumerate(trajectory):
        label = _state_label(state)
        style = ', style="rounded,bold"' if i == len(trajectory) - 1 else ""
        lines.append(f'  "t{i}" [label="{label}"{style}];')

    for i in range(len(trajectory) - 1):
        current = trajectory[i]
        next_s = trajectory[i + 1]
        if highlight_items:
            diff = next_s.items - current.items
            label = next(iter(diff)).id if len(diff) == 1 else ""
            if label:
                lines.append(f'  "t{i}" -> "t{i + 1}" [label="+{label}"];')
            else:
                lines.append(f'  "t{i}" -> "t{i + 1}";')
        else:
            lines.append(f'  "t{i}" -> "t{i + 1}";')

    lines.append("}")
    return "\n".join(lines)


def hasse_mermaid(space: KnowledgeSpace | LearningSpace) -> str:
    """Generate Mermaid flowchart for the Hasse diagram.

    Suitable for embedding in Markdown documentation.

    Args:
        space: A KnowledgeSpace or LearningSpace.

    Returns:
        Mermaid source string.
    """
    lines = ["graph BT"]

    # Node declarations
    for s in sorted(space.states, key=lambda s: (len(s), sorted(s.item_ids))):
        sid = _state_id(s)
        label = _state_label(s)
        lines.append(f"  {sid}[{label}]")

    # Covering edges (each covers exactly one item by construction)
    for lower, upper in _covering_edges(space.states):
        diff = upper.items - lower.items
        label = next(iter(diff)).id
        lid = _state_id(lower)
        uid = _state_id(upper)
        lines.append(f"  {lid} -->|+{label}| {uid}")

    return "\n".join(lines)


def course_json(course: CourseDefinition) -> str:
    """Export a CourseDefinition as JSON.

    Includes domain, prerequisites, states, and metadata.

    Args:
        course: A parsed CourseDefinition.

    Returns:
        JSON string.
    """
    items = [
        {"id": item.id, "label": item.label} for item in sorted(course.domain, key=lambda i: i.id)
    ]

    edges = sorted(course.prerequisite_graph.edges)

    states = [
        sorted(state.item_ids)
        for state in sorted(course.states, key=lambda s: (len(s), sorted(s.item_ids)))
    ]

    data = {
        "name": course.name,
        "description": course.description,
        "domain": {
            "items": items,
            "count": len(items),
        },
        "prerequisites": {
            "edges": edges,
            "count": len(edges),
        },
        "states": {
            "sets": states,
            "count": len(states),
        },
    }

    return json.dumps(data, indent=2)
