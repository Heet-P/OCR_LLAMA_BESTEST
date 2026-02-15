from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from typing import List
from app.db.supabase import supabase
from app.core.ocr import process_form_background
import uuid

router = APIRouter()

@router.post("/upload", response_model=dict)
async def upload_form(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    allowed_types = ["application/pdf", "image/jpeg", "image/png", "image/jpg"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Only PDF and Image files (JPEG, PNG) are allowed")

    try:
        # Generate unique filename
        file_ext = file.filename.split(".")[-1]
        file_name = f"{uuid.uuid4()}.{file_ext}"
        
        # Read file content
        content = await file.read()
        
        # Upload to Supabase Storage
        res = supabase.storage.from_("pdf-forms").upload(
            file_name,
            content,
            {"content-type": "application/pdf"}
        )
        
        # Get Public URL
        public_url = supabase.storage.from_("pdf-forms").get_public_url(file_name)
        
        # Insert into Database
        form_data = {
            "name": file.filename,
            "file_path": file_name,
            "url": public_url,
            "content_type": file.content_type,
            "file_size": len(content),
            "status": "uploaded"
        }
        
        data = supabase.table("forms").insert(form_data).execute()
        form_id = data.data[0]['id']
        
        # Trigger Background OCR
        background_tasks.add_task(process_form_background, form_id, content, file.content_type)
        
        return {"message": "Form uploaded successfully, processing started", "form": data.data[0]}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{form_id}")
async def get_form(form_id: str):
    try:
        data = supabase.table("forms").select("*").eq("id", form_id).single().execute()
        if not data.data:
            raise HTTPException(status_code=404, detail="Form not found")
        return data.data
    except Exception as e:
         raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[dict])
async def list_forms():
    try:
        # Select specific fields to keep payload light
        data = supabase.table("forms").select(
            "id, name, status, created_at, updated_at, file_size"
        ).order("created_at", desc=True).execute()
        return data.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{form_id}/pages/{page_idx}")
async def get_form_page(form_id: str, page_idx: int):
    """
    Render a specific page of the form as a PNG image.
    """
    try:
        # 1. Get Form
        data = supabase.table("forms").select("file_path").eq("id", form_id).single().execute()
        if not data.data:
            raise HTTPException(status_code=404, detail="Form not found")
            
        file_path = data.data['file_path']
        
        # 2. Download File
        file_bytes = supabase.storage.from_("pdf-forms").download(file_path)
        
        # 3. Render Page
        import fitz
        from app.core.highlighter import highlighter
        from fastapi import Response
        
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        
        # Handle images (if we converted them) or try to open as image if pdf fails
        # For MVP assuming standard PDF or we converted it.
        
        png_bytes = highlighter.render_page(doc, page_idx - 1) # 1-based to 0-based
        
        return Response(content=png_bytes, media_type="image/png")
        
    except Exception as e:
        print(f"Error rendering page: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{form_id}/search")
async def search_form_text(form_id: str, q: str):
    """
    Search for text in the form and return coordinates.
    """
    try:
        # 1. Get Form
        data = supabase.table("forms").select("file_path").eq("id", form_id).single().execute()
        if not data.data:
            raise HTTPException(status_code=404, detail="Form not found")
            
        file_path = data.data['file_path']
        
        # 2. Download File
        file_bytes = supabase.storage.from_("pdf-forms").download(file_path)
        
        # 3. Search
        import fitz
        from app.core.highlighter import highlighter
        
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        results = highlighter.search_text(doc, q)
        
        return {"results": results}
        
    except Exception as e:
        print(f"Error searching text: {e}")
        raise HTTPException(status_code=500, detail=str(e))
