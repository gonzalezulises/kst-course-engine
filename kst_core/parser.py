"""YAML parser for .kst.yaml course definitions.

Parses declarative course files into KST structures:
  .kst.yaml → Domain + PrerequisiteGraph → SurmiseRelation → KnowledgeSpace/LearningSpace

The YAML schema:

    domain:
      name: "Course Name"
      description: "Optional description"
      items:
        - id: "item_id"
          label: "Human-readable label"

    prerequisites:
      edges:
        - ["prereq_id", "dependent_id"]
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, field_validator

from kst_core.domain import Domain, Item, KnowledgeState
from kst_core.prerequisites import PrerequisiteGraph, SurmiseRelation
from kst_core.space import KnowledgeSpace, LearningSpace


class ItemSchema(BaseModel, frozen=True):
    """Schema for an item in the YAML file."""

    id: str
    label: str = ""


class DomainSchema(BaseModel, frozen=True):
    """Schema for the domain section of a .kst.yaml file."""

    name: str
    description: str = ""
    items: tuple[ItemSchema, ...]

    @field_validator("items")
    @classmethod
    def items_nonempty(cls, v: tuple[ItemSchema, ...]) -> tuple[ItemSchema, ...]:
        if not v:
            msg = "Domain must contain at least one item"
            raise ValueError(msg)
        return v

    @field_validator("items")
    @classmethod
    def unique_item_ids(cls, v: tuple[ItemSchema, ...]) -> tuple[ItemSchema, ...]:
        ids = [item.id for item in v]
        if len(ids) != len(set(ids)):
            duplicates = {i for i in ids if ids.count(i) > 1}
            msg = f"Duplicate item IDs: {duplicates}"
            raise ValueError(msg)
        return v


class PrerequisitesSchema(BaseModel, frozen=True):
    """Schema for the prerequisites section of a .kst.yaml file."""

    edges: tuple[tuple[str, str], ...] = ()


class CourseSchema(BaseModel, frozen=True):
    """Top-level schema for a .kst.yaml file."""

    domain: DomainSchema
    prerequisites: PrerequisitesSchema = PrerequisitesSchema()


class CourseDefinition(BaseModel, frozen=True):
    """A fully parsed and validated course definition.

    Contains both the raw schema and the derived KST structures.
    """

    schema_: CourseSchema
    domain: Domain
    prerequisite_graph: PrerequisiteGraph
    surmise_relation: SurmiseRelation
    states: frozenset[KnowledgeState]

    model_config = {"arbitrary_types_allowed": True}

    @property
    def name(self) -> str:
        return self.schema_.domain.name

    @property
    def description(self) -> str:
        return self.schema_.domain.description

    def to_knowledge_space(self) -> KnowledgeSpace:
        """Build a KnowledgeSpace from the derived states."""
        return KnowledgeSpace(domain=self.domain, states=self.states)

    def to_learning_space(self) -> LearningSpace:
        """Build a LearningSpace from the derived states.

        This succeeds because states derived from a DAG via Birkhoff's
        theorem always form a learning space (antimatroid).
        """
        return LearningSpace(domain=self.domain, states=self.states)


def parse_yaml(content: str) -> CourseDefinition:
    """Parse a YAML string into a CourseDefinition.

    Args:
        content: YAML string conforming to the .kst.yaml schema.

    Returns:
        A fully validated CourseDefinition with derived KST structures.

    Raises:
        ValueError: If the YAML is invalid or the schema validation fails.
        yaml.YAMLError: If the YAML syntax is malformed.
    """
    raw: Any = yaml.safe_load(content)
    if not isinstance(raw, dict):
        msg = "YAML root must be a mapping"
        raise ValueError(msg)

    schema = CourseSchema(**raw)
    return build_course(schema)


def parse_file(path: str | Path) -> CourseDefinition:
    """Parse a .kst.yaml file into a CourseDefinition.

    Args:
        path: Path to the .kst.yaml file.

    Returns:
        A fully validated CourseDefinition.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the content is invalid.
    """
    file_path = Path(path)
    if not file_path.exists():
        msg = f"File not found: {file_path}"
        raise FileNotFoundError(msg)

    content = file_path.read_text(encoding="utf-8")
    return parse_yaml(content)


def build_course(schema: CourseSchema) -> CourseDefinition:
    """Build KST structures from a validated schema."""
    items = [Item(id=item.id, label=item.label) for item in schema.domain.items]
    domain = Domain(items=frozenset(items))

    item_ids = domain.item_ids
    for src, dst in schema.prerequisites.edges:
        if src not in item_ids:
            msg = f"Prerequisite edge references unknown item: '{src}'"
            raise ValueError(msg)
        if dst not in item_ids:
            msg = f"Prerequisite edge references unknown item: '{dst}'"
            raise ValueError(msg)

    graph = PrerequisiteGraph(
        domain=domain,
        edges=frozenset(schema.prerequisites.edges),
    )

    sr = graph.to_surmise_relation()
    states = sr.to_knowledge_space_states()

    return CourseDefinition(
        schema_=schema,
        domain=domain,
        prerequisite_graph=graph,
        surmise_relation=sr,
        states=states,
    )
