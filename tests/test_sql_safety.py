import pytest
import database


def set_reflected_schema(monkeypatch):
    monkeypatch.setattr(database, "_column_metadata", lambda: {
        "facttickets": {"ticketkey", "ticketid", "ticketstatekey", "issuekey", "createdatkey", "flagskey", "resolvedbykey"},
        "dimticketstate": {"ticketstatekey", "status", "priority"},
        "dimissue": {"issuekey", "category", "issuetype"},
        "dimdate": {"datekey", "fulldate", "yearnumber", "monthnumber"},
    })


def test_allows_select_from_approved_schema(monkeypatch):
    set_reflected_schema(monkeypatch)
    query = database.validate_readonly_sql(
        "SELECT s.Status AS status, COUNT(*) AS ticket_count "
        "FROM facttickets f JOIN dimticketstate s ON f.TicketStateKey = s.TicketStateKey "
        "GROUP BY s.Status"
    )
    assert "SELECT" in query.upper()
    assert "LIMIT" in query.upper()


@pytest.mark.parametrize("query", [
    "DELETE FROM facttickets",
    "UPDATE facttickets SET TicketId = 3",
    "DROP TABLE facttickets",
    "SELECT * FROM facttickets; DELETE FROM facttickets",
    "SELECT LOAD_FILE('/etc/passwd') FROM facttickets",
    "SELECT * FROM information_schema.tables",
    "SELECT * FROM nti_support_dwh.facttickets",
    "SELECT * FROM facttickets",
    "SELECT CustomerEmail FROM dimcustomer",
    "SELECT * FROM facttickets UNION SELECT * FROM dimcustomer",
])
def test_rejects_unsafe_sql(monkeypatch, query):
    set_reflected_schema(monkeypatch)
    with pytest.raises(ValueError):
        database.validate_readonly_sql(query)


def test_rejects_unknown_column(monkeypatch):
    set_reflected_schema(monkeypatch)
    with pytest.raises(ValueError, match="could not be verified"):
        database.validate_readonly_sql("SELECT private_email FROM facttickets")
