# Reporting Guidance

## Goal

Produce a stakeholder-ready report that quickly shows scope, quality, blockers, defects, and evidence in a clear executive dashboard style.

## Required Outputs

Pre-execution scope review:

- `qa-scope-preview.html`
- `qa-scope-preview.md`
- `qa-scope-preview.json`

Post-execution reporting:

- `execution-plan.md`
- `execution-results.md`
- `run-summary.json`
- `qa-report.internal.html`
- `qa-report.external.html`
- `qa-report.html` as a temporary compatibility alias for the internal report
- optional `qa-report.external.pdf` client snapshot

HTML remains the canonical report format. When the user needs a client-shareable attachment, export `qa-report.external.pdf` from `qa-report.external.html` as a snapshot and verify the rendered PDF before sharing it.

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
- evidence panels with copied local screenshot files when results contain `evidence`, `screenshot_path`, `screenshots`, or attachment artifacts
- an expandable generated-files legend near the top with a folder-aware tree, links to every generated file in the bundle, and a short description for each file

The external report should be presentation-ready and concise:

- executive dashboard first
- only the metrics needed to understand the run
- confirmed defect summary
- blocked-case summary
- no full evidence gallery unless the user asks for detailed evidence

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

Do not export internal or combined PDFs by default. For client sharing, export only the external report snapshot as `qa-report.external.pdf` when requested, and still keep `qa-report.external.html` as the canonical deliverable.

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
