---
mode: agent
agent: notify-channel
name: notify-channel-prompt
description:
  Prompt for the notify-channel agent. Creates or updates a notification channel module (Email, SMS, Push, WhatsApp, or a new provider). Each channel implements an `async send()` interface with dry-run support and Pydantic-settings-backed configuration.
---

### Requirements

1.  **Channel Implementation:** Create a new file `app/channels/<channel>.py` following the pattern in `app/channels/email.py`. Must implement `async send(recipient, message, config)`.
2.  **Configuration:** Add Pydantic settings to `app/config.py` for the new channel's environment variables.
3.  **Dry-Run Mode:** Support a `dry_run` flag that logs what would be sent without actually delivering.
4.  **Error Handling:** Wrap provider API calls in try/except, return structured success/failure results.

### Constraints

- Python 3.11+ with async/await
- Provider credentials read from environment via `pydantic-settings` — never hardcoded
- Channel file must not import queue, router, or worker modules

### Success Criteria

- Channel file passes `ruff check .` and `pytest -q` without errors
- Dry-run mode logs the intended payload without calling the provider
- Provider errors are caught and returned as structured results (not exceptions)

### Usage Template

```
Create a [Slack|Teams|Webhook] notification channel in app/channels/ following the email.py pattern.
Include:
- Pydantic settings in app/config.py for the webhook URL
- Dry-run mode support
- Error handling for HTTP failures
Show the diff and wait for my confirmation before applying.
```
