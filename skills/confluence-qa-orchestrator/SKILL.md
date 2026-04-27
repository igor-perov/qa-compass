---
name: confluence-qa-orchestrator
description: Use when the request clearly starts from Confluence pages, folders, or spaces and needs a Confluence-led entry point into requirements-driven QA work.
---

# Confluence QA Orchestrator

## Overview

This is a deprecated compatibility wrapper for older Confluence-led starts.

For new work, use `qa-compass` with Confluence as the source mode. QA Compass owns the unified workflow for Confluence, Jira, markdown, JSON, pasted requirements, execution, reporting, and defect drafts.

## What This Wrapper Owns

- Confluence auth guidance
- root page or folder selection
- subtree ingest strategy
- source preservation for downstream traceability

## What It Does Not Own

After ingest, continue with the flagship workflow in `requirements-qa-orchestrator` for:

- stage inference
- normalization
- case generation
- execution subset selection
- browser execution with `playwright-cli`
- HTML/PDF reporting

For new runs, continue with `qa-compass` instead.

## Hard Rules

- Keep Confluence-specific auth/setup help in this wrapper.
- Use the bundled Confluence ingest guidance and helper script for subtree extraction.
- Preserve source URLs and page titles.
- Keep the shared execution and case-generation anchors:
  - `qa-compass`
  - embedded `test-cases` guidance
  - `playwright-cli`

## Default Flow

1. Confirm the Confluence source root.
2. Gather the smallest requirement-bearing subtree that matches the requested scope.
3. Export `confluence-tree.md` and `requirements-raw.json`.
4. Continue the rest of the workflow using `qa-compass`.
