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
- drafting Jira-ready bug reports from confirmed defects

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
- `draft-defects`
- `create-jira-defects` optional and confirmation-gated

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
