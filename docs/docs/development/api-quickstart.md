---
id: api-quickstart
title: API Quickstart
sidebar_label: API Quickstart
---

# API Quickstart

Run the KST Course Engine REST API locally.

## Installation

```bash
# Install with API dependencies
pip install kst-course-engine[api]

# Or from source
git clone https://github.com/gonzalezulises/kst-course-engine.git
cd kst-course-engine
uv venv && uv pip install -e ".[dev,api]"
```

## Starting the Server

```bash
uvicorn kst_core.api:app --reload
```

The server starts at `http://localhost:8000`. Visit `/docs` for interactive Swagger documentation.

## Quick Example

```bash
# Course info
curl -X POST http://localhost:8000/info \
  -H 'Content-Type: application/json' \
  -d '{
    "domain": {
      "name": "Test",
      "items": [{"id": "a"}, {"id": "b"}]
    },
    "prerequisites": {"edges": [["a", "b"]]}
  }'

# Validate
curl -X POST http://localhost:8000/validate \
  -H 'Content-Type: application/json' \
  -d '{"domain": {"name": "Test", "items": [{"id": "a"}]}}'

# Learning paths
curl -X POST http://localhost:8000/paths \
  -H 'Content-Type: application/json' \
  -d '{"domain": {"name": "Test", "items": [{"id": "a"}, {"id": "b"}]}, "prerequisites": {"edges": [["a", "b"]]}}'
```

## Python Client

```python
import httpx

base = "http://localhost:8000"
course = {
    "domain": {
        "name": "Linear",
        "items": [{"id": "a"}, {"id": "b"}, {"id": "c"}],
    },
    "prerequisites": {"edges": [["a", "b"], ["b", "c"]]},
}

# Get course info
info = httpx.post(f"{base}/info", json=course).json()
print(f"{info['name']}: {info['items']} items, {info['states']} states")

# Interactive assessment
start = httpx.post(f"{base}/assess/start", json=course).json()
session_id = start["session_id"]
print(f"First item: {start['first_item']}")

# Respond
resp = httpx.post(
    f"{base}/assess/{session_id}/respond",
    json={"correct": True}
).json()
print(f"Next: {resp['next_item']}, complete: {resp['is_complete']}")
```

See `examples/api_example.py` for a complete example.
