import { useEffect, useState, useMemo } from 'react'
import AnimatedPage from '../motion/AnimatedPage'
import { api } from '../lib/api'
import KpiCard from '../components/KpiCard'
import ChartContainer from '../components/ChartContainer'
import { KpiSkeleton } from '../components/LoadingSkeleton'
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

export default function Risk() {
    const [data, setData] = useState(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        let cancelled = false
        api.risk()
            .then(d => { if (!cancelled) setData(d) })
            .catch(console.error)
            .finally(() => { if (!cancelled) setLoading(false) })
        return () => { cancelled = true }
    }, [])

    if (loading) return <AnimatedPage><KpiSkeleton count={4} /></AnimatedPage>

    const conc = data?.concentration || {}
    const hhi = (conc.hhi != null ? conc.hhi * 10000 : 0)

    return (
        <AnimatedPage>
            <h1 className="text-2xl font-extrabold text-white tracking-tight mb-1">📈 Risk & Concentration</h1>
            <p className="text-sm text-slate-500 mb-6">Market concentration, volatility, and composite risk scoring</p>

            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
                <KpiCard label="Risk Index" rawValue={data?.risk_index || 0} formatter={v => `${v.toFixed(1)}/100`} accent={data?.risk_index < 30 ? 'green' : data?.risk_index < 60 ? 'amber' : 'red'} />
                <KpiCard label="HHI" rawValue={hhi} formatter={v => v.toFixed(0)} accent="violet" />
                <KpiCard label="Concentration" value={conc.concentration_level || 'N/A'} accent="indigo" />
                <KpiCard label="Top Entity Share" rawValue={conc.top1_share || 0} formatter={v => `${v.toFixed(1)}%`} accent="teal" />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
                {conc.table?.length > 0 && (
                    <ChartContainer title="Market Share Distribution">
                        <ResponsiveContainer width="100%" height={300}>
                            <BarChart data={conc.table.slice(0, 15)} layout="vertical">
                                <XAxis type="number" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                                <YAxis type="category" dataKey={Object.keys(conc.table[0])[0]} tick={{ fill: '#94a3b8', fontSize: 10 }} axisLine={false} tickLine={false} width={90} />
                                <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 12, color: '#e2e8f0' }} />
                                <Bar dataKey="Share %" fill="#6366f1" radius={[0, 6, 6, 0]} />
                            </BarChart>
                        </ResponsiveContainer>
                    </ChartContainer>
                )}

                {data?.volatility?.monthly_data?.length > 0 && (
                    <ChartContainer title="Monthly Value Trend">
                        <ResponsiveContainer width="100%" height={300}>
                            <LineChart data={data.volatility.monthly_data}>
                                <XAxis dataKey="month" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={v => v?.slice(5, 7)} />
                                <YAxis tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={v => `${(v / 1e6).toFixed(0)}M`} />
                                <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 12, color: '#e2e8f0' }} />
                                <Line type="monotone" dataKey="value" stroke="#8b5cf6" strokeWidth={2.5} dot={{ fill: '#8b5cf6', r: 3 }} />
                            </LineChart>
                        </ResponsiveContainer>
                    </ChartContainer>
                )}
            </div>
        </AnimatedPage>
    )
}
