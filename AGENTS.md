# AGENTS.md

## Repository Context

This repository is a Korean-language Obsidian study vault, not a software
project. Keep repository docs such as `README.md` and `AGENTS.md` in English;
keep study notes, MOCs, and templates in Korean unless asked otherwise.

| Folder | Purpose |
|---|---|
| `00_index/` | Vault entry point; `Home.md` is the main MOC |
| `10_학습 노트/` | Study, concept, lab, and troubleshooting notes |
| `20_팀 프로젝트/` | Team-project documents and deliverables |
| `30_자격증/` | Certification study and wrong-answer notes |
| `40_자료/` | PDFs, screenshots, lecture material, and lab assets |
| `90_템플릿/` | Obsidian templates only |
| `99_잡동사니/` | Temporary or unsorted material only when requested |

## Workflow

- Before editing, run `git status --short`. On `dubious ownership`, retry with
  `git -c safe.directory=<repo-path> <git subcommand and args>`; do not change
  global Git configuration.
- Inspect only relevant files. Prefer `rg --files`; use a platform equivalent
  if unavailable.
- Treat existing changes as user work. If a target file is already dirty,
  report the conflict before editing unless the user explicitly includes it.
- Limit edits to requested or directly required files. Do not rename, move, or
  split notes, folders, or assets without explicit approval.
- Preserve Korean filenames and existing wiki-link style.
- For destructive, secret-related, or history-rewriting actions, approval must
  name the action and target. Ambiguous replies such as `ㅇㅋ` are insufficient.

## Read Budget

- If the user names an exact file or path, inspect that target first. Read its
  nearest MOC only when placement, role, or neighboring context is unclear.
- If the topic is known but the exact file is not, start from the nearest
  subject or project MOC. Move upward only when routing remains ambiguous.
- If the scope is broad or unknown, route from `00_index/Home.md` through the
  relevant area MOC and subject or project MOC before opening leaf notes.
- Read `00_index/LLM_AGENT_INDEX.md` only for vault navigation, MOC/index
  architecture, source/RAW separation, stale-index cleanup, or inventory work.
- Read `00_index/Vault_Retrieval_Architecture_v1.md` and
  `00_index/Vault_Curation_Checklist.md` only for repository-wide audits or
  architecture work that needs their design or completion claims.
- Search filenames and links before opening large notes, source directories,
  PDFs, screenshots, or RAW logs.

## Obsidian Conventions

- When routing is unknown, start from `00_index/Home.md` and follow folder/topic
  MOCs, usually `00_*_목차.md`.
- Create notes in the most relevant existing topic folder. Ask before creating
  one if routing is unclear or spans folders.
- Use wiki links only for verified existing targets. Write plain text for
  unresolved targets; never create placeholder links such as `[[]]`.
- Before creating a wiki link, verify the target exists. For basename-only
  links, also check that the basename is not ambiguous.
- Use `90_템플릿/` for templates and `40_자료/` for source materials and assets.

## Vault Architecture Changes

Requests to overhaul, redesign, reorganize, migrate, or audit vault indexes,
MOCs, or navigation are architecture tasks, not simple Markdown-edit tasks.
Do not reduce them to adding MOC files, replacing links, or passing a link
check without first defining the intended navigation outcome.

Before the first repository-specific tool call for such work, state the
provisional outcome, scope, exclusions, discovery plan, decision points, and
outcome-level verification. Then perform read-only discovery before proposing
edits.

For index or MOC work, inventory the relevant navigation artifacts in scope.
Depending on the requested area, this includes `Home.md`, folder and topic
MOCs, project entry documents, dashboards, classification tables, restart
points, source-material indexes, and templates. Distinguish navigation
structure from status records, source catalogs, raw logs, and concrete notes.

Before edits, present the evidence-backed target navigation model and migration
scope when more than one materially different structure is plausible. Do not
ask the user for a full vault specification; resolve factual questions through
inspection and ask only the smallest consolidated question needed for choices
that would change the intended result.

For architecture work, completion requires the agreed outcome-level checks in
addition to Markdown and link checks. State the coverage policy, changed
navigation paths, deliberately excluded artifacts, unresolved decisions, and
any dimensions not verified. Never claim a vault-wide index overhaul is
complete solely because all added links resolve.

## Git And File Hygiene

- Never track local workspaces, plugin bundles, sync secrets, or generated
  binaries: `.obsidian/workspace*.json`, `.obsidian/plugins/*/main.js`,
  `.obsidian/plugins/*/styles.css`, `.obsidian/plugins/remotely-save/data.json`,
  `.obsidian-mobile/plugins/remotely-save/data.json`, or `*.war`.
- Plugin `manifest.json` may be tracked. Do not newly track plugin `data.json`
  without explicit approval after review.
- Report already tracked `*.war` files; ask before index removal or deletion.
- Ask before adding or staging binaries larger than 5 MB, especially under
  `40_자료/`. Prefer external links when practical.
- Do not newly track generated or temporary binaries unless explicitly asked.
- Do not open likely secret files without explicit approval: `.env*`, private
  keys, kubeconfigs, SSH/cloud credentials, real sync config, or filenames
  containing `token`, `credential`, or `secret`. Template/sample exceptions do
  not override a blocked pattern.
- Do not rewrite history, force push, or run destructive cleanup without
  explicit confirmation.

## Commit Messages

Use KST and the existing style:

- `Auto: YYYY. MM. DD. HH:mm:ss <change summary>`
- `Manual: YYYY. MM. DD. HH:mm:ss <change summary>`

Do not introduce Conventional Commit prefixes unless asked.

## Verification

- Markdown: run `git diff --check`, inspect the targeted diff, and verify new
  wiki-link targets.
- `.gitignore` or tracking policy: also run relevant `git status --short`,
  `git ls-files`, `git check-ignore -v`, conflict-marker checks, and
  `git ls-files "*.war"`.
- This vault has no default build or test suite. Report failed or skipped checks.
- If verification fails, fix it within scope or report the blocker. Do not
  present failed or skipped verification as successful.

## Documentation And Language

- Prefer concise Markdown and Obsidian-friendly formatting where useful.
- When reviewing AI-generated output, classify material factual claims by
  evidence status: supported, unsupported, incorrect, or unresolved.
- For recommendations or workflow changes, distinguish evidence-backed
  constraints from design choices that still require user approval or testing.
- Identify unsupported assumptions, scope creep, and verification claims not
  backed by observed checks.
- Prefer reproducible checks: primary sources, repository files, command output,
  diffs, runtime results, or directly inspected source material.
- For cross-validation against another AI's answer:
  - Treat the other answer as a claim set, not as evidence.
  - Inspect the original evidence first when possible. If the answer was already
    shown, return to primary evidence before adopting or rejecting its claims.
  - Agreement between AIs is not evidence.
  - State a brief verdict and identify the evidence actually rechecked when
    material, such as specific files, source pages, commands, diffs, runtime
    results, or official documents.
  - Report only material disagreements, unsupported claims, new findings, and
    required actions. Do not repeat agreed points unless needed for context.
  - Keep each finding compact: evidence, impact, action.
  - If there is no material disagreement, say so briefly and stop.
- Default to Korean. Keep code, identifiers, CLI output, errors, package names,
  and API names in their original language. Follow repository conventions for
  commit messages, docs, comments, changelogs, PR text, and user-facing copy.
