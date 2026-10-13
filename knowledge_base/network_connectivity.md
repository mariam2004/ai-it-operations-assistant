---
title: Network connectivity initial checks
source_type: general_it_guidance
approval_status: not_organization_approved
version: starter-1
---
# Network connectivity initial checks

This is generic IT guidance and is not a company-approved runbook.

## Clarify scope first

Determine whether one device, one user, several users, or a whole site is affected. Capture the exact error, start time, connection method (Wi-Fi or Ethernet), and recent changes. Ask whether public internet access works and which internal service fails.

## Safe local checks

On Windows, `ipconfig /all` shows the current network configuration. Review the output locally and share only sanitized portions; it can contain device and network identifiers. `nslookup <approved-hostname>` tests DNS name resolution. Test a hostname supplied by the organization's approved documentation, not an invented address.

A failed ping is not conclusive because hosts and firewalls may block ICMP. Use approved diagnostic tools and compare a known-good device/network only when policy permits.

## Avoid unsafe changes

Do not reset adapters, modify DNS or static routes, disable firewall/EDR, restart shared equipment, or change switch/router configuration without authorization and an approved change procedure.

## Escalation

Provide the scope, timestamps, exact sanitized errors, tests attempted and outcomes, OS/device type, and recent changes. Do not include passwords, tokens, cookies, or unnecessary personal data.
