# ⚙️ Backend Architecture: AI Form Assistant
**Scalable, Asynchronous, and AI-Driven Core**

This document details the backend engineering behind our application. We built a robust **FastAPI** service capable of ingesting raw PDFs, understanding them semantically using **LLMs**, and generating pixel-perfect filled documents.

---

## 🛠️ Technology Stack

*   **Runtime**: [Python 3.10+](https://www.python.org/)
*   **Framework**: [FastAPI](https://fastapi.tiangolo.com/) — For high-performance, async API endpoints and automatic Swagger documentation.
*   **Database**: [Supabase (PostgreSQL)](https://supabase.com/) — Robust relational data storage for forms, sessions, and chat history.
*   **vision AI & OCR**: [NVIDIA NIM](https://build.nvidia.com/) — Leveraging the **Meta Llama 3.2 90B Vision Instruct** model for state-of-the-art optical character recognition.
*   **Semantic Reasoning**: [Gemini 1.5 Pro](https://deepmind.google/technologies/gemini/) — For intelligent schema extraction and natural language understanding.
*   **PDF Engine**: [PyMuPDF (fitz)](https://pymupdf.readthedocs.io/) — For precise coordinate mapping and text overlay.

---

## 🧠 System Architecture & Pipelines

The backend is designed as a pipeline of independent, specialized services.

### 1. The Ingestion Pipeline (`/api/v1/endpoints/upload.py`)
Handling files requires robustness.
*   **Validation**: Validates file types (PDF/Image) and size.
*   **Storage**: Securely uploads raw files to Supabase Storage buckets.
*   **Async Processing**: Immediately offloads the heavy lifting to a background task (`BackgroundTasks`), returning a 202-like response to the client instantly.

### 2. Parallel OCR with NVIDIA NIM (`core/ocr.py`)
*Hackathon Winning optimization:*
We don't just process pages sequentially. We implemented a **Parallel Processing Engine** using `ThreadPoolExecutor`.
*   **Splitting**: Breaks multi-page PDFs into individual high-res images.
*   **Concurrency**: Sends up to 5 concurrent requests to the NVIDIA NIM API.
*   **Aggregation**: Stitches the results back together into a coherent document text, preserving reading order.
*   **Benefit**: Reduces Time-to-First-Byte (TTFB) for analysis by **3-4x** on large forms.

### 3. Intelligent Schema Extraction (`core/form_parser/analyzer.py`)
Raw text is useless without structure. We pipe the OCR output into **Gemini 1.5 Pro**.
*   **Prompt Engineering**: We use a specialized system prompt that forces the AI to output a strict JSON schema.
*   **Tasks**:
    1.  Identify input fields (Text, Checkbox, Signature).
    2.  Generate user-friendly questions ("What is the applicant's name?").
    3.  **Language Guard**: Enforces English-only output for questions while preserving the original document's field labels for mapping accuracy.

### 4. The Conversation Engine (`services/chat_service.py`)
This is the state machine that drives the user interaction.
*   **Session Management**: Tracks which field the user is currently filling (`current_field_id`).
*   **Validation**: Uses a lightweight LLM call to validate user answers *in context*. (e.g., "Is 'Steve' a valid answer for 'Date of Birth'?").
*   **State Updates**: updates the `forms` table in real-time as the user answers questions.

### 5. The "Mapper" - Pixel Perfect Filling (`core/pdf/mapper.py`)
The hardest part of PDF automation is knowing *where* to write.
*   **Fuzzy Matching**: Matches the identified field labels (from Schema) against the actual text in the PDF.
*   **Heuristic Algorithms**:
    *   Finds visual anchors (underlines `____`, dots `.....`).
    *   Calculates geometric proximity to determine the best writing coordinates (x, y).
*   **Fallback**: Intelligent fallbacks ("Right of label") if visual cues are missing.

---

## 🚀 Key Technical Highlights

*   **Asynchronous Everywhere**: We use `async/await` throughout the codebase, ensuring the server handles high concurrency without blocking (vital for an AI-heavy app).
*   **Resiliency**: The system handles API failures (NVIDIA/Gemini) with error logging and status updates (`status: error`) so the UI never hangs indefinitely.
*   **Type Safety**: Comprehensive use of **Pydantic** models ensures strict data validation between the frontend and backend.
*   **Clean Architecture**: Separation of concerns into `routers`, `services`, and `core` logic makes the codebase modular and testable.
