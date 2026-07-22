select
    payment_id,
    invoice_id,
    cast(payment_date as date) as payment_date,
    amount,
    status,
    refund_amount,
    cast(refund_date as date) as refund_date
from {{ source('raw', 'payments') }}
