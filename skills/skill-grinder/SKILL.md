---
name: skill-grinder
description: >-
  Grind an existing skill through an autonomous mutation loop when repeated failures need broader
  search. Route pure generators to direct evaluation, artifact-producing workflows to stable-artifact
  evaluation, and purely interactive workflows to expert review.
disable-model-invocation: true
---
# Autoresearch for Skills

When an existing skill is inconsistent, run controlled experiments, score the outputs, and keep only changes supported by comparable evidence.

---

## the core job

Take any existing skill, define what "good output" looks like as binary yes/no checks (with at least one mechanically verifiable), then run an autonomous loop that:

1. Generates outputs from the skill using test inputs
2. Scores every output against the eval criteria
3. Mutates the skill prompt to fix failures
4. Keeps supported quality gains and quality-preserving compression, rejects regressions, and re-samples inconclusive results
5. Repeats until gains plateau or the budget is hit

**Output:** An improved SKILL.md + `results.tsv` + `pair-manifest.tsv` + `pair-ledger.tsv` + `changelog.md`.

Use the status vocabulary established by `skill-forge`: `Found`, `Accepted`, `Promoted`, `Compressed`, and `Rejected`. Add `INCONCLUSIVE` when measured scorer noise prevents a decision.

---

## before starting: gather context

Begin experiments only after every field below is confirmed with the user. Ask for missing fields first.

1. **Target skill:** Which skill do you want to optimize? Get the exact path to `SKILL.md`.
2. **Test inputs:** Read [references/eval-guide.md](references/eval-guide.md) before selecting inputs. Gather 5-7 optimization prompts, at least 2 visible validation inputs, and at least 2 locked tests whose bodies remain with a separate evaluator. The optimizer receives only opaque test IDs, commitments, and the isolation procedure. These sets have different jobs:
   - Optimization inputs drive failure analysis and mutation hypotheses.
   - Validation inputs run at baseline and for every mutation. They may gate candidate selection, so they are not evidence of unbiased generalization.
   - Locked test bodies, outputs, and per-eval grades stay outside the optimizer's context. A separate evaluator reveals and runs them only after candidate selection, comparing the original baseline with the selected final skill.
   - When no separate evaluator can enforce that information boundary, treat the affected inputs as validation and describe the result as validation rather than unbiased generalization.
   - The evaluator writes `locked-test-manifest.jsonl` with one `{"id":"opaque-id","commitment_sha256":"..."}` row per private test. The canonical private test object committed by that hash must include its ID, private input body, and exact applicable criterion IDs. Compute each commitment as SHA-256 over UTF-8 JSON serialized with sorted keys, `,` and `:` separators, and ASCII escaping. The optimizer receives this manifest, never the committed bodies or applicability mapping.
3. **Eval criteria:** Define 3-6 binary checks, including at least one mechanically verifiable check. Use the eval guide's template and examples; ask for a mechanical criterion when the proposed suite has none.
4. **Decision contract:** Before baseline execution, freeze `decision-contract.json` with integer `samples_per_input`; the exact public input definitions under `inputs`, each declaring its `optimization` or `validation` split; the complete rubric definitions under `criteria`, each declaring `type` as `MECHANICAL` or `LLM-JUDGED`, explicit `applicable_inputs`, its question, pass/fail conditions, applicability rule, and verification method; at least one `MECHANICAL` criterion; nonempty `optimization_gate`, `validation_gate`, and `noise_band_calculation` objects; a nonempty `mandatory_checks` list; finite nonnegative `material_regression_threshold`; integer `allowed_resample_count`; and a nonempty `disagreement_rule`. Canonicalize each input and criterion value as sorted-key compact ASCII JSON and record its SHA-256 in `pair-manifest.tsv`. Freeze the entire file in `decision-contract.sha256` before baseline and record that hash in the changelog. The validator derives the complete expected applicability matrix from this contract, so omitted inputs, samples, or applicable criteria fail. Changing an input, rubric, or other contract term requires a new uniquely identified run.
5. **Samples per input:** How many times should the skill run for each input in each experiment? **Default: 3 samples per input from baseline onward.** Do not substitute a fixed total run count. Repeated sampling is required to distinguish a mutation from ordinary model variation.
6. **Budget cap:** What is the maximum number of experiment cycles? Default: 12. The user can run another round later.
7. **Run root:** Where should evaluation artifacts be stored? Keep them outside the target skill unless the user explicitly requests otherwise.

**Cost estimate:** Before starting, surface this to the user:
> Planned pre-resampling target-skill invocations: `((optimization_inputs + validation_inputs) x samples_per_input x (1 + budget_cap)) + (locked_tests x samples_per_input x 2)`. The `1` is the baseline, every mutation runs on optimization and validation inputs, and locked tests run only after selection against the original baseline and selected final skill. With 5 optimization inputs, 2 validation inputs, 2 locked tests, 3 samples, and a budget of 12, the planned total is 285 invocations. Early stopping reduces the actual total. Noise re-sampling is additional. Default to at most one additional matched batch for the affected inputs per inconclusive experiment, include that allowance in the approval, and get renewed approval before exceeding it. Confirm the counts, allowance, and cost before starting.

The calibration outputs count toward the optimization baseline when the user confirms the rubric unchanged. If calibration changes an eval or rubric, discard those samples, rebuild the full baseline under the revised regime, and update the estimate with the additional calls.

---

## classifying interactive skills

Not every skill is a clean input/output function. Many skills are interactive (they ask questions, explore codebases, run multi-turn interviews). Before setting up test inputs and evals, classify the target skill:

**Type A: Pure generator.** Input goes in, output comes out. No interaction needed.
Examples: deslop (text in, rewrite out), code generators, formatters.
Approach: Standard grind loop. No adaptation needed.

**Type B: Interactive workflow with testable output.** The skill has an interactive phase (questions, exploration, scope negotiation) but produces a concrete artifact at the end (a spec, a review, an explanation, a memory entry).
Examples: vet-idea (interview then spec), expert-review (persona selection then review), explain-system (exploration then explanation), remember (scan then routing decisions).
Approach: **Bypass the interactive phase. Test the output generation.**
- For interview skills: provide pre-made context instead of running the interview. Use "just write the spec" or "skip questions" paths.
- For exploration skills: point at a known codebase and let it run the non-interactive path.
- For routing/analysis skills: fabricate synthetic inputs (conversation histories, artifacts to analyze) and score the analysis output.
- Evals target the *artifact quality*, not the interaction quality.

**Type C: Purely interactive.** The skill's entire value IS the interaction (a coaching conversation, a live debugging session). There is no separable output to score.
Approach: **Not grindable.** Route it to expert review and manual revision.

When gathering context, classify the target skill and tell the user:
> "This skill is [Type A/B/C]. [For Type B:] I'll test the [artifact name] output quality by bypassing the interactive parts. The [interactive phase] can't be grind-tested, but the [output phase] can."

---

## Read the skill

Before changing anything, read and understand the target skill completely.

1. Read the full SKILL.md file
2. Read any files in `references/` that the skill links to
3. Identify the skill's core job, process steps, and output format
4. Note any existing quality checks or anti-patterns already in the skill
5. **Record the baseline prompt length** (character count of SKILL.md). You will track growth.

This step is complete when the core job, process, output, checks, anti-patterns, linked material, and baseline length are all recorded.

---

## Build the eval suite

Read [references/eval-guide.md](references/eval-guide.md) before writing the structured test.

**Rules for good evals:**
- Use 3-6 binary evals with explicit applicability.
- Include at least one mechanical eval, including mechanical checks for the adversarial and minimal inputs.
- Make each criterion specific enough for consistent scoring and broad enough to resist gaming.

**Scoring uses anchored pair comparison.** Every LLM-judged eval must score the candidate sample alongside the same-input, same-index sample from the currently accepted skill version in the same scorer call, with labels hidden or randomized. The original baseline remains the reporting anchor. Independent absolute judgments can drift on borderline outputs.

**For axis-specific tests, use a narrow single-axis scorer.** When a mutation may affect one specific criterion, do not rely only on a broad multi-eval scorer. Other strengths can mask that regression. Run a separate scorer that asks one question about the affected axis.

**Max score calculation:**
```
max_score = sum(applicable_input_count_for_eval x samples_per_input for each eval)
```

Example: with 5 inputs, 3 samples, 3 general evals that apply to all inputs, 1 adversarial-only eval, and 1 minimal-only eval, the maximum is `(3 x 5 x 3) + (1 x 1 x 3) + (1 x 1 x 3) = 51`.

---

## Calibration run

**Before running the full loop, validate that your evals actually work.**

1. Generate one baseline sample for each of two different optimization inputs.
2. Score both outputs against every applicable eval.
3. Present the scores to the user with the actual outputs:
   > "Here's output A. I scored it: Eval 1 PASS, Eval 2 FAIL, Eval 3 PASS. Here's output B. I scored it: Eval 1 PASS, Eval 2 PASS, Eval 3 FAIL. Do these grades match your judgment?"
4. If the user disagrees with any score, revise the eval criteria before proceeding. The evals are broken, not the skill.
5. For MECHANICAL evals, show the command output so the user can verify the check works.
6. If the user confirms the rubric unchanged, reuse these outputs as their inputs' first baseline samples. If any eval or rubric changes, discard them and rebuild the entire baseline under the revised regime.

**Do not skip calibration.** Bad evals produce confident-looking improvements that are actually noise.

### Eval revision protocol

If calibration or early experiments reveal the evals are too easy or measuring the wrong thing, you may revise them. But you MUST:
1. Log the revision rationale in the changelog (why the old evals were insufficient)
2. Close the current run without deleting or replacing its manifest, commitment, ledger, or decision contract.
3. Create a fresh unique run directory, freeze the revised rubric, applicability manifest, and decision contract there, then re-run the full baseline. Mutation experiment numbering restarts at 1 in the new run.

Changing evals, applicability, or rubrics without re-baselining means you're comparing scores from two different tests.

### High-baseline fast path

If baseline is 90%+ with a narrow failure pattern (1-2 specific inputs failing on 1-2 specific evals), use the fast path after completing every baseline artifact and commitment below. Skip only repeated mutation cycles:
- Target the failure directly with one mutation
- If optimization reaches 100% and validation meets its gate, select the candidate and run the external locked-test evaluation
- If locked tests pass, stop. Don't burn experiments confirming what's already working.
- If the targeted mutation does not resolve the failure, restore the accepted version and stop the fast path. Reassess the remaining failures before asking whether a broader loop is justified. Do not consume the remaining budget automatically.

Report: "Baseline was [X]%. Single targeted fix resolved the remaining failure. Validation held and locked tests confirmed the selected candidate. No full loop needed."

### Calibrate the scorer rubric on baseline (not just the skill)

If baseline outputs demonstrate valid behavior but the scorer fails them, fix the rubric before changing the skill. Common rubric failures include treating an illustrative list as exhaustive, demanding behavior outside the stated criterion, or using fuzzy language that produces inconsistent judgments.

Inspect every unexpected baseline failure. If the rubric is wrong, revise it, document why, and re-score the entire baseline. Do not alter a rubric merely to erase a genuine skill failure.

### Handle scorer noise explicitly

Estimate scorer noise before deciding borderline experiments. Re-score a representative set of unchanged baseline pairs with randomized labels. Record the observed disagreement rate and predeclare how ties or inconsistent judgments will be handled.

If a candidate falls within the observed noise band:

1. Mark the result `INCONCLUSIVE` instead of accepting or rejecting it.
2. Re-run matched samples for the affected inputs and the narrowest relevant scorer. Within each batch, include every frozen sample index for each affected input and criterion; the validator rejects partial batches.
   Append every repeated verdict to `resample-ledger.tsv` under the current experiment and a positive `resample_batch`; never replace the initial pair-ledger row.
3. Accept or reject a quality mutation only when repeated evidence outside the measured noise satisfies the decision rule. A shorter candidate may be Compressed when repeated matched comparisons consistently show no material regression, even if no quality difference can be resolved. One directional judgment after re-sampling is insufficient.
4. Stop when repeated experiments remain indistinguishable. Restore the accepted version unless the candidate independently qualifies as a quality-preserving compression win. A no-change outcome is valid.

---

## Establish baseline

Run the skill AS-IS before changing anything. This is experiment #0.

1. Create a new `[run_root]/skill-grinder-runs/[skill-name]-[MM-DD-YYYY-HHMMSS]-[run-id]/` outside the target skill. Fail if the resolved directory already exists; never reuse or overwrite a prior run.
2. Create `results.tsv` with the header row.
3. Back up the original SKILL.md as `SKILL.md.baseline`
4. Save the approved `decision-contract.json`, its SHA-256, and the body-free `locked-test-manifest.jsonl` from the external evaluator.
5. Create `pair-manifest.tsv` from the frozen applicability matrix. Include one row for every optimization or validation input, sample index, and applicable criterion that each mutation must compare, including the canonical input and criterion hashes from the decision contract. Before running the baseline, commit both artifacts with `python3 <skill-directory>/scripts/validate_pair_ledger.py --manifest pair-manifest.tsv --manifest-commitment pair-manifest.sha256 --decision-contract decision-contract.json --decision-contract-commitment decision-contract.sha256 --commit-manifest`. Changing either artifact after this commitment requires a fresh run directory.
6. Create cumulative `pair-ledger.tsv` and `resample-ledger.tsv` with only their headers. Candidate comparison rows go in the pair ledger; repeated noise-adjudication rows go in the resample ledger. Every experiment requires the frozen `pair-manifest.sha256` commitment and verifies the input and rubric commitments against `decision-contract.json`.
7. Run the skill `samples_per_input` times for every optimization and validation input.
8. Score every output against every applicable eval. For MECHANICAL evals, run the verification command. For LLM-JUDGED evals, use deterministic or low-variance settings when the runtime supports them, and apply the rubric consistently.
9. Record optimization and validation baseline scores separately.
10. Do not reveal or run locked tests in the optimizer context. Record the manifest hash and isolation mechanism for the external final evaluator.

**results.tsv format (tab-separated):**

```
experiment	optimization_score	optimization_max	validation_score	validation_max	status	description	prompt_length	locked_test_result
0	78	90	26	30	baseline	original skill, no changes	4523	pending
```

Use these exact pair files:

```text
pair-manifest.tsv:
split	input_id	input_sha256	sample	criterion	criterion_sha256

pair-ledger.tsv:
experiment	split	input_id	input_sha256	sample	criterion	criterion_sha256	verdict	evidence

resample-ledger.tsv:
experiment	resample_batch	split	input_id	input_sha256	sample	criterion	criterion_sha256	verdict	evidence
```

Use `optimization` or `validation` for `split`, positive integers for `sample`, and `SAME`, `BETTER`, or `WORSE` for `verdict`. Keep evidence short and specific to that pair and criterion. The manifest is frozen with the rubric; changing either requires a fresh run directory and full baseline.

**After establishing baseline, confirm the score with the user before proceeding.** If baseline is already 90%+, the skill may not need optimization. Ask the user if they want to continue.

---

## Experiment loop

This is the core autoresearch loop. Runs autonomously within the budget cap.

**LOOP:**

1. **Analyze failures.** Look at which evals are failing most. Read the actual outputs that failed. Identify the pattern. Is it a formatting issue? A missing instruction? An ambiguous directive?

2. **Form a hypothesis.** Pick ONE thing to change. Don't change multiple things at once.

   Prefer mutations that state the target behavior:
   - Add a specific instruction that addresses the most common failure
   - Reword an ambiguous instruction to be more explicit
   - Replace a recurring failure with a positive instruction for the desired behavior
   - Move a buried instruction higher in the skill (priority = position)
   - Add or improve an example that shows the correct behavior
   - **Remove** an instruction that's causing over-optimization for one eval at the expense of others
   - **Simplify** a verbose section. Shorter prompts that maintain the score are a win.

   The hypothesis is ready when it names one behavior, one targeted edit, and the failing evidence that edit should change.

3. **Make the change.** Edit SKILL.md with ONE targeted mutation.

4. **Check prompt growth.** If SKILL.md is now >40% longer than baseline, flag it:
   > "Warning: skill has grown [X]% from baseline ([baseline_chars] -> [current_chars] chars). Prompt growth increases complexity and can obscure earlier instructions. Consider simplifying or consolidating instructions before adding more."

5. **Run the experiment.** Execute the skill `samples_per_input` times for every optimization and validation input. Keep their scores separate.

6. **Score it.** Run every output through every applicable eval. For MECHANICAL evals, execute the verification commands. For LLM-JUDGED evals, evaluate strictly.

7. **Write and validate the pair ledger.** Append one row to cumulative `pair-ledger.tsv` for every manifest row, using the current experiment number. Resolve `<skill-directory>` to the directory containing this `SKILL.md`, then validate exact coverage for the current and all earlier experiments, unique normalized keys, allowed verdicts, and nonempty evidence:

   ```bash
   python3 <skill-directory>/scripts/validate_pair_ledger.py \
     --manifest pair-manifest.tsv \
     --manifest-commitment pair-manifest.sha256 \
     --decision-contract decision-contract.json \
     --decision-contract-commitment decision-contract.sha256 \
     --ledger pair-ledger.tsv \
     --resample-ledger resample-ledger.tsv \
     --experiment [N]
   ```

   The helper returns `EVIDENCE_VALID`, initial and resample row counts, resample batches, verdict counts, the frozen resample cap, and contract, manifest, and ledger hashes. This status proves structural integrity and frozen input/rubric identity. It does not mean the candidate satisfied the decision gates. Apply the frozen gates in the next step. Do not decide from prose summaries or structurally invalid evidence. Correct ledger rows from the existing scored evidence and rerun the helper; do not rerun target samples merely to repair the research record.

8. **Decide: accept, compress, reject, or mark inconclusive.** Read the validated rows for the current experiment and compare anchored candidate pairs against the accepted skill version.
   - For quality mutations: **Accepted** only if at least one optimization pair is better, no optimization or validation pair is materially worse, mechanical checks pass, and both sets meet their predeclared gates. A train-only improvement is **Found** and does not replace the accepted version.
   - For compression mutations: **Compressed** when no optimization or validation pair is materially worse, mechanical checks pass, and the prompt is smaller.
   - **Rejected** when a pair is materially worse or a mandatory check fails. During active noise adjudication, require a reproducible material regression outside the measured noise, not one adverse pair verdict. Restore the accepted skill version.
   - **INCONCLUSIVE** when the result falls within measured scorer noise. Re-sample before deciding.

   Before rejecting a useful but verbose rule, test a shorter positive instruction for the desired behavior and validate that exact axis with a narrow scorer.

9. **Log the result** in results.tsv and changelog.md.

10. **Check stop conditions** (see below). If none triggered, continue to next experiment.

**STOP CONDITIONS (check after every experiment):**

| Condition | Action |
|-----------|--------|
| Budget cap reached | Stop. Proceed to final evaluation. |
| 95%+ pass rate for 3 consecutive experiments | Stop. Diminishing returns. |
| 5 consecutive Rejected mutations | Stop. Report: "5 consecutive mutations failed to improve the score. Remaining failures may need structural changes to the skill, not prompt tweaks. Review the changelog and consider a different approach." |
| 3 consecutive Rejected mutations | Double the analysis time before the next mutation. Re-read all failing outputs from scratch and choose a different improvement axis. |
| Score crosses 85% | Notify: "Score crossed 85%. Remaining gains will be harder. Each percent from here costs more experiments. [X] experiments remain in budget." |

**If you run out of ideas before hitting a stop condition:** Re-read the failing outputs. Derive one new hypothesis from prior near misses, but change only one behavior in the next experiment. Try removing things instead of adding them. Try a completely different approach to the same problem.

---

## Write the changelog

After each mutation experiment, append its status to `changelog.md`. Record the baseline in `results.tsv` and `SKILL.md.baseline`; begin mutation changelog sections at Experiment 1.

```markdown
## Experiment [N]: [Found/Accepted/Compressed/Rejected/INCONCLUSIVE]

**Score:** [X]/[max] ([percent]%)
**Prompt length:** [chars] ([+/-]% from baseline)
**Change:** [One sentence describing what was changed]
**Reasoning:** [Why this change was expected to help]
**Result:** [What actually happened, including which evals improved or declined]
**Decision evidence:** [Matched-pair verdicts, mechanical results, scorer-control outcome, and any noise handling]
**Pair evidence:** [`pair-ledger.tsv` and `resample-ledger.tsv`, experiment, validated row counts, resample batches, decision-contract hash, manifest hash, ledger hashes, and EVIDENCE_VALID]
**Failing outputs:** [Brief description of what still fails, if anything]
```

This changelog is the most valuable artifact. It's a research log that any future agent (or smarter model) can pick up and continue from.

---

## Final locked-test evaluation

When the loop stops (any stop condition), run the final validation:

1. Hand the original baseline, selected final skill, and frozen `locked-test-manifest.jsonl` to the external evaluator. Do not pass mutation history or candidate labels when they are unnecessary.
2. Reveal each private test only inside that evaluator. Before execution, recompute its canonical JSON commitment and require an exact match with the manifest. Any mismatch invalidates the locked test.
3. Run both skill versions `samples_per_input` times on every verified locked test. Score every applicable eval and check mandatory failures and each narrow measured axis before considering the aggregate. Return only `PASS` or `FAIL`, baseline and final totals, failed axis names, and the verified locked-test manifest SHA-256. Keep locked bodies, outputs, and per-test evidence outside the optimizer context.
4. Pass only when the final has no mandatory failure, no reproducible material regression on any measured axis, and the aggregate holds or improves. A higher or tied total cannot offset an axis regression. On `PASS`, mark a quality candidate `Promoted`; a compression candidate remains `Compressed`. Report the supporting generalization evidence.
5. On `FAIL`, leave a quality candidate `Accepted` but not `Promoted`; reject a compression candidate that regresses. Test no archived candidate against the same locked set, because that would turn the test into validation. A new selection attempt requires a fresh locked set.
6. If isolation was not technically enforced, label the result validation only and do not claim unbiased generalization.

---

## Deliver results

Present to the user:

1. **Score summary:** Baseline score -> Final score (percent improvement)
2. **Validation check:** Baseline validation -> Final validation
3. **Locked-test check:** PASS or FAIL, verified manifest SHA-256, baseline -> final totals, and any failed axis names, or an explicit statement that isolation was unavailable and no unbiased generalization claim is made
4. **Total experiments run:** How many mutations were tried
5. **Experiment outcomes:** How many mutations were Found, Accepted, Promoted, Compressed, Rejected, or INCONCLUSIVE
6. **Prompt growth:** Baseline length -> Final length (percent change)
7. **Top 3 changes that helped most** (from the changelog)
8. **Remaining failure patterns** (what the skill still gets wrong, if anything)
9. **The improved SKILL.md** (already saved in place)
10. **Location of results.tsv and changelog.md** for reference

If the skill plateaued below 90%, note: "Further improvement likely requires structural changes to the skill's approach, not more prompt tweaks. Consider whether the skill's methodology is right for the job."

### Self-audit before declaring done

This is a long autonomous process, so drift is a risk. Before adoption, verify:

1. Calibration was run and the user confirmed score-judgment agreement on baseline outputs
2. At least one MECHANICAL eval was used (not all LLM-judged)
3. Validation score was checked for every mutation and did not regress for the selected final skill
4. Prompt growth (or shrinkage) is documented in the final report
5. Changelog has one section per mutation experiment, records every encountered status, and records the pair-ledger validator `EVIDENCE_VALID` status and hashes
6. If baseline was 90%+, the fast path was used, or the report explains why a full loop was still necessary
7. Borderline comparisons were preserved in the resample ledger and handled with the frozen noise protocol, not an improvised tolerance
8. Locked tests were technically isolated until selection and verified against the frozen manifest, or the report avoids an unbiased generalization claim
9. Locked-test passage was gated on every mandatory and narrow measured axis, not only the aggregate score
10. Pair-ledger validation returns `EVIDENCE_VALID` for the final experiment, which rechecks every cumulative experiment. The final decision separately satisfies the frozen gates.

---

## output format

Produce every artifact and schema defined in **Establish baseline**, plus the improved `SKILL.md`, in the unique run directory. After locked evaluation, bind the baseline and selected candidate results to the final status without reducing the decision to one aggregate score.

---

## Compression hypotheses

Treat every proposed cut as a hypothesis, never as a safe list. Good first candidates are duplicated instructions, prose that merely restates a nearby rule, and formatting prescriptions that do not affect the skill's core output. Commonly load-bearing candidates include worked examples, anti-hallucination rules, core behavioral principles, and named structural beats. Test each affected axis before adopting the cut.
