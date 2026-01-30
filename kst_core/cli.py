"""Command-line interface for the KST Course Engine.

Provides commands for inspecting, validating, and simulating
knowledge space structures from .kst.yaml course definitions.

Usage:
    kst info <file>          Course overview
    kst validate <file>      Formal validation checks
    kst paths <file>         Enumerate learning paths
    kst simulate <file>      Simulate learner cohort
    kst export <file>        Export as DOT, JSON, or Mermaid
"""

from __future__ import annotations

import argparse
import sys
from typing import TYPE_CHECKING

import numpy as np

from kst_core.assessment import AdaptiveAssessment, BLIMParameters, simulate_responses
from kst_core.learning import LearningModel, LearningRate
from kst_core.parser import parse_file
from kst_core.validation import validate_learning_space
from kst_core.viz import course_json, hasse_dot, hasse_mermaid, prerequisites_dot

if TYPE_CHECKING:
    from collections.abc import Sequence


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point for the kst CLI."""
    parser = argparse.ArgumentParser(
        prog="kst",
        description="KST Course Engine — Knowledge Space Theory tools",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # --- kst info ---
    info_parser = subparsers.add_parser("info", help="Show course overview")
    info_parser.add_argument("file", help="Path to .kst.yaml file")

    # --- kst validate ---
    validate_parser = subparsers.add_parser("validate", help="Run formal validation")
    validate_parser.add_argument("file", help="Path to .kst.yaml file")

    # --- kst paths ---
    paths_parser = subparsers.add_parser("paths", help="Enumerate learning paths")
    paths_parser.add_argument("file", help="Path to .kst.yaml file")
    paths_parser.add_argument(
        "--max",
        type=int,
        default=10,
        help="Maximum paths to display (default: 10)",
    )

    # --- kst simulate ---
    sim_parser = subparsers.add_parser("simulate", help="Simulate learner cohort")
    sim_parser.add_argument("file", help="Path to .kst.yaml file")
    sim_parser.add_argument(
        "--learners",
        type=int,
        default=100,
        help="Number of learners to simulate (default: 100)",
    )
    sim_parser.add_argument(
        "--beta",
        type=float,
        default=0.1,
        help="Slip probability (default: 0.1)",
    )
    sim_parser.add_argument(
        "--eta",
        type=float,
        default=0.1,
        help="Guess probability (default: 0.1)",
    )
    sim_parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility",
    )

    # --- kst export ---
    export_parser = subparsers.add_parser("export", help="Export as DOT, JSON, or Mermaid")
    export_parser.add_argument("file", help="Path to .kst.yaml file")
    export_parser.add_argument(
        "--format",
        choices=["dot", "json", "mermaid"],
        default="dot",
        help="Output format (default: dot)",
    )
    export_parser.add_argument(
        "--type",
        choices=["hasse", "prerequisites"],
        default="hasse",
        help="Diagram type (default: hasse)",
    )

    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "info":
        return _cmd_info(args.file)
    if args.command == "validate":
        return _cmd_validate(args.file)
    if args.command == "paths":
        return _cmd_paths(args.file, args.max)
    if args.command == "simulate":
        return _cmd_simulate(args.file, args.learners, args.beta, args.eta, args.seed)
    if args.command == "export":
        return _cmd_export(args.file, args.format, args.type)
    return 0  # pragma: no cover


def _cmd_info(file_path: str) -> int:
    """Show course overview."""
    try:
        course = parse_file(file_path)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print(f"Course: {course.name}")
    if course.description:
        print(f"Description: {course.description}")
    print(f"Items: {len(course.domain)}")
    print(f"States: {len(course.states)}")
    print(f"Prerequisites: {len(course.prerequisite_graph.edges)}")

    critical = course.prerequisite_graph.critical_path()
    if critical:
        print(f"Critical path: {' -> '.join(critical)}")
        print(f"Critical path length: {len(critical)}")

    ls = course.to_learning_space()
    n_paths = len(ls.learning_paths())
    print(f"Learning paths: {n_paths}")

    return 0


def _cmd_validate(file_path: str) -> int:
    """Run formal validation."""
    try:
        course = parse_file(file_path)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    report = validate_learning_space(course.domain, course.states)
    print(f"Validation: {report.summary}")
    for result in report.results:
        status = "PASS" if result.passed else "FAIL"
        print(f"  [{status}] {result.property_name}: {result.message}")

    return 0 if report.is_valid else 1


def _cmd_paths(file_path: str, max_paths: int) -> int:
    """Enumerate learning paths."""
    try:
        course = parse_file(file_path)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    ls = course.to_learning_space()
    paths = ls.learning_paths()
    print(f"Total learning paths: {len(paths)}")
    print()

    display = paths[:max_paths]
    for i, path in enumerate(display):
        items = " -> ".join(item.id for item in path)
        print(f"  {i + 1}. {items}")

    if len(paths) > max_paths:
        print(f"  ... and {len(paths) - max_paths} more (use --max to show more)")

    return 0


def _cmd_simulate(
    file_path: str,
    n_learners: int,
    beta: float,
    eta: float,
    seed: int | None,
) -> int:
    """Simulate learner cohort."""
    try:
        course = parse_file(file_path)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    rng = np.random.default_rng(seed)
    params = BLIMParameters.uniform(course.domain, beta=beta, eta=eta)
    state_list = sorted(course.states, key=lambda s: (len(s), sorted(s.item_ids)))

    # --- Adaptive Assessment Simulation ---
    print(f"Simulating {n_learners} learners on '{course.name}'")
    print(f"Parameters: beta={beta}, eta={eta}, seed={seed}")
    print()

    correct_count = 0
    total_questions: list[int] = []

    for _ in range(n_learners):
        true_state = state_list[int(rng.integers(len(state_list)))]
        responses = simulate_responses(true_state, params, rng=rng)

        session = AdaptiveAssessment.start(course.domain, course.states, params)
        result = session.run(responses)

        if result.current_estimate == true_state:
            correct_count += 1
        total_questions.append(len(responses))

    accuracy = correct_count / n_learners * 100
    print("=== Assessment Results ===")
    print(f"Accuracy: {correct_count}/{n_learners} ({accuracy:.1f}%)")
    print(f"Avg questions: {np.mean(total_questions):.1f}")
    print()

    # --- Learning Trajectory Simulation ---
    ls = course.to_learning_space()
    rates = LearningRate.uniform(course.domain)
    model = LearningModel(space=ls, rates=rates)

    lengths: list[int] = []
    for _ in range(n_learners):
        traj = model.simulate_trajectory(rng=rng)
        lengths.append(len(traj) - 1)

    expected = model.expected_steps()
    empty_state = course.domain.empty_state

    print("=== Learning Trajectories ===")
    print(f"Expected steps to mastery: {expected[empty_state]:.1f}")
    print(f"Simulated avg steps: {np.mean(lengths):.1f} (std={np.std(lengths):.1f})")

    return 0


def _cmd_export(file_path: str, fmt: str, diagram_type: str) -> int:
    """Export course structure as DOT, JSON, or Mermaid."""
    try:
        course = parse_file(file_path)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if fmt == "json":
        print(course_json(course))
        return 0

    ls = course.to_learning_space()

    if diagram_type == "prerequisites":
        if fmt == "mermaid":
            print("Error: Mermaid format not supported for prerequisites", file=sys.stderr)
            return 1
        print(prerequisites_dot(course.prerequisite_graph))
        return 0

    # hasse diagram
    if fmt == "dot":
        print(hasse_dot(ls))
    else:
        print(hasse_mermaid(ls))

    return 0
