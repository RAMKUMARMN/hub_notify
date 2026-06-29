---
mode: agent
agent: notify-queue
name: notify-queue-prompt
description:
  Prompt for the notify-queue agent. Configures or inspects RabbitMQ queues, exchanges, bindings, retry routing, and dead-letter logic for the notification service.
---

### Requirements

1.  **Queue Topology:** Define exchanges, queues, and bindings for each notification channel with `*.process`, `*.retry`, and `*.failed` naming convention.
2.  **Message Schemas:** Versioned Pydantic models in `app/queue/schemas.py` with `version` field for forward compatibility.
3.  **Retry Logic:** Implement ack/nack with configurable retry delays (1min, 5min, 30min) and dead-letter routing after max attempts.
4.  **Inspection:** Provide commands to inspect queue depth, consumer count, and stuck messages via RabbitMQ Management API or CLI.

### Constraints

- Python 3.11+ with aio-pika for async RabbitMQ communication
- Messages must be JSON-serializable Pydantic models
- Retry count tracked in message headers, not in external state

### Success Criteria

- Producer publishes messages to the correct exchange with routing key
- Consumer ack's on success, nack's with requeue=false on failure
- Messages exceeding max retries land in `*.failed` dead-letter queue
- Inspection commands return accurate message counts

### Usage Template

```
Add a [channel].process queue for the [channel] notification channel with:
- 3 retry attempts with 1min/5min/30min backoff
- Dead-letter routing to [channel].failed
- A Pydantic message schema with version field
Show the diff and wait for my confirmation before applying.
```
