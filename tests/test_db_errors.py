import database


def test_connection_status_returns_safe_error(monkeypatch):
    def fail_engine():
        raise RuntimeError("secret password=abc123")
    monkeypatch.setattr(database, "get_engine", fail_engine)
    result = database.connection_status()
    assert result["connected"] is False
    assert "abc123" not in result["message"]


def test_schema_errors_do_not_raise(monkeypatch):
    monkeypatch.setattr(database, "inspect", lambda engine: (_ for _ in ()).throw(RuntimeError("failure")))
    monkeypatch.setattr(database, "get_engine", lambda: object())
    result = database.inspect_schema()
    assert result["ok"] is False
    assert "error" in result
