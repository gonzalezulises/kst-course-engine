"""Example: Using the KST Course Engine REST API with httpx.

Run the server first:
    uvicorn kst_core.api:app --reload

Then run this script:
    python examples/api_example.py
"""

from __future__ import annotations

import json
import sys


def main() -> None:
    """Demonstrate the KST Course Engine REST API."""
    try:
        import httpx
    except ImportError:
        print("httpx is required: pip install httpx")
        sys.exit(1)

    base = "http://localhost:8000"

    course_data = {
        "domain": {
            "name": "Linear Algebra Basics",
            "description": "Foundational linear algebra concepts",
            "items": [
                {"id": "vectors", "label": "Understanding vectors"},
                {"id": "matrices", "label": "Matrix operations"},
                {"id": "determinant", "label": "Computing determinants"},
                {"id": "inverse", "label": "Matrix inverse"},
            ],
        },
        "prerequisites": {
            "edges": [
                ["vectors", "matrices"],
                ["matrices", "determinant"],
                ["matrices", "inverse"],
            ],
        },
    }

    print("=== KST Course Engine API Example ===\n")

    # 1. Course info
    print("1. Course Info")
    resp = httpx.post(f"{base}/info", json=course_data)
    info = resp.json()
    print(f"   Name: {info['name']}")
    print(f"   Items: {info['items']}, States: {info['states']}")
    print(f"   Learning paths: {info['learning_paths']}")
    print()

    # 2. Validation
    print("2. Validation")
    resp = httpx.post(f"{base}/validate", json=course_data)
    val = resp.json()
    print(f"   Valid: {val['is_valid']} ({val['summary']})")
    print()

    # 3. Learning paths
    print("3. Learning Paths")
    resp = httpx.post(f"{base}/paths", json=course_data)
    paths = resp.json()
    for i, path in enumerate(paths["paths"]):
        print(f"   {i + 1}. {' -> '.join(path)}")
    print()

    # 4. Simulation
    print("4. Simulation (5 learners)")
    sim_data = {**course_data, "learners": 5, "seed": 42}
    resp = httpx.post(f"{base}/simulate", json=sim_data)
    sim = resp.json()
    print(f"   Accuracy: {sim['accuracy_pct']}%")
    print(f"   Expected steps: {sim['expected_steps']}")
    print()

    # 5. Export
    print("5. Export (JSON)")
    export_data = {**course_data, "format": "json"}
    resp = httpx.post(f"{base}/export", json=export_data)
    export = resp.json()
    parsed = json.loads(export["content"])
    print(f"   States: {len(parsed['states']['sets'])}")
    print()

    # 6. Interactive assessment
    print("6. Interactive Assessment")
    assess_data = {**course_data, "beta": 0.1, "eta": 0.1}
    resp = httpx.post(f"{base}/assess/start", json=assess_data)
    start = resp.json()
    session_id = start["session_id"]
    print(f"   Session: {session_id[:8]}...")
    print(f"   First item: {start['first_item']}")

    # Answer all items correctly
    for _ in range(4):
        resp = httpx.post(
            f"{base}/assess/{session_id}/respond",
            json={"correct": True},
        )
        data = resp.json()
        print(f"   Step: {data['step']['item_id']} -> correct")
        if data["is_complete"]:
            break

    resp = httpx.get(f"{base}/assess/{session_id}/summary")
    summary = resp.json()
    print(f"   Confidence: {summary['confidence']:.1%}")
    print(f"   Mastered: {summary['mastered']}")

    print("\nDone!")


if __name__ == "__main__":
    main()
