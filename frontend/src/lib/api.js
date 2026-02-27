const BASE = '/data' // Route directly to the public/data folder

async function request(file) {
    const res = await fetch(`${BASE}/${file}`)
    if (!res.ok) {
        throw new Error(`Data load failed: ${res.status}`)
    }
    return res.json()
}

export const api = {
    health: () => Promise.resolve({ status: 'ok', message: 'Running in serverless static mode' }),
    overview: () => request('overview.json'),

    // AI NLP Queries cannot run without a Python backend, returning static mock
    query: (query) => Promise.resolve({
        answer: "I am currently running in **Serverless Offline Mode**. The NLP engine is disabled, but the dashboard data is still fully available.",
        data: null
    }),

    insights: () => request('insights.json'),
    anomalies: () => request('anomalies.json'),
    risk: () => request('risk.json'),

    // Compare is dynamic normally, we'll return the hardcoded default or empty
    compareDimensions: () => Promise.resolve({
        dimension1: ['Category', 'Payer City'],
        dimension2: ['Receiver Type'],
        metrics: ['value']
    }),
    compare: () => request('compare.json'),

    quality: () => request('quality.json'),

    // Upload & Schema cannot work dynamically without Python Pandas
    upload: async () => {
        throw new Error("Dynamic CSV Uploads are disabled in Serverless mode.")
    },
    reset: () => Promise.resolve({ status: 'ok' }),
    schema: () => request('schema.json'),
    preview: () => request('preview.json'),
    exportCSV: () => `/data/upi_transactions.csv`,
}
