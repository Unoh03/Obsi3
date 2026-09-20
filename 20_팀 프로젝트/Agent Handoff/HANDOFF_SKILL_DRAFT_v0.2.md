# Agent Handoff Skill — Candidate Draft v0.2

> Status: research candidate, not canonical.
> Baseline preserved separately in `HANDOFF_SKILL_DRAFT.md`.

## Purpose

Build a reusable Agent Handoff Generation Skill for transferring a task from Chat to Codex/Astra or another fresh Agent without requiring the original conversation to be re-read.

The Skill should serialize only the **minimum high-signal task state required for correct continuation**.

## Candidate Schema v0.2

1. INTENT
2. CURRENT STATE
3. DECISIONS
4. SCOPE
5. INPUTS & ASSETS
6. HOW
7. CONSTRAINTS
8. EVIDENCE
9. DONE
10. FIRST ACTION

This remains a research candidate. Field count and boundaries are not final.

---

## 1. INTENT

### Outcome — REQUIRED

State the target outcome or end state.

### Rationale — CONDITIONAL

Preserve the downstream purpose when it materially affects implementation choice, boundaries, verification strategy, interpretation of success, or downstream use.

Do not generate generic filler merely to populate a WHY field.

Task-level WHY belongs here. Method-level WHY belongs under DECISIONS.

---

## 2. CURRENT STATE

CURRENT STATE is a **compact execution snapshot**, not a project narrative.

Recommended structure:

- Phase
- Completed
- In Progress
- Pending
- Blocked
- Environment (optional)

Its purpose is to let the receiving Agent identify the current execution coordinate immediately.

Do not place long rationale, future plans, or speculative explanations here.

### Execution Status Vocabulary

- COMPLETED
- IN_PROGRESS
- PENDING
- BLOCKED

### Epistemic Status

Do not use the old single taxonomy `FACT / VERIFIED / ASSUMPTION / PLAN` as mutually exclusive states.

When a claim needs qualification, use a separate epistemic axis:

- OBSERVED
- INFERRED
- UNKNOWN

Evidence remains a separate concern.

### Blockers

CURRENT STATE may mark an item as BLOCKED.

If the reason, impact, or unblock condition matters, preserve those details in a structured note or subsection.

---

## 3. DECISIONS

Preserve decisions that would be expensive, ambiguous, or unsafe for a new Agent to reconstruct.

For important decisions, capture:

- Decision
- Rationale
- Rejected Alternatives
- Why Rejected
- Status

Prioritize decisions whose rationale would otherwise disappear with the original conversation.

---

## 4. SCOPE

Preserve the active task boundary.

At minimum, distinguish when relevant:

- In Scope
- Out of Scope

The role of SCOPE is still under study.

Open question: Is SCOPE primarily handoff state, a task-brief contract, or both?

Do not infer permission merely from scope.

---

## 5. INPUTS & ASSETS

Identify the minimum source material, code, data, environments, accounts, and tools required to continue.

Prefer canonical sources and reduce the receiving Agent's search space.

Possible structure:

- Canonical Sources
- Repositories / Paths
- Runtime / Environment
- Existing Tools
- Required External Access

Do not copy source content unnecessarily.

HANDOFF should point to what matters and where to verify it.

---

## 6. HOW

Preserve the current execution strategy only when it is still decision-relevant.

Do not turn HOW into a brittle step-by-step script unless the procedure itself is required.

Prefer:

- selected strategy
- major sequence
- required tools
- known execution dependencies

Avoid forcing a stale method when a receiving Agent could safely adapt while preserving INTENT and DECISIONS.

### Open Question — Tool / Plugin Acquisition Authority

User experience indicates that tasks may need an explicit statement such as:

> The Agent may actively install or request tools/plugins when needed.

It is not yet decided whether this belongs under HOW, CONSTRAINTS / AUTHORITY, or INPUTS & ASSETS / CAPABILITIES.

---

## 7. CONSTRAINTS

Preserve boundaries the receiving Agent must not violate.

Examples:

- read-only requirements
- protected files or systems
- security restrictions
- destructive-action limits
- external-action approval requirements
- user preferences that materially affect execution

Do not duplicate all persistent repository policy from `AGENTS.md`.

Reference persistent policy where possible and preserve only task-relevant constraints.

### Open Question — Authority

Constraints may need to distinguish:

- MUST NOT
- MAY
- MAY ONLY WITH APPROVAL

This may become an explicit authority model later.

---

## 8. EVIDENCE

Specify what observations, artifacts, logs, outputs, or runtime traces can support a success/failure judgment.

EVIDENCE answers:

> What must be observed or preserved?

Where useful, distinguish source existence from runtime evidence.

Do not promote partial evidence into completion.

---

## 9. DONE

Define the acceptance predicate over the required evidence and state.

DONE answers:

> Under exactly what conditions may the task be considered complete?

Keep DONE semantically separate from EVIDENCE.

Artifact existence alone is not completion unless explicitly sufficient.

---

## 10. FIRST ACTION

State the exact first productive action the receiving Agent should take.

Prefer exact file, exact command, exact read-only inspection, and the conclusion to derive.

Avoid vague instructions such as `Review the project` or `Check the current state`.

The necessity of FIRST ACTION as a top-level field is still under study, but its function is to reduce resume latency.

---

# Cross-Cutting Rules

## Preserve WHAT + WHY selectively

Preserve WHY when it changes how the Agent should interpret, adapt, verify, or bound the task.

Do not generate rationale filler.

## Separate task rationale from decision rationale

- Task WHY → INTENT.Rationale
- Method WHY → DECISIONS.Rationale

## Separate orthogonal state dimensions

Execution Status ≠ Epistemic Status ≠ Evidence.

## Preserve uncertainty

Do not silently upgrade:

- inferred → observed
- pending → completed
- source existence → runtime verification
- hypothesis → fact

## Optimize total continuation cost

Do not optimize token count in isolation.

The target is lower total cost across re-reading, rediscovery, duplicated work, incorrect assumptions, rework, and verification failures.

## English by default

The Skill's canonical schema, internal instructions, and generated HANDOFF documents should default to English unless another language is explicitly required.

---

# Current Open Questions

1. Should SCOPE remain top-level?
2. Should HOW remain top-level, or should DECISIONS absorb most of its value?
3. Where should tool/plugin installation and acquisition authority live?
4. Should AUTHORITY / CAPABILITIES become explicit?
5. Should BLOCKERS become top-level or remain under CURRENT STATE?
6. Should Environment State live under CURRENT STATE or INPUTS & ASSETS?
7. Is FIRST ACTION truly distinct from NEXT STEP?
8. Are EVIDENCE and DONE mandatory for trivial tasks?
9. Should the schema stay fixed while allowing empty/omitted subsections?
10. What information has the highest reconstruction cost after session loss?

---

# Validation Direction

Do not evaluate the Skill primarily by prose quality.

Evaluate **state restoration performance**.

A fresh Agent given only the HANDOFF should:

- understand the same intent
- start at the correct execution point
- avoid repeating completed work
- preserve important decisions
- avoid rejected approaches
- respect task boundaries
- use the correct evidence standard
- reach the same DONE condition

Compare, where practical:

- Resume from full conversation
- Resume from HANDOFF only

Inspect duplicate reads, rediscovery, wrong assumptions, turns before productive execution, rework, and total continuation cost.

---

# Research Status

This is the first materially revised design proposal.

- `HANDOFF_SKILL_DRAFT.md` = pre-study baseline
- `HANDOFF_SKILL_DRAFT_v0.2.md` = first research-driven candidate

Do not implement the Skill from this candidate yet.

Continue field-by-field schema attack before producing a canonical specification.

# NEXT RESEARCH ACTION

Attack **SCOPE** next.

Questions:

- Is SCOPE handoff state, task-brief contract, or both?
- What must be preserved when scope changes during execution?
- How should In Scope / Out of Scope differ from Authority boundaries?