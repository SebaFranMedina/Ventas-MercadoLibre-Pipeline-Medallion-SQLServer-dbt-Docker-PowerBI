# ml-sales-medallion

Pipeline **medallón (bronze → silver → gold) sobre SQL Server** para un export de ventas de Mercado Libre,
con **dbt**, **Docker Compose**, **GitHub Actions** y un modelo estrella listo para Power BI.

> Todos los datos del repo son **ficticios** (`scripts/generate_sample_data.py`). Los exports reales nunca se suben.

## El caso

Un negocio de insumos de computación exporta sus ventas de Mercado Libre a Excel (encabezado de dos niveles, fechas en español, más de 100 textos de estado).
El análisis exploratorio mostró que **dos direcciones atípicas explicaban ~75 % de las devoluciones**, tapando el comportamiento real de cada zona.
Este pipeline vuelve ese análisis reproducible y alimenta un reporte en Power BI.

## Capas

* **bronze**: texto crudo + metadatos de carga; datos personales ya hasheados.
* **silver** (dbt): una fila limpia y tipada por línea de venta; fechas parseadas, categorías de estado, zonas, flags.
* **gold** (dbt): `fact_sales`, `dim_date`, `dim_geography`, `dim_product`, `dim_status` y marts (resumen por zona, direcciones atípicas, rentabilidad).

## Privacidad

Nombre, DNI y domicilio del comprador se reemplazan por un hash con clave (HMAC-SHA256) **antes** de cargar; se descartan datos de facturación, seguimientos y transportistas.

## Uso rápido

```bash
cp .env.example .env     # editar contraseñas y PII_SECRET
make up
```

Luego conectar Power BI a `localhost,1433`, base `ventas_ml`, esquema `gold` ([docs/powerbi.md](docs/powerbi.md)).
Con datos reales: copiar el Excel a `data/raw/` (ignorado por git) y `make real FILE=data/raw/archivo.xlsx`.

Se habla de "direcciones atípicas": el repo no afirma la causa.
