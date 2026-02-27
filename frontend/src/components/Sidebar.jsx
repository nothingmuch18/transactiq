import { NavLink, useLocation } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
    LayoutDashboard, Brain, Search, Lightbulb, TrendingUp,
    AlertTriangle, GitCompare, ShieldCheck, FileText, Upload,
} from 'lucide-react'

const NAV = [
    { path: '/', icon: LayoutDashboard, label: 'Home' },
    { path: '/overview', icon: TrendingUp, label: 'Overview' },
    { path: '/ask', icon: Brain, label: 'Ask AI' },
    { path: '/explore', icon: Search, label: 'Explore' },
    { path: '/insights', icon: Lightbulb, label: 'Insights' },
    { path: '/risk', icon: TrendingUp, label: 'Risk' },
    { path: '/anomalies', icon: AlertTriangle, label: 'Anomalies' },
    { path: '/compare', icon: GitCompare, label: 'Compare' },
    { path: '/quality', icon: ShieldCheck, label: 'Quality' },
    { path: '/upload', icon: Upload, label: 'Upload Data' },
    { path: '/docs', icon: FileText, label: 'Docs' },
]

export default function Sidebar() {
    const location = useLocation()

    return (
        <aside className="fixed left-0 top-0 h-screen w-56 bg-slate-950 border-r border-white/[0.06] flex flex-col z-50">
            {/* Brand */}
            <div className="px-5 py-5 border-b border-white/[0.06]">
                <div className="flex items-center gap-2.5">
                    <div className="w-9 h-9 flex-shrink-0">
                        <svg viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-full h-full">
                            <path d="M20 2L5 10v12c0 9.3 6.4 18 15 20 8.6-2 15-10.7 15-20V10L20 2z" fill="url(#shield)" stroke="#94a3b8" strokeWidth="1.2" />
                            <rect x="13" y="22" width="4" height="10" rx="1" fill="#14b8a6" />
                            <rect x="18" y="18" width="4" height="14" rx="1" fill="#14b8a6" />
                            <rect x="23" y="14" width="4" height="18" rx="1" fill="#14b8a6" />
                            <path d="M14 20l6-6 6-2" stroke="#14b8a6" strokeWidth="2" strokeLinecap="round" fill="none" />
                            <circle cx="26" cy="12" r="2" fill="#14b8a6" />
                            <defs><linearGradient id="shield" x1="5" y1="2" x2="35" y2="34"><stop stopColor="#1e293b" /><stop offset="1" stopColor="#0f172a" /></linearGradient></defs>
                        </svg>
                    </div>
                    <div>
                        <div className="text-sm font-bold text-white tracking-tight">TransactIQ</div>
                        <div className="text-[0.6rem] font-semibold text-slate-500 uppercase tracking-[0.1em]">AI Engine</div>
                    </div>
                </div>
            </div>

            {/* Nav */}
            <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
                {NAV.map(({ path, icon: Icon, label }) => {
                    const active = location.pathname === path
                    return (
                        <NavLink key={path} to={path}>
                            <motion.div
                                className={`flex items-center gap-3 px-3 py-2 rounded-lg text-[0.82rem] font-medium transition-all duration-200
                  ${active
                                        ? 'bg-indigo-500/10 text-indigo-400 shadow-sm shadow-indigo-500/5'
                                        : 'text-slate-400 hover:text-slate-200 hover:bg-white/[0.04]'
                                    }`}
                                whileHover={{ x: 2 }}
                                whileTap={{ scale: 0.98 }}
                            >
                                <Icon size={16} className={active ? 'text-indigo-400' : 'text-slate-500'} />
                                {label}
                                {active && (
                                    <motion.div
                                        layoutId="activeIndicator"
                                        className="ml-auto w-1.5 h-1.5 rounded-full bg-indigo-400"
                                        transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                                    />
                                )}
                            </motion.div>
                        </NavLink>
                    )
                })}
            </nav>

            <div className="px-5 py-4 border-t border-white/[0.06]">
                <div className="text-[0.6rem] text-slate-600 leading-relaxed">
                    Zero Hallucination Engine<br />
                    Made by <span className="text-indigo-400 font-semibold">Ryan</span>
                </div>
            </div>
        </aside>
    )
}
