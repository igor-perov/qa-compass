# Confluence Source Guidance

## Goal

Use Confluence as a source adapter when requirements live in a page, page tree, folder, or space.

## Required Inputs

- Confluence base URL
- Atlassian account email
- API token
- root page or folder reference

## Outputs

- `01-sources/confluence-tree.md`
- `01-sources/requirements-raw.json`
- source references preserved for traceability

## Scope Rule

Gather the smallest requirement-bearing subtree that matches the requested QA scope. Do not pull an entire space if a page tree is enough.

## Unified Workflow Rule

After Confluence ingest, continue through `qa-compass` stages for normalization, project summary, grouping, test-case generation, execution, reporting, and optional defect drafts.

