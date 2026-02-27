import { useState } from 'react'
import { motion } from 'framer-motion'
import AnimatedPage from '../motion/AnimatedPage'
import { api } from '../lib/api'
import ChartContainer from '../components/ChartContainer'
import LoadingSkeleton from '../components/LoadingSkeleton'
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { Send, Clock, Database, Target } from 'lucide-react'

const COLORS = ['#6366f1', '#8b5cf6', '#14b8a6', '#3b82f6', '#ec4899', '#f59e0b', '#10b981']
const SAMPLES = [
    'What is the total transaction value?',
    'Top 10 states by transaction value',
    'Show month-over-month growth rate',
    'Compare Delhi vs Maharashtra',
    'What is the fraud rate?',
    'Forecast next month trend',
    'Distribution by category',
    'Show transactions above 5000',
]

export default function AskAI() {
    const [query, setQuery] = useState('')
    const [result, setResult] = useState(null)
    const [loading, setLoading] = useState(false)
    const [history, setHistory] = useState([])

    const execute = async (q) => {
        const text = q || query
        if (!text.trim()) return
        setLoading(true)
        setResult(null)
        try {
            const res = await api.query(text)
            setResult(res)
            setHistory(h => [{ query: text, intent: res.plan.intent, time: res.exec_time_ms }, ...h.slice(0, 9)])
        } catch (e) { console.error(e) }
        setLoading(false)
    }

    const renderChart = () => {
        if (!result || !result.results?.length || !result.chart_spec) return null
        const spec = result.chart_spec
        if (spec.type === 'metric' || spec.type === 'table') return null
        const data = result.results

        if (spec.type === 'line')
            return (
                <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={data}><XAxis dataKey={spec.x} tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} /><YAxis tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} /><Tooltip contentStyle={{ background: '#0f172a', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 12, color: '#e2e8f0' }} /><Line type="monotone" dataKey={spec.y} stroke="#6366f1" strokeWidth={2.5} dot={{ fill: '#6366f1', r: 3 }} /></LineChart>
                </ResponsiveContainer>
            )

        if (spec.type === 'pie')
            return (
                <ResponsiveContainer width="100%" height={300}>
                    <PieChart><Pie data={data} dataKey={spec.y} nameKey={spec.x} cx="50%" cy="50%" innerRadius={60} outerRadius={100} strokeWidth={0}>{data.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}</Pie><Tooltip contentStyle={{ background: '#0f172a', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 12, color: '#e2e8f0' }} /></PieChart>
                </ResponsiveContainer>
            )

        return (
            <ResponsiveContainer width="100%" height={300}>
                <BarChart data={data}><XAxis dataKey={spec.x} tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} /><YAxis tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} /><Tooltip contentStyle={{ background: '#0f172a', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 12, color: '#e2e8f0' }} /><Bar dataKey={spec.y} fill="#6366f1" radius={[6, 6, 0, 0]} /></BarChart>
            </ResponsiveContainer>
        )
    }

    return (
        <AnimatedPage>
            <h1 className="text-2xl font-extrabold text-white tracking-tight mb-1">🧠 Ask AI</h1>
            <p className="text-sm text-slate-500 mb-6">Ask any question in plain English — the engine converts it to a structured plan</p>

            {/* Query Input */}
            <div className="flex gap-3 mb-4">
                <input className="input-premium flex-1" value={query} onChange={e => setQuery(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && execute()} placeholder="e.g., Top 10 states by total value" />
                <button className="btn-primary flex items-center gap-2" onClick={() => execute()}>
                    <Send size={16} /> Ask
                </button>
            </div>

            {/* Sample chips */}
            <div className="flex flex-wrap gap-2 mb-6">
                {SAMPLES.map(s => (
                    <button key={s} onClick={() => { setQuery(s); execute(s) }}
                        className="text-xs px-3 py-1.5 rounded-full bg-white/[0.04] border border-white/[0.06] text-slate-400 hover:text-indigo-400 hover:border-indigo-500/30 transition-all duration-200">
                        {s}
                    </button>
                ))}
            </div>

            {loading && <LoadingSkeleton rows={5} />}

            {result && (
                <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
                    {/* Exec Meta */}
                    <div className="flex gap-3 mb-4 flex-wrap">
                        <span className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-indigo-500/10 text-indigo-400 text-xs font-semibold">
                            <Target size={12} /> {result.plan.intent}
                        </span>
                        <span className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/[0.04] text-slate-400 text-xs font-mono">
                            <Database size={12} /> {result.rows_scanned?.toLocaleString()} rows
                        </span>
                        <span className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/[0.04] text-slate-400 text-xs font-mono">
                            <Clock size={12} /> {result.exec_time_ms?.toFixed(1)}ms
                        </span>
                    </div>

                    {/* Explanation */}
                    <div className="glass-sm p-4 border-l-[3px] border-indigo-500/50 mb-4">
                        <p className="text-sm text-slate-300 leading-relaxed">{result.explanation}</p>
                    </div>

                    {/* Table */}
                    {result.results?.length > 0 && (
                        <div className="glass-sm overflow-hidden mb-4">
                            <div className="overflow-x-auto">
                                <table className="w-full text-sm">
                                    <thead>
                                        <tr className="border-b border-white/[0.06]">
                                            {result.columns.map(c => <th key={c} className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wider text-slate-500">{c}</th>)}
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {result.results.slice(0, 20).map((row, i) => (
                                            <tr key={i} className="border-b border-white/[0.03] hover:bg-white/[0.02] transition-colors">
                                                {result.columns.map(c => <td key={c} className="px-4 py-2.5 text-slate-300 font-mono text-xs">{typeof row[c] === 'number' ? row[c].toLocaleString() : row[c]}</td>)}
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}

                    {/* Chart */}
                    <ChartContainer>{renderChart()}</ChartContainer>
                </motion.div>
            )}

            {/* History */}
            {history.length > 0 && (
                <div className="mt-6">
                    <p className="section-label">Recent Queries</p>
                    <div className="space-y-1">
                        {history.map((h, i) => (
                            <div key={i} className="flex items-center justify-between text-xs text-slate-500 py-1">
                                <span className="text-slate-400">{h.query}</span>
                                <span className="font-mono">{h.intent} · {h.time}ms</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </AnimatedPage>
    )
}
