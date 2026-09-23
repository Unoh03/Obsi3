# Agent Handoff — Build a Reusable Handoff Generation Skill

## 1. WHY

The user often explores ideas freely in Chat, then transfers concrete implementation work to Codex/Astra.

A plain conversation summary has repeatedly caused the receiving agent to lose critical execution context:

- why the work was started,
- what has already been decided or verified,
- what is still only an assumption,
- what may or may not be changed,
- why a specific approach was chosen,
- what evidence is required for success,
- and what exact action should be taken first.

The goal is therefore not to summarize the whole conversation.

The goal is to **serialize the minimum high-signal execution state required for another agent to resume the task without re-reading or reconstructing the original conversation.**

Target workflow:

```text
Chat exploration/design
→ Handoff Skill
→ structured HANDOFF
→ Codex/Astra
→ immediate continuation from the correct state
```

### Design Rationale

The 10 fields are not merely a document template.

They form a **minimal execution-state model for agent-to-agent task transfer**.

Mental model:

```text
Implicit task state in Chat
        ↓ serialize
Structured HANDOFF
        ↓ deserialize
Execution state in receiving Agent
```

The objective is **task-state serialization**, not conversation summarization.

Each field exists to prevent a specific class of handoff failure.

| Field | Primary failure prevented |
|---|---|
| WHY | Optimizing toward the wrong intent despite pursuing the nominal goal |
| GOAL | Unclear success state and uncontrolled task expansion |
| CURRENT STATE | Repeating completed work or treating planned work as completed |
| SCOPE | Unnecessary refactoring, feature expansion, or unrelated work |
| INPUTS & ASSETS | Using stale, incorrect, or non-canonical sources |
| HOW | Re-designing an already-decided execution approach |
| CONSTRAINTS | Modifying protected files, environments, or security boundaries |
| EVIDENCE | Treating artifact existence or partial tests as proof of success |
| DONE | No clear stopping or acceptance condition |
| FIRST ACTION | Repeating discovery and orientation after handoff |

The optimization target is not maximum context.

It is **maximum signal-to-noise ratio for task continuation**.

```text
Full conversation transfer
→ relevant and irrelevant context mixed together
→ receiving Agent reconstructs state again
→ token cost + rework + higher error risk

Structured HANDOFF
→ task-relevant state only
→ verify only necessary sources
→ continue from the current point
```

Prefer **task-relevant state preservation** over conversational completeness.

Important execution steps must preserve both WHAT and WHY.

```text
WHAT only
→ procedure becomes brittle when conditions change

WHAT + WHY
→ receiving Agent can adapt the method while preserving intent
```

WHY is therefore not explanatory decoration.

It is **execution metadata that improves robustness under changed conditions**.

Epistemic state must also remain explicit.

At minimum, distinguish:

- **FACT** — explicitly established information
- **VERIFIED / OBSERVED** — confirmed through execution, output, runtime evidence, or direct inspection
- **ASSUMPTION** — plausible but not yet verified
- **PLAN** — intended future work

Never silently promote a weaker state into a stronger one.

---

## 2. GOAL

Create a reusable **Agent Handoff Generation Skill**.

The Skill must analyze the available conversation context, user-provided materials, and task state, then generate a HANDOFF with exactly these 10 top-level sections:

1. WHY
2. GOAL
3. CURRENT STATE
4. SCOPE
5. INPUTS & ASSETS
6. HOW
7. CONSTRAINTS
8. EVIDENCE
9. DONE
10. FIRST ACTION

A receiving Agent should be able to use the generated HANDOFF without reading the original conversation and still preserve:

- task intent,
- current verification state,
- important decisions,
- scope,
- constraints,
- evidence standards,
- completion criteria,
- and the immediate next action.

The Skill is not intended to be a generic summarizer.

It is intended to **restore the execution state of a task across agent boundaries**.

---

## 3. CURRENT STATE

### Confirmed Base Schema

#### 1. WHY
Why the work exists and the intended final usage scenario.

#### 2. GOAL
What must become possible when this task is complete.

#### 3. CURRENT STATE
What already exists, what has been verified, and what remains uncertain.

#### 4. SCOPE
What is included and explicitly excluded.

#### 5. INPUTS & ASSETS
Existing code, files, data, accounts, environments, repositories, and other required assets.

#### 6. HOW
Tools, execution method, ordering, and major implementation steps.

#### 7. CONSTRAINTS
Prohibitions, security boundaries, protected areas, user preferences, and non-negotiable restrictions.

#### 8. EVIDENCE
What observations, artifacts, logs, outputs, or runtime evidence determine success or failure.

#### 9. DONE
Acceptance criteria and conditions required before the task may be considered complete.

#### 10. FIRST ACTION
The exact first action the receiving Agent should perform.

### Mandatory Rules

> For major steps, preserve not only WHAT must be done, but WHY it is necessary.

> Do not mix FACT, VERIFIED / OBSERVED, ASSUMPTION, and PLAN.

### Recommended Nested Structures

Do not add unnecessary top-level fields.

Use nested structures when needed.

#### DECISIONS

Preserve:

- important decisions already made,
- the selected approach,
- rejected alternatives,
- and the reason for the decision.

Purpose:

Prevent the receiving Agent from reopening settled decisions or returning to approaches already rejected for good reasons.

#### OPEN QUESTIONS / BLOCKERS

Preserve:

- unresolved questions,
- items requiring user judgment,
- external blockers,
- and items still requiring verification.

Purpose:

Prevent unresolved states from being inherited as if they were completed facts.

### Not Yet Completed

- Skill implementation
- Skill installation
- automated generation testing
- regression testing
- automated quality evaluation

---

## 4. SCOPE

### Included

- design the Agent Handoff Skill,
- define the 10-field schema,
- define writing rules for each field,
- define FACT / VERIFIED / ASSUMPTION / PLAN classification,
- preserve WHY and rationale,
- preserve important decisions and rejected alternatives,
- define OPEN QUESTIONS / BLOCKERS handling,
- define behavior when information is missing,
- define long-context compression priorities,
- distinguish HANDOFF from repository-wide instructions such as `AGENTS.md`,
- distinguish EVIDENCE from DONE,
- define FIRST ACTION quality requirements,
- implement the Skill in an installable form,
- test it against at least one real Chat → Codex/Astra case,
- and, if practical, establish a regression-test pattern.

### Excluded

- Graphify implementation,
- Archify implementation,
- Maple-related feature implementation,
- modification of unrelated project code,
- and execution of the downstream task described by a generated HANDOFF.

The purpose of this work is to **build the transfer mechanism**, not to execute transferred work.

---

## 5. INPUTS & ASSETS

Current source material:

- this HANDOFF,
- the confirmed 10-field schema,
- future real Chat → Codex/Astra examples for testing,
- repository `AGENTS.md` files where applicable,
- and relevant MOCs, READMEs, source files, or runtime evidence when required for test cases.

Conceptual role separation:

```text
AGENTS.md
= persistent repository-wide operating rules

HANDOFF
= state and execution contract for one specific task

Graphify
= optional relationship/retrieval aid

Source / Runtime Evidence
= factual and verification ground truth

Receiving Agent
= executor that restores state from the HANDOFF
```

The HANDOFF must not duplicate all of `AGENTS.md`.

Include only persistent rules that materially affect the current task, or reference them where appropriate.

The HANDOFF must also not replace actual sources.

```text
HANDOFF
→ tells the Agent what matters and where to verify it

Source / Runtime Evidence
→ proves the actual state
```

---

## 6. HOW

### Step 1 — Inspect the Current Skill System

Before modifying anything, inspect the current Codex Skill authoring and installation conventions and existing installed Skill structures.

**Why**

Do not guess the current Skill format, loading behavior, or installation layout.

---

### Step 2 — Lock the 10-Field Schema

Use the 10 fields as the stable top-level output contract.

Avoid unnecessary top-level expansion.

**Why**

A stable schema reduces retrieval cost and allows receiving Agents to know where each type of information will always appear.

---

### Step 3 — Implement Epistemic-State Classification

Classify relevant information into at least:

- FACT
- VERIFIED / OBSERVED
- ASSUMPTION
- PLAN

Examples:

```text
"We intend to use this approach."
→ PLAN

"The file exists."
→ FACT

"The command completed successfully and produced the expected output."
→ VERIFIED

"This is probably the root cause."
→ ASSUMPTION
```

Do not promote uncertain information.

**Why**

This prevents planned work from becoming inherited as completed work and prevents model inference from becoming inherited as fact.

---

### Step 4 — Preserve Decision Context

For important decisions, preserve when possible:

- selected approach,
- rejected alternatives,
- reason alternatives were rejected,
- reason the selected approach was chosen.

Example:

```text
DECISION
- Use CDP Network capture → replay instead of DOM scraping.

WHY
- Preserve the real request/response contract and reduce UI dependency.

REJECTED
- DOM scraping.

REASON
- Fragile under UI changes and weak at exposing the actual calculation request source.
```

**Why**

This prevents a new Agent from repeating already-resolved design debates.

---

### Step 5 — Implement Context Compression Rules

Do not summarize everything.

Prioritize:

1. WHY
2. GOAL
3. current verified state
4. major decisions and rationale
5. SCOPE
6. CONSTRAINTS
7. canonical INPUTS / ASSETS
8. EVIDENCE
9. DONE
10. FIRST ACTION

Remove:

- irrelevant conversation,
- repetition,
- resolved dead ends,
- and low-value narrative history.

Preserve a failed approach only if it explains why a current decision exists.

**Why**

The objective is not minimum token count in isolation.

The objective is **minimum total continuation cost**, including rediscovery and rework.

---

### Step 6 — Keep EVIDENCE and DONE Separate

Do not merge them.

```text
EVIDENCE
= what must be observed, captured, or preserved

DONE
= what conditions that evidence must satisfy
```

Example:

```text
EVIDENCE
- Wazuh Alert JSON
- Shuffle Execution
- GitHub Run ID
- Argo Sync result

DONE
- The same incident identifier is traceably linked across
  Alert → Execution → Run → Argo.
```

**Why**

The existence of evidence is not equivalent to satisfying the acceptance condition.

---

### Step 7 — Make FIRST ACTION Concrete

Avoid vague instructions such as:

```text
Review the project.
Inspect the files.
Check the current state.
```

Prefer:

- exact file,
- exact command,
- exact read-only check,
- and what conclusion should be drawn from it.

Example:

```text
FIRST ACTION

Without modifying anything, read:

- scripts/maple/README.md
- scripts/maple/docs/current-architecture.md

Confirm the current capture/replay architecture and incomplete phase,
then compare `git status` with the latest commit.
```

**Why**

FIRST ACTION exists to minimize resume latency and orientation cost.

---

### Step 8 — Test the Skill Against a Real Case

Use this original conversation or a real Maple/Codex task as a test input.

Generate a HANDOFF and compare it against a human-authored reference.

Check specifically for:

- intent preservation,
- epistemic-state accuracy,
- decision preservation,
- rejected alternatives,
- scope preservation,
- EVIDENCE / DONE separation,
- and FIRST ACTION quality.

---

### Step 9 — Perform a Continuation Test

If practical, give a new Agent only the generated HANDOFF, without the original conversation.

Verify whether it:

- understands the same goal,
- starts from the correct current state,
- avoids repeating completed work,
- avoids rejected approaches,
- respects the same constraints,
- uses the same evidence standard,
- and stops under the same DONE condition.

**Why**

Handoff quality should be evaluated by **state restoration performance**, not prose quality alone.

---

## 7. CONSTRAINTS

- Do not invent facts not supported by the available context.
- Do not describe planned work as completed.
- Do not treat file existence as runtime verification.
- Do not treat another AI response as factual evidence by itself.
- Do not remove critical constraints merely to shorten the HANDOFF.
- Do not reduce WHY to a generic goal sentence.
- Do not preserve WHAT while discarding important decision rationale.
- Do not use vague completion criteria.
- Do not use vague FIRST ACTION instructions when concrete actions are available.
- Do not copy the full conversation into the HANDOFF.
- Do not mix persistent repository policy with task-specific state.
- Do not assume destructive, dangerous, or externally visible actions without explicit authorization.
- Mark uncertainty explicitly with labels such as `UNKNOWN`, `ASSUMPTION`, or `NEEDS VERIFICATION`.
- Do not let the HANDOFF replace canonical source material.
- Prefer conservative epistemic classification when evidence is weak.
- Do not blur uncertainty merely to improve prose.
- Missing critical state is worse than moderate document length, but irrelevant history should still be removed.

### Language Rule

The Skill's canonical schema, internal instructions, and generated HANDOFF documents should default to **English** for efficiency and interoperability across agents.

Use another language only when explicitly requested or when preserving exact source wording materially matters.

---

## 8. EVIDENCE

Skill quality must be evaluated through structured checks, not by whether the HANDOFF merely looks polished.

### A. Structural Validation

Confirm:

- all 10 fields exist,
- each field contains the intended information class,
- unnecessary duplication is limited.

### B. Epistemic-State Validation

Check whether important source statements were correctly classified as:

- FACT,
- VERIFIED / OBSERVED,
- ASSUMPTION,
- PLAN.

### C. Information-Preservation Validation

Confirm that important source context preserved:

- WHY,
- GOAL,
- major decisions,
- rejected alternatives,
- constraints,
- incomplete state,
- canonical source locations,
- EVIDENCE,
- DONE,
- FIRST ACTION.

### D. Loss Validation

Compare against a human-authored reference and identify:

- missing critical state,
- unsupported state promotion,
- lost rationale,
- resurrected rejected approaches,
- scope drift,
- EVIDENCE / DONE confusion.

### E. Continuation Validation

Give only the generated HANDOFF to a fresh Agent and verify whether it:

- restores the correct intent,
- starts at the correct point,
- avoids repeating completed work,
- avoids rejected methods,
- respects constraints,
- uses the intended evidence standard,
- and terminates under the intended DONE condition.

### F. Context-Efficiency Validation

If practical, compare:

```text
Resume from full original conversation

vs.

Resume from HANDOFF only
```

Measure or qualitatively compare:

- initial discovery work,
- duplicate file reads,
- incorrect assumptions,
- number of Agent turns before productive execution,
- rework,
- and total continuation cost.

The optimization target is **total continuation efficiency**, not token minimization in isolation.

---

## 9. DONE

The work is complete only when all of the following are satisfied:

1. An installable Handoff Generation Skill exists.
2. It reliably emits the 10-field schema.
3. WHY is preserved.
4. FACT / VERIFIED / ASSUMPTION / PLAN remain distinct.
5. Important decisions and rationale are preserved.
6. Rejected alternatives are preserved when relevant.
7. SCOPE and CONSTRAINTS remain explicit.
8. HANDOFF and canonical Source retain separate roles.
9. EVIDENCE and DONE remain semantically distinct.
10. FIRST ACTION is concrete enough to execute immediately.
11. At least one real conversation is tested against a human-authored reference HANDOFF.
12. A fresh Agent can resume correctly using the generated HANDOFF without the original conversation.
13. The Skill preserves the design intent of **task-state restoration**, rather than degrading into a generic 10-section summarizer.

If practical, preserve test results and known limitations with the Skill.

---

## 10. FIRST ACTION

**Before modifying any files, inspect the current official Codex Skill authoring/installation rules and the structure of existing installed Skills. Then produce a read-only implementation design for this Handoff Skill.**

The design must include at minimum:

- Skill directory structure,
- trigger conditions,
- input context policy,
- 10-field output schema,
- FACT / VERIFIED / ASSUMPTION / PLAN classification rules,
- DECISIONS / REJECTED / OPEN QUESTIONS handling,
- WHY preservation rules,
- context compression rules,
- EVIDENCE / DONE separation,
- FIRST ACTION quality rules,
- test strategy,
- regression-test feasibility,
- expected failure modes,
- safeguards against unsupported state promotion.

Do not begin implementation until the design has been checked against both the requirements and the Design Rationale above.
