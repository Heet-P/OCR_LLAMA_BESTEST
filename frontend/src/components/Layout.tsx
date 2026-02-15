import { FileText } from 'lucide-react';

interface LayoutProps {
    children: React.ReactNode;
    onNavigate?: (view: 'home' | 'history') => void;
    currentView?: 'home' | 'history';
}

export function Layout({ children, onNavigate, currentView = 'home' }: LayoutProps) {
    return (
        <div className="min-h-screen flex flex-col font-sans overflow-x-hidden relative">
            {/* Background Pattern */}
            <div className="fixed inset-0 z-0 bg-dot-grid opacity-[0.4] pointer-events-none"></div>

            {/* Top Navigation */}
            <nav className="relative z-50 w-full glass-panel border-b border-slate-200/60 sticky top-0">
                <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
                    <div
                        className="flex items-center gap-3 cursor-pointer group"
                        onClick={() => onNavigate?.('home')}
                    >
                        <div className="size-8 bg-primary rounded-lg flex items-center justify-center text-white shadow-lg shadow-primary/30 group-hover:scale-105 transition-transform">
                            <FileText size={20} />
                        </div>
                        <h1 className="text-slate-900 text-lg font-bold tracking-tight">AI PDF Assistant</h1>
                    </div>

                    {currentView !== 'history' && (
                        <div className="flex items-center gap-6">
                            {/* Nav Links */}
                            <div className="flex items-center bg-slate-100/50 rounded-full p-1 border border-slate-200/60">
                                <button
                                    onClick={() => onNavigate?.('home')}
                                    className={`px-4 py-1.5 rounded-full text-sm font-medium transition-all ${currentView === 'home'
                                        ? 'bg-white text-slate-900 shadow-sm'
                                        : 'text-slate-500 hover:text-slate-700'
                                        }`}
                                >
                                    New Extraction
                                </button>
                            </div>

                            <div className="h-6 w-px bg-slate-200"></div>

                            <div className="flex items-center gap-3">
                                <div className="size-9 rounded-full overflow-hidden border border-slate-200 cursor-pointer shadow-sm bg-slate-100">
                                    {/* Placeholder Avatar */}
                                    <div className="w-full h-full flex items-center justify-center text-slate-400 font-bold text-xs">US</div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </nav>

            {/* Main Content */}
            <main className="relative z-10 flex-1 flex flex-col items-center justify-start pt-12 pb-20 px-6 max-w-[90rem] mx-auto w-full">
                {children}
            </main>
        </div>
    );
}
