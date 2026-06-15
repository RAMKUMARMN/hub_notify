---
name: notify-agent-skills
description: Skills for the `hub_notify` assistant: notification channel configuration (Email, SMS, Push, WhatsApp), RabbitMQ queue management, FastAPI HTTP API, worker supervision, and safe service maintenance. The agent helps maintainers set up and manage the notification microservice in the repository, with a strong emphasis on safety and human oversight for production-impacting changes.
---
# Notify Agent — Skills Catalog

This document describes the skills, inputs/outputs, tools, safety constraints, and example prompts the `notify-agent` (see `notify agent.agent.md`) supports for the `hub_notify` repository.

**Purpose**
- Provide a compact, discoverable list of the agent's actionable capabilities so maintainers can quickly know what to ask and what to expect.

**Quick summary**
- **Primary domain:** Notification microservice (Email via SMTP, SMS/WhatsApp via Twilio, Push via FCM/APNs, RabbitMQ queue processing).
- **Primary outputs:** repository patches/diffs, GitHub Actions workflow files, CI job templates, README snippets, and PR-ready descriptions.
- **Primary safety posture:** Prepare and validate configuration changes; never autonomously send production notifications or modify live queues without explicit maintainer confirmation.

## Capabilities

- Generate or update GitHub Actions workflows to run `ruff check .`, `pytest -q`, and Docker build.
- Create or update notification channel modules (`app/channels/`) following existing patterns.
- Configure RabbitMQ queue consumers with retry logic and dead-letter routing.
- Create or update HTTP API endpoints for single-send and bulk notification jobs.
- Produce repository patches via `apply_patch` (small, focused edits) and provide diffs for review before applying.
- Run static checks in CI: `ruff check .`, `pytest -q`, optional mypy integration.
- Draft PR descriptions, risk notes, and post-deployment verification checklists.
- Create safe queue inspection commands and dry-run test flows.

## Inputs the agent expects (ask if missing)
- `channel` -- which notification channel to configure: `email`, `sms`, `push`, `whatsapp`, or `new`.
- `queue_name` -- the RabbitMQ queue name to inspect or modify.
- `secret_names` -- repo secret names for `SMTP_PASSWORD`, `TWILIO_AUTH_TOKEN`, `FIREBASE_SERVICE_ACCOUNT_BASE64`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, etc.
- `notification` config -- repo secret name for `SLACK_WEBHOOK_URL` or `NOTIFICATION_EMAIL`.

## Outputs the agent produces
- New or modified workflow YAML files in `/.github/workflows/` (e.g., `notify-ci.yml`).
- New Python files (channel modules, workers, routers) or patches to existing ones.
- README/docs snippets describing required secrets and how to run the service.
- PR-ready changelog/summary and verification checklist.
- Patches (diffs) applied with `apply_patch` when given explicit permission.

## Tools the agent uses
- `apply_patch` -- create or update repo files (used only after human confirmation for impactful changes).
- `read_file`, `file_search`, `grep_search` -- inspect repo layout and find Python modules or config files.
- `manage_todo_list` -- track multi-step tasks and report progress back to the maintainer.
- `run_in_terminal` -- only if explicitly requested; otherwise the agent outputs commands for maintainers to run locally or in CI.

## Safety, boundaries, and policies

- Never request or accept raw secrets in chat messages. Instead, the agent asks for secret *names* (e.g., `SMTP_PASSWORD`, `TWILIO_AUTH_TOKEN`) and instructs maintainers to set them in GitHub Secrets.
- Never send production notifications without an explicit confirmation token: `CONFIRM_PROD_NOTIFICATION` (maintainer must provide this token before the agent takes any action that would send real notifications or modify production queue configs).
- No direct production queue mutations (purge, delete, move) without explicit human approval.
- No automatic PR merging or repo-level approvals -- the agent drafts, explains, and optionally creates patches/PRs after explicit permission.

## Confirmation and escalation rules
- Low-risk edits (formatting, docs, test additions): agent may apply patches after a single maintainer approval.
- Medium-risk edits (new channel modules, worker logic changes, API additions): require an explicit approval message before applying patches.
- High-risk edits (changes that enable or run production notification delivery, alter queue retry/dead-letter config, or modify production worker startup): require the typed confirmation `CONFIRM_PROD_NOTIFICATION` and a second acknowledgment (e.g., "I understand this may send real notifications").

## Example prompts (how to ask the agent)
- "Create a `notify-ci.yml` workflow that runs `ruff check .`, `pytest -q`, and Docker build on push and PR; use PostgreSQL and RabbitMQ service containers; post results to Slack via `SLACK_WEBHOOK_URL`."
- "Add a Slack webhook notification channel following the pattern in `app/channels/email.py` -- show me the patch before applying."
- "Draft a queue health check command that inspects all queues and reports message counts and consumer status."

## Typical workflows the agent supports

1. Discovery: scan repo for `app/channels/*`, `app/workers/*`, `app/routers/*`, and existing config files.
2. Draft: create a draft channel module or worker with tests.
3. Review: produce a PR description, risk summary, and required secrets docs.
4. Apply (human-gated): upon confirmation, the agent can apply small, non-production patches or add CI steps; production notification changes require `CONFIRM_PROD_NOTIFICATION`.

## Error handling & troubleshooting behavior
- If `ruff check .` or `pytest -q` fails, the agent returns a concise diagnostics summary and suggests fixes.
- If queue workers fail to connect to RabbitMQ or show consumer errors, the agent highlights them, explains likely causes, and recommends fixes.

## How progress is reported
- The agent uses `manage_todo_list` to break tasks into steps (discover -> draft -> patch -> verify) and will report the current step and completed steps in chat messages.

## Where to find the agent's configuration and prompts
- Agent behavior is documented in `/.github/agents/notify agent.agent.md` and the repository prompt lives at `/.github/prompts/notify-prompt.prompt.md`.

## Maintenance notes
- Keep `SKILLS.md` aligned with `notify agent.agent.md` and `notify-prompt.prompt.md` -- update all three when adding new capabilities (for example, support for a new notification channel or a different queue backend).
