"""Tests for kst_core.parser — YAML course definition parser."""

from __future__ import annotations

import textwrap

import pytest
import yaml

from kst_core.domain import Item, KnowledgeState
from kst_core.parser import (
    CourseSchema,
    DomainSchema,
    ItemSchema,
    PrerequisitesSchema,
    parse_file,
    parse_yaml,
)

MINIMAL_YAML = textwrap.dedent("""\
    domain:
      name: "Test"
      items:
        - id: "a"
""")

LINEAR_YAML = textwrap.dedent("""\
    domain:
      name: "Linear"
      description: "A linear prerequisite chain"
      items:
        - id: "a"
          label: "Item A"
        - id: "b"
          label: "Item B"
        - id: "c"
          label: "Item C"
    prerequisites:
      edges:
        - ["a", "b"]
        - ["b", "c"]
""")

BRANCHING_YAML = textwrap.dedent("""\
    domain:
      name: "Branching"
      items:
        - id: "a"
        - id: "b"
        - id: "c"
    prerequisites:
      edges:
        - ["a", "b"]
        - ["a", "c"]
""")

NO_PREREQS_YAML = textwrap.dedent("""\
    domain:
      name: "Independent"
      items:
        - id: "x"
        - id: "y"
""")


class TestItemSchema:
    def test_basic(self) -> None:
        s = ItemSchema(id="a", label="Item A")
        assert s.id == "a"
        assert s.label == "Item A"

    def test_default_label(self) -> None:
        s = ItemSchema(id="a")
        assert s.label == ""


class TestDomainSchema:
    def test_valid(self) -> None:
        ds = DomainSchema(name="Test", items=(ItemSchema(id="a"),))
        assert ds.name == "Test"
        assert len(ds.items) == 1

    def test_default_description(self) -> None:
        ds = DomainSchema(name="Test", items=(ItemSchema(id="a"),))
        assert ds.description == ""

    def test_empty_items_raises(self) -> None:
        with pytest.raises(ValueError, match="at least one item"):
            DomainSchema(name="Test", items=())

    def test_duplicate_ids_raises(self) -> None:
        with pytest.raises(ValueError, match="Duplicate"):
            DomainSchema(
                name="Test",
                items=(ItemSchema(id="a"), ItemSchema(id="a")),
            )


class TestPrerequisitesSchema:
    def test_default_empty(self) -> None:
        ps = PrerequisitesSchema()
        assert ps.edges == ()

    def test_with_edges(self) -> None:
        ps = PrerequisitesSchema(edges=(("a", "b"),))
        assert len(ps.edges) == 1


class TestCourseSchema:
    def test_minimal(self) -> None:
        cs = CourseSchema(
            domain=DomainSchema(name="T", items=(ItemSchema(id="a"),)),
        )
        assert cs.prerequisites.edges == ()

    def test_with_prereqs(self) -> None:
        cs = CourseSchema(
            domain=DomainSchema(
                name="T",
                items=(ItemSchema(id="a"), ItemSchema(id="b")),
            ),
            prerequisites=PrerequisitesSchema(edges=(("a", "b"),)),
        )
        assert len(cs.prerequisites.edges) == 1


class TestParseYaml:
    def test_minimal(self) -> None:
        cd = parse_yaml(MINIMAL_YAML)
        assert cd.name == "Test"
        assert len(cd.domain) == 1
        assert len(cd.states) == 2  # empty + {a}

    def test_linear(self) -> None:
        cd = parse_yaml(LINEAR_YAML)
        assert cd.name == "Linear"
        assert cd.description == "A linear prerequisite chain"
        assert len(cd.domain) == 3
        assert len(cd.states) == 4  # ∅, {a}, {a,b}, {a,b,c}

    def test_branching(self) -> None:
        cd = parse_yaml(BRANCHING_YAML)
        assert len(cd.domain) == 3
        assert len(cd.states) == 5  # ∅, {a}, {a,b}, {a,c}, {a,b,c}

    def test_no_prerequisites(self) -> None:
        cd = parse_yaml(NO_PREREQS_YAML)
        assert len(cd.domain) == 2
        assert len(cd.states) == 4  # power set of {x, y}

    def test_linear_learning_paths(self) -> None:
        cd = parse_yaml(LINEAR_YAML)
        ls = cd.to_learning_space()
        paths = ls.learning_paths()
        assert len(paths) == 1
        assert tuple(item.id for item in paths[0]) == ("a", "b", "c")

    def test_branching_learning_paths(self) -> None:
        cd = parse_yaml(BRANCHING_YAML)
        ls = cd.to_learning_space()
        paths = ls.learning_paths()
        assert len(paths) == 2

    def test_knowledge_space(self) -> None:
        cd = parse_yaml(LINEAR_YAML)
        ks = cd.to_knowledge_space()
        assert len(ks.states) == 4

    def test_surmise_relation_derived(self) -> None:
        cd = parse_yaml(LINEAR_YAML)
        sr = cd.surmise_relation
        assert sr.prerequisites_of("c") == frozenset({"a", "b"})
        assert sr.prerequisites_of("b") == frozenset({"a"})
        assert sr.prerequisites_of("a") == frozenset()

    def test_prerequisite_graph(self) -> None:
        cd = parse_yaml(LINEAR_YAML)
        assert cd.prerequisite_graph.critical_path() == ["a", "b", "c"]
        assert cd.prerequisite_graph.longest_path_length() == 2

    def test_states_are_downsets(self) -> None:
        cd = parse_yaml(LINEAR_YAML)
        for state in cd.states:
            assert cd.surmise_relation.is_downset(state)

    def test_invalid_yaml_not_mapping(self) -> None:
        with pytest.raises(ValueError, match="mapping"):
            parse_yaml("just a string")

    def test_invalid_yaml_syntax(self) -> None:
        with pytest.raises(yaml.YAMLError):
            parse_yaml(":\n  :\n    - [invalid")

    def test_missing_domain(self) -> None:
        with pytest.raises(ValueError):
            parse_yaml("prerequisites:\n  edges: []")

    def test_unknown_edge_src(self) -> None:
        bad_yaml = textwrap.dedent("""\
            domain:
              name: "Bad"
              items:
                - id: "a"
            prerequisites:
              edges:
                - ["z", "a"]
        """)
        with pytest.raises(ValueError, match=r"unknown item.*'z'"):
            parse_yaml(bad_yaml)

    def test_unknown_edge_dst(self) -> None:
        bad_yaml = textwrap.dedent("""\
            domain:
              name: "Bad"
              items:
                - id: "a"
            prerequisites:
              edges:
                - ["a", "z"]
        """)
        with pytest.raises(ValueError, match=r"unknown item.*'z'"):
            parse_yaml(bad_yaml)

    def test_cyclic_edges(self) -> None:
        bad_yaml = textwrap.dedent("""\
            domain:
              name: "Cyclic"
              items:
                - id: "a"
                - id: "b"
            prerequisites:
              edges:
                - ["a", "b"]
                - ["b", "a"]
        """)
        with pytest.raises(ValueError, match="acyclic"):
            parse_yaml(bad_yaml)

    def test_none_yaml(self) -> None:
        with pytest.raises(ValueError, match="mapping"):
            parse_yaml("")


class TestParseFile:
    def test_parse_example(self) -> None:
        cd = parse_file("examples/intro-pandas.kst.yaml")
        assert cd.name == "Introduction to Pandas"
        assert len(cd.domain) == 8
        assert len(cd.states) == 15

    def test_file_not_found(self) -> None:
        with pytest.raises(FileNotFoundError, match="not_found"):
            parse_file("not_found.yaml")

    def test_parse_file_pathlib(self, tmp_path: pytest.TempPathFactory) -> None:
        p = tmp_path / "test.kst.yaml"  # type: ignore[operator]
        p.write_text(MINIMAL_YAML)  # type: ignore[union-attr]
        cd = parse_file(p)  # type: ignore[arg-type]
        assert cd.name == "Test"


class TestCourseDefinition:
    def test_name_and_description(self) -> None:
        cd = parse_yaml(LINEAR_YAML)
        assert cd.name == "Linear"
        assert cd.description == "A linear prerequisite chain"

    def test_to_learning_space_is_valid(self) -> None:
        cd = parse_yaml(LINEAR_YAML)
        ls = cd.to_learning_space()
        empty = KnowledgeState()
        for state in ls.states:
            if state == empty:
                continue
            found = False
            for item in state:
                reduced = KnowledgeState(items=state.items - {item})
                if reduced in ls.states:
                    found = True
                    break
            assert found, f"State {state} not accessible"

    def test_roundtrip_linear(self) -> None:
        """Full roundtrip: YAML → parse → learning space → paths → validate."""
        cd = parse_yaml(LINEAR_YAML)
        ls = cd.to_learning_space()
        paths = ls.learning_paths()
        assert len(paths) == 1
        assert all(isinstance(item, Item) for item in paths[0])

    def test_roundtrip_example_file(self) -> None:
        """Parse the real example and verify it produces a valid learning space."""
        cd = parse_file("examples/intro-pandas.kst.yaml")
        ls = cd.to_learning_space()
        paths = ls.learning_paths()
        assert len(paths) > 0
        for path in paths:
            assert len(path) == len(cd.domain)
