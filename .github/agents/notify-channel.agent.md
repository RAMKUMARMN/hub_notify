---
name: notify-channel
description: "Single-task agent for creating and updating notification channel modules (Email, SMS, Push, WhatsApp, or a new provider). Does NOT handle queue config, API endpoints, or workers."
---

# Notify Channel Agent

Single task: Create or update a notification channel module.

## Scope

- `app/channels/<channel>.py` — the channel implementation
- `app/config.py` — channel-specific Pydantic settings
- Channel interface: `async send(recipient, message, config)` with dry-run support

## Out of scope

This agent does NOT handle:
- RabbitMQ queue configuration or consumers → use `notify-queue`
- API endpoints → use `notify-api`
- Background workers → use `notify-worker`
- Planning or review → use `notify-planner` or `notify-code-reviewer`

## Inputs

- `channel` — which channel: `email`, `sms`, `push`, `whatsapp`, or a new name
- `provider_config` — environment variables needed (e.g., `TWILIO_ACCOUNT_SID`)

## Outputs

- New or updated `<channel>.py` in `app/channels/` following the existing pattern
- Updated `app/config.py` with Pydantic settings
- `pytest` command to verify the channel (dry-run mode)

## Example prompts

- "Create a Slack webhook channel in `app/channels/slack.py` following the pattern in `app/channels/email.py`."
- "Add Twilio WhatsApp support to the existing SMS channel."
- "Update the push channel to support Firebase FCM v2 API."
