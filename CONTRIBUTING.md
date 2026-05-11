# Contributing

Contributions are welcome! Here's how to add or improve skills.

## Adding a New Skill

1. Create a directory under `skills/` with a descriptive, hyphenated name
2. Add a `SKILL.md` with YAML frontmatter:
   ```yaml
   ---
   name: your-skill-name
   description: One-line description of when to use this skill
   ---
   ```
3. Keep `SKILL.md` under 500 lines. Use a `references/` subdirectory for supplementary docs.
4. Add executable utilities in a `scripts/` subdirectory if needed.
5. Update the skills table in `README.md`.

## Skill Naming

- Lowercase letters, numbers, and hyphens only
- Max 64 characters
- Prefer gerund form (e.g., `analyzing-transcripts`) or imperative form (e.g., `review-backlog`)

## Pull Requests

- One skill per PR (unless tightly coupled)
- Include a brief description of the skill's purpose and trigger conditions
- Test the skill locally before submitting

## Code of Conduct

Be respectful. Focus on quality and usefulness.
