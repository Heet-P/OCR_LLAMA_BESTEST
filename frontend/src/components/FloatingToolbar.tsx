import { RotateCcw, History } from 'lucide-react';

interface FloatingToolbarProps {
    onReset: () => void;
    onHistory: () => void;
}

export function FloatingToolbar({ onReset, onHistory }: FloatingToolbarProps) {
    return (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-40">
            <div className="glass-panel px-4 py-2 rounded-full shadow-xl shadow-slate-200/50 flex items-center gap-2 border border-white">
                <button
                    onClick={onReset}
                    className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-full transition-colors"
                >
                    <RotateCcw size={18} />
                    Reset
                </button>
                <div className="w-px h-4 bg-slate-300"></div>
                <button
                    onClick={onHistory}
                    className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-full transition-colors"
                >
                    <History size={18} />
                    History
                </button>
            </div>
        </div>
    );
}
