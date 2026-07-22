-- SCD2 source rows for dim_customer: one row per attribute-change event,
-- ordered by customer_id + version_no. dim_customer derives valid_from/
-- valid_to/is_current from this via window functions.
select
    customer_id,
    version_no,
    industry,
    employee_band,
    country,
    acquisition_channel,
    company_name,
    cast(effective_date as date) as effective_date
from {{ source('raw', 'customers_history') }}
