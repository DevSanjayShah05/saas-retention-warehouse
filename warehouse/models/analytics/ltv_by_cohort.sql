-- LTV per signup cohort: both an *observed* net revenue-to-date figure
-- (right-censored -- recent cohorts haven't lived long enough to show their
-- true lifetime value yet, by design) and a *formulaic* estimate
-- (ARPU / blended monthly churn rate, the standard SaaS LTV approximation,
-- excluding gross margin and CAC for simplicity -- see README methodology).
with cohorts as (
    select customer_id, date_trunc('month', signup_date) as cohort_month
    from {{ ref('dim_customer') }}
    where is_current
),

observed_revenue as (
    select customer_id, sum(amount_paid - amount_refunded) as net_revenue_to_date
    from {{ ref('fact_invoices') }}
    group by 1
),

churn_rate as (
    select avg(case when movement_type = 'churn' then 1.0 else 0.0 end) as monthly_churn_rate
    from {{ ref('fact_subscription_events') }}
    where month_start >= (select max(month_start) from {{ ref('fact_subscription_events') }}) - interval 6 month
),

starting_mrr as (
    select customer_id, mrr as starting_mrr
    from {{ ref('fact_subscription_events') }}
    where movement_type = 'new'
)

select
    c.cohort_month,
    count(distinct c.customer_id) as cohort_size,
    round(avg(coalesce(orv.net_revenue_to_date, 0)), 2) as avg_observed_revenue_per_customer,
    round(avg(coalesce(sm.starting_mrr, 0)), 2) as avg_starting_mrr,
    round((select monthly_churn_rate from churn_rate), 4) as blended_monthly_churn_rate,
    round(
        avg(coalesce(sm.starting_mrr, 0)) / nullif((select monthly_churn_rate from churn_rate), 0),
        2
    ) as formulaic_ltv_estimate
from cohorts c
left join observed_revenue orv on orv.customer_id = c.customer_id
left join starting_mrr sm on sm.customer_id = c.customer_id
group by 1
order by 1
