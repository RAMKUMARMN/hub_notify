---
name: notify-queue
description: "Single-task agent for configuring and inspecting RabbitMQ queues, consumers, retry routing, and dead-letter logic. Does NOT handle channel implementations, API endpoints, or workers."
---

# Notify Queue Agent

Single task: Configure or inspect RabbitMQ queues, exchanges, bindings, and retry/dead-letter routing.

## Scope

- `app/queue/schemas.py` — Pydantic message schemas (versioned)
- `app/queue/producer.py` — message publishing
- `app/queue/consumer.py` — message consumption, ack/nack, retry routing
- `app/queue/job_store.py` — job status tracking
- Queue topology: exchanges, queues, bindings, DLQs, TTL

## Out of scope

This agent does NOT handle:
- Channel provider implementations → use `notify-channel`
- HTTP API endpoints → use `notify-api`
- Background worker logic → use `notify-worker`
- Planning or review → use `notify-planner` or `notify-code-reviewer`

## Inputs

- `queue_name` — the queue to configure or inspect (e.g., `email.process`, `sms.retry`)
- `routing_key` — binding pattern for the exchange
- `retry_config` — max retries, backoff intervals, dead-letter target

## Outputs

- Updated queue schema, producer, or consumer code
- RabbitMQ management commands or API calls for inspection
- `pytest` command to verify queue behavior

## Example prompts

- "Add a `slack.process` queue with retry routing (3 retries, 1min/5min/30min backoff) and dead-letter to `slack.failed`."
- "Inspect all queues and report message counts and consumer status."
- "Update the retry logic in the consumer to use exponential backoff instead of fixed delays."
