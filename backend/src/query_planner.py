"""
AI Query Planner — Converts natural language queries into structured JSON execution plans.
Uses keyword-based intent classification. No LLM. Zero hallucination.
"""
import re
import calendar
from src.utils import safe_match_column


# --- Intent Patterns ---
INTENT_PATTERNS = {
    'total_volume': [
        r'\b(total|overall|all)\b.*\b(transactions?|count|volume|number)\b',
        r'\b(how many)\b.*\b(transactions?)\b',
        r'\btotal\s+(number|count)\b',
    ],
    'total_value': [
        r'\b(total|overall|sum|aggregate)\b.*\b(value|amount|revenue|money|inr|rupee)\b',
        r'\btotal\s+amount\b', r'\bsum\s+of\b.*\b(amount|value)\b',
    ],
    'average_value': [
        r'\b(average|avg|mean)\b.*\b(value|amount|transaction|size)\b',
        r'\baverage\s+transaction\b',
    ],
    'trend_analysis': [
        r'\btrend\b', r'\b(monthly|weekly|daily)\b.*\b(trend|pattern|movement)\b',
        r'\bover\s+time\b', r'\btime\s+series\b', r'\bgrowth\s+(over|trend)\b',
        r'\bshow\b.*\bmonth\b',
    ],
    'month_over_month': [
        r'\bmonth[\s\-]over[\s\-]month\b', r'\bmom\b', r'\bmonthly\s+growth\b',
        r'\bgrowth\s+rate\b.*\bmonth\b',
    ],
    'top_k': [
        r'\btop\b\s*\d*', r'\bhighest\b', r'\blargest\b', r'\bbiggest\b',
        r'\bmost\b', r'\bleading\b', r'\bbest\b', r'\bmaximum\b',
    ],
    'bottom_k': [
        r'\bbottom\b\s*\d*', r'\blowest\b', r'\bsmallest\b', r'\bleast\b',
        r'\bworst\b', r'\bminimum\b', r'\bfewest\b',
    ],
    'comparison': [
        r'\bcompare\b', r'\bvs\b', r'\bversus\b', r'\bdifference\b.*\bbetween\b',
        r'\bcomparison\b',
    ],
    'distribution': [
        r'\bdistribution\b', r'\bbreakdown\b', r'\bspread\b', r'\bshare\b',
        r'\bproportion\b', r'\bpercentage\b.*\bby\b', r'\bcomposition\b',
    ],
    'anomaly_detection': [
        r'\banom', r'\boutlier', r'\bunusual\b', r'\bspike\b', r'\bsudden\b',
        r'\babnormal\b', r'\birregular\b', r'\bsuspicious\b',
    ],
    'data_quality': [
        r'\bmissing\b', r'\bnull\b', r'\bduplicate\b', r'\bquality\b',
        r'\binconsisten', r'\bclean\b', r'\bdata\s+issue\b',
    ],
    'concentration': [
        r'\bconcentrat', r'\bdominan', r'\bmarket\s+share\b', r'\bherfindahl\b',
        r'\bgini\b', r'\brisk\s+index\b',
    ],
    'fraud': [
        r'\bfraud\b', r'\bfraudulent\b', r'\bsuspicious\b.*\btransaction\b',
        r'\bfraud\s+rate\b', r'\bfraud\s+flag\b',
    ],
    'failure_analysis': [
        r'\bfail', r'\bfailure\b', r'\bfailed\b', r'\bsuccess\s+rate\b',
        r'\btransaction\s+status\b',
    ],
    'peak_analysis': [
        r'\bpeak\b', r'\bbusiest\b', r'\bhighest\s+activity\b',
        r'\bwhen\b.*\bmost\b', r'\bpeak\s+(hour|day|month|time)\b',
    ],
    'explanation': [
        r'\bexplain\b', r'\bwhy\b', r'\bhow\b.*\bcomputed\b',
        r'\breason\b', r'\bcause\b',
    ],
    'histogram': [
        r'\bhistogram\b', r'\bfrequency\s+distribution\b',
        r'\bvalue\s+distribution\b', r'\bbucket\b', r'\bbin\b',
    ],
    'forecast': [
        r'\bforecast\b', r'\bpredict\b', r'\bprojection\b',
        r'\bnext\s+\d*\s*month\b', r'\bfuture\b', r'\bforecast\b',
        r'\bestimate\s+next\b', r'\bwhat.*will\b',
    ],
    'scenario': [
        r'\bwhat\s+if\b', r'\bscenario\b', r'\bsimulat\b',
        r'\bimpact\s+of\b', r'\bhypothetical\b',
    ],
}

# --- Aggregation keywords ---
AGG_KEYWORDS = {
    'sum': ['sum', 'total', 'aggregate', 'combined', 'overall'],
    'mean': ['average', 'avg', 'mean'],
    'count': ['count', 'number', 'how many', 'volume'],
    'max': ['max', 'maximum', 'highest', 'largest', 'biggest', 'peak'],
    'min': ['min', 'minimum', 'lowest', 'smallest'],
    'std': ['std', 'standard deviation', 'volatility', 'deviation'],
    'median': ['median', 'middle'],
}

# --- Visualization mapping ---
VIZ_MAPPING = {
    'trend_analysis': 'line',
    'month_over_month': 'bar',
    'top_k': 'bar',
    'bottom_k': 'bar',
    'distribution': 'pie',
    'comparison': 'grouped_bar',
    'anomaly_detection': 'scatter',
    'total_volume': 'metric',
    'total_value': 'metric',
    'average_value': 'metric',
    'concentration': 'bar',
    'fraud': 'bar',
    'failure_analysis': 'bar',
    'peak_analysis': 'bar',
    'data_quality': 'table',
    'explanation': 'table',
    'histogram': 'histogram',
    'forecast': 'line',
    'scenario': 'table',
}

# --- Group-by keywords ---
GROUPBY_KEYWORDS = {
    'month': ['month', 'monthly', 'by month'],
    'state': ['state', 'region', 'by state', 'statewise', 'state-wise'],
    'category': ['category', 'merchant', 'by category'],
    'bank': ['bank', 'by bank'],
    'transaction_type': ['type', 'transaction type', 'p2p', 'p2m'],
    'day_of_week': ['day', 'weekday', 'daily', 'day of week'],
    'hour': ['hour', 'hourly', 'time of day', 'hour of day'],
    'age': ['age', 'age group', 'demographic'],
    'device': ['device', 'android', 'ios', 'web'],
    'network': ['network', '4g', '5g', 'wifi'],
    'quarter': ['quarter', 'quarterly', 'q1', 'q2', 'q3', 'q4'],
    'weekend': ['weekend', 'weekday'],
}


def classify_intent(query):
    """Classify the intent of a natural language query."""
    query_lower = query.lower().strip()
    scores = {}
    for intent, patterns in INTENT_PATTERNS.items():
        score = 0
        for pattern in patterns:
            if re.search(pattern, query_lower):
                score += 1
        if score > 0:
            scores[intent] = score

    if not scores:
        return 'general'
    return max(scores, key=scores.get)


def extract_aggregation(query):
    """Extract the aggregation function from query."""
    query_lower = query.lower()
    for agg, keywords in AGG_KEYWORDS.items():
        for kw in keywords:
            if kw in query_lower:
                return agg
    return 'sum'  # Default


def extract_top_k(query):
    """Extract the K value from top/bottom K queries."""
    match = re.search(r'\btop\s*(\d+)', query.lower())
    if match:
        return int(match.group(1))
    match = re.search(r'\bbottom\s*(\d+)', query.lower())
    if match:
        return int(match.group(1))
    match = re.search(r'(\d+)\s*(largest|biggest|highest|lowest|smallest)', query.lower())
    if match:
        return int(match.group(1))
    return 10  # Default


def extract_groupby(query, metadata):
    """Extract group-by field from query, using metadata for column matching."""
    query_lower = query.lower()
    roles = metadata.get('roles', {})

    for group_key, keywords in GROUPBY_KEYWORDS.items():
        for kw in keywords:
            if kw in query_lower:
                # Map group_key to actual column
                if group_key == 'month' and 'date' in roles:
                    return 'month'
                elif group_key == 'quarter' and 'date' in roles:
                    return 'quarter'
                elif group_key == 'state' and 'region' in roles:
                    return roles['region']
                elif group_key == 'category' and 'category' in roles:
                    return roles['category']
                elif group_key == 'bank':
                    return roles.get('sender_bank', roles.get('bank', 'sender_bank'))
                elif group_key == 'transaction_type' and 'transaction_type' in roles:
                    return roles['transaction_type']
                elif group_key == 'day_of_week':
                    return 'day_of_week'
                elif group_key == 'hour':
                    return 'hour_of_day'
                elif group_key == 'age':
                    return 'sender_age_group'
                elif group_key == 'device':
                    return 'device_type'
                elif group_key == 'network':
                    return 'network_type'
                elif group_key == 'weekend':
                    return 'is_weekend'
    return None


def extract_filters(query, df):
    """Extract filter conditions from query."""
    filters = []
    query_lower = query.lower()

    # Status filter
    if 'success' in query_lower and 'fail' not in query_lower:
        status_col = safe_match_column(df, 'status')
        if status_col:
            filters.append({'column': status_col, 'op': '==', 'value': 'SUCCESS'})
    elif 'fail' in query_lower and 'success' not in query_lower:
        status_col = safe_match_column(df, 'status')
        if status_col:
            filters.append({'column': status_col, 'op': '==', 'value': 'FAILED'})

    # Fraud filter
    if 'fraud' in query_lower and 'non-fraud' not in query_lower:
        fraud_col = safe_match_column(df, 'fraud')
        if fraud_col:
            filters.append({'column': fraud_col, 'op': '==', 'value': 1})

    # Transaction type filter
    for tt in ['P2P', 'P2M', 'Bill Payment', 'Recharge']:
        if tt.lower() in query_lower:
            tt_col = safe_match_column(df, 'transaction type')
            if tt_col:
                filters.append({'column': tt_col, 'op': '==', 'value': tt})
                break

    # Specific state mentions
    states = ['delhi', 'maharashtra', 'karnataka', 'tamil nadu', 'uttar pradesh',
              'gujarat', 'rajasthan', 'telangana', 'andhra pradesh', 'west bengal']
    for state in states:
        if state in query_lower:
            state_col = safe_match_column(df, 'state')
            if state_col:
                filters.append({'column': state_col, 'op': '==', 'value': state.title()})

    # Specific category mentions
    categories = ['food', 'shopping', 'grocery', 'fuel', 'utilities', 'entertainment',
                  'healthcare', 'education', 'transport', 'other']
    for cat in categories:
        if cat in query_lower:
            cat_col = safe_match_column(df, 'category')
            if cat_col:
                filters.append({'column': cat_col, 'op': '==', 'value': cat.title()})
                break

    # Amount threshold
    amount_match = re.search(r'(?:above|over|greater than|more than|>)\s*(?:₹|rs\.?|inr)?\s*([\d,]+)', query_lower)
    if amount_match:
        val = int(amount_match.group(1).replace(',', ''))
        amount_col = safe_match_column(df, 'amount')
        if amount_col:
            filters.append({'column': amount_col, 'op': '>', 'value': val})

    amount_match2 = re.search(r'(?:below|under|less than|<)\s*(?:₹|rs\.?|inr)?\s*([\d,]+)', query_lower)
    if amount_match2:
        val = int(amount_match2.group(1).replace(',', ''))
        amount_col = safe_match_column(df, 'amount')
        if amount_col:
            filters.append({'column': amount_col, 'op': '<', 'value': val})

    # Date range filter
    month_names = {name.lower(): num for num, name in enumerate(calendar.month_name) if num}
    month_abbrs = {name.lower(): num for num, name in enumerate(calendar.month_abbr) if num}
    all_months = {**month_names, **month_abbrs}

    date_range_pattern = r'(?:between|from)\s+(\w+)\s*(?:to|and|-)\s*(\w+)'
    date_match = re.search(date_range_pattern, query_lower)
    if date_match:
        start_str = date_match.group(1).strip()
        end_str = date_match.group(2).strip()
        if start_str in all_months and end_str in all_months:
            # Extract year if mentioned
            year_match = re.search(r'(20\d{2})', query_lower)
            year = int(year_match.group(1)) if year_match else 2024
            start_month = all_months[start_str]
            end_month = all_months[end_str]
            date_col_match = safe_match_column(df, 'timestamp') or safe_match_column(df, 'date')
            if date_col_match:
                import pandas as pd
                start_date = pd.Timestamp(year=year, month=start_month, day=1)
                end_date = pd.Timestamp(year=year, month=end_month, day=1) + pd.offsets.MonthEnd(1)
                filters.append({'column': date_col_match, 'op': '>=', 'value': start_date})
                filters.append({'column': date_col_match, 'op': '<=', 'value': end_date})

    return filters


def extract_metric_column(query, metadata):
    """Determine which column to compute metrics on."""
    query_lower = query.lower()
    roles = metadata.get('roles', {})

    if any(kw in query_lower for kw in ['amount', 'value', 'revenue', 'money', 'inr', 'rupee', 'spent', 'spending']):
        return roles.get('amount', None)
    if any(kw in query_lower for kw in ['count', 'volume', 'number', 'transactions', 'how many']):
        return '__count__'

    # Default to amount for value-related intents
    return roles.get('amount', '__count__')


def extract_comparison_entities(query, df, metadata):
    """Extract two entities being compared."""
    query_lower = query.lower()
    roles = metadata.get('roles', {})

    # Pattern: "compare X vs Y" or "X versus Y" or "difference between X and Y"
    patterns = [
        r'compare\s+(.+?)\s+(?:vs|versus|and|with)\s+(.+?)(?:\s|$)',
        r'(?:difference|comparison)\s+between\s+(.+?)\s+and\s+(.+?)(?:\s|$)',
        r'(.+?)\s+vs\.?\s+(.+?)(?:\s|$)',
    ]
    for pattern in patterns:
        match = re.search(pattern, query_lower)
        if match:
            entity_a = match.group(1).strip()
            entity_b = match.group(2).strip()
            return entity_a, entity_b

    return None, None


def plan_query(query, df, metadata):
    """
    Convert a natural language query into a structured execution plan.
    Returns a dict with operation details.
    """
    intent = classify_intent(query)
    agg = extract_aggregation(query)
    group_by = extract_groupby(query, metadata)
    filters = extract_filters(query, df)
    metric_col = extract_metric_column(query, metadata)
    k = extract_top_k(query)
    viz = VIZ_MAPPING.get(intent, 'table')

    plan = {
        'intent': intent,
        'query': query,
        'aggregation': agg,
        'metric_column': metric_col,
        'group_by': group_by,
        'filters': filters,
        'k': k,
        'visualization': viz,
    }

    # Refine plan based on intent
    if intent == 'trend_analysis':
        if not group_by:
            plan['group_by'] = 'month'
        plan['visualization'] = 'line'

    elif intent == 'month_over_month':
        plan['group_by'] = 'month'
        plan['visualization'] = 'bar'

    elif intent == 'comparison':
        entity_a, entity_b = extract_comparison_entities(query, df, metadata)
        plan['compare_a'] = entity_a
        plan['compare_b'] = entity_b

    elif intent == 'distribution':
        if not group_by:
            # Try to find a sensible categorical grouping
            roles = metadata.get('roles', {})
            plan['group_by'] = roles.get('category', roles.get('region', None))
        plan['visualization'] = 'pie'

    elif intent in ('top_k', 'bottom_k'):
        if not group_by:
            roles = metadata.get('roles', {})
            plan['group_by'] = roles.get('region', roles.get('category', None))
        plan['visualization'] = 'bar'

    elif intent in ('total_volume', 'total_value', 'average_value'):
        plan['visualization'] = 'metric'

    elif intent == 'peak_analysis':
        if not group_by:
            plan['group_by'] = 'month'

    elif intent == 'histogram':
        plan['visualization'] = 'histogram'

    elif intent == 'forecast':
        plan['visualization'] = 'line'

    elif intent == 'scenario':
        plan['visualization'] = 'table'

    return plan
