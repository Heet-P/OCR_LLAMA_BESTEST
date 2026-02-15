import { useState } from 'react';
import { Copy, Download, Sparkles, Check } from 'lucide-react';
import { cn } from '../lib/utils';

interface ResultsSectionProps {
    extractedData: any;
    rawText: string;
}

export function ResultsSection({ extractedData, rawText }: ResultsSectionProps) {
    const [activeTab, setActiveTab] = useState<'json' | 'text'>('json');
    const [copied, setCopied] = useState(false);

    if (!extractedData && !rawText) return null;

    const codeContent = activeTab === 'json'
        ? JSON.stringify(extractedData, null, 2)
        : rawText;

    const handleCopy = () => {
        navigator.clipboard.writeText(codeContent);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    const handleExport = () => {
        const blob = new Blob([codeContent], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = activeTab === 'json' ? 'output.json' : 'raw_text.txt';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    };

    return (
        <div className="flex flex-col gap-4 h-full">
            <div className="flex items-center justify-between mb-1">
                <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider">Extraction Result</h3>
            </div>

            {/* Code Editor Window */}
            <div className="rounded-xl border border-slate-700 bg-[#1e1e1e] shadow-xl overflow-hidden flex flex-col h-[600px]">
                {/* Editor Header / Tabs */}
                <div className="flex items-center justify-between bg-[#252526] px-4 py-2 border-b border-slate-700/50">
                    <div className="flex gap-2">
                        {/* Window Controls */}
                        <div className="flex gap-1.5 mr-4">
                            <div className="size-3 rounded-full bg-red-500/80"></div>
                            <div className="size-3 rounded-full bg-yellow-500/80"></div>
                            <div className="size-3 rounded-full bg-green-500/80"></div>
                        </div>

                        {/* Tabs */}
                        <button
                            onClick={() => setActiveTab('json')}
                            className={cn(
                                "px-3 py-1 rounded text-xs font-medium transition-colors border border-transparent",
                                activeTab === 'json'
                                    ? "bg-[#1e1e1e] text-blue-400 border-slate-700"
                                    : "text-slate-400 hover:text-slate-200"
                            )}
                        >
                            output.json
                        </button>
                        <button
                            onClick={() => setActiveTab('text')}
                            className={cn(
                                "px-3 py-1 rounded text-xs font-medium transition-colors border border-transparent",
                                activeTab === 'text'
                                    ? "bg-[#1e1e1e] text-blue-400 border-slate-700"
                                    : "text-slate-400 hover:text-slate-200"
                            )}
                        >
                            raw_text.txt
                        </button>
                    </div>

                    <div className="flex items-center gap-2">
                        <span className="text-[10px] text-slate-500 font-mono uppercase tracking-widest hidden sm:inline-block">Read Only</span>
                    </div>
                </div>

                {/* Editor Content */}
                <div className="flex-1 overflow-auto p-4 font-mono text-sm leading-relaxed custom-scrollbar">
                    <pre className="text-slate-300">
                        <code>
                            {codeContent}
                        </code>
                    </pre>
                </div>

                {/* Editor Footer / Actions */}
                <div className="bg-[#252526] px-4 py-3 border-t border-slate-700/50 flex justify-end gap-3">
                    <button
                        onClick={handleCopy}
                        className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-slate-700 text-slate-200 text-xs font-medium hover:bg-slate-600 transition-colors"
                    >
                        {copied ? <Check size={14} className="text-green-400" /> : <Copy size={14} />}
                        {copied ? 'Copied' : 'Copy'}
                    </button>
                    <button
                        onClick={handleExport}
                        className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-blue-600 text-white text-xs font-medium hover:bg-blue-500 transition-colors"
                    >
                        <Download size={14} />
                        Export
                    </button>
                </div>
            </div>

            {/* AI Insight (Optional) */}
            <div className="mt-2 p-4 rounded-xl bg-blue-50/50 border border-blue-100 flex items-start gap-3">
                <Sparkles className="text-primary mt-0.5 size-5" />
                <div>
                    <p className="text-sm font-medium text-primary">AI Insight</p>
                    <p className="text-xs text-slate-600 mt-1 leading-relaxed">
                        Data extracted with high confidence. The system identified this as a <strong>{extractedData?.form_schema?.type || 'Standard Document'}</strong>.
                    </p>
                </div>
            </div>
        </div>
    );
}
