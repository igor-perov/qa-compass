# Jira Defect Drafts Guidance

## Goal

After execution and reporting, QA Compass may prepare Jira-ready bug drafts for confirmed failed cases.

## Draft-First Rule

Never create Jira issues immediately. First generate `jira-bug-drafts.md` and `jira-bug-drafts.json`, then ask the user to review and confirm.

## Selection Prompt

Ask which defects to draft:

- all confirmed defects
- only critical/high priority defects
- selected defect IDs or test case IDs
- none

## Required Draft Fields

- summary
- issue type suggestion
- priority
- environment
- linked test case ID
- linked requirement IDs
- steps to reproduce
- expected result
- actual result
- evidence paths
- notes

## Jira Creation Rule

Only create Jira issues if the user explicitly confirms and project-specific Jira configuration exists. Do not guess required fields, workflows, links, or whether the defect should be a new issue or a comment on an existing issue.

