# Source Modes

## Goal

Support multiple start modes without forcing everything through Confluence.

## Supported Modes

### `confluence`

Use when requirements live in an Atlassian page tree.

Required for ingest:
- page URL or page ID
- connector access when available, otherwise base URL, user email, and API token

Outputs:
- `confluence-tree.md`
- `requirements-raw.json`
- `source-index.json`
- `confluence-intake-diagnostics.json`

### `confluence_folder`

Use when requirements start from a Confluence folder URL such as `/wiki/spaces/{spaceKey}/folder/{folderId}`.

Required for ingest:
- folder URL
- connector access when available, otherwise base URL, user email, and API token

Rules:
- do not treat folder IDs as page IDs
- prefer Atlassian Rovo connector discovery/read when available
- fall back to REST folder children discovery, then space/page search
- write non-sensitive diagnostics even when no pages are fetched

Outputs:
- `confluence-tree.md`
- `requirements-raw.json`
- `source-index.json`
- `confluence-intake-diagnostics.json`

### `jira`

Use when requirements, completed stories, ready-for-QA issues, or regression scope start in Jira.

Required for live connector work:
- Jira project or board context
- JQL, issue keys, sprint, release, epic, or status filter
- explicit confirmation before any write action

Safe local import:
- exported Jira JSON file

Preserve:
- issue keys
- statuses
- issue types
- epics, sprints, components, labels
- linked issues
- source URLs

Output:
- canonical Jira source package for normalization

### `jira_confluence`

Use when Confluence pages describe the product behavior and Jira issues define implementation or ready-for-QA scope.

Required:
- Confluence source details
- Jira source details or exported JSON
- source-of-truth policy if the same requirement appears in both systems

Default source-of-truth policy:
- Confluence explains intended behavior.
- Jira narrows implemented/released scope.
- Conflicts are surfaced and held for user confirmation before test generation.

### `requirements_json`

Use when normalized or semi-structured requirements already exist in JSON.

Required:
- input file path or pasted JSON

Preserve:
- source references
- requirement ids if stable
- acceptance criteria and business rules

Output:
- canonical `requirements-normalized.json`

### `test_cases_json`

Use when cases already exist and the task starts at execution or reporting.

Required:
- input file path or pasted JSON

Preserve:
- test case ids
- linked requirement ids
- priority
- preconditions, steps, expected results

Output:
- canonical `test-cases.json`

### `markdown`

Use for PRDs, specs, or markdown files.

Required:
- input file path

Output:
- `requirements-raw.json`

### `pasted_text`

Use when the user pastes requirement text directly in the chat.

Required:
- pasted content

Output:
- `requirements-raw.json`

## Canonical Import Rule

Normalize every non-canonical source into the internal artifact shapes before asking the model to do expensive reasoning.

## Reuse Rule

Before ingesting the same scope again, check for reusable QA memory artifacts described in `artifact-lifecycle.md`.

If canonical artifacts already exist and the user wants to continue, execute, report, or draft defects, start from those artifacts instead of re-reading every source.

## Skip Rules

- Skip Confluence questions if the source is JSON, markdown, or pasted text.
- Skip Jira write/setup questions when the user only wants bug drafts or local JSON import.
- Skip normalization if canonical normalized requirements already exist and the user wants execution or reporting.
- Skip case generation if test cases are already supplied.
