-- Cohort retention curve: for every signup-month cohort, what % of the
-- original cohort still had mrr > 0 in each subsequent month_number.
with cohorts as (
    select customer_id, date_trunc('month', signup_date) as cohort_month
    from {{ ref('dim_customer') }}
    where is_current
),

customer_months as (
    select customer_id, month_start, mrr
    from {{ ref('fact_subscription_events') }}
    where mrr > 0
),

joined as (
    select
        c.cohort_month,
        c.customer_id,
        cm.month_start,
        cm.mrr,
        datediff('month', c.cohort_month, cm.month_start) as month_number
    from cohorts c
    inner join customer_months cm on cm.customer_id = c.customer_id
),

cohort_sizes as (
    select cohort_month, count(distinct customer_id) as cohort_size
    from cohorts
    group by 1
),

retention as (
    select
        cohort_month,
        month_number,
        count(distinct customer_id) as retained_customers,
        sum(mrr) as retained_mrr
    from joined
    group by 1, 2
)

select
    r.cohort_month,
    cs.cohort_size,
    r.month_number,
    r.retained_customers,
    round(100.0 * r.retained_customers / cs.cohort_size, 2) as retention_pct,
    r.retained_mrr
from retention r
inner join cohort_sizes cs on cs.cohort_month = r.cohort_month
order by 1, 3
