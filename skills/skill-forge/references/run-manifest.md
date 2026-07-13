# Run manifest and evidence formats

The bundled helper uses immutable JSON artifacts. It rejects duplicate JSON keys and refuses to overwrite decisions or candidates.

## Case JSONL

Each row requires an id, prompt, tags array, and optionally an explicit split:

    {"id":"unique-id","prompt":"user request","tags":["failure-axis"],"split":"train"}

The split field is optional only when it is omitted from every row. In that case, init-run deterministically assigns train, validation, and test from the run ID and case ID. A run must have non-empty train and validation splits. Case IDs must be unique across all splits.

Use explicit splits for small suites so every required split is represented.

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

Aggregate fields must equal the per-case sums. Baseline and candidate evidence must use the frozen case order and identical per-case maximum scores. A higher raw score with a larger denominator is incomparable and rejected.

## Validation adequacy

check-validation identifies baseline train cases below their maximum score, reads their tags from the frozen train split, and confirms that those tags appear in validation. Every failed train case must have at least one tag.

The adequacy artifact is bound to the manifest and train score hashes. decide recomputes it instead of trusting the file.
