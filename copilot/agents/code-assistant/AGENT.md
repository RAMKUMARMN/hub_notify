Agent: Code Assistant

Purpose:
Help implement small, well-scoped code changes, follow repository conventions, and produce unit tests. Use when adding new modules, functions, or small refactors.

Guidelines for prompts:
- Include the target file path and a short description of desired behavior.
- Specify required signatures, return types, and error handling expectations.
- Ask for a corresponding unit test when behavior is non-trivial.

Example prompts:
- "In app/channels/email.py implement `format_email(template: str, ctx: dict) -> str` using existing project patterns. Add a pytest unit test." 
- "Refactor `queue/consumer.py` to extract `validate_payload(payload)` and keep behavior unchanged. Include tests for invalid payloads."

Constraints:
- Keep changes minimal and backwards-compatible.
- Use the project's logging and typing conventions.
