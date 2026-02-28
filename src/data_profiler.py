"""
Data Profiling Engine — Auto-detects schema, computes statistics, and generates metadata.
"""
import pandas as pd
import numpy as np
from src.utils import get_numeric_columns, get_categorical_columns, get_datetime_columns, detect_column_role


def load_and_profile(filepath_or_df):
    """
    Load dataset and generate a complete profile.
    Accepts a file path (str) or a DataFrame.
    Returns (df, metadata).
    """
    if isinstance(filepath_or_df, str):
        df = pd.read_csv(filepath_or_df)
    else:
        df = filepath_or_df.copy()

    # --- Auto-detect and convert date columns ---
    for col in df.columns:
        if df[col].dtype == 'object':
            sample = df[col].dropna().head(50)
            try:
                parsed = pd.to_datetime(sample, infer_datetime_format=True)
                if parsed.notna().sum() > len(sample) * 0.8:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
            except (ValueError, TypeError):
                pass

    metadata = generate_metadata(df)
    return df, metadata


def generate_metadata(df):
    """Generate comprehensive metadata object from a DataFrame."""
    meta = {}

    # Basic info
    meta['rows'] = len(df)
    meta['columns'] = len(df.columns)
    meta['column_names'] = df.columns.tolist()

    # Column type classification
    meta['numeric_columns'] = get_numeric_columns(df)
    meta['categorical_columns'] = get_categorical_columns(df)
    meta['datetime_columns'] = get_datetime_columns(df)

    # Column roles
    meta['roles'] = detect_column_role(df, meta)

    # Column details
    col_details = {}
    for col in df.columns:
        info = {
            'dtype': str(df[col].dtype),
            'missing': int(df[col].isna().sum()),
            'missing_pct': round(df[col].isna().mean() * 100, 2),
            'unique': int(df[col].nunique()),
        }
        if df[col].dtype in ['int64', 'float64']:
            info['mean'] = round(float(df[col].mean()), 2) if not df[col].isna().all() else None
            info['median'] = round(float(df[col].median()), 2) if not df[col].isna().all() else None
            info['std'] = round(float(df[col].std()), 2) if not df[col].isna().all() else None
            info['min'] = float(df[col].min()) if not df[col].isna().all() else None
            info['max'] = float(df[col].max()) if not df[col].isna().all() else None
            info['q25'] = round(float(df[col].quantile(0.25)), 2) if not df[col].isna().all() else None
            info['q75'] = round(float(df[col].quantile(0.75)), 2) if not df[col].isna().all() else None
        elif df[col].dtype == 'object':
            info['top_values'] = df[col].value_counts().head(10).to_dict()
        elif pd.api.types.is_datetime64_any_dtype(df[col]):
            info['min_date'] = str(df[col].min())
            info['max_date'] = str(df[col].max())
            info['date_range_days'] = (df[col].max() - df[col].min()).days if not df[col].isna().all() else None

        col_details[col] = info
    meta['column_details'] = col_details

    # Duplicate detection
    meta['duplicate_rows'] = int(df.duplicated().sum())

    # ID-like columns (high cardinality, unique)
    meta['id_columns'] = [
        col for col in df.columns
        if df[col].nunique() == len(df) or (df[col].nunique() > len(df) * 0.95 and df[col].dtype == 'object')
    ]

    # Summary stats for the primary value column
    amount_col = meta['roles'].get('amount')
    if amount_col:
        meta['total_value'] = float(df[amount_col].sum())
        meta['avg_value'] = float(df[amount_col].mean())
        meta['median_value'] = float(df[amount_col].median())
        meta['total_transactions'] = len(df)

    # Time range
    date_col = meta['roles'].get('date')
    if date_col:
        meta['date_range'] = {
            'start': str(df[date_col].min()),
            'end': str(df[date_col].max()),
            'months': int((df[date_col].max() - df[date_col].min()).days / 30) + 1
        }

    # Correlation matrix for numeric columns
    num_cols = meta['numeric_columns']
    if len(num_cols) >= 2:
        corr = df[num_cols].corr()
        meta['correlation_matrix'] = corr.round(3).to_dict()

    return meta


def get_descriptive_stats(df, metadata):
    """Return a formatted descriptive stats DataFrame."""
    num_cols = metadata.get('numeric_columns', [])
    if not num_cols:
        return pd.DataFrame()
    return df[num_cols].describe().round(2)


def get_column_summary_df(metadata):
    """Return column summary as a DataFrame for display."""
    rows = []
    for col, info in metadata.get('column_details', {}).items():
        rows.append({
            'Column': col,
            'Type': info['dtype'],
            'Missing': f"{info['missing']} ({info['missing_pct']}%)",
            'Unique': info['unique'],
            'Sample': str(info.get('mean', info.get('top_values', {}))).strip()[:60]
        })
    return pd.DataFrame(rows)
