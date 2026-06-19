---
name: discover-queues
description: Trace message broker connections, producers, and Dead Letter Queues (DLQ).
---

# Discover Queues

Analyze the asynchronous event bus and message persistence layer.

## Focus Areas
- Queue Managers and Producers (app/queue/queue_manager.py, app/queue/producer.py)
- Failure Handling (app/queue/dlq_handler.py, app/queue/retry_handler.py)
- Queue Schemas (app/queue/schemas.py)

## Workflow
1. Route the hub folder agent to plugin/skills for this specific skill folder.
2. Invoke the native "discoverQueues" tool.
3. Return the message broker topology and retry strategies.
