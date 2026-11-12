from pathlib import Path

from ml_pipeline import excel_reader

SAMPLE = Path(__file__).resolve().parents[1] / "data" / "sample" / "sample_sales.xlsx"


def test_normalize_name():
    assert excel_reader.normalize_name("Teléfono / Móvil") == "telefono_movil"


def test_read_sample():
    df = excel_reader.read_export(SAMPLE)
    assert len(df) > 5000
    assert df.columns.is_unique
    assert "ventas_de_venta" in df.columns
    assert "publicaciones_sku" in df.columns
    assert df.isna().sum().sum() >= 0
    assert not any(isinstance(v, float) for v in df["ventas_de_venta"].dropna().head(50))
