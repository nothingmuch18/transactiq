"""
Intelligent Insight Engine — Auto-generates 8-10 financial insights from data.
"""
import pandas as pd
import numpy as np
from src.utils import format_currency, format_number, format_pct, safe_divide


def generate_insights(df, metadata):
    """
    Auto-generate 8-10 meaningful financial insights.
    Returns a list of dicts: {title, description, category, value, icon}
    """
    insights = []
    roles = metadata.get('roles', {})
    amount_col = roles.get('amount')
    date_col = roles.get('date')
    region_col = roles.get('region')
    category_col = roles.get('category')

    if not amount_col:
        return [{'title': 'No Amount Column', 'description': 'Cannot generate financial insights without a value column.', 'category': 'error', 'icon': '⚠️'}]

    # 1. Total Volume & Value
    total_value = df[amount_col].sum()
    total_count = len(df)
    avg_value = df[amount_col].mean()
    insights.append({
        'title': 'Total Transaction Volume',
        'description': f"**{format_number(total_count)}** transactions totaling **{format_currency(total_value)}** with average size **{format_currency(avg_value)}**.",
        'category': 'overview',
        'icon': '📊',
        'why': f"Computed by summing all {total_count:,} rows in the dataset. Average = Total Value / Count."
    })

    # 2. Monthly Growth Analysis
    if date_col:
        monthly = df.set_index(date_col).resample('M')[amount_col].agg(['sum', 'count'])
        monthly.columns = ['Total Value', 'Volume']
        if len(monthly) >= 2:
            growth_rates = monthly['Total Value'].pct_change() * 100
            avg_growth = growth_rates.mean()
            last_growth = growth_rates.iloc[-1] if len(growth_rates) > 0 else 0

            # CAGR-like compound growth
            first_val = monthly['Total Value'].iloc[0]
            last_val = monthly['Total Value'].iloc[-1]
            n_months = len(monthly)
            if first_val > 0 and last_val > 0:
                compound_rate = ((last_val / first_val) ** (1 / n_months) - 1) * 100
            else:
                compound_rate = 0

            direction = "📈" if avg_growth > 0 else "📉"
            insights.append({
                'title': 'Monthly Growth Trend',
                'description': f"Average monthly growth: **{format_pct(avg_growth)}**. Compound monthly rate: **{format_pct(compound_rate)}**. Latest month: **{format_pct(last_growth)}**.",
                'category': 'growth',
                'icon': direction,
                'why': f"Growth rates computed as month-over-month percentage change. Compound rate uses formula: (Last/First)^(1/N)-1 over {n_months} months."
            })

    # 3. Peak Transaction Period
    if date_col:
        monthly_value = df.set_index(date_col).resample('M')[amount_col].sum()
        if len(monthly_value) > 0:
            peak_month = monthly_value.idxmax()
            peak_value = monthly_value.max()
            low_month = monthly_value.idxmin()
            low_value = monthly_value.min()
            insights.append({
                'title': 'Peak & Low Activity Periods',
                'description': f"Highest: **{peak_month.strftime('%B %Y')}** ({format_currency(peak_value)}). Lowest: **{low_month.strftime('%B %Y')}** ({format_currency(low_value)}). Spread: **{format_pct(safe_divide(peak_value - low_value, low_value) * 100)}**.",
                'category': 'timing',
                'icon': '🏔️',
                'why': f"Peak identified by finding the month with maximum total value. The {format_pct(safe_divide(peak_value - low_value, low_value) * 100)} spread suggests {'high' if safe_divide(peak_value - low_value, low_value) > 0.5 else 'moderate'} seasonality."
            })

    # 4. Top Contributing Region
    if region_col:
        state_totals = df.groupby(region_col)[amount_col].sum().sort_values(ascending=False)
        top_state = state_totals.index[0]
        top_share = state_totals.iloc[0] / total_value * 100
        top3_share = state_totals.head(3).sum() / total_value * 100
        insights.append({
            'title': 'Regional Dominance',
            'description': f"**{top_state}** leads with **{top_share:.1f}%** of total value. Top 3 states control **{top3_share:.1f}%**.",
            'category': 'concentration',
            'icon': '🗺️',
            'why': f"{top_state} dominates because it has the highest aggregate transaction value. Top 3 controlling {top3_share:.1f}% indicates {'high' if top3_share > 50 else 'moderate'} geographical concentration."
        })

    # 5. Category Distribution
    if category_col:
        cat_totals = df.groupby(category_col)[amount_col].sum().sort_values(ascending=False)
        top_cat = cat_totals.index[0]
        top_cat_share = cat_totals.iloc[0] / total_value * 100
        insights.append({
            'title': 'Top Spending Category',
            'description': f"**{top_cat}** dominates with **{top_cat_share:.1f}%** of total transaction value ({format_currency(cat_totals.iloc[0])}).",
            'category': 'category',
            'icon': '🏷️',
            'why': f"{top_cat} leads because it has the highest sum of transaction amounts across all records. This reflects {'dominant' if top_cat_share > 30 else 'significant'} spending in this category."
        })

    # 6. Transaction Size Distribution (Skewness)
    skewness = df[amount_col].skew()
    median_val = df[amount_col].median()
    p95 = df[amount_col].quantile(0.95)
    high_value_count = len(df[df[amount_col] > p95])
    high_value_share = df[df[amount_col] > p95][amount_col].sum() / total_value * 100

    skew_desc = "right-skewed (many small, few large)" if skewness > 1 else "moderately skewed" if skewness > 0.5 else "approximately symmetric"
    insights.append({
        'title': 'Value Distribution & Skewness',
        'description': f"Distribution is **{skew_desc}** (skew={skewness:.2f}). Median: **{format_currency(median_val)}** vs Mean: **{format_currency(avg_value)}**. Top 5% of transactions hold **{high_value_share:.1f}%** of total value.",
        'category': 'distribution',
        'icon': '📐',
        'why': f"Skewness of {skewness:.2f} means {'most transactions are small but a few very large ones pull the mean up' if skewness > 1 else 'values are relatively evenly distributed'}. The gap between mean ({format_currency(avg_value)}) and median ({format_currency(median_val)}) confirms this."
    })

    # 7. Failure Rate Analysis
    status_col = roles.get('status')
    if status_col:
        status_counts = df[status_col].value_counts()
        failed = status_counts.get('FAILED', 0)
        failure_rate = safe_divide(failed, total_count) * 100
        failed_value = df[df[status_col] == 'FAILED'][amount_col].sum() if failed > 0 else 0
        insights.append({
            'title': 'Transaction Failure Analysis',
            'description': f"Failure rate: **{failure_rate:.2f}%** ({format_number(failed)} failed). Value at risk from failures: **{format_currency(failed_value)}**.",
            'category': 'risk',
            'icon': '⚠️',
            'why': f"{format_number(failed)} transactions out of {format_number(total_count)} failed, representing {format_currency(failed_value)} in potentially lost value. {'This rate is within normal range.' if failure_rate < 5 else 'This rate is elevated and warrants investigation.'}"
        })

    # 8. Fraud Detection Summary
    fraud_col = roles.get('fraud')
    if fraud_col:
        fraud_count = int(df[fraud_col].sum())
        fraud_rate = safe_divide(fraud_count, total_count) * 100
        fraud_value = df[df[fraud_col] == 1][amount_col].sum() if fraud_count > 0 else 0
        insights.append({
            'title': 'Fraud Risk Assessment',
            'description': f"**{fraud_count}** transactions flagged as fraudulent (**{fraud_rate:.3f}%** rate). Fraud-flagged value: **{format_currency(fraud_value)}**.",
            'category': 'fraud',
            'icon': '🚨',
            'why': f"Fraud flag column indicates {fraud_count} suspicious transactions. {'Rate is below industry average (<0.1%), suggesting good controls.' if fraud_rate < 0.1 else 'Rate exceeds typical thresholds and should be monitored.'}"
        })

    # 9. Weekend vs Weekday Pattern
    if 'is_weekend' in df.columns:
        weekend_val = df[df['is_weekend'] == 1][amount_col].sum()
        weekday_val = df[df['is_weekend'] == 0][amount_col].sum()
        weekend_share = safe_divide(weekend_val, total_value) * 100
        weekend_avg = df[df['is_weekend'] == 1][amount_col].mean()
        weekday_avg = df[df['is_weekend'] == 0][amount_col].mean()
        insights.append({
            'title': 'Weekend vs Weekday Behavior',
            'description': f"Weekends account for **{weekend_share:.1f}%** of total value. Avg weekend txn: **{format_currency(weekend_avg)}** vs weekday: **{format_currency(weekday_avg)}**.",
            'category': 'pattern',
            'icon': '📅',
            'why': f"Weekends (2/7 days = 28.6% of time) account for {weekend_share:.1f}% of value. {'Higher than proportional — weekend spending is elevated.' if weekend_share > 30 else 'Lower than proportional — weekday activity dominates.'}"
        })

    # 10. Volatility Index
    if date_col:
        monthly_vals = df.set_index(date_col).resample('M')[amount_col].sum()
        if len(monthly_vals) >= 3:
            volatility = monthly_vals.std() / monthly_vals.mean() * 100
            vol_desc = "low" if volatility < 10 else "moderate" if volatility < 25 else "high"
            insights.append({
                'title': 'Monthly Value Volatility',
                'description': f"Coefficient of variation: **{volatility:.1f}%** ({vol_desc} volatility). Stable month-to-month values indicate predictable transaction patterns.",
                'category': 'risk',
                'icon': '📊',
                'why': f"CV = Standard Deviation / Mean × 100 = {volatility:.1f}%. {'Low CV means monthly totals are consistent and predictable.' if volatility < 15 else 'High CV suggests significant month-to-month variation, possibly due to seasonality or growth.'}"
            })

    return insights
