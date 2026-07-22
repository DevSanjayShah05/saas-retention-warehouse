-- Intermediate: reconstructs the piecewise MRR history of every subscription
-- as a series of non-overlapping [valid_from, valid_to] segments -- one per
-- plan the subscription was on, in order. Feeds fact_subscription_events.
with base_events as (
    select
        subscription_id,
        customer_id,
        start_date as valid_from,
        plan_id,
        initial_mrr as mrr
    from {{ ref('stg_subscriptions') }}
    where start_date is not null

    union all

    select
        pc.subscription_id,
        s.customer_id,
        pc.change_date as valid_from,
        pc.new_plan_id as plan_id,
        pc.new_mrr as mrr
    from {{ ref('stg_plan_changes') }} pc
    inner join {{ ref('stg_subscriptions') }} s on s.subscription_id = pc.subscription_id
),

with_bounds as (
    select
        b.*,
        lead(b.valid_from) over (partition by b.subscription_id order by b.valid_from) as next_valid_from,
        s.cancel_date
    from base_events b
    inner join {{ ref('stg_subscriptions') }} s on s.subscription_id = b.subscription_id
)

select
    subscription_id,
    customer_id,
    plan_id,
    mrr,
    valid_from,
    case
        when next_valid_from is not null then next_valid_from - interval 1 day
        when cancel_date is not null then cancel_date - interval 1 day
        else null
    end as valid_to
from with_bounds
