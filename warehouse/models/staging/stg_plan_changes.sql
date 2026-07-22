select
    change_id,
    subscription_id,
    cast(change_date as date) as change_date,
    change_type,
    old_plan_id,
    new_plan_id,
    old_mrr,
    new_mrr
from {{ source('raw', 'plan_changes') }}
