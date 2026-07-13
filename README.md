# Skills

[![skills.sh](https://skills.sh/b/tflaim/skills)](https://skills.sh/tflaim/skills)

Nine portable skills for AI coding agents. Each skill uses the Agent Skills SKILL.md format and is designed to work across Claude Code, Codex, Cursor, and other compatible runtimes.

## Installation

Install the catalog with the [skills CLI](https://www.skills.sh/docs/cli):

    npx skills@latest add tflaim/skills

Install one skill:

    npx skills@latest add tflaim/skills --skill baton

Install globally instead of in the current project:

    npx skills@latest add tflaim/skills -g

The skills CLI collects anonymous installation telemetry by default. To opt out:

    DISABLE_TELEMETRY=1 npx skills@latest add tflaim/skills

### Manual fallback

Clone the repository:

    git clone https://github.com/tflaim/skills.git ~/skills

Then copy the skill you want into the directory documented by your agent. For example:

    cp -R ~/skills/skills/baton ~/.claude/skills/baton

## Security note

Skills are instructions to an AI agent with tool access. Review a skill before installing it or pointing an agent at sensitive work.

## Catalog

| Skill | What it does |
| --- | --- |
| [baton](#baton) | Creates an actionable state transfer for a fresh agent session |
| [deslop](#deslop) | Removes AI writing patterns while preserving meaning and register |
| [expert-review](#expert-review) | Applies a grounded expert persona to critique an artifact |
| [explain-system](#explain-system) | Builds a verified mental model of a technical system |
| [pr-preflight](#pr-preflight) | Gates commit, push, and PR actions on repository readiness |
| [pr-review-feedback](#pr-review-feedback) | Adjudicates reviewer claims before code or PR changes |
| [skill-forge](#skill-forge) | Searches for skill improvements and gates promotion on held-out evidence |
| [skill-grinder](#skill-grinder) | Runs controlled skill mutations with anchored evaluation |
| [vet-idea](#vet-idea) | Stress-tests an idea and captures the resulting decisions in a spec |

## Skills

### baton

Creates a state-transfer document a fresh agent can act on without reconstructing the conversation. It captures the done state, ruled-out approaches, live artifacts, repository state, next concrete action, required context, and the exact first prompt to paste.

The handoff adapts to the target runtime and requires user approval before writing the file.

### deslop

Edits AI-sounding prose in two passes: remove recurring patterns, then restore an appropriate human voice. It defaults to a professional register, respects user and project style rules, preserves facts and quotations, and loads the detailed pattern reference only when needed.

The skill includes an attributed MIT license and a detailed patterns reference.

### expert-review

Reviews an artifact through a user-selected expert, an automatically selected expert, or a small multi-domain panel. It grounds claims in the referenced artifact and source system, challenges assumptions, checks affected stakeholders, and closes every issue with a concrete recommendation.

### explain-system

Explores code or documentation until it can explain a system as a mental model rather than a file inventory. It traces an entry path, verifies critical claims, marks inference and uncertainty, proposes an adaptive outline, and uses diagrams or integration maps only when they help.

Exploration is capability-based and portable across runtimes.

### pr-preflight

Runs before commit, push, or PR creation. It snapshots staged and unstaged intent, fetches remote truth, checks repository conventions, reviews the actual diff, runs targeted deterministic checks, and blocks the requested action when material concerns remain.

It preserves unrelated local work and derives branch or ticket conventions from the repository instead of imposing a global policy.

### pr-review-feedback

Turns reviewer feedback into source claims, verifies each claim against current code, classifies the verdict, and fixes only accepted issues. It preserves the distinction between valid, partially valid, not valid, duplicate, and out-of-scope feedback.

PR writes require user authorization and available write access. Otherwise the skill returns an exact draft response.

### skill-forge

Combines bounded mutation search with explicit validation and promotion gates. It separates Found, Accepted, Promoted, Compressed, and Rejected outcomes, checks whether validation covers observed train failures, and rejects incomparable evidence.

The bundled standard-library helper is self-contained:

    python3 scripts/skill_forge.py init-run ...
    python3 scripts/skill_forge.py apply-edits ...
    python3 scripts/skill_forge.py check-validation ...
    python3 scripts/skill_forge.py decide ...

### skill-grinder

Runs a controlled mutation loop against an existing skill. Baseline and candidate samples are compared on the same inputs, narrow changes receive focused regression checks, borderline results are resampled, and compression wins are kept separate from quality claims.

Adapted from Andrej Karpathy's [autoresearch methodology](https://www.youtube.com/watch?v=LBMiNFBp0cI), applying autonomous experimentation loops to prompt engineering.

It produces an auditable run directory outside the target skill, including the frozen pair manifest, pair ledger, results, and changelog.

### vet-idea

Stress-tests an existing direction through one challenging question at a time. It inspects available context before asking, includes a genuine challenger option, avoids inventing hard requirements, and stops immediately when the user asks for the best available spec.

It produces a focused spec with requirements, reasoning, open questions, execution guidance, and context files.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

The repository is MIT by default. The deslop skill retains its attributed MIT license.
