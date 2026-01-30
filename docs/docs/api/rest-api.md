---
id: rest-api
title: REST API
sidebar_label: REST API
---

# REST API Reference

The KST Course Engine provides a REST API via FastAPI for course analysis, validation, simulation, and export.

## Starting the Server

```bash
pip install kst-course-engine[api]
uvicorn kst_core.api:app --reload
```

The API is available at `http://localhost:8000`. Interactive documentation at `/docs`.

## Endpoints

### POST `/info`

Course overview: items, states, prerequisites, paths.

**Request:**
```bash
curl -X POST http://localhost:8000/info \
  -H 'Content-Type: application/json' \
  -d '{
    "domain": {
      "name": "Test",
      "items": [{"id": "a"}, {"id": "b"}],
      "description": ""
    },
    "prerequisites": {"edges": [["a", "b"]]}
  }'
```

**Response:**
```json
{
  "name": "Test",
  "description": "",
  "items": 2,
  "states": 3,
  "prerequisites": 1,
  "critical_path": ["a", "b"],
  "critical_path_length": 2,
  "learning_paths": 1
}
```

### POST `/validate`

Formal validation of knowledge space axioms (S1, S2, S3, accessibility).

**Response includes:**
- `is_valid`: boolean
- `summary`: e.g. `"6/6 checks passed"`
- `results`: array of `{property_name, passed, message, reference}`

### POST `/paths`

Enumerate all learning paths from $\emptyset$ to $Q$.

### POST `/simulate`

Simulate a learner cohort with adaptive assessment and learning trajectories.

**Additional fields:** `learners`, `beta`, `eta`, `seed`.

### POST `/export`

Export course structure as DOT, JSON, or Mermaid.

**Additional fields:** `format` (`"dot"`, `"json"`, `"mermaid"`), `type` (`"hasse"`, `"prerequisites"`).

### POST `/assess/start`

Start an interactive assessment session.

**Request:**
```json
{
  "domain": {"name": "Test", "items": [{"id": "a"}]},
  "beta": 0.1,
  "eta": 0.1
}
```

**Response:**
```json
{
  "session_id": "abc123...",
  "first_item": "a"
}
```

### POST `/assess/{session_id}/respond`

Record a response and get the next item.

**Request:**
```json
{"correct": true}
```

### GET `/assess/{session_id}/summary`

Get the assessment summary for a session.

## Request Models

| Model | Fields |
|-------|--------|
| `CourseInput` | `domain: DomainInput`, `prerequisites: PrerequisitesInput` |
| `DomainInput` | `name: str`, `description: str`, `items: list[ItemInput]` |
| `ItemInput` | `id: str`, `label: str` |
| `PrerequisitesInput` | `edges: list[tuple[str, str]]` |
| `SimulateRequest` | Extends CourseInput + `learners`, `beta`, `eta`, `seed` |
| `ExportRequest` | Extends CourseInput + `format`, `type` |

## Error Handling

- **422**: Invalid input (malformed course, unknown items, cyclic prerequisites)
- **400**: Unsupported operation (e.g. Mermaid + prerequisites)
- **404**: Session not found (assessment endpoints)
