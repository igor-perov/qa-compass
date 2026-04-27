# Roles And Grouping Guidance

## Goal

Roles and grouping make QA coverage reviewable before execution. QA Compass should identify possible roles and report groupings, then ask the user to confirm how testing should be organized.

## Role Layer

Roles are a first-class QA dimension. Do not bury them only inside individual requirements.

When roles are detected, summarize them and ask whether coverage should include all roles or a selected subset.

## Grouping Options

Propose grouping from available source structure:

- `feature`: product module or feature name
- `role`: user role
- `source_section`: top-level source document or section
- `jira_epic`: Jira epic, when available
- `jira_component`: Jira component, when available
- `custom`: user-provided grouping

## Default Recommendation

Use `feature` by default when feature names are available. Prefer `role` only when the user's request is role-driven. Prefer Jira epic/component when the user explicitly asks to follow Jira structure.

## Output Artifacts

- `roles.json`
- `roles-and-groups.md`
- `grouping-proposal.json`

