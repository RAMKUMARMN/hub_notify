Skill: Python Project Conventions

Description:
This skill captures the core conventions for the `hub_notify` project so Copilot can produce consistent code: packaging, import style, logging, and error handling patterns used across `app/`, `queue/`, and `workers/`.

When to use:
- Adding new modules under `app/`, `queue/`, or `workers/`.
- Refactoring code to match project patterns.

Quick prompt templates:
- "Follow the project's existing import style and logging conventions; add a function `X` that does Y and include type hints, docstring, and unit tests." 
- "Write a small module for `workers/NAME` that processes jobs from `queue.consumer`. Use structured logging and retry on transient errors."

Examples:
- "Create `app/channels/push.py` helper `send_push(payload: dict) -> bool` matching current channel modules' style."
