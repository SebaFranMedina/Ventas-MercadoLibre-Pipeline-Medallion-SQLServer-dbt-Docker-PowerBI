-- Silver must have exactly one row per (order_id, sku).
select order_id, sku, count(*) as n
from {{ ref('sales') }}
group by order_id, sku
having count(*) > 1
