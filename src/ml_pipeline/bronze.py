"""Bronze layer: append the (pseudonymised) export to SQL Server as text, plus load metadata."""
from __future__ import annotations

import hashlib
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from .config import Settings

BRONZE_SCHEMA = "bronze"
BRONZE_TABLE = "sales_raw"
TEXT_LENGTH = 4000


def file_sha256(path: str | Path) -> str:
    sha = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            sha.update(chunk)
    return sha.hexdigest()


def add_metadata(df: pd.DataFrame, source_file: str, file_hash: str, loaded_at: datetime) -> pd.DataFrame:
    out = df.copy()
    out["_source_file"] = source_file
    out["_file_hash"] = file_hash
    out["_loaded_at"] = loaded_at
    out["_row_number"] = range(1, len(out) + 1)
    return out


def make_engine(settings: Settings, database: str | None = None, autocommit: bool = False):
    # Imported here so the pure-Python parts of the package can be tested without an ODBC driver.
    from sqlalchemy import create_engine
    from sqlalchemy.engine import URL

    url = URL.create(
        "mssql+pyodbc",
        username=settings.user,
        password=settings.password,
        host=settings.host,
        port=settings.port,
        database=database or settings.database,
        query={"driver": settings.driver, "TrustServerCertificate": "yes"},
    )
    kwargs = {"fast_executemany": True}
    if autocommit:
        kwargs["isolation_level"] = "AUTOCOMMIT"
    return create_engine(url, **kwargs)


def wait_for_server(settings: Settings, attempts: int = 30, delay: float = 2.0) -> None:
    from sqlalchemy import text

    engine = make_engine(settings, database="master")
    last_error: Exception | None = None
    for _ in range(attempts):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return
        except Exception as exc:          # server still starting
            last_error = exc
            time.sleep(delay)
    raise RuntimeError(f"SQL Server not reachable at {settings.host}:{settings.port}: {last_error}")


def ensure_database(settings: Settings) -> None:
    from sqlalchemy import text

    engine = make_engine(settings, database="master", autocommit=True)
    with engine.connect() as conn:
        conn.execute(text(f"IF DB_ID(N'{settings.database}') IS NULL CREATE DATABASE [{settings.database}]"))


def ensure_schema(engine) -> None:
    from sqlalchemy import text

    with engine.begin() as conn:
        conn.execute(text(f"IF SCHEMA_ID(N'{BRONZE_SCHEMA}') IS NULL EXEC('CREATE SCHEMA {BRONZE_SCHEMA}')"))


def table_exists(engine) -> bool:
    from sqlalchemy import inspect

    return inspect(engine).has_table(BRONZE_TABLE, schema=BRONZE_SCHEMA)


def already_loaded(engine, file_hash: str) -> bool:
    from sqlalchemy import text

    if not table_exists(engine):
        return False
    with engine.connect() as conn:
        n = conn.execute(
            text(f"SELECT COUNT(*) FROM {BRONZE_SCHEMA}.{BRONZE_TABLE} WHERE _file_hash = :h"),
            {"h": file_hash},
        ).scalar()
    return bool(n)


def _dtypes(columns: list[str]) -> dict:
    from sqlalchemy.types import DateTime, Integer, NVARCHAR

    types = {c: NVARCHAR(TEXT_LENGTH) for c in columns}
    types.update({"_file_hash": NVARCHAR(64), "_source_file": NVARCHAR(260),
                  "_loaded_at": DateTime(), "_row_number": Integer()})
    return types


def evolve_table(engine, df: pd.DataFrame) -> pd.DataFrame:
    """Align the DataFrame with the existing table: add new columns to the table, NULL-fill missing ones."""
    from sqlalchemy import inspect, text

    existing = [c["name"] for c in inspect(engine).get_columns(BRONZE_TABLE, schema=BRONZE_SCHEMA)]
    new_columns = [c for c in df.columns if c not in existing]
    with engine.begin() as conn:
        for col in new_columns:
            conn.execute(text(f"ALTER TABLE {BRONZE_SCHEMA}.{BRONZE_TABLE} ADD [{col}] NVARCHAR({TEXT_LENGTH}) NULL"))
    out = df.copy()
    for col in existing:
        if col not in out.columns:
            out[col] = None
    return out


def load(engine, df: pd.DataFrame) -> int:
    """Append in a single transaction: either the whole file is loaded or nothing is."""
    if table_exists(engine):
        df = evolve_table(engine, df)
    with engine.begin() as conn:
        df.to_sql(BRONZE_TABLE, conn, schema=BRONZE_SCHEMA, if_exists="append", index=False,
                  dtype=_dtypes(list(df.columns)), chunksize=1000)
    return len(df)


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)
