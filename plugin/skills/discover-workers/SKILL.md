---
name: discover-workers
description: Map the background task processors handling heavy AI and delivery workloads.
---

# Discover Workers

Analyze the fleet of background workers consuming queue messages.

## Focus Areas
- Delivery Workers (email_worker.py, sms_worker.py)
- Heavy Compute Workers (ai_worker.py, rag_worker.py, embedding_worker.py)

## Workflow
1. Route the hub folder agent to plugin/skills for this specific skill folder.
2. Invoke the native "discoverWorkers" tool.
3. Return the worker deployment and consumption map.
