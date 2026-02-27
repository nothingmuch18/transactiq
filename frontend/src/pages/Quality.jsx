import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import AnimatedPage from '../motion/AnimatedPage'
import { api } from '../lib/api'
import KpiCard from '../components/KpiCard'
import { KpiSkeleton } from '../components/LoadingSkeleton'
import LoadingSkeleton from '../components/LoadingSkeleton'
import { staggerContainer, staggerItem } from '../motion/variants'
import { CheckCircle, XCircle } from 'lucide-react'

export default function Quality() {
    const [data, setData] = useState(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        let cancelled = false
        api.quality()
            .then(d => { if (!cancelled) setData(d) })
            .catch(console.error)
            .finally(() => { if (!cancelled) setLoading(false) })
        return () => { cancelled = true }
    }, [])

    if (loading) return <AnimatedPage><KpiSkeleton count={4} /><LoadingSkeleton rows={4} className="mt-4" /></AnimatedPage>

    const checks = [
        { name: 'Missing Values', data: data?.missing_values, ok: data?.missing_values?.total === 0 },
        { name: 'Duplicates', data: { count: data?.duplicates }, ok: data?.duplicates === 0 },
        { name: 'Negative Values', data: data?.negative_values, ok: !data?.negative_values?.found },
        { name: 'Extreme Outliers', data: data?.extreme_outliers, ok: !data?.extreme_outliers?.found },
        { name: 'Consistency', data: data?.consistency, ok: !data?.consistency?.found },
    ]

    return (
        <AnimatedPage>
            <h1 className="text-2xl font-extrabold text-white tracking-tight mb-1">🛡 Data Quality</h1>
            <p className="text-sm text-slate-500 mb-6">Comprehensive data quality assessment with a composite score</p>

            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
                <KpiCard label="Quality Score" rawValue={data?.quality_score || 0} formatter={v => `${v.toFixed(0)}/100`} accent={data?.quality_score >= 90 ? 'green' : data?.quality_score >= 75 ? 'amber' : 'red'} />
                <KpiCard label="Grade" value={data?.quality_grade?.split(' — ')[0] || 'N/A'} accent="indigo" />
                <KpiCard label="Records" rawValue={data?.total_records || 0} formatter={v => v.toLocaleString('en-IN')} accent="violet" />
                <KpiCard label="Columns" rawValue={data?.total_columns || 0} formatter={v => Math.round(v).toString()} accent="teal" />
            </div>

            <motion.div variants={staggerContainer} initial="hidden" animate="visible" className="space-y-3">
                {checks.map((check, i) => (
                    <motion.div key={i} variants={staggerItem}
                        className={`glass-sm p-4 border-l-[3px] ${check.ok ? 'border-emerald-500/30' : 'border-amber-500/30'}`}>
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                                {check.ok ? <CheckCircle size={16} className="text-emerald-400" /> : <XCircle size={16} className="text-amber-400" />}
                                <h3 className="text-sm font-bold text-slate-200">{check.name}</h3>
                            </div>
                            <span className={`badge ${check.ok ? 'bg-emerald-500/10 text-emerald-400' : 'bg-amber-500/10 text-amber-400'}`}>
                                {check.ok ? 'Pass' : 'Issues Found'}
                            </span>
                        </div>
                        {check.data?.table?.length > 0 && (
                            <div className="mt-3 overflow-x-auto">
                                <table className="w-full text-xs">
                                    <thead><tr className="border-b border-white/[0.06]">
                                        {Object.keys(check.data.table[0]).map(k => <th key={k} className="px-3 py-1.5 text-left text-[0.6rem] font-bold uppercase text-slate-500">{k}</th>)}
                                    </tr></thead>
                                    <tbody>
                                        {check.data.table.slice(0, 5).map((row, j) => (
                                            <tr key={j} className="border-b border-white/[0.03]">
                                                {Object.values(row).map((v, vi) => <td key={vi} className="px-3 py-1.5 text-slate-400 font-mono">{String(v).slice(0, 40)}</td>)}
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </motion.div>
                ))}
            </motion.div>
        </AnimatedPage>
    )
}
