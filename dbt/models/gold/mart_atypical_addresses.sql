{{ config(materialized='table') }}

-- Addresses (pseudonymised ids) that receive many orders and send most of them back.
with per_address as (
    select
        s.address_id,
        count(distinct s.order_id)                                       as orders,
        count(distinct case when s.is_returned = 1 then s.order_id end)  as returned_orders,
        count(distinct case when s.has_claim = 1 then s.order_id end)    as orders_with_claim,
        max(s.zone)                                                      as zone
    from {{ ref('sales') }} as s
    where s.is_analysis_base = 1
      and s.address_id is not null
    group by s.address_id
)

select
    p.address_id,
    p.zone,
    p.orders,
    p.returned_orders,
    p.orders_with_claim,
    cast(100.0 * p.returned_orders / nullif(p.orders, 0) as decimal(6, 2)) as returned_pct,
    case
        when p.orders >= {{ var('atypical_min_orders') }}
         and 100.0 * p.returned_orders / nullif(p.orders, 0) >= {{ var('atypical_min_returned_pct') }}
        then 1 else 0
    end as is_atypical
from per_address as p
where p.returned_orders > 0
   or p.orders_with_claim > 0
