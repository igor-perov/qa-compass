---
name: qa-compass
description: Use when requirements, Jira issues, Confluence pages, markdown specs, test cases, or execution results need to become QA artifacts, test coverage, browser validation, internal/external reports, run diagnostics, or Jira-ready defect drafts.
---

# QA Compass

## Overview

This is the flagship QA workflow for turning source materials into reusable QA artifacts.

It is prompt-first where QA judgment is needed, but uses bundled scripts and canonical JSON artifacts to reduce token spend across intake, normalization, project understanding, case generation, optional reusable Playwright spec export, pre-execution scope preview, execution, reporting, and defect drafting.

## When to Use

- Requirements start in Confluence
- Requirements start from a Confluence folder URL
- Requirements start in Jira
- Requirements already exist as JSON
- A PRD or spec exists as markdown
- The user pastes requirements text directly
- The user only wants execution from existing test cases
- The user only wants a report from existing execution results
- The user wants QA Compass run diagnostics or a developer-facing support pack
- The user wants Jira-ready bug drafts from confirmed defects

## Startup Contract

1. Infer the likely source mode and stage with `scripts/detect_start_mode.py`.
2. Resolve the output workspace before ingesting or generating:
   - run `scripts/workspace_lifecycle.py detect --root <output-dir>` when a project artifact folder is available
   - initialize workspace v2 for new projects
   - migrate `legacy_single_run` layouts before continuing, reusing existing `00-03` artifacts
3. Always confirm:
   - what the user wants to produce
   - what the source input is
4. If generating cases from requirements, ask `full coverage or smoke only?` unless the request already answers it.
5. If reusable automation artifacts would help, ask whether grouped Playwright `.spec.ts` starter files are wanted.
6. Ask only the next blocker question.
7. If the source, workspace, and requested outcome are already clear, start immediately.

## Atlassian Connector Rule

When Jira live intake is requested and the Atlassian Rovo connector is available, use connector tools instead of asking the user to export JSON manually.

For Jira reads:

1. Confirm the smallest Jira scope: project/board, current sprint, status set, issue keys, epic, release, component, or JQL.
2. Use `scripts/build_jira_jql.py` when the user gives a structured scope instead of raw JQL.
3. Call `mcp__codex_apps__atlassian_rovo._searchjiraissuesusingjql` with the generated JQL, `cloudId`, requested fields, and max results.
4. Preserve the raw connector response as `jira-work-items.raw.json` when writing artifacts is part of the run.
5. Normalize to `jira-work-items.json` with `scripts/ingest_jira.py`.
6. Let AI classify QA readiness only after raw Jira status, issue type, priority, sprint/release, links, and descriptions are preserved.

For Jira writes:

1. Generate `jira-bug-drafts.json` and `jira-bug-drafts.md` first.
2. Ask which drafts should be created.
3. Ask for project-specific fields if required.
4. Create Jira issues only after explicit confirmation.

## Stage Model

- `ingest`
- `normalize`
- `project-summary`
- `propose-grouping`
- `generate-cases`
- `export-playwright-specs`
- `scope-preview`
- `execute`
- `report`
- `run-diagnostics`
- `draft-defects`
- `create-jira-defects`

Detailed rules live in:
- `references/intake-and-stage-inference.md`
- `references/source-modes.md`
- `references/workflow-help.md`
- `references/sources-confluence.md`
- `references/sources-jira.md`
- `references/project-summary.md`
- `references/artifact-lifecycle.md`
- `references/roles-and-grouping.md`
- `references/jira-defect-drafts.md`
- `references/execution-policy.md`
- `references/reporting.md`

## Hard Rules

- Detect And Protect Secrets: If the user provides an API token, password, session token, bearer token, cookie, OTP, or Atlassian token, never echo it back, never write it to artifacts, recommend rotation if it was exposed in chat, and prefer connector-based auth when available.
- Confluence support stays first-class, but it is optional.
- Confluence folders are first-class inputs. Folder URLs must be treated as `confluence_folder`, not as page IDs.
- For Confluence folders, prefer Atlassian Rovo connector discovery/read when available; if REST folder discovery fails, continue with search fallback before asking the user for exports.
- Jira support stays source-adapter and draft-first; do not create Jira issues without explicit confirmation and project-specific configuration.
- When generating test cases, do not invent a new methodology.
- Use the bundled `references/embedded-test-cases-skill.md` guidance as the quality baseline.
- Use `scripts/prepare_test_case_brief.py` only to reduce token spend and shape inputs.
- When requirements are the source for case generation, explicitly resolve `full coverage` versus `smoke only` before generating the suite.
- Reusable Playwright `.spec.ts` files are optional starter artifacts and should be grouped by feature or module when exported.
- Scope Preview Stop Rule: before browser execution, generate a pre-execution scope preview when test cases or an execution subset are available, share the preview artifact path, and stop. A prior request to `run`, `test`, or `execute` is not confirmation. Do not start browser execution in the same uninterrupted flow after generating the preview; wait for a follow-up user message confirming the scope and cases or requesting changes.
- At the scope-preview gate, ask for every blocker needed for execution: target environment URL if unknown, test account/access details if authenticated flows are in scope, required test data, feature flags/allowlists, and OTP/MFA handling if any selected case can trigger a code or magic link.
- OTP/MFA Gate: if execution reaches an OTP, MFA, email-code, SMS-code, or magic-link step, stop and ask the user for the current code or confirmation flow. If the code is sent to the user's email or phone, tell them it should arrive there and wait for them to provide it. Never echo OTP values back, never store them in artifacts, and do not mark the case blocked simply because the user was temporarily away.
- Every run should preserve reusable QA memory so future runs can reuse canonical artifacts before re-ingesting or regenerating.
- Use workspace v2 for repeated QA work: keep reusable project artifacts in `00-overview`, `01-sources`, `02-normalized`, and `03-generated`; put execution, reports, and evidence for each attempt under `runs/<run-id>/`.
- If an older single-run layout is found, migrate it with `scripts/workspace_lifecycle.py migrate` before doing more work. Do not regenerate requirements, roles, groups, or test cases when reusable artifacts already exist.
- Run Diagnostics Gate: generate `qa-compass-run-diagnostics.md` only when requested or when the user accepts an offer after a run. Before generating the final Markdown, ask whether the user wants to add comments or local observations. Redact secrets from user comments and collected diagnostics.
- Browser execution must use `playwright-cli`.
- Do not generate internal or combined PDF reports by default. Prefer HTML reports as canonical, but always export and verify `qa-report.external.pdf` from `qa-report.external.html` as part of the standard report stage.
- Do not call the report stage complete until `qa-report.external.pdf` exists, unless the user explicitly accepts a development-only `--skip-pdf` exception after a tooling failure.
- Keep report outputs distinct: `qa-report.internal.html` is the detailed team report, `qa-report.external.html` is the client-facing dashboard, and new runs should not create a generic `qa-report.html` alias.
- Internal reports must list passed cases explicitly. When evidence exists, show it inside the related case; when no screenshot/evidence was captured, say that plainly instead of hiding the case.
- Embed only bundled local evidence files in HTML reports. Protected remote screenshot URLs should be rendered as links so private assets do not appear as broken images or access-denied screenshots.
- Generated `.spec.ts` files do not replace `playwright-cli` for live execution inside this skill.
- Prefer canonical JSON artifacts first, then render markdown and HTML from them.
- Keep reusable scripts and templates in this skill folder; create project-local files only for outputs and run artifacts.

## Primary Scripts

- `scripts/detect_start_mode.py`
- `scripts/build_jira_jql.py`
- `scripts/ingest_confluence.py`
- `scripts/ingest_jira.py`
- `scripts/ingest_markdown.py`
- `scripts/import_requirements_json.py`
- `scripts/import_test_cases_json.py`
- `scripts/normalize_requirements.py`
- `scripts/prepare_test_case_brief.py`
- `scripts/propose_grouping.py`
- `scripts/export_playwright_specs.py`
- `scripts/workspace_lifecycle.py`
- `scripts/select_execution_subset.py`
- `scripts/build_scope_preview.py`
- `scripts/build_report_bundle.py`
- `scripts/build_artifact_manifest.py`
- `scripts/build_run_diagnostics.py`
- `scripts/draft_jira_bugs.py`
- `scripts/export_report_pdf.py`

## Compatibility

Use `qa-compass` for the general workflow.
`confluence-qa-orchestrator` is a compatibility wrapper for older Confluence-led starts.
