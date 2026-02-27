import { motion, useInView } from 'framer-motion'
import { useRef, useEffect, useState, useMemo } from 'react'

/** Format number for Indian numbering system */
export function formatINR(value) {
    if (value == null || isNaN(value)) return 'N/A'
    const abs = Math.abs(value)
    if (abs >= 1e7) return `₹${(value / 1e7).toFixed(2)} Cr`
    if (abs >= 1e5) return `₹${(value / 1e5).toFixed(2)} L`
    if (abs >= 1e3) return `₹${(value / 1e3).toFixed(1)}K`
    return `₹${value.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`
}

export function formatCount(value) {
    if (value == null || isNaN(value)) return 'N/A'
    const abs = Math.abs(value)
    if (abs >= 1e7) return `${(value / 1e7).toFixed(2)} Cr`
    if (abs >= 1e5) return `${(value / 1e5).toFixed(2)} L`
    if (abs >= 1e3) return `${(value / 1e3).toFixed(1)}K`
    return value.toLocaleString('en-IN')
}

/** Animated counter that counts up from 0 to target */
function AnimatedCounter({ target, formatter, duration = 1.2 }) {
    const [display, setDisplay] = useState('0')
    const ref = useRef(null)
    const inView = useInView(ref, { once: true })

    useEffect(() => {
        if (!inView || target == null) return
        const num = typeof target === 'number' ? target : parseFloat(target)
        if (isNaN(num)) { setDisplay(String(target)); return }

        const frames = Math.round(duration * 60)
        let frame = 0
        const timer = setInterval(() => {
            frame++
            const progress = frame / frames
            // Ease out cubic
            const eased = 1 - Math.pow(1 - progress, 3)
            const current = num * eased
            setDisplay(formatter ? formatter(current) : formatDefault(current, num))
            if (frame >= frames) {
                setDisplay(formatter ? formatter(num) : formatDefault(num, num))
                clearInterval(timer)
            }
        }, 1000 / 60)
        return () => clearInterval(timer)
    }, [inView, target, formatter, duration])

    return <span ref={ref}>{display}</span>
}

function formatDefault(current, target) {
    if (Math.abs(target) >= 1e6) return `${(current / 1e6).toFixed(1)}M`
    if (Math.abs(target) >= 1e3) return current.toLocaleString('en-IN', { maximumFractionDigits: 0 })
    if (Number.isInteger(target)) return Math.round(current).toLocaleString('en-IN')
    return current.toFixed(2)
}

export default function KpiCard({ label, value, rawValue, formatter, icon, accent = 'indigo', trend, className = '' }) {
    const colors = {
        indigo: 'from-indigo-500/10 to-indigo-500/5 text-indigo-400 border-indigo-500/20',
        green: 'from-emerald-500/10 to-emerald-500/5 text-emerald-400 border-emerald-500/20',
        amber: 'from-amber-500/10 to-amber-500/5 text-amber-400 border-amber-500/20',
        red: 'from-rose-500/10 to-rose-500/5 text-rose-400 border-rose-500/20',
        teal: 'from-teal-500/10 to-teal-500/5 text-teal-400 border-teal-500/20',
        violet: 'from-violet-500/10 to-violet-500/5 text-violet-400 border-violet-500/20',
    }

    // If rawValue is provided, use animated counter. Otherwise show static value.
    const useAnimation = rawValue != null && typeof rawValue === 'number'

    return (
        <motion.div
            className={`kpi-card bg-gradient-to-br ${colors[accent] || colors.indigo} ${className}`}
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
            whileHover={{ scale: 1.01 }}
        >
            <div className="flex items-center justify-between mb-2">
                <span className="text-[0.65rem] font-bold uppercase tracking-[0.1em] text-slate-500">{label}</span>
                {icon && <span className="text-slate-600">{icon}</span>}
            </div>
            <div className="text-2xl font-extrabold text-white tracking-tight">
                {useAnimation ? <AnimatedCounter target={rawValue} formatter={formatter} /> : (value ?? 'N/A')}
            </div>
            {trend != null && (
                <div className={`text-xs font-semibold mt-1 ${parseFloat(trend) >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                    {parseFloat(trend) >= 0 ? '↗' : '↘'} {trend}
                </div>
            )}
        </motion.div>
    )
}
