import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import AnimatedPage from '../motion/AnimatedPage'
import { staggerContainer, staggerItem } from '../motion/variants'
import { api } from '../lib/api'
import KpiCard, { formatINR, formatCount } from '../components/KpiCard'
import { KpiSkeleton } from '../components/LoadingSkeleton'
import {
    LayoutDashboard, Brain, Search, Lightbulb, TrendingUp,
    AlertTriangle, GitCompare, ShieldCheck, FileText, Upload,
} from 'lucide-react'

const NAV_CARDS = [
    { path: '/overview', icon: LayoutDashboard, label: 'Executive Overview', desc: 'KPIs & trends', color: 'from-indigo-500/20 to-indigo-600/10' },
    { path: '/ask', icon: Brain, label: 'Ask AI', desc: 'Natural language queries', color: 'from-violet-500/20 to-violet-600/10' },
    { path: '/explore', icon: Search, label: 'Explore Data', desc: 'Filter & aggregate', color: 'from-cyan-500/20 to-cyan-600/10' },
    { path: '/insights', icon: Lightbulb, label: 'Insights', desc: 'Auto intelligence', color: 'from-amber-500/20 to-amber-600/10' },
    { path: '/risk', icon: TrendingUp, label: 'Risk Analysis', desc: 'Concentration & HHI', color: 'from-rose-500/20 to-rose-600/10' },
    { path: '/anomalies', icon: AlertTriangle, label: 'Anomalies', desc: 'Multi-method detection', color: 'from-orange-500/20 to-orange-600/10' },
    { path: '/compare', icon: GitCompare, label: 'Compare', desc: 'Side-by-side analysis', color: 'from-pink-500/20 to-pink-600/10' },
    { path: '/quality', icon: ShieldCheck, label: 'Data Quality', desc: 'Quality assessment', color: 'from-emerald-500/20 to-emerald-600/10' },
    { path: '/upload', icon: Upload, label: 'Upload Data', desc: 'Analyze any CSV', color: 'from-purple-500/20 to-purple-600/10' },
    { path: '/docs', icon: FileText, label: 'Documentation', desc: 'Architecture & docs', color: 'from-slate-500/20 to-slate-600/10' },
]

export default function Home() {
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

    const kpis = data?.kpis || {}

    return (
        <AnimatedPage>
            {/* Hero Banner */}
            <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-900 via-indigo-950/50 to-slate-900 p-8 lg:p-10 mb-8 border border-white/[0.06] glow-indigo">
                <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_rgba(99,102,241,0.12)_0%,_transparent_60%)]" />
                <div className="relative z-10">
                    <h1 className="text-3xl lg:text-4xl font-black tracking-tight text-white mb-2">
                        🧠 TransactIQ
                    </h1>
                    <p className="text-slate-400 text-base font-medium max-w-xl">
                        AI-powered analytics engine — ask anything about your transaction data
                    </p>
                    {data && (
                        <div className="mt-3 flex gap-4 text-xs font-mono text-slate-500">
                            <span>⚡ Loaded in {data.load_time_ms}ms</span>
                            <span>📊 {kpis.total_transactions?.toLocaleString('en-IN')} records</span>
                            <span>📅 {data.date_range?.months} months</span>
                        </div>
                    )}
                </div>
            </div>

            {/* KPIs — using rawValue for animated counting */}
            {loading ? <KpiSkeleton /> : (
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                    <KpiCard label="Total Transactions" rawValue={kpis.total_transactions} formatter={formatCount} accent="indigo" />
                    <KpiCard label="Total Value" rawValue={kpis.total_value} formatter={formatINR} accent="violet" />
                    <KpiCard label="Avg Transaction" rawValue={kpis.avg_transaction} formatter={formatINR} accent="teal" />
                    <KpiCard label="Risk Index" rawValue={kpis.risk_index} formatter={v => `${v.toFixed(1)}/100`} accent={kpis.risk_index < 30 ? 'green' : kpis.risk_index < 60 ? 'amber' : 'red'} />
                </div>
            )}

            {/* Navigation Grid */}
            <p className="section-label">Quick Navigation</p>
            <motion.div
                className="grid grid-cols-2 lg:grid-cols-5 gap-3"
                variants={staggerContainer}
                initial="hidden"
                animate="visible"
            >
                {NAV_CARDS.map(({ path, icon: Icon, label, desc, color }) => (
                    <motion.div key={path} variants={staggerItem}>
                        <Link to={path}>
                            <div className={`glass-sm p-4 text-center bg-gradient-to-br ${color} transition-all duration-300 hover:-translate-y-1 hover:shadow-lg hover:shadow-indigo-500/5 group cursor-pointer`}>
                                <Icon className="mx-auto mb-2 text-slate-400 group-hover:text-indigo-400 transition-colors" size={22} />
                                <div className="text-xs font-bold text-slate-200">{label}</div>
                                <div className="text-[0.6rem] text-slate-500 mt-0.5">{desc}</div>
                            </div>
                        </Link>
                    </motion.div>
                ))}
            </motion.div>
        </AnimatedPage>
    )
}
