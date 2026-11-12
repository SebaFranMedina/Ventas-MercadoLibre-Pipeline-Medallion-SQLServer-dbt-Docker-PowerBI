# Architecture

```mermaid
flowchart TB
  subgraph Python
    R[excel_reader: 2-level header -> snake_case]
    P[pii: HMAC hash / drop]
    L[bronze: append + file SHA-256 idempotency]
  end
  subgraph SQL Server
    B[bronze.sales_raw]
    S[silver.sales]
    G1[gold.fact_sales]
    G2[gold.dim_date / dim_geography / dim_product / dim_status]
    M[gold.mart_zone_summary / mart_atypical_addresses / mart_product_profitability]
  end
  R --> P --> L --> B --> S --> G1
  S --> G2
  G1 --> M
  G1 --> PBI[Power BI]
  G2 --> PBI
  M --> PBI
```

## Star schema

`fact_sales` (grain: order line = order_id + sku) joins to `dim_date` (date_key), `dim_geography` (geography_key), `dim_product` (sku) and `dim_status` (status_category).

## Idempotency

Ingestion stores the SHA-256 of each file; loading the same file twice is skipped (`--force` overrides).
Silver keeps the **latest** bronze version of each (order_id, sku), so a newer export updates statuses of older sales.

## Data quality

Singular dbt tests: unique key, order dates parsed, arrival not before order, returned lines never counted as net sales.
