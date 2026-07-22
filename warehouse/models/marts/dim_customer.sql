-- SCD Type 2 dimension, hand-built with window functions rather than a dbt
-- snapshot: dbt snapshot is designed to capture changes going forward as a
-- pipeline runs repeatedly over wall-clock time. Our raw customer history is
-- already fully known (backfilled synthetic history), so the correct way to
-- build a SCD2 mart from it is to derive valid_from/valid_to/is_current
-- directly from the ordered version history, which is what this model does.
with ordered as (
    select
        h.customer_id,
        h.version_no,
        h.industry,
        h.employee_band,
        h.country,
        h.acquisition_channel,
        h.company_name,
        h.effective_date,
        lead(h.effective_date) over (
            partition by h.customer_id order by h.version_no
        ) as next_effective_date
    from {{ ref('stg_customers_history') }} h
)

select
    md5(o.customer_id || '-' || cast(o.version_no as varchar)) as customer_key,
    o.customer_id,
    o.version_no,
    o.company_name,
    o.industry,
    o.employee_band,
    o.country,
    o.acquisition_channel,
    c.signup_date,
    o.effective_date as valid_from,
    case
        when o.next_effective_date is not null then o.next_effective_date - interval 1 day
        else null
    end as valid_to,
    case when o.next_effective_date is null then true else false end as is_current
from ordered o
inner join {{ ref('stg_customers') }} c using (customer_id)
