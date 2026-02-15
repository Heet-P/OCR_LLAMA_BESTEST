import { useEffect, useState } from 'react';
import { getForms } from '../lib/api';
import { FileText, Clock, ArrowRight } from 'lucide-react';
import { cn } from '../lib/utils';

interface HistorySectionProps {
    onSelectForm: (formId: string) => void;
    onBack: () => void;
}

interface FormRecord {
    id: string;
    name: string;
    status: string;
    created_at: string;
    file_size: number;
}

export function HistorySection({ onSelectForm, onBack }: HistorySectionProps) {
    const [forms, setForms] = useState<FormRecord[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        loadHistory();
    }, []);

    const loadHistory = async () => {
        setIsLoading(true);
        try {
            const data = await getForms();
            setForms(data);
        } catch (err) {
            console.error("Failed to load history", err);
            setError("Failed to load your history.");
        } finally {
            setIsLoading(false);
        }
    };

    const formatDate = (isoString: string) => {
        return new Date(isoString).toLocaleDateString(undefined, {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'ready':
            case 'completed':
                return 'text-green-700 bg-green-100 border-green-200';
            case 'processing':
                return 'text-blue-700 bg-blue-100 border-blue-200';
            case 'error':
                return 'text-red-700 bg-red-100 border-red-200';
            default:
                return 'text-slate-700 bg-slate-100 border-slate-200';
        }
    };

    return (
        <div className="w-full max-w-6xl mx-auto animate-in fade-in duration-500">
            <div className="flex items-center gap-4 mb-8">
                <button
                    onClick={onBack}
                    className="p-2 -ml-2 rounded-full hover:bg-slate-100 text-slate-400 hover:text-slate-900 transition-colors"
                >
                    <ArrowRight className="rotate-180" size={24} />
                </button>
                <h2 className="text-3xl font-bold text-slate-900 flex items-center gap-3">
                    <Clock className="text-primary" />
                    History
                </h2>
            </div>

            {isLoading ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {[1, 2, 3].map(i => (
                        <div key={i} className="h-48 rounded-xl bg-white border border-slate-200 shadow-sm animate-pulse"></div>
                    ))}
                </div>
            ) : error ? (
                <div className="p-8 text-center text-red-600 bg-red-50 border border-red-200 rounded-xl">
                    {error}
                </div>
            ) : forms.length === 0 ? (
                <div className="p-12 text-center text-slate-500 bg-white border border-slate-200 rounded-xl shadow-sm">
                    <p>No history found. Start a new extraction!</p>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {forms.map(form => (
                        <div
                            key={form.id}
                            onClick={() => onSelectForm(form.id)}
                            className="group relative bg-white border border-slate-200 rounded-xl p-6 hover:border-primary/50 transition-all cursor-pointer shadow-sm hover:shadow-md"
                        >
                            <div className="flex justify-between items-start mb-4">
                                <div className="size-10 rounded-lg bg-slate-100 flex items-center justify-center text-slate-400 group-hover:bg-primary group-hover:text-white transition-colors">
                                    <FileText size={20} />
                                </div>
                                <span className={cn(
                                    "px-2.5 py-0.5 rounded-full text-xs font-medium border",
                                    getStatusColor(form.status)
                                )}>
                                    {form.status}
                                </span>
                            </div>

                            <h3 className="text-lg font-semibold text-slate-900 mb-1 truncate px-1">
                                {form.name}
                            </h3>
                            <p className="text-xs text-slate-500 px-1 mb-6">
                                {formatDate(form.created_at)}
                            </p>

                            <div className="absolute bottom-6 right-6 opacity-0 transform translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 transition-all duration-300">
                                <div className="flex items-center gap-1 text-sm font-medium text-primary">
                                    Open <ArrowRight size={16} />
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
