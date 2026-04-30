# Reporting Guidance

## Goal

Produce a stakeholder-ready report that quickly shows scope, quality, blockers, defects, and evidence in a clear executive dashboard style.

## Required Outputs

Pre-execution scope review:

- `runs/<run-id>/04-execution/qa-scope-preview.html`
- `runs/<run-id>/04-execution/qa-scope-preview.md`
- `runs/<run-id>/04-execution/qa-scope-preview.json`

Post-execution reporting:

- `runs/<run-id>/05-reports/execution-plan.md`
- `runs/<run-id>/05-reports/execution-results.md`
- `runs/<run-id>/05-reports/run-summary.json`
- `runs/<run-id>/05-reports/qa-report.internal.html`
- `runs/<run-id>/05-reports/qa-report.external.html`
- `runs/<run-id>/05-reports/qa-report.external.pdf`

Optional developer diagnostics:

- `runs/<run-id>/06-diagnostics/qa-compass-run-diagnostics.md`
- `runs/<run-id>/06-diagnostics/qa-compass-run-diagnostics.json`

HTML remains the canonical report format. Always export `qa-report.external.pdf` from `qa-report.external.html` as the client-shareable snapshot and verify the rendered PDF before sharing it.

For legacy single-run outputs, these files may exist at the old root-level `04-execution` or `05-reports` paths. Migrate before adding new execution or report artifacts.

## HTML Quality Bar

The scope preview should make the upcoming execution easy to approve before testing starts:

- selected versus total test cases
- grouping strategy and grouped scope sections
- priority and type mix
- compact selected-case list by group
- link to the full `test-cases.json` source for detailed case review
- warnings for missing requirement links, missing expected results, missing role attachment, or excluded cases

The internal report should be visibly stronger than a raw dump. Prefer:

- a clean default visual style with an executive header and environment metadata
- summary cards
- a pie chart near the top for pass / fail / blocked distribution
- execution results grouped by the confirmed grouping strategy, with case ID, title, roles, priority, duration, and status
- blocked section
- defect section with failure summary, expected result, actual result, executed steps, diagnostics, and evidence
- passed-cases section with each passed case, its roles, executed steps, and evidence when captured
- copied local screenshot files when results contain `evidence`, `screenshot_path`, `screenshots`, or attachment artifacts; protected remote screenshot URLs should stay as links instead of broken embedded images
- an expandable generated-files legend near the top with links to run artifacts and reusable workspace artifacts, plus a short description for each file

The external report should be presentation-ready and concise:

- executive dashboard first
- only the metrics needed to understand the run
- confirmed defect summary
- blocked-case summary
- no full evidence gallery unless the user asks for detailed evidence

The run diagnostics report is different from internal/external QA reporting. It is a developer-facing handoff for improving QA Compass itself. Generate it only on request or after user confirmation, ask for user comments first, and redact secrets before writing Markdown or JSON.

## Defect and Blocker Handling

- blocked cases stay in a blocked section
- failed cases may become defect cards
- do not convert blocked cases into defects

For each defect include:

- title
- linked test case
- linked requirement ids
- roles covered by the failed case when known
- steps executed
- expected result
- actual result
- failure description
- console errors if captured
- network or API errors if captured
- browser context if relevant
- screenshot path if available
- evidence reference if available

## PDF Export

Do not export internal or combined PDFs by default. Always export only the external report snapshot as `qa-report.external.pdf`, and still keep `qa-report.external.html` as the canonical deliverable.

If PDF tooling fails, keep the HTML reports and explain the failure, but do not treat reporting as fully complete until the PDF is generated or the user explicitly accepts a development-only skip.

Before sharing the PDF, verify:

- the first page shows the dashboard without clipped edges
- charts and KPI cards fit within page margins
- issue cards do not split awkwardly when possible
- text remains readable at print scale
- screenshots or evidence links remain available in the HTML bundle when detailed evidence is needed

```bash
npm install -g @playwright/cli@latest
playwright-cli --help
playwright-cli install --skills
```

## Reader Outcome

A PM, BA, QA lead, or engineer should understand in under a minute:

- what was tested
- what passed
- what failed
- what was blocked
- what needs follow-up
- where the screenshots or evidence live
