---
mode: agent
agent: notify-api
name: notify-api-prompt
description:
  Prompt for the notify-api agent. Creates or updates FastAPI REST endpoints for notification sending, bulk jobs, job status tracking, and streaming.
---

### Requirements

1.  **REST Endpoints:** Create endpoints in `app/routers/notify.py` or `app/routers/jobs.py` with consistent URL patterns under `/api/v1/notify/` and `/api/v1/jobs/`.
2.  **Request/Response Schemas:** Use Pydantic models for request validation and response serialization.
3.  **Error Handling:** Return appropriate HTTP status codes (200, 201, 400, 404, 422, 500) with structured error bodies.
4.  **Streaming:** Support SSE streaming for real-time job status updates where applicable.

### Constraints

- Python 3.11+ with FastAPI async endpoints
- All endpoints accept and return JSON
- Sensitive data (recipient details) must not appear in error responses or logs

### Success Criteria

- Endpoint returns correct status code and response body for valid requests
- Invalid requests return 422 with clear validation messages
- Endpoint is registered in `app/main.py` router includes
- `curl` command provided to test the endpoint

### Usage Template

```
Add a [METHOD] /api/v1/notify/[path] endpoint that:
- Accepts [request schema fields]
- Returns [response schema fields]
- Validates [specific validation rules]
- Returns [status code] on success, [status code] on validation failure
Show the diff and wait for my confirmation before applying.
```
