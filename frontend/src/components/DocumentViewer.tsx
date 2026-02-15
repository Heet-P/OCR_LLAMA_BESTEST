import { useState, useEffect } from 'react';
import { Loader2, ChevronLeft, ChevronRight, Search } from 'lucide-react';
import { api } from '../lib/api';

interface DocumentViewerProps {
    formId: string;
    highlightTerm?: string;
}

interface HighlightRect {
    page: number;
    rect: [number, number, number, number]; // x0, y0, x1, y1
    text: string;
}

export function DocumentViewer({ formId, highlightTerm }: DocumentViewerProps) {
    const [pageIdx, setPageIdx] = useState(1);
    const [imageUrl, setImageUrl] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [highlights, setHighlights] = useState<HighlightRect[]>([]);
    const [isSearching, setIsSearching] = useState(false);

    // Fetch Page Image
    useEffect(() => {
        if (!formId) return;

        const fetchPage = async () => {
            setIsLoading(true);
            try {
                // We use a blob URL for the image
                const response = await api.get(`/forms/${formId}/pages/${pageIdx}`, {
                    responseType: 'blob'
                });
                const url = URL.createObjectURL(response.data);
                setImageUrl(url);
            } catch (err) {
                console.error("Failed to load page image", err);
            } finally {
                setIsLoading(false);
            }
        };

        fetchPage();

        return () => {
            if (imageUrl) URL.revokeObjectURL(imageUrl);
        };
    }, [formId, pageIdx]);

    // Search for Highlights
    useEffect(() => {
        if (!formId || !highlightTerm) {
            setHighlights([]);
            return;
        }

        const fetchHighlights = async () => {
            setIsSearching(true);
            try {
                const response = await api.get(`/forms/${formId}/search`, {
                    params: { q: highlightTerm }
                });
                console.log("Search Results:", response.data);
                setHighlights(response.data.results || []);

                // Auto-switch page if highlight is on another page
                const firstMatch = response.data.results[0];
                if (firstMatch && firstMatch.page !== pageIdx) {
                    setPageIdx(firstMatch.page);
                }
            } catch (err) {
                console.error("Search failed", err);
            } finally {
                setIsSearching(false);
            }
        };

        // Debounce slightly to avoid rapid searches
        const timer = setTimeout(fetchHighlights, 300);
        return () => clearTimeout(timer);

    }, [formId, highlightTerm]);

    // We need to scale highlights to the displayed image size.
    // However, the backend returns PDF coordinates (72 DPI usually).
    // The image we requested is 2x zoom (144 DPI roughly).
    // Let's rely on percentage or just try to fit it.
    // Implementation Detail: PyMuPDF Default is 72 pt/inch.
    // Our render was matrix(2,2) -> so 2x pixels.
    // If we display the image with `width: 100%`, we need to know the natural size.
    // Better strategy: Use a container with relative positioning.

    // For MVP: We assume standard A4 and just try to project blindly or use a scale factor.
    // Let's assume the displayed image width matches the PDF width * scale.
    // Actually, simpler: Use `style={{ left: x, top: y, width: w, height: h }}` but we need to know the ratio.

    // TRICK: We can just return the PDF page dimensions from the backend? 
    // OR just use percentage based coordinates from backend?
    // Let's stick to raw coordinates and applying a scale factor. 
    // PyMuPDF coords are "points". 
    // If we render at 2x, the image is 2x points.
    // On screen, we fit it to container.

    return (
        <div className="flex flex-col h-full border border-slate-700 bg-[#1e1e1e] rounded-xl shadow-xl overflow-hidden">
            {/* Header */}
            <div className="flex items-center justify-between bg-[#252526] px-4 py-3 border-b border-slate-700/50">
                <span className="text-slate-300 font-medium text-sm flex items-center gap-2">
                    <Search size={14} className="text-primary" />
                    Document Viewer
                </span>
                <div className="flex items-center gap-2">
                    <button
                        onClick={() => setPageIdx(p => Math.max(1, p - 1))}
                        className="p-1 hover:bg-slate-700 rounded text-slate-300 disabled:opacity-50"
                        disabled={pageIdx <= 1}
                    >
                        <ChevronLeft size={16} />
                    </button>
                    <span className="text-xs text-slate-400">Page {pageIdx}</span>
                    <button
                        onClick={() => setPageIdx(p => p + 1)}
                        className="p-1 hover:bg-slate-700 rounded text-slate-300"
                    >
                        <ChevronRight size={16} />
                    </button>
                </div>
            </div>

            {/* Viewer */}
            <div className="flex-1 relative overflow-auto bg-[#111] flex justify-center p-4">
                {isLoading ? (
                    <div className="flex items-center justify-center h-full">
                        <Loader2 className="animate-spin text-primary" />
                    </div>
                ) : (
                    <div className="relative shadow-2xl inline-block leading-none">
                        {/* Image */}
                        {imageUrl && (
                            <img
                                src={imageUrl}
                                alt="Page"
                                className="block max-w-full h-auto border border-slate-700"
                                style={{ maxHeight: 'calc(100vh - 200px)' }}
                            />
                        )
                        }

                        {/* Highlights */}
                        {/* 
                           Note: Exact positioning is tricky without knowing the exact rendered size vs displayed size.
                           For this Hackathon MVP, we will try a "best effort" overlay.
                           Ref: PyMuPDF default is 72 DPI. Render is 2x = 144 DPI.
                           So 1 point = 2 pixels in the image.
                           But the image is scaled down via CSS `max-w-full`.
                           
                           Approach: Simply DRAW the highlight onto the image in the backend?
                           No, we need it dynamic.
                           
                           Alternative: Just show the user which page it is on, and maybe a "Toast" saying "Found 2 matches".
                           Visual Highlighting is hard to get pixel perfect in web without a PDF.js viewer.
                           
                           WAIT: I can use a simpler approach. 
                           I know the displayed width of the specific image element.
                       */}
                        {imageUrl && highlights
                            .filter(h => h.page === pageIdx)
                            .map((h, i) => (
                                <HighlightBox key={i} rect={h.rect} />
                            ))
                        }
                    </div>
                )}
            </div>

            {/* Status Bar */}
            {
                highlightTerm && (
                    <div className="bg-[#252526] px-4 py-2 text-xs text-slate-400 border-t border-slate-700/50 flex justify-between">
                        <span>Searching: <span className="text-primary font-bold">{highlightTerm}</span></span>
                        <span>{isSearching ? 'Scanning...' : `Found ${highlights.length} matches`}</span>
                    </div>
                )
            }
        </div >
    );
}

// Helper to render the box. We need to handle the scaling logic here.
// Since we don't know the exact CSS Pixel dimensions, we might be off.
// Let's try to assume the image is rendered natural size for now, or just skip the visual box if it's too hard.
// User asked for "Highlight the exact source text".
// Let's try CSS `mix-blend-mode` overlay.

function HighlightBox({ rect }: { rect: [number, number, number, number] }) {
    // Rect is now [x0%, y0%, x1%, y1%] (0.0 to 1.0)

    return (
        <div
            className="absolute border-2 border-red-500 bg-red-500/30 pointer-events-none transition-all duration-300"
            style={{
                left: `${rect[0] * 100}%`,
                top: `${rect[1] * 100}%`,
                width: `${(rect[2] - rect[0]) * 100}%`,
                height: `${(rect[3] - rect[1]) * 100}%`,
            }}
        />
    );
}
