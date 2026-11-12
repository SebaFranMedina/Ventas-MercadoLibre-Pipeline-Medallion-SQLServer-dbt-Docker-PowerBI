select order_id, sku
from {{ ref('sales') }}
where is_returned = 1
  and is_net_sale = 1
