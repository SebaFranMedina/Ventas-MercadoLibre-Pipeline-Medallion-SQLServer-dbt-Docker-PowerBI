{{ config(materialized='table') }}

-- One row per SKU; the title is the most frequent one used for that SKU.
with titles as (
    select sku, listing_title, count(*) as n
    from {{ ref('sales') }}
    where sku is not null
    group by sku, listing_title
),

ranked as (
    select
        t.*,
        row_number() over (partition by t.sku order by t.n desc, t.listing_title) as rn
    from titles as t
)

select
    r.sku,
    r.listing_title as title
from ranked as r
where r.rn = 1
