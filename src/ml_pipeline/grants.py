"""Create a read-only SQL login for Power BI with SELECT on the gold schema only."""
from __future__ import annotations

import sys

from sqlalchemy import text

from .bronze import make_engine
from .config import get_settings

LOGIN = "powerbi_reader"


def main() -> int:
    settings = get_settings()
    if not settings.reader_password:
        print("POWERBI_READER_PASSWORD not set: skipping read-only login (connect as sa for local tests).")
        return 0
    password = settings.reader_password.replace("'", "''")

    master = make_engine(settings, database="master", autocommit=True)
    with master.connect() as conn:
        conn.execute(text(
            f"IF NOT EXISTS (SELECT 1 FROM sys.server_principals WHERE name = N'{LOGIN}') "
            f"CREATE LOGIN [{LOGIN}] WITH PASSWORD = N'{password}', CHECK_POLICY = OFF"
        ))

    db = make_engine(settings, autocommit=True)
    with db.connect() as conn:
        conn.execute(text(
            f"IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = N'{LOGIN}') "
            f"CREATE USER [{LOGIN}] FOR LOGIN [{LOGIN}]"
        ))
        conn.execute(text(f"GRANT SELECT ON SCHEMA::gold TO [{LOGIN}]"))
    print(f"Login '{LOGIN}' can read the gold schema only.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
