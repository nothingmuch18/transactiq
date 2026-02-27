import { useEffect, useState, useMemo } from 'react'
import { motion } from 'framer-motion'
import AnimatedPage from '../motion/AnimatedPage'
import { api } from '../lib/api'
import KpiCard, { formatINR } from '../components/KpiCard'
import ChartContainer from '../components/ChartContainer'
import { KpiSkeleton } from '../components/LoadingSkeleton'
import LoadingSkeleton from '../components/LoadingSkeleton'
import { AreaChart, Area, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

export default function Predictions() {
    const [forecast, setForecast] = useState(null)
    const [scenarios, setScenarios] = useState(null)
    const [scenarioResult, setScenarioResult] = useState(null)
    const [selectedScenario, setSelectedScenario] = useState('')
    const [scenarioValue, setScenarioValue] = useState(20)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    useEffect(() => {
        let cancelled = false
        Promise.all([api.forecast(3), api.scenarios()])
            .then(([f, s]) => {
                if (cancelled) return
                setForecast(f)
                setScenarios(s.scenarios || [])
                if (s.scenarios?.length) setSelectedScenario(s.scenarios[0].id)
            })
            .catch(e => { if (!cancelled) setError(e.message) })
            .finally(() => { if (!cancelled) setLoading(false) })
        return () => { cancelled = true }
    }, [])

    const runScenario = async () => {
        if (!selectedScenario) return
        try {
            setScenarioResult(null)
            const res = await api.scenario(selectedScenario, scenarioValue)
            setScenarioResult(res)
        } catch (e) { console.error(e) }
    }

    // Normalize column names from API to chart-friendly keys
    const chartData = useMemo(() => {
        if (!forecast) return []
        const historical = (forecast.historical || []).map(d => ({
            month: d.Month || d.month || '',
            actual: d.Actual ?? d.actual ?? d.value ?? null,
            fitted: d.Fitted ?? d.fitted ?? null,
        }))
        const predicted = (forecast.forecast || []).map(d => ({
            month: d.Month || d.month || '',
            predicted: d.Predicted ?? d.predicted ?? null,
            upper: d['Upper (95%)'] ?? d.upper ?? null,
            lower: d['Lower (95%)'] ?? d.lower ?? null,
        }))
        return [...historical, ...predicted]
    }, [forecast])

    if (loading) return <AnimatedPage><KpiSkeleton count={4} /><LoadingSkeleton rows={5} className="mt-4" /></AnimatedPage>

    if (error) return (
        <AnimatedPage>
            <div className="glass p-8 text-center">
                <div className="text-4xl mb-4">⚠️</div>
                <h2 className="text-lg font-bold text-white mb-2">Predictions Unavailable</h2>
                <p className="text-sm text-slate-400">{error}</p>
            </div>
        </AnimatedPage>
    )

    const metrics = forecast?.metrics || {}

    return (
        <AnimatedPage>
            <h1 className="text-2xl font-extrabold text-white tracking-tight mb-1">✨ Predictions</h1>
            <p className="text-sm text-slate-500 mb-6">Trend forecasting with confidence intervals and what-if scenario simulation</p>

            {/* Metrics */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
                <KpiCard label="RMSE" rawValue={metrics.rmse || 0} formatter={v => formatINR(v)} accent="indigo" />
                <KpiCard label="MAE" rawValue={metrics.mae || 0} formatter={v => formatINR(v)} accent="violet" />
                <KpiCard label="R² Score" rawValue={metrics.r2 || 0} formatter={v => v.toFixed(3)} accent={metrics.r2 > 0.7 ? 'green' : 'amber'} />
                <KpiCard label="MAPE" rawValue={metrics.mape || 0} formatter={v => `${v.toFixed(1)}%`} accent="teal" />
            </div>

            {/* Forecast Chart */}
            {chartData.length > 0 && (
                <ChartContainer title="Monthly Forecast with Confidence Interval" className="mb-6">
                    <ResponsiveContainer width="100%" height={320}>
                        <AreaChart data={chartData}>
                            <defs>
                                <linearGradient id="forecastGrad" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="0%" stopColor="#6366f1" stopOpacity={0.15} />
                                    <stop offset="100%" stopColor="#6366f1" stopOpacity={0.02} />
                                </linearGradient>
                            </defs>
                            <XAxis dataKey="month" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false}
                                tickFormatter={v => { try { return new Date(v).toLocaleDateString('en', { month: 'short' }) } catch { return v?.toString().slice(5, 7) } }} />
                            <YAxis tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false}
                                tickFormatter={v => `${(v / 1e6).toFixed(0)}M`} />
                            <Tooltip
                                contentStyle={{ background: '#0f172a', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 12, color: '#e2e8f0', fontSize: 12 }}
                                formatter={(v) => v != null ? [formatINR(v)] : ['-']}
                                labelFormatter={v => { try { return new Date(v).toLocaleDateString('en-IN', { month: 'long', year: 'numeric' }) } catch { return v } }}
                            />
                            <Area type="monotone" dataKey="upper" stroke="transparent" fill="url(#forecastGrad)" fillOpacity={1} />
                            <Area type="monotone" dataKey="lower" stroke="transparent" fill="#0a0f1e" fillOpacity={0.8} />
                            <Line type="monotone" dataKey="actual" stroke="#6366f1" strokeWidth={2.5} dot={{ fill: '#6366f1', r: 3, strokeWidth: 0 }} connectNulls={false} />
                            <Line type="monotone" dataKey="fitted" stroke="#6366f1" strokeWidth={1.5} strokeOpacity={0.4} dot={false} connectNulls={false} />
                            <Line type="monotone" dataKey="predicted" stroke="#8b5cf6" strokeWidth={2.5} strokeDasharray="6 3" dot={{ fill: '#8b5cf6', r: 4, strokeWidth: 0 }} connectNulls={false} />
                        </AreaChart>
                    </ResponsiveContainer>
                </ChartContainer>
            )}

            {/* Explanation */}
            {forecast?.explanation && (
                <div className="glass-sm p-4 border-l-[3px] border-indigo-500/50 mb-6">
                    <p className="text-sm text-slate-300 leading-relaxed">{forecast.explanation}</p>
                </div>
            )}

            {/* Model Info */}
            {forecast?.model_info && (
                <div className="glass-sm p-4 mb-6">
                    <p className="text-[0.65rem] font-bold uppercase tracking-[0.1em] text-slate-500 mb-2">Model Details</p>
                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-2 text-xs text-slate-400">
                        <span>Method: <span className="text-slate-200 font-semibold">{forecast.model_info.method}</span></span>
                        <span>Slope: <span className="text-slate-200 font-mono">{forecast.model_info.slope?.toLocaleString()}</span>/month</span>
                        <span>Train: <span className="text-slate-200 font-mono">{metrics.train_size}</span> months</span>
                        <span>Test: <span className="text-slate-200 font-mono">{metrics.test_size}</span> months</span>
                    </div>
                </div>
            )}

            {/* Scenario Simulation */}
            <p className="section-label">What-If Scenario Simulation</p>
            <div className="glass-sm p-5 mb-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
                    <div>
                        <label className="text-xs font-bold text-slate-500 uppercase tracking-wide block mb-1">Scenario</label>
                        <select className="input-premium" value={selectedScenario}
                            onChange={e => setSelectedScenario(e.target.value)}>
                            {scenarios?.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                        </select>
                    </div>
                    <div>
                        <label className="text-xs font-bold text-slate-500 uppercase tracking-wide block mb-1">Change (%)</label>
                        <input type="number" className="input-premium" value={scenarioValue}
                            onChange={e => setScenarioValue(parseFloat(e.target.value) || 0)} />
                    </div>
                    <button className="btn-primary h-[46px]" onClick={runScenario}>Simulate</button>
                </div>
            </div>

            {scenarioResult && (
                <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
                    <div className="glass-sm p-4 border-l-[3px] border-violet-500/50 mb-4">
                        <p className="text-sm text-slate-300 leading-relaxed">{scenarioResult.explanation}</p>
                    </div>
                    {scenarioResult.comparison?.length > 0 && (
                        <div className="glass-sm overflow-hidden">
                            <table className="w-full text-sm">
                                <thead>
                                    <tr className="border-b border-white/[0.06]">
                                        {Object.keys(scenarioResult.comparison[0]).map(k => (
                                            <th key={k} className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wider text-slate-500">{k}</th>
                                        ))}
                                    </tr>
                                </thead>
                                <tbody>
                                    {scenarioResult.comparison.map((row, i) => (
                                        <tr key={i} className="border-b border-white/[0.03] hover:bg-white/[0.02] transition-colors">
                                            {Object.values(row).map((v, j) => (
                                                <td key={j} className="px-4 py-2.5 text-slate-300 font-mono text-xs">{typeof v === 'number' ? v.toLocaleString('en-IN') : v}</td>
                                            ))}
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </motion.div>
            )}
        </AnimatedPage>
    )
}
