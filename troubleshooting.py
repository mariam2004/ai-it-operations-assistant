"""Safe, read-only IT troubleshooting playbooks for support engineers."""
from __future__ import annotations

from typing import Any

PLAYBOOKS: dict[str, dict[str, Any]] = {
    "network_connectivity": {
        "title": "Network / Wi-Fi / VPN connectivity",
        "steps": [
            "Confirm scope: one user/device, one location, or multiple users. Check the approved service-status/incident channel first.",
            "Identify the path affected: office network, Wi-Fi, wired Ethernet, VPN, or one specific application.",
            "Check the device's connection state and whether other approved internal services work. Ask for the exact error and when it began.",
            "If permitted by local support policy, collect read-only diagnostics such as ipconfig /all, ping to the approved gateway, or nslookup for the affected hostname. Redact public IPs or internal hostnames before sharing outside the IT team.",
            "Compare with a known-good device/network and check recent network, VPN, DNS, or certificate changes before escalating with evidence.",
        ],
        "collect": ["affected user/device and location", "Wi-Fi/Ethernet/VPN path", "exact error", "start time and scope", "approved diagnostic output"],
        "stop_conditions": ["Do not reset network adapters, change DNS/routes, disable endpoint protection, or restart shared network equipment without authorization."],
    },
    "account_access": {
        "title": "Account access / sign-in / MFA",
        "steps": [
            "Confirm the exact application/SSO URL and whether the problem affects one user or several users.",
            "Capture the error text and timestamp; check approved identity-provider status, lockout, and conditional-access logs.",
            "Check keyboard layout/caps lock and whether the account format is correct without asking the user to disclose a password.",
            "For MFA problems, use the organization's approved recovery or re-registration workflow and verify identity according to policy.",
            "Escalate with the error/correlation ID and timestamp if the account, device compliance, or identity-provider policy blocks access.",
        ],
        "collect": ["application/SSO URL", "error text or correlation ID", "timestamp", "one or multiple users", "MFA method affected (never the code)"],
        "stop_conditions": ["Never ask for passwords, OTPs, recovery codes, session cookies, or API keys. Do not bypass MFA or access controls."],
    },
    "email_access": {
        "title": "Email access / sync / sending and receiving",
        "steps": [
            "Clarify whether the issue is sign-in, sending, receiving, search, attachments, or synchronization.",
            "Check whether webmail and the desktop/mobile client behave differently and whether other users are affected.",
            "Check connectivity, approved mail-service status, mailbox quota, and any displayed bounce or sync error.",
            "Record the time, client/version, affected action, and message ID if available; do not collect message content unless policy authorizes it.",
            "If only one client is affected, follow the approved client repair/re-profile procedure; confirm backup/synchronization status before destructive changes." 
        ],
        "collect": ["webmail vs app", "send/receive/sync symptom", "exact error", "time and affected scope", "redacted bounce/message ID"],
        "stop_conditions": ["Do not request user passwords or full email contents. Do not delete/recreate profiles or mail data until synchronization and backup are verified."],
    },
    "software_installation": {
        "title": "Software installation / update",
        "steps": [
            "Confirm application name/version, OS version, install source, and exact error code.",
            "Check the approved software catalog, license/entitlement, compatibility, free disk space, and pending restart.",
            "Review relevant installer logs after removing usernames, tokens, license keys, and other sensitive values.",
            "Use the approved managed deployment or service-desk elevation workflow; compare with another managed device if available.",
            "Escalate with installer version, error code, timestamp, and sanitized log excerpt if installation repeatedly fails.",
        ],
        "collect": ["application/version", "OS/build", "error code", "install source", "sanitized installer log"],
        "stop_conditions": ["Do not bypass application controls, disable antivirus/EDR, use untrusted installers, or request an administrator password."],
    },
    "security_incident": {
        "title": "Potential security incident / phishing / suspected compromise",
        "steps": [
            "Treat unexpected credential prompts, suspicious attachments, unusual sign-ins, and EDR alerts as potential incidents until triaged.",
            "Do not click links, open attachments, forward suspicious files broadly, or enter credentials into the suspect page.",
            "Preserve evidence such as timestamps, sender/subject, alert ID, and endpoint name using approved reporting procedures.",
            "Report promptly to the security/incident-response team. Isolate a device only according to the organization's incident-response policy or explicit responder instruction.",
            "Follow incident-response direction and keep actions/timestamps documented; do not wipe, reimage, or delete logs before evidence is preserved.",
        ],
        "collect": ["alert/ticket ID", "timestamp", "device identifier", "what was clicked/executed", "security tool alert text"],
        "stop_conditions": ["Never disable EDR/antivirus, delete evidence, run unapproved cleanup tools, or enter/share credentials or MFA codes."],
    },
    "device_performance": {
        "title": "Slow laptop / application performance",
        "steps": [
            "Find whether the slowdown affects one application or the whole device, and whether it started after an update or change.",
            "Save work, then inspect CPU, memory, disk utilization, free disk space, and approved endpoint-health status.",
            "Compare with a known-good device and check managed update/incident status; note the time and workload when the problem occurs.",
            "A normal application restart or device restart may be considered after saving work and checking that it will not interrupt critical operations.",
            "Collect sanitized event/application logs and escalate if resource usage stays high or there are disk/thermal/EDR warnings.",
        ],
        "collect": ["device/OS", "one app vs whole device", "when it started", "CPU/RAM/disk indicators", "recent updates and sanitized logs"],
        "stop_conditions": ["Do not delete user data, terminate unfamiliar security/management processes, disable protection, or make registry changes without authorization."],
    },
    "application_error": {
        "title": "Application error / unexpected behavior",
        "steps": [
            "Capture the exact error, affected function, timestamp, application/version, and whether the issue is reproducible.",
            "Determine scope: one user, one device, one region, or multiple users. Check the approved application status page/incident channel.",
            "Try a safe comparison such as another approved browser/session or a known-good device, if policy permits.",
            "Check recent release/configuration changes and collect sanitized logs or correlation IDs.",
            "Escalate with reproduction steps, impact, timestamp, and evidence; do not infer root cause from a similar historical ticket alone.",
        ],
        "collect": ["application and version", "exact error", "scope/impact", "timestamp", "reproduction steps", "recent changes"],
        "stop_conditions": ["Do not paste tokens, cookies, customer records, passwords, or unredacted logs into the assistant."],
    },
    "printer_peripheral": {
        "title": "Printer / peripheral issue",
        "steps": [
            "Confirm the printer/device, connection type, exact error, and whether one or multiple users are affected.",
            "Check power, physical connection, paper/consumables, and device status without opening hardware beyond authorized procedures.",
            "Check the print queue or device status and send a test job if permitted; identify whether the issue follows a user or endpoint.",
            "Verify approved driver/version and print-server status; record the queue name and error code.",
            "Escalate with device/queue identifier, timestamp, scope, and sanitized error details if the issue persists.",
        ],
        "collect": ["device/queue", "connection type", "error code", "scope", "driver/version"],
        "stop_conditions": ["Do not install drivers from unofficial sites or change shared print-server configuration without authorization."],
    },
    "unknown": {
        "title": "Initial IT triage",
        "steps": [
            "Identify the service/application/device and what the user was trying to do.",
            "Ask for the exact error text (remove usernames, email addresses, tokens, and other sensitive data).",
            "Determine the impact and scope: one user/device or multiple users; when it started; whether anything changed recently.",
            "Record troubleshooting steps already tried and whether the issue is still reproducible.",
            "Choose the matching approved IT playbook after the problem domain is clear; check incident status before making changes.",
        ],
        "collect": ["service/device", "expected vs actual behavior", "exact sanitized error", "start time and scope", "recent changes", "steps already tried"],
        "stop_conditions": ["Do not request passwords, MFA codes, API keys, cookies, or unredacted customer data. Avoid destructive or privileged changes without approval."],
    },
}


def get_troubleshooting_playbook(topic: str, symptoms: str = "") -> dict[str, Any]:
    """Return safe, general IT guidance; this is not database-derived evidence."""
    key = (topic or "unknown").strip().lower()
    playbook = PLAYBOOKS.get(key, PLAYBOOKS["unknown"])
    return {
        "ok": True,
        "source_type": "general_it_guidance",
        "topic": key if key in PLAYBOOKS else "unknown",
        "title": playbook["title"],
        "reported_symptoms": (symptoms or "")[:400],
        "steps": list(playbook["steps"]),
        "information_to_collect": list(playbook["collect"]),
        "stop_conditions": list(playbook["stop_conditions"]),
        "note": "General troubleshooting guidance only. Follow the organization's approved runbooks and escalation policy. This tool does not verify the environment or perform any change.",
    }
