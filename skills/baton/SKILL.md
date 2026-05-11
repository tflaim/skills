---
name: baton
description: Pass the baton to a fresh session of any AI coding agent (Claude Code, Codex, Cursor, Aider, Cline, etc.). Writes a state-transfer doc the next agent can act on without recomputing. Use when context is bloating mid-task and you want a clean window without losing your place. Triggers - "/baton", "pass the baton", "hand this off", "start fresh on this", "fresh session for this".
argument-hint: "[--target=<agent-name>] <what the next session will focus on>"
---

You are writing a **state-transfer document**, not a conversation summary. The receiver needs to *act*, not reconstruct what happened.

## Path

Save to `~/handoffs/YYYY-MM-DD-HHMM-<slug>.md` (use the user's preferred time zone for the timestamp; default to local time if unspecified).

- `<slug>` = short kebab-case derived from the focus argument (e.g. `auth-refactor-resume`, `payments-bug-followup`, `rate-limiter-investigation`).
- `mkdir -p` the parent if needed.
- New files do not require a Read before Write — use Write directly.
- **Decide the full absolute path FIRST, before drafting the doc.** Section 8 must embed this exact path as a literal string. Do not draft with placeholders like "this file" or `<path>` — substitute the real path.

## Target

If the user names a target agent (e.g. `--target=codex` or "for Cursor"), tailor the doc to what that agent supports. Two axes that matter most:

- **Auto-loaded context.** Some agents auto-load project memory or system prompts at session start; others don't. If the receiver has auto-memory, you can reference memory files by path and skip restating their content. If not, link or inline anything load-bearing — assume nothing auto-loads.
- **Skills / slash commands.** Some agents expose registered skills or slash commands; others only have generic tools (bash, file edit, etc.). For agents with skills, you may reference them by name. For agents without, write plain step-by-step procedures the receiver can execute with their default toolset.

If no target is specified, write tool-agnostic: imperative steps, absolute paths, explicit instructions. The receiver adapts.

## Required sections

Hit every section. If a section truly doesn't apply, write `n/a` — do not omit the heading.

1. **Header** — `Written:` timestamp, `Target:` agent name (or `any`), `Repo:` + branch if in a git repo
2. **Why this matters** — current stakes in 1-3 lines (not project background — current motivation)
3. **What "done" looks like** — concrete success criteria the receiver can verify against
4. **What's been tried (and ruled out)** — prevents the next agent from re-deriving rejected approaches
5. **Where we're stuck / next concrete step** — the literal next action *the receiver* will take, written as an imperative ("Restore the stashed config and re-run the dev server", "Resolve the conflict between line 230 and line 480 by deciding which is canonical"). The action belongs to the receiver, not to you. **Banned phrasings:** "I'll", "I'm stuck on", "we'll", "wait for review", "once X is done I'll Y". If you're not stuck, say what the receiver should do first, not what you were about to do.
6. **Live artifacts** — paths/URLs to PRs, plans, specs, dashboards, tickets. Reference, don't duplicate.
7. **Repo state at handoff** — output of `git status --short`, current branch, last commit SHA + subject. Skip if not in a repo.
8. **First prompt to paste** — the literal sentence the user pastes into the new session. This is the single highest-leverage line in the document. **MUST include all three:**
   - (a) The absolute path of this baton file, substituted in as a literal string. Never write "this file" or `<path>` placeholders.
   - (b) A concrete receiver-action verb tied to the success criteria in section 3. Banned vague verbs: "ship it", "finish it", "close the loop", "look right and ship", "fix the X", "wrap it up". Replace with operational verbs: "rebase PR #1234 onto main, push, and request re-review from @reviewer," "run the test suite for the affected module and confirm pass."
   - (c) An explicit Read instruction for any file the receiver must consult before acting (the baton itself plus any spec/source file that's load-bearing for the action).
9. **Tools the receiver will need** — target-aware. For agents with skills/slash commands: list relevant skill names. For agents without: list the underlying commands (`git`, `gh`, test runner, build command, etc.) so the receiver can execute them with generic tools.
10. **Context the receiver should load** — files the receiver should Read before acting. If the target agent auto-loads project memory, list ONLY load-bearing memory files (adjacent or merely-topical files create noise — skip them). If the target agent has no auto-memory, list every load-bearing file explicitly so the receiver knows to Read each one.

## Don'ts

- Don't recap the conversation chronologically.
- Don't duplicate PRDs, plans, ADRs, commit messages, or diffs. Link them by path or URL.
- Don't assume the receiver has the same toolset, environment, or memory as you. If the doc references a command, make sure the receiver can run it; if it references a file, make sure the receiver knows the path.
- Don't write silently. See the confirmation gate below.

## Confirm before writing

Show the full doc to the user before saving. Wait for approval, then Write. Never save on first draft. If the user requests changes, revise and re-show.

## After writing

Print two things, in this order, so the user can copy directly:

1. The absolute path of the baton file
2. The literal "First prompt to paste" block (section 8)
