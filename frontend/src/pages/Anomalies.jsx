import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import AnimatedPage from '../motion/AnimatedPage'
import { api } from '../lib/api'
import KpiCard from '../components/KpiCard'
import { KpiSkeleton } from '../components/LoadingSkeleton'
import LoadingSkeleton from '../components/LoadingSkeleton'
import { staggerContainer, staggerItem } from '../motion/variants'

export default function Anomalies() {
    const [data, setData] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    useEffect(() => {
        let cancelled = false
        api.anomalies({ method: 'all' })
            .then(d => { if (!cancelled) setData(d) })
            .catch(e => { if (!cancelled) setError(e.message) })
            .finally(() => { if (!cancelled) setLoading(false) })
        return () => { cancelled = true }
    }, [])

    if (loading) return <AnimatedPage><KpiSkeleton count={3} /><LoadingSkeleton rows={5} className="mt-4" /></AnimatedPage>
    if (error) return <AnimatedPage><div className="glass p-6 text-center"><p className="text-slate-400">{error}</p></div></AnimatedPage>

    return (
        <AnimatedPage>
            <h1 className="text-2xl font-extrabold text-white tracking-tight mb-1">⚠️ Anomaly Detection</h1>
            <p className="text-sm text-slate-500 mb-6">Multi-method statistical anomaly detection across your dataset</p>

            <div className="grid grid-cols-2 lg:grid-cols-3 gap-3 mb-6">
                <KpiCard label="Total Anomalies" rawValue={data?.total_anomalies || 0} formatter={v => v.toLocaleString('en-IN')} accent="red" />
                <KpiCard label="Anomaly Rate" rawValue={data?.anomaly_rate || 0} formatter={v => `${v.toFixed(2)}%`} accent="amber" />
                <KpiCard label="Methods Used" rawValue={data?.methods_used || 0} formatter={v => Math.round(v).toString()} accent="indigo" />
            </div>

            <motion.div variants={staggerContainer} initial="hidden" animate="visible" className="space-y-4">
                {data?.results && Object.entries(data.results).map(([method, info]) => (
                    <motion.div key={method} variants={staggerItem} className="glass-sm p-5 border-l-[3px] border-amber-500/30">
                        <div className="flex items-center justify-between mb-2">
                            <h3 className="text-sm font-bold text-slate-200">{method}</h3>
                            <span className={`badge ${info.count > 0 ? 'bg-rose-500/10 text-rose-400' : 'bg-emerald-500/10 text-emerald-400'}`}>
                                {info.count} found
                            </span>
                        </div>
                        <p className="text-xs text-slate-500">{info.description}</p>

                        {info.anomalies?.length > 0 && (
                            <div className="mt-3 overflow-x-auto">
                                <table className="w-full text-xs">
                                    <thead>
                                        <tr className="border-b border-white/[0.06]">
                                            {Object.keys(info.anomalies[0]).slice(0, 5).map(k => (
                                                <th key={k} className="px-3 py-2 text-left text-[0.6rem] font-bold uppercase tracking-wider text-slate-500">{k}</th>
                                            ))}
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {info.anomalies.slice(0, 5).map((row, i) => (
                                            <tr key={i} className="border-b border-white/[0.03] hover:bg-white/[0.02] transition-colors">
                                                {Object.keys(row).slice(0, 5).map(k => (
                                                    <td key={k} className="px-3 py-2 text-slate-400 font-mono">{typeof row[k] === 'number' ? row[k].toLocaleString('en-IN') : String(row[k]).slice(0, 40)}</td>
                                                ))}
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                                {info.anomalies.length > 5 && <p className="text-xs text-slate-600 mt-2">+ {info.anomalies.length - 5} more...</p>}
                            </div>
                        )}
                    </motion.div>
                ))}
            </motion.div>
        </AnimatedPage>
    )
}
