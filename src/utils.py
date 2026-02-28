"""
Shared utility functions for the UPI Intelligence Platform.
"""
import pandas as pd
import numpy as np
import re


def format_currency(value):
    """Format number as INR currency string."""
    if pd.isna(value):
        return "N/A"
    if abs(value) >= 1e7:
        return f"₹{value/1e7:.2f} Cr"
    elif abs(value) >= 1e5:
        return f"₹{value/1e5:.2f} L"
    elif abs(value) >= 1e3:
        return f"₹{value/1e3:.1f}K"
    else:
        return f"₹{value:,.0f}"


def format_number(value):
    """Format large numbers with K/L/Cr suffixes."""
    if pd.isna(value):
        return "N/A"
    if abs(value) >= 1e7:
        return f"{value/1e7:.2f} Cr"
    elif abs(value) >= 1e5:
        return f"{value/1e5:.2f} L"
    elif abs(value) >= 1e3:
        return f"{value/1e3:.1f}K"
    else:
        return f"{value:,.0f}"


def format_pct(value):
    """Format as percentage."""
    if pd.isna(value):
        return "N/A"
    return f"{value:+.2f}%"


def safe_match_column(df, query_term):
    """
    Find the best matching column name for a query term.
    Uses fuzzy substring matching on column names.
    """
    query_lower = query_term.lower().strip()
    columns = df.columns.tolist()

    # Exact match
    for col in columns:
        if col.lower() == query_lower:
            return col

    # Contains match
    for col in columns:
        if query_lower in col.lower() or col.lower() in query_lower:
            return col

    # Word overlap match
    query_words = set(re.split(r'[\s_\-]+', query_lower))
    best_match = None
    best_score = 0
    for col in columns:
        col_words = set(re.split(r'[\s_\-()]+', col.lower()))
        overlap = len(query_words & col_words)
        if overlap > best_score:
            best_score = overlap
            best_match = col
    if best_score > 0:
        return best_match

    return None


def get_numeric_columns(df):
    """Get numeric column names."""
    return df.select_dtypes(include=[np.number]).columns.tolist()


def get_categorical_columns(df):
    """Get categorical/object column names."""
    return df.select_dtypes(include=['object', 'category']).columns.tolist()


def get_datetime_columns(df):
    """Get datetime column names."""
    return df.select_dtypes(include=['datetime64']).columns.tolist()


def safe_divide(a, b):
    """Safe division avoiding ZeroDivisionError."""
    if b == 0 or pd.isna(b):
        return 0
    return a / b


def compute_growth_rate(series):
    """Compute period-over-period growth rates from a time series."""
    if len(series) < 2:
        return pd.Series(dtype=float)
    return series.pct_change() * 100


def detect_column_role(df, metadata):
    """
    Detect semantic roles for columns in a financial dataset.
    Returns dict mapping role → column name.
    """
    roles = {}

    # Date column
    dt_cols = get_datetime_columns(df)
    if dt_cols:
        roles['date'] = dt_cols[0]

    # Amount / value column
    num_cols = get_numeric_columns(df)
    for col in num_cols:
        col_lower = col.lower()
        if any(kw in col_lower for kw in ['amount', 'value', 'price', 'cost', 'revenue', 'inr', 'rupee']):
            roles['amount'] = col
            break
    if 'amount' not in roles and num_cols:
        # Fallback: pick the numeric column with largest mean that isn't an ID or flag
        candidates = [c for c in num_cols if not any(kw in c.lower() for kw in ['id', 'flag', 'weekend', 'hour', 'day'])]
        if candidates:
            roles['amount'] = max(candidates, key=lambda c: df[c].mean())

    # State / region column
    cat_cols = get_categorical_columns(df)
    for col in cat_cols:
        col_lower = col.lower()
        if any(kw in col_lower for kw in ['state', 'region', 'province', 'city', 'location']):
            roles['region'] = col
            break

    # Category column
    for col in cat_cols:
        col_lower = col.lower()
        if any(kw in col_lower for kw in ['category', 'merchant', 'type']):
            if 'transaction' not in col_lower or 'type' in col_lower:
                roles['category'] = col
                break

    # Transaction type
    for col in cat_cols:
        col_lower = col.lower()
        if 'transaction' in col_lower and 'type' in col_lower:
            roles['transaction_type'] = col
            break

    # Bank columns
    for col in cat_cols:
        col_lower = col.lower()
        if 'bank' in col_lower:
            if 'sender' in col_lower:
                roles['sender_bank'] = col
            elif 'receiver' in col_lower:
                roles['receiver_bank'] = col
            elif 'bank' not in roles:
                roles['bank'] = col

    # Status column
    for col in cat_cols:
        col_lower = col.lower()
        if 'status' in col_lower:
            roles['status'] = col
            break

    # Fraud flag
    for col in num_cols + cat_cols:
        col_lower = col.lower()
        if 'fraud' in col_lower:
            roles['fraud'] = col
            break

    return roles
