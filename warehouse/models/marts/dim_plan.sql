-- SCD Type 2 dimension. Source (stg_plans_history) already carries a full
-- price-change history with effective_from/effective_to per plan version
-- (list price increases over time) -- this model just re-shapes it into
-- standard dim SCD2 form with a surrogate key.
select
    md5(plan_id) as plan_key,
    plan_id,
    plan_name,
    tier,
    billing_interval,
    monthly_price,
    effective_from as valid_from,
    effective_to as valid_to,
    is_current
from {{ ref('stg_plans_history') }}
