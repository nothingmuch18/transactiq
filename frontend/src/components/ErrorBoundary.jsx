import React from 'react'

export class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props)
        this.state = { hasError: false, error: null }
    }

    static getDerivedStateFromError(error) {
        return { hasError: true, error }
    }

    componentDidCatch(error, errorInfo) {
        console.error('ErrorBoundary caught:', error, errorInfo)
    }

    render() {
        if (this.state.hasError) {
            return (
                this.props.fallback || (
                    <div className="glass p-8 text-center m-8">
                        <div className="text-4xl mb-4">⚠️</div>
                        <h2 className="text-lg font-bold text-white mb-2">Something went wrong</h2>
                        <p className="text-sm text-slate-400 mb-4">{this.state.error?.message || 'An unexpected error occurred'}</p>
                        <button
                            className="btn-primary"
                            onClick={() => { this.setState({ hasError: false, error: null }) }}
                        >
                            Try Again
                        </button>
                    </div>
                )
            )
        }
        return this.props.children
    }
}
