import AnimatedPage from '../motion/AnimatedPage'
import { motion } from 'framer-motion'
import { staggerContainer, staggerItem } from '../motion/variants'

const SECTIONS = [
    {
        title: '🏗 Architecture',
        content: `This platform uses a decoupled architecture:\n\n**Backend (FastAPI):** 8 REST API endpoints wrapping 11 modular Python analysis engines.\n**Frontend (React + Vite):** Tailwind CSS + Framer Motion with Recharts visualizations.\n\n**Data Flow:** CSV → DataProfiler → Metadata + DataFrame → API → Frontend\n\n**Zero Hallucination:** All answers computed directly from data. No LLM. Rule-based NLP → Pandas execution.`,
    },
    {
        title: '🧠 AI Query Engine',
        content: `18+ intent types supported:\n\n• total, average, count, max, min (aggregation)\n• top_n, bottom_n (ranking)\n• trend, growth (time series)\n• compare (group vs group)\n• distribution, histogram (statistical)\n• anomaly (detection)\n• forecast, scenario (predictive)\n\nEach query is converted to a structured JSON plan, then executed against Pandas.`,
    },
    {
        title: '📊 Analysis Modules',
        content: `**11 Backend Modules:**\n\n1. data_profiler — Auto schema detection, role mapping\n2. query_planner — NL → structured JSON\n3. query_executor — JSON → Pandas execution\n4. insight_engine — 10 auto-insights with "Why?"\n5. anomaly_detector — IQR, Z-score, percentile, rolling, growth\n6. predictor — Linear trend + seasonal decomposition\n7. scenario_engine — 5 what-if simulations\n8. risk_analyzer — HHI concentration, volatility\n9. comparator — Side-by-side comparison\n10. data_quality — 5 quality checks, composite score\n11. utils — Formatting, matching, helpers`,
    },
    {
        title: '🎨 Design System',
        content: `**Dark Fintech Theme:**\n\n• Font: Inter (400–900)\n• Palette: Slate-950 base, Indigo-500 accent, Violet-500 secondary\n• Components: Glassmorphism cards, shimmer loading, gradient borders\n• Animations: Framer Motion stagger, spring, page transitions\n• Charts: Recharts with dark tooltip theme`,
    },
    {
        title: '📋 Sample Queries',
        content: `Try these in the Ask AI page:\n\n• "Total transaction value"\n• "Top 10 states by value"\n• "Compare Delhi vs Maharashtra"\n• "Month over month growth rate"\n• "What is the fraud rate?"\n• "Distribution by category"\n• "Forecast next 3 months"\n• "Show anomalies"`,
    },
]

export default function Docs() {
    return (
        <AnimatedPage>
            <h1 className="text-2xl font-extrabold text-white tracking-tight mb-1">📖 Documentation</h1>
            <p className="text-sm text-slate-500 mb-6">Architecture, methodology, and usage guide</p>

            <motion.div variants={staggerContainer} initial="hidden" animate="visible" className="space-y-4">
                {SECTIONS.map((s, i) => (
                    <motion.div key={i} variants={staggerItem} className="glass-sm p-5">
                        <h2 className="text-base font-bold text-white mb-3">{s.title}</h2>
                        <div className="text-sm text-slate-400 leading-relaxed whitespace-pre-line">{s.content}</div>
                    </motion.div>
                ))}
            </motion.div>
        </AnimatedPage>
    )
}
