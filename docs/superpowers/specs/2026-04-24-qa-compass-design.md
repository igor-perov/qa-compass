# QA Compass Design Spec

## Purpose

QA Compass is the next version of the existing requirements QA orchestrator. It keeps the current requirements-to-QA pipeline intact, but makes the workflow easier to understand, easier to resume, and more useful for real project QA work.

The skill should guide a user from source materials to reusable QA artifacts, browser validation, internal/external reports, and optional Jira-ready defect drafts.

## Non-Negotiable Compatibility

QA Compass must preserve the current working feature set:

- source intake from Confluence, requirements JSON, test-cases JSON, markdown/PRD files, and pasted text
- stage detection through `detect_start_mode.py`
- canonical requirement and test-case JSON contracts
- `embedded-test-cases-skill.md` as the authoritative test-case generation baseline
- `prepare_test_case_brief.py` as the token-saving bridge between normalized requirements and AI generation
- full/smoke generation scope prompting
- grouped Playwright `.spec.ts` starter export
- deterministic execution subset selection
- `playwright-cli` as the browser execution and PDF export tool
- report bundle generation
- existing unit tests and smoke validation

The initial `skills/qa-compass/` folder is a copy of the current flagship skill and passes the copied test suite. All new work should build from that green baseline.

## Architecture

QA Compass should be one public skill: `qa-compass`.

Confluence should no longer be a separate public orchestrator. It becomes a source adapter inside QA Compass, alongside Jira, markdown, JSON, and pasted text. The old `confluence-qa-orchestrator` may stay temporarily as a deprecated compatibility wrapper that redirects users to `qa-compass` with `source_mode=confluence`.

The skill remains prompt-first where human judgment is needed, and script-first where work is mechanical:

- scripts handle ingestion, canonicalization, artifact manifests, deterministic selection, report rendering, and PDF export
- AI handles product understanding, project summary writing, requirement interpretation, test-case generation, risk analysis, conflict explanation, and defect draft wording

## Workflow

The expanded stage model is:

1. `ingest`
2. `normalize`
3. `project-summary`
4. `propose-grouping`
5. `generate-cases`
6. `export-playwright-specs`
7. `execute`
8. `report`
9. `draft-defects`
10. `create-jira-defects` optional

Users should be able to ask what the skill can do, what stage they are in, which files were generated, and how to resume from existing artifacts.

## Artifact Structure

Runs should use a clearer folder structure:

```text
qa_runs/<run-id>/
  00-overview/
    project-summary.md
    artifact-legend.md
    artifact-manifest.json
  01-sources/
    requirements-raw.json
    confluence-tree.md
    jira-issues.json
    source-index.json
  02-normalized/
    requirements-normalized.json
    requirements-normalized.md
    roles.json
    roles-and-groups.md
    grouping-proposal.json
  03-generated/
    test-cases.json
    test-cases.md
    traceability.json
    coverage-gaps.md
    reusable-test-plan.md
    playwright-specs/
  04-execution/
    execution-plan.md
    execution-subset.json
    execution-results.json
    execution-results.md
    execution-progress.json
    remaining-cases.json
    evidence/
  05-reports/
    run-summary.json
    qa-report.internal.html
    qa-report.internal.pdf
    qa-report.external.html
    qa-report.external.pdf
    jira-bug-drafts.md
    jira-bug-drafts.json
```

Not every run creates every file. The manifest should explain what exists, what created it, and how it should be used.

## Project Summary

`project-summary.md` must become a human-readable AI-generated product summary, not a technical counter page.

It should describe:

- what the product appears to do
- main user roles
- core business flows
- important domain rules
- areas covered by source requirements
- areas not clearly covered
- testing implications

This helps a new QA, BA, PM, or engineer verify that the agent understood the project before trusting generated test coverage.

## Roles And Grouping

Roles are a first-class QA dimension. QA Compass should detect roles from source materials, show them to the user, and ask for confirmation when role coverage affects test generation.

Grouping should be proposed before execution or reporting when enough source information exists. Supported grouping dimensions:

- feature/module
- user role
- Jira epic
- Jira component
- Confluence section
- custom user grouping

The selected grouping should influence test-case organization, execution planning, internal report sections, and external report summaries.

## Reports

QA Compass should produce separate reports for separate audiences.

The external report is a polished client-facing dashboard. It should be short, presentable, and focused on the useful executive view: scope, environment, pass/fail/blocked counts, confirmed defects, critical blockers, and next steps.

The internal report is an audit/debugging artifact. It should include generated file legend, source links, role coverage, grouping, executed steps, evidence, screenshots, skipped cases, blockers, and defect details.

The internal report must include an expandable generated-files legend with links to artifacts and explanations for what each file means.

## Reusable QA Memory

Every run should preserve reusable QA memory so future runs start from existing artifacts instead of re-ingesting and regenerating everything.

Reusable artifacts include:

- canonical test cases
- traceability mapping
- roles and grouping
- execution history
- remaining cases
- reusable test plan
- optional grouped Playwright starter specs

Grouped Playwright `.spec.ts` files remain optional. They are useful as starter automation artifacts, but they are not required for every project and should not be presented as finished automated tests.

## Jira Support

Jira has two roles:

1. source intake, for requirements and ready-for-QA work
2. post-report defect drafting and optional issue creation

Jira source support should read issues using status presets or custom JQL, preserve issue keys and links, and map Jira content into the source index.

Defect handling is draft-first:

1. after reports, ask whether the user wants Jira bug drafts
2. ask whether to draft all confirmed defects, selected defects, or only critical/high defects
3. write `jira-bug-drafts.md` and `jira-bug-drafts.json`
4. only create Jira issues after explicit confirmation
5. require `jira-project-config.json` before automatic issue creation

QA Compass must not guess required Jira fields or silently create issues/comments.

## Source Freshness And Conflicts

QA Compass should add a basic, transparent source freshness layer without trying to be too clever.

It should mark possible stale or conflicting source information and ask the user to choose a source-of-truth policy when needed. It should not automatically resolve serious Confluence/Jira conflicts.

## Out Of Scope For This Version

Do not add these companion skills to the default workflow:

- TestDino
- Jenny
- task-completion-validator
- ultrathink-debugger
- Currents

They may be reconsidered later if the team starts testing with codebase access or deeper automation needs.

## Success Criteria

- `qa-compass` is the primary public skill name and entry point.
- Existing tests copied from `requirements-qa-orchestrator` keep passing.
- The old functionality remains available.
- New artifacts make the generated files understandable.
- Internal and external reports serve different audiences.
- Jira bug handling is safe, draft-first, and confirmation-driven.
- Future runs can reuse previous QA artifacts to reduce token spend.
