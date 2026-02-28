"""
Anomaly Detection Module — IQR, Z-score, rolling deviation, and spike detection.
"""
import pandas as pd
import numpy as np
from src.utils import format_currency, get_numeric_columns


def detect_iqr_anomalies(df, column, multiplier=1.5):
    """Detect anomalies using the IQR method."""
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - multiplier * IQR
    upper = Q3 + multiplier * IQR

    anomalies = df[(df[column] < lower) | (df[column] > upper)].copy()
    anomalies['anomaly_reason'] = anomalies[column].apply(
        lambda x: f"Below IQR lower bound ({lower:.0f})" if x < lower else f"Above IQR upper bound ({upper:.0f})"
    )
    return anomalies, {'Q1': Q1, 'Q3': Q3, 'IQR': IQR, 'lower': lower, 'upper': upper}


def detect_zscore_anomalies(df, column, threshold=3.0):
    """Detect anomalies using Z-score method."""
    mean = df[column].mean()
    std = df[column].std()
    if std == 0:
        return pd.DataFrame(), {'mean': mean, 'std': 0, 'threshold': threshold}

    df_copy = df.copy()
    df_copy['_zscore'] = (df_copy[column] - mean) / std
    anomalies = df_copy[df_copy['_zscore'].abs() > threshold].copy()
    anomalies['anomaly_reason'] = anomalies['_zscore'].apply(
        lambda z: f"Z-score: {z:.2f} (threshold: ±{threshold})"
    )
    anomalies = anomalies.drop(columns=['_zscore'])
    return anomalies, {'mean': mean, 'std': std, 'threshold': threshold}


def detect_rolling_anomalies(df, date_col, value_col, window=7, threshold=2.0):
    """Detect anomalies using rolling mean deviation."""
    daily = df.set_index(date_col).resample('D')[value_col].sum().reset_index()
    daily.columns = ['Date', 'Value']
    daily = daily.sort_values('Date')

    daily['Rolling_Mean'] = daily['Value'].rolling(window=window, min_periods=1).mean()
    daily['Rolling_Std'] = daily['Value'].rolling(window=window, min_periods=1).std()
    daily['Deviation'] = (daily['Value'] - daily['Rolling_Mean']) / daily['Rolling_Std'].replace(0, np.nan)

    anomalies = daily[daily['Deviation'].abs() > threshold].copy()
    anomalies['anomaly_reason'] = anomalies.apply(
        lambda row: f"Value {row['Value']:.0f} deviates {row['Deviation']:.1f}σ from rolling mean {row['Rolling_Mean']:.0f}",
        axis=1
    )
    return anomalies, daily


def detect_growth_spikes(df, date_col, value_col, growth_threshold=50.0):
    """Detect sudden growth spikes (month-over-month)."""
    monthly = df.set_index(date_col).resample('M')[value_col].sum().reset_index()
    monthly.columns = ['Month', 'Value']
    monthly = monthly.sort_values('Month')
    monthly['Growth %'] = monthly['Value'].pct_change() * 100

    spikes = monthly[monthly['Growth %'].abs() > growth_threshold].copy()
    spikes['anomaly_reason'] = spikes['Growth %'].apply(
        lambda g: f"{'Surge' if g > 0 else 'Drop'} of {g:.1f}% month-over-month"
    )
    return spikes, monthly


def detect_concentration_anomaly(df, group_col, value_col, dominance_threshold=30.0):
    """Flag if any single group dominates excessively."""
    grouped = df.groupby(group_col)[value_col].sum()
    total = grouped.sum()
    shares = (grouped / total * 100).sort_values(ascending=False)

    anomalies = shares[shares > dominance_threshold]
    results = []
    for group_name, share in anomalies.items():
        results.append({
            'Group': group_name,
            'Share %': round(share, 2),
            'anomaly_reason': f"{group_name} holds {share:.1f}% of total — exceeds {dominance_threshold}% threshold"
        })
    return pd.DataFrame(results) if results else pd.DataFrame()


def detect_percentile_anomalies(df, column, lower_pct=1, upper_pct=99):
    """Detect anomalies using percentile thresholds."""
    lower_bound = df[column].quantile(lower_pct / 100)
    upper_bound = df[column].quantile(upper_pct / 100)

    anomalies = df[(df[column] < lower_bound) | (df[column] > upper_bound)].copy()
    anomalies['anomaly_reason'] = anomalies[column].apply(
        lambda x: f"Below {lower_pct}th percentile ({lower_bound:.0f})" if x < lower_bound
        else f"Above {upper_pct}th percentile ({upper_bound:.0f})"
    )
    return anomalies, {'lower_pct': lower_pct, 'upper_pct': upper_pct,
                       'lower_bound': lower_bound, 'upper_bound': upper_bound}


def run_full_anomaly_detection(df, metadata, method='all'):
    """
    Run all anomaly detection methods.
    Returns dict of method → (anomaly_df, stats).
    """
    results = {}
    roles = metadata.get('roles', {})
    amount_col = roles.get('amount')
    date_col = roles.get('date')
    region_col = roles.get('region')

    if not amount_col:
        return results

    if method in ('all', 'iqr'):
        anomalies, stats = detect_iqr_anomalies(df, amount_col)
        results['IQR Method'] = {
            'anomalies': anomalies,
            'stats': stats,
            'count': len(anomalies),
            'description': f"Found {len(anomalies)} anomalies using IQR (1.5x). Bounds: [{stats['lower']:.0f}, {stats['upper']:.0f}]"
        }

    if method in ('all', 'zscore'):
        anomalies, stats = detect_zscore_anomalies(df, amount_col)
        results['Z-Score Method'] = {
            'anomalies': anomalies,
            'stats': stats,
            'count': len(anomalies),
            'description': f"Found {len(anomalies)} anomalies with |Z| > {stats['threshold']}. Mean: {stats['mean']:.0f}, Std: {stats['std']:.0f}"
        }

    if method in ('all', 'rolling') and date_col:
        anomalies, daily = detect_rolling_anomalies(df, date_col, amount_col)
        results['Rolling Deviation'] = {
            'anomalies': anomalies,
            'daily_data': daily,
            'count': len(anomalies),
            'description': f"Found {len(anomalies)} daily anomalies using 7-day rolling window (2σ threshold)"
        }

    if method in ('all', 'growth') and date_col:
        spikes, monthly = detect_growth_spikes(df, date_col, amount_col)
        results['Growth Spikes'] = {
            'anomalies': spikes,
            'monthly_data': monthly,
            'count': len(spikes),
            'description': f"Found {len(spikes)} month-over-month growth spikes (>50% change)"
        }

    if method in ('all', 'concentration') and region_col:
        conc_anomalies = detect_concentration_anomaly(df, region_col, amount_col)
        results['Concentration Anomaly'] = {
            'anomalies': conc_anomalies,
            'count': len(conc_anomalies),
            'description': f"Found {len(conc_anomalies)} regions with >30% concentration"
        }

    if method in ('all', 'percentile'):
        anomalies, stats = detect_percentile_anomalies(df, amount_col)
        results['Percentile Threshold'] = {
            'anomalies': anomalies,
            'stats': stats,
            'count': len(anomalies),
            'description': f"Found {len(anomalies)} anomalies outside [{stats['lower_pct']}th, {stats['upper_pct']}th] percentile. Bounds: [{stats['lower_bound']:.0f}, {stats['upper_bound']:.0f}]"
        }

    return results
