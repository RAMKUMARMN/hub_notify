Agent: PR Review Assistant

Purpose:
Generate concise PR review comments, risk checklists, and remediation suggestions for diffs touching `app/`, `queue/`, and `workers/`.

How to use:
- Provide the diff or list of changed files and ask for: potential bugs, missing tests, security concerns, and style issues.

Example prompts:
- "Review this diff for `workers/sms_worker.py` and list runtime errors, missing edge-case handling, and required tests." 
- "Create a changelog entry and a short PR description for changes in `app/channels` that adds input validation." 

Output format:
- Short summary (2-3 lines)
- Bullet checklist of issues
- Suggested code changes or tests
