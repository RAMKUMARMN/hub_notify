---
applyTo: "**/*.py"
---
# Project coding standards for Python (Notification Microservice)

Apply the [general coding guidelines](./general-coding.instructions.md) to all code.

## Python Guidelines
- Use Python 3.11+ features: `Self` type, except*, Tomllib
- Use async/await for all I/O (FastAPI, aio-pika, aiosmtplib)
- Use Pydantic v2 for settings, request/response, and queue message schemas
- Type annotate all function signatures
- Use `pathlib.Path` for filesystem operations

## Channel Guidelines
- Each notification channel is a module in `app/channels/` (email, sms, push, whatsapp)
- All channels implement a consistent interface: `async send(recipient, message, config)`
- Channel secrets via Pydantic settings in `app/config.py` — never hardcoded
- Support dry-run mode for testing without real delivery

## Queue & Worker Guidelines
- Queue messages versioned via Pydantic schema with `version` field
- Workers use ack/nack + dead-letter routing for retry handling
- New workers register in `app/main.py` lifespan and `app/workers/`
- Worker names follow `<channel>_worker.py` convention
- Maximum retries of 3 with exponential backoff before dead-letter

## API & Operations Guidelines
- REST endpoints in `app/routers/` — `/api/v1/notify` and `/api/v1/jobs`
- Job status tracked in PostgreSQL via `NotificationJob` model
- Health check at `/health` verifies DB, RabbitMQ, and provider connectivity
- Docker uses supervisord to manage API + workers in one container
- Graceful shutdown on SIGTERM for queue consumers
