"""
Cohort & Ledger — synthetic OLTP seed generator.

Generates a reproducible (fixed-seed) synthetic transactional dataset for a
B2B SaaS subscription business spanning Jan 2023 - Jun 2026: customers,
subscriptions, plan changes, invoices, payments, and monthly product usage
summaries. Includes trials, upgrades/downgrades, cancellations,
reactivations, refunds/failed payments, and grandfathered pricing.

Run:
    python data/seed/generate_seed_data.py

Writes CSVs to data/raw/. This script is the single source of truth for the
dataset — the committed CSVs in data/raw/ are its output, checked in so the
rest of the pipeline never depends on re-running it.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from pathlib import Path

SEED = 42
rng = np.random.default_rng(SEED)

DATA_START = date(2023, 1, 1)
DATA_END = date(2026, 6, 30)
N_CUSTOMERS = 3000

OUT_DIR = Path(__file__).resolve().parent.parent / "raw"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------

TIERS = ["Starter", "Growth", "Scale", "Enterprise"]
TIER_WEIGHTS = [0.42, 0.33, 0.18, 0.07]

# base monthly list price, then price-rise "versions" with an effective date
# each row: (tier, monthly_price, effective_from, effective_to_or_None)
PLAN_PRICE_HISTORY = [
    ("Starter", 29.0, date(2023, 1, 1), date(2024, 6, 30)),
    ("Starter", 35.0, date(2024, 7, 1), date(2025, 12, 31)),
    ("Starter", 39.0, date(2026, 1, 1), None),
    ("Growth", 99.0, date(2023, 1, 1), date(2024, 6, 30)),
    ("Growth", 119.0, date(2024, 7, 1), date(2025, 12, 31)),
    ("Growth", 129.0, date(2026, 1, 1), None),
    ("Scale", 299.0, date(2023, 1, 1), date(2024, 12, 31)),
    ("Scale", 349.0, date(2025, 1, 1), None),
    ("Enterprise", 899.0, date(2023, 1, 1), date(2025, 5, 31)),
    ("Enterprise", 999.0, date(2025, 6, 1), None),
]
BILLING_INTERVALS = ["monthly", "annual"]
ANNUAL_DISCOUNT_MULT = 10.0 / 12.0  # 2 months free when paying annually

INDUSTRIES = [
    "SaaS/Technology", "Retail/Ecommerce", "Healthcare", "Financial Services",
    "Education", "Manufacturing", "Media/Entertainment", "Professional Services",
]
INDUSTRY_WEIGHTS = [0.28, 0.14, 0.10, 0.12, 0.09, 0.09, 0.08, 0.10]

EMPLOYEE_BANDS = ["1-10", "11-50", "51-200", "201-500", "501-1000", "1000+"]
EMPLOYEE_WEIGHTS = [0.32, 0.30, 0.20, 0.10, 0.05, 0.03]

COUNTRIES = ["United States", "United Kingdom", "Canada", "Germany", "Australia", "India", "France", "Brazil"]
COUNTRY_WEIGHTS = [0.52, 0.11, 0.09, 0.07, 0.06, 0.06, 0.05, 0.04]

CHANNELS = ["Organic Search", "Paid Search", "Referral", "Content/Blog", "Outbound Sales", "Partner"]
CHANNEL_WEIGHTS = [0.27, 0.20, 0.15, 0.13, 0.15, 0.10]

CANCEL_REASONS = [
    "too_expensive", "missing_features", "switched_competitor",
    "no_longer_needed", "poor_support", "payment_failed", "budget_cuts",
]
CANCEL_REASON_WEIGHTS = [0.22, 0.18, 0.14, 0.16, 0.08, 0.10, 0.12]


def month_range(start: date, end: date):
    cur = date(start.year, start.month, 1)
    while cur <= end:
        yield cur
        cur = cur + relativedelta(months=1)


def plan_price_on(tier: str, on_date: date) -> float:
    for t, price, eff_from, eff_to in PLAN_PRICE_HISTORY:
        if t == tier and eff_from <= on_date and (eff_to is None or on_date <= eff_to):
            return price
    # fallback to latest known price for tier
    candidates = [p for t, p, f, to in PLAN_PRICE_HISTORY if t == tier]
    return candidates[-1]


def plan_version_id(tier: str, on_date: date) -> str:
    versions = [row for row in PLAN_PRICE_HISTORY if row[0] == tier]
    versions.sort(key=lambda r: r[2])
    for i, (t, price, eff_from, eff_to) in enumerate(versions, start=1):
        if eff_from <= on_date and (eff_to is None or on_date <= eff_to):
            return f"{tier.lower()}_v{i}"
    return f"{tier.lower()}_v{len(versions)}"


# ---------------------------------------------------------------------------
# 1. plans_history — dimension source w/ full price-change history (SCD2 fuel)
# ---------------------------------------------------------------------------

def build_plans_history() -> pd.DataFrame:
    rows = []
    for tier in TIERS:
        versions = [r for r in PLAN_PRICE_HISTORY if r[0] == tier]
        versions.sort(key=lambda r: r[2])
        for i, (t, monthly_price, eff_from, eff_to) in enumerate(versions, start=1):
            for interval in BILLING_INTERVALS:
                plan_id = f"{tier.lower()}_{interval}_v{i}"
                price = monthly_price if interval == "monthly" else round(monthly_price * ANNUAL_DISCOUNT_MULT, 2)
                rows.append({
                    "plan_id": plan_id,
                    "plan_name": f"{tier} ({interval.title()})",
                    "tier": tier,
                    "billing_interval": interval,
                    "monthly_price": price,
                    "effective_from": eff_from,
                    "effective_to": eff_to,
                    "is_current": eff_to is None,
                })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 2. customers + customers_history (SCD2 fuel: ~15% get a later attribute change)
# ---------------------------------------------------------------------------

def build_customers():
    n = N_CUSTOMERS
    # growth-trending signup distribution: more signups in later months, mild seasonality
    months = list(month_range(DATA_START, DATA_END))
    n_months = len(months)
    growth = np.linspace(1.0, 3.2, n_months) ** 1.3
    season = 1.0 + 0.15 * np.sin(np.arange(n_months) * (2 * np.pi / 12))
    weights = growth * season
    weights = weights / weights.sum()
    month_choice = rng.choice(n_months, size=n, p=weights)

    customer_ids = [f"CUST-{i:05d}" for i in range(1, n + 1)]
    signup_dates = []
    for m_idx in month_choice:
        m = months[m_idx]
        day = int(rng.integers(1, 28))
        signup_dates.append(date(m.year, m.month, day))
    signup_dates.sort()

    industries = rng.choice(INDUSTRIES, size=n, p=INDUSTRY_WEIGHTS)
    bands = rng.choice(EMPLOYEE_BANDS, size=n, p=EMPLOYEE_WEIGHTS)
    countries = rng.choice(COUNTRIES, size=n, p=COUNTRY_WEIGHTS)
    channels = rng.choice(CHANNELS, size=n, p=CHANNEL_WEIGHTS)

    customers = pd.DataFrame({
        "customer_id": customer_ids,
        "signup_date": signup_dates,
        "company_name": [f"Company {i:05d}" for i in range(1, n + 1)],
        "industry": industries,
        "employee_band": bands,
        "country": countries,
        "acquisition_channel": channels,
    })

    # customers_history: SCD2 source. Row 1 = as-signed at signup. ~15% get one
    # later attribute-change event (band growth or industry reclassification).
    history_rows = []
    for _, c in customers.iterrows():
        history_rows.append({
            "customer_id": c.customer_id,
            "version_no": 1,
            "industry": c.industry,
            "employee_band": c.employee_band,
            "country": c.country,
            "acquisition_channel": c.acquisition_channel,
            "company_name": c.company_name,
            "effective_date": c.signup_date,
        })
        if rng.random() < 0.15:
            days_after = int(rng.integers(90, 900))
            change_date = c.signup_date + timedelta(days=days_after)
            if change_date <= DATA_END:
                new_band = c.employee_band
                if rng.random() < 0.7:
                    idx = EMPLOYEE_BANDS.index(c.employee_band)
                    new_band = EMPLOYEE_BANDS[min(idx + 1, len(EMPLOYEE_BANDS) - 1)]
                new_industry = c.industry
                if rng.random() < 0.15:
                    new_industry = rng.choice(INDUSTRIES, p=INDUSTRY_WEIGHTS)
                history_rows.append({
                    "customer_id": c.customer_id,
                    "version_no": 2,
                    "industry": new_industry,
                    "employee_band": new_band,
                    "country": c.country,
                    "acquisition_channel": c.acquisition_channel,
                    "company_name": c.company_name,
                    "effective_date": change_date,
                })

    customers_history = pd.DataFrame(history_rows)
    return customers, customers_history


# ---------------------------------------------------------------------------
# 3-5. subscriptions, plan_changes, invoices, payments
# ---------------------------------------------------------------------------

TIER_MONTHLY_CHURN_BASE = {"Starter": 0.045, "Growth": 0.030, "Scale": 0.020, "Enterprise": 0.012}


def churn_hazard(tier: str, tenure_months: int) -> float:
    base = TIER_MONTHLY_CHURN_BASE[tier]
    if tenure_months <= 1:
        return base * 2.6
    if tenure_months <= 3:
        return base * 1.8
    if tenure_months <= 6:
        return base * 1.2
    return base


def build_subscriptions_and_downstream(customers: pd.DataFrame):
    subs = []
    plan_changes = []
    sub_counter = 1
    change_counter = 1

    for _, c in customers.iterrows():
        cid = c.customer_id
        cursor_start = c.signup_date
        prev_sub_id = None
        is_reactivation = False
        # a customer may churn and reactivate up to twice
        for attempt in range(3):
            if cursor_start > DATA_END:
                break
            sub_id = f"SUB-{sub_counter:06d}"
            sub_counter += 1

            on_trial = (attempt == 0) and (rng.random() < 0.55)
            trial_start = cursor_start if on_trial else None
            trial_end = cursor_start + timedelta(days=14) if on_trial else None

            converts = True
            if on_trial and rng.random() < 0.30:
                converts = False

            tier = str(rng.choice(TIERS, p=TIER_WEIGHTS)) if not is_reactivation else prev_tier
            interval = "annual" if rng.random() < 0.22 else "monthly"

            paid_start = trial_end if on_trial else cursor_start

            if on_trial and not converts:
                subs.append({
                    "subscription_id": sub_id, "customer_id": cid, "plan_id": None,
                    "tier": tier, "billing_interval": interval,
                    "start_date": None, "trial_start_date": trial_start,
                    "trial_end_date": trial_end, "initial_mrr": 0.0,
                    "status": "trial_expired", "cancel_date": trial_end,
                    "cancel_reason": "trial_not_converted",
                    "is_reactivation": is_reactivation,
                    "reactivated_from_subscription_id": prev_sub_id,
                })
                break  # this customer's journey ends (no paid history)

            plan_id = plan_version_id(tier, paid_start)
            monthly_price = plan_price_on(tier, paid_start)
            mrr = monthly_price if interval == "monthly" else round(monthly_price * ANNUAL_DISCOUNT_MULT, 2)

            # simulate month-by-month tenure to find churn date (or right-censor at DATA_END)
            tenure = 0
            cur_month = paid_start
            churned_date = None
            cur_mrr = mrr
            cur_plan_id = plan_id
            cur_tier = tier
            last_change_month = 0
            n_changes_this_sub = 0
            max_changes = int(rng.integers(0, 3))

            while True:
                tenure += 1
                cur_month = cur_month + relativedelta(months=1)
                if cur_month > DATA_END:
                    break
                haz = churn_hazard(cur_tier, tenure)
                if rng.random() < haz:
                    churned_date = cur_month
                    break
                # possible plan change
                if n_changes_this_sub < max_changes and tenure - last_change_month >= 2 and rng.random() < 0.06:
                    upgrade = rng.random() < 0.68
                    tier_idx = TIERS.index(cur_tier)
                    if upgrade and tier_idx < len(TIERS) - 1:
                        new_tier = TIERS[tier_idx + 1]
                        change_type = "upgrade"
                    elif not upgrade and tier_idx > 0:
                        new_tier = TIERS[tier_idx - 1]
                        change_type = "downgrade"
                    else:
                        new_tier = cur_tier
                        change_type = None
                    if change_type:
                        new_plan_id = plan_version_id(new_tier, cur_month)
                        new_monthly = plan_price_on(new_tier, cur_month)
                        new_mrr = new_monthly if interval == "monthly" else round(new_monthly * ANNUAL_DISCOUNT_MULT, 2)
                        plan_changes.append({
                            "change_id": f"CHG-{change_counter:06d}", "subscription_id": sub_id,
                            "change_date": cur_month, "change_type": change_type,
                            "old_plan_id": cur_plan_id, "new_plan_id": new_plan_id,
                            "old_mrr": cur_mrr, "new_mrr": new_mrr,
                        })
                        change_counter += 1
                        cur_plan_id, cur_mrr, cur_tier = new_plan_id, new_mrr, new_tier
                        n_changes_this_sub += 1
                        last_change_month = tenure

            status = "canceled" if churned_date else "active"
            involuntary = churned_date is not None and rng.random() < 0.12
            cancel_reason = None
            if churned_date:
                cancel_reason = "payment_failed" if involuntary else str(
                    rng.choice(CANCEL_REASONS[:-1], p=np.array(CANCEL_REASON_WEIGHTS[:-1]) / sum(CANCEL_REASON_WEIGHTS[:-1]))
                )

            subs.append({
                "subscription_id": sub_id, "customer_id": cid, "plan_id": cur_plan_id,
                "tier": cur_tier, "billing_interval": interval,
                "start_date": paid_start, "trial_start_date": trial_start,
                "trial_end_date": trial_end, "initial_mrr": mrr,
                "status": status, "cancel_date": churned_date,
                "cancel_reason": cancel_reason,
                "is_reactivation": is_reactivation,
                "reactivated_from_subscription_id": prev_sub_id,
                "_final_mrr": cur_mrr, "_final_plan_id": cur_plan_id, "_final_tier": cur_tier,
                "_paid_start": paid_start,
            })

            if not churned_date:
                break  # still active through DATA_END, no further reactivation attempts
            # decide reactivation
            if rng.random() < 0.16:
                gap_months = int(rng.integers(1, 10))
                cursor_start = churned_date + relativedelta(months=gap_months)
                prev_sub_id = sub_id
                prev_tier = cur_tier
                is_reactivation = True
                continue
            break

    subs_df = pd.DataFrame(subs)
    plan_changes_df = pd.DataFrame(plan_changes)
    return subs_df, plan_changes_df


def build_invoices_and_payments(subs_df: pd.DataFrame, plan_changes_df: pd.DataFrame):
    invoices = []
    payments = []
    inv_counter = 1
    pay_counter = 1

    pc_by_sub = {}
    if not plan_changes_df.empty:
        for sub_id, grp in plan_changes_df.sort_values("change_date").groupby("subscription_id"):
            pc_by_sub[sub_id] = grp.to_dict("records")

    paid_subs = subs_df[subs_df["start_date"].notna()]

    for _, s in paid_subs.iterrows():
        start = s.start_date
        end = s.cancel_date if pd.notna(s.cancel_date) else DATA_END
        interval_months = 12 if s.billing_interval == "annual" else 1
        changes = pc_by_sub.get(s.subscription_id, [])

        cur_mrr = s.initial_mrr
        cur_plan_id = s.plan_id
        change_idx = 0
        cur_date = start
        while cur_date <= end:
            # apply any plan changes effective at/before this billing date
            while change_idx < len(changes) and changes[change_idx]["change_date"] <= cur_date:
                cur_mrr = changes[change_idx]["new_mrr"]
                cur_plan_id = changes[change_idx]["new_plan_id"]
                change_idx += 1

            invoice_id = f"INV-{inv_counter:07d}"
            inv_counter += 1
            amount_due = round(cur_mrr * interval_months, 2)
            invoices.append({
                "invoice_id": invoice_id, "subscription_id": s.subscription_id,
                "customer_id": s.customer_id, "plan_id": cur_plan_id,
                "invoice_date": cur_date,
                "period_start": cur_date,
                "period_end": cur_date + relativedelta(months=interval_months) - timedelta(days=1),
                "amount_due": amount_due,
            })

            # payment behavior
            pay_date = cur_date + timedelta(days=int(rng.integers(0, 4)))
            fail_first = rng.random() < 0.05
            refunded = rng.random() < 0.02
            if fail_first:
                payments.append({
                    "payment_id": f"PAY-{pay_counter:07d}", "invoice_id": invoice_id,
                    "payment_date": pay_date, "amount": amount_due, "status": "failed",
                    "refund_amount": None, "refund_date": None,
                })
                pay_counter += 1
                retry_success = rng.random() < 0.6
                if retry_success:
                    retry_date = pay_date + timedelta(days=int(rng.integers(2, 6)))
                    payments.append({
                        "payment_id": f"PAY-{pay_counter:07d}", "invoice_id": invoice_id,
                        "payment_date": retry_date, "amount": amount_due, "status": "succeeded",
                        "refund_amount": None, "refund_date": None,
                    })
                    pay_counter += 1
            else:
                refund_amount = None
                refund_date = None
                status = "succeeded"
                if refunded:
                    refund_amount = round(amount_due * (1.0 if rng.random() < 0.4 else rng.uniform(0.2, 0.8)), 2)
                    refund_date = pay_date + timedelta(days=int(rng.integers(1, 20)))
                    status = "refunded"
                payments.append({
                    "payment_id": f"PAY-{pay_counter:07d}", "invoice_id": invoice_id,
                    "payment_date": pay_date, "amount": amount_due, "status": status,
                    "refund_amount": refund_amount, "refund_date": refund_date,
                })
                pay_counter += 1

            cur_date = cur_date + relativedelta(months=interval_months)

    return pd.DataFrame(invoices), pd.DataFrame(payments)


def build_usage_monthly(subs_df: pd.DataFrame):
    rows = []
    paid_subs = subs_df[subs_df["start_date"].notna()]
    for _, s in paid_subs.iterrows():
        start = s.start_date
        end = s.cancel_date if pd.notna(s.cancel_date) else DATA_END
        for m in month_range(start, end):
            month_end = m + relativedelta(months=1)
            tenure_days = (min(month_end, end) - m).days
            if tenure_days <= 0:
                continue
            months_to_churn = None
            if pd.notna(s.cancel_date):
                months_to_churn = (s.cancel_date.year - m.year) * 12 + (s.cancel_date.month - m.month)
            base_engagement = {"Starter": 8, "Growth": 14, "Scale": 20, "Enterprise": 24}.get(s.tier, 10)
            decay = 1.0
            if months_to_churn is not None and 0 <= months_to_churn <= 2:
                decay = 0.55 if months_to_churn == 0 else (0.7 if months_to_churn == 1 else 0.85)
            login_days = int(np.clip(rng.poisson(base_engagement * decay), 0, 30))
            feature_events = int(np.clip(rng.poisson(base_engagement * decay * 6), 0, None))
            api_calls = int(np.clip(rng.poisson(base_engagement * decay * 40), 0, None))
            rows.append({
                "customer_id": s.customer_id, "subscription_id": s.subscription_id,
                "usage_month": m, "login_days": login_days,
                "feature_events": feature_events, "api_calls": api_calls,
            })
    return pd.DataFrame(rows)


def main():
    print(f"Generating synthetic dataset (seed={SEED})...")
    plans_history = build_plans_history()
    customers, customers_history = build_customers()
    subs_df, plan_changes_df = build_subscriptions_and_downstream(customers)
    invoices_df, payments_df = build_invoices_and_payments(subs_df, plan_changes_df)
    usage_df = build_usage_monthly(subs_df)

    subs_out = subs_df.drop(columns=[c for c in ["_final_mrr", "_final_plan_id", "_final_tier", "_paid_start"] if c in subs_df.columns])

    plans_history.to_csv(OUT_DIR / "plans_history.csv", index=False)
    customers.to_csv(OUT_DIR / "customers.csv", index=False)
    customers_history.to_csv(OUT_DIR / "customers_history.csv", index=False)
    subs_out.to_csv(OUT_DIR / "subscriptions.csv", index=False)
    plan_changes_df.to_csv(OUT_DIR / "plan_changes.csv", index=False)
    invoices_df.to_csv(OUT_DIR / "invoices.csv", index=False)
    payments_df.to_csv(OUT_DIR / "payments.csv", index=False)
    usage_df.to_csv(OUT_DIR / "usage_monthly.csv", index=False)

    print("Row counts:")
    for name, df in [
        ("plans_history", plans_history), ("customers", customers),
        ("customers_history", customers_history), ("subscriptions", subs_out),
        ("plan_changes", plan_changes_df), ("invoices", invoices_df),
        ("payments", payments_df), ("usage_monthly", usage_df),
    ]:
        print(f"  {name:20s} {len(df):>8,d}")
    print(f"\nWrote CSVs to {OUT_DIR}")


if __name__ == "__main__":
    main()
