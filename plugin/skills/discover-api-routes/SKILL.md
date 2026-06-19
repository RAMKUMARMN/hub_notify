---
name: discover-api-routes
description: Map the FastAPI endpoints for job triggering and file ingestion.
---

# Discover API Routes

Analyze the synchronous REST API layer of the service.

## Focus Areas
- Notification Endpoints (app/routers/notify.py)
- Job Management (app/routers/jobs.py)
- File Uploads (app/routers/files.py)

## Workflow
1. Route the hub folder agent to plugin/skills for this specific skill folder.
2. Invoke the native "discoverApiRoutes" tool.
3. Return the synchronous API map.
