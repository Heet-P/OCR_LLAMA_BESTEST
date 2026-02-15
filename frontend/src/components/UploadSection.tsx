import React, { useCallback, useState } from 'react';
import { CloudUpload, FolderOpen, Loader2, CheckCircle, ArrowRight } from 'lucide-react';
import { cn } from '../lib/utils';

interface UploadSectionProps {
    onFileSelect: (file: File) => void;
    status: 'idle' | 'uploading' | 'processing' | 'completed' | 'error';
    progress?: number;
    processingLogs?: string[];
    error?: string;
}

export function UploadSection({ onFileSelect, status, progress = 0, processingLogs = [], error }: UploadSectionProps) {
    const [isDragging, setIsDragging] = useState(false);

    const handleDrag = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        if (status !== 'idle' && status !== 'error' && status !== 'completed') return;

        if (e.type === 'dragenter' || e.type === 'dragover') {
            setIsDragging(true);
        } else if (e.type === 'dragleave') {
            setIsDragging(false);
        }
    }, [status]);

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);
        if (status !== 'idle' && status !== 'error' && status !== 'completed') return;

        const files = e.dataTransfer.files;
        if (files && files[0]) {
            validateAndUpload(files[0]);
        }
    }, [status]);

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            validateAndUpload(e.target.files[0]);
        }
    };

    const validateAndUpload = (file: File) => {
        if (!file.type.match('application/pdf') && !file.type.match('image.*')) {
            alert('Please upload a PDF or Image file');
            return;
        }
        onFileSelect(file);
    };

    return (
        <div className="flex flex-col gap-6">
            {/* Upload Zone */}
            <div
                className={cn(
                    "group relative w-full aspect-[4/3] max-h-[400px] flex flex-col items-center justify-center rounded-2xl border-2 border-dashed transition-all duration-300 ease-out",
                    isDragging ? "border-primary bg-blue-50/50 scale-[1.02]" : "border-slate-300 bg-white/40 hover:border-primary/50 hover:bg-white/60 hover:shadow-lg",
                    (status === 'uploading' || status === 'processing') && "opacity-50 pointer-events-none"
                )}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
            >
                <div className="flex flex-col items-center gap-4 p-8 text-center">
                    <div className="size-16 rounded-full bg-slate-50 flex items-center justify-center shadow-sm group-hover:scale-110 transition-transform duration-300">
                        <CloudUpload className="text-primary size-8" />
                    </div>
                    <div className="space-y-1">
                        <p className="text-lg font-semibold text-slate-900">Drag & drop files here</p>
                        <p className="text-sm text-slate-500">Supports PDF, JPG, PNG up to 20MB</p>
                    </div>
                    <div className="mt-4">
                        <button
                            onClick={() => document.getElementById('file-upload')?.click()}
                            className="bg-primary hover:bg-blue-700 text-white font-medium py-2.5 px-6 rounded-lg shadow-md shadow-primary/20 transition-all hover:shadow-lg hover:shadow-primary/30 active:scale-95 flex items-center gap-2"
                        >
                            <FolderOpen size={18} />
                            Browse Files
                        </button>
                        <input
                            id="file-upload"
                            type="file"
                            className="hidden"
                            accept=".pdf,image/*"
                            onChange={handleFileSelect}
                        />
                    </div>
                </div>
            </div>

            {/* Error Message */}
            {status === 'error' && error && (
                <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-red-600 text-sm">
                    Error: {error}
                </div>
            )}

            {/* Processing Status */}
            {(status === 'uploading' || status === 'processing' || status === 'completed') && (
                <div className="rounded-xl border border-slate-200 bg-white shadow-sm p-5 space-y-4">
                    <div className="flex justify-between items-end">
                        <div className="flex items-center gap-2">
                            {status === 'completed' ? (
                                <CheckCircle className="text-green-500 size-5" />
                            ) : (
                                <Loader2 className="text-primary animate-spin size-5" />
                            )}
                            <span className="text-slate-800 font-semibold text-sm">
                                {status === 'uploading' ? 'Uploading...' : status === 'processing' ? 'Processing Document...' : 'Extraction Complete'}
                            </span>
                        </div>
                        <span className="text-slate-500 font-mono text-xs">{progress}%</span>
                    </div>

                    {/* Progress Bar */}
                    <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
                        <div
                            className="h-full bg-gradient-to-r from-primary to-blue-400 rounded-full transition-all duration-300 shadow-[0_0_10px_rgba(17,50,212,0.4)]"
                            style={{ width: `${progress}%` }}
                        ></div>
                    </div>

                    {/* Status Log */}
                    <div className="bg-slate-50 rounded-lg p-3 border border-slate-100 font-mono text-xs space-y-2 max-h-[120px] overflow-y-auto">
                        {processingLogs.map((log, idx) => (
                            <div key={idx} className="flex items-center gap-2 text-slate-600">
                                <ArrowRight size={12} className="text-primary" />
                                <span>{log}</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
