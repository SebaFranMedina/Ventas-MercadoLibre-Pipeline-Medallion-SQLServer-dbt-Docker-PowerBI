-- Every order date must have been parsed from the Spanish text.
select order_id, sku
from {{ ref('sales') }}
where order_ts is null
