{{ config(materialized='table') }}

-- Grain: one row per sale line (order_id + sku).
select
    concat(s.order_id, '-', coalesce(s.sku, ''))                    as sale_line_key,
    s.order_id,
    s.order_date                                                    as date_key,
    {{ geography_key('s.province', 's.city', 's.postal_code') }} as geography_key,
    s.sku,
    s.status_category,
    s.shipping_method,
    s.order_hour,
    s.units,
    s.delivery_days,
    s.is_analysis_base,
    s.is_net_sale,
    s.is_returned,
    s.has_claim,
    s.is_business,
    coalesce(a.is_atypical, 0)                                      as is_atypical_address,
    s.return_result,
    s.return_condition,
    s.return_destination,
    s.address_id,
    s.buyer_id
from {{ ref('sales') }} as s
left join {{ ref('mart_atypical_addresses') }} as a
    on a.address_id = s.address_id
