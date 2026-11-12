"""Pseudonymisation of personal data BEFORE anything reaches the database.

* buyer name, document number and address -> keyed hash (HMAC-SHA256, truncated)
* billing data, tracking numbers/URLs and courier names -> dropped

The hash is stable for a given PII_SECRET, so the same address or buyer always gets the
same id across loads (needed to detect repeated addresses) but cannot be reversed without the secret.
"""
from __future__ import annotations

import hashlib
import hmac
import re

import pandas as pd

HASHED = {
    "compradores_comprador": "buyer_hash",
    "compradores_dni": "document_hash",
    "compradores_domicilio": "address_hash",
}

DROPPED_EXACT = {
    "facturacion_al_comprador_datos_personales_o_de_empresa",
    "facturacion_al_comprador_tipo_y_numero_de_documento",
    "facturacion_al_comprador_direccion",
    "facturacion_al_comprador_numero_iibb",
    "envios_transportista",
    "devoluciones_transportista",
}
DROPPED_TOKENS = ("seguimiento",)          # tracking numbers and tracking URLs

# Raw columns that must never exist in the output.
FORBIDDEN = set(HASHED) | DROPPED_EXACT


def hash_value(value: str | None, secret: str) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    normalized = re.sub(r"\s+", " ", value.strip().lower())
    if not normalized:
        return None
    digest = hmac.new(secret.encode(), normalized.encode(), hashlib.sha256).hexdigest()
    return digest[:16]


def pseudonymize(df: pd.DataFrame, secret: str) -> pd.DataFrame:
    out = df.copy()
    for raw_name, new_name in HASHED.items():
        if raw_name in out.columns:
            out[new_name] = out[raw_name].map(lambda v: hash_value(v, secret))
    drop = [c for c in out.columns if c in FORBIDDEN or any(t in c for t in DROPPED_TOKENS)]
    out = out.drop(columns=drop)
    leaked = FORBIDDEN & set(out.columns)
    if leaked:                                      # defensive: should be impossible
        raise RuntimeError(f"Personal data columns still present: {sorted(leaked)}")
    return out
