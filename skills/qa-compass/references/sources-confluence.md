# Confluence Source Guidance

## Goal

Use Confluence as a source adapter when requirements live in a page, page tree, folder, or space.

## Required Inputs

- Confluence base URL
- root page or folder reference
- connector access, when available
- Atlassian account email and API token only when connector access is unavailable

## Outputs

- `01-sources/confluence-tree.md`
- `01-sources/requirements-raw.json`
- `01-sources/source-index.json`
- `01-sources/confluence-intake-diagnostics.json`
- source references preserved for traceability

## Folder URL Rule

Confluence folder URLs are first-class inputs:

- `/wiki/spaces/{spaceKey}/folder/{folderId}`
- `/spaces/{spaceKey}/folder/{folderId}`

Classify these as `confluence_folder`. Do not treat the folder ID as a page ID and do not call page-body fetch logic on the folder ID. Folder IDs and page IDs can look similar but behave differently.

Normal page URLs remain `confluence_page`, including:

- `/wiki/spaces/{spaceKey}/pages/{pageId}/...`
- `/spaces/{spaceKey}/pages/{pageId}/...`
- pasted page IDs when the user explicitly identifies them as pages

## Folder Fallback Order

When the source is a Confluence folder:

1. Prefer Atlassian Rovo connector discovery/read if connector data is available in the session.
2. If connector discovery is unavailable, use `scripts/ingest_confluence.py` REST folder children discovery.
3. If REST folder children discovery fails or returns no pages, fall back to space/page search using the parsed `spaceKey`.
4. If all methods fail, keep partial artifacts and produce diagnostics explaining what was tried.

Failed REST folder lookup should not block the run if connector/search can retrieve the pages.

## Diagnostics Rule

Always preserve non-sensitive intake diagnostics at:

`01-sources/confluence-intake-diagnostics.json`

The diagnostics should include:

- input URL
- parsed base URL
- parsed space key
- parsed folder ID or page ID
- detected source type
- discovery methods attempted
- method status
- non-sensitive error summary
- discovered page count
- fetched page count
- warnings

Never include API tokens, authorization headers, cookies, OTPs, bearer tokens, session tokens, or Atlassian tokens in diagnostics, logs, or generated artifacts.

If all methods fail, ask the user for one of:

- connector access to the Confluence folder/pages
- a direct page URL instead of a folder URL
- exported page HTML/Markdown/JSON
- a list of child page URLs from the folder

## Scope Rule

Gather the smallest requirement-bearing subtree that matches the requested QA scope. Do not pull an entire space if a page tree is enough.

## Unified Workflow Rule

After Confluence ingest, continue through `qa-compass` stages for normalization, project summary, grouping, test-case generation, execution, reporting, and optional defect drafts.
