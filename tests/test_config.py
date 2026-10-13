from pathlib import Path

import pytest

from config import Settings


def test_missing_gemini_key_is_reported():
    settings = Settings(gemini_api_key="", gemini_model="gemini-3.8-flash")
    with pytest.raises(ValueError, match="GEMINI_API_KEY"):
        settings.validate_gemini()


def test_sqlite_database_url_uses_configured_file(tmp_path):
    db_file = tmp_path / "gold_support.db"
    db_file.touch()

    settings = Settings(sqlite_database=str(db_file))
    url = settings.database_url()

    assert url.drivername == "sqlite"
    assert Path(url.database).resolve() == db_file.resolve()


def test_missing_sqlite_database_file_is_reported(tmp_path):
    missing_file = tmp_path / "missing.db"
    settings = Settings(sqlite_database=str(missing_file))

    with pytest.raises(ValueError, match="SQLite database file was not found"):
        settings.database_url()
