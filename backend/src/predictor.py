"""
Predictive Analytics Module — Linear trend + seasonal decomposition forecasting.
Includes train/test split, RMSE metric, and explainability.
"""
import pandas as pd
import numpy as np
from src.utils import format_currency, format_number, format_pct, safe_divide


def _decompose_trend_seasonal(values):
    """Decompose a time series into trend and seasonal components."""
    n = len(values)
    if n < 3:
        return values, np.zeros(n), values

    # Linear trend via polyfit
    x = np.arange(n)
    coeffs = np.polyfit(x, values, 1)
    trend = np.polyval(coeffs, x)

    # Seasonal = residual pattern (monthly average of detrended values)
    detrended = values - trend
    # If we have at least 12 points, compute monthly seasonal factors
    if n >= 12:
        seasonal = np.zeros(n)
        for i in range(12):
            indices = list(range(i, n, 12))
            seasonal_avg = np.mean(detrended[indices])
            for idx in indices:
                seasonal[idx] = seasonal_avg
    else:
        seasonal = np.zeros(n)

    residual = values - trend - seasonal
    return trend, seasonal, residual


def forecast_monthly(df, metadata, forecast_months=3, test_ratio=0.2):
    """
    Forecast monthly transaction value using trend + seasonal decomposition.
    
    Returns dict with:
    - historical_df: DataFrame with Month, Actual, Trend, Seasonal, Fitted
    - forecast_df: DataFrame with Month, Predicted, Lower, Upper
    - metrics: dict with RMSE, MAE, train_size, test_size
    - explanation: human-readable explanation
    - model_info: dict with coefficients and methodology
    """
    roles = metadata.get('roles', {})
    amount_col = roles.get('amount')
    date_col = roles.get('date')

    if not amount_col or not date_col:
        return {
            'error': 'Need both amount and date columns for forecasting.',
            'explanation': 'Cannot generate forecast without date and amount columns.'
        }

    # Aggregate monthly
    monthly = df.set_index(date_col).resample('M')[amount_col].sum().reset_index()
    monthly.columns = ['Month', 'Value']
    monthly = monthly.sort_values('Month')

    if len(monthly) < 4:
        return {
            'error': 'Need at least 4 months of data for forecasting.',
            'explanation': 'Insufficient historical data. Need at least 4 months.'
        }

    values = monthly['Value'].values
    n = len(values)

    # Train/Test split
    split_idx = max(int(n * (1 - test_ratio)), 3)
    train_vals = values[:split_idx]
    test_vals = values[split_idx:]

    # Decompose on training data
    x_train = np.arange(len(train_vals))
    trend_coeffs = np.polyfit(x_train, train_vals, 1)
    slope, intercept = trend_coeffs[0], trend_coeffs[1]

    # Compute trend for full series + forecast
    x_full = np.arange(n + forecast_months)
    trend_full = np.polyval(trend_coeffs, x_full)

    # Seasonal factors from training data
    train_trend = np.polyval(trend_coeffs, x_train)
    detrended = train_vals - train_trend
    seasonal_factors = np.zeros(12)
    for i in range(12):
        indices = [j for j in range(len(detrended)) if j % 12 == i]
        if indices:
            seasonal_factors[i] = np.mean(detrended[indices])

    # Apply seasonal to full + forecast
    seasonal_full = np.array([seasonal_factors[i % 12] for i in range(n + forecast_months)])
    fitted_full = trend_full + seasonal_full

    # Compute residual std for confidence intervals
    fitted_train = fitted_full[:split_idx]
    residuals = train_vals - fitted_train
    residual_std = np.std(residuals) if len(residuals) > 1 else 0

    # Metrics on test set
    if len(test_vals) > 0:
        fitted_test = fitted_full[split_idx:n]
        test_errors = test_vals - fitted_test
        rmse = float(np.sqrt(np.mean(test_errors ** 2)))
        mae = float(np.mean(np.abs(test_errors)))
        mape = float(np.mean(np.abs(test_errors) / np.maximum(test_vals, 1)) * 100)
    else:
        rmse = float(np.sqrt(np.mean(residuals ** 2)))
        mae = float(np.mean(np.abs(residuals)))
        mape = 0

    # Build historical DataFrame
    historical_df = pd.DataFrame({
        'Month': monthly['Month'],
        'Actual': values,
        'Trend': trend_full[:n],
        'Seasonal': seasonal_full[:n],
        'Fitted': fitted_full[:n],
        'Split': ['Train'] * split_idx + ['Test'] * (n - split_idx),
    })

    # Build forecast DataFrame
    last_month = monthly['Month'].iloc[-1]
    forecast_months_list = pd.date_range(start=last_month + pd.offsets.MonthEnd(1),
                                          periods=forecast_months, freq='ME')
    forecast_values = fitted_full[n:n + forecast_months]
    forecast_df = pd.DataFrame({
        'Month': forecast_months_list,
        'Predicted': forecast_values.round(2),
        'Lower (95%)': (forecast_values - 1.96 * residual_std).round(2),
        'Upper (95%)': (forecast_values + 1.96 * residual_std).round(2),
    })

    # Direction analysis
    if slope > 0:
        trend_direction = "upward"
        trend_desc = f"increasing by approximately {format_currency(abs(slope))} per month"
    else:
        trend_direction = "downward"
        trend_desc = f"decreasing by approximately {format_currency(abs(slope))} per month"

    # Seasonal analysis
    peak_month_idx = int(np.argmax(seasonal_factors))
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    peak_month_name = month_names[peak_month_idx % 12] if peak_month_idx < 12 else 'N/A'

    explanation = (
        f"**Forecast Model**: Linear trend + seasonal decomposition.\n\n"
        f"**Trend**: The data shows an **{trend_direction}** trend, {trend_desc}.\n\n"
        f"**Seasonality**: Peak activity occurs in **{peak_month_name}** based on historical patterns.\n\n"
        f"**Accuracy**: RMSE = **{format_currency(rmse)}**, MAE = **{format_currency(mae)}**"
        f"{f', MAPE = **{mape:.1f}%**' if mape > 0 else ''}. "
        f"Trained on **{split_idx}** months, tested on **{n - split_idx}** months.\n\n"
        f"**Next {len(forecast_df)} months**: Predicted total = **{format_currency(forecast_values.sum())}**.\n\n"
        f"⚠️ *This is a simple statistical model (not deep ML). Predictions assume historical trends continue.*"
    )

    return {
        'historical_df': historical_df,
        'forecast_df': forecast_df,
        'metrics': {
            'rmse': round(rmse, 2),
            'mae': round(mae, 2),
            'mape': round(mape, 2),
            'train_size': split_idx,
            'test_size': n - split_idx,
            'slope': round(slope, 2),
            'intercept': round(intercept, 2),
        },
        'explanation': explanation,
        'model_info': {
            'method': 'Linear Trend + Seasonal Decomposition',
            'trend_direction': trend_direction,
            'peak_seasonal_month': peak_month_name,
            'seasonal_factors': {month_names[i]: round(seasonal_factors[i], 2) for i in range(12)},
            'confidence_interval': '95%',
        }
    }


def forecast_volume(df, metadata, forecast_months=3):
    """
    Forecast monthly transaction count (volume).
    Same method as value forecasting but on counts.
    """
    roles = metadata.get('roles', {})
    date_col = roles.get('date')

    if not date_col:
        return {'error': 'Need date column for volume forecasting.'}

    monthly = df.set_index(date_col).resample('M').size().reset_index(name='Count')
    monthly.columns = ['Month', 'Value']
    monthly = monthly.sort_values('Month')

    if len(monthly) < 4:
        return {'error': 'Insufficient data for volume forecast.'}

    values = monthly['Value'].values.astype(float)
    n = len(values)

    # Simple linear forecast
    x = np.arange(n)
    coeffs = np.polyfit(x, values, 1)
    slope = coeffs[0]

    x_forecast = np.arange(n, n + forecast_months)
    predicted = np.polyval(coeffs, x_forecast)

    last_month = monthly['Month'].iloc[-1]
    forecast_months_list = pd.date_range(start=last_month + pd.offsets.MonthEnd(1),
                                          periods=forecast_months, freq='ME')

    forecast_df = pd.DataFrame({
        'Month': forecast_months_list,
        'Predicted Volume': predicted.round(0).astype(int),
    })

    direction = "growing" if slope > 0 else "declining"
    explanation = (
        f"Transaction volume is **{direction}** at approximately **{format_number(abs(slope))}** "
        f"per month based on linear trend."
    )

    return {
        'forecast_df': forecast_df,
        'historical_df': monthly,
        'explanation': explanation,
    }
