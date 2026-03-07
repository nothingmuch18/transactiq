/**
 * Static API layer — fetches pre-generated JSON from /data/*.json
 * Used for Netlify (and any static host) deployment.
 * POST-based endpoints (query, anomalies, compare) return cached static data.
 */

async function fetchJSON(path) {
    const res = await fetch(path)
    if (!res.ok) {
        const text = await res.text().catch(() => '')
        throw new Error(`Fetch error ${res.status}: ${text || res.statusText}`)
    }
    return res.json()
}

export const api = {
    health: () => Promise.resolve({ status: 'ok', mode: 'static' }),

    overview: () => fetchJSON('/data/overview.json'),

    // AI NLP Query — not available in static mode, return a helpful message
    query: (query) => Promise.resolve({
        intent: 'static_mode',
        answer: `This is a static demo deployment. The AI query engine requires a live backend server. Your query was: "${query}"`,
        data: null,
        visualization: null,
    }),

    // Insights
    insights: () => fetchJSON('/data/insights.json'),

    // Anomaly detection — returns pre-computed data
    anomalies: (_methodOrObj = 'all') => fetchJSON('/data/anomalies.json'),

    // Risk analysis
    risk: (_dimension) => fetchJSON('/data/risk.json'),

    // Compare — returns static dimensions + cached comparison
    compareDimensions: () => fetchJSON('/data/compare.json').then(d => d.dimensions || []),
    compare: (_dim, _a, _b) => fetchJSON('/data/compare.json'),

    // Quality
    quality: () => fetchJSON('/data/quality.json'),

    // Upload — disabled in static mode
    upload: async (_file) => {
        throw new Error('Upload is not available in this static demo. Please run the full-stack version locally.')
    },
    reset: () => Promise.resolve({ status: 'ok' }),
    schema: () => fetchJSON('/data/schema.json'),
    preview: (_limit = 50) => fetchJSON('/data/preview.json'),
    exportCSV: () => '/data/preview.json',
}
