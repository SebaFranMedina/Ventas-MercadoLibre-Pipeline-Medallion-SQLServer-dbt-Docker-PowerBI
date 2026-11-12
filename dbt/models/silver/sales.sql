{{ config(materialized='table') }}

{#
  SILVER: one clean, typed row per sale line (order_id + sku).
  - Takes the latest bronze version of each sale (a newer export updates the status of an old sale).
  - Parses Spanish dates ("4 de noviembre de 2026 09:33 hs.", "Llegó el 5 de septiembre").
  - Classifies the free-text status, derives the zone, flags returns and claims.
#}

with latest as (
    select
        s.*,
        row_number() over (
            partition by s.ventas_de_venta, coalesce(s.publicaciones_sku, '')
            order by s._loaded_at desc, s._row_number desc
        ) as rn
    from {{ source('bronze', 'sales_raw') }} as s
),

dedup as (
    select * from latest where rn = 1
),

cleaned as (
    select
        d.ventas_de_venta                                                                   as order_id,
        nullif(ltrim(rtrim(d.publicaciones_sku)), '')                                       as sku,
        nullif(ltrim(rtrim(d.publicaciones_de_publicacion)), '')                            as listing_id,
        nullif(ltrim(rtrim(d.publicaciones_titulo_de_la_publicacion)), '')                  as listing_title,
        nullif(ltrim(rtrim(d.ventas_fecha_de_venta)), '')                                   as order_date_text,
        nullif(ltrim(rtrim(d.ventas_estado)), '')                                           as status_raw,
        nullif(ltrim(rtrim(d.ventas_descripcion_del_estado)), '')                           as status_description,
        try_cast(try_cast(nullif(ltrim(rtrim(d.ventas_unidades)), '') as decimal(12, 2)) as int) as units,
        nullif(ltrim(rtrim(d.compradores_estado)), '')                                      as province,
        nullif(ltrim(rtrim(d.compradores_ciudad)), '')                                      as city,
        nullif(ltrim(rtrim(d.compradores_codigo_postal)), '')                               as postal_code,
        nullif(ltrim(rtrim(d.compradores_negocio)), '')                                     as is_business_text,
        nullif(ltrim(rtrim(d.envios_forma_de_entrega)), '')                                 as shipping_method,
        nullif(ltrim(rtrim(d.devoluciones_resultado)), '')                                  as return_result,
        nullif(ltrim(rtrim(d.devoluciones_motivo_del_resultado)), '')                       as return_condition,
        nullif(ltrim(rtrim(d.devoluciones_destino)), '')                                    as return_destination,
        nullif(ltrim(rtrim(d.reclamos_reclamo_abierto)), '')                                as claim_open_text,
        nullif(ltrim(rtrim(d.reclamos_reclamo_cerrado)), '')                                as claim_closed_text,
        d.buyer_hash,
        d.address_hash,
        d._source_file                                                                      as source_file,
        d._loaded_at                                                                        as loaded_at
    from dedup as d
),

-- "4 de noviembre de 2026 09:33 hs." -> day / month name / year / time
date_1 as (
    select c.*, nullif(charindex(' de ', c.order_date_text), 0) as p1
    from cleaned as c
),
date_2 as (
    select d.*, case when d.p1 is not null then substring(d.order_date_text, d.p1 + 4, 100) end as rest1
    from date_1 as d
),
date_3 as (
    select d.*, nullif(charindex(' de ', d.rest1), 0) as p2
    from date_2 as d
),
date_4 as (
    select
        d.*,
        left(d.order_date_text, d.p1 - 1)       as day_text,
        left(d.rest1, d.p2 - 1)                 as month_text,
        substring(d.rest1, d.p2 + 4, 100)       as rest2
    from date_3 as d
),
parsed as (
    select
        d.*,
        try_convert(datetime2(0), concat(
            left(d.rest2, 4), '-',
            right(concat('0', {{ spanish_month_number('d.month_text') }}), 2), '-',
            right(concat('0', d.day_text), 2), 'T',
            substring(d.rest2, 6, 5), ':00'
        )) as order_ts
    from date_4 as d
),

-- "Llegó el 5 de septiembre" (no year) -> arrival date, year taken from the order date
arrival_1 as (
    select
        p.*,
        case when p.status_description like 'Lleg%'
             then nullif(charindex(' el ', p.status_description), 0) end as pe
    from parsed as p
),
arrival_2 as (
    select a.*, case when a.pe is not null then substring(a.status_description, a.pe + 4, 60) end as arr_rest
    from arrival_1 as a
),
arrival_3 as (
    select a.*, nullif(charindex(' de ', a.arr_rest), 0) as pa
    from arrival_2 as a
),
arrival_4 as (
    select
        a.*,
        left(a.arr_rest, a.pa - 1)                       as arr_day_text,
        rtrim(substring(a.arr_rest, a.pa + 4, 30))       as arr_month_text
    from arrival_3 as a
),
arrival_5 as (
    select
        a.*,
        try_convert(date, concat(
            year(a.order_ts), '-',
            right(concat('0', {{ spanish_month_number('a.arr_month_text') }}), 2), '-',
            right(concat('0', a.arr_day_text), 2)
        )) as arrival_candidate
    from arrival_4 as a
),

enriched as (
    select
        a.*,
        {{ status_category('lower(a.status_raw)') }} as status_category,
        case
            when a.arrival_candidate is null then null
            when a.arrival_candidate < cast(a.order_ts as date) then dateadd(year, 1, a.arrival_candidate)
            else a.arrival_candidate
        end as arrival_date,
        -- first 4-digit run of the postal code (works for "1425" and "C1425ABC")
        substring(a.postal_code, nullif(patindex('%[0-9][0-9][0-9][0-9]%', a.postal_code), 0), 4) as zip4
    from arrival_5 as a
)

select
    e.order_id,
    e.sku,
    e.listing_id,
    e.listing_title,
    e.order_ts,
    cast(e.order_ts as date)                    as order_date,
    datepart(hour, e.order_ts)                  as order_hour,
    e.status_raw,
    e.status_description,
    e.status_category,
    e.units,
    coalesce(e.province, 'Unknown')             as province,
    e.city,
    e.postal_code,
    case
        when e.province is null then 'Unknown'
        when e.province = 'Capital Federal' then 'CABA'
        -- approximation: Buenos Aires postal codes 1600-1999 = Greater Buenos Aires / La Plata
        when e.province = 'Buenos Aires' and try_cast(e.zip4 as int) between 1600 and 1999 then 'GBA (approx.)'
        when e.province = 'Buenos Aires' then 'Rest of Buenos Aires'
        else 'Interior'
    end                                         as zone,
    case when e.is_business_text = N'Sí' then 1 when e.is_business_text is null then null else 0 end as is_business,
    e.shipping_method,
    case when e.status_category = 'Returned' then 1 else 0 end                                  as is_returned,
    case when e.claim_open_text = N'Sí' or e.claim_closed_text is not null then 1 else 0 end    as has_claim,
    -- analysis base: real orders (no cancellations, no cart summary rows)
    case when e.status_category in ('Cancelled', 'Package header') then 0 else 1 end            as is_analysis_base,
    -- net sale: analysis base minus returned and failed deliveries
    case when e.status_category in ('Cancelled', 'Package header', 'Returned', 'Failed delivery')
         then 0 else 1 end                                                                      as is_net_sale,
    e.arrival_date,
    case when e.status_category = 'Delivered'
         then datediff(day, cast(e.order_ts as date), e.arrival_date) end                       as delivery_days,
    e.return_result,
    e.return_condition,
    e.return_destination,
    e.buyer_hash                                as buyer_id,
    e.address_hash                              as address_id,
    e.source_file,
    e.loaded_at
from enriched as e
