---
name: notify-worker
description: "Single-task agent for creating and updating queue workers in app/workers/ and registering them in app/main.py. Does NOT handle channel implementations, queue topology, or API endpoints."
---

# Notify Worker Agent

Single task: Create or update background queue workers and register them in the application lifespan.

## Scope

- `app/workers/<name>_worker.py` — worker implementation (process messages from queue)
- `app/workers/__init__.py` — re-export of the worker
- `app/main.py` — lifespan registration for startup/shutdown
- Worker pattern: consume messages, call channel `send()`, ack/nack, handle retries

## Out of scope

This agent does NOT handle:
- Channel provider implementations → use `notify-channel`
- Queue topology or routing → use `notify-queue`
- HTTP API endpoints → use `notify-api`
- Planning or review → use `notify-planner` or `notify-code-reviewer`

## Inputs

- `worker_name` — the worker name (e.g., `slack`, `email`, `sms`)
- `queue_name` — the queue to consume from (e.g., `slack.process`)
- `channel_module` — the channel module to call for delivery

## Outputs

- New or updated worker file in `app/workers/`
- Updated `app/main.py` lifespan with worker startup/shutdown
- `pytest` command to verify worker behavior

## Example prompts

- "Create a Slack worker in `app/workers/slack_worker.py` that consumes from `slack.process` and calls the Slack channel."
- "Add graceful shutdown handling to the email worker."
- "Register the existing SMS worker in `app/main.py` lifespan."
