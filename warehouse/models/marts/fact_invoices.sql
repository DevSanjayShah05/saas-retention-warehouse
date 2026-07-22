with payment_agg as (
    select
        invoice_id,
        sum(case when status = 'succeeded' then amount else 0 end) as amount_paid,
        sum(coalesce(refund_amount, 0)) as amount_refunded,
        bool_or(status = 'failed') as had_failed_attempt,
        min(payment_date) as first_payment_date
    from {{ ref('stg_payments') }}
    group by invoice_id
)

select
    i.invoice_id,
    i.subscription_id,
    i.customer_id,
    i.plan_id,
    dc.customer_key,
    dp.plan_key,
    i.invoice_date,
    i.period_start,
    i.period_end,
    i.amount_due,
    coalesce(pa.amount_paid, 0) as amount_paid,
    coalesce(pa.amount_refunded, 0) as amount_refunded,
    coalesce(pa.had_failed_attempt, false) as had_failed_attempt,
    pa.first_payment_date
from {{ ref('stg_invoices') }} i
left join payment_agg pa on pa.invoice_id = i.invoice_id
left join {{ ref('dim_customer') }} dc on dc.customer_id = i.customer_id and dc.is_current
left join {{ ref('dim_plan') }} dp on dp.plan_id = i.plan_id
