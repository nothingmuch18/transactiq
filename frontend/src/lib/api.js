const BASE = '/api'

async function request(path, options = {}) {
    const res = await fetch(`${BASE}/${path}`, options)
    if (!res.ok) {
        const text = await res.text().catch(() => '')
        throw new Error(`API error ${res.status}: ${text || res.statusText}`)
    }
    return res.json()
}

function post(path, body) {
    return request(path, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    })
}

export const api = {
    health: () => request('health'),
    overview: () => request('overview'),

    // AI NLP Query
    query: (query) => post('query', { query }),

    // Insights
    insights: () => request('insights'),

    // Anomaly detection
    anomalies: (methodOrObj = 'all') => {
        const method = typeof methodOrObj === 'object' ? (methodOrObj.method || 'all') : methodOrObj
        return post('anomalies', { method })
    },

    // Risk analysis
    risk: (dimension) => request(`risk${dimension ? `?dimension=${encodeURIComponent(dimension)}` : ''}`),

    // Compare
    compareDimensions: () => request('compare/dimensions'),
    compare: (dimOrObj, group_a, group_b) => {
        if (typeof dimOrObj === 'object') {
            return post('compare', { dimension: dimOrObj.dimension, group_a: dimOrObj.group_a, group_b: dimOrObj.group_b })
        }
        return post('compare', { dimension: dimOrObj, group_a, group_b })
    },

    // Quality
    quality: () => request('quality'),

    // Upload & Dataset management
    upload: async (file) => {
        const formData = new FormData()
        formData.append('file', file)
        const res = await fetch(`${BASE}/upload`, { method: 'POST', body: formData })
        if (!res.ok) throw new Error(`Upload failed: ${res.status}`)
        return res.json()
    },
    reset: () => post('reset', {}),
    schema: () => request('schema'),
    preview: (limit = 50) => request(`preview?limit=${limit}`),
    exportCSV: () => `${BASE}/export`,
}
