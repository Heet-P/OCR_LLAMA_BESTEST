import React, { useState, useEffect, useRef } from 'react';
import { Send, User, Bot, Loader2, Download, AlertCircle } from 'lucide-react';
import { cn } from '../lib/utils';
import { startChat, sendMessage, generatePDF } from '../lib/api';

interface ChatSectionProps {
    formId: string;
    onHighlightChange?: (term: string) => void;
}

interface Message {
    role: 'user' | 'assistant';
    content: string;
}

export function ChatSection({ formId, onHighlightChange }: ChatSectionProps) {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [sessionId, setSessionId] = useState<string | null>(null);
    const [downloadUrl, setDownloadUrl] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (formId) {
            initChat();
        }
    }, [formId]);

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    const initChat = async () => {
        setIsLoading(true);
        try {
            const res = await startChat(formId);
            setSessionId(res.session_id);
            setMessages([{ role: 'assistant', content: res.message }]);

            // Highlight first field
            if (res.field && res.field.label && onHighlightChange) {
                onHighlightChange(res.field.label);
            }
        } catch (err) {
            console.error('Failed to start chat:', err);
            setError("Failed to start the conversation. Please try resetting.");
        } finally {
            setIsLoading(false);
        }
    };

    const handleSend = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || !sessionId) return;

        const userMsg = input.trim();
        setInput('');
        setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
        setIsLoading(true);

        try {
            const res = await sendMessage(sessionId, userMsg);
            setMessages(prev => [...prev, { role: 'assistant', content: res.message }]);

            // Highlight next field
            if (res.field_label && onHighlightChange) {
                onHighlightChange(res.field_label);
            }

            if (res.completed) {
                // Automatically trigger PDF generation or offered it
                try {
                    const pdfRes = await generatePDF(formId, sessionId);
                    setDownloadUrl(pdfRes.url);
                } catch (e) {
                    console.error("PDF Generation failed", e);
                    setMessages(prev => [...prev, { role: 'assistant', content: "Form completed, but PDF generation failed." }]);
                }
            }
        } catch (err) {
            console.error('Failed to send message:', err);
            setMessages(prev => [...prev, { role: 'assistant', content: "Sorry, I encountered an error. Please try again." }]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="flex flex-col h-full w-full rounded-xl border border-slate-700 bg-[#1e1e1e] shadow-xl overflow-hidden relative">
            {/* Header */}
            <div className="flex items-center justify-between bg-[#252526] px-4 py-3 border-b border-slate-700/50">
                <div className="flex items-center gap-2">
                    <div className="size-2 rounded-full bg-green-500 animate-pulse"></div>
                    <span className="text-slate-300 font-medium text-sm">AI Assistant Active</span>
                </div>
                {downloadUrl ? (
                    <a
                        href={downloadUrl}
                        target="_blank"
                        rel="noreferrer"
                        className="flex items-center gap-2 text-xs font-bold text-white bg-green-600 px-3 py-1.5 rounded-md hover:bg-green-700 transition"
                    >
                        <Download size={14} />
                        Download PDF
                    </a>
                ) : (
                    // Show Generate button if form is done but no URL (retry case)
                    // We need a way to track if form is done in state, or just infer it
                    <button
                        onClick={async () => {
                            if (!formId || !sessionId) return;
                            setIsLoading(true);
                            try {
                                const pdfRes = await generatePDF(formId, sessionId);
                                setDownloadUrl(pdfRes.url);
                            } catch (e) {
                                console.error("PDF Retry failed", e);
                                alert("Failed to generate PDF. Please try again.");
                            } finally {
                                setIsLoading(false);
                            }
                        }}
                        className="flex items-center gap-2 text-xs font-bold text-white bg-primary px-3 py-1.5 rounded-md hover:bg-blue-700 transition"
                    >
                        <Download size={14} />
                        Generate PDF
                    </button>
                )}
            </div>

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-6 custom-scrollbar">
                {error && (
                    <div className="flex items-center gap-2 p-3 text-red-400 bg-red-900/20 border border-red-900/50 rounded-lg text-sm">
                        <AlertCircle size={16} />
                        {error}
                    </div>
                )}

                {messages.map((msg, idx) => (
                    <div
                        key={idx}
                        className={cn(
                            "flex gap-3 max-w-[85%]",
                            msg.role === 'user' ? "ml-auto flex-row-reverse" : ""
                        )}
                    >
                        <div
                            className={cn(
                                "size-8 rounded-full flex items-center justify-center shrink-0",
                                msg.role === 'user' ? "bg-slate-700" : "bg-primary"
                            )}
                        >
                            {msg.role === 'user' ? <User size={16} className="text-white" /> : <Bot size={16} className="text-white" />}
                        </div>
                        <div
                            className={cn(
                                "rounded-2xl px-4 py-2 text-sm leading-relaxed shadow-sm",
                                msg.role === 'user'
                                    ? "bg-slate-700 text-white rounded-tr-sm"
                                    : "bg-[#2d2d2d] text-slate-200 rounded-tl-sm border border-slate-700"
                            )}
                        >
                            {msg.content}
                        </div>
                    </div>
                ))}

                {isLoading && (
                    <div className="flex gap-3 max-w-[85%]">
                        <div className="size-8 rounded-full bg-primary flex items-center justify-center shrink-0">
                            <Bot size={16} className="text-white" />
                        </div>
                        <div className="bg-[#2d2d2d] border border-slate-700 rounded-2xl rounded-tl-sm px-4 py-3 flex items-center gap-1.5">
                            <div className="size-1.5 rounded-full bg-slate-400 animate-bounce [animation-delay:-0.3s]"></div>
                            <div className="size-1.5 rounded-full bg-slate-400 animate-bounce [animation-delay:-0.15s]"></div>
                            <div className="size-1.5 rounded-full bg-slate-400 animate-bounce"></div>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="p-4 bg-[#252526] border-t border-slate-700/50">
                <form onSubmit={handleSend} className="relative flex items-center gap-2">
                    <input
                        type="text"
                        name="chat-input"
                        id="chat-input"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Type your answer..."
                        className="w-full bg-[#1e1e1e] border border-slate-700 text-slate-200 text-sm rounded-xl px-4 py-3 pr-12 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary placeholder:text-slate-500"
                        disabled={isLoading || !!error}
                    />
                    <button
                        type="submit"
                        disabled={isLoading || !input.trim() || !!error}
                        className="absolute right-2 p-1.5 rounded-lg bg-primary text-white hover:bg-blue-600 disabled:opacity-50 disabled:hover:bg-primary transition-colors"
                    >
                        {isLoading ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
                    </button>
                </form>
            </div>
        </div>
    );
}
