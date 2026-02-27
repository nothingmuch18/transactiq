import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AnimatePresence } from 'framer-motion'
import { lazy, Suspense } from 'react'
import Sidebar from './components/Sidebar'
import { ErrorBoundary } from './components/ErrorBoundary'
import { KpiSkeleton } from './components/LoadingSkeleton'

// Lazy-loaded pages for code splitting
const Home = lazy(() => import('./pages/Home'))
const Overview = lazy(() => import('./pages/Overview'))
const AskAI = lazy(() => import('./pages/AskAI'))
const Explore = lazy(() => import('./pages/Explore'))
const Insights = lazy(() => import('./pages/Insights'))
const Risk = lazy(() => import('./pages/Risk'))
const Anomalies = lazy(() => import('./pages/Anomalies'))
const Compare = lazy(() => import('./pages/Compare'))
const Quality = lazy(() => import('./pages/Quality'))
const UploadPage = lazy(() => import('./pages/Upload'))
const Docs = lazy(() => import('./pages/Docs'))

function PageLoader() {
    return (
        <div className="space-y-4 animate-fade-in">
            <div className="shimmer h-32 rounded-2xl" />
            <KpiSkeleton count={4} />
            <div className="shimmer h-64 rounded-2xl" />
        </div>
    )
}

export default function App() {
    return (
        <BrowserRouter>
            <div className="flex min-h-screen bg-slate-950">
                <Sidebar />
                <main className="ml-56 flex-1 p-6 lg:p-8">
                    <ErrorBoundary>
                        <Suspense fallback={<PageLoader />}>
                            <AnimatePresence mode="wait">
                                <Routes>
                                    <Route path="/" element={<Home />} />
                                    <Route path="/overview" element={<Overview />} />
                                    <Route path="/ask" element={<AskAI />} />
                                    <Route path="/explore" element={<Explore />} />
                                    <Route path="/insights" element={<Insights />} />
                                    <Route path="/risk" element={<Risk />} />
                                    <Route path="/anomalies" element={<Anomalies />} />
                                    <Route path="/compare" element={<Compare />} />
                                    <Route path="/quality" element={<Quality />} />
                                    <Route path="/upload" element={<UploadPage />} />
                                    <Route path="/docs" element={<Docs />} />
                                </Routes>
                            </AnimatePresence>
                        </Suspense>
                    </ErrorBoundary>
                </main>
            </div>
        </BrowserRouter>
    )
}
