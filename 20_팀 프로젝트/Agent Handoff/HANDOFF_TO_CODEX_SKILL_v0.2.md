---
type: project-note
status: active
created: 2026-09-30
project: Agent Handoff
project_moc: "[[20_팀 프로젝트/Agent Handoff/00_Agent Handoff MOC]]"
---

# HANDOFF — Experimental Agent Handoff Skill v0.2

> Receiver: Codex / Astra
>
> Purpose: implement the first experimental Agent Handoff Generation Skill from the current research state.
>
> This HANDOFF is also the first real dogfooding case of the v0.2 handoff schema.
>
> The original Chat conversation is **not required**. Treat this document plus the referenced project files as the continuation package.

---

## 1. INTENT

### Outcome

Implement an **experimental, usable Agent Handoff Generation Skill v0.2** that converts available task/conversation context into a compact HANDOFF for a fresh receiving Agent.

The prototype must preserve the current research intent:

> A HANDOFF is not a generic conversation summary. It is a task-state transfer artifact intended to restore enough execution state for another Agent to continue correctly without re-reading the original conversation.

The prototype must be installable/usable according to the **current supported Codex Skill mechanism**, verified at implementation time rather than guessed from stale knowledge.

### Rationale

The user routinely explores and designs work in Chat, then transfers implementation to Codex/Astra. The receiving Agent can otherwise lose:

- the real downstream intent,
- current execution position,
- important decisions and rejected alternatives,
- scope boundaries,
- source-of-truth locations,
- verification state,
- acceptance criteria,
- and the correct continuation point.

The Skill exists to reduce rediscovery, duplicate work, state promotion, scope drift, and total continuation cost.

This is an **experimental prototype**, not the canonical v1 specification. Its implementation should expose design problems rather than silently freeze them.

---

## 2. CURRENT STATE

### Phase

**Research → first prototype implementation**

### COMPLETED

- The Agent Handoff topic has been promoted to a standalone project.
- A pre-study baseline exists:
  - `20_팀 프로젝트/Agent Handoff/HANDOFF_SKILL_DRAFT.md`
- A first research-driven candidate exists:
  - `20_팀 프로젝트/Agent Handoff/HANDOFF_SKILL_DRAFT_v0.2.md`
- A research log exists:
  - `20_팀 프로젝트/Agent Handoff/01_연구 로그.md`
- The project MOC exists:
  - `20_팀 프로젝트/Agent Handoff/00_Agent Handoff MOC.md`
- The following schema changes have been developed:
  - `WHY + GOAL` → candidate `INTENT {Outcome, Rationale}`
  - `DECISIONS` promoted as a major state category
  - `CURRENT STATE` narrowed to a compact execution snapshot
  - the old `FACT / VERIFIED / ASSUMPTION / PLAN` single taxonomy identified as structurally mixed
  - execution status, epistemic status, and evidence separated conceptually
- SCOPE was analyzed after v0.2 was written.

### IN_PROGRESS

- Turning the research candidate into an executable Skill.
- Testing whether the v0.2 schema is practical in real handoffs.

### PENDING

- INPUTS & ASSETS field attack
- HOW field attack
- Authority / Capabilities / Execution Envelope modeling
- CONSTRAINTS field attack
- EVIDENCE field attack
- DONE field attack
- FIRST ACTION field attack
- real continuation tests across multiple tasks
- canonical `HANDOFF_SKILL_SPEC.md`
- v1.0 stabilization

### BLOCKED

None currently known.

### Important freshness note

The latest SCOPE analysis is **newer than `HANDOFF_SKILL_DRAFT_v0.2.md`** and must not be lost:

- SCOPE = the current effective **work boundary**
- preferred semantics:
  - In Scope
  - Out of Scope
  - Supporting Work Boundary when useful
- SCOPE must not be treated as equivalent to permission/authority.
- `IN SCOPE ≠ AUTHORIZED`
- tool/plugin installation permission belongs to an Authority / Execution Envelope concept, not automatically to SCOPE.
- a strong candidate execution model is:
  - MAY
  - MUST NOT
  - REQUIRES APPROVAL
  - optionally MAY REQUEST

This is a research finding, not yet a finalized schema change.

---

## 3. DECISIONS

### Decision 1 — Build a prototype now

**Decision**

Implement v0.2 experimentally before finishing every remaining field analysis.

**Rationale**

Several open questions are now more likely to be resolved through real usage than through further paper-only design. The prototype is intended to reveal duplication, missing state, awkward field boundaries, and continuation failures.

**Rejected alternative**

Finish the full theoretical schema before implementing anything.

**Why rejected**

It risks over-designing without empirical feedback.

**Status**

ACTIVE FOR THIS TASK.

---

### Decision 2 — Preserve the baseline

**Decision**

Do not overwrite:

- `HANDOFF_SKILL_DRAFT.md`
- `HANDOFF_SKILL_DRAFT_v0.2.md`
- existing research history

Create implementation artifacts separately.

**Rationale**

The project intentionally preserves meaningful design states for comparison. Git tracks line history; explicit versions preserve human-readable design milestones.

**Status**

NON-NEGOTIABLE.

---

### Decision 3 — Treat handoff as state transfer, not summary

**Decision**

The Skill must optimize for **state restoration performance**, not conversational completeness or prose polish.

**Rationale**

A receiving Agent should resume correctly without reconstructing the original conversation.

**Rejected behavior**

- generic conversation summarization
- chronological retelling
- copying the full conversation
- prose-first compression that blurs epistemic state

**Status**

CORE DESIGN PRINCIPLE.

---

### Decision 4 — Preserve decisions and rationale

**Decision**

Important decisions must preserve:

- selected approach,
- rationale,
- rejected alternatives when materially relevant,
- why those alternatives were rejected.

**Rationale**

Decision rationale often has high reconstruction cost after session loss and prevents new Agents from reopening settled design debates.

**Status**

CORE DESIGN PRINCIPLE.

---

### Decision 5 — Separate state dimensions

**Decision**

Do not model `FACT / VERIFIED / ASSUMPTION / PLAN` as one mutually exclusive classification.

Prefer separate concepts such as:

- execution status: COMPLETED / IN_PROGRESS / PENDING / BLOCKED
- epistemic status: OBSERVED / INFERRED / UNKNOWN
- evidence: source/runtime proof

**Rationale**

The old labels mix different dimensions: truth/knowledge, verification, and time/execution state.

**Status**

STRONG CANDIDATE; implement conservatively and record any awkwardness.

---

### Decision 6 — Task WHY and Method WHY are different

**Decision**

- task-level rationale → `INTENT.Rationale`
- method-level rationale → `DECISIONS.Rationale`

**Rationale**

They answer different questions and should not be collapsed into one generic WHY bucket.

**Status**

STRONG CANDIDATE.

---

## 4. SCOPE

### In Scope

- inspect the current supported Codex Skill authoring/install mechanism
- inspect existing installed Skills only as needed to learn current structure
- implement one experimental Agent Handoff Skill based on v0.2
- make the Skill usable by Chat/Codex-compatible Agent workflows where the current Skill mechanism supports it
- encode the current research principles without pretending open questions are settled
- add lightweight validation/test material if the current Skill framework supports it
- perform at least one practical generation/self-check using available project material
- document implementation findings, contradictions, and schema friction
- preserve enough instructions that another Agent can inspect and reproduce the prototype

### Out of Scope

- declaring v0.2 canonical or final
- creating `HANDOFF_SKILL_SPEC.md` as if research were complete
- silently redesigning unresolved schema fields
- implementing Graphify or Archify
- modifying Maple feature code
- broad Obsidian vault cleanup
- unrelated repository refactoring
- rewriting the research history
- deleting or replacing baseline drafts
- turning this project into a generic memory/RAG system

### Supporting Work Boundary

Supporting work is allowed only when it is necessary to:

1. make the prototype Skill function,
2. verify it,
3. or document a material implementation finding.

Do not expand into general tooling/framework cleanup merely because it would be convenient.

---

## 5. INPUTS & ASSETS

### Primary project sources

Read in this order:

1. `AGENTS.md`
2. `20_팀 프로젝트/Agent Handoff/00_Agent Handoff MOC.md`
3. `20_팀 프로젝트/Agent Handoff/HANDOFF_SKILL_DRAFT_v0.2.md`
4. `20_팀 프로젝트/Agent Handoff/01_연구 로그.md`
5. `20_팀 프로젝트/Agent Handoff/HANDOFF_SKILL_DRAFT.md` only when comparison with the original baseline is useful
6. this HANDOFF

### Source roles

- `AGENTS.md` = persistent repository operating rules
- project MOC = routing and current project state
- research log = rationale/history of schema changes
- baseline draft = pre-study comparison point
- v0.2 draft = current implementation candidate
- this HANDOFF = task-specific execution contract for the prototype implementation

Do not treat any draft as stronger factual evidence than inspected runtime/tool behavior.

### External/current sources

For Codex Skill mechanics, use **current official OpenAI/Codex documentation and current installed Skill structures** rather than relying on old assumptions.

### Environment / capabilities

The receiving Agent may use available repository tools and local development tools necessary for this implementation.

If a useful capability is missing:

- local development tooling may be installed when low-risk and task-relevant;
- a relevant plugin/connector may be actively requested if it materially improves the implementation;
- do not treat the absence of a currently installed tool as a reason to stop before checking whether an appropriate tool can be added.

This permission does **not** authorize unrelated system changes or sensitive/external actions.

---

## 6. HOW

Use this as the current execution strategy, not as an immutable implementation script.

### Step 1 — Establish the real Skill interface

Before implementation:

- inspect current official Codex Skill authoring/install rules,
- inspect the minimum necessary installed Skill examples,
- determine the actual supported directory/file structure,
- determine how Skills are discovered/triggered,
- determine whether validation or packaging helpers exist.

**Why**

Do not design against a stale or imagined Skill format.

### Step 2 — Map v0.2 semantics onto the real Skill mechanism

The generated HANDOFF should currently aim to preserve these top-level concepts:

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

But do not hide framework/schema conflicts. If the real Skill mechanism makes another representation materially better, preserve the semantic contract and record the discrepancy rather than silently changing the project theory.

### Step 3 — Encode cross-cutting rules

At minimum, the prototype should instruct the model to:

- prefer high-signal continuation state over full conversation summary,
- preserve task rationale only when decision-relevant,
- preserve important decision rationale,
- keep CURRENT STATE compact,
- distinguish execution state from epistemic confidence and evidence,
- preserve uncertainty,
- avoid promoting plans into completed state,
- avoid promoting source existence into runtime verification,
- avoid reopening rejected approaches without new evidence,
- reduce source search space by pointing to canonical inputs,
- keep EVIDENCE separate from DONE,
- make FIRST ACTION concrete when possible,
- avoid inventing content merely to fill fields.

### Step 4 — Handle unresolved research honestly

Do not pretend the following are settled:

- whether SCOPE remains top-level long term
- whether HOW remains top-level
- whether AUTHORITY / EXECUTION ENVELOPE should replace or extend CONSTRAINTS
- whether BLOCKERS become top-level
- where Environment State belongs
- whether EVIDENCE and DONE are mandatory for trivial tasks
- whether FIRST ACTION is distinct enough from NEXT STEP
- whether a fixed 10-field schema remains desirable

Where implementation requires a choice, choose the smallest reversible option and record it as an implementation assumption.

### Step 5 — Validate with a real-ish handoff case

Use available project material to generate or simulate at least one HANDOFF and inspect:

- intent preservation
- current-state accuracy
- decision preservation
- scope preservation
- uncertainty handling
- evidence/done separation
- usefulness of first action
- unnecessary verbosity
- duplicated information
- missing information

If practical, use this very HANDOFF as a reference/dogfooding case.

### Step 6 — Record findings

Create a concise implementation findings artifact inside the Agent Handoff project.

It should distinguish:

- VERIFIED implementation behavior
- design friction discovered during implementation
- assumptions
- recommended schema changes
- unresolved questions

Do not rewrite the research log as though these findings had already existed.

---

## 7. CONSTRAINTS

### Repository constraints

Follow root `AGENTS.md`.

Especially:

- preserve unrelated work,
- do not rename/move/delete notes or assets without explicit approval,
- do not rewrite Git history,
- do not inspect likely secrets without explicit approval,
- keep edits limited to this project and necessary Skill installation/source locations.

### Experimental-status constraint

The prototype must clearly identify itself as experimental v0.2.

Do not present the schema as finalized.

### Authority / execution envelope for this task

#### MAY

- read the referenced project files
- inspect current official Skill documentation
- inspect installed Skill examples
- create implementation files for the Agent Handoff prototype
- create/update project-local documentation necessary to route or explain the prototype
- install low-risk local development dependencies when genuinely required
- run non-destructive validation/tests

#### MAY REQUEST

- a missing plugin/connector if it materially improves the task

#### REQUIRES USER APPROVAL

- connecting a new external account
- destructive actions
- externally visible publishing/deployment unrelated to normal Skill installation
- broad changes outside the Agent Handoff project
- removal/replacement of baseline research artifacts
- secret/credential access not already explicitly authorized

#### MUST NOT

- overwrite `HANDOFF_SKILL_DRAFT.md`
- overwrite `HANDOFF_SKILL_DRAFT_v0.2.md` as though implementation findings were already part of the research candidate
- declare v0.2 canonical
- fabricate evidence or completion
- broaden the task into unrelated vault/tool cleanup

---

## 8. EVIDENCE

Preserve evidence sufficient to show what was actually implemented and verified.

Minimum evidence should include, where the real Skill system supports it:

- exact Skill source/install path
- key files created
- official/current Skill mechanism inspected
- validation or load/install check performed
- at least one generated/test HANDOFF or equivalent output
- observed discrepancies between the prototype and v0.2 theory
- repository diff/status relevant to this task
- any skipped or unverified validation clearly identified

Do not treat file creation alone as proof that the Skill is usable.

---

## 9. DONE

This prototype task is complete only when all of the following are true:

1. An experimental Agent Handoff Skill v0.2 has been implemented using the current supported Skill mechanism.
2. The Skill's purpose is task-state transfer, not generic summarization.
3. The core v0.2 semantics are represented:
   - INTENT
   - compact CURRENT STATE
   - DECISIONS + rationale
   - SCOPE
   - input/source guidance
   - execution strategy
   - constraints/authority behavior
   - EVIDENCE
   - DONE
   - concrete continuation guidance
4. Execution status, epistemic status, and evidence are not silently collapsed into the old mixed taxonomy.
5. The prototype clearly remains experimental and does not claim the schema is final.
6. Baseline and v0.2 research drafts remain preserved.
7. At least one practical output/self-check has been performed.
8. Implementation findings and unresolved schema friction have been recorded.
9. Relevant repository/Skill validation has been run and failures/skips are reported.
10. A future Chat/Codex session can locate the prototype and understand how to invoke/test it without reconstructing this conversation.

The task is **not** blocked merely because some schema questions remain unresolved. Those unresolved questions are part of the experiment.

---

## 10. FIRST ACTION

Before modifying anything:

1. run the repository's required read-only baseline checks, including `git status --short`;
2. read root `AGENTS.md`;
3. read:
   - `20_팀 프로젝트/Agent Handoff/00_Agent Handoff MOC.md`
   - `20_팀 프로젝트/Agent Handoff/HANDOFF_SKILL_DRAFT_v0.2.md`
   - `20_팀 프로젝트/Agent Handoff/01_연구 로그.md`
   - this HANDOFF;
4. inspect the **current official Codex Skill authoring/install mechanism** and the minimum necessary installed Skill examples;
5. then proceed directly to the smallest reversible experimental implementation.

Do not stop after producing another design-only proposal unless the current Skill mechanism presents a real blocker. The purpose of this task is to build and test the prototype.
