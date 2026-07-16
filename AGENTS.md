# AGENTS.md

## Repository Context

This is a Korean Obsidian study vault, not a software project. Keep repository
docs such as `README.md` and `AGENTS.md` in English and vault content in Korean
unless asked otherwise. `00_index/Home.md` is the entry point; study, project,
certification, source, optional-template, and temporary material live under
`10_학습 노트/`, `20_팀 프로젝트/`, `30_자격증/`, `40_자료/`, `90_템플릿/`,
and `99_잡동사니/` respectively.

## Workflow

- Before editing, run `git status --short`; preserve unrelated and dirty work.
- Inspect only relevant files, preferring `rg --files` and `rg`.
- Limit edits to the requested outcome. Do not rename, move, split, delete, or
  untrack notes and assets without explicit approval.
- Preserve Korean filenames and the existing wiki-link style.
- Destructive, secret-related, or history-rewriting approval must name the
  action and target; an ambiguous `ㅇㅋ` is insufficient.

## Read Budget

- Exact path: read the target first; check its MOC only if role or placement is
  unclear. Known topic: start at the nearest subject/project MOC. Broad unknown
  scope: route from `Home.md` through area and subject/project MOCs.
- Cleanup: start from the Git range and affected files, not the full MOC chain.
- Read `LLM_AGENT_INDEX.md` only for unresolved routing/RAW/legacy ambiguity.
  Read the architecture and checklist documents only for formal audits or
  design decisions.
- Search filenames and links before source, PDF, screenshot, or RAW content.
- For a large note, locate the relevant H1/Part and read only that section plus
  necessary adjacent context before considering a full-body read.

## Note Creation

- Templates are optional examples. Choose the note role and body structure
  directly; avoid empty boilerplate.
- New notes require `type`, `status`, `created`, and routing: `topic` plus
  `parent_moc`, or `project` plus `project_moc`. Add source/evidence fields only
  when useful.
- Use canonical values from `90_템플릿/00_템플릿_목차.md`; do not duplicate
  `status` as a tag.
- Do not retrofit legacy notes unless requested or current routing depends on
  their metadata.

## Obsidian Conventions

- Create notes in the nearest existing topic folder; ask only if routing spans
  materially different areas.
- Link only verified targets. Check basename ambiguity and use plain text for
  unresolved references; never create `[[]]` placeholders.
- Keep optional templates in `90_템플릿/` and sources/assets in `40_자료/`.

## Vault Architecture Changes

- Treat index/MOC overhaul, migration, and audit as architecture work. Before
  repository actions, state the intended outcome, scope, exclusions, discovery,
  decision points, and outcome checks; then perform read-only discovery.
- Inventory the navigation artifacts in scope and distinguish routes from
  status records, source catalogs, RAW logs, and leaf notes.
- When several structures remain valid, present the evidence-backed target
  model before editing and ask only decisions that materially change it.
- Completion requires coverage and retrieval checks, not merely valid links.
  Report excluded artifacts, unresolved choices, and unverified dimensions.

## Post-session Cleanup

- Record `START_REF=$(git rev-parse HEAD)` before other sessions when possible.
  Obsidian Git auto-commits, so inspect both `START_REF..END_REF` and the current
  worktree; a clean status is not proof of review.
- Start with `git diff --name-status START_REF..END_REF`, then inspect only
  affected paths and run `validate_frontmatter.py --range START_REF..END_REF`.
- Update a MOC only for route, restart, RAW/source, or legacy changes; never add
  completion logs. Without a start ref, use reported paths and recent commits
  and state the remaining uncertainty.

## Git And File Hygiene

- Existing tracked Obsidian plugin files are intentional backups. Exclude them
  from normal reads and do not untrack/delete them without explicit approval.
- Do not newly track workspace state, sync secrets, plugin `data.json`, `*.war`,
  or generated/temporary binaries without explicit approval. Never track real
  Remotely Save configuration.
- Ask before adding/staging binaries over 5 MB; report tracked `*.war` files.
- Do not open `.env*`, private keys, kubeconfigs, credentials, real sync config,
  or likely secret files without explicit approval.
- Do not rewrite history, force push, or run destructive cleanup without
  explicit confirmation.

## Commit Messages

Use KST and the existing `Auto:` or `Manual: YYYY. MM. DD. HH:mm:ss <summary>`
style. Do not introduce Conventional Commit prefixes unless asked.

## Verification

- Markdown: run `git diff --check`, inspect the targeted diff, and verify new
  wiki-link targets.
- For frontmatter, run `validate_frontmatter.py --changed`; after auto-commit,
  use `--range START_REF..END_REF`.
- For ignore/tracking changes, also inspect status, tracked files, ignore rules,
  conflict markers, and tracked `*.war` files.
- Report failed, skipped, and unverified checks; this vault has no default build.

## Documentation And Language

- Default to Korean and concise Obsidian-friendly Markdown; preserve technical
  identifiers and repository conventions.
- Base claims on inspected files, commands, runtime evidence, or primary sources;
  state unsupported assumptions and unverified dimensions.
- Treat another AI answer as claims, not evidence. Report only material
  disagreements, unsupported claims, new findings, and required actions.
