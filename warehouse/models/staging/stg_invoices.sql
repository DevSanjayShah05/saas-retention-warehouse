select
    invoice_id,
    subscription_id,
    customer_id,
    plan_id,
    cast(invoice_date as date) as invoice_date,
    cast(period_start as date) as period_start,
    cast(period_end as date) as period_end,
    amount_due
from {{ source('raw', 'invoices') }}
