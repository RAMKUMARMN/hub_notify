---
mode: agent
agent: notify-planner
name: notify-planner-prompt
description:
  Prompt for the notify-planner agent. Generates structured implementation plans for notification service features, channels, queue changes, or refactoring. Read-only — never makes code edits.
---

### Requirements

1.  **Discovery:** Search the codebase for existing patterns in `app/channels/`, `app/queue/`, `app/routers/`, and `app/workers/`.
2.  **Research:** Fetch web documentation for any new libraries or provider APIs involved.
3.  **Plan:** Produce a Markdown plan with sections: Overview, Requirements, Implementation Steps, Testing.

### Constraints

- Read-only — never write code or modify files
- Plans are handed off to the appropriate implementation agent (notify-channel, notify-queue, notify-api, notify-worker)

### Success Criteria

- Plan includes all functional and non-functional requirements
- Implementation steps reference specific files and patterns
- Testing section covers unit, integration, and dry-run tests

### Usage Template

```
Plan the implementation of [feature description].
Include:
- Files to create/modify
- Configuration changes needed
- Queue topology (if applicable)
- Test strategy
Show the plan and wait for my confirmation before handing off.
```
