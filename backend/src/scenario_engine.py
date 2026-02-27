"""
Scenario Simulation Engine — What-if analysis for UPI transaction data.
Simulates parameter changes and shows before/after impact on KPIs.
"""
import pandas as pd
import numpy as np
from src.utils import format_currency, format_number, format_pct, safe_divide


SCENARIOS = {
    'value_increase': {
        'label': 'Transaction Value Increase',
        'description': 'Simulate if average transaction value increases by X%',
        'param': 'percentage',
        'default': 10,
    },
    'value_decrease': {
        'label': 'Transaction Value Decrease',
        'description': 'Simulate if average transaction value decreases by X%',
        'param': 'percentage',
        'default': 10,
    },
    'volume_increase': {
        'label': 'Transaction Volume Increase',
        'description': 'Simulate if transaction volume increases by X%',
        'param': 'percentage',
        'default': 15,
    },
    'fraud_rate_change': {
        'label': 'Fraud Rate Change',
        'description': 'Simulate new fraud rate at X%',
        'param': 'target_rate',
        'default': 0.5,
    },
    'failure_rate_change': {
        'label': 'Failure Rate Change',
        'description': 'Simulate new failure rate at X%',
        'param': 'target_rate',
        'default': 5.0,
    },
}


def simulate_scenario(df, metadata, scenario_type, param_value):
    """
    Run a what-if simulation and return before/after comparison.
    
    Returns dict with:
    - comparison_df: Before vs After metrics
    - explanation: Narrative explanation
    - impact_summary: Key impact bullets
    """
    roles = metadata.get('roles', {})
    amount_col = roles.get('amount')
    status_col = roles.get('status')
    fraud_col = roles.get('fraud')

    if not amount_col:
        return {'error': 'No amount column detected.'}

    # Current KPIs
    current = _compute_kpis(df, roles)

    # Simulate
    sim_df = df.copy()

    if scenario_type == 'value_increase':
        factor = 1 + (param_value / 100)
        sim_df[amount_col] = sim_df[amount_col] * factor
        action_desc = f"transaction values increased by {param_value}%"

    elif scenario_type == 'value_decrease':
        factor = 1 - (param_value / 100)
        sim_df[amount_col] = sim_df[amount_col] * factor
        action_desc = f"transaction values decreased by {param_value}%"

    elif scenario_type == 'volume_increase':
        # Duplicate a percentage of rows to simulate volume increase
        n_extra = int(len(sim_df) * param_value / 100)
        extra_rows = sim_df.sample(n=min(n_extra, len(sim_df)), replace=True, random_state=42)
        sim_df = pd.concat([sim_df, extra_rows], ignore_index=True)
        action_desc = f"transaction volume increased by {param_value}%"

    elif scenario_type == 'fraud_rate_change':
        if fraud_col:
            current_fraud_count = int(sim_df[fraud_col].sum())
            target_fraud_count = int(len(sim_df) * param_value / 100)
            diff = target_fraud_count - current_fraud_count

            if diff > 0:
                # Add more fraud flags
                non_fraud_mask = sim_df[fraud_col] == 0
                non_fraud_indices = sim_df[non_fraud_mask].index.tolist()
                flip_count = min(diff, len(non_fraud_indices))
                flip_indices = np.random.choice(non_fraud_indices, size=flip_count, replace=False)
                sim_df.loc[flip_indices, fraud_col] = 1
            elif diff < 0:
                # Remove fraud flags
                fraud_mask = sim_df[fraud_col] == 1
                fraud_indices = sim_df[fraud_mask].index.tolist()
                flip_count = min(abs(diff), len(fraud_indices))
                flip_indices = np.random.choice(fraud_indices, size=flip_count, replace=False)
                sim_df.loc[flip_indices, fraud_col] = 0

            action_desc = f"fraud rate changed to {param_value}%"
        else:
            return {'error': 'No fraud column detected.'}

    elif scenario_type == 'failure_rate_change':
        if status_col:
            current_fail_count = len(sim_df[sim_df[status_col] == 'FAILED'])
            target_fail_count = int(len(sim_df) * param_value / 100)
            diff = target_fail_count - current_fail_count

            if diff > 0:
                success_mask = sim_df[status_col] == 'SUCCESS'
                success_indices = sim_df[success_mask].index.tolist()
                flip_count = min(diff, len(success_indices))
                flip_indices = np.random.choice(success_indices, size=flip_count, replace=False)
                sim_df.loc[flip_indices, status_col] = 'FAILED'
            elif diff < 0:
                fail_mask = sim_df[status_col] == 'FAILED'
                fail_indices = sim_df[fail_mask].index.tolist()
                flip_count = min(abs(diff), len(fail_indices))
                flip_indices = np.random.choice(fail_indices, size=flip_count, replace=False)
                sim_df.loc[flip_indices, status_col] = 'SUCCESS'

            action_desc = f"failure rate changed to {param_value}%"
        else:
            return {'error': 'No status column detected.'}
    else:
        return {'error': f'Unknown scenario type: {scenario_type}'}

    # After KPIs
    after = _compute_kpis(sim_df, roles)

    # Build comparison DataFrame
    metrics = list(current.keys())
    comparison_df = pd.DataFrame({
        'Metric': metrics,
        'Before': [current[m] for m in metrics],
        'After': [after[m] for m in metrics],
    })
    comparison_df['Change'] = comparison_df['After'] - comparison_df['Before']
    comparison_df['Change %'] = comparison_df.apply(
        lambda row: round(safe_divide(row['Change'], row['Before']) * 100, 2)
        if row['Before'] != 0 else 0, axis=1
    )

    # Impact summary
    impacts = []
    for _, row in comparison_df.iterrows():
        if abs(row['Change %']) > 0.01:
            direction = "↑" if row['Change'] > 0 else "↓"
            impacts.append(f"{direction} **{row['Metric']}**: {row['Change %']:+.2f}%")

    explanation = (
        f"**Scenario**: What if {action_desc}?\n\n"
        f"**Key Impacts**:\n" + "\n".join(f"- {imp}" for imp in impacts) + "\n\n"
        f"*This simulation modifies the dataset in-memory to project hypothetical outcomes. "
        f"Actual results may vary based on market dynamics.*"
    )

    return {
        'comparison_df': comparison_df,
        'explanation': explanation,
        'impact_summary': impacts,
        'scenario_label': SCENARIOS.get(scenario_type, {}).get('label', scenario_type),
        'param_value': param_value,
    }


def _compute_kpis(df, roles):
    """Compute standard KPIs for simulation comparison."""
    amount_col = roles.get('amount')
    status_col = roles.get('status')
    fraud_col = roles.get('fraud')

    kpis = {}
    kpis['Total Transactions'] = len(df)

    if amount_col:
        kpis['Total Value (INR)'] = round(float(df[amount_col].sum()), 2)
        kpis['Average Value (INR)'] = round(float(df[amount_col].mean()), 2)
        kpis['Median Value (INR)'] = round(float(df[amount_col].median()), 2)
        kpis['Max Transaction (INR)'] = round(float(df[amount_col].max()), 2)

    if status_col:
        total = len(df)
        failed = len(df[df[status_col] == 'FAILED'])
        kpis['Failure Rate %'] = round(safe_divide(failed, total) * 100, 3)
        kpis['Success Count'] = total - failed

    if fraud_col:
        kpis['Fraud Count'] = int(df[fraud_col].sum())
        kpis['Fraud Rate %'] = round(safe_divide(int(df[fraud_col].sum()), len(df)) * 100, 4)

    return kpis


def get_available_scenarios(metadata):
    """Return available scenarios based on dataset columns."""
    roles = metadata.get('roles', {})
    available = {}

    if roles.get('amount'):
        available['value_increase'] = SCENARIOS['value_increase']
        available['value_decrease'] = SCENARIOS['value_decrease']
        available['volume_increase'] = SCENARIOS['volume_increase']

    if roles.get('fraud'):
        available['fraud_rate_change'] = SCENARIOS['fraud_rate_change']

    if roles.get('status'):
        available['failure_rate_change'] = SCENARIOS['failure_rate_change']

    return available
