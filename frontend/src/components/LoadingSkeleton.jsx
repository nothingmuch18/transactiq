export default function LoadingSkeleton({ rows = 4, className = '' }) {
    return (
        <div className={`space-y-3 ${className}`}>
            {Array.from({ length: rows }).map((_, i) => (
                <div key={i} className="shimmer h-12 rounded-xl" style={{ animationDelay: `${i * 0.1}s` }} />
            ))}
        </div>
    )
}

export function KpiSkeleton({ count = 4 }) {
    return (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {Array.from({ length: count }).map((_, i) => (
                <div key={i} className="shimmer h-24 rounded-2xl" style={{ animationDelay: `${i * 0.08}s` }} />
            ))}
        </div>
    )
}
