---
name: notify-agent-skills
description: "Skills catalog for the hub_notify repository. Six single-task agents handle specific domains: channel modules, queue configuration, API endpoints, workers, planning, and code review."
---

# Notify Agent — Skills Catalog

This document catalogs all single-task agents available for the `hub_notify` repository. Each agent handles exactly one task domain.

## Agents

### 1. notify-channel
- **File:** `notify-channel.agent.md` / Prompt: `notify-channel-prompt.prompt.md`
- **Single task:** Create or update a notification channel module (Email, SMS, Push, WhatsApp, or new provider)
- **Scope:** `app/channels/<channel>.py`, `app/config.py` (settings), dry-run support
- **Example prompt:** *"Create a Slack webhook channel following the pattern in app/channels/email.py."*

### 2. notify-queue
- **File:** `notify-queue.agent.md` / Prompt: `notify-queue-prompt.prompt.md`
- **Single task:** Configure or inspect RabbitMQ queues, exchanges, bindings, retry/dead-letter routing
- **Scope:** `app/queue/schemas.py`, `app/queue/producer.py`, `app/queue/consumer.py`, `app/queue/job_store.py`
- **Example prompt:** *"Add a slack.process queue with 3 retry attempts and dead-letter routing."*

### 3. notify-api
- **File:** `notify-api.agent.md` / Prompt: `notify-api-prompt.prompt.md`
- **Single task:** Create or update FastAPI REST endpoints
- **Scope:** `app/routers/notify.py`, `app/routers/jobs.py`, Pydantic request/response schemas
- **Example prompt:** *"Add a POST /api/v1/notify/send endpoint with recipient, channel, and message fields."*

### 4. notify-worker
- **File:** `notify-worker.agent.md` / Prompt: `notify-worker-prompt.prompt.md`
- **Single task:** Create or update background queue workers and register in `app/main.py` lifespan
- **Scope:** `app/workers/<name>_worker.py`, `app/workers/__init__.py`, `app/main.py`
- **Example prompt:** *"Create a Slack worker that consumes from slack.process and calls the Slack channel."*

### 5. notify-planner
- **File:** `notify-planner.agent.md`
- **Single task:** Generate implementation plans before any code work begins
- **Scope:** Read-only — produces Markdown plan documents only
- **Example prompt:** *"Plan adding a rate-limiting layer to the notify API endpoint."*

### 6. notify-code-reviewer
- **File:** `notify-code-reviewer.agent.md`
- **Single task:** Review code changes across correctness, readability, architecture, security, and performance
- **Scope:** Read-only — produces categorized review reports
- **Example prompt:** *"Review this PR for correctness and security before merge."*

## Safety policies (all agents)

- Never request or accept raw secrets in chat messages
- Never send production notifications without `CONFIRM_PROD_NOTIFICATION` token
- No direct production queue mutations without explicit human approval
- No automatic PR merging or repo-level approvals

## Maintenance notes

Keep `SKILLS.md` aligned with all `.agent.md` files and `.prompt.md` files. When adding a new agent:
1. Create `<agent-name>.agent.md` in `.github/agents/`
2. Create `<agent-name>-prompt.prompt.md` in `.github/prompts/` (if the agent uses a prompt)
3. Update this `SKILLS.md` catalog
4. Update `copilot-instructions.md` agent list
