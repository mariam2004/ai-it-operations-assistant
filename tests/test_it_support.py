from __future__ import annotations

import pandas as pd

import analytics
from troubleshooting import get_troubleshooting_playbook


def test_playbook_returns_safe_general_guidance():
    result = get_troubleshooting_playbook("network_connectivity", "VPN cannot connect")
    assert result["ok"] is True
    assert result["source_type"] == "general_it_guidance"
    assert result["steps"]
    assert any("Do not reset" in item for item in result["stop_conditions"])


def test_unknown_topic_falls_back_to_initial_triage():
    result = get_troubleshooting_playbook("not_a_topic")
    assert result["topic"] == "unknown"
    assert result["title"] == "Initial IT triage"


def test_support_text_redacts_email_and_phone():
    value = analytics._sanitize_support_text("Contact admin@example.com at +1 202-555-0174")
    assert value is not None
    assert "admin@example.com" not in value
    assert "202-555-0174" not in value
    assert "[email redacted]" in value
    assert "[phone redacted]" in value


def test_search_similar_tickets_uses_bound_parameters_and_redacts(monkeypatch):
    monkeypatch.setattr(analytics, "has_columns", lambda *args: True)
    monkeypatch.setattr(analytics, "_relationship_ok", lambda *args: True)
    captured = {}

    def fake_query_df(sql, params=None):
        captured["sql"] = sql
        captured["params"] = params
        return pd.DataFrame([{
            "ticket_id": 42,
            "issue_description": "VPN cannot connect; contact admin@example.com",
            "resolution_notes": "Checked VPN client; phone +1 202-555-0174 redacted from test",
            "resolution_time_minutes": 36,
            "first_response_time_minutes": 8,
            "reopen_count": 0,
            "escalation_reason": None,
            "category": "Network & Connectivity",
            "issue_type": "VPN Issue",
            "status": "Resolved",
            "priority": "Medium",
            "sla_breached_flag": "No",
        }])

    monkeypatch.setattr(analytics, "query_df", fake_query_df)
    result = analytics.search_similar_tickets("VPN cannot connect")

    assert result["ok"] is True
    assert result["match_count"] == 1
    assert "vpn" in result["search_terms"]
    assert "admin@example.com" not in result["rows"][0]["issue_description"]
    assert "admin@example.com" not in captured["sql"]
    assert any("%vpn%" == value for key, value in captured["params"].items() if key.startswith("term_"))
    assert "customeremail" not in captured["sql"].lower()


def test_get_ticket_for_investigation_rejects_non_integer(monkeypatch):
    result = analytics.get_ticket_for_investigation("not-an-id")
    assert result["ok"] is False
    assert result["found"] is False
    assert "integer" in result["error"]
