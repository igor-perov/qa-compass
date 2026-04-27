# Viking Registration and Stage 1 Intake

## Overview

Users should be able to start valuation onboarding from a public landing page using a work email address only.

## User Roles

- Guest visitor
- Registered user
- Admin reviewer

## Core Flows

### Registration

- User enters a work email on the landing page.
- User submits full name and phone number.
- User receives a one-time verification code by email.
- User enters the code and reaches the company data screen.

### Stage 1

- Registered user opens company data.
- User completes required fields.
- User cannot continue while required fields are empty.

## Acceptance Criteria

- Public email domains must be rejected.
- Invalid verification codes must be rejected.
- Successful verification redirects the user to company data.
- Required company data fields block continuation when empty.

## Business Rules

- OTP expires after 10 minutes.
- Verification codes are numeric and 6 digits long.
- A user may request a new code after the resend timer ends.
