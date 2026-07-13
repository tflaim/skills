# Contributing

Contributions should remain portable, focused, and independently verifiable.

## Add or change a skill

1. Create or edit a lower-case, hyphenated directory under skills.
2. Include SKILL.md with a matching name and a description that explains when the skill should trigger.
3. Keep SKILL.md under 500 lines. Put supplementary guidance in references and executable utilities in scripts.
4. If the skill needs Codex-specific UI metadata, put it in agents/openai.yaml using the interface mapping.
5. Reference every bundled file from SKILL.md or explain why it is development-only.
6. Update README.md and skills.sh.json when catalog membership changes.

## Portability gate

Public skills must not contain:

- absolute user or home-directory paths
- company, product, repository, ticket, or branch conventions that are not intrinsic to the skill
- local run names or evaluation workspaces
- private sibling dependencies
- backup snapshots, .DS_Store, __pycache__, or .pyc files
- runtime-specific tool syntax when capability-based language works

Keep machine-local evaluation artifacts outside the repository.

## Validation gate

Before opening a PR:

1. Validate structure and internal links for every changed skill.
2. Run deterministic tests for bundled scripts.
3. Compare the candidate against the current version on focused train, validation, and unseen holdout cases.
4. Include at least one mechanical assertion for each changed behavior.
5. Check trigger routing with positive queries and difficult near-misses.
6. Confirm no mandatory failures or portability violations remain.
7. Record the exact validation commands and a concise evidence summary in the PR.

Use the smallest evaluation that can falsify the intended claim. Expand it when results are noisy or the change affects several behavior axes.

## Pull requests

Prefer one coherent change per PR. Several skills may share a PR when the delivery unit is a catalog migration or coordinated portability release, but each skill still needs independent validation evidence.

Preserve attribution and per-skill licenses. Do not include raw local evaluation artifacts.

## Code of conduct

Be respectful. Focus review on correctness, portability, and usefulness.
