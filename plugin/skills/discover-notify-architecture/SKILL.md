---
name: discover-notify-architecture
description: Map the foundational Python architecture, dependencies, and environment configs.
---

# Discover Notify Architecture

Analyze the core structure of the Notification Service.

## Focus Areas
- Python Dependencies (requirements.txt)
- Application Configs (app/config.py)
- Database Schemas (app/models/notification.py)

## Workflow
1. Route the hub folder agent to plugin/skills for this specific skill folder.
2. Invoke the native "discoverNotifyArchitecture" tool.
3. Invoke the native "discoverEnvironmentConfig" tool.
4. Return the architectural blueprint.
