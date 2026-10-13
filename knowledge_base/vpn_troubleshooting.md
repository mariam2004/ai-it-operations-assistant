---
title: VPN connection troubleshooting basics
source_type: general_it_guidance
approval_status: not_organization_approved
version: starter-1
---
# VPN connection troubleshooting basics

This is general guidance, not an organization-approved runbook. Confirm the exact VPN product and follow the company's approved procedure.

## Start with one safe diagnostic step

Ask whether the issue affects one user/device or multiple users. Record the exact client error, time it began, operating system, VPN client/version, connection type, and recent changes. Do not collect passwords, one-time codes, private keys, or unredacted diagnostic logs.

## Connection timed out

A timeout means the client did not complete a connection within its configured time. It does not by itself prove the VPN gateway is down. First identify the configured VPN server hostname from the approved client profile or help desk configuration. Do not guess a hostname.

When authorized, `nslookup <approved-vpn-hostname>` can check whether DNS resolves the name. A successful DNS lookup does not prove the service is reachable. A failed `ping` alone does not prove the gateway is unavailable because ICMP may be blocked.

If the exact hostname, client, and scope are known, follow the organization's approved network-path test. Do not change DNS, routes, router settings, firewall rules, certificates, or VPN profiles without authorization.

## Escalation evidence

Record the sanitized error, timestamp and timezone, affected scope, client version, whether general internet access works, recent changes, and the relevant sanitized client log lines. Escalate to the network/VPN owner if multiple users are affected or if server-side status is needed.

## Safety

Never disable endpoint protection, bypass MFA, share credentials, or modify company VPN configuration without approved authorization.
