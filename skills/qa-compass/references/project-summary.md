# Project Summary Guidance

## Goal

Create `00-overview/project-summary.md` when QA starts from source requirements.

This file is a human-readable product understanding summary. It is not an execution plan and not a test strategy. A new QA, BA, PM, or engineer should be able to read it and confirm whether the agent understood the product correctly before trusting generated test coverage.

## Creation Rule

This artifact should be AI-generated from normalized source material. Scripts may prepare compact inputs, but the summary itself requires interpretation and should not be reduced to counters.

## Required Sections

- `What This Product Appears To Do`: concise description of the product or feature area.
- `Main User Roles`: detected roles and what each role appears to do.
- `Core Business Flows`: major workflows visible in the requirements.
- `Important Domain Rules`: rules that affect QA coverage or expected behavior.
- `Areas Covered By Requirements`: explicit coverage in the source material.
- `Areas Not Clearly Covered`: unclear, missing, contradictory, or assumed areas.
- `Testing Implications`: what this means for test generation and execution.

## Tone

Write for humans. Be concise, concrete, and transparent about uncertainty.

Use phrases such as `appears to`, `source material indicates`, and `needs confirmation` when the requirements are incomplete.

## Do Not Include

- raw requirement dumps
- long execution steps
- pass/fail metrics
- report dashboard content
- Jira bug drafts

