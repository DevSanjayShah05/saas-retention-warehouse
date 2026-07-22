select
    customer_id,
    subscription_id,
    cast(usage_month as date) as usage_month,
    login_days,
    feature_events,
    api_calls
from {{ source('raw', 'usage_monthly') }}
