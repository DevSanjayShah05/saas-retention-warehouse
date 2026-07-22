select
    plan_id,
    plan_name,
    tier,
    billing_interval,
    monthly_price,
    cast(effective_from as date) as effective_from,
    cast(effective_to as date) as effective_to,
    is_current
from {{ source('raw', 'plans_history') }}
