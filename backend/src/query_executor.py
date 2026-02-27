"""
Query Execution Engine — Takes structured JSON plans and executes them via Pandas.
Returns result DataFrame, chart specification, explanation, and execution time.
"""
import time
import pandas as pd
import numpy as np
from src.utils import format_currency, format_number, safe_match_column, get_numeric_columns


def apply_filters(df, filters):
    """Apply a list of filter conditions to DataFrame."""
    filtered = df.copy()
    for f in filters:
        col = f['column']
        op = f['op']
        val = f['value']
        if col not in filtered.columns:
            continue
        if op == '==':
            filtered = filtered[filtered[col] == val]
        elif op == '!=':
            filtered = filtered[filtered[col] != val]
        elif op == '>':
            filtered = filtered[filtered[col] > val]
        elif op == '<':
            filtered = filtered[filtered[col] < val]
        elif op == '>=':
            filtered = filtered[filtered[col] >= val]
        elif op == '<=':
            filtered = filtered[filtered[col] <= val]
        elif op == 'in':
            filtered = filtered[filtered[col].isin(val)]
    return filtered


def resolve_group_column(df, group_by, metadata):
    """Resolve a group_by key to actual DataFrame operations."""
    roles = metadata.get('roles', {})
    date_col = roles.get('date')

    if group_by == 'month' and date_col:
        df = df.copy()
        df['_month'] = df[date_col].dt.to_period('M').astype(str)
        return df, '_month'
    elif group_by == 'quarter' and date_col:
        df = df.copy()
        df['_quarter'] = df[date_col].dt.to_period('Q').astype(str)
        return df, '_quarter'
    elif group_by == 'week' and date_col:
        df = df.copy()
        df['_week'] = df[date_col].dt.to_period('W').astype(str)
        return df, '_week'
    elif group_by in df.columns:
        return df, group_by
    else:
        # Try matching
        matched = safe_match_column(df, group_by)
        if matched:
            return df, matched
    return df, group_by


def execute_plan(plan, df, metadata):
    """
    Execute a structured query plan against the DataFrame.
    Returns dict with: result_df, chart_spec, explanation, exec_time_ms
    """
    start = time.time()

    intent = plan.get('intent', 'general')
    agg = plan.get('aggregation', 'sum')
    metric_col = plan.get('metric_column')
    group_by = plan.get('group_by')
    filters = plan.get('filters', [])
    k = plan.get('k', 10)
    viz = plan.get('visualization', 'table')
    roles = metadata.get('roles', {})

    # Resolve metric column
    amount_col = roles.get('amount')
    if metric_col == '__count__' or metric_col is None:
        use_count = True
        display_metric = 'Transaction Count'
    else:
        use_count = False
        if metric_col in df.columns:
            display_metric = metric_col
        else:
            matched = safe_match_column(df, metric_col)
            if matched:
                display_metric = matched
                metric_col = matched
            else:
                use_count = True
                display_metric = 'Transaction Count'

    # Apply filters
    filtered = apply_filters(df, filters)
    filter_desc = ""
    if filters:
        parts = [f"{f['column']} {f['op']} {f['value']}" for f in filters]
        filter_desc = "Filters applied: " + ", ".join(parts)

    result_df = pd.DataFrame()
    explanation = ""

    # --- Execute based on intent ---
    if intent in ('total_volume', 'total_value', 'average_value'):
        if intent == 'total_volume':
            val = len(filtered)
            explanation = f"Total number of transactions: **{format_number(val)}**"
            result_df = pd.DataFrame([{'Metric': 'Total Transactions', 'Value': val}])
        elif intent == 'total_value':
            if amount_col:
                val = filtered[amount_col].sum()
                explanation = f"Total transaction value: **{format_currency(val)}**"
                result_df = pd.DataFrame([{'Metric': 'Total Value (INR)', 'Value': val}])
            else:
                explanation = "No amount column detected in dataset."
                result_df = pd.DataFrame([{'Metric': 'Error', 'Value': 'No amount column'}])
        elif intent == 'average_value':
            if amount_col:
                val = filtered[amount_col].mean()
                explanation = f"Average transaction value: **{format_currency(val)}**"
                result_df = pd.DataFrame([{'Metric': 'Average Value (INR)', 'Value': round(val, 2)}])
            else:
                explanation = "No amount column detected."
                result_df = pd.DataFrame([{'Metric': 'Error', 'Value': 'No amount column'}])
        viz = 'metric'

    elif intent in ('trend_analysis', 'month_over_month', 'peak_analysis'):
        if group_by:
            filtered, actual_group = resolve_group_column(filtered, group_by, metadata)
            if actual_group in filtered.columns:
                if use_count:
                    grouped = filtered.groupby(actual_group).size().reset_index(name='Count')
                    grouped = grouped.sort_values(actual_group)
                    result_df = grouped
                    explanation = f"Transaction count by **{group_by}**."
                else:
                    if agg == 'sum':
                        grouped = filtered.groupby(actual_group)[metric_col].sum().reset_index()
                    elif agg == 'mean':
                        grouped = filtered.groupby(actual_group)[metric_col].mean().round(2).reset_index()
                    elif agg == 'count':
                        grouped = filtered.groupby(actual_group)[metric_col].count().reset_index()
                    elif agg == 'max':
                        grouped = filtered.groupby(actual_group)[metric_col].max().reset_index()
                    elif agg == 'min':
                        grouped = filtered.groupby(actual_group)[metric_col].min().reset_index()
                    else:
                        grouped = filtered.groupby(actual_group)[metric_col].sum().reset_index()
                    grouped = grouped.sort_values(actual_group)
                    result_df = grouped
                    explanation = f"{agg.title()} of **{display_metric}** by **{group_by}**."

                if intent == 'month_over_month' and len(result_df) >= 2:
                    val_col = result_df.columns[-1]
                    result_df['MoM Growth %'] = result_df[val_col].pct_change() * 100
                    result_df['MoM Growth %'] = result_df['MoM Growth %'].round(2)
                    explanation += " Month-over-month growth rates calculated."

                if intent == 'peak_analysis':
                    val_col = result_df.columns[-1] if len(result_df.columns) >= 2 else result_df.columns[0]
                    if len(result_df) > 0:
                        peak_row = result_df.loc[result_df[val_col].idxmax()]
                        explanation += f" Peak: **{peak_row.iloc[0]}** with {format_number(peak_row[val_col])}."
            else:
                explanation = f"Could not resolve group column: {group_by}"
                result_df = filtered.head(20)
        else:
            explanation = "No group-by column detected. Showing raw data."
            result_df = filtered.head(20)

        # Add 'Why?' reasoning for trend
        if intent == 'trend_analysis' and len(result_df) >= 2:
            val_col = result_df.columns[-1]
            first_val = result_df[val_col].iloc[0]
            last_val = result_df[val_col].iloc[-1]
            if first_val > 0:
                overall_change = ((last_val / first_val) - 1) * 100
                direction = "increased" if overall_change > 0 else "decreased"
                explanation += (f"\n\n**Why this trend?** Over the observed period, "
                              f"values {direction} by **{overall_change:+.1f}%** "
                              f"from {format_number(first_val)} to {format_number(last_val)}.")
                # Find biggest jump
                changes = result_df[val_col].pct_change() * 100
                if len(changes.dropna()) > 0:
                    max_change_idx = changes.abs().idxmax()
                    max_change = changes.loc[max_change_idx]
                    period = result_df.iloc[max_change_idx][result_df.columns[0]]
                    explanation += (f" Largest single-period change: **{max_change:+.1f}%** "
                                  f"at **{period}**.")

    elif intent in ('top_k', 'bottom_k'):
        if group_by:
            filtered, actual_group = resolve_group_column(filtered, group_by, metadata)
            if actual_group in filtered.columns:
                if use_count:
                    grouped = filtered.groupby(actual_group).size().reset_index(name='Count')
                    sort_col = 'Count'
                else:
                    if agg == 'mean':
                        grouped = filtered.groupby(actual_group)[metric_col].mean().round(2).reset_index()
                    else:
                        grouped = filtered.groupby(actual_group)[metric_col].sum().reset_index()
                    sort_col = metric_col

                ascending = intent == 'bottom_k'
                grouped = grouped.sort_values(sort_col, ascending=ascending).head(k).reset_index(drop=True)
                result_df = grouped
                direction = "Bottom" if intent == 'bottom_k' else "Top"
                explanation = f"{direction} {k} **{actual_group}** by {agg} of **{display_metric}**."
            else:
                explanation = f"Could not resolve group column: {group_by}"
                result_df = filtered.head(k)
        else:
            if amount_col and not use_count:
                ascending = intent == 'bottom_k'
                result_df = filtered.nsmallest(k, amount_col) if ascending else filtered.nlargest(k, amount_col)
                result_df = result_df.reset_index(drop=True)
                direction = "Bottom" if intent == 'bottom_k' else "Top"
                explanation = f"{direction} {k} transactions by **{amount_col}**."
            else:
                result_df = filtered.head(k)
                explanation = f"Showing first {k} records."

    elif intent == 'distribution':
        if group_by:
            filtered, actual_group = resolve_group_column(filtered, group_by, metadata)
            if actual_group in filtered.columns:
                if use_count:
                    grouped = filtered.groupby(actual_group).size().reset_index(name='Count')
                    grouped['Share %'] = (grouped['Count'] / grouped['Count'].sum() * 100).round(2)
                else:
                    grouped = filtered.groupby(actual_group)[metric_col].sum().reset_index()
                    grouped['Share %'] = (grouped[metric_col] / grouped[metric_col].sum() * 100).round(2)
                grouped = grouped.sort_values('Share %', ascending=False)
                result_df = grouped
                explanation = f"Distribution of **{display_metric}** by **{actual_group}**."
        else:
            explanation = "No grouping column detected for distribution."
            result_df = filtered.head(20)

    elif intent == 'fraud':
        fraud_col = roles.get('fraud')
        if fraud_col:
            total = len(filtered)
            fraud_count = int(filtered[fraud_col].sum())
            fraud_rate = round(fraud_count / total * 100, 3) if total > 0 else 0

            if group_by:
                filtered, actual_group = resolve_group_column(filtered, group_by, metadata)
                if actual_group in filtered.columns:
                    grouped = filtered.groupby(actual_group).agg(
                        Total=(fraud_col, 'count'),
                        Fraud_Count=(fraud_col, 'sum')
                    ).reset_index()
                    grouped['Fraud Rate %'] = (grouped['Fraud_Count'] / grouped['Total'] * 100).round(3)
                    grouped = grouped.sort_values('Fraud Rate %', ascending=False)
                    result_df = grouped
                    explanation = f"Fraud analysis by **{actual_group}**. Overall fraud rate: **{fraud_rate}%**."
                else:
                    result_df = pd.DataFrame([{'Total': total, 'Fraud Count': fraud_count, 'Fraud Rate %': fraud_rate}])
                    explanation = f"Overall fraud rate: **{fraud_rate}%** ({fraud_count} flagged out of {format_number(total)})."
            else:
                result_df = pd.DataFrame([{'Total': total, 'Fraud Count': fraud_count, 'Fraud Rate %': fraud_rate}])
                explanation = f"Overall fraud rate: **{fraud_rate}%** ({fraud_count} flagged out of {format_number(total)})."
        else:
            explanation = "No fraud column detected in dataset."
            result_df = pd.DataFrame()

    elif intent == 'failure_analysis':
        status_col = roles.get('status')
        if not status_col:
            status_col = safe_match_column(df, 'status')
        if status_col:
            if group_by:
                filtered, actual_group = resolve_group_column(filtered, group_by, metadata)
                if actual_group in filtered.columns:
                    grouped = filtered.groupby([actual_group, status_col]).size().reset_index(name='Count')
                    pivot = grouped.pivot_table(index=actual_group, columns=status_col, values='Count', fill_value=0).reset_index()
                    if 'SUCCESS' in pivot.columns and 'FAILED' in pivot.columns:
                        pivot['Success Rate %'] = (pivot['SUCCESS'] / (pivot['SUCCESS'] + pivot['FAILED']) * 100).round(2)
                        pivot = pivot.sort_values('Success Rate %', ascending=True)
                    result_df = pivot
                    explanation = f"Success/Failure analysis by **{actual_group}**."
                else:
                    result_df = filtered[status_col].value_counts().reset_index()
                    result_df.columns = ['Status', 'Count']
                    explanation = "Transaction status distribution."
            else:
                result_df = filtered[status_col].value_counts().reset_index()
                result_df.columns = ['Status', 'Count']
                total = result_df['Count'].sum()
                success = result_df.loc[result_df['Status'] == 'SUCCESS', 'Count'].sum()
                explanation = f"Transaction status: **{success}/{total}** successful ({round(success/total*100, 2)}% success rate)."
        else:
            explanation = "No status column detected."
            result_df = pd.DataFrame()

    elif intent == 'comparison':
        entity_a = plan.get('compare_a')
        entity_b = plan.get('compare_b')
        if entity_a and entity_b:
            # Try to find which column these entities belong to
            comparison_col = None
            for col in filtered.columns:
                if filtered[col].dtype == 'object':
                    vals = filtered[col].str.lower().unique()
                    if entity_a.lower() in vals and entity_b.lower() in vals:
                        comparison_col = col
                        break
                    # Partial match
                    matches_a = [v for v in vals if entity_a.lower() in v]
                    matches_b = [v for v in vals if entity_b.lower() in v]
                    if matches_a and matches_b:
                        comparison_col = col
                        entity_a = matches_a[0]
                        entity_b = matches_b[0]
                        break

            if comparison_col and amount_col:
                group_a = filtered[filtered[comparison_col].str.lower() == entity_a.lower()]
                group_b = filtered[filtered[comparison_col].str.lower() == entity_b.lower()]
                a_sum = group_a[amount_col].sum()
                b_sum = group_b[amount_col].sum()
                a_count = len(group_a)
                b_count = len(group_b)
                a_avg = group_a[amount_col].mean() if a_count > 0 else 0
                b_avg = group_b[amount_col].mean() if b_count > 0 else 0

                result_df = pd.DataFrame({
                    'Metric': ['Total Value (INR)', 'Transaction Count', 'Average Value (INR)'],
                    entity_a.title(): [round(a_sum, 2), a_count, round(a_avg, 2)],
                    entity_b.title(): [round(b_sum, 2), b_count, round(b_avg, 2)],
                    'Difference': [round(a_sum - b_sum, 2), a_count - b_count, round(a_avg - b_avg, 2)],
                    'Diff %': [round((a_sum - b_sum) / b_sum * 100, 2) if b_sum else 0,
                               round((a_count - b_count) / b_count * 100, 2) if b_count else 0,
                               round((a_avg - b_avg) / b_avg * 100, 2) if b_avg else 0],
                })
                explanation = f"Comparison: **{entity_a.title()}** vs **{entity_b.title()}** on column **{comparison_col}**."
                viz = 'grouped_bar'
            else:
                explanation = f"Could not find matching data for comparison between '{entity_a}' and '{entity_b}'."
                result_df = pd.DataFrame()
        else:
            explanation = "Could not extract comparison entities from query."
            result_df = pd.DataFrame()

    elif intent == 'data_quality':
        cols_info = []
        for col in filtered.columns:
            missing = int(filtered[col].isna().sum())
            missing_pct = round(missing / len(filtered) * 100, 2)
            unique = int(filtered[col].nunique())
            cols_info.append({
                'Column': col,
                'Missing': missing,
                'Missing %': missing_pct,
                'Unique Values': unique,
                'Data Type': str(filtered[col].dtype)
            })
        result_df = pd.DataFrame(cols_info)
        dup_count = filtered.duplicated().sum()
        explanation = f"Data quality report: **{len(filtered)}** rows, **{len(filtered.columns)}** columns, **{dup_count}** duplicate rows."
        viz = 'table'

    elif intent == 'concentration':
        if group_by and amount_col:
            filtered, actual_group = resolve_group_column(filtered, group_by, metadata)
            if actual_group in filtered.columns:
                grouped = filtered.groupby(actual_group)[amount_col].sum().reset_index()
                total = grouped[amount_col].sum()
                grouped['Share %'] = (grouped[amount_col] / total * 100).round(2)
                grouped = grouped.sort_values(amount_col, ascending=False)

                # HHI
                shares = grouped['Share %'] / 100
                hhi = (shares ** 2).sum()

                # Top contributor
                top_share = grouped['Share %'].iloc[0]

                result_df = grouped
                explanation = (f"Concentration analysis by **{actual_group}**. "
                              f"HHI Index: **{hhi:.4f}** (0=perfect competition, 1=monopoly). "
                              f"Top contributor holds **{top_share}%** share.")
        else:
            explanation = "Need a group-by column and amount column for concentration analysis."
            result_df = pd.DataFrame()

    elif intent == 'explanation':
        explanation = ("This system converts your natural language questions into structured execution plans. "
                      "Each plan specifies: intent, grouping, metrics, filters, and visualization. "
                      "The execution engine runs Pandas operations on the raw data. "
                      "No AI hallucination — all numbers are computed from the actual dataset.")
        result_df = pd.DataFrame([{
            'Step': 'Query parsed',
            'Detail': plan.get('query', '')
        }, {
            'Step': 'Intent detected',
            'Detail': plan.get('intent', '')
        }, {
            'Step': 'Aggregation',
            'Detail': plan.get('aggregation', '')
        }, {
            'Step': 'Group by',
            'Detail': str(plan.get('group_by', 'None'))
        }, {
            'Step': 'Filters',
            'Detail': str(plan.get('filters', []))
        }])
        viz = 'table'

    elif intent == 'histogram':
        if amount_col:
            # Create histogram bins
            values = filtered[amount_col].dropna()
            counts, bin_edges = np.histogram(values, bins=20)
            bin_labels = [f"{bin_edges[i]:.0f}-{bin_edges[i+1]:.0f}" for i in range(len(counts))]
            result_df = pd.DataFrame({
                'Range': bin_labels,
                'Count': counts,
                'Percentage': (counts / counts.sum() * 100).round(2)
            })
            median = values.median()
            mean = values.mean()
            explanation = (f"Histogram of **{amount_col}**: "
                         f"Mean = **{format_currency(mean)}**, "
                         f"Median = **{format_currency(median)}**. "
                         f"{'Right-skewed (mean > median) — many small transactions, few large ones.' if mean > median * 1.2 else 'Approximately symmetric distribution.'}")
            viz = 'histogram'
        else:
            explanation = "No numeric column detected for histogram."
            result_df = pd.DataFrame()

    elif intent == 'forecast':
        try:
            from src.predictor import forecast_monthly
            fc_result = forecast_monthly(df, metadata)
            if 'error' in fc_result:
                explanation = fc_result['error']
                result_df = pd.DataFrame()
            else:
                # Combine historical + forecast for display
                hist = fc_result['historical_df'][['Month', 'Actual', 'Fitted']].copy()
                hist['Type'] = 'Historical'
                fc = fc_result['forecast_df'].copy()
                fc['Actual'] = None
                fc['Fitted'] = fc['Predicted']
                fc['Type'] = 'Forecast'
                fc = fc[['Month', 'Actual', 'Fitted', 'Type']]
                result_df = pd.concat([hist, fc], ignore_index=True)
                explanation = fc_result['explanation']
                viz = 'line'
        except Exception as e:
            explanation = f"Forecast error: {str(e)}"
            result_df = pd.DataFrame()

    elif intent == 'scenario':
        explanation = ("Use the **Predictions & Scenarios** page for interactive what-if simulation. "
                      "You can adjust parameters like transaction value, volume, fraud rate, and see projected impacts.")
        result_df = pd.DataFrame([{
            'Available Scenarios': 'Value Increase/Decrease, Volume Increase, Fraud Rate Change, Failure Rate Change'
        }])
        viz = 'table'

    else:
        # General / fallback
        if group_by:
            filtered, actual_group = resolve_group_column(filtered, group_by, metadata)
            if actual_group in filtered.columns:
                if use_count:
                    grouped = filtered.groupby(actual_group).size().reset_index(name='Count')
                    grouped = grouped.sort_values('Count', ascending=False)
                else:
                    grouped = filtered.groupby(actual_group)[metric_col].sum().reset_index()
                    grouped = grouped.sort_values(metric_col, ascending=False)
                result_df = grouped.head(20)
                explanation = f"Results grouped by **{actual_group}** ({agg})."
            else:
                result_df = filtered.head(20)
                explanation = f"Showing first 20 rows."
        else:
            result_df = filtered.head(20)
            explanation = f"Showing first 20 rows of filtered data ({len(filtered)} total rows)."
            viz = 'table'

    if filter_desc:
        explanation = filter_desc + "\n\n" + explanation

    exec_time = round((time.time() - start) * 1000, 1)

    return {
        'result_df': result_df,
        'chart_spec': {
            'type': viz,
            'x': result_df.columns[0] if len(result_df.columns) >= 1 else None,
            'y': result_df.columns[-1] if len(result_df.columns) >= 2 else None,
            'title': plan.get('query', 'Query Result'),
        },
        'explanation': explanation,
        'exec_time_ms': exec_time,
        'plan': plan,
        'rows_scanned': len(filtered),
    }
