---
name: requirements-qa-orchestrator
description: Use when requirements need to be turned into test cases, execution subsets, browser validation, or QA reports from Confluence, JSON, markdown, or pasted text.
---

# Requirements QA Orchestrator

## Overview

This is the flagship requirements-to-QA workflow.

It is prompt-first, but uses bundled scripts and canonical JSON artifacts to reduce token spend across intake, normalization, case generation, optional reusable Playwright spec export, execution, and reporting.

## When to Use

- Requirements start in Confluence
- Requirements already exist as JSON
- A PRD or spec exists as markdown
- The user pastes requirements text directly
- The user only wants execution from existing test cases
- The user only wants a report from existing execution results

## Startup Contract

1. Infer the likely source mode and stage with `scripts/detect_start_mode.py`.
2. Always confirm:
   - what the user wants to produce
   - what the source input is
3. If generating cases from requirements, ask `full coverage or smoke only?` unless the request already answers it.
4. If reusable automation artifacts would help, ask whether grouped Playwright `.spec.ts` starter files are wanted.
5. Ask only the next blocker question.
6. If the source and requested outcome are already clear, start immediately.

## Stage Model

- `ingest`
- `normalize`
- `generate-cases`
- `export-playwright-specs`
- `execute`
- `report`

Detailed rules live in:
- `references/intake-and-stage-inference.md`
- `references/source-modes.md`
- `references/execution-policy.md`
- `references/reporting.md`

## Hard Rules

- Confluence support stays first-class, but it is optional.
- When generating test cases, do not invent a new methodology.
- Use the bundled `references/embedded-test-cases-skill.md` guidance as the quality baseline.
- Use `scripts/prepare_test_case_brief.py` only to reduce token spend and shape inputs.
- When requirements are the source for case generation, explicitly resolve `full coverage` versus `smoke only` before generating the suite.
- Reusable Playwright `.spec.ts` files are optional starter artifacts and should be grouped by feature or module when exported.
- Browser execution and PDF export must use `playwright-cli`.
- Generated `.spec.ts` files do not replace `playwright-cli` for live execution inside this skill.
- Prefer canonical JSON artifacts first, then render markdown and HTML from them.
- Keep reusable scripts and templates in this skill folder; create project-local files only for outputs and run artifacts.

## Primary Scripts

- `scripts/detect_start_mode.py`
- `scripts/ingest_confluence.py`
- `scripts/ingest_markdown.py`
- `scripts/import_requirements_json.py`
- `scripts/import_test_cases_json.py`
- `scripts/normalize_requirements.py`
- `scripts/prepare_test_case_brief.py`
- `scripts/export_playwright_specs.py`
- `scripts/select_execution_subset.py`
- `scripts/build_report_bundle.py`
- `scripts/export_report_pdf.py`

## Compatibility

Use `requirements-qa-orchestrator` for the general workflow.
Use `confluence-qa-orchestrator` only when the user is clearly starting from Confluence and wants the Confluence-led entry point.
