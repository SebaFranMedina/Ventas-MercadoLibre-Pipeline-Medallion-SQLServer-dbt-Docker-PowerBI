{{ config(materialized='table') }}

select
    {{ geography_key('s.province', 's.city', 's.postal_code') }} as geography_key,
    max(s.province)    as province,
    max(s.city)        as city,
    max(s.postal_code) as postal_code,
    max(s.zone)        as zone
from {{ ref('sales') }} as s
group by {{ geography_key('s.province', 's.city', 's.postal_code') }}
