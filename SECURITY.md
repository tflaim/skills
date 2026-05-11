# Security Policy

Skills are markdown files that instruct an AI coding agent. If a SKILL.md tells the agent to read secrets, execute arbitrary commands, or fetch hostile content, the agent will follow those instructions to the extent its tool permissions allow. Review before installing.

## Reporting a concern

If you find a SKILL.md in this repo that could be misused, please report it privately:

- **Preferred:** open a private vulnerability report via the [Security tab](https://github.com/tflaim/skills/security/advisories/new).
- **Alternative:** open a public issue for low-severity concerns (typos, awkward phrasings).

Please do not include exploit details or sensitive data in public issues.

## Out of scope

- The AI agent runtime (Claude Code, Codex, Cursor, Aider, Cline, or others). Report those to the respective vendor.
- Third-party tools referenced by a skill (Docling, Twilio, etc.). Report those to their maintainers.
- Your local agent permissions or environment configuration.
