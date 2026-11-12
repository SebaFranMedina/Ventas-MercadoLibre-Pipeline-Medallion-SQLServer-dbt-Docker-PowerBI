{{ config(materialized='table') }}

-- Calendar from the first to the last order date. Weekday numbering is independent of SQL Server's DATEFIRST
-- setting (1900-01-01 was a Monday).
with bounds as (
    select min(order_date) as first_date, max(order_date) as last_date
    from {{ ref('sales') }}
),

numbers as (
    select top (select datediff(day, first_date, last_date) + 1 from bounds)
        row_number() over (order by (select null)) - 1 as n
    from sys.all_objects as a
    cross join sys.all_objects as b
),

dates as (
    select dateadd(day, numbers.n, bounds.first_date) as date_key
    from numbers
    cross join bounds
)

select
    d.date_key,
    year(d.date_key)                                                        as year_number,
    month(d.date_key)                                                       as month_number,
    case month(d.date_key)
        when 1 then 'January' when 2 then 'February' when 3 then 'March' when 4 then 'April'
        when 5 then 'May' when 6 then 'June' when 7 then 'July' when 8 then 'August'
        when 9 then 'September' when 10 then 'October' when 11 then 'November' else 'December'
    end                                                                     as month_name,
    concat(year(d.date_key), '-', right(concat('0', month(d.date_key)), 2)) as year_month,
    dateadd(day, -(datediff(day, '19000101', d.date_key) % 7), d.date_key)  as week_start,
    (datediff(day, '19000101', d.date_key) % 7) + 1                         as day_of_week_number,
    case (datediff(day, '19000101', d.date_key) % 7)
        when 0 then 'Monday' when 1 then 'Tuesday' when 2 then 'Wednesday' when 3 then 'Thursday'
        when 4 then 'Friday' when 5 then 'Saturday' else 'Sunday'
    end                                                                     as day_name,
    case when (datediff(day, '19000101', d.date_key) % 7) >= 5 then 1 else 0 end as is_weekend
from dates as d
