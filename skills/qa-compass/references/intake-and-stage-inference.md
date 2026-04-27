# Intake and Stage Inference

## Default Intake Style

Use the hybrid intake contract:

1. Infer the likely source mode and stage from the request.
2. Confirm the project goal and source input.
3. If generating cases from requirements, create or refresh the project summary before case generation unless one already exists.
4. Identify candidate roles and grouping strategy before generating or executing test cases.
5. If generating cases from requirements, resolve `full coverage` versus `smoke only` before generation.
6. If reusable automation artifacts would materially help, ask whether grouped Playwright `.spec.ts` starter files are wanted.
7. Ask only the next blocker question.

Do not ask a long setup questionnaire when the request already implies the path.

## Required Confirmation

Always confirm:

- what the user wants to produce
- what the source input is

Examples:

- "Pull requirements from Confluence and generate test cases"
  - goal: test cases
  - source: Confluence
  - next blocker: Confluence access details only if missing, then `full coverage or smoke only?`

- "Run 5 high-priority cases from this JSON on staging"
  - goal: execution
  - source: test-cases JSON
  - next blocker: environment URL or credentials only if missing

- "Make this into a stakeholder report"
  - goal: report
  - source: pasted execution results or result file
  - next blocker: source artifact only if missing

## Stage Heuristics

- `ingest`: request mentions pulling, fetching, parsing, importing, reading source materials
- `normalize`: request mentions structuring, cleaning, tracing, mapping, or converting requirements
- `project-summary`: request mentions product summary, project understanding, product overview, or "what this project does"
- `propose-grouping`: request mentions grouping by feature/module/epic/role/custom scope
- `generate-cases`: request mentions test cases, QA coverage, scenarios, or coverage matrix
- `export-playwright-specs`: request mentions reusable Playwright specs, `.spec.ts`, or starter automation artifacts
- `scope-preview`: request mentions scope preview, pre-execution review, confirm scope, or reviewing cases before execution
- `execute`: request mentions run, test, validate, rerun, browser checks, smoke, top 5, high priority
- `report`: request mentions report, stakeholder summary, html, pdf, defect list, summary
- `draft-defects`: request mentions Jira-ready bug drafts, bug drafts, defect drafts, or drafting tickets from failed results
- `create-jira-defects`: request asks to create Jira bugs after reviewing drafts and explicit Jira configuration is available

## Source Heuristics

- `confluence`: Confluence URL, Atlassian folder/page wording, API token, space/folder/page reference
- `jira`: Jira, JQL, issue keys, Ready for QA, Ready for Regression, sprint, release, Jira issues
- `jira_confluence`: request mentions both Jira scope and Confluence requirements
- `requirements_json`: requirement JSON, traceability JSON, normalized requirements JSON
- `test_cases_json`: test-cases JSON, execution subset, case list to run
- `markdown`: `.md`, PRD, specification, product doc, markdown file
- `pasted_text`: plain pasted requirements without a file

## When to Ask

Ask only if the missing information blocks the next action. Good blocker questions:

- missing environment URL before execution
- missing credentials for authenticated execution
- missing source file or URL
- unresolved `full coverage or smoke only?` before generating from requirements
- unresolved source-of-truth conflict between Jira and Confluence before generating final coverage
- unconfirmed roles or grouping strategy if they materially affect coverage structure
- whether grouped Playwright `.spec.ts` starter files are wanted when the user asks for reusable automation artifacts
- explicit confirmation before creating Jira issues from reviewed bug drafts
- ambiguous target stage with multiple valid interpretations

## When Not to Ask

Do not ask broad questions about all future stages.
Do not ask for Confluence details when the user already supplied JSON or markdown.
Do not ask for credentials before the workflow reaches execution.
Do not ask about Playwright spec export when the user only wants a report or execution run.
Do not create Jira tickets during draft generation.
