Skill: Testing Guidelines

Description:
Patterns and prompt snippets to generate unit and integration tests for this repository. Emphasizes small, deterministic tests using pytest and fixtures.

When to use:
- Adding unit tests for `app/` modules or `workers/` logic.
- Creating fixtures for queue messages and external channel mocks.

Prompt templates:
- "Write pytest unit tests for `app/channels/sms.py`. Mock external network calls and assert that `send_sms` returns True on success and raises `ValueError` for invalid input." 
- "Create a fixture `sample_job` representing a valid job payload for `queue.consumer` and use it in tests for `workers/sms_worker.py`."

Best practices:
- Keep tests isolated and fast; mock network and file I/O.
- Use parametrize for edge cases.
