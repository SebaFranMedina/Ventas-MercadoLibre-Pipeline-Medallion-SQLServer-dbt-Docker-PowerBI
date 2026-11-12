select order_id, sku, order_date, arrival_date
from {{ ref('sales') }}
where arrival_date < order_date
