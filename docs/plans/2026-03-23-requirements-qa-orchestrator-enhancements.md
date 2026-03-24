# Requirements QA Orchestrator Enhancements Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add optional reusable Playwright spec export, generation-stage coverage prompting, and a clearer default stakeholder report theme with pie-chart metrics.

**Architecture:** Extend the existing prompt-first pipeline without introducing a new mandatory mode. Keep canonical JSON artifacts as the source of truth, add an explicit optional `export-playwright-specs` path from canonical test cases, and upgrade report rendering through the existing HTML/PDF bundle flow.

**Tech Stack:** Python 3, HTML/CSS, Playwright CLI, unittest

---

## Chunk 1: Test-First Contract Updates

### Task 1: Add detection coverage for reusable Playwright spec requests

**Files:**
- Modify: `skills/requirements-qa-orchestrator/skills/requirements-qa-orchestrator/tests/test_detect_start_mode.py`
- Modify: `skills/requirements-qa-orchestrator/skills/requirements-qa-orchestrator/scripts/detect_start_mode.py`

- [ ] **Step 1: Write the failing test**

Add a test that passes text such as `Generate test cases and reusable Playwright spec files from this PRD` and expects:
- `stage == "generate-cases"`
- a new export signal for Playwright specs

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest skills/requirements-qa-orchestrator/tests/test_detect_start_mode.py`
Expected: FAIL because the export signal is not detected yet.

- [ ] **Step 3: Write minimal implementation**

Update `detect_start_mode.py` to detect:
- requests for reusable Playwright specs
- requests using terms like `spec`, `.spec.ts`, `playwright test files`, `reusable Playwright`

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest skills/requirements-qa-orchestrator/tests/test_detect_start_mode.py`
Expected: PASS

### Task 2: Add report rendering assertions for pie-chart and defect clarity

**Files:**
- Modify: `skills/requirements-qa-orchestrator/skills/requirements-qa-orchestrator/tests/test_report_bundle.py`
- Modify: `skills/requirements-qa-orchestrator/skills/requirements-qa-orchestrator/tests/fixtures/sample_execution_results.json`
- Modify: `skills/requirements-qa-orchestrator/skills/requirements-qa-orchestrator/scripts/build_report_bundle.py`
- Modify: `skills/requirements-qa-orchestrator/skills/requirements-qa-orchestrator/templates/report.template.html`

- [ ] **Step 1: Write the failing test**

Assert that generated HTML includes:
- pie-chart markup or config
- execution metadata cards
- defect section content with executed steps and failure description
- evidence references

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest skills/requirements-qa-orchestrator/tests/test_report_bundle.py`
Expected: FAIL because the current report uses a bar chart and simpler layout.

- [ ] **Step 3: Write minimal implementation**

Upgrade `build_report_bundle.py` and `report.template.html` to render:
- default polished template
- pie chart
- clearer defect and blocker sections
- evidence gallery

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest skills/requirements-qa-orchestrator/tests/test_report_bundle.py`
Expected: PASS

## Chunk 2: Reusable Playwright Spec Export

### Task 3: Add exporter tests for grouped `.spec.ts` artifacts

**Files:**
- Create: `skills/requirements-qa-orchestrator/skills/requirements-qa-orchestrator/tests/test_export_playwright_specs.py`
- Modify: `skills/requirements-qa-orchestrator/skills/requirements-qa-orchestrator/tests/fixtures/sample_test_cases.json`
- Create: `skills/requirements-qa-orchestrator/skills/requirements-qa-orchestrator/scripts/export_playwright_specs.py`

- [ ] **Step 1: Write the failing test**

Add a test that exports grouped specs from canonical test cases and asserts:
- grouped filenames like `auth.spec.ts`
- each test title includes the test case ID
- only automation-candidate cases are exported
- requirement IDs remain traceable in output comments or metadata

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest skills/requirements-qa-orchestrator/tests/test_export_playwright_specs.py`
Expected: FAIL because the exporter does not exist yet.

- [ ] **Step 3: Write minimal implementation**

Create `export_playwright_specs.py` that:
- reads canonical `test-cases.json`
- groups cases by feature/module
- writes `.spec.ts` files
- emits starter Playwright tests with traceability comments

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest skills/requirements-qa-orchestrator/tests/test_export_playwright_specs.py`
Expected: PASS

## Chunk 3: Skill and Reference Updates

### Task 4: Update skill instructions for generation-stage prompting and export path

**Files:**
- Modify: `skills/requirements-qa-orchestrator/skills/requirements-qa-orchestrator/SKILL.md`
- Modify: `skills/requirements-qa-orchestrator/skills/requirements-qa-orchestrator/references/intake-and-stage-inference.md`
- Modify: `skills/requirements-qa-orchestrator/skills/requirements-qa-orchestrator/references/reporting.md`
- Modify: `skills/requirements-qa-orchestrator/skills/requirements-qa-orchestrator/references/execution-policy.md`

- [ ] **Step 1: Write the failing review checklist**

Confirm the docs do not yet mention:
- `full coverage or smoke only?` generation question
- optional reusable Playwright `.spec.ts` export
- default polished report theme with pie chart

- [ ] **Step 2: Write minimal documentation updates**

Update the skill and references so they clearly state:
- when to ask the generation-scope question
- when to ask about reusable Playwright specs
- `playwright-cli` remains the execution/PDF tool
- report defaults now use the clearer theme and pie chart

- [ ] **Step 3: Verify docs are internally consistent**

Run:
- `rg -n "smoke only|full coverage|spec.ts|pie chart|playwright-cli" skills/requirements-qa-orchestrator`

Expected:
- required terms appear in the right docs
- no contradictory guidance remains

## Chunk 4: Integration Verification

### Task 5: Run the targeted test suite and smoke validation

**Files:**
- Verify only

- [ ] **Step 1: Run targeted unit tests**

Run:
- `python3 -m unittest skills/requirements-qa-orchestrator/tests/test_detect_start_mode.py`
- `python3 -m unittest skills/requirements-qa-orchestrator/tests/test_report_bundle.py`
- `python3 -m unittest skills/requirements-qa-orchestrator/tests/test_export_playwright_specs.py`
- `python3 -m unittest skills/requirements-qa-orchestrator/tests/test_subset_selection.py`

Expected: PASS

- [ ] **Step 2: Run full repo smoke validation**

Run:
- `python3 scripts/smoke_validate.py`

Expected: PASS

- [ ] **Step 3: Optionally verify PDF export path**

Run:
- `python3 scripts/smoke_validate.py --with-pdf`

Expected: PASS if `playwright-cli` or `npx` is available

- [ ] **Step 4: Review git diff**

Run:
- `git status --short`
- `git diff -- skills/requirements-qa-orchestrator scripts README.md`

Expected: only intended files changed
