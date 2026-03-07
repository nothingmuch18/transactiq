/**
 * Static data API — loads pre-generated JSON from /data/ directory.
 * Falls back gracefully for endpoints that require a live backend.
 */

async function fetchJSON(path) {
    const res = await fetch(`/data/${path}`)
    if (!res.ok) {
        throw new Error(`Failed to load ${path}: ${res.status}`)
    }
    return res.json()
}

export const api = {
    health: () => Promise.resolve({ status: 'ok', rows: 250000, load_time_ms: 0, source: 'static' }),
    overview: () => fetchJSON('overview.json'),

    // AI NLP Query — not available in static mode
    query: () => Promise.reject(new Error('AI queries require a live backend. Upload your data to a running instance.')),

    // Insights
    insights: () => fetchJSON('insights.json'),

    // Anomaly detection
    anomalies: () => fetchJSON('anomalies.json'),

    // Risk analysis
    risk: () => fetchJSON('risk.json'),

    // Compare
    compareDimensions: () => fetchJSON('schema.json').then(s => s.categorical_columns || []),
    compare: () => fetchJSON('compare.json'),

    // Quality
    quality: () => fetchJSON('quality.json'),

    // Upload & Dataset management — not available in static mode
    upload: () => Promise.reject(new Error('Upload requires a live backend.')),
    reset: () => Promise.reject(new Error('Reset requires a live backend.')),
    schema: () => fetchJSON('schema.json'),
    preview: () => fetchJSON('preview.json'),
    exportCSV: () => '/data/preview.json',
}
