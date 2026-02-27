import { useState, useCallback, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import AnimatedPage from '../motion/AnimatedPage'
import { staggerContainer, staggerItem } from '../motion/variants'
import { api } from '../lib/api'
import KpiCard, { formatCount } from '../components/KpiCard'
import { KpiSkeleton } from '../components/LoadingSkeleton'
import LoadingSkeleton from '../components/LoadingSkeleton'
import { Upload as UploadIcon, FileUp, RotateCcw, Download, Database, Table2, BarChart3, Columns3, AlertCircle, CheckCircle } from 'lucide-react'

export default function Upload() {
    const [profile, setProfile] = useState(null)
    const [preview, setPreview] = useState(null)
    const [uploading, setUploading] = useState(false)
    const [error, setError] = useState(null)
    const [dragOver, setDragOver] = useState(false)
    const [tab, setTab] = useState('profile')
    const inputRef = useRef(null)

    const handleUpload = useCallback(async (file) => {
        if (!file) return
        setUploading(true)
        setError(null)
        setProfile(null)
        setPreview(null)

        try {
            const result = await api.upload(file)
            setProfile(result)
            // Load preview
            const prev = await api.preview(50)
            setPreview(prev)
        } catch (e) {
            setError(e.message)
        } finally {
            setUploading(false)
        }
    }, [])

    const handleDrop = useCallback((e) => {
        e.preventDefault()
        setDragOver(false)
        const file = e.dataTransfer.files[0]
        if (file) handleUpload(file)
    }, [handleUpload])

    const handleReset = async () => {
        setUploading(true)
        setError(null)
        try {
            const res = await api.reset()
            setProfile(null)
            setPreview(null)
            // Reload profile from schema
            const schema = await api.schema()
            setProfile({
                ...res,
                ...schema,
                column_summary: Object.entries(schema.column_details || {}).map(([col, info]) => ({
                    Column: col, Type: info.dtype,
                    Missing: `${info.missing} (${info.missing_pct}%)`,
                    Unique: info.unique,
                })),
            })
            const prev = await api.preview(50)
            setPreview(prev)
        } catch (e) { setError(e.message) }
        setUploading(false)
    }

    const TABS = [
        { id: 'profile', label: 'Schema', icon: Columns3 },
        { id: 'preview', label: 'Data', icon: Table2 },
        { id: 'stats', label: 'Stats', icon: BarChart3 },
    ]

    return (
        <AnimatedPage>
            <h1 className="text-2xl font-extrabold text-white tracking-tight mb-1">📂 Upload Data</h1>
            <p className="text-sm text-slate-500 mb-6">Upload any CSV to instantly analyze it with the AI engine — all pages adapt automatically</p>

            {/* Upload Zone */}
            {!profile && !uploading && (
                <motion.div
                    initial={{ opacity: 0, y: 16 }}
                    animate={{ opacity: 1, y: 0 }}
                    className={`relative rounded-2xl border-2 border-dashed transition-all duration-300 text-center py-16 px-8 cursor-pointer
            ${dragOver ? 'border-indigo-400 bg-indigo-500/10 scale-[1.01]' : 'border-white/[0.1] bg-white/[0.02] hover:border-indigo-500/30 hover:bg-white/[0.04]'}`}
                    onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
                    onDragLeave={() => setDragOver(false)}
                    onDrop={handleDrop}
                    onClick={() => inputRef.current?.click()}
                >
                    <input ref={inputRef} type="file" accept=".csv,.tsv,.txt" className="hidden"
                        onChange={(e) => e.target.files[0] && handleUpload(e.target.files[0])} />

                    <motion.div animate={{ y: dragOver ? -4 : 0 }} transition={{ type: 'spring', stiffness: 300 }}>
                        <FileUp size={48} className={`mx-auto mb-4 ${dragOver ? 'text-indigo-400' : 'text-slate-600'}`} />
                        <h3 className="text-lg font-bold text-slate-200 mb-2">
                            {dragOver ? 'Drop it here!' : 'Drag & drop your CSV file'}
                        </h3>
                        <p className="text-sm text-slate-500 mb-4">or click to browse — supports CSV, TSV up to 50MB</p>
                        <div className="flex gap-3 justify-center text-xs text-slate-600">
                            <span className="px-3 py-1 rounded-full bg-white/[0.04] border border-white/[0.06]">Auto schema detection</span>
                            <span className="px-3 py-1 rounded-full bg-white/[0.04] border border-white/[0.06]">Multi-delimiter support</span>
                            <span className="px-3 py-1 rounded-full bg-white/[0.04] border border-white/[0.06]">Encoding detection</span>
                        </div>
                    </motion.div>
                </motion.div>
            )}

            {/* Loading */}
            {uploading && (
                <div className="text-center py-16">
                    <div className="w-12 h-12 mx-auto mb-4 border-3 border-indigo-500 border-t-transparent rounded-full animate-spin" />
                    <p className="text-sm text-slate-400 font-semibold">Processing dataset...</p>
                    <p className="text-xs text-slate-600 mt-1">Detecting schema, computing statistics, profiling columns</p>
                </div>
            )}

            {/* Error */}
            {error && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                    className="glass-sm p-4 border-l-[3px] border-rose-500/50 mb-4 flex items-center gap-3">
                    <AlertCircle size={18} className="text-rose-400 flex-shrink-0" />
                    <div>
                        <p className="text-sm font-semibold text-rose-300">Upload Failed</p>
                        <p className="text-xs text-slate-400">{error}</p>
                    </div>
                </motion.div>
            )}

            {/* Profile Results */}
            {profile && (
                <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
                    {/* Header with filename and actions */}
                    <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-3">
                            <div className="w-9 h-9 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
                                <CheckCircle size={18} className="text-emerald-400" />
                            </div>
                            <div>
                                <h3 className="text-sm font-bold text-white">{profile.filename || profile.source}</h3>
                                <p className="text-xs text-slate-500 font-mono">{profile.rows?.toLocaleString('en-IN')} rows × {profile.columns} columns • {profile.load_time_ms}ms</p>
                            </div>
                        </div>
                        <div className="flex gap-2">
                            <button onClick={() => inputRef.current?.click()} className="btn-ghost flex items-center gap-1.5 text-xs">
                                <UploadIcon size={14} /> Upload New
                            </button>
                            <button onClick={handleReset} className="btn-ghost flex items-center gap-1.5 text-xs">
                                <RotateCcw size={14} /> Reset Default
                            </button>
                            <a href={api.exportCSV()} download className="btn-ghost flex items-center gap-1.5 text-xs">
                                <Download size={14} /> Export
                            </a>
                            <input ref={inputRef} type="file" accept=".csv,.tsv,.txt" className="hidden"
                                onChange={(e) => e.target.files[0] && handleUpload(e.target.files[0])} />
                        </div>
                    </div>

                    {/* KPIs */}
                    <div className="grid grid-cols-2 lg:grid-cols-5 gap-3 mb-6">
                        <KpiCard label="Rows" rawValue={profile.rows} formatter={formatCount} accent="indigo" />
                        <KpiCard label="Columns" rawValue={profile.columns} formatter={v => Math.round(v).toString()} accent="violet" />
                        <KpiCard label="Numeric Cols" rawValue={profile.numeric_columns?.length || 0} formatter={v => Math.round(v).toString()} accent="teal" />
                        <KpiCard label="Categorical" rawValue={profile.categorical_columns?.length || 0} formatter={v => Math.round(v).toString()} accent="amber" />
                        <KpiCard label="Duplicates" rawValue={profile.duplicate_rows || 0} formatter={v => Math.round(v).toString()} accent={profile.duplicate_rows > 0 ? 'red' : 'green'} />
                    </div>

                    {/* Detected Roles */}
                    {profile.roles && Object.keys(profile.roles).length > 0 && (
                        <div className="glass-sm p-4 mb-6">
                            <p className="text-[0.65rem] font-bold uppercase tracking-[0.1em] text-slate-500 mb-2">🎯 Auto-Detected Roles</p>
                            <div className="flex flex-wrap gap-2">
                                {Object.entries(profile.roles).map(([role, col]) => (
                                    <span key={role} className="px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-xs">
                                        <span className="text-indigo-400 font-semibold">{role}:</span>{' '}
                                        <span className="text-slate-300 font-mono">{col}</span>
                                    </span>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Tabs */}
                    <div className="flex gap-1 mb-4 bg-white/[0.03] rounded-lg p-1 w-fit">
                        {TABS.map(({ id, label, icon: Icon }) => (
                            <button key={id} onClick={() => setTab(id)}
                                className={`flex items-center gap-1.5 px-4 py-2 rounded-md text-xs font-semibold transition-all duration-200
                  ${tab === id ? 'bg-indigo-500/15 text-indigo-400' : 'text-slate-500 hover:text-slate-300'}`}>
                                <Icon size={14} /> {label}
                            </button>
                        ))}
                    </div>

                    {/* Tab Content */}
                    <AnimatePresence mode="wait">
                        {tab === 'profile' && (
                            <motion.div key="profile" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                                {profile.column_summary?.length > 0 && (
                                    <div className="glass-sm overflow-hidden">
                                        <table className="w-full text-sm">
                                            <thead>
                                                <tr className="border-b border-white/[0.06]">
                                                    <th className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wider text-slate-500">Column</th>
                                                    <th className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wider text-slate-500">Type</th>
                                                    <th className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wider text-slate-500">Missing</th>
                                                    <th className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wider text-slate-500">Unique</th>
                                                    <th className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wider text-slate-500">Sample</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {profile.column_summary.map((row, i) => (
                                                    <tr key={i} className="border-b border-white/[0.03] hover:bg-white/[0.02] transition-colors">
                                                        <td className="px-4 py-2.5 text-indigo-400 font-mono font-semibold text-xs">{row.Column}</td>
                                                        <td className="px-4 py-2.5">
                                                            <span className={`badge text-[0.55rem] ${row.Type?.includes('int') || row.Type?.includes('float') ? 'bg-teal-500/10 text-teal-400' :
                                                                    row.Type?.includes('datetime') ? 'bg-amber-500/10 text-amber-400' :
                                                                        'bg-violet-500/10 text-violet-400'
                                                                }`}>{row.Type}</span>
                                                        </td>
                                                        <td className="px-4 py-2.5 text-slate-400 font-mono text-xs">{row.Missing}</td>
                                                        <td className="px-4 py-2.5 text-slate-400 font-mono text-xs">{row.Unique}</td>
                                                        <td className="px-4 py-2.5 text-slate-500 text-xs max-w-[200px] truncate">{row.Sample}</td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                )}
                            </motion.div>
                        )}

                        {tab === 'preview' && preview && (
                            <motion.div key="preview" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                                <div className="glass-sm overflow-hidden">
                                    <div className="overflow-x-auto">
                                        <table className="w-full text-xs">
                                            <thead>
                                                <tr className="border-b border-white/[0.06]">
                                                    <th className="px-3 py-2 text-left text-[0.6rem] font-bold uppercase tracking-wider text-slate-600">#</th>
                                                    {preview.columns.map(c => (
                                                        <th key={c} className="px-3 py-2 text-left text-[0.6rem] font-bold uppercase tracking-wider text-slate-500 whitespace-nowrap">{c}</th>
                                                    ))}
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {preview.rows.slice(0, 30).map((row, i) => (
                                                    <tr key={i} className="border-b border-white/[0.03] hover:bg-white/[0.02] transition-colors">
                                                        <td className="px-3 py-1.5 text-slate-600 font-mono">{i + 1}</td>
                                                        {preview.columns.map(c => (
                                                            <td key={c} className="px-3 py-1.5 text-slate-400 font-mono whitespace-nowrap max-w-[160px] truncate">
                                                                {typeof row[c] === 'number' ? row[c].toLocaleString('en-IN') : String(row[c] ?? '').slice(0, 50)}
                                                            </td>
                                                        ))}
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                    <div className="px-4 py-2 border-t border-white/[0.06] text-xs text-slate-600">
                                        Showing {Math.min(30, preview.rows.length)} of {preview.total_rows?.toLocaleString('en-IN')} rows
                                    </div>
                                </div>
                            </motion.div>
                        )}

                        {tab === 'stats' && profile.correlation_matrix && (
                            <motion.div key="stats" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                                <div className="glass-sm p-5">
                                    <h3 className="text-sm font-semibold text-slate-300 mb-3">Correlation Matrix (Numeric Columns)</h3>
                                    <div className="overflow-x-auto">
                                        <table className="text-xs">
                                            <thead>
                                                <tr>
                                                    <th className="px-3 py-2 text-slate-500"></th>
                                                    {Object.keys(profile.correlation_matrix).map(c => (
                                                        <th key={c} className="px-3 py-2 text-slate-500 font-mono whitespace-nowrap">{c.slice(0, 12)}</th>
                                                    ))}
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {Object.entries(profile.correlation_matrix).map(([row, vals]) => (
                                                    <tr key={row}>
                                                        <td className="px-3 py-1.5 text-slate-500 font-mono text-[0.65rem] whitespace-nowrap">{row.slice(0, 12)}</td>
                                                        {Object.values(vals).map((v, i) => {
                                                            const abs = Math.abs(v)
                                                            const bg = abs > 0.7 ? 'bg-indigo-500/30' : abs > 0.4 ? 'bg-indigo-500/15' : abs > 0.2 ? 'bg-white/[0.03]' : ''
                                                            return <td key={i} className={`px-3 py-1.5 text-center font-mono ${bg} ${abs > 0.7 ? 'text-indigo-300 font-bold' : 'text-slate-500'}`}>{v?.toFixed(2)}</td>
                                                        })}
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </motion.div>
            )}
        </AnimatedPage>
    )
}
