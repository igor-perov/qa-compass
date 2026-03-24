# Requirements QA Orchestrator Skills

Cross-platform AI skills for turning product requirements into test cases, reusable Playwright starter specs, execution subsets, browser validation, and stakeholder-ready QA reports.

This repo is designed to work well for teams using Codex or Claude Code, especially PMs, BAs, QAs, and engineers who want a guided requirements-to-QA workflow instead of a one-off prompt.

## Included Skills

### `requirements-qa-orchestrator`

The flagship workflow.

Use it when requirements start in:

- Confluence
- requirements JSON
- test-cases JSON
- markdown or PRD files
- pasted text

It helps with:

- guided intake and stage inference
- requirement normalization
- traceable test-case generation
- optional grouped Playwright `.spec.ts` starter export
- execution subset selection
- browser validation with `playwright-cli`
- HTML and PDF QA reporting

### `confluence-qa-orchestrator`

A compatibility wrapper for Confluence-led starts.

Use it when the request is clearly about a Confluence page tree, folder, or space and you want a Confluence-first entry point before continuing with the flagship workflow.

## Why This Repo Exists

Most requirements-to-QA prompting breaks down in one of two ways:

1. it spends too many tokens re-explaining the workflow every time
2. it produces nice-looking artifacts that are not reusable or traceable

This repo is opinionated about fixing both problems.

## What It Optimizes For

- lower token spend through bundled scripts and canonical JSON artifacts
- better first-turn guidance that asks only the next blocker question
- better generation guidance by explicitly resolving `full coverage` versus `smoke only`
- preserved `test-cases` generation rules as a quality baseline
- `playwright-cli` for browser execution and PDF export
- reusable Playwright starter specs when teams want repo-friendly artifacts
- reusable installation across projects and teammates
- outputs that are readable by PM, BA, QA, and engineering stakeholders

## Repo Layout

```text
skills/
  requirements-qa-orchestrator/
  confluence-qa-orchestrator/
scripts/
  install_local_skills.py
  smoke_validate.py
```

## Requirements

- Python 3.9+
- `npm` and `npx`
- Playwright CLI for browser execution and PDF export

Global Playwright install:

```bash
npm install -g @playwright/cli@latest
playwright-cli --help
playwright-cli install --skills
```

The packaged PDF export helper also supports an `npx` fallback when a global `playwright-cli` is not installed.

## Install

### Codex

Clone the repo, then install into the local Codex skills directory:

```bash
python3 scripts/install_local_skills.py --dest ~/.codex/skills
```

Install only the flagship skill:

```bash
python3 scripts/install_local_skills.py \
  --dest ~/.codex/skills \
  --skill requirements-qa-orchestrator
```

### Claude Code

Use the same installer, but point it at Claude Code's skills directory:

```bash
python3 scripts/install_local_skills.py --dest ~/.claude/skills
```

Install only the flagship skill:

```bash
python3 scripts/install_local_skills.py \
  --dest ~/.claude/skills \
  --skill requirements-qa-orchestrator
```

### Replace Existing Installed Copies

```bash
python3 scripts/install_local_skills.py --overwrite
```

Restart your agent app after installation.

## Install From GitHub

### Codex

After pushing this repo to GitHub, Codex users can install directly with the built-in skill installer.

Prompt example:

```text
Use $skill-installer to install requirements-qa-orchestrator and confluence-qa-orchestrator from <owner>/<repo>.
```

Direct script example:

```bash
python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo <owner>/<repo> \
  --path skills/requirements-qa-orchestrator \
  --path skills/confluence-qa-orchestrator
```

### Claude Code

Clone the repo and install to `~/.claude/skills`:

```bash
git clone <repo-url>
cd requirements-qa-orchestrator-skills
python3 scripts/install_local_skills.py --dest ~/.claude/skills
```

Restart your agent app after installation.

## Quick Start

Once installed, good starter prompts include:

- "Pull requirements from Confluence and generate test cases"
- "Pull requirements from Confluence and generate full-coverage test cases plus reusable Playwright specs"
- "Here is a PRD markdown file. Normalize it and create QA coverage"
- "Here is a requirements JSON file. Build traceable QA artifacts"
- "Here is a test-cases JSON file. Run the top 5 high-priority cases on staging"
- "Export grouped Playwright .spec.ts starter files from this test-cases JSON"
- "Turn these execution results into an HTML and PDF stakeholder report"

## Validation

Run the packaged test suite and build a sample HTML report:

```bash
python3 scripts/smoke_validate.py
```

Also verify PDF export:

```bash
python3 scripts/smoke_validate.py --with-pdf
```

## Platform Notes

- Codex users get the smoothest GitHub-based install flow through the built-in skill installer.
- Claude Code users can use this repo cleanly through clone-and-install to `~/.claude/skills`.
- The flagship skill is the recommended default for new users.
- The Confluence wrapper exists for compatibility and Confluence-first workflows, not as the main entry point.

## License

MIT. See [LICENSE](LICENSE).
