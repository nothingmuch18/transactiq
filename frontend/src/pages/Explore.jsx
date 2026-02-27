import AnimatedPage from '../motion/AnimatedPage'
import { Search } from 'lucide-react'

export default function Explore() {
    return (
        <AnimatedPage>
            <h1 className="text-2xl font-extrabold text-white tracking-tight mb-1">🔍 Explore Data</h1>
            <p className="text-sm text-slate-500 mb-6">Use the Ask AI page to run complex queries — this works as a quick data browser</p>

            <div className="glass p-6 text-center">
                <Search size={40} className="mx-auto text-slate-600 mb-4" />
                <h3 className="text-lg font-bold text-slate-300 mb-2">Interactive Data Explorer</h3>
                <p className="text-sm text-slate-500 max-w-md mx-auto mb-4">
                    Navigate to <span className="text-indigo-400 font-semibold">Ask AI</span> to run natural language queries like:
                </p>
                <div className="flex flex-wrap gap-2 justify-center">
                    {['Top 10 states by value', 'Average amount by category', 'Monthly transaction volume', 'Show transactions above 5000'].map(q => (
                        <span key={q} className="text-xs px-3 py-1.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                            {q}
                        </span>
                    ))}
                </div>
            </div>
        </AnimatedPage>
    )
}
