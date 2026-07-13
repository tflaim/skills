# Run manifest and evidence formats

The bundled helper uses immutable JSON artifacts. It rejects duplicate JSON keys and refuses to overwrite decisions or candidates.

## Case JSONL

Each visible row requires an id, prompt, tags array, and optionally an explicit split:

    {"id":"unique-id","prompt":"user request","tags":["failure-axis"],"split":"train"}

The split field is optional only when it is omitted from every row. In that case, init-run deterministically assigns train and validation from the run ID and case ID. A run must have non-empty train and validation splits. Case IDs must be unique across all splits.

Use explicit splits for small suites so every visible split is represented.

## Locked-test commitments

The optimizer receives a separate JSONL file containing only opaque IDs and SHA-256 commitments created by the external evaluator:

    {"id":"test-a","commitment_sha256":"sha256 of the canonical private test case"}

The external evaluator keeps the test prompts outside the optimizer context. Compute each commitment as SHA-256 over UTF-8 JSON serialized with sorted keys, `,` and `:` separators, and ASCII escaping. Before scoring, the evaluator verifies that each revealed case reproduces its commitment. `init-run` writes only these commitment rows to `cases/test-commitments.jsonl`; it never writes locked prompts into the run directory.

## Patch JSON

    {
      "base_sha256": "sha256 of the baseline SKILL.md",
      "edits": [
        {
          "op": "replace",
          "target": "exact text occurring once",
          "replacement": "replacement text"
        }
      ]
    }

Targets must be unique, non-overlapping, and occur exactly once. Frontmatter edits require --allow-frontmatter-edits.

## Score JSON

    {
      "schema_version": "skill-forge-score-v1",
      "run_id": "frozen run id",
      "manifest_sha256": "sha256 from manifest.json",
      "skill_sha256": "sha256 of the skill that produced these outputs",
      "evaluator_sha256": "sha256 of the frozen evaluator and rubric configuration",
      "split": "validation",
      "score": 8,
      "max_score": 10,
      "mandatory_failures": 0,
      "cases": [
        {"id":"validation-a","score":4,"max_score":5,"mandatory_failures":0},
        {"id":"validation-b","score":4,"max_score":5,"mandatory_failures":0}
      ]
    }

Optional infrastructure_failures fields default to zero and must also match their per-case sum. Any nonzero infrastructure failure invalidates comparison.

Locked-test score rows also require `commitment_sha256`. The helper compares every value with the frozen commitment for that case ID before it can produce `Promoted` or retain `Compressed`.

Aggregate fields must equal the per-case sums. Baseline and candidate evidence must match the run and manifest, bind to their exact skill files, use the same evaluator hash, use the frozen case order, and use identical per-case maximum scores. Stale candidate evidence, a changed evaluator, or a higher raw score with a larger denominator is rejected.

Decision artifacts contain canonical payload hashes for every train, validation, and locked-test score they consume. A final locked-test decision also contains and verifies the canonical payload hash of the prior Accepted or Compressed decision, so promotion cannot bypass or silently substitute the accepted-stage evidence.

## Validation adequacy

check-validation identifies baseline train cases below their maximum score, reads their tags from the frozen train split, and confirms that those tags appear in validation. Every failed train case must have at least one tag.

The adequacy artifact is bound to the manifest and train score hashes. decide recomputes it instead of trusting the file.
