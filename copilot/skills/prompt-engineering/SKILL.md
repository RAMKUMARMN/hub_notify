Skill: Prompt Engineering for Copilot

Description:
Guidance and reusable prompt patterns for getting predictable, high-quality code suggestions from Copilot in this repo.

Core principles:
- Be specific about function signatures, return types, and side effects.
- Provide surrounding context: file path, related modules, and desired tests.
- Ask for small, focused changes rather than large rewrites.

Reusable prompt templates:
- "In [file path], implement `function_name(args)` to do X. Follow project patterns: type hints, logging, and simple error handling. Include docstring and one pytest unit test." 
- "Refactor [module] to extract helper `name()` without changing external behavior. Keep existing tests passing." 

Dos:
- Supply exact module paths and expected behavior.
- Request unit tests with fixtures when I/O or external services are involved.

Don'ts:
- Don't ask for broad 'improve code' without constraints.

Example prompt:
- "In app/channels/email.py, add `format_email(template_name: str, context: dict) -> str` using jinja2-style formatting used elsewhere. Add a unit test in `sample/` demonstrating expected output." 
