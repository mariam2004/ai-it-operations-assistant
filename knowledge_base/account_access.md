---
title: Account access and sign-in troubleshooting
source_type: general_it_guidance
approval_status: not_organization_approved
version: starter-1
---
# Account access and sign-in troubleshooting

This document contains general guidance only. Use the organization's identity and access management runbook for actual account changes.

## First response

Ask which application or sign-in portal is affected, whether one or multiple users are impacted, the exact sanitized error, when the issue began, and whether it follows a password, device, or policy change. Never ask the user to send a password, MFA code, recovery code, or session cookie.

## Safe checks

Confirm the official application URL and that the device date/time are reasonable. Check the approved identity provider's incident/status channel and, if authorized, review account status, lockout, sign-in logs, device compliance and conditional-access results through the organization's approved admin tools.

Use the official identity verification and account recovery workflow. Do not bypass MFA or access policy, share verification codes, or create an alternate account to avoid controls.

## Escalation

Share the timestamp, exact error or correlation ID, application, scope, and sanitized relevant logs with the identity team. Redact personal details not required for diagnosis.
