const BASE = '/api'

async function request(url, options = {}) {
    const res = await fetch(`${BASE}${url}`, {
        headers: { 'Content-Type': 'application/json', ...options.headers },
        ...options,
    })
    if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body.detail || `API error: ${res.status}`)
    }
    return res.json()
}

export const api = {
    health: () => request('/health'),
    overview: () => request('/overview'),
    query: (query) => request('/query', { method: 'POST', body: JSON.stringify({ query }) }),
    insights: () => request('/insights'),
    anomalies: (params = {}) => request('/anomalies', { method: 'POST', body: JSON.stringify(params) }),
    risk: (dimension) => request(`/risk${dimension ? `?dimension=${dimension}` : ''}`),
    compareDimensions: () => request('/compare/dimensions'),
    compare: (params) => request('/compare', { method: 'POST', body: JSON.stringify(params) }),
    quality: () => request('/quality'),

    // Upload & Schema
    upload: async (file) => {
        const form = new FormData()
        form.append('file', file)
        const res = await fetch(`${BASE}/upload`, { method: 'POST', body: form })
        if (!res.ok) {
            const body = await res.json().catch(() => ({}))
            throw new Error(body.detail || `Upload failed: ${res.status}`)
        }
        return res.json()
    },
    reset: () => request('/reset', { method: 'POST' }),
    schema: () => request('/schema'),
    preview: (limit = 50) => request(`/preview?limit=${limit}`),
    exportCSV: () => `${BASE}/export`,
}
