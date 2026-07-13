# Acceptance policy

Use the narrowest claim supported by the evidence.

| Evidence | Quality mode | Compression mode | Exploratory mode |
| --- | --- | --- | --- |
| Train improves only | Found | Found | Found |
| Validation ties | Found when train improved | Compressed only if prompt shrank | Found |
| Validation strictly improves | Accepted | Accepted if prompt did not shrink | Found |
| Accepted quality candidate passes locked test | Promoted | n/a | n/a |
| Locked test regresses | Remains Accepted, with risk | Rejected | n/a |
| Validation has candidate mandatory failures | Rejected | Rejected | Rejected |
| Locked test has candidate mandatory failures | Remains Accepted, with risk | Rejected | n/a |

## Promotion boundary

Validation and locked test must use frozen, non-overlapping cases. Do not inspect or tune against locked-test content before validation accepts the exact candidate.

Do not claim promotion when test evidence is missing, denominators differ, mandatory failures remain, or the evaluation mechanism changed between baseline and candidate.

## Compression boundary

Compression is its own claim. A shorter prompt that improves validation is still reported as Compressed when the run mode is compression. Do not convert a compression run into a general quality claim after seeing results.

## Reporting

Report the selected mode, split counts, observed failure tags, validation coverage, exact candidate diff, score deltas, prompt-size delta, mandatory failures, final status, and residual risks.
