"""Configuration loaded from environment variables and an optional .env file."""
from __future__ import annotations

import os
from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv
from sqlalchemy import URL

load_dotenv()


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "").strip()
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip()
    openrouter_site_url: str = os.getenv("OPENROUTER_SITE_URL", "").strip()
    openrouter_app_name: str = os.getenv("OPENROUTER_APP_NAME", "AI IT Operations Assistant").strip()

    sqlite_database: str = os.getenv(
        "SQLITE_DATABASE_PATH",
        str(Path(__file__).resolve().parent / "data" / "gold_support.db"),
    ).strip()

    app_host: str = os.getenv("APP_HOST", "127.0.0.1").strip()
    app_port: int = int(os.getenv("APP_PORT", "7860"))
    sql_max_rows: int = min(max(int(os.getenv("SQL_MAX_ROWS", "200")), 1), 1000)
    db_connect_timeout: int = min(max(int(os.getenv("DB_CONNECT_TIMEOUT", "5")), 1), 30)

    def database_url(self) -> URL:
        path = Path(self.sqlite_database).expanduser()
        if not path.is_absolute():
            path = Path(__file__).resolve().parent / path
        path = path.resolve()

        if not path.is_file():
            raise ValueError(
                "SQLite database file was not found. Check SQLITE_DATABASE_PATH."
            )

        return URL.create("sqlite", database=str(path))

    def validate_gemini(self) -> None:
        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is missing. Add your Gemini API key to .env.")
        if not self.gemini_model:
            raise ValueError("GEMINI_MODEL is empty. Set it in .env.")


settings = Settings()

