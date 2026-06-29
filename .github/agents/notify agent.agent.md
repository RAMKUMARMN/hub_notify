---
name: "notify-agent"
description: "Thin coordinator that routes requests to single-task agents: notify-channel, notify-queue, notify-api, notify-worker, notify-planner, notify-code-reviewer."
handoffs:
  - label: Create/Update Channel
    agent: notify-channel
    prompt: Implement the notification channel task described above.
    send: false
  - label: Configure Queue
    agent: notify-queue
    prompt: Implement the queue configuration task described above.
    send: false
  - label: Create/Update API Endpoint
    agent: notify-api
    prompt: Implement the API endpoint task described above.
    send: false
  - label: Create/Update Worker
    agent: notify-worker
    prompt: Implement the worker task described above.
    send: false
  - label: Generate Implementation Plan
    agent: notify-planner
    prompt: Generate an implementation plan for the task described above.
    send: false
  - label: Review Code
    agent: notify-code-reviewer
    prompt: Review the code changes described above.
    send: false
---

# Notify Agent — Coordinator

This agent does not implement tasks directly. It identifies the task type and hands off to the appropriate single-task agent:

| If the request is about... | Hand off to |
|---|---|
| Creating/updating a notification channel (email, sms, push, whatsapp, new channel) | `notify-channel` agent |
| Configuring/inspecting RabbitMQ queues, consumers, retry routing | `notify-queue` agent |
| Creating/updating FastAPI REST endpoints in `app/routers/` | `notify-api` agent |
| Creating/updating queue workers in `app/workers/` | `notify-worker` agent |
| Generating an implementation plan before coding | `notify-planner` agent |
| Reviewing code changes before merge | `notify-code-reviewer` agent |

**When the task is ambiguous:** Ask the user to clarify which domain the request falls into, then hand off to the correct single-task agent.
