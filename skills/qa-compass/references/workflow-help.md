# Workflow Help

## What QA Compass Can Do

QA Compass can help with:

- importing requirements from Confluence, Jira, markdown, JSON, or pasted text
- searching live Jira work items through the Atlassian connector when available
- normalizing requirements into canonical QA artifacts
- summarizing what the project appears to do
- detecting roles and proposing grouping
- generating requirement-driven test cases
- selecting execution subsets
- generating a pre-execution scope preview for user confirmation
- validating flows with `playwright-cli`
- creating internal and external QA reports
- collecting optional developer-facing run diagnostics after a completed run
- drafting Jira-ready bug reports from confirmed defects
- reusing project memory across repeated smoke, regression, rerun failed, rerun blocked, or custom QA runs

## Stages

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
- `create-jira-defects` optional and confirmation-gated

Before moving from `scope-preview` to `execute`, explicitly ask whether the scope and generated cases are acceptable or should be changed. Treat the preview as a hard stop: a previous `run this` request is not enough. Start browser execution only after the user sends a follow-up confirmation after seeing the preview.

At the same gate, ask for missing environment URL, test accounts/access, required data, feature flags/allowlists, and OTP/MFA handling for flows that send a code or magic link.

After report generation, if the user asks for debug data, support pack, feedback report, or run diagnostics, treat it as `run-diagnostics`. Before generating the Markdown, ask whether they want to add comments about what looked wrong, what they expected, what they did manually, or what local environment detail might matter.

## Repeated QA Runs

Before doing expensive work, detect the workspace layout with `scripts/workspace_lifecycle.py detect --root <output-dir>`.

- New project: initialize workspace v2.
- Existing workspace v2: reuse `00-03`, create a new `runs/<run-id>/` folder for execution/reporting, and update `history/case-history.json` after execution.
- Legacy single-run output: migrate it first, preserving existing sources, normalized requirements, roles, groups, and generated test cases.

For "run smoke again", "full regression", "rerun failed", "rerun blocked", or "test only this group", start from `03-generated/test-cases.json` plus `history/case-history.json`; do not re-ingest Confluence/Jira or regenerate cases unless the user explicitly asks to update coverage.

## Token Economy

Reuse existing canonical artifacts whenever possible. Use scripts for mechanical conversion and AI for interpretation, test design, and defect wording.

## Jira Live Intake Examples

Use Jira live intake when the user says things like:

- "Take current sprint stories and prepare QA coverage"
- "Find Ready for QA issues in project ABC"
- "Use these Jira keys and generate tests"
- "Check release 2.4 scope and draft a QA plan"

When available, use Atlassian Rovo search instead of asking for manual export. Ask for only the next blocker: usually `cloudId`/site, project key, and scope if the prompt does not already include them.

If workflow statuses vary by project, start from current sprint, release, epic, or a broader status set, then classify readiness in the QA analysis instead of pretending every project uses the same status names.
