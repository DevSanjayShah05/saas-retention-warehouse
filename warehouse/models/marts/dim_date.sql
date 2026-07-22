select
    cast(d as date) as date_day,
    extract(year from d) as year,
    extract(month from d) as month,
    extract(day from d) as day,
    extract(quarter from d) as quarter,
    strftime(d, '%Y-%m') as year_month,
    date_trunc('month', d) as month_start,
    (date_trunc('month', d) + interval 1 month - interval 1 day) as month_end,
    dayname(d) as day_name,
    case when extract(dow from d) in (0, 6) then true else false end as is_weekend
from generate_series(
    cast('{{ var("report_start_date") }}' as date),
    cast('{{ var("report_end_date") }}' as date),
    interval 1 day
) as t(d)
