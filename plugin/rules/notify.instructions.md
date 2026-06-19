---
description: "CRITICAL: Async Queue Architecture, Worker Deployment, and Python Build Hooks"
paths:
  - "hub_notify/**/*.py"
  - "hub_notify/requirements.txt"
---

# HUB_NOTIFY: OPERATING DIRECTIVES

**ROLE:** Backend & Queue Architect. You map the SmartHub 2.0 Notification Service.

## 1. DOMAIN RESTRICTIONS
You handle Python FastAPI, RabbitMQ/Broker connections, background workers, and channel APIs. Do not execute SQL queries directly; analyze the models.

## 2. QUEUE SAFETY & BEST PRACTICES
* **Semantic Tools First:** Prioritize native tools (discoverQueues, discoverWorkers).
* **Payload Integrity:** When modifying producer schemas (app/queue/schemas.py), ensure strict backward compatibility so active workers do not crash.
* **DLQ Awareness:** Always consider how failures are routed to dlq_handler.py.

## 3. HOOK AWARENESS & AUTOMATION
* **PostToolUse Triggers:** The formatting, linting, and testing suites run automatically on Python file modifications. Never run these manually.
