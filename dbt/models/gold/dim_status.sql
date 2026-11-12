{{ config(materialized='table') }}

select
    v.status_category,
    v.is_analysis_base,
    v.is_net_sale,
    v.sort_order
from (
    values
        ('Delivered',      1, 1, 1),
        ('In transit',     1, 1, 2),
        ('Preparing',      1, 1, 3),
        ('Claim resolved', 1, 1, 4),
        ('Exchange',       1, 1, 5),
        ('Returned',       1, 0, 6),
        ('Failed delivery', 1, 0, 7),
        ('Cancelled',      0, 0, 8),
        ('Package header', 0, 0, 9),
        ('Other',          1, 1, 10)
) as v (status_category, is_analysis_base, is_net_sale, sort_order)
