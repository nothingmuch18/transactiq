import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import AnimatedPage from '../motion/AnimatedPage'
import { api } from '../lib/api'
import LoadingSkeleton from '../components/LoadingSkeleton'
import ChartContainer from '../components/ChartContainer'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts'

export default function Compare() {
    const [dims, setDims] = useState(null)
    const [selected, setSelected] = useState({ dimension: '', group_a: '', group_b: '' })
    const [result, setResult] = useState(null)
    const [loading, setLoading] = useState(false)

    useEffect(() => {
        api.compareDimensions().then(d => {
            setDims(d.dimensions)
            const first = Object.keys(d.dimensions)[0]
            if (first) {
                const vals = d.dimensions[first].values
                setSelected({ dimension: first, group_a: vals[0] || '', group_b: vals[1] || '' })
            }
        }).catch(console.error)
    }, [])

    const run = async () => {
        if (!selected.dimension || !selected.group_a || !selected.group_b) return
        setLoading(true)
        try { setResult(await api.compare(selected)) } catch (e) { console.error(e) }
        setLoading(false)
    }

    return (
        <AnimatedPage>
            <h1 className="text-2xl font-extrabold text-white tracking-tight mb-1">🔄 Compare</h1>
            <p className="text-sm text-slate-500 mb-6">Side-by-side comparison of any two groups or time periods</p>

            {dims && (
                <div className="glass-sm p-5 mb-6">
                    <div className="grid grid-cols-3 gap-4">
                        <div>
                            <label className="text-xs font-bold text-slate-500 uppercase tracking-wide">Dimension</label>
                            <select className="input-premium mt-1" value={selected.dimension}
                                onChange={e => {
                                    const d = e.target.value
                                    const vals = dims[d]?.values || []
                                    setSelected({ dimension: d, group_a: vals[0] || '', group_b: vals[1] || '' })
                                }}>
                                {Object.keys(dims).map(d => <option key={d} value={d}>{d}</option>)}
                            </select>
                        </div>
                        <div>
                            <label className="text-xs font-bold text-slate-500 uppercase tracking-wide">Group A</label>
                            <select className="input-premium mt-1" value={selected.group_a}
                                onChange={e => setSelected(s => ({ ...s, group_a: e.target.value }))}>
                                {dims[selected.dimension]?.values?.map(v => <option key={v} value={v}>{v}</option>)}
                            </select>
                        </div>
                        <div>
                            <label className="text-xs font-bold text-slate-500 uppercase tracking-wide">Group B</label>
                            <select className="input-premium mt-1" value={selected.group_b}
                                onChange={e => setSelected(s => ({ ...s, group_b: e.target.value }))}>
                                {dims[selected.dimension]?.values?.map(v => <option key={v} value={v}>{v}</option>)}
                            </select>
                        </div>
                    </div>
                    <button className="btn-primary mt-4" onClick={run}>Compare</button>
                </div>
            )}

            {loading && <LoadingSkeleton rows={5} />}

            {result && (
                <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
                    <div className="glass-sm p-4 border-l-[3px] border-indigo-500/50 mb-4">
                        <p className="text-sm text-slate-300 leading-relaxed">{result.explanation}</p>
                    </div>

                    {result.comparison?.length > 0 && (
                        <div className="glass-sm overflow-hidden mb-4">
                            <table className="w-full text-sm">
                                <thead>
                                    <tr className="border-b border-white/[0.06]">
                                        {result.columns?.map(c => <th key={c} className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wider text-slate-500">{c}</th>)}
                                    </tr>
                                </thead>
                                <tbody>
                                    {result.comparison.map((row, i) => (
                                        <tr key={i} className="border-b border-white/[0.03] hover:bg-white/[0.02]">
                                            {result.columns?.map(c => <td key={c} className="px-4 py-2.5 text-slate-300 font-mono text-xs">{typeof row[c] === 'number' ? row[c].toLocaleString() : row[c]}</td>)}
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}

                    {result.chart_data?.length > 0 && (
                        <ChartContainer title="Visual Comparison">
                            <ResponsiveContainer width="100%" height={280}>
                                <BarChart data={result.chart_data}>
                                    <XAxis dataKey="Metric" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                                    <YAxis tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                                    <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 12, color: '#e2e8f0' }} />
                                    <Legend wrapperStyle={{ color: '#94a3b8', fontSize: 12 }} />
                                    {Object.keys(result.chart_data[0]).filter(k => k !== 'Metric').map((k, i) => (
                                        <Bar key={k} dataKey={k} fill={i === 0 ? '#6366f1' : '#8b5cf6'} radius={[6, 6, 0, 0]} />
                                    ))}
                                </BarChart>
                            </ResponsiveContainer>
                        </ChartContainer>
                    )}
                </motion.div>
            )}
        </AnimatedPage>
    )
}
