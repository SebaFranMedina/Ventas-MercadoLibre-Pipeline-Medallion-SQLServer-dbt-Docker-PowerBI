"""Runtime settings, read from environment variables (see .env.example)."""
from __future__ import annotations

import os
import re
from dataclasses import dataclass

_IDENT = re.compile(r"^[A-Za-z0-9_]+$")


@dataclass(frozen=True)
class Settings:
    host: str
    port: int
    user: str
    password: str
    database: str
    driver: str
    pii_secret: str
    reader_password: str


def get_settings() -> Settings:
    password = os.environ.get("MSSQL_SA_PASSWORD")
    secret = os.environ.get("PII_SECRET")
    if not password:
        raise RuntimeError("MSSQL_SA_PASSWORD is not set (copy .env.example to .env).")
    if not secret or secret.startswith("change-me"):
        raise RuntimeError("PII_SECRET is not set or still has the placeholder value (see .env.example).")
    database = os.environ.get("MSSQL_DB", "ventas_ml")
    if not _IDENT.match(database):
        raise RuntimeError("MSSQL_DB may only contain letters, digits and underscores.")
    return Settings(
        host=os.environ.get("DB_HOST", "localhost"),
        port=int(os.environ.get("DB_PORT", "1433")),
        user=os.environ.get("DB_USER", "sa"),
        password=password,
        database=database,
        driver=os.environ.get("ODBC_DRIVER", "ODBC Driver 18 for SQL Server"),
        pii_secret=secret,
        reader_password=os.environ.get("POWERBI_READER_PASSWORD", ""),
    )
