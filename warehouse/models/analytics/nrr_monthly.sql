-- Net Revenue Retention, trailing 12 months: of the MRR that existed from a
-- given base-month's active customers, how much of it (including expansion,
-- net of contraction/churn, excluding any new-logo MRR) survives 12 months
-- later.
with monthly as (
    select customer_id, month_start, mrr
    from {{ ref('fact_subscription_events') }}
),

base as (
    select customer_id, month_start as base_month, mrr as base_mrr
    from monthly
    where mrr > 0
),

future as (
    select customer_id, month_start as future_month, mrr as future_mrr
    from monthly
)

select
    b.base_month,
    b.base_month + interval 12 month as measurement_month,
    count(distinct b.customer_id) as base_customers,
    round(sum(b.base_mrr), 2) as base_mrr_total,
    round(sum(coalesce(f.future_mrr, 0)), 2) as retained_mrr_total,
    round(100.0 * sum(coalesce(f.future_mrr, 0)) / nullif(sum(b.base_mrr), 0), 2) as nrr_pct
from base b
left join future f
    on f.customer_id = b.customer_id
    and f.future_month = b.base_month + interval 12 month
group by 1, 2
having b.base_month + interval 12 month <= (select max(month_start) from monthly)
order by 1
