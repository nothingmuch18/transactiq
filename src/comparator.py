"""
Comparative Analysis Module — Compare two groups, periods, or categories.
"""
import pandas as pd
import numpy as np
from src.utils import format_currency, format_number, format_pct, safe_divide


def compare_groups(df, column, group_a, group_b, amount_col, metadata=None):
    """
    Compare two groups within a categorical column.
    Returns comparison metrics and DataFrames.
    """
    df_a = df[df[column].str.lower() == group_a.lower()]
    df_b = df[df[column].str.lower() == group_b.lower()]

    if len(df_a) == 0 and len(df_b) == 0:
        return None

    metrics = _compute_comparison(df_a, df_b, amount_col, group_a, group_b)
    return metrics


def compare_time_periods(df, date_col, amount_col, period_a, period_b):
    """
    Compare two time periods (months, quarters).
    period_a, period_b: strings like '2024-01', '2024-Q1', etc.
    """
    df = df.copy()
    df['_month'] = df[date_col].dt.to_period('M').astype(str)
    df['_quarter'] = df[date_col].dt.to_period('Q').astype(str)

    # Try month match
    df_a = df[df['_month'] == period_a]
    df_b = df[df['_month'] == period_b]

    if len(df_a) == 0:
        df_a = df[df['_quarter'] == period_a]
    if len(df_b) == 0:
        df_b = df[df['_quarter'] == period_b]

    if len(df_a) == 0 and len(df_b) == 0:
        return None

    metrics = _compute_comparison(df_a, df_b, amount_col, period_a, period_b)
    return metrics


def _compute_comparison(df_a, df_b, amount_col, label_a, label_b):
    """Compute comparison table between two DataFrames."""
    a_count = len(df_a)
    b_count = len(df_b)
    a_sum = df_a[amount_col].sum() if a_count > 0 else 0
    b_sum = df_b[amount_col].sum() if b_count > 0 else 0
    a_avg = df_a[amount_col].mean() if a_count > 0 else 0
    b_avg = df_b[amount_col].mean() if b_count > 0 else 0
    a_median = df_a[amount_col].median() if a_count > 0 else 0
    b_median = df_b[amount_col].median() if b_count > 0 else 0
    a_max = df_a[amount_col].max() if a_count > 0 else 0
    b_max = df_b[amount_col].max() if b_count > 0 else 0

    comparison_df = pd.DataFrame({
        'Metric': ['Transaction Count', 'Total Value (INR)', 'Average Value (INR)',
                   'Median Value (INR)', 'Max Transaction (INR)'],
        label_a.title(): [a_count, round(a_sum, 2), round(a_avg, 2), round(a_median, 2), round(a_max, 2)],
        label_b.title(): [b_count, round(b_sum, 2), round(b_avg, 2), round(b_median, 2), round(b_max, 2)],
    })

    comparison_df['Absolute Diff'] = comparison_df[label_a.title()] - comparison_df[label_b.title()]
    comparison_df['% Difference'] = comparison_df.apply(
        lambda row: round(safe_divide(row['Absolute Diff'], row[label_b.title()]) * 100, 2), axis=1
    )

    # Winner
    comparison_df['Higher'] = comparison_df.apply(
        lambda row: label_a.title() if row[label_a.title()] > row[label_b.title()] else label_b.title(), axis=1
    )

    # Explanation
    value_diff = a_sum - b_sum
    value_pct = safe_divide(value_diff, b_sum) * 100

    explanation = (
        f"**{label_a.title()}** vs **{label_b.title()}**: "
        f"{'higher' if value_diff > 0 else 'lower'} total value by **{format_pct(value_pct)}** "
        f"({format_currency(abs(value_diff))}). "
        f"Volume: {format_number(a_count)} vs {format_number(b_count)} transactions."
    )

    return {
        'comparison_df': comparison_df,
        'explanation': explanation,
        'label_a': label_a.title(),
        'label_b': label_b.title(),
        'chart_data': pd.DataFrame({
            'Metric': ['Total Value', 'Avg Value', 'Volume'],
            label_a.title(): [a_sum, a_avg, a_count],
            label_b.title(): [b_sum, b_avg, b_count],
        })
    }


def get_available_comparisons(df, metadata):
    """Return available comparison dimensions."""
    roles = metadata.get('roles', {})
    comparisons = {}

    for col_key, label in [('region', 'States'), ('category', 'Categories'),
                            ('sender_bank', 'Sender Banks'), ('transaction_type', 'Transaction Types')]:
        col = roles.get(col_key)
        if col and col in df.columns:
            comparisons[label] = {
                'column': col,
                'values': sorted(df[col].dropna().unique().tolist())
            }

    # Time-based comparisons
    date_col = roles.get('date')
    if date_col:
        months = sorted(df[date_col].dt.to_period('M').unique().astype(str).tolist())
        if months:
            comparisons['Months'] = {'column': '_month', 'values': months}
        quarters = sorted(df[date_col].dt.to_period('Q').unique().astype(str).tolist())
        if quarters:
            comparisons['Quarters'] = {'column': '_quarter', 'values': quarters}

    return comparisons
