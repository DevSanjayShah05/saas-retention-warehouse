select
    customer_id,
    signup_date,
    company_name,
    industry,
    employee_band,
    country,
    acquisition_channel
from {{ source('raw', 'customers') }}
