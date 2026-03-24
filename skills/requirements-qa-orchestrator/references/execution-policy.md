# Execution Policy

## Goal

Run the smallest useful subset first, gather strong evidence, and keep result statuses unambiguous.

## Standard Tool

Browser execution and PDF export must use `playwright-cli`.

Reusable Playwright `.spec.ts` files are optional starter artifacts. They are for reuse and refinement, not a replacement for `playwright-cli` execution inside this workflow.

```bash
npm install -g @playwright/cli@latest
playwright-cli --help
playwright-cli install --skills
```

## Preferred Execution Modes

- `high-priority`
- `smoke`
- `critical-path`
- `rerun-failed`
- `rerun-blocked`

## Status Taxonomy

- `Passed`: expected behavior was observed
- `Failed`: product behavior mismatched the expected result
- `Blocked`: execution could not complete because of an external dependency, missing credential, missing data, environment issue, or access problem

Blocked cases are not defects.

## Evidence Requirements

Each executed case should capture:

- test case id and title
- environment
- executed steps
- status
- notes
- screenshot path when meaningful
- log references when useful
- failure details for `Failed`
- blocker details for `Blocked`

## Subset Selection Rules

- Prioritize `High` before `Medium` before `Low`
- Prefer core functional and critical-path flows first
- Include error-handling cases only when requested or when they belong to the default smoke/high-priority slice
- Keep selection deterministic so reruns are easy to compare

## Defect Rule

Create a defect entry only for confirmed behavior mismatches.

A defect entry should include:

- defect id
- linked test case id
- linked requirement ids
- executed steps
- failure summary
- screenshot or evidence reference
