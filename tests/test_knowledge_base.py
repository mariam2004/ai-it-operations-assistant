from __future__ import annotations

import math
from pathlib import Path

import knowledge_base as kb


def test_split_into_chunks_respects_boundaries_and_limit():
    text = ("VPN timeout troubleshooting.\n\n" * 100).strip()
    chunks = kb.split_into_chunks(text, chunk_chars=300, overlap=40)
    assert len(chunks) > 1
    assert all(0 < len(part) <= 300 for part in chunks)


def test_redacts_email_and_common_api_secret():
    secret = "sk-or-v1-" + "A" * 40
    text = f"Contact admin@example.com; GEMINI_API_KEY={secret}"
    redacted = kb.redact_sensitive_text(text)
    assert "admin@example.com" not in redacted
    assert secret not in redacted
    assert "[REDACTED_EMAIL]" in redacted
    assert "[REDACTED_SECRET]" in redacted


def test_load_chunks_marks_unreviewed_files_as_not_approved(tmp_path):
    path = tmp_path / "guide.md"
    path.write_text("# Example\n\nA safe check for VPN timeout.", encoding="utf-8")
    chunks, signature = kb.load_chunks(tmp_path)
    assert signature
    assert chunks
    assert chunks[0]["approval_status"] == "not_organization_approved"
    assert chunks[0]["source"] == "guide.md"


def test_front_matter_metadata_parsed():
    metadata, body = kb._parse_front_matter(
        "---\ntitle: VPN runbook\nsource_type: company_document\napproval_status: approved\n---\nSafe step.",
        "fallback",
    )
    assert metadata["title"] == "VPN runbook"
    assert metadata["source_type"] == "company_document"
    assert metadata["approval_status"] == "approved"
    assert body.strip() == "Safe step."


def test_search_requires_nonempty_query():
    result = kb.search_knowledge_base("  ", directory=Path("/definitely/not/a/real/kb"))
    assert result["ok"] is False
    assert "query" in result["error"].lower()


def test_search_returns_ranked_sources_with_mocked_embeddings(tmp_path, monkeypatch):
    (tmp_path / "vpn.md").write_text(
        "---\ntitle: VPN timeout\nsource_type: general_it_guidance\napproval_status: not_organization_approved\n---\nVPN connection timeout. Check the approved gateway hostname and DNS.",
        encoding="utf-8",
    )
    (tmp_path / "email.md").write_text(
        "---\ntitle: Email sync\n---\nTroubleshoot email synchronization and mailbox access.",
        encoding="utf-8",
    )

    # Deterministic test vectors: the query and VPN text share a direction;
    # the email text is orthogonal. No model download or API is needed.
    def fake_encode(texts):
        vectors = []
        for text in texts:
            lower = text.lower()
            if "email" in lower or "mailbox" in lower:
                vectors.append([0.0, 1.0])
            else:
                vectors.append([1.0, 0.0])
        return vectors

    monkeypatch.setattr(kb, "_encode", fake_encode)
    kb.clear_index_cache()
    result = kb.search_knowledge_base("VPN connection timed out", top_k=2, directory=tmp_path)
    assert result["ok"] is True
    assert result["result_count"] >= 1
    assert result["results"][0]["source"] == "vpn.md"
    assert result["results"][0]["approval_status"] == "not_organization_approved"
    kb.clear_index_cache()


def test_index_ignores_env_and_python_files(tmp_path):
    (tmp_path / ".env").write_text("GEMINI_API_KEY=private", encoding="utf-8")
    (tmp_path / "module.py").write_text("password='dontread'", encoding="utf-8")
    chunks, _ = kb.load_chunks(tmp_path)
    assert chunks == []


def test_cosine_normalized():
    assert math.isclose(kb._cosine_normalized([1.0, 0.0], [1.0, 0.0]), 1.0)
    assert math.isclose(kb._cosine_normalized([1.0, 0.0], [0.0, 1.0]), 0.0)
