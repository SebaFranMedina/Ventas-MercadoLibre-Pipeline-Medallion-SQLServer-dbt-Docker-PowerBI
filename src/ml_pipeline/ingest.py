"""CLI: load one Mercado Libre Excel export into the bronze layer.

    python -m ml_pipeline.ingest data/sample/sample_sales.xlsx [--force]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import bronze
from .config import get_settings
from .excel_reader import read_export
from .pii import pseudonymize


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", help="Excel export (.xlsx)")
    parser.add_argument("--force", action="store_true", help="load even if this exact file was already loaded")
    args = parser.parse_args(argv)

    settings = get_settings()
    path = Path(args.path)
    if not path.exists():
        print(f"File not found: {path}", file=sys.stderr)
        return 2

    print(f"Reading {path} ...")
    df = read_export(path)
    print(f"  {len(df):,} rows, {len(df.columns)} columns")
    df = pseudonymize(df, settings.pii_secret)

    file_hash = bronze.file_sha256(path)
    df = bronze.add_metadata(df, path.name, file_hash, bronze.utc_now())

    bronze.wait_for_server(settings)
    bronze.ensure_database(settings)
    engine = bronze.make_engine(settings)
    bronze.ensure_schema(engine)

    if bronze.already_loaded(engine, file_hash) and not args.force:
        print("This exact file was already loaded (same SHA-256). Skipping. Use --force to reload.")
        return 0

    loaded = bronze.load(engine, df)
    print(f"Loaded {loaded:,} rows into {bronze.BRONZE_SCHEMA}.{bronze.BRONZE_TABLE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
