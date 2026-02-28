"""
Data Quality Module — Missing values, duplicates, negative values, outliers, inconsistencies.
"""
import pandas as pd
import numpy as np
from src.utils import get_numeric_columns, get_categorical_columns


def run_quality_checks(df, metadata):
    """
    Run comprehensive data quality checks.
    Returns a dict of check results.
    """
    results = {}

    # 1. Missing Values
    missing = df.isnull().sum()
    missing_pct = (missing / len(df) * 100).round(2)
    missing_df = pd.DataFrame({
        'Column': missing.index,
        'Missing Count': missing.values,
        'Missing %': missing_pct.values,
        'Has Missing': ['Yes' if m > 0 else 'No' for m in missing.values]
    })
    missing_df = missing_df[missing_df['Missing Count'] > 0].sort_values('Missing Count', ascending=False)
    results['missing_values'] = {
        'df': missing_df,
        'total_missing': int(missing.sum()),
        'total_cells': int(len(df) * len(df.columns)),
        'overall_pct': round(missing.sum() / (len(df) * len(df.columns)) * 100, 3),
        'description': f"Found {int(missing.sum())} missing cells across {len(missing_df)} columns."
    }

    # 2. Duplicate Rows
    dup_count = int(df.duplicated().sum())
    dup_subset_counts = {}
    for col in df.columns[:10]:  # Check first 10 columns
        dup_subset_counts[col] = int(df.duplicated(subset=[col]).sum())
    results['duplicates'] = {
        'exact_duplicates': dup_count,
        'column_duplicates': dup_subset_counts,
        'description': f"Found {dup_count} exact duplicate rows."
    }

    # 3. Negative Values (numeric columns)
    num_cols = get_numeric_columns(df)
    negative_results = []
    for col in num_cols:
        neg_count = int((df[col] < 0).sum())
        if neg_count > 0:
            negative_results.append({
                'Column': col,
                'Negative Count': neg_count,
                'Negative %': round(neg_count / len(df) * 100, 2),
                'Min Value': float(df[col].min())
            })
    results['negative_values'] = {
        'df': pd.DataFrame(negative_results),
        'found': len(negative_results) > 0,
        'description': f"Found negative values in {len(negative_results)} columns." if negative_results else "No negative values found."
    }

    # 4. Extreme Outliers (>4σ)
    outlier_results = []
    for col in num_cols:
        mean = df[col].mean()
        std = df[col].std()
        if std > 0:
            extreme = int(((df[col] - mean).abs() > 4 * std).sum())
            if extreme > 0:
                outlier_results.append({
                    'Column': col,
                    'Extreme Outliers': extreme,
                    'Outlier %': round(extreme / len(df) * 100, 3),
                    'Mean': round(mean, 2),
                    'Std': round(std, 2),
                    'Threshold': f">{round(mean + 4*std, 0)} or <{round(mean - 4*std, 0)}"
                })
    results['extreme_outliers'] = {
        'df': pd.DataFrame(outlier_results),
        'found': len(outlier_results) > 0,
        'description': f"Found extreme outliers (>4σ) in {len(outlier_results)} columns." if outlier_results else "No extreme outliers detected."
    }

    # 5. Column Consistency Checks
    cat_cols = get_categorical_columns(df)
    consistency_issues = []

    for col in cat_cols:
        values = df[col].dropna().unique()
        # Check for whitespace issues
        stripped = pd.Series(values).str.strip()
        if not (pd.Series(values) == stripped).all():
            consistency_issues.append({
                'Column': col,
                'Issue': 'Contains leading/trailing whitespace',
                'Severity': 'Low'
            })

        # Check for case inconsistency
        lower_vals = pd.Series(values).str.lower()
        if len(lower_vals.unique()) < len(values):
            consistency_issues.append({
                'Column': col,
                'Issue': 'Case inconsistency detected',
                'Severity': 'Medium'
            })

        # Check for very low cardinality (possible constant)
        if len(values) == 1:
            consistency_issues.append({
                'Column': col,
                'Issue': f'Constant value: {values[0]}',
                'Severity': 'Info'
            })

    results['consistency'] = {
        'df': pd.DataFrame(consistency_issues),
        'found': len(consistency_issues) > 0,
        'description': f"Found {len(consistency_issues)} consistency issues." if consistency_issues else "No consistency issues found."
    }

    # 6. Overall Quality Score (0-100)
    score = 100
    total_cells = len(df) * len(df.columns)
    score -= min(results['missing_values']['overall_pct'] * 5, 20)  # Missing penalty
    score -= min(dup_count / len(df) * 100, 15)  # Duplicate penalty
    score -= min(len(negative_results) * 3, 10)  # Negative penalty
    score -= min(len(outlier_results) * 2, 10)  # Outlier penalty
    score -= min(len(consistency_issues) * 2, 10)  # Consistency penalty

    results['quality_score'] = max(0, round(score, 1))
    if results['quality_score'] >= 90:
        results['quality_grade'] = 'A — Excellent'
    elif results['quality_score'] >= 75:
        results['quality_grade'] = 'B — Good'
    elif results['quality_score'] >= 60:
        results['quality_grade'] = 'C — Acceptable'
    else:
        results['quality_grade'] = 'D — Needs Improvement'

    return results
