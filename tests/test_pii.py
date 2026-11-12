from pathlib import Path

import pandas as pd

from ml_pipeline import excel_reader, pii

SAMPLE = Path(__file__).resolve().parents[1] / "data" / "sample" / "sample_sales.xlsx"


def test_hash_is_stable_and_normalised():
    a = pii.hash_value("Av. Siempre Viva 123", "k")
    b = pii.hash_value("  av.  siempre viva 123 ", "k")
    assert a == b and len(a) == 16


def test_hash_depends_on_secret():
    assert pii.hash_value("x", "k1") != pii.hash_value("x", "k2")


def test_hash_handles_blank():
    assert pii.hash_value(None, "k") is None
    assert pii.hash_value(float("nan"), "k") is None


def test_sample_has_no_raw_pii():
    df = excel_reader.read_export(SAMPLE)
    out = pii.pseudonymize(df, "test-secret")
    cols = set(out.columns)
    assert {"buyer_hash", "document_hash", "address_hash"} <= cols
    for c in cols:
        assert "seguimiento" not in c and "transportista" not in c and c not in pii.DROPPED_EXACT
    assert "compradores_comprador" not in cols and "compradores_dni" not in cols
    assert "compradores_domicilio" not in cols
