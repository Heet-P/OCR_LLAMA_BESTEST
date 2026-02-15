import requests
import base64
import os
import asyncio
from typing import Dict, Any

class OCRService:
    def __init__(self):
        self.api_key = os.environ.get("NVIDIA_API_KEY")
        self.invoke_url = "https://integrate.api.nvidia.com/v1/chat/completions"
        if not self.api_key:
            print("WARNING: NVIDIA_API_KEY not found in environment variables.")

    def process_document(self, file_content: bytes, content_type: str) -> Dict[str, Any]:
        """
        Process PDF or Image content bytes and return structured OCR data.
        Uses NVIDIA NIM meta/llama-3.2-90b-vision-instruct model.
        """
        if not self.api_key:
             raise ValueError("NVIDIA_API_KEY is not set")

        try:    
            full_text = ""
            
            if content_type == "application/pdf":
                import fitz # PyMuPDF
                doc = fitz.open(stream=file_content, filetype="pdf")
                
                print(f"DEBUG: Processing PDF with {len(doc)} pages")
                
                for i, page in enumerate(doc):
                    print(f"DEBUG: Processing Page {i+1}/{len(doc)}")
                    # 2x zoom for better OCR resolution
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                    png_bytes = pix.tobytes("png")
                    b64_img = base64.b64encode(png_bytes).decode('utf-8')
                    
                    page_text = self._perform_ocr_request(b64_img, f"image/png")
                    full_text += f"\n--- Page {i+1} ---\n{page_text}"
                    
            else:
                # Standard Image
                b64_content = base64.b64encode(file_content).decode('utf-8')
                full_text = self._perform_ocr_request(b64_content, content_type)
            
            return {"text": full_text}

        except Exception as e:
            print(f"OCR Error: {e}")
            raise e

    def _perform_ocr_request(self, b64_image: str, content_type: str) -> str:
        """
        Helper to send a single image to NVIDIA API
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }

        content_blocks = [
            {
                "type": "text",
                "text": "Extract all text from this document. Preserve the structure as much as possible."
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{content_type};base64,{b64_image}"
                }
            }
        ]

        payload = {
            "model": "meta/llama-3.2-90b-vision-instruct",
            "messages": [
                {
                    "role": "user",
                    "content": content_blocks
                }
            ],
            "max_tokens": 1024,
            "temperature": 0.2,
            "top_p": 0.7,
            "stream": False
        }
        
        # print(f"DEBUG: Sending request to {self.invoke_url}")
        
        response = requests.post(self.invoke_url, headers=headers, json=payload)
        
        if response.status_code != 200:
            print(f"DEBUG: API Error Status: {response.status_code}")
            try:
                print(f"DEBUG: API Error Body: {response.json()}")
            except:
                print(f"DEBUG: API Error Body: {response.text}")
        
        response.raise_for_status()
        
        response_json = response.json()
        return response_json['choices'][0]['message']['content']



# Global instance
_ocr_service = None

def get_ocr_service():
    global _ocr_service
    if _ocr_service is None:
        _ocr_service = OCRService()
    return _ocr_service

async def process_form_background(form_id: str, file_content: bytes, content_type: str = "application/pdf"):
    """
    Background task to process form OCR and update database.
    """
    from app.db.supabase import supabase
    
    try:
        print(f"Starting OCR for form {form_id} with type {content_type}")
        
        # Update status to processing
        supabase.table("forms").update({"status": "processing"}).eq("id", form_id).execute()
        
        ocr_service = get_ocr_service()
        
        # Requests is synchronous, so run in executor to avoid blocking event loop
        loop = asyncio.get_event_loop()
        ocr_data = await loop.run_in_executor(None, ocr_service.process_document, file_content, content_type)
        
        # Run Analysis
        from app.core.form_parser.analyzer import analyzer
        schema = await analyzer.analyze_form(ocr_data)
        
        # Add raw text to schema for convenience
        schema['raw_text'] = ocr_data.get("text", "")

        # Update database with result
        supabase.table("forms").update({
            "status": "ready", 
            "ocr_data": ocr_data, # Store the raw text
            "form_schema": schema
        }).eq("id", form_id).execute()
        
        print(f"OCR completed for form {form_id} (Analysis skipped)")
        
    except Exception as e:
        print(f"Error processing form {form_id}: {e}")
        supabase.table("forms").update({
            "status": "error", 
            "ocr_data": {"error": str(e)}
        }).eq("id", form_id).execute()
