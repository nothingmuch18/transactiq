"""
Risk & Concentration Analysis Module — Herfindahl index, dominance, volatility.
"""
import pandas as pd
import numpy as np
from src.utils import format_currency, format_pct, safe_divide


def compute_herfindahl_index(shares):
    """Compute Herfindahl-Hirschman Index from market shares (as fractions)."""
    return float((shares ** 2).sum())


def compute_concentration_metrics(df, group_col, value_col):
    """Compute full concentration analysis for a grouping."""
    grouped = df.groupby(group_col)[value_col].sum().sort_values(ascending=False)
    total = grouped.sum()
    shares = grouped / total

    # HHI
    hhi = compute_herfindahl_index(shares)

    # Top contributor
    top1 = grouped.index[0]
    top1_share = shares.iloc[0] * 100

    # Top 3 concentration
    top3_share = shares.head(3).sum() * 100

    # Top 5 concentration
    top5_share = shares.head(5).sum() * 100

    # Number of groups needed for 80% of value
    cumulative = shares.cumsum()
    groups_for_80 = int((cumulative <= 0.80).sum()) + 1

    # Concentration classification
    if hhi > 0.25:
        concentration_level = "Highly Concentrated"
    elif hhi > 0.15:
        concentration_level = "Moderately Concentrated"
    else:
        concentration_level = "Competitive"

    return {
        'hhi': round(hhi, 4),
        'concentration_level': concentration_level,
        'top1': top1,
        'top1_share': round(top1_share, 2),
        'top3_share': round(top3_share, 2),
        'top5_share': round(top5_share, 2),
        'groups_for_80_pct': groups_for_80,
        'total_groups': len(grouped),
        'shares_df': pd.DataFrame({
            group_col: grouped.index,
            'Total Value': grouped.values,
            'Share %': (shares * 100).round(2).values,
            'Cumulative %': (cumulative * 100).round(2).values
        })
    }


def compute_volatility_index(df, date_col, value_col):
    """Compute monthly volatility (coefficient of variation)."""
    monthly = df.set_index(date_col).resample('M')[value_col].sum()
    if len(monthly) < 2:
        return {'volatility_cv': 0, 'monthly_std': 0, 'monthly_mean': 0, 'interpretation': 'Insufficient data'}

    cv = (monthly.std() / monthly.mean()) * 100

    if cv < 5:
        interpretation = "Very stable — consistent monthly patterns"
    elif cv < 15:
        interpretation = "Low volatility — minor monthly fluctuations"
    elif cv < 30:
        interpretation = "Moderate volatility — notable monthly variance"
    else:
        interpretation = "High volatility — significant monthly swings"

    return {
        'volatility_cv': round(cv, 2),
        'monthly_std': round(float(monthly.std()), 2),
        'monthly_mean': round(float(monthly.mean()), 2),
        'monthly_min': round(float(monthly.min()), 2),
        'monthly_max': round(float(monthly.max()), 2),
        'interpretation': interpretation,
        'monthly_series': monthly
    }


def compute_risk_summary(df, metadata):
    """Generate comprehensive risk summary."""
    roles = metadata.get('roles', {})
    amount_col = roles.get('amount')
    date_col = roles.get('date')
    region_col = roles.get('region')
    status_col = roles.get('status')
    fraud_col = roles.get('fraud')

    risk_metrics = {}

    # Concentration Risk
    if region_col and amount_col:
        conc = compute_concentration_metrics(df, region_col, amount_col)
        risk_metrics['concentration'] = conc

    # Volatility Risk
    if date_col and amount_col:
        vol = compute_volatility_index(df, date_col, amount_col)
        risk_metrics['volatility'] = vol

    # Failure Risk
    if status_col:
        total = len(df)
        failed = len(df[df[status_col] == 'FAILED'])
        risk_metrics['failure_rate'] = round(safe_divide(failed, total) * 100, 3)

    # Fraud Risk
    if fraud_col:
        risk_metrics['fraud_rate'] = round(safe_divide(int(df[fraud_col].sum()), len(df)) * 100, 4)

    # Overall Risk Index (0-100)
    risk_score = 0
    components = 0

    if 'concentration' in risk_metrics:
        hhi = risk_metrics['concentration']['hhi']
        risk_score += min(hhi * 200, 50)  # Max 50 from concentration
        components += 1

    if 'volatility' in risk_metrics:
        cv = risk_metrics['volatility']['volatility_cv']
        risk_score += min(cv, 30)  # Max 30 from volatility
        components += 1

    if 'failure_rate' in risk_metrics:
        risk_score += min(risk_metrics['failure_rate'] * 2, 10)  # Max 10 from failures
        components += 1

    if 'fraud_rate' in risk_metrics:
        risk_score += min(risk_metrics['fraud_rate'] * 100, 10)  # Max 10 from fraud
        components += 1

    risk_metrics['risk_index'] = round(min(risk_score, 100), 1)

    if risk_metrics['risk_index'] < 20:
        risk_metrics['risk_level'] = 'Low Risk'
    elif risk_metrics['risk_index'] < 50:
        risk_metrics['risk_level'] = 'Moderate Risk'
    else:
        risk_metrics['risk_level'] = 'High Risk'

    return risk_metrics
