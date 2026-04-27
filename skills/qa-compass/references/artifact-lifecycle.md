# Artifact Lifecycle And Reusable QA Memory

## Goal

Every QA Compass run should leave reusable QA memory so future runs can start from existing artifacts instead of re-ingesting and regenerating everything.

## Reuse Rule

Before ingesting or generating again, check whether canonical artifacts already exist for the requested project and scope.

Prefer reuse when the user wants to continue, rerun, report, draft defects, or execute a new subset.

## Reusable Artifacts

- `00-overview/project-summary.md`: product understanding to confirm the agent's interpretation.
- `00-overview/artifact-manifest.json`: machine-readable artifact index.
- `00-overview/artifact-legend.md`: human-readable file legend.
- `02-normalized/requirements-normalized.json`: canonical requirements.
- `02-normalized/roles.json`: detected role layer.
- `02-normalized/grouping-proposal.json`: grouping options and selected grouping.
- `03-generated/test-cases.json`: canonical test cases and source of truth for execution.
- `03-generated/traceability.json`: requirement to test-case mapping.
- `03-generated/reusable-test-plan.md`: compact plan for future runs.
- `03-generated/playwright-specs/`: optional starter Playwright automation files.
- `04-execution/execution-progress.json`: completed, skipped, blocked, and remaining execution state.
- `04-execution/remaining-cases.json`: cases suitable for a later continuation run.
- `05-reports/run-summary.json`: summary metrics and defect/blocker state.

## Token Economy

Use scripts for mechanical work: file indexing, deterministic sorting, subset selection, report rendering, and JSON conversion.

Use AI for judgment work: understanding the product, interpreting requirements, naming groups, generating test cases, explaining conflicts, and writing defect drafts.

## Resume Behavior

If a user asks to continue a previous run, inspect the manifest and prefer the most specific reusable artifact:

- report request: start from `execution-results.json` or `run-summary.json`
- rerun request: start from `remaining-cases.json`, `execution-progress.json`, or `test-cases.json`
- defect draft request: start from failed cases in `execution-results.json`
- coverage update: start from `requirements-normalized.json` and existing `test-cases.json`

