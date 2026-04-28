# QA Compass

QA Compass is an AI skill for turning product requirements, Jira work items, Confluence pages, PRDs, test cases, and execution results into a clear, reusable QA workflow.

It helps PMs, BAs, QAs, and engineers move from "we have requirements somewhere" to practical QA artifacts: project summaries, role-aware test coverage, execution subsets, browser validation guidance, internal reports, external reports, and Jira-ready defect drafts.

The goal is simple: make requirements-driven QA faster, easier to review, and easier to continue later without re-reading every source document from scratch.

## What QA Compass Does

QA Compass can:

- ingest requirements from Confluence, Jira, markdown, JSON, or pasted text
- search live Jira work items through the Atlassian/Rovo connector when available
- normalize messy source material into canonical QA artifacts
- create a project summary that explains what the product appears to do
- detect user roles and ask for confirmation before coverage is built around them
- propose grouping by feature, module, epic, role, source section, or custom strategy
- generate traceable test cases from requirements
- preserve the embedded test-case generation rules as the quality baseline
- select execution subsets such as smoke, top priority, critical path, rerun failed, or rerun blocked
- generate a pre-execution scope preview and stop for explicit confirmation before browser execution starts
- guide browser validation with `playwright-cli`
- optionally export grouped Playwright `.spec.ts` starter files
- generate internal HTML reports with evidence and artifact legends
- generate cleaner external reports for client or stakeholder sharing
- draft Jira-ready bugs from confirmed failures
- keep reusable QA memory so future runs can continue from existing artifacts

## Why It Exists

Requirements-to-QA work often fails in two predictable ways:

- the AI spends too many tokens rediscovering the same project context every time
- the output looks useful once, but is hard to reuse, trace, or continue

QA Compass is built around reusable artifacts and guided decisions. It asks only the next blocker question, uses scripts for mechanical conversion, and leaves judgment-heavy work to AI: project understanding, test design, readiness analysis, role interpretation, and defect wording.

## Typical Workflow

```text
Source materials
  -> ingest
  -> normalize
  -> project summary
  -> roles and grouping
  -> test cases
  -> optional Playwright starter specs
  -> execution subset
  -> scope preview and confirmation
  -> browser validation
  -> internal and external reports
  -> optional Jira bug drafts
```

You do not need to run every stage every time. QA Compass can start from requirements, existing test cases, execution results, or a specific Jira scope.

## Supported Sources

### Confluence

Use Confluence when requirements live in pages, folders, spaces, or linked product docs. QA Compass preserves page titles, URLs, and source references so generated coverage remains traceable.

Confluence folder URLs are handled as folder inputs, not page IDs. QA Compass prefers connector-based discovery when available, falls back to REST folder children/search, and writes non-sensitive `confluence-intake-diagnostics.json` if discovery is partial or blocked.

### Jira

Use Jira when QA scope lives in current sprint, Ready for QA statuses, issue keys, epics, releases, components, or JQL.

When Atlassian/Rovo is available, QA Compass can use live Jira search instead of requiring a manual export. It can build common JQL plans for:

- Ready for QA style statuses
- current sprint
- custom workflow statuses
- exact issue keys
- epic scope
- release or fixVersion scope
- component scope

### Markdown and PRDs

Use markdown for product specs, PRDs, or local requirement docs.

### JSON

Use JSON when requirements, test cases, or execution results already exist in a structured format.

### Pasted Text

Use pasted text for quick one-off analysis, small specs, or early drafts.

## Generated Artifacts

QA Compass is artifact-first. Important outputs are designed to be reused in later runs.

Common artifacts include:

- `project-summary.md`: AI-generated understanding of what the product appears to do
- `requirements-normalized.json`: canonical requirements
- `confluence-intake-diagnostics.json`: non-sensitive Confluence discovery diagnostics
- `test-cases.json`: source of truth for generated test coverage
- `traceability.json`: requirement-to-test mapping
- `roles.json`: detected and confirmed roles
- `grouping-proposal.json`: feature, module, epic, role, or custom grouping options
- `qa-scope-preview.html`: pre-execution scope review for user confirmation
- `qa-scope-preview.json`: machine-readable selected scope preview
- `qa-scope-preview.md`: readable selected scope preview
- `execution-progress.json`: execution state for continuation
- `remaining-cases.json`: cases not yet executed
- `run-summary.json`: machine-readable execution summary
- `qa-report.internal.html`: detailed team-facing report
- `qa-report.external.html`: stakeholder-facing report
- `qa-report.external.pdf`: optional client snapshot exported from the external HTML report
- `jira-bug-drafts.json`: structured defect drafts
- `jira-bug-drafts.md`: readable defect drafts for review
- `playwright-specs/`: optional starter `.spec.ts` files grouped by scope

Scope previews show selected versus total cases, grouping, priority/type mix, warnings, readiness questions, a grouped selected-case list, and links to the full test-case source. Browser execution should start only after the user confirms the preview and supplies missing environment/access/OTP details.

Internal reports include an expandable generated-files legend with a folder-aware tree, links to generated files, and a short purpose description for every file in the report bundle.

## Reports

QA Compass produces one pre-execution review and two post-execution report styles:

- **Scope preview**: pre-execution HTML/Markdown/JSON review of what will be tested, grouped by the confirmed strategy.
- **Internal report**: detailed QA report for the delivery team, including roles, evidence, executed steps, defects, blockers, and generated artifact links.
- **External report**: cleaner executive-style report for clients and stakeholders, focused on scope, status, key metrics, confirmed defects, and blockers.

HTML reports are the canonical output because they render most predictably. For client sharing, QA Compass can also export a verified PDF snapshot from the external HTML report.

## Jira Defect Flow

QA Compass is intentionally draft-first for Jira writes.

The flow is:

1. Execution results identify confirmed failures.
2. QA Compass creates Jira-ready bug drafts.
3. The user reviews and selects which drafts should become Jira issues.
4. Project-specific required fields are confirmed.
5. Jira issues are created only after explicit confirmation.

This keeps the workflow safe across teams where Jira fields, issue types, linking rules, and bug-reporting conventions differ.

## Token Economy

QA Compass reduces token spend by using scripts and canonical files for mechanical work:

- import and normalize source files
- build JQL plans
- prepare compact test-case generation briefs
- select execution subsets
- render pre-execution scope previews
- render reports
- generate artifact manifests
- draft structured defect payloads

AI is reserved for tasks that need judgment:

- understanding the product
- resolving ambiguous requirements
- identifying roles and business flows
- designing test coverage
- classifying Jira readiness when workflow statuses are unclear
- writing high-quality defect descriptions

## Requirements

- Python 3.10+
- `npm` and `npx`
- Playwright CLI for browser execution

Global Playwright install:

```bash
npm install -g @playwright/cli@latest
playwright-cli --help
playwright-cli install --skills
```

The packaged PDF export helper exports the external report snapshot and supports an `npx` fallback when a global `playwright-cli` is not installed.

## Install

### Codex

Clone the repo, then install into the local Codex skills directory:

```bash
python3 scripts/install_local_skills.py --dest ~/.codex/skills --skill qa-compass
```

### Claude Code

Use the same installer, but point it at Claude Code's skills directory:

```bash
python3 scripts/install_local_skills.py --dest ~/.claude/skills --skill qa-compass
```

### Replace Existing Installed Copies

```bash
python3 scripts/install_local_skills.py --dest ~/.codex/skills --skill qa-compass --overwrite
```

Restart your agent app after installation.

## Install From GitHub

Codex users can install directly with the built-in skill installer after this repo is available on GitHub.

Prompt example:

```text
Use $skill-installer to install qa-compass from <owner>/<repo>.
```

Direct script example:

```bash
python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo <owner>/<repo> \
  --path skills/qa-compass
```

## Quick Start Prompts

Try prompts like:

```text
Use $qa-compass to pull requirements from Confluence and generate full coverage test cases.
```

```text
Use $qa-compass to find Ready for QA issues in Jira project ABC and create a QA plan.
```

```text
Use $qa-compass to analyze the current sprint in Jira, identify what is ready for QA, and generate traceable test cases.
```

```text
Use $qa-compass to normalize this PRD markdown file, summarize the project, confirm roles, and propose test grouping.
```

```text
Use $qa-compass to run the top 5 high-priority cases from this test-cases JSON on staging.
```

```text
Use $qa-compass to turn these execution results into internal and external QA reports.
```

```text
Use $qa-compass to draft Jira bugs for the confirmed defects in this run.
```

## Repo Layout

```text
skills/
  qa-compass/
    SKILL.md
    references/
    scripts/
    templates/
    tests/
scripts/
  install_local_skills.py
  smoke_validate.py
```

## Validation

Run the packaged test suite and build sample artifacts:

```bash
python3 scripts/smoke_validate.py
```

Optional experimental PDF export check:

```bash
python3 scripts/smoke_validate.py --with-pdf
```

Run the skill test suite directly:

```bash
python3 -m unittest discover skills/qa-compass/tests -v
```

## License

MIT. See [LICENSE](LICENSE).
