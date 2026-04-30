# Execution Policy

## Goal

Run the smallest useful subset first, gather strong evidence, and keep result statuses unambiguous.

## Standard Tool

Browser execution must use `playwright-cli`.

Reusable Playwright `.spec.ts` files are optional starter artifacts. They are for reuse and refinement, not a replacement for `playwright-cli` execution inside this workflow.

Execution should reuse canonical artifacts when possible. Prefer existing `03-generated/test-cases.json`, `history/case-history.json`, `execution-progress.json`, and `remaining-cases.json` before regenerating cases or re-ingesting source material.

For repeated QA work, create a fresh run folder before scope preview:

```bash
python3 scripts/workspace_lifecycle.py create-run --root <output-dir> --suite smoke --mode smoke
```

Write execution artifacts under `runs/<run-id>/04-execution/` and reports under `runs/<run-id>/05-reports/`.

Before live browser validation starts, generate `qa-scope-preview.html`, `qa-scope-preview.md`, and `qa-scope-preview.json` from the selected test cases. Then stop and ask the user to confirm that the grouped scope, selected cases, full test-case link, execution readiness questions, and warnings look right. A prior request to `run`, `test`, or `execute` is not confirmation. Do not run browser execution until the user sends a follow-up confirmation after seeing the preview.

```bash
npm install -g @playwright/cli@latest
playwright-cli --help
playwright-cli install --skills
```

## Pre-Execution Confirmation Gate

The scope preview is a hard gate, not a decorative artifact.

At this gate, ask for:

- confirmation that the selected scope and generated cases are correct, or requested changes
- target environment URL when unknown
- test account, role, access path, and required data for authenticated flows
- feature flags, allowlists, seed data, or access constraints that could block execution
- OTP/MFA handling if any selected case mentions OTP, MFA, verification code, email code, SMS code, or magic link

Do not continue into browser execution in the same uninterrupted flow after creating the scope preview.

## OTP/MFA Gate

If a flow requires OTP, MFA, email code, SMS code, or magic link:

- stop before entering or bypassing the code
- ask the user for the current code or confirmation action
- if the user's email or phone receives the code, tell them to check it and wait for the value
- use the value only for the active browser step
- never echo the code back, never store it in artifacts, and never include it in reports
- do not mark the case blocked simply because the user was temporarily away; wait or record the case as paused until the user responds

## Preferred Execution Modes

- `high-priority`
- `smoke`
- `critical-path`
- `rerun-failed`
- `rerun-blocked`
- `full-regression`
- `custom`

## Status Taxonomy

- `Passed`: expected behavior was observed
- `Failed`: product behavior mismatched the expected result
- `Blocked`: execution could not complete because of an external dependency, missing credential, missing data, environment issue, or access problem

Blocked cases are not defects.

## Evidence Requirements

Each executed case should capture:

- test case id and title
- role or roles covered by the case when known
- environment
- executed steps
- status
- expected result for failed cases
- actual result for failed cases
- notes
- screenshot path when meaningful; store it in `evidence`, `screenshot_path`, `screenshots`, or `attachments` so the report bundle can copy it into the internal report
- log references when useful
- console errors when visible
- network or API errors when visible
- browser context when useful: URL, browser, viewport, role, test account
- failure details for `Failed`
- blocker details for `Blocked`

## Subset Selection Rules

- Prioritize `High` before `Medium` before `Low`
- Prefer core functional and critical-path flows first
- Include error-handling cases only when requested or when they belong to the default smoke/high-priority slice
- For rerun modes, use `history/case-history.json` as the authoritative last-status source when available.
- Keep selection deterministic so reruns are easy to compare

## Defect Rule

Create a defect entry only for confirmed behavior mismatches.

A defect entry should include:

- defect id
- linked test case id
- linked requirement ids
- role or roles covered by the failed case when known
- executed steps
- expected result
- actual result
- failure summary
- console errors when captured
- network or API errors when captured
- browser context when relevant
- screenshot or evidence reference

## Continuation Artifacts

When execution is partial, interrupted, blocked, or intentionally batched, preserve:

- `execution-progress.json`
- `remaining-cases.json`
- `history/case-history.json`
- `history/runs-index.json`

These files let a future run continue without spending tokens rediscovering which cases were already handled.
