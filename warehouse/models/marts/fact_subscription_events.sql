-- Grain: one row per customer per calendar month they had any subscription
-- history. Classifies the month-over-month MRR delta into the standard SaaS
-- movement taxonomy (new / expansion / contraction / reactivation / churn),
-- which is exactly what the MRR waterfall and cohort/NRR analytics query.
with months as (
    select distinct month_start from {{ ref('dim_date') }}
),

subs as (
    select subscription_id, customer_id, start_date, cancel_date
    from {{ ref('stg_subscriptions') }}
    where start_date is not null
),

sub_months as (
    select s.subscription_id, s.customer_id, m.month_start
    from subs s
    inner join months m
        on m.month_start >= date_trunc('month', s.start_date)
        and m.month_start <= date_trunc(
            'month', coalesce(s.cancel_date, cast('{{ var("report_end_date") }}' as date))
        )
),

mrr_by_sub_month as (
    select
        sm.subscription_id,
        sm.customer_id,
        sm.month_start,
        seg.plan_id,
        coalesce(seg.mrr, 0) as mrr
    from sub_months sm
    left join {{ ref('int_subscription_segments') }} seg
        on seg.subscription_id = sm.subscription_id
        and seg.valid_from <= (sm.month_start + interval 1 month - interval 1 day)
        and (seg.valid_to is null or seg.valid_to >= sm.month_start)

    union all

    -- Explicit $0-MRR marker for the first calendar month with no coverage
    -- after a subscription cancels. Without this, a churned customer's row
    -- sequence simply stops (no row at all) instead of showing a drop to 0,
    -- so the LAG-based movement classification below would never see the
    -- transition and would silently undercount churn. Convention: the
    -- cancellation month itself still carries the MRR the customer paid for
    -- that month; the *following* month is the first with $0 MRR.
    select
        s.subscription_id,
        s.customer_id,
        date_trunc('month', s.cancel_date) + interval 1 month as month_start,
        cast(null as varchar) as plan_id,
        0 as mrr
    from subs s
    where s.cancel_date is not null
        and date_trunc('month', s.cancel_date) + interval 1 month <= cast('{{ var("report_end_date") }}' as date)
),

customer_month_mrr as (
    select
        customer_id,
        month_start,
        sum(mrr) as mrr,
        max(plan_id) as plan_id
    from mrr_by_sub_month
    group by 1, 2
),

with_prior as (
    select
        customer_id,
        month_start,
        plan_id,
        mrr,
        lag(mrr) over (partition by customer_id order by month_start) as prior_mrr
    from customer_month_mrr
)

select
    md5(customer_id || '-' || cast(month_start as varchar)) as subscription_event_id,
    customer_id,
    month_start,
    plan_id,
    mrr,
    coalesce(prior_mrr, 0) as prior_mrr,
    mrr - coalesce(prior_mrr, 0) as delta_mrr,
    case
        when prior_mrr is null then 'new'
        when prior_mrr = 0 and mrr > 0 then 'reactivation'
        when mrr = 0 and prior_mrr > 0 then 'churn'
        when mrr > prior_mrr then 'expansion'
        when mrr < prior_mrr and mrr > 0 then 'contraction'
        else 'flat'
    end as movement_type
from with_prior
