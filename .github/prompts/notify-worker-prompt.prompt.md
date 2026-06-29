---
mode: agent
agent: notify-worker
name: notify-worker-prompt
description:
  Prompt for the notify-worker agent. Creates or updates background queue workers that consume messages from RabbitMQ and dispatch through notification channels.
---

### Requirements

1.  **Worker Module:** Create a new file `app/workers/<name>_worker.py` following the pattern in existing workers. Must consume from a specific queue and call the corresponding channel's `send()`.
2.  **Lifespan Registration:** Register the worker in `app/main.py` lifespan so it starts/stops with the application.
3.  **Re-export:** Add the worker to `app/workers/__init__.py`.
4.  **Graceful Shutdown:** Handle SIGTERM to stop consuming and allow in-flight messages to complete.

### Constraints

- Python 3.11+ with async/await
- Worker consumes from a single queue (e.g., `email.process`)
- Worker calls the channel module — does NOT implement delivery logic itself

### Success Criteria

- Worker starts and connects to RabbitMQ on application startup
- Worker consumes messages and calls the correct channel `send()` method
- Worker acknowledges on success, nacks on failure
- Worker shuts down gracefully on SIGTERM
- `pytest` unit test verifies worker message processing

### Usage Template

```
Create a [name] worker in app/workers/[name]_worker.py that:
- Consumes from the [queue_name] queue
- Calls app/channels/[channel].py send() for delivery
- Acknowledges on success, nacks with requeue=false on failure
- Is registered in app/main.py lifespan
Show the diff and wait for my confirmation before applying.
```
