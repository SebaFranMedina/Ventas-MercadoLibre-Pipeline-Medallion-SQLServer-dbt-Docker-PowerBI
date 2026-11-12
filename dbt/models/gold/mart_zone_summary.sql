{{ config(materialized='table') }}

-- Key comparison: return and claim rates per zone, with and without the atypical addresses.
with lines as (
    select
        g.zone,
        f.order_id,
        f.units,
        f.is_net_sale,
        f.is_returned,
        f.has_claim,
        f.is_atypical_address,
        f.delivery_days
    from {{ ref('fact_sales') }} as f
    inner join {{ ref('dim_geography') }} as g
        on g.geography_key = f.geography_key
    where f.is_analysis_base = 1
)

select
    zone,
    count(distinct order_id)                                                              as orders,
    sum(case when is_net_sale = 1 then coalesce(units, 0) else 0 end)                     as net_units,
    count(distinct case when is_returned = 1 then order_id end)                           as returned_orders,
    count(distinct case when has_claim = 1 then order_id end)                             as orders_with_claim,
    cast(100.0 * count(distinct case when is_returned = 1 then order_id end)
         / nullif(count(distinct order_id), 0) as decimal(6, 2))                          as returned_pct,
    cast(100.0 * count(distinct case when has_claim = 1 then order_id end)
         / nullif(count(distinct order_id), 0) as decimal(6, 2))                          as claim_pct,
    count(distinct case when is_atypical_address = 0 then order_id end)                   as orders_excl_atypical,
    cast(100.0 * count(distinct case when is_atypical_address = 0 and is_returned = 1 then order_id end)
         / nullif(count(distinct case when is_atypical_address = 0 then order_id end), 0) as decimal(6, 2))
                                                                                          as returned_pct_excl_atypical,
    cast(100.0 * count(distinct case when is_atypical_address = 0 and has_claim = 1 then order_id end)
         / nullif(count(distinct case when is_atypical_address = 0 then order_id end), 0) as decimal(6, 2))
                                                                                          as claim_pct_excl_atypical,
    cast(avg(case when delivery_days is not null then 1.0 * delivery_days end) as decimal(6, 2))
                                                                                          as avg_delivery_days
from lines
group by zone
