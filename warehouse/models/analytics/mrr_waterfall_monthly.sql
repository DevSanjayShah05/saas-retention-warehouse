-- Standard SaaS MRR waterfall: new / expansion / contraction / reactivation
-- / churn components that reconcile to the ending MRR each month.
select
    month_start,
    sum(case when movement_type = 'new' then delta_mrr else 0 end) as new_mrr,
    sum(case when movement_type = 'expansion' then delta_mrr else 0 end) as expansion_mrr,
    sum(case when movement_type = 'contraction' then delta_mrr else 0 end) as contraction_mrr,
    sum(case when movement_type = 'reactivation' then delta_mrr else 0 end) as reactivation_mrr,
    sum(case when movement_type = 'churn' then delta_mrr else 0 end) as churn_mrr,
    sum(delta_mrr) as net_new_mrr,
    sum(mrr) as ending_mrr,
    count(distinct case when mrr > 0 then customer_id end) as active_customers
from {{ ref('fact_subscription_events') }}
group by 1
order by 1
