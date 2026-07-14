# Skills

[![skills.sh](https://skills.sh/b/tflaim/skills)](https://skills.sh/tflaim/skills)

Composable skills for AI coding agents, built from friction I kept hitting in real work. I use them daily, then sand off the project-specific edges so they can travel across Claude Code, Codex, Cursor, and other runtimes that support the Agent Skills `SKILL.md` format.

## Installation

Install the whole collection with the [skills CLI](https://www.skills.sh/docs/cli):

```bash
npx skills@latest add tflaim/skills
```

Install one skill:

```bash
npx skills@latest add tflaim/skills --skill baton
```

Install globally instead of in the current project:

```bash
npx skills@latest add tflaim/skills -g
```

The skills CLI collects anonymous installation telemetry by default. To opt out:

```bash
DISABLE_TELEMETRY=1 npx skills@latest add tflaim/skills
```

## At a glance

| Skill | What it does |
| --- | --- |
| [baton](#baton) | Hands live work to a fresh agent session without losing state |
| [deslop](#deslop) | Strips AI writing patterns and restores an appropriate human voice |
| [expert-review](#expert-review) | Brings in the expert most likely to catch consequential mistakes |
| [explain-system](#explain-system) | Builds a verified mental model of a technical system |
| [pr-preflight](#pr-preflight) | Checks repository readiness before work leaves the machine |
| [pr-review-feedback](#pr-review-feedback) | Verifies reviewer claims before changing code or replying |
| [skill-forge](#skill-forge) | Searches for skill improvements and gates promotion on held-out evidence |
| [skill-grinder](#skill-grinder) | Runs controlled prompt mutations with anchored evaluation |
| [vet-idea](#vet-idea) | Stress-tests a direction and captures the decisions in a spec |

## Skills

### baton

Writes a state-transfer document so a fresh agent can continue the work without reconstructing the conversation. It captures what matters, what has already been tried, the live repository state, the next concrete action, and the exact first prompt to paste into the new session.

**Target-aware.** Name the receiving agent and Baton adapts the handoff to its tools, skills, and auto-loaded context. It shows you the complete draft before writing anything.

**When to use:**

- Context is bloating and you want a clean session without losing your place
- You are handing work from one agent or runtime to another
- You are pausing mid-task and need a reliable restart point

---

### deslop

Two jobs: remove AI-generated patterns, then restore a voice that fits the audience. Stripping the robot is not enough if what remains is sterile.

Deslop calibrates casual, professional, and formal registers; respects project style rules; preserves facts and quotations; and catches 25 recurring patterns. Its detailed reference includes words to watch and before-and-after examples.

**When to use:**

- A draft sounds generated even though the facts are right
- You are editing AI-assisted copy before publishing it
- Someone says, "This sounds like AI"

**Example trigger:** Ask your agent to "humanize this" or "deslop this text."

---

### expert-review

Steps into the role of the expert most likely to make the work better. You can name the persona, let the skill choose one from context, or use a small panel when the artifact genuinely spans distinct domains.

The reviewer grounds itself in the artifact and its source system before judging. It challenges assumptions, traces affected stakeholders, separates verified behavior from risk, and closes every criticism with a concrete recommendation.

**When to use:**

- You need a critical second opinion on a spec, plan, prompt, or implementation
- The artifact crosses domains and one reviewer would miss important tradeoffs
- You want feedback that ends in specific changes instead of vague concerns

---

### explain-system

Builds the kind of mental model you can take into a meeting and reason with, rather than a file inventory you will forget. It starts with what you need to understand, follows a real entry path, and marks each important claim as verified, inferred, or uncertain.

**Includes:**

- An adaptive outline shaped around the system and your goal
- Bounded exploration that avoids wandering through the entire codebase
- Diagrams, integration maps, and data flows when they make the system easier to reason about
- A comprehension check that exposes gaps before the explanation is finished

**When to use:**

- You are preparing for a technical discussion about an unfamiliar system
- You are onboarding to a codebase or service
- You need to understand failure modes before making a product or engineering decision

---

### pr-preflight

Runs the final readiness check before a commit, push, or pull request leaves the machine. It compares the branch with current remote truth, inspects staged and unstaged intent, reads repository conventions, reviews the actual diff, and runs targeted deterministic checks.

Preflight preserves unrelated local work and blocks the requested Git or GitHub action when material concerns remain. It derives branch, ticket, and validation expectations from the repository instead of imposing one global workflow.

**When to use:**

- You are about to commit or push a meaningful change
- You want to open a pull request without leaking unrelated files
- A branch has been sitting long enough that its base or checks may be stale

---

### pr-review-feedback

Treats reviewer feedback as a set of claims to verify, not a list of instructions to obey. It checks every material comment against the current branch and PR diff, then classifies it as valid, partially valid, not valid, duplicate, or out of scope.

Accepted issues are fixed and tested. Declined issues get a concrete reason. PR mutations require explicit authorization, so a read-only review ends with exact response drafts rather than quietly changing code or posting comments.

**When to use:**

- A human or automated reviewer leaves actionable PR feedback
- You suspect a comment is stale, duplicated, or based on the wrong execution path
- You need to explain clearly why feedback was accepted, declined, or deferred

---

### skill-forge

Searches for a useful skill edit, then makes it earn promotion. Fast train experiments can find a candidate, but only held-out validation can mark it accepted, and only a locked test can promote it.

Skill Forge keeps quality work, compression work, and exploratory findings separate. Its bundled standard-library helper freezes the evidence contract, checks ledger coverage, and rejects incomparable results.

```bash
python3 skills/skill-forge/scripts/skill_forge.py init-run ...
python3 skills/skill-forge/scripts/skill_forge.py apply-edits ...
python3 skills/skill-forge/scripts/skill_forge.py check-validation ...
python3 skills/skill-forge/scripts/skill_forge.py decide ...
```

**When to use:**

- You have a known skill failure and want to test a surgical fix quickly
- You need held-out evidence before keeping a prompt change
- You want to shrink a skill without quietly trading away behavior

---

### skill-grinder

Runs a controlled mutation loop against an existing skill. Baseline and candidate outputs are sampled on the same inputs, scored against the same criteria, and recorded in a validated pair ledger. One mutation changes at a time, and unsupported changes are discarded.

The loop handles noisy judgments with matched resampling, gives narrow changes focused regression checks, and keeps compression wins separate from quality claims. Interactive skills are evaluated through stable artifacts instead of pretending every workflow is a simple input-output function.

Adapted from Andrej Karpathy's [autoresearch methodology](https://www.youtube.com/watch?v=LBMiNFBp0cI), applying autonomous experimentation loops to prompt engineering.

**Output:** An improved `SKILL.md`, a frozen pair manifest, a validated pair ledger, `results.tsv`, and a changelog in an auditable run directory outside the target skill.

**When to use:**

- An existing skill has repeated failures that need more than one targeted edit
- You want a mutation history another session can audit and continue
- You need comparable train, validation, and locked-test evidence before promotion

Use Skill Forge for a fast, bounded search. Use Skill Grinder when you need a broader autonomous loop.

---

### vet-idea

Stress-tests a direction through one challenging question at a time. It inspects the available context first, offers a genuine challenger option, and records why decisions were made instead of sanding away disagreement.

Choose a focused Quick interview or an exhaustive Deep one. Checkpoint summaries keep the reasoning visible, and unresolved issues remain open instead of being turned into invented requirements.

**Output:** A focused spec with requirements, decision reasoning, open questions, execution guidance, and context files.

**When to use:**

- You have a direction and want to find the holes before building it
- You need to turn a rough idea into a spec another session can execute
- You want to test scope and tradeoffs before committing to implementation

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT. The `deslop` skill retains its attributed MIT license.
