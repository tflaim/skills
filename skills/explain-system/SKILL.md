---
name: explain-system
description: >-
  Explain a code or non-code technical system by building a verified mental model. Adapt exploration
  and output for small targets, large multi-subsystem targets, and the user's decision or discussion goal.
---
# Explain System

Build mental models of technical systems you can reason with. Not summaries. Understanding that lets you make product decisions, ask smart questions, and communicate accurately with engineers.

## Done State

The explanation is complete when:

- it addresses the user's stated motivation and negotiated scope
- the critical control or information flow has been verified against source
- verified, inferred, and uncertain claims are visibly distinguished
- every approved outline section is delivered and every domain term is defined at first use
- verified code claims cite `filename.ext:lineN`, and diagrams match components actually inspected
- unexplored boundaries and unresolved uncertainty are explicit
- one comprehension scenario has been offered, with any response corrected or confirmed

## Phase 1: Context Gathering

Before exploring, ask two questions and wait for answers:

1. **"What's driving your curiosity about this?"**
   - "Meeting about this tomorrow" vs "deep architecture understanding" produces very different outputs
   - This determines which sections to expand and which to keep brief

2. **"Are there other artifacts I should look at?"** (if only codebase provided)
   - Team documentation (Confluence, Notion, Google Docs, etc.), ticket tracker epics (Jira, Linear, GitHub Issues, etc.), architecture diagrams, READMEs, team-chat threads?

**If the user skips these questions** (e.g., "just explain it"): assume a general architecture overview at medium depth. Note this assumption in the outline proposal so the user can course-correct.

### Scope Negotiation

After initial exploration (Phase 2), if the target is large (3+ major subsystems, multiple services, or spans multiple repos), negotiate scope before continuing:

> "This system has [N] major subsystems: [list]. I can give you an overview of all of them, or go deep on one or two. What's most useful given [their stated motivation]?"

Never produce a 3000-token explanation when the user only needed one subsystem.

### Non-Code Targets

If the target is a concept, process, or documentation rather than a specific codebase:
- **Concept** ("how do we handle agent handoffs"): check team documentation, agent memory files, and the ticket tracker first. Skip the file exploration checklist. Map the concept through documentation and conversation.
- **Documentation URL or ticket epic**: use the relevant MCP tool for that platform (Atlassian, Notion, GitHub, etc.) or fall back to a web-fetch tool to retrieve the content, then apply the same analysis framework.
- **Multi-repo system**: identify all repos in Phase 1, explore one at a time, connect them in the Integration Map.

For non-code targets, adapt downstream phases: depth limits don't apply (there are no import chains), complexity assessment maps to breadth of documentation, and confidence signaling shifts from file:line references to source attribution ("per the design doc at <link>" / "based on the ticket description" / "inferred, not documented anywhere I found").

## Phase 2: Exploration

### Check Existing Knowledge First

Before exploring from scratch, check:
- Project memory files and the agent-instructions file (CLAUDE.md, AGENTS.md, GEMINI.md, or equivalent) for prior briefs
- Any prior exploration notes or briefs already captured for this system
- Earlier context in the current conversation

Only explore what you don't already know.

### Exploration Strategy

You are building a mental model you can reason with, not cataloguing files. Explore only what sharpens that model. Explore directly by default. Delegate independent exploration only when the user or local instructions authorize it and it materially improves the answer. Prioritize in this order:

1. **Entry points first**: main, index, router, handler, app files
2. **Follow the request path**: trace a single request through the system end-to-end
3. **Map integration boundaries**: env vars, external imports, API clients, config files
4. **Read error handling only if integration complexity is high**

```
Exploration checklist:
[] Entry points (index, main, router, handler, app)
[] Trace one request path end-to-end
[] External dependencies (imports from outside the system, env vars, API clients)
[] Config and schema files
[] Error handling patterns (only if failure modes are relevant to user's goal)
```

### Depth Limits

- **Stop at 3 hops of import chains** from the entry point unless the user asked for more (barrel/index re-exports don't count as a hop)
- **Read no more than 8-10 files in full**. Stop when your mental model can predict what the next file holds, not when you run out of files. If you can't determine the architecture from 8-10 files, say so and ask the user which component to focus on
- **Note what you didn't explore** and why. Don't pretend you read everything

### Complexity Assessment

After exploration, internally classify:
- **Trivial** (single file or under ~200 lines): skip outline negotiation and section-library formats. Deliver a brief inline explanation covering purpose, inputs/outputs, and key decisions, then offer the comprehension check.
- **Simple** (single service, clear request path, few integrations): skip Integration Map, brief Failure Modes
- **Medium** (multiple components, some external deps): standard treatment
- **Complex** (distributed, many integrations, heavy error handling): expand Integration Map and Failure Modes, add Data Flow

## Phase 3: Verification & Adaptive Outline

### Self-Verification (Do Not Skip)

Before generating any explanation, re-read the 2-3 most critical files and confirm:
- Does your mental model match the actual control flow?
- Are there components you assumed a role for but didn't verify?
- If uncertain about any component's role, **flag it explicitly** rather than guessing

> Example: "I'm fairly confident the routing layer delegates to handlers based on the path matcher in `router.ts:42`, but I didn't find where fallback routing is configured. Worth confirming with the team."

### Propose an Adaptive Outline

Based on what you found, propose a custom outline. Select from this index:

| Section | Select when |
| --- | --- |
| Analogy | A familiar comparison would anchor an unfamiliar system |
| Architecture Overview | Multiple components or boundaries shape the mental model |
| Integration Map | The system has 2+ external dependencies or failure impact matters |
| Data Flow | The request path is non-obvious or contains critical decisions |
| Failure Modes & Edge Cases | Operational risk or complex error handling matters |
| Key Terminology | Domain language will recur in the user's work or discussion |
| Configuration & Environment | Flags or environment materially change behavior |
| Questions to Ask the Team | Source gaps or operational decisions need human answers |

Use only sections that advance this user's goal.

```markdown
## Proposed Outline

Based on what I found, here's what I'd cover:

1. The Analogy
2. Architecture Overview (Mermaid diagram)
3. [Section selected based on complexity]
4. [Section selected based on user's goal]
5. Questions to Ask the Team

Want me to adjust this before I dive in?
```

Wait for confirmation or adjustment before proceeding.

## Phase 4: Explanation

Every section should hand the user a piece of a mental model they can reason with, not a summary they have to memorize. Deliver the sections from the approved outline. For outlines with 4+ sections, offer one natural pause at a logical midpoint (e.g., after architecture + data flow, before failure modes + questions). Don't pause after every section since the user already approved the outline.

Before writing the approved sections, read [references/section-library.md](references/section-library.md) for their formats and constraints.

### Confidence Signaling

Throughout the explanation, distinguish between:
- **Verified**: "Based on `handler.ts:15`, requests route through..."
- **Inferred**: "Based on the import pattern, this likely..."
- **Uncertain**: "I didn't find explicit configuration for this. Worth asking the team."

Keep those confidence levels visible throughout. Define domain terms inline where they first matter.

---

## Phase 5: Comprehension Check

After delivering the explanation, proactively offer one scenario question. Extended active learning starts only when the user requests it:

> "Quick check to make sure my explanation landed: if [specific failure condition from this system], what would happen to [user-facing behavior]?"

If the user engages, identify the gap or confirm the model:
> "You've got [X] solid. The gap I'd focus on is [Y] because [why it matters for their role]."

Stop after this response unless the user asks for active learning. When they ask to be quizzed or tested, continue with this loop:

1. **Teach-Back**: "In one sentence, explain what happens when [scenario]."
2. **Scenario**: "If [failure condition], what would happen to [user-facing behavior]?"
3. **Connection**: "How does this relate to [system they know]?"
4. **Gap ID**: Name the next concept to revisit and why.

End active learning when the user can explain the critical path and one material failure scenario correctly, or asks to stop.

## Phase 6: Exportable Artifacts

Provide copy-paste exports for artifacts produced by the approved outline. Include only applicable headings:

```markdown
## Exportable Artifacts

### Mermaid Diagram (paste into your wiki, GitHub README, Notion page, etc.)
[Full mermaid code block]

### Questions Checklist
- [ ] Question 1
- [ ] Question 2
```
