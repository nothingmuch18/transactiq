import { useEffect, useState, useMemo } from 'react'
import AnimatedPage from '../motion/AnimatedPage'
import { api } from '../lib/api'
import KpiCard, { formatINR, formatCount } from '../components/KpiCard'
import ChartContainer from '../components/ChartContainer'
import { KpiSkeleton } from '../components/LoadingSkeleton'
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts'

const COLORS = ['#6366f1', '#8b5cf6', '#14b8a6', '#3b82f6', '#ec4899', '#f59e0b', '#10b981', '#ef4444']

const fmtTooltip = (v) => v != null ? [`₹${(v / 1e7).toFixed(2)} Cr`] : ['-']

export default function Overview() {
    const [data, setData] = useState(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        let cancelled = false
        api.overview()
            .then(d => { if (!cancelled) setData(d) })
            .catch(console.error)
            .finally(() => { if (!cancelled) setLoading(false) })
        return () => { cancelled = true }
    }, [])

    if (loading) return <AnimatedPage><KpiSkeleton count={8} /></AnimatedPage>

    const k = data?.kpis || {}

    return (
        <AnimatedPage>
            <h1 className="text-2xl font-extrabold text-white tracking-tight mb-1">📊 Executive Overview</h1>
            <p className="text-sm text-slate-500 mb-6">Key performance indicators, trends, and dataset summary</p>

            <div className="grid grid-cols-2 lg:grid-cols-5 gap-3 mb-6">
                <KpiCard label="Transactions" rawValue={k.total_transactions} formatter={formatCount} accent="indigo" />
                <KpiCard label="Total Value" rawValue={k.total_value} formatter={formatINR} accent="violet" />
                <KpiCard label="Avg Txn" rawValue={k.avg_transaction} formatter={formatINR} accent="teal" />
                <KpiCard label="Success Rate" rawValue={k.success_rate || 0} formatter={v => `${v.toFixed(1)}%`} accent="green" />
                <KpiCard label="Risk Index" rawValue={k.risk_index} formatter={v => `${v.toFixed(1)}/100`} accent={k.risk_index < 30 ? 'green' : 'amber'} />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
                <ChartContainer title="Monthly Transaction Value">
                    <ResponsiveContainer width="100%" height={280}>
                        <LineChart data={data?.monthly_trend}>
                            <XAxis dataKey="month" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false}
                                tickFormatter={v => v?.slice(5, 7)} />
                            <YAxis tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false}
                                tickFormatter={v => `${(v / 1e6).toFixed(0)}M`} />
                            <Tooltip contentStyle={{ background: '#334155', border: '1px solid rgba(255,255,255,0.2)', borderRadius: 12, color: '#fff', boxShadow: '0 8px 32px rgba(0,0,0,0.5)' }} formatter={fmtTooltip} />
                            <Line type="monotone" dataKey="value" stroke="#6366f1" strokeWidth={2.5} dot={{ fill: '#6366f1', r: 3 }} />
                        </LineChart>
                    </ResponsiveContainer>
                </ChartContainer>

                <ChartContainer title="Top 10 States">
                    <ResponsiveContainer width="100%" height={280}>
                        <BarChart data={data?.top_states?.slice(0, 10)} layout="vertical">
                            <XAxis type="number" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false}
                                tickFormatter={v => `${(v / 1e6).toFixed(0)}M`} />
                            <YAxis type="category" dataKey="state" tick={{ fill: '#94a3b8', fontSize: 10 }} axisLine={false} tickLine={false} width={90} />
                            <Tooltip contentStyle={{ background: '#334155', border: '1px solid rgba(255,255,255,0.2)', borderRadius: 12, color: '#fff', boxShadow: '0 8px 32px rgba(0,0,0,0.5)' }} formatter={fmtTooltip} />
                            <Bar dataKey="value" fill="#6366f1" radius={[0, 6, 6, 0]} />
                        </BarChart>
                    </ResponsiveContainer>
                </ChartContainer>
            </div>

            {data?.categories?.length > 0 && (
                <ChartContainer title="Value by Category">
                    <ResponsiveContainer width="100%" height={280}>
                        <PieChart>
                            <Pie data={data.categories} dataKey="value" nameKey="category" cx="50%" cy="50%"
                                innerRadius={60} outerRadius={100} strokeWidth={0}>
                                {data.categories.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                            </Pie>
                            <Tooltip contentStyle={{ background: '#334155', border: '1px solid rgba(255,255,255,0.2)', borderRadius: 12, color: '#fff', boxShadow: '0 8px 32px rgba(0,0,0,0.5)', fontSize: 12 }}
                                formatter={fmtTooltip} />
                            <Legend wrapperStyle={{ color: '#94a3b8', fontSize: 11 }} />
                        </PieChart>
                    </ResponsiveContainer>
                </ChartContainer>
            )}
        </AnimatedPage>
    )
}
