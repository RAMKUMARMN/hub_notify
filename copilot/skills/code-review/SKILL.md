Skill: Code Review Prompts

Description:
Short guidance to prompt Copilot to generate review comments, find potential issues, and suggest improvements tailored to this repository.

Use cases:
- Generate a checklist for reviewing changes in `queue/` or `workers/`.
- Produce suggested PR review comments focusing on correctness, logging, and error handling.

Prompt templates:
- "Review the following diff for `workers/sms_worker.py` and list possible runtime errors, missing tests, and suggestions to improve logging and retries." 
- "Provide a concise PR checklist for changes touching `app/channels/*`: security, input validation, and test coverage." 
