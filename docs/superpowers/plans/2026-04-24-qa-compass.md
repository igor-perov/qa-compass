# QA Compass Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the current requirements QA orchestrator into `qa-compass`, a single QA workflow skill with clearer artifacts, project summaries, roles/grouping, internal/external reports, reusable QA memory, and draft-first Jira defect handling.

**Architecture:** Build from the existing green `skills/qa-compass/` copy of `requirements-qa-orchestrator`. Keep current contracts and tests passing while adding focused scripts, references, templates, and tests. Confluence becomes a source adapter inside the single QA Compass skill; the old Confluence wrapper remains only as temporary compatibility guidance.

**Tech Stack:** Python 3, unittest, markdown templates, HTML/CSS templates, `playwright-cli` for browser execution and PDF export.

---

## Current Baseline

- `skills/qa-compass/` exists as an untracked copy of `skills/requirements-qa-orchestrator/`.
- `diff -qr skills/requirements-qa-orchestrator skills/qa-compass` shows no meaningful differences except ignored local cache files.
- `python3 -m unittest discover skills/qa-compass/tests -v` passes 20 tests.
- `python3 scripts/smoke_validate.py` passes against the original flagship skill.

Do not delete or rewrite existing behavior while adding the new workflow.

## File Structure

### Existing Files To Preserve

- `skills/qa-compass/references/embedded-test-cases-skill.md`: authoritative test-case generation guidance.
- `skills/qa-compass/scripts/prepare_test_case_brief.py`: compact AI input for token efficiency.
- `skills/qa-compass/scripts/export_playwright_specs.py`: optional reusable starter automation artifact export.
- `skills/qa-compass/scripts/select_execution_subset.py`: deterministic subset selection.
- `skills/qa-compass/scripts/build_report_bundle.py`: report bundle generation, to be split/extended.
- `skills/qa-compass/scripts/export_report_pdf.py`: PDF export.

### New Or Modified Files

- Modify: `skills/qa-compass/SKILL.md`
- Modify: `skills/qa-compass/agents/openai.yaml`
- Modify: `skills/qa-compass/scripts/contracts.py`
- Modify: `skills/qa-compass/scripts/detect_start_mode.py`
- Modify: `skills/qa-compass/scripts/build_report_bundle.py`
- Create: `skills/qa-compass/scripts/build_artifact_manifest.py`
- Create: `skills/qa-compass/scripts/propose_grouping.py`
- Create: `skills/qa-compass/scripts/draft_jira_bugs.py`
- Create: `skills/qa-compass/scripts/ingest_jira.py`
- Create: `skills/qa-compass/references/workflow-help.md`
- Create: `skills/qa-compass/references/artifact-lifecycle.md`
- Create: `skills/qa-compass/references/project-summary.md`
- Create: `skills/qa-compass/references/roles-and-grouping.md`
- Create: `skills/qa-compass/references/sources-jira.md`
- Create: `skills/qa-compass/references/sources-confluence.md`
- Create: `skills/qa-compass/references/jira-defect-drafts.md`
- Create: `skills/qa-compass/templates/artifact-legend.template.md`
- Create: `skills/qa-compass/templates/internal-report.template.html`
- Create: `skills/qa-compass/templates/external-report.template.html`
- Create: `skills/qa-compass/templates/jira-bug-drafts.template.md`
- Add tests under `skills/qa-compass/tests/`.
- Modify: `scripts/smoke_validate.py`
- Modify: `scripts/install_local_skills.py`
- Modify: `README.md`

## Chunk 1: Rename Metadata And Preserve Baseline

### Task 1: Make `qa-compass` the primary skill identity

**Files:**
- Modify: `skills/qa-compass/SKILL.md`
- Modify: `skills/qa-compass/agents/openai.yaml`
- Test: `skills/qa-compass/tests/test_detect_start_mode.py`

- [x] **Step 1: Write the failing metadata test**

Add a test that reads `skills/qa-compass/SKILL.md` and asserts:

```python
self.assertIn("name: qa-compass", skill_text)
self.assertIn("# QA Compass", skill_text)
self.assertIn("Jira", skill_text)
```

- [x] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest discover skills/qa-compass/tests -v`

Expected: FAIL because the skill still says `requirements-qa-orchestrator`.

- [x] **Step 3: Update skill metadata**

Set frontmatter:

```yaml
---
name: qa-compass
description: Use when requirements, Jira issues, Confluence pages, markdown specs, test cases, or execution results need to become QA artifacts, test coverage, browser validation, internal/external reports, or Jira-ready defect drafts.
---
```

Update `agents/openai.yaml`:

```yaml
interface:
  display_name: "QA Compass"
  short_description: "Guide QA work from sources to reusable reports"
  brand_color: "#1746A2"
  default_prompt: "Use $qa-compass to turn requirements, Jira issues, Confluence pages, test cases, or execution results into QA artifacts, reports, and defect drafts."
```

- [x] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest discover skills/qa-compass/tests -v`

Expected: PASS.

### Task 2: Update packaging to include `qa-compass`

**Files:**
- Modify: `scripts/install_local_skills.py`
- Modify: `scripts/smoke_validate.py`
- Modify: `README.md`

- [x] **Step 1: Write/update validation expectations**

Update `scripts/smoke_validate.py` so `FLAGSHIP_ROOT` points to `skills/qa-compass`.

Require:

```python
REPO_ROOT / "skills" / "qa-compass" / "SKILL.md"
REPO_ROOT / "skills" / "qa-compass" / "agents" / "openai.yaml"
```

- [x] **Step 2: Update installer skill list**

In `scripts/install_local_skills.py`, add `qa-compass` to installable skills. Keep old skills temporarily if backward compatibility is desired.

- [x] **Step 3: Update README**

Make `qa-compass` the primary skill. Move `requirements-qa-orchestrator` and `confluence-qa-orchestrator` to legacy/compatibility notes.

- [x] **Step 4: Run validation**

Run: `python3 scripts/smoke_validate.py`

Expected: PASS using `skills/qa-compass`.

## Chunk 2: Artifact Manifest And Clear Run Structure

### Task 3: Add artifact manifest builder

**Files:**
- Create: `skills/qa-compass/scripts/build_artifact_manifest.py`
- Create: `skills/qa-compass/templates/artifact-legend.template.md`
- Test: `skills/qa-compass/tests/test_artifact_manifest.py`

- [x] **Step 1: Write failing tests**

Create tests that build a manifest for a temp run directory containing:

```text
00-overview/project-summary.md
03-generated/test-cases.json
05-reports/qa-report.internal.html
```

Assert generated `artifact-manifest.json` entries include:

```json
{
  "path": "03-generated/test-cases.json",
  "label": "Canonical test cases",
  "created_by": "script_or_ai",
  "source_of_truth": true
}
```

Also assert `artifact-legend.md` explains each file.

- [x] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest skills/qa-compass/tests/test_artifact_manifest.py -v`

Expected: FAIL because the script does not exist.

- [x] **Step 3: Implement `build_artifact_manifest.py`**

Implement a deterministic map for known artifact names:

```python
KNOWN_ARTIFACTS = {
    "project-summary.md": ("Project summary", "AI-generated product understanding", False),
    "test-cases.json": ("Canonical test cases", "Source of truth for generated QA coverage", True),
    "traceability.json": ("Traceability map", "Requirement to test-case mapping", True),
    "execution-results.json": ("Execution results", "Machine-readable execution results", True),
    "qa-report.internal.html": ("Internal QA report", "Detailed team-facing report", False),
    "qa-report.external.html": ("External QA report", "Client-facing executive report", False),
    "jira-bug-drafts.json": ("Jira bug drafts", "Draft-first defect payloads", False),
}
```

- [x] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest skills/qa-compass/tests/test_artifact_manifest.py -v`

Expected: PASS.

## Chunk 3: Project Summary And Reusable QA Memory

### Task 4: Add project summary guidance

**Files:**
- Create: `skills/qa-compass/references/project-summary.md`
- Modify: `skills/qa-compass/templates/project-summary.template.md`
- Modify: `skills/qa-compass/SKILL.md`

- [x] **Step 1: Add reference guidance**

Create `references/project-summary.md` explaining that `project-summary.md` is AI-generated and should include:

- what the product appears to do
- main user roles
- core business flows
- important domain rules
- areas covered by requirements
- unclear areas
- testing implications

- [x] **Step 2: Replace technical summary template**

Update `templates/project-summary.template.md` so it is no longer only counts. Keep placeholders for AI-generated sections.

- [x] **Step 3: Update SKILL stage model**

Add `project-summary` after `normalize`.

- [x] **Step 4: Verify docs**

Run: `rg -n "project-summary|What This Product Appears To Do|testing implications" skills/qa-compass`

Expected: The new reference and SKILL stage are discoverable.

### Task 5: Add reusable QA memory guidance

**Files:**
- Create: `skills/qa-compass/references/artifact-lifecycle.md`
- Modify: `skills/qa-compass/references/source-modes.md`
- Modify: `skills/qa-compass/references/execution-policy.md`

- [x] **Step 1: Document reusable artifacts**

List reusable QA memory artifacts:

- `test-cases.json`
- `traceability.json`
- `roles.json`
- `grouping-proposal.json`
- `execution-progress.json`
- `remaining-cases.json`
- optional `playwright-specs/`

- [x] **Step 2: Add reuse rule**

Add rule: reuse existing canonical artifacts before re-ingesting or regenerating.

- [x] **Step 3: Verify references**

Run: `rg -n "reusable QA memory|remaining-cases|execution-progress|playwright-specs" skills/qa-compass/references`

Expected: terms appear in lifecycle and execution docs.

## Chunk 4: Roles And Grouping

### Task 6: Add grouping proposal script

**Files:**
- Create: `skills/qa-compass/scripts/propose_grouping.py`
- Create: `skills/qa-compass/tests/test_propose_grouping.py`
- Create: `skills/qa-compass/references/roles-and-grouping.md`

- [x] **Step 1: Write failing tests**

Use sample requirements with fields:

```json
{
  "feature": "Authentication",
  "roles": ["Admin", "Client"],
  "source_title": "Auth / Login",
  "requirement_id": "AUTH-1"
}
```

Assert `propose_grouping.py` outputs:

- detected roles
- feature groups
- source section groups
- recommended default grouping

- [x] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest skills/qa-compass/tests/test_propose_grouping.py -v`

Expected: FAIL because script does not exist.

- [x] **Step 3: Implement deterministic grouping extraction**

Read `requirements-normalized.json` and produce:

```json
{
  "roles": ["Admin", "Client"],
  "grouping_options": [
    {"type": "feature", "groups": [...]},
    {"type": "role", "groups": [...]},
    {"type": "source_section", "groups": [...]}
  ],
  "recommended": "feature"
}
```

- [x] **Step 4: Run tests**

Run: `python3 -m unittest skills/qa-compass/tests/test_propose_grouping.py -v`

Expected: PASS.

### Task 7: Extend contracts for roles and grouping

**Files:**
- Modify: `skills/qa-compass/scripts/contracts.py`
- Modify: `skills/qa-compass/scripts/prepare_test_case_brief.py`
- Test: `skills/qa-compass/tests/test_import_and_normalize.py`

- [x] **Step 1: Add contract expectations**

Assert project context includes:

- `roles_confirmed`
- `grouping_strategy`
- `source_of_truth_policy`

- [x] **Step 2: Include roles in test-case brief**

Update `prepare_test_case_brief.py` to include roles and business flows when present.

- [x] **Step 3: Run tests**

Run: `python3 -m unittest skills/qa-compass/tests/test_import_and_normalize.py -v`

Expected: PASS.

## Chunk 5: Jira Source And Defect Drafts

### Task 8: Add Jira source mode scaffolding

**Files:**
- Create: `skills/qa-compass/references/sources-jira.md`
- Create: `skills/qa-compass/scripts/ingest_jira.py`
- Modify: `skills/qa-compass/scripts/detect_start_mode.py`
- Modify: `skills/qa-compass/scripts/contracts.py`
- Test: `skills/qa-compass/tests/test_detect_start_mode.py`

- [x] **Step 1: Add failing detection tests**

Assert:

```python
payload = detect_start_mode("Use Jira Ready for QA issues and generate test cases")
self.assertEqual(payload["source_mode"], "jira")
```

Also test mixed source:

```python
payload = detect_start_mode("Use Confluence requirements and linked Jira Done issues")
self.assertEqual(payload["source_mode"], "jira_confluence")
```

- [x] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest skills/qa-compass/tests/test_detect_start_mode.py -v`

Expected: FAIL.

- [x] **Step 3: Implement detection and contracts**

Add `jira` and `jira_confluence` source modes.

- [x] **Step 4: Add `ingest_jira.py` dry-run/import shape**

For the first iteration, support importing a local Jira issues JSON fixture into canonical source records. Leave real API connection documented/config-driven.

- [x] **Step 5: Run tests**

Run: `python3 -m unittest skills/qa-compass/tests/test_detect_start_mode.py -v`

Expected: PASS.

### Task 9: Add Jira bug draft generation

**Files:**
- Create: `skills/qa-compass/scripts/draft_jira_bugs.py`
- Create: `skills/qa-compass/templates/jira-bug-drafts.template.md`
- Create: `skills/qa-compass/references/jira-defect-drafts.md`
- Create: `skills/qa-compass/tests/test_draft_jira_bugs.py`

- [x] **Step 1: Write failing tests**

Use sample execution results with one failed case. Assert JSON draft includes:

- summary/title
- priority suggestion
- environment
- linked test case ID
- linked requirement IDs
- steps to reproduce
- expected result
- actual result
- evidence paths

- [x] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest skills/qa-compass/tests/test_draft_jira_bugs.py -v`

Expected: FAIL because script does not exist.

- [x] **Step 3: Implement draft generator**

Read `execution-results.json` or current sample payload and write:

- `jira-bug-drafts.json`
- `jira-bug-drafts.md`

Do not create Jira issues in this task.

- [x] **Step 4: Run tests**

Run: `python3 -m unittest skills/qa-compass/tests/test_draft_jira_bugs.py -v`

Expected: PASS.

## Chunk 6: Internal And External Reports

### Task 10: Split report templates

**Files:**
- Modify: `skills/qa-compass/scripts/build_report_bundle.py`
- Create: `skills/qa-compass/templates/internal-report.template.html`
- Create: `skills/qa-compass/templates/external-report.template.html`
- Modify: `skills/qa-compass/references/reporting.md`
- Test: `skills/qa-compass/tests/test_report_bundle.py`

- [x] **Step 1: Update failing report tests**

Assert report bundle writes:

- `qa-report.internal.html`
- `qa-report.external.html`
- `run-summary.json`

Assert internal report contains:

- `Generated Files`
- `<details`
- evidence gallery
- executed steps

Assert external report contains:

- executive dashboard
- counts
- confirmed defect summary
- no full evidence gallery

- [x] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest skills/qa-compass/tests/test_report_bundle.py -v`

Expected: FAIL because current script writes only `qa-report.html`.

- [x] **Step 3: Implement split rendering**

Keep old `qa-report.html` temporarily as alias or redirect copy if needed for compatibility.

- [x] **Step 4: Run tests**

Run: `python3 -m unittest skills/qa-compass/tests/test_report_bundle.py -v`

Expected: PASS.

### Task 11: Add artifact legend into internal report

**Files:**
- Modify: `skills/qa-compass/scripts/build_report_bundle.py`
- Modify: `skills/qa-compass/templates/internal-report.template.html`
- Test: `skills/qa-compass/tests/test_report_bundle.py`

- [x] **Step 1: Add test assertion**

Assert internal HTML includes:

```html
<details
Generated files and artifact legend
test-cases.json
```

- [x] **Step 2: Implement legend rendering**

Use manifest entries if `artifact-manifest.json` exists. Otherwise render known report artifacts.

- [x] **Step 3: Run tests**

Run: `python3 -m unittest skills/qa-compass/tests/test_report_bundle.py -v`

Expected: PASS.

## Chunk 7: Compatibility And Cleanup

### Task 12: Make Confluence wrapper deprecated

**Files:**
- Modify: `skills/confluence-qa-orchestrator/SKILL.md`
- Modify: `README.md`

- [x] **Step 1: Update wrapper guidance**

Change body to say this is a compatibility wrapper and new work should use `qa-compass` with Confluence source mode.

- [x] **Step 2: Keep install compatibility**

Do not delete the folder until users have migrated.

- [x] **Step 3: Verify discoverability**

Run: `rg -n "qa-compass|deprecated|compatibility" skills/confluence-qa-orchestrator README.md`

Expected: wrapper and README both point to QA Compass.

### Task 13: Remove external companion skill recommendations

**Files:**
- Modify: `skills/qa-compass/SKILL.md`
- Modify: `README.md`

- [x] **Step 1: Verify no default recommendations**

Run: `rg -n "TestDino|Jenny|task-completion|ultrathink|Currents" skills/qa-compass README.md`

Expected: no default workflow dependency on these skills.

- [x] **Step 2: Keep Playwright CLI only**

Ensure `playwright-cli` remains documented as the browser execution and PDF export tool.

## Chunk 8: Final Verification

### Task 14: Run full test and smoke suite

**Files:**
- Verify only

- [x] **Step 1: Run qa-compass tests**

Run: `python3 -m unittest discover skills/qa-compass/tests -v`

Expected: PASS.

- [x] **Step 2: Run smoke validation**

Run: `python3 scripts/smoke_validate.py`

Expected: PASS and smoke validation uses `skills/qa-compass`.

- [ ] **Step 3: Optional PDF validation**

Run: `python3 scripts/smoke_validate.py --with-pdf`

Expected: PASS if `playwright-cli` or `npx` is available.

- [x] **Step 4: Review diffs**

Run:

```bash
git status --short
git diff -- README.md scripts skills docs
```

Expected: only intended files changed.

Result: tracked diffs are README, install/smoke scripts, and the Confluence compatibility wrapper. `git status` also shows the new untracked `skills/qa-compass/` skill folder and the new design/implementation docs.

- [x] **Step 5: Installation smoke check**

Run:

```bash
python3 scripts/install_local_skills.py --dest /tmp/qa-compass-install --skill qa-compass --overwrite
find /tmp/qa-compass-install/qa-compass -maxdepth 2 -type f | sort
```

Expected: `SKILL.md`, `agents/openai.yaml`, references, scripts, templates, and tests are copied.

## Execution Notes

- Keep commits small: one chunk or one task per commit.
- Keep `embedded-test-cases-skill.md` intact unless there is a deliberate update to test-case generation policy.
- Treat Jira issue creation as a later, confirmation-gated feature. Draft generation comes first.
- Do not make generated Playwright `.spec.ts` files mandatory. They are reusable starter artifacts, not finished automated tests.
- If a change risks breaking old users, preserve an alias or compatibility wrapper for one release.

## Follow-Up Chunk: Jira Live Intake Via Atlassian Connector

### Task 15: Add Jira live search planning

**Files:**
- Create: `skills/qa-compass/scripts/build_jira_jql.py`
- Create: `skills/qa-compass/tests/test_build_jira_jql.py`
- Modify: `skills/qa-compass/SKILL.md`
- Modify: `skills/qa-compass/references/sources-jira.md`
- Modify: `skills/qa-compass/references/workflow-help.md`
- Modify: `scripts/smoke_validate.py`

- [x] **Step 1: Add failing tests for common Jira scopes**

Cover Ready for QA, current sprint, exact issue keys, and custom statuses.

- [x] **Step 2: Implement JQL planner**

Build a deterministic query plan that names `mcp__codex_apps__atlassian_rovo._searchjiraissuesusingjql`, fields, max results, and JQL.

- [x] **Step 3: Document connector-first Jira intake**

Teach `qa-compass` to use Atlassian Rovo for live Jira reads when available and fall back to local JSON export only when connector access is unavailable.

- [x] **Step 4: Extend smoke validation**

Require and execute the Jira JQL planner in `scripts/smoke_validate.py`.
