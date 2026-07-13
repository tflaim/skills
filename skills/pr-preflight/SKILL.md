---
name: pr-preflight
description: Run before committing, pushing, or creating/opening a PR. Triggers on "commit and push", "push PR", "create/open PR", "run before push", "prep this PR", "ready to push", or similar requests. Reviews the current branch against the updated remote base, runs deterministic checks, performs a bounded review/fix/verify pass, and blocks unsafe git/GitHub actions.
---

# PR Preflight

Use this skill as the final readiness gate before work leaves the machine or becomes reviewable.

Do not treat this as a raw Git hook. Keep the process conversational and visible because preflight may edit files, preserve staged intent, restage only intended changes, or stop before push.

## Done State

Pass only when:

- branch naming has been checked before the requested commit, push, or PR action
- the diff is reviewed against the updated remote base
- deterministic checks appropriate to the touched files pass, or blockers are explicit
- no accepted `blocker`, `high`, or material local `medium` concern remains
- the commit, push, or PR creation includes only intended files

If those conditions are not met, stop before the requested git/GitHub action and report the exact residuals.

## Workflow

1. Snapshot current state:
   - run `git status --short` and identify staged, unstaged, untracked, and unrelated dirty files
   - run `git branch --show-current` before committing, pushing, or creating/opening a PR, and record whether the branch is detached, protected, tool-generated, or convention-compliant
   - preserve unrelated user changes and do not add them to a commit
   - if staged intent is unclear, stop before committing and ask for direction
   - if any unstaged file could plausibly belong to the requested change, do not commit or push staged-only work until the user explicitly includes it, excludes it, or says to proceed staged-only
   - keep clearly unrelated local files such as `.env*` out of the action unless the user explicitly names them
2. Refresh remote truth:
   - run `git fetch origin --prune` when a remote exists
   - detect the default/base branch dynamically from PR metadata, upstream config, `origin/HEAD`, or remote defaults
   - compare against remote refs, not stale local assumptions
3. Read repo instructions and local conventions:
   - load project guidance such as `AGENTS.md`, `CLAUDE.md`, package docs, and nearby tests when relevant
   - compare the current branch name to repository or team conventions from local instructions, recent branches, explicit ticket identifiers, or user context
   - before commit, push, or PR creation, if a clear branch naming convention exists and the current branch violates it, rename or create a convention-compliant branch; block and ask for direction when the intended name is ambiguous
   - do not treat tool-generated prefixes such as `codex/` as team conventions unless the user or repo instructions explicitly ask for them
   - check exports and immediate callers before assuming a file is independent
4. Inspect the actual diff:
   - review staged and unstaged changes separately when commit boundaries matter
   - include changed tests, generated files, manifests, lockfiles, schemas, migrations, docs, and config
5. Run deterministic checks first:
   - always run `git diff --check`
   - run the smallest relevant type, lint, test, build, schema, generated-artifact, or docs checks implied by the diff and repo instructions
   - prefer targeted checks first, then broader checks when the touched surface is shared or risky
6. Run bounded review passes:
   - behavior/spec: user-visible behavior, edge paths, failure paths, and request/spec fit
   - tests/validation: tests prove the real contract at the right layer and validation matches touched behavior
   - type/generated/dependency: type boundaries, casts, nullability, generated artifacts, schemas, manifests, and lockfiles
   - structural maintainability: architecture regression, spaghetti growth, wrong-layer logic, thin wrappers, duplicate helpers, file-size growth, and obvious simplification opportunities
   - repo-specific policy: local instructions, security boundaries, release rules, and domain-specific review checklists
7. Use review agents only when available and allowed by the active runtime or explicitly requested by the user. Keep them no-edit and bounded. If review agents are unavailable or not permitted, perform the same passes locally and say they were skipped.
8. Coordinate findings:
   - accept only concrete concerns with a file/line, command, policy, or diff evidence
   - reject vague, preference-only, speculative, or low-value nits
   - fix accepted `blocker`, `high`, and material local `medium` concerns when the fix preserves intent
   - do not do broad redesign during preflight unless the current diff creates a clear maintainability or correctness risk
9. Rerun affected checks after fixes.
10. Proceed with the requested commit, push, or PR creation only after the done state is met. Otherwise report blocked status.

If the request is too small to establish repo state, such as only `push`, keep the response short: block, say the missing context or inspection permission, and do not invent completed checks.

## Structural Maintainability Pass

Flag aggressively when the current diff:

- makes a file cross from under 1000 lines to over 1000 lines without a strong reason
- adds scattered feature checks, one-off flags, nullable modes, or special-case branches into busy shared flows
- introduces wrappers, adapters, generic dependency bags, or pass-through helpers that do not delete complexity
- adds `any`, `unknown`, casts, unclear optionality, or silent fallback where a typed boundary should express the invariant
- puts feature logic in the wrong package, module, or ownership layer
- duplicates a canonical helper or pattern that already exists nearby
- creates partial-update or unnecessarily sequential orchestration where the cleaner structure is obvious

Prefer behavior-preserving remedies that delete complexity: move logic to the canonical owner, split a large file, extract a small pure helper, collapse duplicate branches, remove an unnecessary wrapper, make the type boundary explicit, or reframe the state model so conditionals disappear.

Severity guide:

- `blocker`: the diff is review-hostile or risky, such as unjustified 1000-line crossing, scattered shared-path feature logic, wrong-layer durable behavior, or clearly tangled control flow.
- `high`: an obvious simpler structure would remove branches, wrappers, casts, or duplicated logic and is local enough to fix before push.
- `medium`: local cleanup that preserves intent and materially improves readability or ownership.
- `low`: naming, style, or taste. Do not block push solely on low findings.

## Output

Report only:

- `pr-preflight: pass` or `pr-preflight: blocked`
- branch name check result and any rename/block taken
- base ref and diff scope reviewed
- validation commands and results
- review-agent status if used or intentionally skipped
- accepted fixes made
- residual `blocker`, `high`, or material `medium` concerns
- commit/push/PR action taken, or the exact reason it was not taken
