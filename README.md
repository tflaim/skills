# Skills

Composable skills for AI coding agents that I use daily. Each one solving specific friction points I kept hitting. Every skill is SKILL.md-format and runs on any agent that supports the standard: Claude Code, Codex, Cursor, and others. I also generalized them so it's easy to plug them into your workflow.

## Installation

### Plugin marketplace (Claude Code)

```
/plugin marketplace add tflaim/skills
```

### Manual install

Clone the whole collection:

```bash
git clone https://github.com/tflaim/skills.git ~/skills
```

Or copy a single skill into your agent's skills directory. For Claude Code this is typically `~/.claude/skills/`. Other agents may use a different location, check your agent's docs.

```bash
# Example: install just baton
cp -r skills/baton ~/.claude/skills/baton
```

## Security note

Skills are instructions to an AI agent that has tool access. A SKILL.md you install can shape what your agent reads, writes, executes, or fetches.

The skills here are the ones I use myself, but you should review the SKILL.md of anything you install before pointing your agent at it. This applies to skills in this repo and any third-party skills you find elsewhere.

## Skills

| Skill | What it does |
|-------|-------------|
| [animation-vocabulary](#the-design-engineering-suite) | Turn a vague description of a motion effect into its exact term |
| [apple-design](#the-design-engineering-suite) | Apple's fluid-interface and design principles, translated for the web |
| [baton](#baton) | Hand off a state-transfer document to a fresh agent session |
| [deslop](#deslop) | Strip AI writing patterns and inject human voice |
| [emil-design-eng](#the-design-engineering-suite) | Design-engineering craft: animation decisions, easing, springs, polish |
| [expert-review](#expert-review) | Invoke a domain expert persona for genuinely critical feedback |
| [explain-system](#explain-system) | Build mental models of technical systems you can reason with |
| [improve-animations](#the-design-engineering-suite) | Audit a codebase's motion, produce prioritized self-contained fix plans |
| [review-animations](#the-design-engineering-suite) | Strict craft-bar review of animation and motion code |
| [skill-grinder](#skill-grinder) | Autonomous prompt optimization via binary evals and mutation loops |
| [vet-idea](#vet-idea) | Stress-test ideas through rigorous questioning, produce execution-ready specs |

---

### The design engineering suite

Five skills recreated from [emilkowalski/skills](https://github.com/emilkowalski/skills) (MIT, © Emil Kowalski), distilling his [animations.dev](https://animations.dev/) design-engineering philosophy. Together they cover build, review, audit, naming, and the Apple motion canon:

- **emil-design-eng** — the main knowledge base: the animation decision framework (should it animate → purpose → easing → duration), strong custom curves, springs, press feedback, origin-aware popovers, clip-path techniques, gesture physics, GPU performance rules, and the Sonner component-building lessons. Invoke while building or polishing UI.
- **review-animations** — a strict reviewer for motion diffs. Ten non-negotiable standards, hard escalation triggers (`transition: all`, `ease-in` on UI, `scale(0)`, keyframes on rapidly-triggered elements), a remedial hierarchy that prefers deleting animation over decorating it, and a required Before/After/Why findings table ending in Block or Approve. Ships a STANDARDS.md with the exact curves, duration budgets, and spring configs to cite.
- **improve-animations** — the audit-then-plan advisor. Read-only recon of a codebase's motion surface, an eight-category audit (fan-out subagents on big repos), vetted findings ordered by leverage, then self-contained implementation plans under `plans/` that a zero-context executor can run. Ships AUDIT.md (the category playbook) and PLAN-TEMPLATE.md.
- **animation-vocabulary** — a reverse-lookup glossary: describe the effect ("the iOS rubber-band scroll"), get the term (*Rubber-banding*), so you can prompt AIs and brief designers with the right words.
- **apple-design** — Apple's WWDC design canon translated for the web: interruptible springs (damping/response values Apple actually ships), velocity handoff, momentum projection, rubber-banding, translucent materials, UI typography, and the eight design principles.

**When to use:**
- Building or polishing any UI with motion (`emil-design-eng`, `apple-design`)
- Reviewing an animation diff before merge (`review-animations`)
- "Make this app feel better" across a whole codebase (`improve-animations`)
- "What's it called when..." (`animation-vocabulary`)

---

### baton

Writes a state-transfer document so a fresh agent session can continue your work without recomputing what you already know. Use when context is bloating mid-task and you want a clean window without losing your place.

Produces a structured handoff with ten required sections: why the work matters, what "done" looks like, what's been tried and ruled out, where you're stuck (or the literal next action if not stuck), live artifacts, repo state, the exact first prompt to paste into the new session, tools the receiver will need, and context to load. Forces receiver-POV imperatives (no "I'll do X next") and concrete operational verbs (no "ship it" or "finish it").

**Target-aware.** If you pass `--target=codex` (or any other agent name), it adapts: agents with auto-loaded project memory get memory-file references; agents without get explicit Read instructions for each load-bearing file.

**When to use:**
- Context is bloating and you want a fresh session without losing state
- Handing off to a different agent (Claude Code to Codex, Codex to Cursor, etc.)
- Pausing for a meeting and resuming after with a different model

---

### deslop

Two jobs: remove AI-generated patterns, then add genuine voice. Stripping the robot is not enough if what's left is sterile.

Based on Wikipedia's [WikiProject AI Cleanup](https://en.wikipedia.org/wiki/Wikipedia:WikiProject_AI_Cleanup) research and the [humanizer](https://github.com/blader/humanizer) skill by blader (MIT). Adds register calibration (casual/professional/formal), voice injection, banned phrase tiers, and pattern 25 (negation-correction framing).

**25 patterns detected** across content, language, style, communication, filler, and hedging. Each pattern has a "words to watch" list and before/after examples in the included `patterns.md` reference.

**When to use:**
- Text reads like AI-generated output
- Editing AI-assisted drafts before publishing
- Someone flags "this sounds like AI"

**Example trigger:** Just ask your agent to "humanize this" or "deslop this text", or invoke directly with `/deslop`.

---

### explain-system

Builds mental models of technical systems through structured exploration. The kind you can take into a meeting and reason with, not skim and forget.

Starts by asking what's driving your curiosity (a meeting tomorrow vs deep architecture understanding). Explores the codebase or documentation, proposes a custom outline, then delivers an explanation with confidence signaling on every claim (verified, inferred, or uncertain).

**Includes:**
- Adaptive section library: analogy, architecture diagram (Mermaid), integration map, data flow, failure modes, key terminology
- Depth limits (3 hops, 8-10 files max) to prevent rabbit holes
- Comprehension check at the end to catch gaps
- Exportable artifacts (Mermaid diagrams render natively in most wikis, GitHub, GitLab, Notion)

**When to use:**
- Preparing for a technical discussion about an unfamiliar system
- Onboarding onto a new codebase
- Understanding how a service works before making product decisions

---

### expert-review

Steps into the role of a world-class domain expert to make your work better. The goal is excellence, and the expert holds you to that standard.

Three modes:
1. **User-specified:** "Review this as a senior platform engineer"
2. **Auto-select:** Analyzes context and picks the most impactful expert
3. **Multi-persona:** Panel of 2-3 experts when the work spans domains

Reviews hit these beats: gut reaction, what works, what does not (with consequences and alternatives), what is missing, and a verdict. Calibrates depth to the artifact stage (rough draft vs near-final spec vs production code).

**Sticky mode:** Ask the expert to stay active throughout the conversation. They will track whether previous feedback was addressed and escalate recurring issues.

---

### skill-grinder

Autonomous mutation loop that optimizes any existing skill's prompt. Adapted from Andrej Karpathy's [autoresearch methodology](https://www.youtube.com/watch?v=LBMiNFBp0cI) (autonomous experimentation loops applied to prompt engineering instead of ML training code).

The core loop: run a skill repeatedly with test inputs, score every output against binary evals, mutate one thing at a time, keep improvements, discard the rest. Stops when gains plateau or budget is hit.

**Key design decisions:**
- **At least one mechanical eval required** (grep, wc, parse, execute). LLM-only evaluation drifts toward reward hacking.
- **Holdout inputs** (2+ inputs never seen during optimization) detect overfitting at the end.
- **Exponential cooldown:** 3 consecutive discards = slow down, 5 = full stop with diagnosis.
- **Prompt growth tracking:** warns at 40%+ growth from baseline to prevent "lost in the middle" degradation.
- **Type A/B/C classification** for interactive skills: bypass the interview, grind the output quality.

**Output:** Improved SKILL.md + `results.tsv` score log + `changelog.md` research log of every mutation tried.

Includes `references/eval-guide.md` with examples of mechanical vs LLM-judged evals for text, visual, code, and document skills.

**When to use:**
- A skill works ~70% of the time and you want to close the gap
- You want to systematically identify which instructions are unclear or missing
- You want a research log that future sessions can continue from

**Not for:** Creating new skills (use skill-creator). One-off eval runs (use skill-creator). Purely interactive skills with no separable output (use expert-review + manual rewrite).

---

### vet-idea

Stress-tests an idea through targeted, challenging questions before producing a spec. Not brainstorming (divergent, "what should we build?"), but validation (convergent, "have I thought this through?"). Inspired by [Thariq's spec-based workflow](https://x.com/trq212/status/2005315279455142243).

Two modes: **Quick** (8-12 rounds, focused) and **Deep** (no cap, exhaustive). Every question includes a challenger option that pushes against the user's likely assumption. Checkpoint summaries every ~5 rounds keep the interview visible. Unresolved items get parked as Open Questions instead of forcing premature decisions.

**Output:** A `SPEC.md` with inline decision reasoning (not a separate decision log), execution guidance, and context file references. Designed to be handed to a fresh agent session for implementation.

**When to use:**
- You have an idea and want to find the holes before building
- Converting a rough concept into a spec another session can execute
- Validating scope and tradeoffs before committing to implementation

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT. The `deslop` skill carries its own MIT license with attribution to [blader/humanizer](https://github.com/blader/humanizer) for patterns 1-24. The design engineering suite (`emil-design-eng`, `review-animations`, `improve-animations`, `animation-vocabulary`, `apple-design`) is recreated from [emilkowalski/skills](https://github.com/emilkowalski/skills) (MIT, © Emil Kowalski).
