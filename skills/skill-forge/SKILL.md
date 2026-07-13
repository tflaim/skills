---
name: skill-forge
description: Use when optimizing an existing agent skill with fast mutation search and validation-gated promotion. Trigger on "skill forge", "optimize this skill", "compare skill edits", "validation-gated skill improvement", or "safe skill compression".
---

# Skill Forge

Search for useful skill edits, then accept them only when held-out evidence supports the claim. Keep search and promotion separate.

## Status language

| Status | Meaning |
| --- | --- |
| Found | Train or exploratory evidence improved, but validation did not prove generalization. |
| Accepted | Held-out validation strictly improved with zero mandatory failures. |
| Promoted | An accepted quality candidate also passed locked test without regression. |
| Compressed | A compression candidate held validation, passed mandatory checks, and reduced prompt size. |
| Rejected | The candidate regressed, overfit, lacked the required lift, or failed an invariant. |

Never call Found better. Never call Accepted promoted without locked-test evidence.

## Choose one mode

| Mode | Use when | Acceptance rule |
| --- | --- | --- |
| quality | The goal is better behavior. | Require strict held-out validation improvement. |
| compression | The goal is a smaller prompt. | Require validation tie or improvement and a smaller prompt. |
| exploratory | The goal is learning or candidate discovery. | Report useful train improvements as Found. |

Do not use exploratory mode for an efficacy claim.

## Workflow

1. Read the target SKILL.md, its linked references and scripts, and any trustworthy prior evidence.
2. Define observable success criteria and mandatory invariants before editing.
3. Build visible train and validation cases. Use different case IDs across splits and tag train failures by the behavior they exercise. Have a separate evaluator keep the locked-test bodies and give the optimizer only rows containing an opaque `id` and a `commitment_sha256` over each canonical test case. The optimizer must never receive the locked prompts.
4. Initialize a frozen run:

       python3 scripts/skill_forge.py init-run \
         --skill path/to/SKILL.md \
         --cases cases.jsonl \
         --test-commitments locked-test-commitments.jsonl \
         --run-dir run \
         --mode quality

5. Score the baseline on train and validation. Use the score schema in [run-manifest.md](references/run-manifest.md).
6. Check validation adequacy before optimizing:

       python3 scripts/skill_forge.py check-validation \
         --run-dir run \
         --train-score train-score.json \
         --out run/validation-adequacy.json

   Stop if validation does not cover every observed train failure tag.

7. Search with one bounded mutation at a time. Log attempts, including rejected edits. Apply exact patches through the helper:

       python3 scripts/skill_forge.py apply-edits \
         --skill path/to/SKILL.md \
         --edits edits.json \
         --run-dir run \
         --out run/candidates/candidate.SKILL.md

8. Score candidates on train for diagnosis and preservation of the original failures. Release validation only for plausible candidates. Release locked tests only after validation accepts the exact candidate. The external evaluator verifies the committed test bodies, runs the baseline and candidate, and returns score files bound to the run, manifest, exact skill hash, and evaluator hash.
9. Write the decision:

       python3 scripts/skill_forge.py decide \
         --mode quality \
         --run-dir run \
         --current current-validation.json \
         --candidate candidate-validation.json \
         --current-skill path/to/SKILL.md \
         --candidate-skill run/candidates/candidate.SKILL.md \
         --candidate-receipt run/candidates/candidate.SKILL.md.receipt.json \
         --validation-adequacy run/validation-adequacy.json \
         --train-score train-score.json \
         --candidate-train-score candidate-train-score.json \
         --out run/decisions/accepted.json

   Run this first without locked-test scores. Only after it returns `Accepted` or `Compressed`, send the immutable decision and exact candidate to the external evaluator. The evaluator verifies the decision's candidate hash before revealing committed test bodies, then returns score rows containing the matching case commitments. Rerun `decide` with `--test-current`, `--test-candidate`, and a new output path such as `run/decisions/final.json`. A quality candidate becomes Promoted only when locked test has no mandatory failures and does not regress.

10. Report mode, split counts, validation coverage, exact diff, status, validation delta, locked-test delta when used, prompt-size delta, and remaining failures.

## Evidence rules

- Bind every score file to the run ID, manifest hash, exact skill hash, and evaluator hash. Compare the same cases, evaluator, and maximum scores. The helper rejects stale candidates, changed evaluators, and unequal denominators.
- Treat infrastructure failures as invalid evidence, not candidate failures.
- A baseline mandatory failure blocks comparison. Repair the baseline and start a new run.
- A candidate train mandatory failure or regression on an original train failure blocks acceptance.
- A validation mandatory failure is Rejected. A locked-test mandatory failure blocks promotion and leaves a quality candidate Accepted with an explicit risk.
- A train-only win is Found.
- A locked-test regression leaves a quality candidate Accepted, not promoted. Reject a compression candidate that regresses on locked test.
- Keep evaluation artifacts outside a public skill repository unless the repository explicitly requests fixtures.

## Required run artifacts

- manifest.json
- cases/train.jsonl
- cases/validation.jsonl
- cases/test-commitments.jsonl
- validation-adequacy.json
- results.tsv
- changelog.md
- rejected-edits.jsonl
- candidate skill and receipt
- decisions/accepted.json
- decisions/final.json when locked tests run

Read [acceptance-policy.md](references/acceptance-policy.md) before making a publication or promotion claim.

## Push back

Push back when validation does not cover observed failures, a train-only win is called accepted, unrelated skill domains are mixed into one target, or an interactive skill has no observable artifact or behavior to evaluate.
