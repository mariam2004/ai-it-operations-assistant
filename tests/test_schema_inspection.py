import database


class FakeInspector:
    def get_table_names(self):
        return ["facttickets", "dimdate"]

    def get_columns(self, table):
        if table == "facttickets":
            return [{"name": "TicketKey", "type": "INTEGER", "nullable": False}]
        return [{"name": "DateKey", "type": "INTEGER", "nullable": False}]

    def get_pk_constraint(self, table):
        return {"constrained_columns": ["TicketKey"] if table == "facttickets" else ["DateKey"]}

    def get_foreign_keys(self, table):
        return []

    def get_indexes(self, table):
        return []


def test_inspect_schema_uses_reflected_metadata(monkeypatch):
    monkeypatch.setattr(database, "inspect", lambda engine: FakeInspector())
    monkeypatch.setattr(database, "get_engine", lambda: object())
    result = database.inspect_schema()
    assert "facttickets" in result["tables"]
    assert result["tables"]["facttickets"]["columns"][0]["name"] == "TicketKey"
    assert "dimcustomer" in result["missing_expected_tables"]
    assert result["ok"] is False


def test_schema_inspection_failure_is_safe(monkeypatch):
    def broken_inspect(_engine):
        raise RuntimeError("hidden database failure")
    monkeypatch.setattr(database, "inspect", broken_inspect)
    monkeypatch.setattr(database, "get_engine", lambda: object())
    result = database.inspect_schema()
    assert result["ok"] is False
    assert "error" in result
    assert "password" not in result["error"].lower()
