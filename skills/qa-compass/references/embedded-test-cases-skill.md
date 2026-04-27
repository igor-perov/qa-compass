This guidance remains the authoritative case-generation quality baseline for requirements-qa-orchestrator.

---
name: test-cases
description: This skill should be used when generating comprehensive test cases from PRD documents or user requirements. Triggers when users request test case generation, QA planning, test scenario creation, or need structured test documentation. Produces detailed test cases covering functional, edge case, error handling, and state transition scenarios.
license: MIT
---

# Test Cases Generator

This skill generates comprehensive, requirement-driven test cases from PRD documents or user requirements.

## Purpose

Transform product requirements into structured test cases that ensure complete coverage of functionality, edge cases, error scenarios, and state transitions. The skill follows a pragmatic testing philosophy: test what matters, ensure every requirement has corresponding test coverage, and maintain test quality over quantity.

## When to Use

Trigger this skill when:
- User provides a PRD or requirements document and requests test cases
- User asks to "generate test cases", "create test scenarios", or "plan QA"
- User mentions testing coverage for a feature or requirement
- User needs structured test documentation in markdown format

## Core Testing Principles

Follow these principles when generating test cases:

1. **Requirement-driven, not implementation-driven** - Test cases must map directly to requirements, not implementation details
2. **Complete coverage** - Every requirement must have at least one test case covering:
   - Happy path (normal use cases)
   - Edge cases (boundary values, empty inputs, max limits)
   - Error handling (invalid inputs, failure scenarios, permission errors)
   - State transitions (if stateful, cover all valid state changes)
3. **Clear and actionable** - Each test case must be executable by a QA engineer without ambiguity
4. **Traceable** - Maintain clear mapping between requirements and test cases

## Workflow

### Step 1: Gather Requirements

First, identify the source of requirements:

1. If user provides a file path to a PRD, read it using the Read tool
2. If user describes requirements verbally, capture them
3. If requirements are unclear or incomplete, use AskUserQuestion to clarify:
   - What are the core user flows?
   - What are the acceptance criteria?
   - What are the edge cases or error scenarios to consider?
   - Are there any state transitions or workflows?
   - What platforms or environments need testing?

### Step 2: Extract Test Scenarios

Analyze requirements and extract test scenarios:

1. **Functional scenarios** - Normal use cases from requirements
2. **Edge case scenarios** - Boundary conditions, empty states, maximum limits
3. **Error scenarios** - Invalid inputs, permission failures, network errors
4. **State transition scenarios** - If the feature involves state, map all transitions

For each requirement, identify:
- Preconditions (what must be true before testing)
- Test steps (actions to perform)
- Expected results (what should happen)
- Postconditions (state after test completes)

### Step 3: Structure Test Cases

Organize test cases using this structure:

```markdown
# Test Cases: [Feature Name]

## Overview
- **Feature**: [Feature name]
- **Requirements Source**: [PRD file path or description]
- **Test Coverage**: [Summary of what's covered]
- **Last Updated**: [Date]

## Test Case Categories

### 1. Functional Tests
Test cases covering normal user flows and core functionality.

#### TC-F-001: [Test Case Title]
- **Requirement**: [Link to specific requirement]
- **Priority**: [High/Medium/Low]
- **Preconditions**:
  - [Condition 1]
  - [Condition 2]
- **Test Steps**:
  1. [Step 1]
  2. [Step 2]
  3. [Step 3]
- **Expected Results**:
  - [Expected result 1]
  - [Expected result 2]
- **Postconditions**: [State after test]

### 2. Edge Case Tests
Test cases covering boundary conditions and unusual inputs.

#### TC-E-001: [Test Case Title]
[Same structure as above]

### 3. Error Handling Tests
Test cases covering error scenarios and failure modes.

#### TC-ERR-001: [Test Case Title]
[Same structure as above]

### 4. State Transition Tests
Test cases covering state changes and workflows (if applicable).

#### TC-ST-001: [Test Case Title]
[Same structure as above]

## Test Coverage Matrix

| Requirement ID | Test Cases | Coverage Status |
|---------------|------------|-----------------|
| REQ-001 | TC-F-001, TC-E-001 | ✓ Complete |
| REQ-002 | TC-F-002 | ⚠ Partial |

## Notes
- [Any additional testing considerations]
- [Known limitations or assumptions]
```
