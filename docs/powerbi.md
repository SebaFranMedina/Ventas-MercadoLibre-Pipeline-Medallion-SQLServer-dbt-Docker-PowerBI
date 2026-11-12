# Power BI

## Connect
1. Get data → SQL Server. Server `localhost,1433`, database `ventas_ml`, Import mode.
2. Credentials: database → user `powerbi_reader` and the password from `POWERBI_READER_PASSWORD`.
3. If you get a certificate error (local container, self-signed certificate), untick *Encrypt connections*. Local use only.
4. Load **only the `gold` schema** tables.

## Relationships (all many-to-one, single direction)
* `fact_sales[date_key]` → `dim_date[date_key]`
* `fact_sales[geography_key]` → `dim_geography[geography_key]`
* `fact_sales[sku]` → `dim_product[sku]`
* `fact_sales[status_category]` → `dim_status[status_category]`

(Check the exact column names in `dbt/models/gold/*.sql`.)

## Measures (DAX)
```dax
Orders = DISTINCTCOUNT ( fact_sales[order_id] )
Net Units = CALCULATE ( SUM ( fact_sales[units] ), fact_sales[is_net_sale] = 1 )
Returned Orders = CALCULATE ( DISTINCTCOUNT ( fact_sales[order_id] ), fact_sales[is_returned] = 1 )
Return Rate % = DIVIDE ( [Returned Orders], [Orders] )
Claim Rate % =
    DIVIDE ( CALCULATE ( DISTINCTCOUNT ( fact_sales[order_id] ), fact_sales[has_claim] = 1 ), [Orders] )
Orders excl. Atypical = CALCULATE ( [Orders], fact_sales[is_atypical_address] = 0 )
Return Rate excl. Atypical % =
    CALCULATE ( [Return Rate %], fact_sales[is_atypical_address] = 0 )
Avg Delivery Days = AVERAGE ( fact_sales[delivery_days] )
Units per Order = DIVIDE ( SUM ( fact_sales[units] ), [Orders] )
```
Filter report pages with `is_analysis_base = 1` to exclude cart-header rows.

## Suggested pages
1. Overview: orders, net units, return rate by month.
2. Zones: return/claim rate by zone, with vs. without atypical addresses (`mart_zone_summary`).
3. Products: profitability (`mart_product_profitability`).
