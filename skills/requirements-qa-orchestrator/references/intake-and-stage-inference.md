# Intake and Stage Inference

## Default Intake Style

Use the hybrid intake contract:

1. Infer the likely source mode and stage from the request.
2. Confirm the project goal and source input.
3. If generating cases from requirements, resolve `full coverage` versus `smoke only` before generation.
4. If reusable automation artifacts would materially help, ask whether grouped Playwright `.spec.ts` starter files are wanted.
5. Ask only the next blocker question.

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
- `generate-cases`: request mentions test cases, QA coverage, scenarios, or coverage matrix
- `export-playwright-specs`: request mentions reusable Playwright specs, `.spec.ts`, or starter automation artifacts
- `execute`: request mentions run, test, validate, rerun, browser checks, smoke, top 5, high priority
- `report`: request mentions report, stakeholder summary, html, pdf, defect list, summary

## Source Heuristics

- `confluence`: Confluence URL, Atlassian folder/page wording, API token, space/folder/page reference
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
- whether grouped Playwright `.spec.ts` starter files are wanted when the user asks for reusable automation artifacts
- ambiguous target stage with multiple valid interpretations

## When Not to Ask

Do not ask broad questions about all future stages.
Do not ask for Confluence details when the user already supplied JSON or markdown.
Do not ask for credentials before the workflow reaches execution.
Do not ask about Playwright spec export when the user only wants a report or execution run.
