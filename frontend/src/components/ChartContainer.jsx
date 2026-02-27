import { motion } from 'framer-motion'

export default function ChartContainer({ title, children, className = '' }) {
    return (
        <motion.div
            className={`chart-container ${className}`}
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
        >
            {title && (
                <h3 className="text-sm font-semibold text-slate-300 mb-4 tracking-tight">{title}</h3>
            )}
            {children}
        </motion.div>
    )
}
