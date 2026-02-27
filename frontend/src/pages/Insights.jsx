import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import AnimatedPage from '../motion/AnimatedPage'
import { staggerContainer, staggerItem } from '../motion/variants'
import { api } from '../lib/api'
import LoadingSkeleton from '../components/LoadingSkeleton'
import { ChevronDown } from 'lucide-react'

const CATEGORY_COLORS = {
    overview: '#6366f1', growth: '#10b981', timing: '#f59e0b', concentration: '#8b5cf6',
    category: '#ec4899', distribution: '#14b8a6', risk: '#ef4444', fraud: '#dc2626', pattern: '#3b82f6',
}

export default function Insights() {
    const [data, setData] = useState(null)
    const [loading, setLoading] = useState(true)
    const [expanded, setExpanded] = useState({})

    useEffect(() => {
        api.insights().then(setData).catch(console.error).finally(() => setLoading(false))
    }, [])

    if (loading) return <AnimatedPage><LoadingSkeleton rows={8} /></AnimatedPage>

    return (
        <AnimatedPage>
            <h1 className="text-2xl font-extrabold text-white tracking-tight mb-1">💡 Financial Insights</h1>
            <p className="text-sm text-slate-500 mb-6">Auto-generated intelligence — each insight includes a "Why?" explanation</p>

            <motion.div variants={staggerContainer} initial="hidden" animate="visible" className="space-y-3">
                {data?.insights?.map((ins, i) => {
                    const color = CATEGORY_COLORS[ins.category] || '#6366f1'
                    return (
                        <motion.div key={i} variants={staggerItem}>
                            <div className="insight-card" style={{ borderLeftColor: color }}>
                                <div className="flex items-center justify-between mb-1">
                                    <span className="text-sm font-bold text-slate-200">
                                        {ins.icon} {ins.title}
                                    </span>
                                    <span className="badge text-[0.55rem]" style={{ background: `${color}15`, color }}>
                                        {ins.category}
                                    </span>
                                </div>
                                <p className="text-[0.82rem] text-slate-400 leading-relaxed">{ins.description}</p>

                                {ins.why && (
                                    <>
                                        <button onClick={() => setExpanded(p => ({ ...p, [i]: !p[i] }))}
                                            className="flex items-center gap-1 text-xs text-indigo-400 mt-2 hover:text-indigo-300 transition-colors font-semibold">
                                            <ChevronDown size={14} className={`transition-transform ${expanded[i] ? 'rotate-180' : ''}`} />
                                            Why?
                                        </button>
                                        {expanded[i] && (
                                            <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }}
                                                className="mt-2 text-xs text-slate-500 bg-white/[0.02] rounded-lg p-3 leading-relaxed">
                                                {ins.why}
                                            </motion.div>
                                        )}
                                    </>
                                )}
                            </div>
                        </motion.div>
                    )
                })}
            </motion.div>

            <p className="text-xs text-slate-600 mt-6 text-center">{data?.count} insights generated</p>
        </AnimatedPage>
    )
}
