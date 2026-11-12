"""Read the Mercado Libre "Ventas" Excel export.

The export has a title block, then a two-level header (group row + column row).
This module flattens it to unique snake_case column names such as ``ventas_estado``
or ``compradores_estado`` (the same column name appears in several groups).
"""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import pandas as pd

HEADER_MARKER = "# de venta"      # first column of the real header row


def normalize_name(text: object) -> str:
    text = unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-zA-Z0-9]+", "_", text.strip().lower()).strip("_")


def _to_text(value: object) -> str | None:
    """Excel cell -> text. Blank / whitespace-only cells become None."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    text = str(value).strip()
    return text or None


def find_header_row(raw: pd.DataFrame) -> int:
    first_col = raw.iloc[:, 0].astype(str).str.strip()
    hits = raw.index[first_col == HEADER_MARKER]
    if len(hits) == 0 or hits[0] == 0:
        raise ValueError(f"Header row not found: no cell equals '{HEADER_MARKER}' in the first column.")
    return int(hits[0])


def flatten_header(groups: pd.Series, columns: pd.Series) -> list[str]:
    names: list[str] = []
    seen: dict[str, int] = {}
    for group, column in zip(groups.ffill(), columns):
        name = normalize_name(f"{group}_{column}")
        seen[name] = seen.get(name, 0) + 1
        names.append(name if seen[name] == 1 else f"{name}_{seen[name]}")
    return names


def read_export(path: str | Path) -> pd.DataFrame:
    """Return the export as a DataFrame of text columns (None for blanks)."""
    raw = pd.read_excel(path, header=None, dtype=object)
    header_row = find_header_row(raw)
    names = flatten_header(raw.iloc[header_row - 1], raw.iloc[header_row])
    df = raw.iloc[header_row + 1:].copy()
    df.columns = names
    df = df.dropna(how="all").reset_index(drop=True)
    df = df.map(_to_text).astype(object)
    return df.where(df.notna(), None)
