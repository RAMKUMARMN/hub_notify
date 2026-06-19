---
name: trace-notify-features
description: Deep search for specific feature flows, such as QA tests or custom integrations.
---

# Trace Notify Features

Search the codebase for specific implementations spanning routers, queues, and workers.

## Focus Areas
- Test validations (test_notifications.py, test_workers.py)
- Cross-module logic

## Workflow
1. Route the hub folder agent to plugin/skills for this specific skill folder.
2. Invoke the native "findFeature" tool with your target keyword.
3. Return the cross-module trace.
