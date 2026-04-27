# Jira Source Guidance

## Goal

Use Jira as a source adapter when active QA work lives in Jira issues, statuses, epics, components, or linked Confluence pages.

## Supported Inputs

- local Jira issues JSON export
- live Jira search through Atlassian Rovo `_searchjiraissuesusingjql`
- raw JQL supplied by the user
- status presets such as `Ready for QA`, `Ready for Regression`, `Ready for Release`, and `Done`
- current sprint scope
- exact issue keys
- epic, release, or component scope

## Live Connector Flow

When Atlassian Rovo is available, prefer it over manual JSON export.

1. Confirm `cloudId` or Jira site if missing.
2. Confirm the smallest scope:
   - current sprint
   - Ready for QA style statuses
   - custom statuses
   - issue keys
   - epic
   - release/fixVersion
   - component
   - raw JQL
3. If the user did not provide raw JQL, build the query plan with `scripts/build_jira_jql.py`.
4. Call `mcp__codex_apps__atlassian_rovo._searchjiraissuesusingjql`.
5. Request fields that preserve QA context:
   - `key`
   - `summary`
   - `description`
   - `status`
   - `issuetype`
   - `priority`
   - `parent`
   - `sprint`
   - `fixVersions`
   - `components`
   - `labels`
   - `issuelinks`
   - `updated`
6. If artifacts are being written, save the raw connector response as `jira-work-items.raw.json`.
7. Normalize raw/exported JSON through `scripts/ingest_jira.py` into `jira-work-items.json`.
8. Continue to project summary, readiness analysis, roles/grouping, and test generation.

## Scope Presets

Use `scripts/build_jira_jql.py` for common scopes:

```bash
python3 scripts/build_jira_jql.py --project-key QA --mode ready-for-qa
python3 scripts/build_jira_jql.py --project-key QA --mode current-sprint
python3 scripts/build_jira_jql.py --project-key QA --mode status --status "In QA" --status "QA Review"
python3 scripts/build_jira_jql.py --project-key QA --mode issue-keys --issue-key QA-1 --issue-key QA-2
```

If project workflow statuses are unclear, fetch a broader sprint/release/status set first and let AI classify which issues are actually ready for QA. Do not discard non-ready issues silently; mark them as out-of-scope or needs-confirmation.

## Preservation Rules

Preserve:

- issue key
- summary
- description
- status
- issue type
- priority
- epic
- sprint or fix version when available
- components
- labels
- linked issues
- linked Confluence pages
- updated date

## Source-Of-Truth Rule

Do not assume Jira always overrides Confluence. If Jira and Confluence disagree, mark the possible conflict and ask the user which source-of-truth policy to use for this run.

Default mixed-source behavior:

- Confluence describes intended product behavior.
- Jira defines implementation, sprint, release, and readiness scope.
- Jira descriptions and comments can refine behavior only when the user accepts Jira as a source of truth for that topic.

## Creation Rule

This source adapter only imports Jira content. Jira bug creation belongs to the defect draft workflow and requires explicit user confirmation.

Use `_createjiraissue` only after reviewed drafts are selected and project-specific Jira fields are confirmed.
