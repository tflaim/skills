---
name: pr-review-feedback
description: Adjudicate PR review feedback before making changes. Use when asked to respond to or address reviewer, CI, or automated-review feedback on a pull request. Verify every claim against current source truth, classify the verdict, fix only accepted issues, and draft or post an authorized response.
---

# PR Review Feedback

Use this skill when review feedback arrives and the next move could be code changes, a PR comment, or a decision to push back.

The core rule: adjudicate before acting. Reviewer feedback is input, not truth.

## Done State

Pass only when:

- every material reviewer claim has been verified against the current branch or PR diff
- each claim is classified as `valid`, `partially valid`, `not valid`, `duplicate`, or `out of scope`
- accepted fixes are implemented, tested, and pushed when the user wants the PR updated
- declined or deferred feedback has a concrete reason
- the PR response says what was accepted, changed, declined, or deferred

If the current source truth cannot be checked, stop and say what is missing. Do not implement from the review text alone.

If the input has no adjudicable claims (e.g. only "CC reviewed this") or no checkable source, do not emit a claim table or the full output shape. Reply in under 80 words: name what is missing (the specific reviewer findings, and the PR/branch or code to verify against) and ask for it. Do not fabricate an adjudication.

## Workflow

1. Capture the review source:
   - read the linked PR comment, review, CI output, or inline annotations
   - if the user pasted feedback, use that as input but still verify against source
   - fetch current PR metadata and branch state when GitHub access is available
2. Snapshot repo state:
   - run `git status --short --branch`
   - preserve unrelated dirty files
   - identify whether you are on the PR branch, a detached worktree, or the wrong branch
3. Turn feedback into claims:
   - rewrite each material point as a concrete source claim
   - include file/path/line references when the reviewer provides them
   - separate blockers from suggestions and style notes
4. Verify each claim:
   - inspect the named files and immediate callers
   - check tests, schemas, ownership boundaries, and runtime behavior where relevant
   - do not infer from old repo lore when current source or PR diff is available
5. Classify:
   - `valid`: source confirms the issue and it matters
   - `partially valid`: the concern is real, but scope, severity, or proposed fix needs adjustment
   - `not valid`: source disproves the claim
   - `duplicate`: already covered by another accepted fix
   - `out of scope`: real or plausible, but outside the ticket or current PR contract
6. Decide action:
   - fix `valid` and intentionally accepted `partially valid` findings
   - decline or defer with evidence when a finding is `not valid`, `duplicate`, or `out of scope`
   - if accepting feedback changes behavior beyond the ticket, call out the tradeoff before or while fixing
7. Validate:
   - run targeted checks first
   - run broader checks when the touched surface is shared, user-facing, security-sensitive, or required by repo instructions
   - rerun after fixes
8. Respond on the PR only when the user has authorized PR writes and the runtime has write access:
   - summarize accepted fixes and commit hash
   - list validation commands
   - mention declined/deferred findings briefly with rationale
   - avoid defensive tone, but do not pretend unaccepted feedback was fixed
   - otherwise, provide the exact response as a draft and make no external write

## Guardrails

- Do not batch-apply reviewer suggestions.
- Do not treat confident wording as evidence.
- Do not turn optional suggestions into scope creep unless the current PR needs them.
- Do not weaken the original ticket silently to satisfy a reviewer. Name the tradeoff.
- Do not claim a finding is fixed until code and tests prove the accepted contract.
- Do not hide behavior changes inside a generic “address review” comment.
- Do not write to a PR without user authorization and confirmed write access.

## Output Shape

For a read-only pass:

```text
pr-review-feedback: adjudicated

| Claim | Verdict | Evidence | Action |
| --- | --- | --- | --- |
| ... | valid | path:line ... | fix |

Blocked/deferred:
- ...
```

For a fix pass:

```text
pr-review-feedback: updated

Accepted and fixed:
- ...

Declined or deferred:
- ...

Validation:
- ...

PR comment:
- ...
```
