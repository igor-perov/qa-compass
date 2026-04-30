# Artifact Lifecycle And Reusable QA Memory

## Goal

Every QA Compass run should leave reusable QA memory so future runs can start from existing artifacts instead of re-ingesting and regenerating everything.

## Workspace V2 Layout

Use this structure for real QA work that repeats over time:

```text
qa-compass-output/
  workspace-index.json
  project-profile.json
  00-overview/
  01-sources/
  02-normalized/
  03-generated/
    test-cases.json
    traceability.json
    suites/
    versions/
  runs/
    <run-id>/
      run-config.json
      04-execution/
      05-reports/
      06-diagnostics/
      evidence/
  history/
    runs-index.json
    case-history.json
    migration-report.json
```

`00-03` are project memory. `runs/<run-id>` is one execution attempt. `history` lets future reruns know what passed, failed, or was blocked.

## Reuse Rule

Before ingesting or generating again, check whether canonical artifacts already exist for the requested project and scope.

Prefer reuse when the user wants to continue, rerun, report, draft defects, or execute a new subset.

Use `scripts/workspace_lifecycle.py detect --root <output-dir>` before starting costly work. If it reports `legacy_single_run`, run `scripts/workspace_lifecycle.py migrate --root <output-dir>` and continue from the migrated artifacts.

## Reusable Artifacts

- `workspace-index.json`: workspace v2 index and canonical paths.
- `project-profile.json`: project-level metadata.
- `00-overview/project-summary.md`: product understanding to confirm the agent's interpretation.
- `00-overview/artifact-manifest.json`: machine-readable artifact index.
- `00-overview/artifact-legend.md`: human-readable file legend.
- `01-sources/confluence-intake-diagnostics.json`: non-sensitive diagnostics for Confluence discovery attempts.
- `01-sources/source-index.json`: cross-source map for imported source pages and relationships.
- `02-normalized/requirements-normalized.json`: canonical requirements.
- `02-normalized/roles.json`: detected role layer.
- `02-normalized/grouping-proposal.json`: grouping options and selected grouping.
- `03-generated/test-cases.json`: canonical test cases and source of truth for execution.
- `03-generated/traceability.json`: requirement to test-case mapping.
- `03-generated/reusable-test-plan.md`: compact plan for future runs.
- `03-generated/playwright-specs/`: optional starter Playwright automation files.
- `03-generated/suites/*.json`: named reusable suites such as smoke, full regression, feature groups, or custom selections.
- `03-generated/versions/`: previous canonical test-case versions when coverage is refreshed.
- `runs/<run-id>/run-config.json`: suite/mode/config for one execution attempt.
- `runs/<run-id>/04-execution/qa-scope-preview.html`: pre-execution review of selected scope, groups, warnings, selected cases, and full test-case links.
- `runs/<run-id>/04-execution/qa-scope-preview.json`: machine-readable scope preview payload.
- `runs/<run-id>/04-execution/qa-scope-preview.md`: readable scope preview summary.
- `runs/<run-id>/04-execution/execution-progress.json`: completed, skipped, blocked, and remaining execution state.
- `runs/<run-id>/04-execution/remaining-cases.json`: cases suitable for a later continuation run.
- `runs/<run-id>/05-reports/run-summary.json`: summary metrics and defect/blocker state.
- `runs/<run-id>/05-reports/qa-report.internal.html`: detailed team-facing report.
- `runs/<run-id>/05-reports/qa-report.external.html`: canonical client-facing HTML report.
- `runs/<run-id>/05-reports/qa-report.external.pdf`: required client-shareable PDF snapshot exported from the external HTML report.
- `runs/<run-id>/06-diagnostics/qa-compass-run-diagnostics.md`: developer-facing Markdown handoff for skill feedback and run issues.
- `runs/<run-id>/06-diagnostics/qa-compass-run-diagnostics.json`: machine-readable source payload for the diagnostics report.
- `history/runs-index.json`: run history for repeated QA cycles.
- `history/case-history.json`: latest status and counters per case for rerun failed/blocked flows.

## Token Economy

Use scripts for mechanical work: file indexing, deterministic sorting, subset selection, report rendering, and JSON conversion.

Use AI for judgment work: understanding the product, interpreting requirements, naming groups, generating test cases, explaining conflicts, and writing defect drafts.

## New Run Behavior

For smoke, regression, rerun failed, rerun blocked, or custom group execution:

1. Reuse `03-generated/test-cases.json`, `02-normalized/roles.json`, and `02-normalized/grouping-proposal.json`.
2. Create a fresh run folder with `scripts/workspace_lifecycle.py create-run --root <output-dir> --suite <suite> --mode <mode>`.
3. Use `scripts/select_execution_subset.py --case-history history/case-history.json` for rerun modes.
4. Generate `qa-scope-preview.*` inside `runs/<run-id>/04-execution/`.
5. Stop for user confirmation before browser execution.
6. After execution, update `history/case-history.json` with `scripts/workspace_lifecycle.py update-history`.

Do not put new `04-execution` or `05-reports` folders at the workspace root.

## Run Diagnostics Behavior

After a run is complete, QA Compass may optionally generate a developer-facing diagnostics handoff:

1. Ask the user whether they want to collect QA Compass Run Diagnostics.
2. Before writing the final Markdown, ask whether the user wants to add comments, local observations, suspected skill mistakes, or manual workaround notes.
3. Generate diagnostics with `scripts/build_run_diagnostics.py --workspace-root <output-dir> --run-id <run-id>`.
4. Write `qa-compass-run-diagnostics.md` and `qa-compass-run-diagnostics.json` under `runs/<run-id>/06-diagnostics/`.
5. Redact API tokens, bearer tokens, authorization headers, cookies, passwords, session tokens, and OTP values before writing either file.

The diagnostics report is for the skill developer, not the client. It should summarize run metadata, local context, source/run artifacts, warnings, confirmed defects, blockers, user comments, and links to relevant artifacts.

## Coverage Update Behavior

When requirements or tests need updates:

1. Start from existing `01-sources`, `02-normalized`, and `03-generated/test-cases.json`.
2. Refresh only changed source/requirement areas when possible.
3. Save the previous canonical case file under `03-generated/versions/` before replacing it.
4. Keep stable case IDs when behavior is unchanged.
5. Mark removed or no-longer-applicable cases as retired in a changelog instead of silently deleting context.

Use AI for deciding changed coverage; use scripts for file movement, manifests, and deterministic suite selection.

## Legacy Migration

Older QA Compass outputs may have `04-execution` and `05-reports` at the root beside `00-03`.

When this is detected:

- classify it as `legacy_single_run`
- run `scripts/workspace_lifecycle.py migrate --root <output-dir>`
- keep existing `00-03` artifacts as reusable project memory
- move root-level `04-execution`, `05-report`, or `05-reports` into `runs/<run-id>/`
- write `history/migration-report.json`
- continue from the migrated workspace without re-ingesting or regenerating unless the user requested a coverage refresh

## Resume Behavior

If a user asks to continue a previous run, inspect the manifest and prefer the most specific reusable artifact:

- report request: start from `execution-results.json` or `run-summary.json`
- run diagnostics request: start from `run-config.json`, `run-summary.json`, `execution-results.json`, `workspace-index.json`, and `history/case-history.json`; ask for user comments before writing Markdown
- rerun request: start from `history/case-history.json`, `remaining-cases.json`, `execution-progress.json`, or `03-generated/test-cases.json`
- scope confirmation request: start from `03-generated/test-cases.json`, `execution-subset.json`, `roles.json`, and `grouping-proposal.json`; generate `qa-scope-preview.*`, stop, and wait for a follow-up user confirmation before browser execution
- defect draft request: start from failed cases in `execution-results.json`
- coverage update: start from `requirements-normalized.json` and existing `test-cases.json`
- Confluence folder failure: inspect `01-sources/confluence-intake-diagnostics.json` and continue with connector/search/export fallback instead of retrying the same page fetch.
