select
    subscription_id,
    customer_id,
    plan_id,
    tier,
    billing_interval,
    cast(start_date as date) as start_date,
    cast(trial_start_date as date) as trial_start_date,
    cast(trial_end_date as date) as trial_end_date,
    initial_mrr,
    status,
    cast(cancel_date as date) as cancel_date,
    cancel_reason,
    is_reactivation,
    reactivated_from_subscription_id
from {{ source('raw', 'subscriptions') }}
