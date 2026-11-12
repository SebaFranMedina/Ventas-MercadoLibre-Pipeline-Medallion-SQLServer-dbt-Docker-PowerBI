{{ config(materialized='table') }}

-- Gross margin per product = units * (price - cost - marketplace fee). Prices come from the seed
-- `product_prices` (replace it with the client's real price list). Shipping and taxes are not included.
select
    p.sku,
    d.title,
    sum(coalesce(f.units, 0))                                                                       as units,
    cast(sum(coalesce(f.units, 0) * p.unit_price) as decimal(18, 2))                                as revenue,
    cast(sum(coalesce(f.units, 0) * (p.unit_price - p.unit_cost - p.unit_price * p.fee_pct / 100.0))
         as decimal(18, 2))                                                                         as gross_margin,
    cast(100.0 * sum(coalesce(f.units, 0) * (p.unit_price - p.unit_cost - p.unit_price * p.fee_pct / 100.0))
         / nullif(sum(coalesce(f.units, 0) * p.unit_price), 0) as decimal(6, 2))                    as gross_margin_pct
from {{ ref('fact_sales') }} as f
inner join {{ ref('product_prices') }} as p
    on p.sku = f.sku
left join {{ ref('dim_product') }} as d
    on d.sku = f.sku
where f.is_net_sale = 1
group by p.sku, d.title
