import fitz  # PyMuPDF
from app.db.supabase import supabase
import os
import uuid
from app.core.pdf.mapper import mapper

class PDFWriter:
    async def fill_pdf(self, form_id: str, session_id: str) -> str:
        """
        Fill the PDF with data from the session.
        Returns the public URL of the filled PDF.
        """
        # 1. Fetch Form and Session Data
        form_res = supabase.table("forms").select("*").eq("id", form_id).single().execute()
        session_res = supabase.table("sessions").select("form_data").eq("id", session_id).single().execute()
        
        if not form_res.data or not session_res.data:
            raise ValueError("Form or Session not found")
            
        form = form_res.data
        form_data = session_res.data['form_data']
        schema = form['form_schema']
        
        # 2. Download Original PDF
        file_path = form['file_path']
        original_pdf_bytes = supabase.storage.from_("pdf-forms").download(file_path)
        
        # 3. Fill PDF using PyMuPDF
        content_type = form.get('content_type', 'application/pdf')
        
        if 'pdf' in content_type:
             try:
                 doc = fitz.open(stream=original_pdf_bytes, filetype="pdf")
             except Exception:
                 # Fallback if content_type was wrong
                 img_doc = fitz.open(stream=original_pdf_bytes)
                 pdf_bytes = img_doc.convert_to_pdf()
                 doc = fitz.open("pdf", pdf_bytes)
                 img_doc.close()
        else:
             img_doc = fitz.open(stream=original_pdf_bytes)
             pdf_bytes = img_doc.convert_to_pdf()
             doc = fitz.open("pdf", pdf_bytes)
             img_doc.close()
        
        
        
        # 3.5. Try AcroForm Filling First
        print("Checking for Fillable Form Fields (AcroForm)...")
        acro_map = mapper.map_acroform_fields(doc, schema)
        print(f"Mapped {len(acro_map)} fields to widgets.")
        
        # Track which fields are handled by AcroForm
        handled_fields = set()
        
        if acro_map:
            for page in doc:
                for widget in page.widgets():
                    if widget.field_name in acro_map.values():
                        # Find which field_id maps to this widget
                        # Reverse lookup (inefficiet but fine for small forms)
                        field_id = next((k for k, v in acro_map.items() if v == widget.field_name), None)
                        
                        if field_id and field_id in form_data:
                            val = form_data[field_id]
                            if isinstance(val, list): val = ", ".join(map(str, val))
                            
                            print(f"Filling Widget: {widget.field_name} with {val}")
                            widget.field_value = str(val)
                            widget.update() # Commit change
                            handled_fields.add(field_id)

        # 4. Map Coordinates (Visual Fallback)
        print("Mapping visual coordinates for remaining fields...")
        field_map = mapper.get_field_coordinates(doc, schema)

        # 5. Fill Data
        # Track unmapped fields to put on summary page
        unmapped_fields = []

        for field_id, value in form_data.items():
            if field_id in handled_fields:
                continue

            # Handle non-string values
            if isinstance(value, list):
                value = ", ".join(map(str, value))
            
            # Check if we have a visual map
            mapping = field_map.get(field_id)
            
            if mapping:
                # Write to specific location
                try:
                    page_idx = mapping['page_idx']
                    rect = mapping['rect']
                    page = doc[page_idx]
                    
                    # Insert Widget (Auto-Convert to Fillable)
                    # We create a new form field at this location
                    widget = fitz.Widget()
                    widget.rect = rect
                    widget.field_name = field_id
                    widget.field_value = str(value)
                    widget.text_color = [0, 0, 1] # Blue
                    widget.text_fontsize = 10
                    page.add_widget(widget)
                    
                    print(f" injected Widget {field_id} at {rect} on page {page_idx}")
                    continue # Success
                except Exception as e:
                    print(f"Error filling {field_id}: {e}")
            
            unmapped_fields.append((field_id, value))

        # 6. Append Summary Page for Unmapped items
        if unmapped_fields:
            page = doc.new_page()
            page.insert_text((50, 50), "Additional / Unmapped Data", fontsize=16)
            
            y = 100
            for field_id, value in unmapped_fields:
                 # Find label
                label = next((f['label'] for f in schema['fields'] if f['id'] == field_id), field_id)
                text = f"{label}: {value}"
                
                try:
                    page.insert_text((50, y), str(text), fontsize=12)
                except Exception:
                    pass
                y += 20
                
                if y > 800:
                    page = doc.new_page()
                    y = 50
                
        # 4. Save and Upload
        output_filename = f"filled_{uuid.uuid4()}.pdf"
        output_bytes = doc.tobytes()
        
        supabase.storage.from_("pdf-forms").upload(
            output_filename,
            output_bytes,
            {"content-type": "application/pdf"}
        )
        
        # 5. Get URL
        public_url = supabase.storage.from_("pdf-forms").get_public_url(output_filename)
        
        return public_url

pdf_writer = PDFWriter()
